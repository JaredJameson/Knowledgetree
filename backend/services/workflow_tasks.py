"""
KnowledgeTree - Workflow Tasks
Celery tasks for background workflow management
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

from sqlalchemy import select, delete

from core.celery_app import celery_app
from core.database import AsyncSessionLocal
from models.agent_workflow import AgentWorkflow, WorkflowStatus


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
