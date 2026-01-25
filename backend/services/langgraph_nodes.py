"""
KnowledgeTree - LangGraph Workflow Orchestrator
LangGraph-based agent workflow execution system
"""

import json
from typing import TypedDict, List, Dict, Any, Optional, Literal, Annotated, Callable
from datetime import datetime
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from models.agent_workflow import AgentWorkflow, WorkflowStatus
from models.workflow_support import (
    WorkflowState,
    WorkflowTool,
    URLCandidate,
    AgentMessage
)
from services.claude_tool_client import AnthropicToolClient
from services.agent_tools import register_all_tools
from services.google_search import GoogleSearchService, get_google_search_service
from services.crawler_orchestrator import CrawlerOrchestrator, CrawlEngine
from services.category_tree_generator import CategoryTreeGenerator
from services.api_key_service import get_api_key_for_agent
from models.api_key import KeyType
from core.config import settings
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Helper Functions
# ============================================================================


async def get_user_anthropic_client(db: AsyncSession, user_id: int) -> AnthropicToolClient:
    """
    Get Anthropic client with user-specific API key

    Tries to get API key from database first, then falls back to environment variable.
    """
    api_key = await get_api_key_for_agent(
        db, user_id, KeyType.ANTHROPIC, "ANTHROPIC_API_KEY"
    )
    return AnthropicToolClient(api_key=api_key)


async def get_user_google_search(db: AsyncSession, user_id: int) -> GoogleSearchService:
    """
    Get Google Search service with user-specific API key

    Tries to get API key from database first, then falls back to environment variable.
    """
    api_key = await get_api_key_for_agent(
        db, user_id, KeyType.GOOGLE_SEARCH, "GOOGLE_API_KEY"
    )
    search_service = GoogleSearchService(api_key=api_key)
    await search_service.initialize()
    return search_service


# ============================================================================
# Agent State Definition
# ============================================================================

class TaskType(str, Enum):
    """Workflow task types"""
    RESEARCH = "research"
    SCRAPE = "scrape"
    ANALYZE = "analyze"
    FULL_PIPELINE = "full_pipeline"


class Complexity(str, Enum):
    """Task complexity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class WorkflowStatusState(str, Enum):
    """Workflow execution states"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    AWAITING_APPROVAL = "awaiting_approval"
    CANCELLED = "cancelled"


class AgentWorkflowState(TypedDict):
    """
    Complete state for LangGraph workflow execution
    
    This state is passed between nodes and contains all workflow
    information including user query, discovered URLs, scraped content,
    extracted knowledge, and execution status.
    """
    # Core identifiers
    workflow_id: int
    user_id: int
    project_id: int

    # Task definition
    user_query: str
    task_type: TaskType
    complexity: Complexity

    # Workflow control
    current_step: str
    status: WorkflowStatusState
    current_agent: Optional[str]

    # URL discovery
    discovered_urls: List[Dict[str, Any]]
    approved_urls: List[str]
    rejected_urls: List[int]

    # Scraping results
    scraped_content: List[Dict[str, Any]]
    scraping_errors: List[Dict[str, Any]]

    # Knowledge extraction
    knowledge_points: List[Dict[str, Any]]
    entity_relationships: List[Dict[str, Any]]

    # Tree generation
    category_tree_id: Optional[int]

    # Planning
    execution_plan: Optional[Dict[str, Any]]
    completed_steps: List[str]
    remaining_steps: List[str]

    # Metadata
    error_message: Optional[str]
    retry_count: int
    start_time: datetime
    last_update: datetime

    # Config
    max_urls: int
    require_approval: bool
    category_id: Optional[int]


# ============================================================================
# Node Functions
# ============================================================================

import re

def _detect_youtube_url(text: str) -> bool:
    """Quick detection of YouTube URLs in text"""
    youtube_patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)[a-zA-Z0-9_-]{11}',
        r'youtube\.com\/shorts\/[a-zA-Z0-9_-]{11}',
    ]
    for pattern in youtube_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


