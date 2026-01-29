"""
KnowledgeTree - Celery Configuration
Background task processing for agent workflows
"""

import os
from celery import Celery

# Get Redis URL from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "knowledgetree",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "services.workflow_tasks",
        "services.document_tasks",
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Priority queue support (Redis broker)
    # Priorities: 0 (lowest) to 9 (highest)
    # Subscription tier mapping:
    #   FREE: priority 3 (low)
    #   STARTER: priority 5 (normal)
    #   PROFESSIONAL: priority 7 (high)
    #   ENTERPRISE: priority 9 (highest)
    broker_transport_options={
        "priority_steps": list(range(10)),  # Enable priorities 0-9
        "sep": ":",
        "queue_order_strategy": "priority",
    },
    task_default_priority=5,  # Default to normal priority

    # Task routing
    task_routes={
        "services.workflow_tasks.execute_workflow": {"queue": "workflows"},
        "services.workflow_tasks.execute_research": {"queue": "research"},
        "services.workflow_tasks.execute_scraping": {"queue": "scraping"},
        "services.document_tasks.process_document_task": {"queue": "documents"},
        "services.document_tasks.process_agentic_crawl_task": {"queue": "workflows"},
    },

    # Task result settings
    result_expires=3600,  # 1 hour
    task_track_started=True,

    # Worker settings
    worker_prefetch_multiplier=4,
    worker_concurrency=4,

    # Retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Task time limits
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3000,  # 50 minutes soft limit
)


# Periodic tasks (if needed later)
# from celery.schedules import crontab
#
# celery_app.conf.beat_schedule = {
#     "cleanup-old-workflows": {
#         "task": "services.workflow_tasks.cleanup_old_workflows",
#         "schedule": crontab(hour=2, minute=0),  # 2 AM daily
#     },
# }
