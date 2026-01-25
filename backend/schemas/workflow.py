"""
KnowledgeTree - Agent Workflow Schemas
Pydantic schemas for agent workflow API endpoints
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class WorkflowTaskType(str, Enum):
    """Types of workflow tasks"""
    RESEARCH = "research"
    SCRAPE = "scrape"
    ANALYZE = "analyze"
    FULL_PIPELINE = "full_pipeline"


class TaskComplexity(str, Enum):
    """Complexity levels for tasks"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class UserApproval(str, Enum):
    """User approval status for URL candidates"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# ============================================================================
# Request Schemas
# ============================================================================

class WorkflowConfig(BaseModel):
    """Configuration options for workflow execution"""
    max_urls: int = Field(20, ge=1, le=200, description="Maximum URLs to discover/scrape")
    scrape_parallel: bool = Field(True, description="Use parallel scraping")
    require_approval: bool = Field(True, description="Require user approval for URLs")
    category_id: Optional[int] = Field(None, description="Category ID for saved content")
    date_range: str = Field("any", description="Date range filter: day, week, month, year, any")
    language: str = Field("pl", description="Search language")


class WorkflowStartRequest(BaseModel):
    """Request to start a new workflow"""
    task_type: WorkflowTaskType = Field(..., description="Type of workflow to execute")
    user_query: str = Field(..., min_length=10, max_length=2000, description="User's query/request")
    config: Optional[WorkflowConfig] = Field(None, description="Optional workflow configuration")


class ApprovalRequest(BaseModel):
    """Request to approve/reject workflow checkpoint"""
    decision: Literal["approve", "reject", "modify"] = Field(..., description="User decision")
    modifications: Optional["ApprovalModifications"] = Field(None, description="Modifications if decision is 'modify'")


class ApprovalModifications(BaseModel):
    """Modifications to workflow at approval checkpoint"""
    add_urls: Optional[List[str]] = Field(None, description="Additional URLs to add")
    remove_urls: Optional[List[int]] = Field(None, description="URL IDs to remove")
    modify_config: Optional[Dict[str, Any]] = Field(None, description="Config modifications")
    notes: Optional[str] = Field(None, description="User notes")


# ============================================================================
# Response Schemas
# ============================================================================

class ProgressInfo(BaseModel):
    """Progress information for workflow"""
    completed_steps: int = Field(..., description="Number of completed steps")
    total_steps: int = Field(..., description="Total number of steps")
    percentage: float = Field(..., description="Progress percentage (0-100)")
    current_operation: str = Field(..., description="Current operation description")


class AgentReasoning(BaseModel):
    """Agent reasoning information"""
    agent: str = Field(..., description="Agent type (e.g., 'ResearchAgent')")
    step: str = Field(..., description="Current workflow step")
    message: str = Field(..., description="Agent message")
    reasoning: str = Field(..., description="Detailed reasoning")
    timestamp: datetime = Field(..., description="When reasoning was logged")


class WorkflowResults(BaseModel):
    """Results from workflow execution"""
    urls_discovered: int = Field(0, description="Number of URLs discovered")
    urls_scraped: int = Field(0, description="Number of URLs successfully scraped")
    knowledge_points: int = Field(0, description="Number of knowledge points extracted")
    relationships: int = Field(0, description="Number of relationships found")
    knowledge_tree_id: Optional[int] = Field(None, description="ID of generated knowledge tree")


class WorkflowStatusResponse(BaseModel):
    """Response with workflow status"""
    id: int = Field(..., description="Workflow ID")
    name: str = Field(..., description="Workflow name")
    status: str = Field(..., description="Current status")
    task_type: WorkflowTaskType = Field(..., description="Type of task")
    current_step: str = Field(..., description="Current workflow step")
    current_agent: Optional[str] = Field(None, description="Currently executing agent")
    progress: Optional[ProgressInfo] = Field(None, description="Progress information")
    agent_reasoning: Optional[AgentReasoning] = Field(None, description="Latest agent reasoning")
    results: Optional[WorkflowResults] = Field(None, description="Workflow results (if completed)")
    created_at: datetime = Field(..., description="Workflow creation time")
    updated_at: datetime = Field(..., description="Last update time")


class WorkflowStartResponse(BaseModel):
    """Response when starting a workflow"""
    workflow_id: int = Field(..., description="ID of created workflow")
    status: str = Field(..., description="Initial status")
    estimated_steps: int = Field(..., description="Estimated number of steps")
    current_step: str = Field(..., description="First step")
    current_agent: Optional[str] = Field(None, description="Agent for first step")
    estimated_duration_minutes: int = Field(..., description="Estimated duration")
    message: str = Field(..., description="Status message")


class ApprovalResponse(BaseModel):
    """Response to approval request"""
    message: str = Field(..., description="Response message")
    workflow_id: int = Field(..., description="Workflow ID")
    status: str = Field(..., description="New workflow status")
    next_step: str = Field(..., description="Next step after approval")


class AgentMessageResponse(BaseModel):
    """Single agent message"""
    id: int = Field(..., description="Message ID")
    agent_type: str = Field(..., description="Agent type")
    step: str = Field(..., description="Workflow step")
    content: str = Field(..., description="Message content")
    reasoning: Optional[str] = Field(None, description="Agent reasoning")
    timestamp: datetime = Field(..., description="Message timestamp")


class WorkflowMessagesResponse(BaseModel):
    """Response with agent reasoning chain"""
    messages: List[AgentMessageResponse] = Field(..., description="List of agent messages")


class ToolCallResponse(BaseModel):
    """Single tool call record"""
    id: int = Field(..., description="Tool call ID")
    tool_name: str = Field(..., description="Name of tool")
    agent_type: Optional[str] = Field(None, description="Agent that called tool")
    input: Dict[str, Any] = Field(..., description="Tool input parameters")
    output: Optional[Dict[str, Any]] = Field(None, description="Tool output")
    status: str = Field(..., description="Execution status")
    error_message: Optional[str] = Field(None, description="Error if failed")
    duration_ms: Optional[int] = Field(None, description="Execution duration")
    timestamp: datetime = Field(..., description="Tool execution time")


class WorkflowToolsResponse(BaseModel):
    """Response with tool calls for a workflow"""
    tool_calls: List[ToolCallResponse] = Field(..., description="List of tool calls")


class URLCandidateResponse(BaseModel):
    """Single URL candidate"""
    id: int = Field(..., description="Candidate ID")
    url: str = Field(..., description="URL")
    title: Optional[str] = Field(None, description="Page title")
    relevance_score: Optional[float] = Field(None, description="Relevance score (0-1)")
    source: Optional[str] = Field(None, description="Discovery source")
    user_approval: UserApproval = Field(..., description="User approval status")


class URLCandidatesResponse(BaseModel):
    """Response with URL candidates for review"""
    workflow_id: int = Field(..., description="Workflow ID")
    candidates: List[URLCandidateResponse] = Field(..., description="URL candidates")
    total: int = Field(..., description="Total number of candidates")
    pending: int = Field(..., description="Number pending approval")
    approved: int = Field(..., description="Number approved")
    rejected: int = Field(..., description="Number rejected")


class WorkflowListResponse(BaseModel):
    """Response listing workflows"""
    workflows: List[WorkflowStatusResponse] = Field(..., description="List of workflows")
    total: int = Field(..., description="Total count")
    page: int = Field(..., description="Current page")
    per_page: int = Field(..., description="Items per page")


# ============================================================================
# Internal Schemas (for service layer)
# ============================================================================

class AgentWorkflowState(BaseModel):
    """Complete state for LangGraph workflow execution"""
    # Core identifiers
    workflow_id: int
    user_id: int
    project_id: int
    
    # Task definition
    user_query: str
    task_type: WorkflowTaskType
    complexity: TaskComplexity
    
    # Workflow control
    current_step: str
    status: Literal["pending", "in_progress", "completed", "failed", "awaiting_approval"]
    current_agent: Optional[str]
    
    # URL discovery
    discovered_urls: List[Dict[str, Any]] = []
    approved_urls: List[str] = []
    rejected_urls: List[int] = []
    
    # Scraping results
    scraped_content: List[Dict[str, Any]] = []
    scraping_errors: List[Dict[str, Any]] = []
    
    # Knowledge extraction
    knowledge_points: List[Dict[str, Any]] = []
    entity_relationships: List[Dict[str, Any]] = []
    
    # Tree generation
    category_tree_id: Optional[int] = None
    
    # Planning
    execution_plan: Optional[Dict[str, Any]] = None
    completed_steps: List[str] = []
    remaining_steps: List[str] = []
    
    # Metadata
    error_message: Optional[str] = None
    retry_count: int = 0
    start_time: datetime
    last_update: datetime


# ============================================================================
# Update forward references
# ============================================================================

ApprovalRequest.model_rebuild()