async def classify_intent(
    state: AgentWorkflowState,
    config: Dict[str, Any]
) -> AgentWorkflowState:
    """
    Node 1: Classify user query into task type and complexity

    Uses Claude API to analyze user query and determine:
    - Task type (research, scrape, analyze, full_pipeline, youtube)
    - Complexity level (low, medium, high)
    - Required resources
    """
    workflow_id = state["workflow_id"]
    user_id = state["user_id"]
    db: AsyncSession = config["db"]

    logger.info(f"[classify_intent] Workflow {workflow_id}: Classifying intent for query: {state['user_query'][:50]}...")

    # Quick YouTube URL detection
    if _detect_youtube_url(state['user_query']):
        logger.info(f"[classify_intent] Workflow {workflow_id}: YouTube URL detected, using youtube task type")
        state["task_type"] = TaskType.SCRAPE  # YouTube processing is similar to scraping
        state["complexity"] = Complexity.LOW
        state["current_step"] = "extract_knowledge"  # Skip to extraction where tools are called
        state["current_agent"] = "Orchestrator"
        state["youtube_detected"] = True  # Flag for YouTube processing

        await _log_agent_message(
            db=db,
            workflow_id=workflow_id,
            agent_type="Orchestrator",
            step="classify_intent",
            content="YouTube URL detected, will use process_youtube_video tool",
            reasoning="Detected YouTube URL pattern in user query"
        )

        return state

    # Create Claude client with user-specific API key
    claude = await get_user_anthropic_client(db, user_id)

    prompt = f"""Analyze this user query and classify it:

Query: "{state['user_query']}"

Task types:
- research: Discover URLs, scrape content, extract knowledge, build tree
- scrape: Scrape provided URLs and extract knowledge
- analyze: Analyze existing content and extract insights
- full_pipeline: Complete research-to-knowledge-tree pipeline

Complexity:
- low: Simple, straightforward task (<3 steps)
- medium: Moderate complexity (3-7 steps)
- high: Complex, multi-faceted task (7+ steps)

Respond with JSON only:
{{
    "task_type": "research|scrape|analyze|full_pipeline",
    "complexity": "low|medium|high",
    "reasoning": "Brief explanation of classification"
}}
"""

    try:
        response = await claude.execute_simple(
            prompt=prompt,
            model="claude-3-5-sonnet-20241022",
            max_tokens=500
        )

        result = json.loads(response)

        # Update state
        state["task_type"] = TaskType(result["task_type"])
        state["complexity"] = Complexity(result["complexity"])
        state["current_step"] = "create_plan"
        state["current_agent"] = "Orchestrator"
        state["youtube_detected"] = False

        # Log reasoning
        await _log_agent_message(
            db=db,
            workflow_id=workflow_id,
            agent_type="Orchestrator",
            step="classify_intent",
            content=f"Classified as {result['task_type']} ({result['complexity']})",
            reasoning=result.get("reasoning", "")
        )

        logger.info(f"[classify_intent] Workflow {workflow_id}: Classified as {result['task_type']}")

        return state

    except Exception as e:
        logger.error(f"[classify_intent] Workflow {workflow_id}: Error: {e}")
        state["error_message"] = str(e)
        state["status"] = WorkflowStatusState.FAILED
        return state


