"""
KnowledgeTree - Rate Limiting Service
Redis-based rate limiting per user and subscription tier
"""

import redis
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
from models.subscription import SubscriptionPlan

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded"""
    def __init__(self, limit: int, window: str, retry_after: int):
        self.limit = limit
        self.window = window
        self.retry_after = retry_after
        super().__init__(
            f"Rate limit exceeded: {limit} requests per {window}. "
            f"Try again in {retry_after} seconds."
        )


class RateLimiter:
    """
    Redis-based rate limiter with subscription tier support

    Rate limits per subscription plan:
    - FREE: 5 uploads/hour, 50 API calls/hour
    - STARTER: 20 uploads/hour, 200 API calls/hour
    - PROFESSIONAL: 100 uploads/hour, 1000 API calls/hour
    - ENTERPRISE: 1000 uploads/hour, 10000 API calls/hour
    """

    # Upload rate limits (requests per hour)
    UPLOAD_LIMITS = {
        SubscriptionPlan.FREE.value: 5,
        SubscriptionPlan.STARTER.value: 20,
        SubscriptionPlan.PROFESSIONAL.value: 100,
        SubscriptionPlan.ENTERPRISE.value: 1000,
    }

    # API call rate limits (requests per hour)
    API_LIMITS = {
        SubscriptionPlan.FREE.value: 50,
        SubscriptionPlan.STARTER.value: 200,
        SubscriptionPlan.PROFESSIONAL.value: 1000,
        SubscriptionPlan.ENTERPRISE.value: 10000,
    }

    def __init__(self, redis_url: str):
        """
        Initialize rate limiter with Redis connection

        Args:
            redis_url: Redis connection URL
        """
        self.redis_client = redis.from_url(redis_url, decode_responses=True)

    def _get_key(self, user_id: int, action: str, window_start: datetime) -> str:
        """
        Generate Redis key for rate limit tracking

        Args:
            user_id: User ID
            action: Action type (upload, api)
            window_start: Start of current time window

        Returns:
            Redis key string
        """
        # Use hour-based windows: rate_limit:upload:123:2024-01-27-14
        timestamp = window_start.strftime("%Y-%m-%d-%H")
        return f"rate_limit:{action}:{user_id}:{timestamp}"

    def _get_limit(self, subscription_plan: str, action: str) -> int:
        """
        Get rate limit for subscription plan and action

        Args:
            subscription_plan: Subscription plan (free, starter, professional, enterprise)
            action: Action type (upload, api)

        Returns:
            Rate limit (requests per hour)
        """
        limits = self.UPLOAD_LIMITS if action == "upload" else self.API_LIMITS
        return limits.get(subscription_plan, limits[SubscriptionPlan.FREE.value])

    def check_rate_limit(
        self,
        user_id: int,
        subscription_plan: str,
        action: str = "upload"
    ) -> Tuple[bool, int, int]:
        """
        Check if user has exceeded rate limit

        Args:
            user_id: User ID
            subscription_plan: User's subscription plan
            action: Action type (upload, api)

        Returns:
            Tuple of (allowed, current_count, limit)

        Raises:
            RateLimitExceeded: If rate limit exceeded
        """
        now = datetime.utcnow()
        window_start = now.replace(minute=0, second=0, microsecond=0)
        key = self._get_key(user_id, action, window_start)
        limit = self._get_limit(subscription_plan, action)

        # Get current count from Redis
        try:
            current = self.redis_client.get(key)
            count = int(current) if current else 0
        except Exception as e:
            logger.error(f"Redis error checking rate limit: {e}")
            # Fail open - allow request if Redis is down
            return True, 0, limit

        # Check if limit exceeded
        if count >= limit:
            # Calculate retry_after (seconds until next hour)
            next_window = window_start + timedelta(hours=1)
            retry_after = int((next_window - now).total_seconds())

            logger.warning(
                f"Rate limit exceeded for user {user_id}: "
                f"{count}/{limit} {action}s per hour"
            )
            raise RateLimitExceeded(limit=limit, window="hour", retry_after=retry_after)

        return True, count, limit

    def increment_rate_limit(
        self,
        user_id: int,
        subscription_plan: str,
        action: str = "upload",
        amount: int = 1
    ) -> int:
        """
        Increment rate limit counter for user

        Args:
            user_id: User ID
            subscription_plan: User's subscription plan
            action: Action type (upload, api)
            amount: Amount to increment (default: 1)

        Returns:
            New count value
        """
        now = datetime.utcnow()
        window_start = now.replace(minute=0, second=0, microsecond=0)
        key = self._get_key(user_id, action, window_start)

        try:
            # Increment counter
            new_count = self.redis_client.incr(key, amount)

            # Set expiry to end of next hour (2 hours from window start)
            # This ensures the key persists through the entire window
            if new_count == amount:  # First increment, set expiry
                expiry = int((window_start + timedelta(hours=2) - now).total_seconds())
                self.redis_client.expire(key, expiry)

            logger.debug(
                f"Rate limit incremented for user {user_id}: "
                f"{new_count} {action}s in current hour"
            )

            return new_count

        except Exception as e:
            logger.error(f"Redis error incrementing rate limit: {e}")
            return 0

    def get_remaining(
        self,
        user_id: int,
        subscription_plan: str,
        action: str = "upload"
    ) -> Tuple[int, int]:
        """
        Get remaining requests in current window

        Args:
            user_id: User ID
            subscription_plan: User's subscription plan
            action: Action type (upload, api)

        Returns:
            Tuple of (remaining, limit)
        """
        now = datetime.utcnow()
        window_start = now.replace(minute=0, second=0, microsecond=0)
        key = self._get_key(user_id, action, window_start)
        limit = self._get_limit(subscription_plan, action)

        try:
            current = self.redis_client.get(key)
            count = int(current) if current else 0
            remaining = max(0, limit - count)
            return remaining, limit
        except Exception as e:
            logger.error(f"Redis error getting remaining: {e}")
            return limit, limit

    def reset_user_limits(self, user_id: int, action: Optional[str] = None):
        """
        Reset rate limits for user (admin function)

        Args:
            user_id: User ID
            action: Optional action type to reset (if None, resets all)
        """
        now = datetime.utcnow()
        window_start = now.replace(minute=0, second=0, microsecond=0)

        actions = [action] if action else ["upload", "api"]

        for action_type in actions:
            key = self._get_key(user_id, action_type, window_start)
            try:
                self.redis_client.delete(key)
                logger.info(f"Reset rate limit for user {user_id}, action: {action_type}")
            except Exception as e:
                logger.error(f"Redis error resetting limit: {e}")
