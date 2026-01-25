"""
Usage Tracking Service
Track and manage user API usage
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from models.user import User
from models.usage import Usage

logger = logging.getLogger(__name__)


class UsageService:
    """Service for tracking and managing user usage"""

    # Usage limits per plan (messages per month)
    PLAN_LIMITS = {
        "free": 50,
        "starter": 500,
        "professional": 2000,
        "enterprise": None,  # Unlimited
    }

    @staticmethod
    async def get_period_start_end(period: str) -> tuple[datetime, datetime]:
        """Get start and end dates for a period"""
        now = datetime.utcnow()

        if period == "daily":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
        elif period == "monthly":
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # Next month
            if now.month == 12:
                end = start.replace(year=now.year + 1, month=1, day=1)
            else:
                end = start.replace(month=now.month + 1, day=1)
        elif period == "yearly":
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = start.replace(year=now.year + 1)
        else:
            raise ValueError(f"Invalid period: {period}")

        return start, end

    @staticmethod
    async def get_or_create_usage(
        db: AsyncSession,
        user_id: int,
        metric: str,
        period: str
    ) -> Usage:
        """Get existing usage record or create new one"""
        period_start, period_end = await UsageService.get_period_start_end(period)

        result = await db.execute(
            select(Usage).where(
                and_(
                    Usage.user_id == user_id,
                    Usage.metric == metric,
                    Usage.period == period,
                    Usage.period_start == period_start
                )
            )
        )
        usage = result.scalar_one_or_none()

        if not usage:
            usage = Usage(
                user_id=user_id,
                metric=metric,
                value=0,
                period=period,
                period_start=period_start,
                period_end=period_end
            )
            db.add(usage)
            await db.flush()

        return usage

    @staticmethod
    async def increment_usage(
        db: AsyncSession,
        user_id: int,
        metric: str,
        period: str = "monthly",
        amount: int = 1
    ) -> Usage:
        """Increment usage counter"""
        usage = await UsageService.get_or_create_usage(db, user_id, metric, period)
        usage.value += amount
        usage.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(usage)

        logger.info(f"Incremented usage: user={user_id}, metric={metric}, value={usage.value}")
        return usage

    @staticmethod
    async def get_usage(
        db: AsyncSession,
        user_id: int,
        metric: str,
        period: str = "monthly"
    ) -> int:
        """Get current usage for a metric"""
        usage = await UsageService.get_or_create_usage(db, user_id, metric, period)
        return usage.value

    @staticmethod
    async def check_limit(
        db: AsyncSession,
        user_id: int,
        metric: str,
        plan: str = "free"
    ) -> tuple[bool, int, Optional[int]]:
        """
        Check if user is within usage limits

        Returns:
            (allowed, current_usage, limit)
            - allowed: Whether the action is allowed
            - current_usage: Current usage count
            - limit: Usage limit (None for unlimited)
        """
        limit = UsageService.PLAN_LIMITS.get(plan)
        current_usage = await UsageService.get_usage(db, user_id, metric, "monthly")

        if limit is None:
            # Unlimited
            return True, current_usage, None

        allowed = current_usage < limit
        return allowed, current_usage, limit

    @staticmethod
    async def get_usage_summary(
        db: AsyncSession,
        user_id: int
    ) -> dict:
        """Get usage summary for all metrics"""
        period_start, period_end = await UsageService.get_period_start_end("monthly")

        result = await db.execute(
            select(
                Usage.metric,
                func.sum(Usage.value).label('total')
            ).where(
                and_(
                    Usage.user_id == user_id,
                    Usage.period == "monthly",
                    Usage.period_start == period_start
                )
            ).group_by(Usage.metric)
        )

        usage_data = {row.metric: row.total for row in result}

        return {
            "messages_sent": usage_data.get("messages_sent", 0),
            "tokens_used": usage_data.get("tokens_used", 0),
            "documents_uploaded": usage_data.get("documents_uploaded", 0),
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
        }


usage_service = UsageService()