async def create_plan(
    state: AgentWorkflowState,
    config: Dict[str, Any]
) -> AgentWorkflowState:
    """
    Node 2: Generate execution plan using Claude
    
    Creates detailed step-by-step plan based on task type
    and complexity level.
    """
    workflow_id = state["workflow_id"]
    db: AsyncSession = config["db"]
    
    logger.info(f"[create_plan] Workflow {workflow_id}: Creating execution plan...")
    
    # Define steps based on task type
    task_steps = {
        TaskType.RESEARCH: [
            "classify_intent",
            "create_plan",
            "discover_urls",
            "await_user_review",
            "scrape_urls",
            "extract_knowledge",
            "build_tree",
            "synthesize_results"
        ],
        TaskType.SCRAPE: [
            "classify_intent",
            "create_plan",
            "scrape_urls",
            "extract_knowledge",
            "synthesize_results"
        ],
        TaskType.ANALYZE: [
            "classify_intent",
            "create_plan",
            "query_knowledge_base",
            "extract_insights",
            "synthesize_results"
        ],
        TaskType.FULL_PIPELINE: [
            "classify_intent",
            "create_plan",
            "discover_urls",
            "await_user_review",
            "scrape_urls",
            "extract_knowledge",
            "build_tree",
            "synthesize_results"
        ]
    }
    
    steps = task_steps.get(state["task_type"], task_steps[TaskType.RESEARCH])
    
    # Estimate duration
    duration_per_step = 5  # minutes
    if state["complexity"] == Complexity.HIGH:
        duration_per_step = 10
    
    estimated_duration = len(steps) * duration_per_step
    
    # Update state
    state["execution_plan"] = {
        "steps": steps,
        "estimated_duration_minutes": estimated_duration,
        "task_type": state["task_type"].value,
        "complexity": state["complexity"].value
    }
    state["remaining_steps"] = [s for s in steps if s not in ["classify_intent", "create_plan"]]
    state["completed_steps"] = ["classify_intent", "create_plan"]
    
    # Determine next step
    if state["task_type"] in [TaskType.RESEARCH, TaskType.FULL_PIPELINE]:
        state["current_step"] = "discover_urls"
    elif state["task_type"] == TaskType.SCRAPE:
        state["current_step"] = "scrape_urls"
    else:  # ANALYZE
        state["current_step"] = "query_knowledge_base"
    
    # Update workflow in database
    await _update_workflow_db(
        db=db,
        workflow_id=workflow_id,
        estimated_duration=estimated_duration
    )
    
    # Save checkpoint
    await _save_checkpoint(db, workflow_id, "create_plan", state)
    
    logger.info(f"[create_plan] Workflow {workflow_id}: Plan created with {len(steps)} steps")
    
    return state


async def discover_urls(
    state: AgentWorkflowState,
    config: Dict[str, Any]
) -> AgentWorkflowState:
    """
    Node 3: Discover relevant URLs using Google Search API

    Searches for URLs related to user query and stores them
    as URL candidates for user approval.
    """
    workflow_id = state["workflow_id"]
    user_id = state["user_id"]
    db: AsyncSession = config["db"]

    logger.info(f"[discover_urls] Workflow {workflow_id}: Discovering URLs...")

    state["current_agent"] = "ResearchAgent"
    state["current_step"] = "discover_urls"
    state["status"] = WorkflowStatusState.IN_PROGRESS

    # Get Google Search service with user-specific API key
    search_service = await get_user_google_search(db, user_id)
    
    # Extract search query from user message
    query = state["user_query"]
    
    try:
        # Execute search
        results = await search_service.search(
            query=query,
            num_results=state["max_urls"],
            date_range="year"  # Get recent content
        )
        
        # Store URL candidates
        url_candidates = []
        for result in results:
            # Check if already exists (deduplication)
            existing = await db.execute(
                select(URLCandidate).where(
                    URLCandidate.workflow_id == workflow_id,
                    URLCandidate.url == result["url"]
                )
            )
            if not existing.scalar_one_or_none():
                candidate = URLCandidate(
                    workflow_id=workflow_id,
                    url=result["url"],
                    title=result.get("title", ""),
                    relevance_score=result.get("relevance_score", 0.5),
                    source=result.get("source", "google_search"),
                    metadata=json.dumps({
                        "snippet": result.get("snippet", ""),
                        "date": result.get("date")
                    }),
                    user_approval="pending"
                )
                db.add(candidate)
                url_candidates.append(candidate)
        
        await db.commit()
        
        # Update state
        state["discovered_urls"] = [
            {
                "id": c.id,
                "url": c.url,
                "title": c.title,
                "score": float(c.relevance_score) if c.relevance_score else 0.5
            }
            for c in url_candidates
        ]
        
        # Log reasoning
        await _log_agent_message(
            db=db,
            workflow_id=workflow_id,
            agent_type="ResearchAgent",
            step="discover_urls",
            content=f"Discovered {len(url_candidates)} URLs for query: {query[:50]}...",
            reasoning=f"Used Google Search API with query '{query}', found {len(url_candidates)} relevant results"
        )
        
        # Save checkpoint
        await _save_checkpoint(db, workflow_id, "discover_urls", state)
        
        logger.info(f"[discover_urls] Workflow {workflow_id}: Found {len(url_candidates)} URLs")
        
        # Next step depends on approval requirement
        if state["require_approval"]:
            state["current_step"] = "await_user_review"
            state["status"] = WorkflowStatusState.AWAITING_APPROVAL
        else:
            # Auto-approve all URLs
            for candidate in url_candidates:
                candidate.user_approval = "approved"
            await db.commit()
            
            state["approved_urls"] = [c.url for c in url_candidates]
            state["current_step"] = "scrape_urls"
        
        return state
        
    except Exception as e:
        logger.error(f"[discover_urls] Workflow {workflow_id}: Error: {e}")
        state["error_message"] = str(e)
        state["status"] = WorkflowStatusState.FAILED
        return state


