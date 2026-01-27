"""
KnowledgeTree Backend - Rate Limiting Dependencies
FastAPI dependencies for rate limiting
"""

import logging
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.config import settings
from models.user import User
from models.subscription import Subscription, SubscriptionPlan
from api.dependencies.auth import get_current_active_user
from services.rate_limiter import RateLimiter, RateLimitExceeded
from sqlalchemy import select

logger = logging.getLogger(__name__)


# Initialize rate limiter
rate_limiter = RateLimiter(redis_url=settings.REDIS_URL)


async def get_user_subscription_plan(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> str:
    """
    Get user's subscription plan

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        Subscription plan (free, starter, professional, enterprise)
    """
    # Get user's subscription
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == current_user.id)
    )
    subscription = result.scalar_one_or_none()

    # Default to free plan if no subscription
    if not subscription or not subscription.is_active:
        return SubscriptionPlan.FREE.value

    return subscription.plan


def check_rate_limit(action: str = "upload"):
    """
    Create rate limit checker dependency for specific action

    Args:
        action: Action type (upload, api)

    Returns:
        Dependency function that checks rate limit

    Example:
        @router.post("/upload", dependencies=[Depends(check_rate_limit("upload"))])
        async def upload_document(...):
            ...
    """

    async def _check_rate_limit(
        current_user: User = Depends(get_current_active_user),
        subscription_plan: str = Depends(get_user_subscription_plan)
    ):
        """Check if user has exceeded rate limit for action"""
        try:
            # Check rate limit
            allowed, current_count, limit = rate_limiter.check_rate_limit(
                user_id=current_user.id,
                subscription_plan=subscription_plan,
                action=action
            )

            # Log rate limit check
            logger.debug(
                f"Rate limit check for user {current_user.id}: "
                f"{current_count}/{limit} {action}s per hour"
            )

        except RateLimitExceeded as e:
            # Rate limit exceeded - return 429 Too Many Requests
            logger.warning(
                f"Rate limit exceeded for user {current_user.id}: "
                f"{e.limit} {action}s per hour"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": str(e),
                    "limit": e.limit,
                    "window": e.window,
                    "retry_after": e.retry_after
                },
                headers={"Retry-After": str(e.retry_after)}
            )

    return _check_rate_limit


async def increment_rate_limit(
    action: str,
    current_user: User,
    subscription_plan: str,
    amount: int = 1
):
    """
    Increment rate limit counter after successful request

    Args:
        action: Action type (upload, api)
        current_user: Current authenticated user
        subscription_plan: User's subscription plan
        amount: Amount to increment (default: 1)
    """
    try:
        new_count = rate_limiter.increment_rate_limit(
            user_id=current_user.id,
            subscription_plan=subscription_plan,
            action=action,
            amount=amount
        )

        logger.debug(
            f"Rate limit incremented for user {current_user.id}: "
            f"{new_count} {action}s in current hour"
        )

    except Exception as e:
        # Log error but don't fail the request
        logger.error(f"Failed to increment rate limit: {e}")


async def get_rate_limit_info(
    action: str,
    current_user: User,
    subscription_plan: str
) -> dict:
    """
    Get rate limit information for user

    Args:
        action: Action type (upload, api)
        current_user: Current authenticated user
        subscription_plan: User's subscription plan

    Returns:
        Dict with remaining, limit, and reset information
    """
    try:
        remaining, limit = rate_limiter.get_remaining(
            user_id=current_user.id,
            subscription_plan=subscription_plan,
            action=action
        )

        return {
            "remaining": remaining,
            "limit": limit,
            "action": action,
            "window": "hour"
        }

    except Exception as e:
        logger.error(f"Failed to get rate limit info: {e}")
        return {
            "remaining": 0,
            "limit": 0,
            "action": action,
            "window": "hour"
        }
