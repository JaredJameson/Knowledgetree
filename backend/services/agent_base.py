"""
KnowledgeTree - Base Agent Service
Base classes and utilities for agent orchestration
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.workflow_support import AgentMessage, WorkflowTool, WorkflowState
from models.agent_workflow import AgentWorkflow


class BaseAgent(ABC):
    """
    Base class for all agent types

    Provides common functionality for logging reasoning,
    tracking tool calls, and managing state.
    """

    def __init__(self, name: Optional[str] = None):
        # Use class name if no name provided
        if name is None:
            name = self.__class__.__name__
        self.name = name
    
    async def log_reasoning(
        self,
        db: AsyncSession,
        workflow_id: int,
        step: str,
        content: str,
        reasoning: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentMessage:
        """
        Log agent reasoning to database
        
        Args:
            db: Database session
            workflow_id: Workflow ID
            step: Current workflow step
            content: Message content
            reasoning: Detailed reasoning explanation
            metadata: Additional metadata
        
        Returns:
            Created AgentMessage record
        """
        import json

        message = AgentMessage(
            workflow_id=workflow_id,
            agent_type=self.name,
            step=step,
            content=content,
            reasoning=reasoning,
            meta_data=json.dumps(metadata) if metadata else None
        )
        
        db.add(message)
        await db.flush()
        
        return message
    
    async def log_tool_call(
        self,
        db: AsyncSession,
        workflow_id: int,
        tool_name: str,
        input_data: Dict[str, Any],
        output_data: Optional[Dict[str, Any]],
        status: str,
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None
    ) -> WorkflowTool:
        """
        Log tool execution to database
        
        Args:
            db: Database session
            workflow_id: Workflow ID
            tool_name: Name of tool called
            input_data: Tool input parameters
            output_data: Tool output results
            status: Execution status
            error_message: Error details if failed
            duration_ms: Execution duration
        
        Returns:
            Created WorkflowTool record
        """
        import json
        
        tool_call = WorkflowTool(
            workflow_id=workflow_id,
            tool_name=tool_name,
            agent_type=self.name,
            input=json.dumps(input_data),
            output=json.dumps(output_data) if output_data else None,
            status=status,
            error_message=error_message,
            duration_ms=duration_ms
        )
        
        db.add(tool_call)
        await db.flush()
        
        return tool_call
    
    async def save_state_checkpoint(
        self,
        db: AsyncSession,
        workflow_id: int,
        step: str,
        state_snapshot: Dict[str, Any],
        status: str
    ) -> WorkflowState:
        """
        Save workflow state checkpoint
        
        Args:
            db: Database session
            workflow_id: Workflow ID
            step: Current step name
            state_snapshot: Complete state as dict
            status: Current status
        
        Returns:
            Created WorkflowState record
        """
        import json
        
        checkpoint = WorkflowState(
            workflow_id=workflow_id,
            step=step,
            state_snapshot=json.dumps(state_snapshot),
            status=status
        )
        
        db.add(checkpoint)
        await db.flush()
        
        return checkpoint
    
    async def execute(
        self,
        state: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Execute agent's primary function (default implementation)

        Each agent should override this with their specific execute logic.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement execute() method. "
            f"Use specific execute_* methods instead (e.g., execute_research, execute_scraping)."
        )


class AgentOrchestrator:
    """
    Central orchestrator for agent workflows
    
    Manages workflow execution, agent coordination,
    and state persistence.
    """
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
    
    def register_agent(self, agent: BaseAgent):
        """Register an agent with the orchestrator"""
        self.agents[agent.name] = agent
    
    async def start_workflow(
        self,
        db: AsyncSession,
        user_id: int,
        project_id: int,
        task_type: str,
        user_query: str,
        config: Optional[Dict[str, Any]] = None
    ) -> AgentWorkflow:
        """
        Start a new agent workflow
        
        Args:
            db: Database session
            user_id: User ID
            project_id: Project ID
            task_type: Type of task
            user_query: User's query
            config: Optional configuration
        
        Returns:
            Created AgentWorkflow
        """
        from models.agent_workflow import WorkflowStatus, WorkflowTemplate
        
        workflow = AgentWorkflow(
            name=f"{task_type}: {user_query[:50]}...",
            template=WorkflowTemplate.CUSTOM,
            status=WorkflowStatus.PENDING,
            config=str(config) if config else None,
            project_id=project_id,
            estimated_duration_minutes=self._estimate_duration(task_type)
        )
        
        db.add(workflow)
        await db.commit()
        await db.refresh(workflow)
        
        return workflow
    
    async def get_workflow_state(
        self,
        db: AsyncSession,
        workflow_id: int
    ) -> Dict[str, Any]:
        """
        Get current workflow state from latest checkpoint
        
        Args:
            db: Database session
            workflow_id: Workflow ID
        
        Returns:
            Current state as dict
        """
        import json
        
        result = await db.execute(
            select(WorkflowState)
            .where(WorkflowState.workflow_id == workflow_id)
            .order_by(WorkflowState.created_at.desc())
            .limit(1)
        )
        
        checkpoint = result.scalar_one_or_none()
        
        if checkpoint:
            return json.loads(checkpoint.state_snapshot)
        
        return {}
    
    async def update_workflow_status(
        self,
        db: AsyncSession,
        workflow_id: int,
        status: str,
        error_message: Optional[str] = None
    ):
        """Update workflow status"""
        from models.agent_workflow import WorkflowStatus
        
        result = await db.execute(
            select(AgentWorkflow).where(AgentWorkflow.id == workflow_id)
        )
        workflow = result.scalar_one_or_none()
        
        if workflow:
            workflow.status = WorkflowStatus(status)
            workflow.error_message = error_message
            
            if status == "completed":
                workflow.completed_at = datetime.utcnow()
            
            await db.commit()
    
    def _estimate_duration(self, task_type: str) -> int:
        """Estimate workflow duration in minutes"""
        durations = {
            "research": 30,
            "scrape": 15,
            "analyze": 20,
            "full_pipeline": 45
        }
        return durations.get(task_type, 30)


class ToolExecutionStrategy:
    """
    Strategies for tool execution
    """
    
    @staticmethod
    async def sequential(
        tools: List[callable],
        inputs: List[Dict[str, Any]]
    ) -> List[Any]:
        """Execute tools one after another"""
        import asyncio
        
        results = []
        for tool, input_data in zip(tools, inputs):
            result = await tool(**input_data)
            results.append(result)
        return results
    
    @staticmethod
    async def parallel(
        tools: List[callable],
        inputs: List[Dict[str, Any]]
    ) -> List[Any]:
        """Execute tools concurrently"""
        import asyncio
        
        tasks = [tool(**input) for tool, input in zip(tools, inputs)]
        return await asyncio.gather(*tasks)
    
    @staticmethod
    async def retry(
        tool: callable,
        input_data: Dict[str, Any],
        max_retries: int = 3,
        backoff: float = 1.0
    ) -> Any:
        """Execute tool with retry logic"""
        import asyncio
        
        for attempt in range(max_retries):
            try:
                return await tool(**input_data)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(backoff * (2 ** attempt))
    
    @staticmethod
    async def fallback(
        primary_tool: callable,
        fallback_tool: callable,
        input_data: Dict[str, Any]
    ) -> Any:
        """Execute fallback tool if primary fails"""
        try:
            return await primary_tool(**input_data)
        except Exception:
            return await fallback_tool(**input_data)