async def await_user_review(
    state: AgentWorkflowState,
    config: Dict[str, Any]
) -> AgentWorkflowState:
    """
    Node 4: Human-in-the-loop checkpoint
    
    Pauses workflow execution to wait for user to review
    and approve/reject URL candidates.
    
    This is a checkpoint node - workflow will be paused here
    until user action triggers resumption.
    """
    workflow_id = state["workflow_id"]
    db: AsyncSession = config["db"]
    
    logger.info(f"[await_user_review] Workflow {workflow_id}: Awaiting user review...")
    
    state["current_agent"] = "Orchestrator"
    state["current_step"] = "await_user_review"
    state["status"] = WorkflowStatusState.AWAITING_APPROVAL
    
    # Get approved URLs
    result = await db.execute(
        select(URLCandidate).where(
            URLCandidate.workflow_id == workflow_id,
            URLCandidate.user_approval == "approved"
        )
    )
    
    approved = result.scalars().all()
    state["approved_urls"] = [url.url for url in approved]
    
    if not state["approved_urls"]:
        # No approved URLs - wait for user
        logger.info(f"[await_user_review] Workflow {workflow_id}: No approved URLs, waiting...")
        return state
    
    # Log reasoning
    await _log_agent_message(
        db=db,
        workflow_id=workflow_id,
        agent_type="Orchestrator",
        step="await_user_review",
        content=f"User approved {len(state['approved_urls'])} URLs",
        reasoning=f"Human-in-the-loop checkpoint completed with {len(state['approved_urls'])} approved URLs"
    )
    
    # Move to next step
    state["current_step"] = "scrape_urls"
    state["status"] = WorkflowStatusState.IN_PROGRESS
    
    return state


