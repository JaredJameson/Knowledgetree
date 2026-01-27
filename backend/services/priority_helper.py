"""
KnowledgeTree - Priority Helper
Map subscription plans to Celery task priorities
"""

from models.subscription import SubscriptionPlan


# Celery priority levels (0-9, higher is more important)
PRIORITY_LEVELS = {
    SubscriptionPlan.FREE.value: 3,         # Low priority
    SubscriptionPlan.STARTER.value: 5,      # Normal priority
    SubscriptionPlan.PROFESSIONAL.value: 7,  # High priority
    SubscriptionPlan.ENTERPRISE.value: 9,    # Highest priority
}


def get_task_priority(subscription_plan: str) -> int:
    """
    Get Celery task priority for subscription plan

    Args:
        subscription_plan: User's subscription plan (free, starter, professional, enterprise)

    Returns:
        Priority level (0-9, higher is more important)
    """
    return PRIORITY_LEVELS.get(subscription_plan, PRIORITY_LEVELS[SubscriptionPlan.FREE.value])


def get_priority_name(priority: int) -> str:
    """
    Get human-readable name for priority level

    Args:
        priority: Priority level (0-9)

    Returns:
        Priority name (lowest, low, normal, high, highest)
    """
    if priority <= 2:
        return "lowest"
    elif priority <= 4:
        return "low"
    elif priority <= 6:
        return "normal"
    elif priority <= 8:
        return "high"
    else:
        return "highest"
