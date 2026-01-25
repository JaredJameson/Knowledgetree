"""
KnowledgeTree - LangGraph Orchestrator
Main LangGraph StateGraph for agent workflow orchestration
"""

from typing import Dict, Any, Optional, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import json
import asyncio

from core.database import AsyncSessionLocal
from models.agent_workflow import AgentWorkflow, WorkflowStatus
from models.workflow_support import WorkflowState, URLCandidate
from schemas.workflow import AgentWorkflowState, WorkflowTaskType, TaskComplexity
from services.langgraph_nodes import (
    classify_intent,
    create_plan,
    discover_urls,
    await_user_review,
    scrape_urls,
    extract_knowledge,
    build_tree,
    synthesize_results,
    handle_error,
    should_create_plan,
    determine_next_step,
    check_approval_required,
    check_user_response,
)
from services.claude_tool_client import AnthropicToolClient


# ============================================================================
# LangGraph Orchestrator
# ============================================================================


class LangGraphOrchestrator:
    """
    Main LangGraph workflow orchestrator

    Manages the complete agent workflow using LangGraph StateGraph:
    1. Classify user intent
    2. Create execution plan
    3. Discover URLs via search
    4. Await user approval (human-in-the-loop)
    5. Scrape discovered URLs
    6. Extract knowledge from content
    7. Build hierarchical tree
    8. Synthesize final results
    9. Handle errors at any step
    """

    def __init__(self):
        self.workflow = None
        self.checkpointer = MemorySaver()
        self._build_graph()

    def _build_graph(self):
        """Build the LangGraph StateGraph with all nodes and edges"""

        # Create StateGraph with our state schema
        self.workflow = StateGraph(AgentWorkflowState)

        # Add all nodes (9 total)
        self.workflow.add_node("classify_intent", classify_intent)
        self.workflow.add_node("create_plan", create_plan)
        self.workflow.add_node("discover_urls", discover_urls)
        self.workflow.add_node("await_user_review", await_user_review)
        self.workflow.add_node("scrape_urls", scrape_urls)
        self.workflow.add_node("extract_knowledge", extract_knowledge)
        self.workflow.add_node("build_tree", build_tree)
        self.workflow.add_node("synthesize_results", synthesize_results)
        self.workflow.add_node("handle_error", handle_error)

        # Set entry point
        self.workflow.set_entry_point("classify_intent")

        # Add conditional edges

        # classify_intent → (create_plan OR discover_urls)
        self.workflow.add_conditional_edges(
            "classify_intent",
            should_create_plan,
            {
                "create_plan": "create_plan",
                "discover_urls": "discover_urls"
            }
        )

        # create_plan → discover_urls
        self.workflow.add_edge("create_plan", "discover_urls")

        # discover_urls → (await_user_review OR scrape_urls)
        self.workflow.add_conditional_edges(
            "discover_urls",
            check_approval_required,
            {
                "await_approval": "await_user_review",
                "proceed": "scrape_urls"
            }
        )

        # await_user_review → (scrape_urls OR classify_intent)
        self.workflow.add_conditional_edges(
            "await_user_review",
            check_user_response,
            {
                "approved": "scrape_urls",
                "rejected": "classify_intent",
                "modified": "discover_urls"
            }
        )

        # scrape_urls → (extract_knowledge OR build_tree)
        self.workflow.add_conditional_edges(
            "scrape_urls",
            determine_next_step,
            {
                "extract_knowledge": "extract_knowledge",
                "build_tree": "build_tree",
                "synthesize": "synthesize_results",
                "error": "handle_error"
            }
        )

        # extract_knowledge → (build_tree OR synthesize_results)
        self.workflow.add_conditional_edges(
            "extract_knowledge",
            determine_next_step,
            {
                "build_tree": "build_tree",
                "synthesize": "synthesize_results",
                "error": "handle_error"
            }
        )

        # build_tree → synthesize_results
        self.workflow.add_edge("build_tree", "synthesize_results")

        # synthesize_results → END
        self.workflow.add_edge("synthesize_results", END)

        # Error handling edges from any node
        self.workflow.add_edge("handle_error", END)

        # Compile graph with checkpointer
        self.workflow = self.workflow.compile(checkpointer=self.checkpointer)

    async def execute_workflow(
        self,
        workflow_id: int,
        user_id: int,
        project_id: int,
        user_query: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the LangGraph workflow

        Args:
            workflow_id: Database workflow ID
            user_id: User ID
            project_id: Project ID
            user_query: User's natural language query
            config: Optional configuration (timeout, max_urls, etc.)

        Returns:
            Dict with final results and status
        """
        if config is None:
            config = {}

        # Initialize state
        initial_state: AgentWorkflowState = {
            "workflow_id": workflow_id,
            "user_id": user_id,
            "project_id": project_id,
            "user_query": user_query,
            "task_type": WorkflowTaskType.FULL_PIPELINE,
            "complexity": TaskComplexity.MEDIUM,
            "current_step": "classify_intent",
            "status": "in_progress",
            "discovered_urls": [],
            "approved_urls": [],
            "scraped_content": [],
            "knowledge_points": [],
            "tree_structure": {},
            "error": None,
            "retry_count": 0,
            "max_retries": config.get("max_retries", 3),
            "max_urls": config.get("max_urls", 20),
            "timeout_seconds": config.get("timeout_seconds", 1800),  # 30 min default
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "metadata": config
        }

        # LangGraph config with thread_id for checkpointing
        graph_config = {
            "configurable": {
                "thread_id": f"workflow_{workflow_id}"
            }
        }

        try:
            # Execute workflow graph
            async with AsyncSessionLocal() as db:
                # Update workflow status to processing
                await self._update_workflow_status(
                    db, workflow_id, WorkflowStatus.PROCESSING
                )

                # Run the graph asynchronously
                result = await self.workflow.ainvoke(
                    initial_state,
                    config=graph_config
                )

                # Update final status
                if result.get("error"):
                    await self._update_workflow_status(
                        db, workflow_id, WorkflowStatus.FAILED, error=result["error"]
                    )
                elif result.get("status") == "awaiting_approval":
                    # Workflow paused for user approval
                    await self._update_workflow_status(
                        db, workflow_id, WorkflowStatus.AWAITING_APPROVAL
                    )
                else:
                    await self._update_workflow_status(
                        db, workflow_id, WorkflowStatus.COMPLETED
                    )

                await db.commit()

            return {
                "success": not bool(result.get("error")),
                "workflow_id": workflow_id,
                "status": result.get("status"),
                "final_state": result,
                "tree_structure": result.get("tree_structure"),
                "knowledge_points": result.get("knowledge_points"),
                "scraped_urls_count": len(result.get("approved_urls", [])),
                "error": result.get("error")
            }

        except Exception as e:
            # Handle execution errors
            async with AsyncSessionLocal() as db:
                await self._update_workflow_status(
                    db, workflow_id, WorkflowStatus.FAILED, error=str(e)
                )
                await db.commit()

            return {
                "success": False,
                "workflow_id": workflow_id,
                "status": "failed",
                "error": str(e)
            }

    async def resume_workflow(
        self,
        workflow_id: int,
        user_action: Literal["approve", "reject", "modify"],
        user_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Resume a paused workflow after user approval

        Args:
            workflow_id: Workflow ID to resume
            user_action: User's action (approve/reject/modify)
            user_data: Optional data (e.g., modified URLs for modify action)

        Returns:
            Dict with results
        """
        async with AsyncSessionLocal() as db:
            # Get current workflow state
            result = await db.execute(
                select(AgentWorkflow).where(AgentWorkflow.id == workflow_id)
            )
            workflow = result.scalar_one_or_none()

            if not workflow:
                return {
                    "success": False,
                    "error": "Workflow not found"
                }

            if workflow.status != WorkflowStatus.AWAITING_APPROVAL:
                return {
                    "success": False,
                    "error": f"Workflow is not awaiting approval. Current status: {workflow.status}"
                }

            # Get latest checkpoint state
            state_result = await db.execute(
                select(WorkflowState)
                .where(WorkflowState.workflow_id == workflow_id)
                .order_by(WorkflowState.created_at.desc())
                .limit(1)
            )
            latest_state = state_result.scalar_one_or_none()

            if not latest_state:
                return {
                    "success": False,
                    "error": "No checkpoint state found"
                }

            # Load state from JSON
            state: AgentWorkflowState = json.loads(latest_state.state_snapshot)

            # Update state based on user action
            if user_action == "approve":
                # Approve all discovered URLs
                url_result = await db.execute(
                    select(URLCandidate).where(
                        URLCandidate.workflow_id == workflow_id,
                        URLCandidate.status == "pending"
                    )
                )
                candidates = url_result.scalars().all()

                approved_urls = [c.url for c in candidates]
                state["approved_urls"] = approved_urls
                state["user_response"] = "approved"

                # Mark candidates as approved
                for candidate in candidates:
                    candidate.status = "approved"
                    candidate.reviewed_at = datetime.utcnow()

            elif user_action == "reject":
                state["user_response"] = "rejected"
                state["discovered_urls"] = []
                state["approved_urls"] = []

                # Mark candidates as rejected
                url_result = await db.execute(
                    select(URLCandidate).where(URLCandidate.workflow_id == workflow_id)
                )
                candidates = url_result.scalars().all()
                for candidate in candidates:
                    candidate.status = "rejected"
                    candidate.reviewed_at = datetime.utcnow()

            elif user_action == "modify":
                # User provided modified URLs
                if user_data and "urls" in user_data:
                    state["discovered_urls"] = user_data["urls"]
                    state["approved_urls"] = user_data["urls"]
                    state["user_response"] = "modified"

                    # Update URL candidates
                    # Delete old candidates
                    await db.execute(
                        URLCandidate.__table__.delete()
                        .where(URLCandidate.workflow_id == workflow_id)
                    )

                    # Add new candidates as approved
                    for url in user_data["urls"]:
                        candidate = URLCandidate(
                            workflow_id=workflow_id,
                            url=url,
                            title="User-provided",
                            status="approved",
                            relevance_score=1.0,
                            reviewed_at=datetime.utcnow()
                        )
                        db.add(candidate)

            # Update workflow status
            workflow.status = WorkflowStatus.PROCESSING
            await db.commit()

            # Resume graph execution
            graph_config = {
                "configurable": {
                    "thread_id": f"workflow_{workflow_id}"
                }
            }

            try:
                result = await self.workflow.ainvoke(
                    state,
                    config=graph_config
                )

                # Update final status
                if result.get("error"):
                    await self._update_workflow_status(
                        db, workflow_id, WorkflowStatus.FAILED, error=result["error"]
                    )
                else:
                    await self._update_workflow_status(
                        db, workflow_id, WorkflowStatus.COMPLETED
                    )

                await db.commit()

                return {
                    "success": not bool(result.get("error")),
                    "workflow_id": workflow_id,
                    "status": result.get("status"),
                    "final_state": result,
                    "error": result.get("error")
                }

            except Exception as e:
                await self._update_workflow_status(
                    db, workflow_id, WorkflowStatus.FAILED, error=str(e)
                )
                await db.commit()

                return {
                    "success": False,
                    "workflow_id": workflow_id,
                    "error": str(e)
                }

    async def stop_workflow(self, workflow_id: int) -> Dict[str, Any]:
        """
        Stop a running workflow

        Args:
            workflow_id: Workflow ID to stop

        Returns:
            Dict with status
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(AgentWorkflow).where(AgentWorkflow.id == workflow_id)
            )
            workflow = result.scalar_one_or_none()

            if not workflow:
                return {
                    "success": False,
                    "error": "Workflow not found"
                }

            # Update status to cancelled
            workflow.status = WorkflowStatus.FAILED
            workflow.error_message = "Cancelled by user"
            workflow.updated_at = datetime.utcnow()

            await db.commit()

            # Note: Actual cancellation of running async tasks would require
            # additional cancellation token handling in node functions
            # This is a simplified version

            return {
                "success": True,
                "workflow_id": workflow_id,
                "status": "cancelled"
            }

    async def get_workflow_state(
        self,
        workflow_id: int
    ) -> Optional[AgentWorkflowState]:
        """
        Get current workflow state from latest checkpoint

        Args:
            workflow_id: Workflow ID

        Returns:
            Current state or None if not found
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(WorkflowState)
                .where(WorkflowState.workflow_id == workflow_id)
                .order_by(WorkflowState.created_at.desc())
                .limit(1)
            )
            latest_state = result.scalar_one_or_none()

            if latest_state:
                return json.loads(latest_state.state_snapshot)

            return None

    async def _update_workflow_status(
        self,
        db: AsyncSession,
        workflow_id: int,
        status: WorkflowStatus,
        error: Optional[str] = None
    ):
        """Helper to update workflow status in database"""
        result = await db.execute(
            select(AgentWorkflow).where(AgentWorkflow.id == workflow_id)
        )
        workflow = result.scalar_one_or_none()

        if workflow:
            workflow.status = status
            workflow.updated_at = datetime.utcnow()

            if error:
                workflow.error_message = error

            # Set completion time if finished
            if status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]:
                if not workflow.completed_at:
                    workflow.completed_at = datetime.utcnow()


# ============================================================================
# Global Instance
# ============================================================================


_langgraph_orchestrator: Optional[LangGraphOrchestrator] = None


def get_langgraph_orchestrator() -> LangGraphOrchestrator:
    """
    Get global LangGraph orchestrator instance

    Returns:
        LangGraphOrchestrator singleton
    """
    global _langgraph_orchestrator

    if _langgraph_orchestrator is None:
        _langgraph_orchestrator = LangGraphOrchestrator()

    return _langgraph_orchestrator