async def scrape_urls(
    state: AgentWorkflowState,
    config: Dict[str, Any]
) -> AgentWorkflowState:
    """
    Node 5: Scrape approved URLs using multi-engine crawler
    
    Executes parallel web scraping using auto-detection
    of optimal scraping engine (HTTP/Playwright/Firecrawl).
    """
    workflow_id = state["workflow_id"]
    db: AsyncSession = config["db"]
    
    logger.info(f"[scrape_urls] Workflow {workflow_id}: Scraping {len(state['approved_urls'])} URLs...")
    
    state["current_agent"] = "ScraperAgent"
    state["current_step"] = "scrape_urls"
    state["status"] = WorkflowStatusState.IN_PROGRESS
    
    orchestrator = CrawlerOrchestrator()
    
    try:
        # Execute parallel scraping
        results = await orchestrator.batch_crawl(
            urls=state["approved_urls"],
            concurrency=5,
            extract_links=True,
            extract_images=False
        )
        
        # Process results
        scraped = []
        errors = []
        
        for result in results:
            if result.error:
                errors.append({
                    "url": result.url,
                    "error": result.error,
                    "engine": result.engine.value if result.engine else "unknown"
                })
            else:
                scraped.append({
                    "url": result.url,
                    "title": result.title or "",
                    "text": result.text,
                    "text_length": len(result.text),
                    "links": result.links,
                    "engine": result.engine.value,
                    "status_code": result.status_code
                })
        
        # Update state
        state["scraped_content"] = scraped
        state["scraping_errors"] = errors
        
        # Save scraped content to database
        await _save_scraped_content(
            db=db,
            workflow_id=workflow_id,
            scraped=scraped,
            project_id=state["project_id"],
            category_id=state.get("category_id")
        )
        
        # Log reasoning
        await _log_agent_message(
            db=db,
            workflow_id=workflow_id,
            agent_type="ScraperAgent",
            step="scrape_urls",
            content=f"Scraped {len(scraped)} URLs successfully, {len(errors)} failed",
            reasoning=f"Used multi-engine crawler with auto-detection, success rate: {len(scraped)}/{len(scraped)+len(errors)}"
        )
        
        # Save checkpoint
        await _save_checkpoint(db, workflow_id, "scrape_urls", state)
        
        logger.info(f"[scrape_urls] Workflow {workflow_id}: Scraped {len(scraped)}/{len(state['approved_urls'])} URLs")
        
        # Move to next step
        state["current_step"] = "extract_knowledge"
        
        return state
        
    except Exception as e:
        logger.error(f"[scrape_urls] Workflow {workflow_id}: Error: {e}")
        state["error_message"] = str(e)
        
        # Log error
        await _log_agent_message(
            db=db,
            workflow_id=workflow_id,
            agent_type="ScraperAgent",
            step="scrape_urls",
            content=f"Scraping failed: {str(e)}",
            reasoning=f"Error during web scraping: {str(e)}"
        )
        
        state["status"] = WorkflowStatusState.FAILED
        return state


