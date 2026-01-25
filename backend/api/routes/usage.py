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
        - tokens: Token limit status (if applicable)
        - plan: Current plan name (default: free)
    """
    # TODO: Get user's plan from subscription when Stripe is integrated
    # For now, default to "free" plan
    plan = "free"

    try:
        messages_allowed, messages_used, messages_limit = await usage_service.check_limit(
            db=db,
            user_id=current_user.id,
            metric="messages_sent",
            plan=plan
        )

        return {
            "plan": plan,
            "messages": {
                "allowed": messages_allowed,
                "used": messages_used,
                "limit": messages_limit,
                "remaining": (messages_limit - messages_used) if messages_limit else None
            }
        }
    except Exception as e:
        logger.error(f"Failed to get usage limits: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
