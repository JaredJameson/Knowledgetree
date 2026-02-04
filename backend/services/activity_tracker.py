"""
Activity Tracker Service
Records user and system activity events for analytics
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from models.activity import ActivityEvent


class EventType(str, Enum):
    """Standard activity event types"""

    # Document events
    DOCUMENT_UPLOADED = "document.uploaded"
    DOCUMENT_DELETED = "document.deleted"
    DOCUMENT_PROCESSED = "document.processed"

    # Search events
    SEARCH_PERFORMED = "search.performed"

    # Chat events
    CHAT_MESSAGE_SENT = "chat.message_sent"
    CHAT_CONVERSATION_CREATED = "chat.conversation_created"
    CHAT_CONVERSATION_DELETED = "chat.conversation_deleted"

    # Insight events
    INSIGHT_GENERATED = "insight.generated"

    # Category events
    CATEGORY_CREATED = "category.created"
    CATEGORY_UPDATED = "category.updated"
    CATEGORY_DELETED = "category.deleted"
    CATEGORY_TREE_GENERATED = "category.tree_generated"

    # Project events
    PROJECT_CREATED = "project.created"
    PROJECT_UPDATED = "project.updated"
    PROJECT_DELETED = "project.deleted"

    # User events
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_REGISTERED = "user.registered"


class ActivityTracker:
    """Service for tracking user and system activity"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_event(
        self,
        user_id: int,
        event_type: EventType,
        event_data: Dict[str, Any],
        project_id: Optional[int] = None
    ) -> ActivityEvent:
        """
        Record a single activity event.

        Args:
            user_id: ID of the user performing the action
            event_type: Type of event from EventType enum
            event_data: JSONB data with event-specific information
            project_id: Optional project association

        Returns:
            Created ActivityEvent instance
        """
        event = ActivityEvent(
            user_id=user_id,
            project_id=project_id,
            event_type=event_type.value,
            event_data=event_data,
            created_at=datetime.utcnow()
        )

        self.db.add(event)
        await self.db.flush()

        return event

    async def record_document_upload(
        self,
        user_id: int,
        project_id: int,
        document_id: int,
        filename: str,
        size_bytes: int,
        processing_time_ms: Optional[int] = None
    ) -> ActivityEvent:
        """Convenience method for document upload events"""
        event_data = {
            "document_id": document_id,
            "filename": filename,
            "size_bytes": size_bytes
        }

        if processing_time_ms is not None:
            event_data["processing_time_ms"] = processing_time_ms

        return await self.record_event(
            user_id=user_id,
            event_type=EventType.DOCUMENT_UPLOADED,
            event_data=event_data,
            project_id=project_id
        )

    async def record_search(
        self,
        user_id: int,
        project_id: int,
        query: str,
        results_count: int,
        search_type: str,
        response_time_ms: Optional[int] = None
    ) -> ActivityEvent:
        """Convenience method for search events"""
        event_data = {
            "query": query,
            "results_count": results_count,
            "search_type": search_type
        }

        if response_time_ms is not None:
            event_data["response_time_ms"] = response_time_ms

        return await self.record_event(
            user_id=user_id,
            event_type=EventType.SEARCH_PERFORMED,
            event_data=event_data,
            project_id=project_id
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
        """Convenience method for chat message events"""
        event_data = {
            "conversation_id": conversation_id,
            "message_id": message_id
        }

        if tokens_used is not None:
            event_data["tokens_used"] = tokens_used

        if response_time_ms is not None:
            event_data["response_time_ms"] = response_time_ms

        return await self.record_event(
            user_id=user_id,
            event_type=EventType.CHAT_MESSAGE_SENT,
            event_data=event_data,
            project_id=project_id
        )

    async def record_insight_generation(
        self,
        user_id: int,
        project_id: int,
        insight_type: str,
        document_id: Optional[int] = None,
        tokens_used: Optional[int] = None
    ) -> ActivityEvent:
        """Convenience method for insight generation events"""
        event_data = {
            "insight_type": insight_type
        }

        if document_id is not None:
            event_data["document_id"] = document_id

        if tokens_used is not None:
            event_data["tokens_used"] = tokens_used

        return await self.record_event(
            user_id=user_id,
            event_type=EventType.INSIGHT_GENERATED,
            event_data=event_data,
            project_id=project_id
        )