async def extract_knowledge(
    state: AgentWorkflowState,
    config: Dict[str, Any]
) -> AgentWorkflowState:
    """
    Node 6: Extract structured knowledge using Claude
    
    Uses Claude API to extract entities, relationships,
    facts, and insights from scraped content.
    """
    workflow_id = state["workflow_id"]
    db: AsyncSession = config["db"]
    
    logger.info(f"[extract_knowledge] Workflow {workflow_id}: Extracting knowledge from {len(state['scraped_content'])} documents...")
    
    state["current_agent"] = "AnalyzerAgent"
    state["current_step"] = "extract_knowledge"
    
    claude = AnthropicToolClient()
    
    knowledge_points = []
    entity_relationships = []
    
    # Process each scraped document
    for doc in state["scraped_content"][:10]:  # Limit to 10 documents for now
        try:
            prompt = f"""Extract structured knowledge from this text:

Title: {doc['title']}
URL: {doc['url']}
Text: {doc['text'][:8000]}  # First 8000 chars

Extract:
1. Key entities (people, organizations, concepts, technologies)
2. Relationships between entities
3. Important facts and insights
4. Categories and classifications

Format as JSON:
{{
    "entities": [{{"name": "...", "type": "...", "description": "..."}}],
    "relationships": [{{"source": "...", "target": "...", "type": "..."}}],
    "facts": ["..."],
    "categories": ["..."]
}}
"""
            
            response = await claude.execute_simple(
                prompt=prompt,
                model="claude-3-5-sonnet-20241022",
                max_tokens=3000
            )
            
            extracted = json.loads(response)
            
            # Process entities
            for entity in extracted.get("entities", []):
                knowledge_points.append({
                    "type": "entity",
                    "name": entity.get("name"),
                    "entity_type": entity.get("type"),
                    "description": entity.get("description"),
                    "source_url": doc["url"],
                    "source_title": doc["title"]
                })
            
            # Process facts
            for fact in extracted.get("facts", []):
                knowledge_points.append({
                    "type": "fact",
                    "content": fact,
                    "source_url": doc["url"],
                    "source_title": doc["title"]
                })
            
            # Process relationships
            for rel in extracted.get("relationships", []):
                entity_relationships.append({
                    "source": rel.get("source"),
                    "target": rel.get("target"),
                    "relationship_type": rel.get("type"),
                    "source_url": doc["url"]
                })
            
        except Exception as e:
            logger.warning(f"[extract_knowledge] Error processing document: {e}")
    
    # Update state
    state["knowledge_points"] = knowledge_points
    state["entity_relationships"] = entity_relationships
    
    # Log reasoning
    await _log_agent_message(
        db=db,
        workflow_id=workflow_id,
        agent_type="AnalyzerAgent",
        step="extract_knowledge",
        content=f"Extracted {len(knowledge_points)} knowledge points and {len(entity_relationships)} relationships",
        reasoning=f"Used Claude API to extract entities, facts, and relationships from {len(state['scraped_content'])} documents"
    )
    
    # Save checkpoint
    await _save_checkpoint(db, workflow_id, "extract_knowledge", state)
    
    logger.info(f"[extract_knowledge] Workflow {workflow_id}: Extracted {len(knowledge_points)} knowledge points")
    
    # Move to next step
    state["current_step"] = "build_tree"
    
    return state


async def build_tree(
    state: AgentWorkflowState,
    config: Dict[str, Any]
) -> AgentWorkflowState:
    """
    Node 7: Generate hierarchical knowledge tree
    
    Uses CategoryTreeGenerator to organize knowledge
    points into a hierarchical tree structure.
    """
    workflow_id = state["workflow_id"]
    db: AsyncSession = config["db"]
    
    logger.info(f"[build_tree] Workflow {workflow_id}: Building knowledge tree from {len(state['knowledge_points'])} points...")
    
    state["current_agent"] = "OrganizerAgent"
    state["current_step"] = "build_tree"
    
    try:
        generator = CategoryTreeGenerator()
        
        # Build tree
        tree = await generator.generate_tree(
            knowledge_points=state["knowledge_points"],
            relationships=state["entity_relationships"],
            project_id=state["project_id"],
            parent_category_id=state.get("category_id")
        )
        
        # Update state
        state["category_tree_id"] = tree.id
        
        # Log reasoning
        await _log_agent_message(
            db=db,
            workflow_id=workflow_id,
            agent_type="OrganizerAgent",
            step="build_tree",
            content=f"Built knowledge tree with ID {tree.id}",
            reasoning=f"Used CategoryTreeGenerator to organize {len(state['knowledge_points'])} knowledge points into hierarchical structure"
        )
        
        # Save checkpoint
        await _save_checkpoint(db, workflow_id, "build_tree", state)
        
        logger.info(f"[build_tree] Workflow {workflow_id}: Built tree {tree.id}")
        
        # Move to final step
        state["current_step"] = "synthesize_results"
        
        return state
        
    except Exception as e:
        logger.error(f"[build_tree] Workflow {workflow_id}: Error: {e}")
        state["error_message"] = str(e)
        return state


