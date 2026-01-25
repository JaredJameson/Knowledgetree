"""
KnowledgeTree - Workflow Tasks
Celery tasks for background workflow execution
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from core.celery_app import celery_app
from core.database import AsyncSessionLocal
from models.agent_workflow import AgentWorkflow, WorkflowStatus
from models.workflow_support import WorkflowState, AgentMessage
from services.agent_base import AgentOrchestrator
import json


@celery_app.task(name="services.workflow_tasks.execute_workflow")
def execute_workflow(workflow_id: int) -> Dict[str, Any]:
    """
    Execute a workflow in the background
    
    This is a synchronous wrapper for async workflow execution.
    Celery will run this in a worker process.
    
    Args:
        workflow_id: ID of workflow to execute
    
    Returns:
        Execution results
    """
    # Run async function in new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            _execute_workflow_async(workflow_id)
        )
        return result
    finally:
        loop.close()


async def _execute_workflow_async(workflow_id: int) -> Dict[str, Any]:
    """Async implementation of workflow execution"""
    async with AsyncSessionLocal() as db:
        # Get workflow
        result = await db.execute(
            select(AgentWorkflow).where(AgentWorkflow.id == workflow_id)
        )
        workflow = result.scalar_one_or_none()
        
        if not workflow:
            return {"error": "Workflow not found"}
        
        # Update status
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.utcnow()
        await db.commit()
        
        # TODO: Execute actual LangGraph workflow here
        # For now, just simulate execution
        
        # Log initial message
        message = AgentMessage(
            workflow_id=workflow_id,
            agent_type="Orchestrator",
            step="initialize",
            content=f"Starting workflow: {workflow.name}",
            reasoning="Workflow initialized via Celery background task"
        )
        db.add(message)
        await db.commit()
        
        # Simulate some work
        await asyncio.sleep(2)
        
        # Update as completed
        workflow.status = WorkflowStatus.COMPLETED
        workflow.completed_at = datetime.utcnow()
        
        if workflow.started_at:
            duration = workflow.completed_at - workflow.started_at
            workflow.actual_duration_minutes = int(duration.total_seconds() / 60)
        
        await db.commit()
        
        return {
            "workflow_id": workflow_id,
            "status": "completed",
            "duration_minutes": workflow.actual_duration_minutes
        }


@celery_app.task(name="services.workflow_tasks.execute_research")
def execute_research(workflow_id: int, query: str) -> Dict[str, Any]:
    """
    Execute research phase of workflow
    
    Args:
        workflow_id: ID of workflow
        query: Research query
    
    Returns:
        Research results
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            _execute_research_async(workflow_id, query)
        )
        return result
    finally:
        loop.close()


async def _execute_research_async(workflow_id: int, query: str) -> Dict[str, Any]:
    """Async implementation of research execution"""
    async with AsyncSessionLocal() as db:
        # Log research start
        message = AgentMessage(
            workflow_id=workflow_id,
            agent_type="ResearchAgent",
            step="discover_urls",
            content=f"Discovering URLs for query: {query}",
            reasoning="Starting URL discovery process"
        )
        db.add(message)
        await db.commit()
        
        # TODO: Implement actual URL discovery with Google Search API
        # For now, return mock results
        
        await asyncio.sleep(1)
        
        return {
            "workflow_id": workflow_id,
            "urls_discovered": 0,
            "query": query
        }


@celery_app.task(name="services.workflow_tasks.execute_scraping")
def execute_scraping(workflow_id: int, urls: list) -> Dict[str, Any]:
    """
    Execute scraping phase of workflow
    
    Args:
        workflow_id: ID of workflow
        urls: List of URLs to scrape
    
    Returns:
        Scraping results
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            _execute_scraping_async(workflow_id, urls)
        )
        return result
    finally:
        loop.close()


async def _execute_scraping_async(workflow_id: int, urls: list) -> Dict[str, Any]:
    """Async implementation of scraping execution"""
    async with AsyncSessionLocal() as db:
        # Log scraping start
        message = AgentMessage(
            workflow_id=workflow_id,
            agent_type="ScraperAgent",
            step="scrape_urls",
            content=f"Scraping {len(urls)} URLs",
            reasoning="Starting parallel web scraping"
        )
        db.add(message)
        await db.commit()
        
        # TODO: Implement actual scraping with crawler orchestrator
        # For now, return mock results
        
        await asyncio.sleep(1)
        
        return {
            "workflow_id": workflow_id,
            "urls_scraped": 0,
            "failed": 0
        }


@celery_app.task(name="services.workflow_tasks.check_approval_timeout")
def check_approval_timeout(workflow_id: int, timeout_minutes: int = 60) -> bool:
    """
    Check if workflow has been waiting too long for approval
    
    Args:
        workflow_id: ID of workflow
        timeout_minutes: Timeout in minutes
    
    Returns:
        True if timed out, False otherwise
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            _check_approval_timeout_async(workflow_id, timeout_minutes)
        )
        return result
    finally:
        loop.close()


async def _check_approval_timeout_async(workflow_id: int, timeout_minutes: int) -> bool:
    """Async implementation of approval timeout check"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(AgentWorkflow).where(AgentWorkflow.id == workflow_id)
        )
        workflow = result.scalar_one_or_none()
        
        if not workflow or workflow.status != "awaiting_approval":
            return False
        
        # Check if timeout exceeded
        if workflow.updated_at:
            timeout = datetime.utcnow() - workflow.updated_at
            if timeout > timedelta(minutes=timeout_minutes):
                # Mark as failed due to timeout
                workflow.status = WorkflowStatus.FAILED
                workflow.error_message = f"Approval timeout after {timeout_minutes} minutes"
                await db.commit()
                return True
        
        return False


@celery_app.task(name="services.workflow_tasks.cleanup_old_workflows")
def cleanup_old_workflows(days: int = 30) -> int:
    """
    Clean up old completed workflows
    
    Args:
        days: Delete workflows older than this many days
    
    Returns:
        Number of workflows deleted
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            _cleanup_old_workflows_async(days)
        )
        return result
    finally:
        loop.close()


async def _cleanup_old_workflows_async(days: int) -> int:
    """Async implementation of cleanup"""
    from sqlalchemy import delete
    
    async with AsyncSessionLocal() as db:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Delete old completed workflows
        stmt = delete(AgentWorkflow).where(
            AgentWorkflow.status == WorkflowStatus.COMPLETED,
            AgentWorkflow.completed_at < cutoff_date
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        return result.rowcount
