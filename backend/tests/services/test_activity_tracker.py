"""
Unit tests for ActivityTracker service
"""

import pytest
from datetime import datetime
from sqlalchemy import select

from services.activity_tracker import ActivityTracker, EventType
from models.activity import ActivityEvent


@pytest.mark.asyncio
class TestActivityTracker:
    """Test suite for ActivityTracker service"""

    async def test_record_event_basic(self, db_session, test_user, test_project):
        """Test recording a basic activity event"""
        tracker = ActivityTracker(db_session)

        event = await tracker.record_event(
            user_id=test_user.id,
            event_type=EventType.DOCUMENT_UPLOADED,
            event_data={"filename": "test.pdf", "size_bytes": 1024},
            project_id=test_project.id
        )

        await db_session.commit()

        # Verify event was created
        assert event is not None
        assert event.id is not None
        assert event.user_id == test_user.id
        assert event.project_id == test_project.id
        assert event.event_type == EventType.DOCUMENT_UPLOADED.value
        assert event.event_data["filename"] == "test.pdf"
        assert event.event_data["size_bytes"] == 1024
        assert isinstance(event.created_at, datetime)

    async def test_record_event_without_project(self, db_session, test_user):
        """Test recording an event without project association"""
        tracker = ActivityTracker(db_session)

        event = await tracker.record_event(
            user_id=test_user.id,
            event_type=EventType.INSIGHT_GENERATED,
            event_data={"insight_type": "summary", "tokens_used": 500},
            project_id=None
        )

        await db_session.commit()

        # Verify event was created without project
        assert event is not None
        assert event.project_id is None
        assert event.event_data["insight_type"] == "summary"

    async def test_record_document_upload(self, db_session, test_user, test_project):
        """Test convenience method for document upload"""
        tracker = ActivityTracker(db_session)

        event = await tracker.record_document_upload(
            user_id=test_user.id,
            project_id=test_project.id,
            document_id=123,
            filename="document.pdf",
            size_bytes=2048,
            processing_time_ms=500
        )

        await db_session.commit()

        # Verify document upload event
        assert event.event_type == EventType.DOCUMENT_UPLOADED.value
        assert event.event_data["document_id"] == 123
        assert event.event_data["filename"] == "document.pdf"
        assert event.event_data["size_bytes"] == 2048
        assert event.event_data["processing_time_ms"] == 500

    async def test_record_search(self, db_session, test_user, test_project):
        """Test convenience method for search activity"""
        tracker = ActivityTracker(db_session)

        event = await tracker.record_search(
            user_id=test_user.id,
            project_id=test_project.id,
            query="test query",
            results_count=5,
            search_type="semantic",
            response_time_ms=250
        )

        await db_session.commit()

        # Verify search event
        assert event.event_type == EventType.SEARCH_PERFORMED.value
        assert event.event_data["query"] == "test query"
        assert event.event_data["results_count"] == 5
        assert event.event_data["search_type"] == "semantic"
        assert event.event_data["response_time_ms"] == 250

    async def test_record_chat_message(self, db_session, test_user, test_project):
        """Test convenience method for chat message"""
        tracker = ActivityTracker(db_session)

        event = await tracker.record_chat_message(
            user_id=test_user.id,
            project_id=test_project.id,
            conversation_id=456,
            message_id=789,
            tokens_used=1000,
            response_time_ms=1500
        )

        await db_session.commit()

        # Verify chat message event
        assert event.event_type == EventType.CHAT_MESSAGE_SENT.value
        assert event.event_data["conversation_id"] == 456
        assert event.event_data["message_id"] == 789
        assert event.event_data["tokens_used"] == 1000
        assert event.event_data["response_time_ms"] == 1500

    async def test_record_insight_generation(self, db_session, test_user, test_project):
        """Test convenience method for insight generation"""
        tracker = ActivityTracker(db_session)

        event = await tracker.record_insight_generation(
            user_id=test_user.id,
            project_id=test_project.id,
            insight_type="summary",
            document_id=999,
            tokens_used=500
        )

        await db_session.commit()

        # Verify insight generation event
        assert event.event_type == EventType.INSIGHT_GENERATED.value
        assert event.event_data["insight_type"] == "summary"
        assert event.event_data["document_id"] == 999
        assert event.event_data["tokens_used"] == 500

    async def test_multiple_events_same_user(self, db_session, test_user, test_project):
        """Test recording multiple events for the same user"""
        tracker = ActivityTracker(db_session)

        # Record 3 different events
        event1 = await tracker.record_document_upload(
            user_id=test_user.id,
            project_id=test_project.id,
            document_id=1,
            filename="doc1.pdf",
            size_bytes=1024
        )

        event2 = await tracker.record_search(
            user_id=test_user.id,
            project_id=test_project.id,
            query="search 1",
            results_count=5,
            search_type="semantic"
        )

        event3 = await tracker.record_chat_message(
            user_id=test_user.id,
            project_id=test_project.id,
            conversation_id=1,
            message_id=1
        )

        await db_session.commit()

        # Query all events for this user
        result = await db_session.execute(
            select(ActivityEvent)
            .where(ActivityEvent.user_id == test_user.id)
            .order_by(ActivityEvent.created_at)
        )
        events = result.scalars().all()

        # Verify all 3 events were recorded
        assert len(events) == 3
        assert events[0].id == event1.id
        assert events[1].id == event2.id
        assert events[2].id == event3.id

    async def test_event_data_jsonb_structure(self, db_session, test_user, test_project):
        """Test JSONB storage and retrieval of complex event data"""
        tracker = ActivityTracker(db_session)

        complex_data = {
            "filename": "complex.pdf",
            "metadata": {
                "author": "Test Author",
                "pages": 100,
                "categories": ["cat1", "cat2", "cat3"]
            },
            "processing": {
                "time_ms": 5000,
                "chunks_created": 50
            }
        }

        event = await tracker.record_event(
            user_id=test_user.id,
            event_type=EventType.DOCUMENT_UPLOADED,
            event_data=complex_data,
            project_id=test_project.id
        )

        await db_session.commit()
        await db_session.refresh(event)

        # Verify complex JSONB structure is preserved
        assert event.event_data["filename"] == "complex.pdf"
        assert event.event_data["metadata"]["author"] == "Test Author"
        assert event.event_data["metadata"]["pages"] == 100
        assert len(event.event_data["metadata"]["categories"]) == 3
        assert event.event_data["processing"]["time_ms"] == 5000
        assert event.event_data["processing"]["chunks_created"] == 50

    async def test_events_cascade_delete_with_user(self, db_session, test_user, test_project):
        """Test that events are deleted when user is deleted (CASCADE)"""
        tracker = ActivityTracker(db_session)

        # Create some events
        await tracker.record_document_upload(
            user_id=test_user.id,
            project_id=test_project.id,
            document_id=1,
            filename="doc.pdf",
            size_bytes=1024
        )

        await db_session.commit()

        # Verify event exists
        result = await db_session.execute(
            select(ActivityEvent).where(ActivityEvent.user_id == test_user.id)
        )
        events_before = result.scalars().all()
        assert len(events_before) == 1

        # Delete user
        await db_session.delete(test_user)
        await db_session.commit()

        # Verify events were cascade deleted
        result = await db_session.execute(
            select(ActivityEvent).where(ActivityEvent.user_id == test_user.id)
        )
        events_after = result.scalars().all()
        assert len(events_after) == 0

    async def test_events_cascade_delete_with_project(self, db_session, test_user, test_project):
        """Test that events are deleted when project is deleted (CASCADE)"""
        tracker = ActivityTracker(db_session)

        # Create some events
        await tracker.record_search(
            user_id=test_user.id,
            project_id=test_project.id,
            query="test",
            results_count=3,
            search_type="semantic"
        )

        await db_session.commit()

        # Verify event exists
        result = await db_session.execute(
            select(ActivityEvent).where(ActivityEvent.project_id == test_project.id)
        )
        events_before = result.scalars().all()
        assert len(events_before) == 1

        # Delete project
        await db_session.delete(test_project)
        await db_session.commit()

        # Verify events were cascade deleted
        result = await db_session.execute(
            select(ActivityEvent).where(ActivityEvent.project_id == test_project.id)
        )
        events_after = result.scalars().all()
        assert len(events_after) == 0