async def synthesize_results(
    state: AgentWorkflowState,
    config: Dict[str, Any]
) -> AgentWorkflowState:
    """
    Node 8: Generate final summary using Claude
    
    Creates comprehensive summary of findings, insights,
    and recommendations based on all workflow results.
    """
    workflow_id = state["workflow_id"]
    db: AsyncSession = config["db"]
    
    logger.info(f"[synthesize_results] Workflow {workflow_id}: Synthesizing results...")
    
    state["current_agent"] = "Orchestrator"
    state["current_step"] = "synthesize_results"
    
    claude = AnthropicToolClient()
    
    prompt = f"""Synthesize research results:

User Query: {state['user_query']}

Results:
- URLs Discovered: {len(state.get('discovered_urls', []))}
- URLs Scraped: {len(state.get('scraped_content', []))}
- Knowledge Points: {len(state.get('knowledge_points', []))}
- Relationships: {len(state.get('entity_relationships', []))}
- Knowledge Tree ID: {state.get('category_tree_id')}

Provide a comprehensive summary including:
1. Main findings
2. Key insights
3. Recommendations
4. Next steps for further research
"""
    
    try:
        summary = await claude.execute_simple(
            prompt=prompt,
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000
        )
        
        # Update workflow status
        await _update_workflow_db(
            db=db,
            workflow_id=workflow_id,
            status=WorkflowStatus.COMPLETED,
            summary=summary
        )
        
        # Log reasoning
        await _log_agent_message(
            db=db,
            workflow_id=workflow_id,
            agent_type="Orchestrator",
            step="synthesize_results",
            content=f"Generated final summary for workflow",
            reasoning="Synthesized all results into comprehensive summary"
        )
        
        # Update state
        state["status"] = WorkflowStatusState.COMPLETED
        state["completed_steps"] = state["completed_steps"] + ["synthesize_results"]
        state["remaining_steps"] = []
        
        # Save final checkpoint
        await _save_checkpoint(db, workflow_id, "synthesize_results", state)
        
        logger.info(f"[synthesize_results] Workflow {workflow_id}: Workflow completed")
        
        return state
        
    except Exception as e:
        logger.error(f"[synthesize_results] Workflow {workflow_id}: Error: {e}")
        state["error_message"] = str(e)
        state["status"] = WorkflowStatusState.FAILED
        return state


async def handle_error(
    state: AgentWorkflowState,
    config: Dict[str, Any]
) -> AgentWorkflowState:
    """
    Node 9: Error handling and recovery
    
    Attempts to recover from errors with retry logic
    or graceful degradation.
    """
    workflow_id = state["workflow_id"]
    db: AsyncSession = config["db"]
    
    logger.error(f"[handle_error] Workflow {workflow_id}: Handling error in step {state['current_step']}")
    
    state["current_agent"] = "ErrorHandler"
    state["retry_count"] = state.get("retry_count", 0) + 1
    
    # Log error
    await _log_agent_message(
        db=db,
        workflow_id=workflow_id,
        agent_type="ErrorHandler",
        step="handle_error",
        content=f"Error in step {state['current_step']}: {state.get('error_message', 'Unknown error')}",
        reasoning=f"Attempt {state['retry_count']} at error recovery"
    )
    
    if state["retry_count"] < 3:
        # Retry from last successful step
        state["status"] = WorkflowStatusState.IN_PROGRESS
        # Determine retry logic based on error type
        # This would be more sophisticated in production
    else:
        # Max retries exceeded
        state["status"] = WorkflowStatusState.FAILED
        await _update_workflow_db(
            db=db,
            workflow_id=workflow_id,
            status=WorkflowStatus.FAILED,
            error_message=state.get("error_message", "Max retries exceeded")
        )
    
    return state


# ============================================================================
# Conditional Edge Functions
# ============================================================================

def should_create_plan(state: AgentWorkflowState) -> str:
    """Determine next step after classify_intent"""
    if state.get("error_message"):
        return "handle_error"
    return "create_plan"


def determine_next_step(state: AgentWorkflowState) -> str:
    """Determine next step after create_plan"""
    task_type = state.get("task_type", TaskType.RESEARCH)
    
    if task_type in [TaskType.RESEARCH, TaskType.FULL_PIPELINE]:
        return "discover_urls"
    elif task_type == TaskType.SCRAPE:
        return "scrape_urls"
    else:  # ANALYZE
        return "query_knowledge_base"


