"""
KnowledgeTree - Activity Tracking Service
Records user actions and system events for analytics
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession

from models.activity import ActivityEvent

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Standard activity event types"""
    # Document operations
    DOCUMENT_UPLOADED = "document.uploaded"
    DOCUMENT_DELETED = "document.deleted"
    DOCUMENT_VIEWED = "document.viewed"
    DOCUMENT_EXPORTED = "document.exported"

    # Search operations
    SEARCH_PERFORMED = "search.performed"
    SEARCH_FILTERED = "search.filtered"

    # Chat operations
    CHAT_MESSAGE_SENT = "chat.message_sent"
    CHAT_CONVERSATION_STARTED = "chat.conversation_started"
    CHAT_CONVERSATION_DELETED = "chat.conversation_deleted"

    # Category operations
    CATEGORY_CREATED = "category.created"
    CATEGORY_UPDATED = "category.updated"
    CATEGORY_DELETED = "category.deleted"
    CATEGORY_TREE_GENERATED = "category.tree_generated"

    # Insight operations
    INSIGHT_GENERATED = "insight.generated"
    INSIGHT_VIEWED = "insight.viewed"

    # Project operations
    PROJECT_CREATED = "project.created"
    PROJECT_UPDATED = "project.updated"
    PROJECT_DELETED = "project.deleted"

    # Workflow operations
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"

    # Crawl operations
    CRAWL_STARTED = "crawl.started"
    CRAWL_COMPLETED = "crawl.completed"
    CRAWL_FAILED = "crawl.failed"

    # Authentication operations
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_REGISTERED = "user.registered"


class ActivityTracker:
    """
    Service for tracking user activity and system events.

    Records events to the activity_events table for:
    - Real-time activity feeds
    - Usage analytics
    - Audit trails
    - Daily metrics aggregation

    Example:
        tracker = ActivityTracker(db_session)
        await tracker.record_event(
            user_id=1,
            project_id=5,
            event_type=EventType.DOCUMENT_UPLOADED,
            event_data={
                "document_id": 123,
                "filename": "report.pdf",
                "size_bytes": 1024000,
                "processing_time_ms": 5000
            }
        )
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize activity tracker with database session.

        Args:
            db: AsyncSession for database operations
        """
        self.db = db

    async def record_event(
        self,
        user_id: int,
        event_type: EventType,
        event_data: Dict[str, Any],
        project_id: Optional[int] = None,
    ) -> ActivityEvent:
        """
        Record a single activity event.

        Args:
            user_id: User who performed the action
            event_type: Type of event (use EventType enum)
            event_data: Event-specific data (JSON-serializable dict)
            project_id: Optional project context

        Returns:
            Created ActivityEvent instance

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            event = ActivityEvent(
                user_id=user_id,
                project_id=project_id,
                event_type=event_type.value,
                event_data=event_data,
                created_at=datetime.utcnow()
            )

            self.db.add(event)
            await self.db.flush()  # Get the ID without committing

            logger.debug(
                f"Recorded event: {event_type.value} for user {user_id} "
                f"(project: {project_id}, event_id: {event.id})"
            )

            return event

        except Exception as e:
            logger.error(
                f"Failed to record event {event_type.value} for user {user_id}: {str(e)}"
            )
            raise

    async def record_document_upload(
        self,
        user_id: int,
        project_id: int,
        document_id: int,
        filename: str,
        size_bytes: int,
        processing_time_ms: Optional[int] = None
    ) -> ActivityEvent:
        """
        Record document upload event.

        Args:
            user_id: User who uploaded the document
            project_id: Project the document belongs to
            document_id: ID of the uploaded document
            filename: Original filename
            size_bytes: File size in bytes
            processing_time_ms: Optional processing time in milliseconds

        Returns:
            Created ActivityEvent instance
        """
        event_data = {
            "document_id": document_id,
            "filename": filename,
            "size_bytes": size_bytes,
        }
        if processing_time_ms is not None:
            event_data["processing_time_ms"] = processing_time_ms

        return await self.record_event(
            user_id=user_id,
            project_id=project_id,
            event_type=EventType.DOCUMENT_UPLOADED,
            event_data=event_data
        )

    async def record_search(
        self,
        user_id: int,
        project_id: int,
        query: str,
        results_count: int,
        search_type: str = "hybrid",
        response_time_ms: Optional[int] = None
    ) -> ActivityEvent:
        """
        Record search operation event.

        Args:
            user_id: User who performed the search
            project_id: Project context
            query: Search query string
            results_count: Number of results returned
            search_type: Type of search (hybrid, semantic, keyword)
            response_time_ms: Optional search response time

        Returns:
            Created ActivityEvent instance
        """
        event_data = {
            "query": query,
            "results_count": results_count,
            "search_type": search_type,
        }
        if response_time_ms is not None:
            event_data["response_time_ms"] = response_time_ms

        return await self.record_event(
            user_id=user_id,
            project_id=project_id,
            event_type=EventType.SEARCH_PERFORMED,
            event_data=event_data
        )

    async def record_chat_message(
        self,
        user_id: int,
        project_id: int,
        conversation_id: int,
        message_id: int,
        tokens_used: Optional[int] = None,
        response_time_ms: Optional[int] = None
    ) -> ActivityEvent:
        """
        Record chat message sent event.

        Args:
            user_id: User who sent the message
            project_id: Project context
            conversation_id: ID of the conversation
            message_id: ID of the message
            tokens_used: Optional token count
            response_time_ms: Optional response time

        Returns:
            Created ActivityEvent instance
        """
        event_data = {
            "conversation_id": conversation_id,
            "message_id": message_id,
        }
        if tokens_used is not None:
            event_data["tokens_used"] = tokens_used
        if response_time_ms is not None:
            event_data["response_time_ms"] = response_time_ms

        return await self.record_event(
            user_id=user_id,
            project_id=project_id,
            event_type=EventType.CHAT_MESSAGE_SENT,
            event_data=event_data
        )

    async def record_insight_generation(
        self,
        user_id: int,
        project_id: int,
        insight_type: str,
        data: Dict[str, Any]
    ) -> ActivityEvent:
        """
        Record insight generation event.

        Args:
            user_id: User who generated the insight
            project_id: Project context
            insight_type: Type of insight (summary, trends, patterns, etc.)
            data: Insight-specific data

        Returns:
            Created ActivityEvent instance
        """
        event_data = {
            "insight_type": insight_type,
            **data
        }

        return await self.record_event(
            user_id=user_id,
            project_id=project_id,
            event_type=EventType.INSIGHT_GENERATED,
            event_data=event_data
        )
