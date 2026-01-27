"""
Celery Worker Entry Point
This file MUST be the entry point for celery worker to ensure
eventlet monkey patching happens before any other imports
"""

# CRITICAL: This MUST be the FIRST thing that runs
import eventlet
eventlet.monkey_patch()

# Now safe to import celery app
from core.celery_app import celery_app

__all__ = ["celery_app"]
