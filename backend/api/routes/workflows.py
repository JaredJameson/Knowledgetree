"""
KnowledgeTree - Agent Workflows API Routes
REST API for agent workflow management and execution
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from datetime import datetime

from core.database import get_db
from api.dependencies import get_current_user
from models.user import User
from models.agent_workflow import AgentWorkflow, WorkflowStatus, WorkflowTemplate
from models.workflow_support import (
    WorkflowState,
    WorkflowTool,
    URLCandidate,
    AgentMessage,
    ResearchTask
)
from schemas.workflow import (
    WorkflowStartRequest,
    WorkflowStartResponse,
    WorkflowStatusResponse,
    ApprovalRequest,
    ApprovalResponse,
    WorkflowMessagesResponse,
    AgentMessageResponse,
    WorkflowToolsResponse,
    ToolCallResponse,
    URLCandidatesResponse,
    URLCandidateResponse,
    WorkflowListResponse,
    ProgressInfo,
    AgentReasoning,
    WorkflowResults,
)
from services.langgraph_orchestrator import get_langgraph_orchestrator
from services.workflow_tasks import execute_workflow
import json


router = APIRouter(prefix='/agent-workflows', tags=['Agent Workflows'])


# ============================================================================
# Helper Functions
# ============================================================================

async def get_workflow(
    workflow_id: int,
    user_id: int,
    db: AsyncSession
) -> AgentWorkflow:
    """Get workflow by ID with user authorization check"""
    result = await db.execute(
        select(AgentWorkflow).where(
            AgentWorkflow.id == workflow_id,
            AgentWorkflow.project_id == user_id  # Assuming project_id = user_id for now
        )
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return workflow


async def calculate_progress(workflow: AgentWorkflow, db: AsyncSession) -> ProgressInfo:
    """Calculate workflow progress based on completed steps"""
    # Count total steps from execution plan
    if workflow.config:
        try:
            config = json.loads(workflow.config)
            total_steps = len(config.get("steps", []))
        except:
            total_steps = 5  # Default
    else:
        total_steps = 5
    
    # Count completed checkpoints
    result = await db.execute(
        select(func.count(WorkflowState.id)).where(
            WorkflowState.workflow_id == workflow.id
        )
    )
    completed_steps = result.scalar() or 0
    
    return ProgressInfo(
        completed_steps=completed_steps,
        total_steps=total_steps,
        percentage=round((completed_steps / total_steps) * 100, 1) if total_steps > 0 else 0,
        current_operation=workflow.status
    )


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/start", response_model=WorkflowStartResponse)
async def start_workflow(
    request: WorkflowStartRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start a new agent workflow
    
    Creates a new workflow and starts background execution.
    
    **Example:**
    ```json
    {
        "task_type": "research",
        "user_query": "Zrób deep research na temat AI w medycynie",
        "config": {
            "max_urls": 20,
            "require_approval": true
        }
    }
    ```
    """
    # Create workflow record in database
    workflow = AgentWorkflow(
        project_id=current_user.id,
        name=request.user_query[:100],  # Use query as name
        template=WorkflowTemplate[request.task_type.value.upper()],
        status=WorkflowStatus.PENDING,
        config=json.dumps(request.config.dict() if request.config else {}),
        user_query=request.user_query
    )
    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)

    # Start LangGraph workflow execution
    orchestrator = get_langgraph_orchestrator()

    # Execute in background
    background_tasks.add_task(
        orchestrator.execute_workflow,
        workflow_id=workflow.id,
        user_id=current_user.id,
        project_id=current_user.id,
        user_query=request.user_query,
        config=request.config.dict() if request.config else {}
    )

    # Estimate steps and duration based on task type
    estimated_steps = {
        "research": 7,
        "scraping": 4,
        "analysis": 5,
        "full_pipeline": 9
    }.get(request.task_type.value, 5)

    return WorkflowStartResponse(
        workflow_id=workflow.id,
        status=workflow.status.value,
        estimated_steps=estimated_steps,
        current_step="classify_intent",
        current_agent="Orchestrator",
        estimated_duration_minutes=30,
        message=f"Workflow started: {workflow.name}"
    )


