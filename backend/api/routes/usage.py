"""
Usage Routes
Get user usage statistics and limits
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.user import User
from services.usage_service import usage_service
from services.stripe_service import stripe_service
from api.dependencies import get_current_active_user

router = APIRouter(prefix="/usage", tags=["Usage"])
logger = logging.getLogger(__name__)


@router.get("/summary")
async def get_usage_summary(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current usage summary

    Returns usage statistics for the current billing period (monthly)
    """
    try:
        summary = await usage_service.get_usage_summary(db, current_user.id)
        return summary
    except Exception as e:
        logger.error(f"Failed to get usage summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/limits")
async def get_usage_limits(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Check usage limits for current user

    Returns:
        - messages: Message limit status
        - documents: Document limit status
        - storage: Storage limit status
        - projects: Project limit status
        - plan: Current plan name
    """
    try:
        # Get user's actual subscription plan
        subscription = await stripe_service.get_or_create_subscription(db, current_user)
        plan = subscription.plan

        # Check limits for all metrics
        messages_allowed, messages_used, messages_limit = await usage_service.check_limit(
            db=db,
            user_id=current_user.id,
            metric="messages_sent",
            plan=plan
        )

        documents_allowed, documents_used, documents_limit = await usage_service.check_limit(
            db=db,
            user_id=current_user.id,
            metric="documents_uploaded",
            plan=plan
        )

        storage_allowed, storage_used, storage_limit = await usage_service.check_limit(
            db=db,
            user_id=current_user.id,
            metric="storage_gb",
            plan=plan
        )

        projects_allowed, projects_used, projects_limit = await usage_service.check_limit(
            db=db,
            user_id=current_user.id,
            metric="projects",
            plan=plan
        )

        return {
            "plan": plan,
            "messages": {
                "allowed": messages_allowed,
                "used": messages_used,
                "limit": messages_limit,
                "remaining": (messages_limit - messages_used) if messages_limit else None
            },
            "documents": {
                "allowed": documents_allowed,
                "used": documents_used,
                "limit": documents_limit,
                "remaining": (documents_limit - documents_used) if documents_limit else None
            },
            "storage": {
                "allowed": storage_allowed,
                "used": storage_used,
                "limit": storage_limit,
                "remaining": (storage_limit - storage_used) if storage_limit else None
            },
            "projects": {
                "allowed": projects_allowed,
                "used": projects_used,
                "limit": projects_limit,
                "remaining": (projects_limit - projects_used) if projects_limit else None
            }
        }
    except Exception as e:
        logger.error(f"Failed to get usage limits: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