def check_approval_required(state: AgentWorkflowState) -> str:
    """Check if user approval is required"""
    if state.get("require_approval", True):
        return "await_user_review"
    else:
        return "scrape_urls"


def check_user_response(state: AgentWorkflowState) -> str:
    """Check user's approval decision"""
    if not state.get("approved_urls"):
        # User rejected all URLs or didn't approve any
        return "handle_error"  # Will cancel workflow
    return "scrape_urls"


# ============================================================================
# Helper Functions
# ============================================================================

async def _log_agent_message(
    db: AsyncSession,
    workflow_id: int,
    agent_type: str,
    step: str,
    content: str,
    reasoning: str
):
    """Log agent reasoning to database"""
    message = AgentMessage(
        workflow_id=workflow_id,
        agent_type=agent_type,
        step=step,
        content=content,
        reasoning=reasoning
    )
    db.add(message)
    await db.commit()


async def _save_checkpoint(
    db: AsyncSession,
    workflow_id: int,
    step: str,
    state: AgentWorkflowState
):
    """Save workflow state checkpoint"""
    # Convert to JSON-serializable dict
    state_copy = state.copy()
    
    # Convert enums to strings
    if "task_type" in state_copy and isinstance(state_copy["task_type"], Enum):
        state_copy["task_type"] = state_copy["task_type"].value
    if "complexity" in state_copy and isinstance(state_copy["complexity"], Enum):
        state_copy["complexity"] = state_copy["complexity"].value
    if "status" in state_copy and isinstance(state_copy["status"], Enum):
        state_copy["status"] = state_copy["status"].value
    
    checkpoint = WorkflowState(
        workflow_id=workflow_id,
        step=step,
        state_snapshot=json.dumps(state_copy, default=str),
        status=state_copy["status"]
    )
    db.add(checkpoint)
    await db.commit()


async def _update_workflow_db(
    db: AsyncSession,
    workflow_id: int,
    status: Optional[WorkflowStatus] = None,
    estimated_duration: Optional[int] = None,
    summary: Optional[str] = None,
    error_message: Optional[str] = None
):
    """Update workflow in database"""
    result = await db.execute(
        select(AgentWorkflow).where(AgentWorkflow.id == workflow_id)
    )
    workflow = result.scalar_one_or_none()
    
    if workflow:
        if status:
            workflow.status = status
            if status == WorkflowStatus.RUNNING and not workflow.started_at:
                from datetime import datetime
                workflow.started_at = datetime.utcnow()
            elif status == WorkflowStatus.COMPLETED:
                from datetime import datetime
                workflow.completed_at = datetime.utcnow()
        
        if estimated_duration:
            workflow.estimated_duration_minutes = estimated_duration
        
        if error_message:
            workflow.error_message = error_message
        
        if summary:
            if workflow.execution_log:
                log = json.loads(workflow.execution_log)
            else:
                log = {}
            log["summary"] = summary
            workflow.execution_log = json.dumps(log)
        
        await db.commit()


async def _save_scraped_content(
    db: AsyncSession,
    workflow_id: int,
    scraped: List[Dict[str, Any]],
    project_id: int,
    category_id: Optional[int]
):
    """Save scraped content to database"""
    from models.document import Document
    
    for item in scraped:
        document = Document(
            project_id=project_id,
            category_id=category_id,
            filename=item["title"][:200] or "scraped_content",
            original_url=item["url"],
            status="completed",
            content_type="text/html",
            file_size=item["text_length"],
            page_count=1,
            processed_text=item["text"],
            metadata={
                "engine": item["engine"],
                "workflow_id": workflow_id,
                "links_count": len(item.get("links", []))
            }
        )
        db.add(document)
    
    await db.commit()