@router.get("/{workflow_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get workflow status and progress
    
    Returns current status, progress information, latest agent reasoning,
    and results if completed.
    """
    workflow = await get_workflow(workflow_id, current_user.id, db)
    
    # Get progress
    progress = await calculate_progress(workflow, db)
    
    # Get latest agent reasoning
    result = await db.execute(
        select(AgentMessage)
        .where(AgentMessage.workflow_id == workflow_id)
        .order_by(AgentMessage.created_at.desc())
        .limit(1)
    )
    latest_message = result.scalar_one_or_none()
    
    agent_reasoning = None
    if latest_message:
        agent_reasoning = AgentReasoning(
            agent=latest_message.agent_type,
            step=latest_message.step,
            message=latest_message.content,
            reasoning=latest_message.reasoning or "",
            timestamp=latest_message.created_at
        )
    
    # Get results if completed
    results = None
    if workflow.status == WorkflowStatus.COMPLETED:
        # Count various metrics
        urls_result = await db.execute(
            select(func.count(URLCandidate.id)).where(
                URLCandidate.workflow_id == workflow_id,
                URLCandidate.user_approval == "approved"
            )
        )
        urls_scraped = urls_result.scalar() or 0
        
        # TODO: Get actual knowledge points and relationships when implemented
        results = WorkflowResults(
            urls_discovered=0,  # Will be populated from URLCandidates
            urls_scraped=urls_scraped,
            knowledge_points=0,
            relationships=0,
            knowledge_tree_id=None
        )
    
    return WorkflowStatusResponse(
        id=workflow.id,
        name=workflow.name,
        status=workflow.status.value,
        task_type=workflow.template.value,  # Using template as task_type for now
        current_step="completed" if workflow.status == WorkflowStatus.COMPLETED else workflow.status.value,
        current_agent=workflow.agent_type,
        progress=progress,
        agent_reasoning=agent_reasoning,
        results=results,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at
    )


@router.post("/{workflow_id}/approve", response_model=ApprovalResponse)
async def approve_workflow_checkpoint(
    workflow_id: int,
    request: ApprovalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Approve, reject, or modify workflow checkpoint
    
    Used for human-in-the-loop approval of URL candidates and other checkpoints.
    
    **Example for approve:**
    ```json
    {
        "decision": "approve"
    }
    ```
    
    **Example for modify:**
    ```json
    {
        "decision": "modify",
        "modifications": {
            "add_urls": ["https://example.com"],
            "remove_urls": [1, 2],
            "notes": "Added additional source"
        }
    }
    ```
    """
    workflow = await get_workflow(workflow_id, current_user.id, db)

    if workflow.status != WorkflowStatus.AWAITING_APPROVAL:
        raise HTTPException(
            status_code=400,
            detail=f"Workflow is not awaiting approval (current status: {workflow.status})"
        )

    orchestrator = get_langgraph_orchestrator()

    # Prepare user data based on decision
    user_action = "approve" if request.decision == "approve" else "reject" if request.decision == "reject" else "modify"
    user_data = None

    # Handle modifications if provided
    if request.decision == "modify" and request.modifications:
        # Get current pending URLs
        result = await db.execute(
            select(URLCandidate).where(
                URLCandidate.workflow_id == workflow_id,
                URLCandidate.user_approval == "pending"
            )
        )
        pending_candidates = result.scalars().all()

        # Start with approved URLs (already approved before)
        approved_result = await db.execute(
            select(URLCandidate).where(
                URLCandidate.workflow_id == workflow_id,
                URLCandidate.user_approval == "approved"
            )
        )
        approved_urls = [c.url for c in approved_result.scalars().all()]

        # Add URLs from modifications
        if request.modifications.add_urls:
            for url in request.modifications.add_urls:
                if url not in approved_urls:
                    candidate = URLCandidate(
                        workflow_id=workflow_id,
                        url=url,
                        user_approval="approved",
                        source="user_added"
                    )
                    db.add(candidate)
                    approved_urls.append(url)

        # Remove URLs from modifications
        if request.modifications.remove_urls:
            for url_id in request.modifications.remove_urls:
                result = await db.execute(
                    select(URLCandidate).where(URLCandidate.id == url_id)
                )
                url_candidate = result.scalar_one_or_none()
                if url_candidate and url_candidate.url in approved_urls:
                    approved_urls.remove(url_candidate.url)
                    url_candidate.user_approval = "rejected"

        user_data = {"urls": approved_urls}

    # Update URL approvals if decision is approve/reject
    elif request.decision == "approve":
        result = await db.execute(
            select(URLCandidate).where(
                URLCandidate.workflow_id == workflow_id,
                URLCandidate.user_approval == "pending"
            )
        )
        for candidate in result.scalars().all():
            candidate.user_approval = "approved"

    elif request.decision == "reject":
        result = await db.execute(
            select(URLCandidate).where(
                URLCandidate.workflow_id == workflow_id,
                URLCandidate.user_approval == "pending"
            )
        )
        for candidate in result.scalars().all():
            candidate.user_approval = "rejected"

    await db.commit()

    # Resume workflow with LangGraph orchestrator
    result = await orchestrator.resume_workflow(
        workflow_id=workflow_id,
        user_action=user_action,
        user_data=user_data
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to resume workflow"))

    return ApprovalResponse(
        message=f"Workflow {request.decision}ed",
        workflow_id=workflow_id,
        status=result.get("status", workflow.status.value),
        next_step="scrape_urls" if request.decision in ["approve", "modify"] else "none"
    )


@router.get("/{workflow_id}/messages", response_model=WorkflowMessagesResponse)
async def get_workflow_messages(
    workflow_id: int,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get agent reasoning chain for workflow
    
    Returns all agent messages with reasoning for full transparency.
    """
    workflow = await get_workflow(workflow_id, current_user.id, db)
    
    result = await db.execute(
        select(AgentMessage)
        .where(AgentMessage.workflow_id == workflow_id)
        .order_by(AgentMessage.created_at.desc())
        .limit(limit)
    )
    
    messages = [
        AgentMessageResponse(
            id=msg.id,
            agent_type=msg.agent_type,
            step=msg.step,
            content=msg.content,
            reasoning=msg.reasoning,
            timestamp=msg.created_at
        )
        for msg in result.scalars().all()
    ]
    
    return WorkflowMessagesResponse(messages=messages)


@router.get("/{workflow_id}/tools", response_model=WorkflowToolsResponse)
async def get_workflow_tools(
    workflow_id: int,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get tool calls for workflow
    
    Returns all tool executions with inputs, outputs, and timing.
    """
    workflow = await get_workflow(workflow_id, current_user.id, db)
    
    result = await db.execute(
        select(WorkflowTool)
        .where(WorkflowTool.workflow_id == workflow_id)
        .order_by(WorkflowTool.created_at.desc())
        .limit(limit)
    )
    
    tool_calls = []
    for tool in result.scalars().all():
        tool_calls.append(
            ToolCallResponse(
                id=tool.id,
                tool_name=tool.tool_name,
                agent_type=tool.agent_type,
                input=json.loads(tool.input) if tool.input else {},
                output=json.loads(tool.output) if tool.output else None,
                status=tool.status,
                error_message=tool.error_message,
                duration_ms=tool.duration_ms,
                timestamp=tool.created_at
            )
        )
    
    return WorkflowToolsResponse(tool_calls=tool_calls)


@router.post("/{workflow_id}/stop")
async def stop_workflow(
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Stop a running workflow

    Cancels workflow execution. Cannot stop completed workflows.
    """
    workflow = await get_workflow(workflow_id, current_user.id, db)

    if workflow.status == WorkflowStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Cannot stop completed workflow")

    orchestrator = get_langgraph_orchestrator()
    result = await orchestrator.stop_workflow(workflow_id)

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to stop workflow"))

    return {
        "message": "Workflow stopped",
        "workflow_id": workflow_id,
        "status": result.get("status", "cancelled")
    }


@router.get("", response_model=WorkflowListResponse)
async def list_workflows(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all workflows for current user
    
    Returns paginated list of workflows with optional status filter.
    """
    query = select(AgentWorkflow).where(
        AgentWorkflow.project_id == current_user.id
    )
    
    if status:
        query = query.where(AgentWorkflow.status == WorkflowStatus(status))
    
    # Get total count
    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar() or 0
    
    # Get paginated results
    query = query.order_by(AgentWorkflow.created_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = await query.execute()
    workflows = result.scalars().all()
    
    workflow_responses = []
    for workflow in workflows:
        progress = await calculate_progress(workflow, db)
        
        workflow_responses.append(
            WorkflowStatusResponse(
                id=workflow.id,
                name=workflow.name,
                status=workflow.status.value,
                task_type=workflow.template.value,
                current_step=workflow.status.value,
                current_agent=workflow.agent_type,
                progress=progress,
                agent_reasoning=None,
                results=None,
                created_at=workflow.created_at,
                updated_at=workflow.updated_at
            )
        )
    
    return WorkflowListResponse(
        workflows=workflow_responses,
        total=total,
        page=skip // limit + 1,
        per_page=limit
    )


@router.get("/{workflow_id}/urls", response_model=URLCandidatesResponse)
async def get_url_candidates(
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get URL candidates for review
    
    Returns all discovered URLs awaiting user approval.
    """
    workflow = await get_workflow(workflow_id, current_user.id, db)
    
    result = await db.execute(
        select(URLCandidate).where(
            URLCandidate.workflow_id == workflow_id
        )
    )
    
    candidates = []
    pending = 0
    approved = 0
    rejected = 0
    
    for candidate in result.scalars().all():
        from schemas.workflow import UserApproval
        
        candidates.append(
            URLCandidateResponse(
                id=candidate.id,
                url=candidate.url,
                title=candidate.title,
                relevance_score=float(candidate.relevance_score) if candidate.relevance_score else None,
                source=candidate.source,
                user_approval=UserApproval(candidate.user_approval or "pending")
            )
        )
        
        if candidate.user_approval == "pending":
            pending += 1
        elif candidate.user_approval == "approved":
            approved += 1
        elif candidate.user_approval == "rejected":
            rejected += 1
    
    return URLCandidatesResponse(
        workflow_id=workflow_id,
        candidates=candidates,
        total=len(candidates),
        pending=pending,
        approved=approved,
        rejected=rejected
    )


@router.get("/{workflow_id}/results")
async def get_workflow_results(
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get final workflow results
    
    Returns complete results including generated knowledge tree,
    extracted knowledge points, and summary.
    """
    workflow = await get_workflow(workflow_id, current_user.id, db)
    
    if workflow.status != WorkflowStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Workflow is not completed yet"
        )
    
    # Get URL candidates
    urls_result = await db.execute(
        select(func.count(URLCandidate.id)).where(
            URLCandidate.workflow_id == workflow_id,
            URLCandidate.user_approval == "approved"
        )
    )
    urls_scraped = urls_result.scalar() or 0
    
    # TODO: Get actual results from knowledge tree when implemented
    
    return {
        "workflow_id": workflow_id,
        "status": "completed",
        "results": {
            "urls_discovered": 0,
            "urls_scraped": urls_scraped,
            "knowledge_points": 0,
            "relationships": 0,
            "knowledge_tree_id": None,
            "summary": "Workflow completed successfully",
            "duration_minutes": workflow.actual_duration_minutes
        },
        "created_at": workflow.created_at,
        "completed_at": workflow.completed_at
    }
