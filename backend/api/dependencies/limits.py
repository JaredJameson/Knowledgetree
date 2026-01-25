"""
KnowledgeTree Backend - Usage Limit Dependencies
Dependency functions for enforcing subscription limits
"""

import logging
from typing import Callable
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.user import User
from api.dependencies.auth import get_current_active_user
from services.usage_service import usage_service
from services.stripe_service import stripe_service

logger = logging.getLogger(__name__)


def check_usage_limit(metric: str) -> Callable:
    """
    Factory function that creates a dependency for checking usage limits.

    Args:
        metric: The metric to check (messages_sent, documents_uploaded, storage_gb, projects)

    Returns:
        Async dependency function that checks the limit

    Usage:
        @router.post("/endpoint")
        async def endpoint(
            user: User = Depends(get_current_active_user),
            _: None = Depends(check_usage_limit("messages_sent"))
        ):
            # This only runs if limit check passes
            pass
    """
    async def _check_limit(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
    ) -> None:
        """Check if user is within usage limits for the specified metric"""
        try:
            # Get user's subscription plan
            subscription = await stripe_service.get_or_create_subscription(db, current_user)
            plan = subscription.plan

            # Check limit
            allowed, current_usage, limit = await usage_service.check_limit(
                db=db,
                user_id=current_user.id,
                metric=metric,
                plan=plan
            )

            if not allowed:
                # User has exceeded their limit
                limit_name = metric.replace("_", " ").title()
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": f"{limit_name} limit exceeded",
                        "message": f"You have reached your plan limit of {limit} {metric}. Please upgrade your plan to continue.",
                        "current_usage": current_usage,
                        "limit": limit,
                        "plan": plan,
                        "metric": metric
                    }
                )

            logger.debug(f"Limit check passed: user={current_user.id}, metric={metric}, usage={current_usage}/{limit}")

        except HTTPException:
            # Re-raise HTTP exceptions (like 429)
            raise
        except Exception as e:
            logger.error(f"Error checking usage limit: {str(e)}")
            # Don't block the request on limit check errors
            # This ensures service continues even if usage tracking has issues
            pass

    return _check_limit


def check_messages_limit() -> Callable:
    """Dependency to check if user can send more messages"""
    return check_usage_limit("messages_sent")


def check_documents_limit() -> Callable:
    """Dependency to check if user can upload more documents"""
    return check_usage_limit("documents_uploaded")


def check_storage_limit() -> Callable:
    """Dependency to check if user has storage space available"""
    return check_usage_limit("storage_gb")


def check_projects_limit() -> Callable:
    """Dependency to check if user can create more projects"""
    return check_usage_limit("projects")
