"""
API integration tests for analytics endpoints
"""

import pytest
from datetime import date, datetime, timedelta
from httpx import AsyncClient

from models.activity import ActivityEvent, DailyMetric
from services.activity_tracker import ActivityTracker, EventType


@pytest.mark.asyncio
class TestAnalyticsMetricsEndpoint:
    """Test /analytics/metrics/{project_id} endpoint"""

    async def test_get_metrics_success(
        self, client: AsyncClient, db_session, test_project, test_user, auth_headers
    ):
        """Test successful retrieval of daily metrics"""
        # Create some daily metrics
        today = date.today()
        for i in range(5):
            metric_date = today - timedelta(days=i)
            metric = DailyMetric(
                project_id=test_project.id,
                metric_date=metric_date,
                documents_uploaded=i + 1,
                searches_performed=(i + 1) * 2,
                chat_messages_sent=(i + 1) * 3,
                insights_generated=i,
                active_users=1
            )
            db_session.add(metric)

        await db_session.commit()

        # Request metrics
        response = await client.get(
            f"/api/v1/analytics/metrics/{test_project.id}",
            params={"days": 7},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["project_id"] == test_project.id
        assert data["period_days"] == 7
        assert isinstance(data["metrics"], list)
        assert len(data["metrics"]) == 5  # We created 5 days of metrics

        # Verify totals are calculated
        assert "total_documents" in data
        assert "total_searches" in data
        assert "total_messages" in data
        assert "total_insights" in data

        # Verify metric structure
        first_metric = data["metrics"][0]
        assert "date" in first_metric
        assert "documents_uploaded" in first_metric
        assert "searches_performed" in first_metric
        assert "chat_messages_sent" in first_metric
        assert "insights_generated" in first_metric
        assert "active_users" in first_metric

    async def test_get_metrics_empty_project(
        self, client: AsyncClient, test_project, auth_headers
    ):
        """Test metrics for project with no activity"""
        response = await client.get(
            f"/api/v1/analytics/metrics/{test_project.id}",
            params={"days": 30},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["project_id"] == test_project.id
        assert data["metrics"] == []
        assert data["total_documents"] == 0
        assert data["total_searches"] == 0

    async def test_get_metrics_unauthorized(self, client: AsyncClient, test_project):
        """Test metrics endpoint without authentication"""
        response = await client.get(
            f"/api/v1/analytics/metrics/{test_project.id}",
            params={"days": 7}
        )

        assert response.status_code == 401

    async def test_get_metrics_invalid_project(
        self, client: AsyncClient, auth_headers
    ):
        """Test metrics for non-existent project"""
        response = await client.get(
            "/api/v1/analytics/metrics/99999",
            params={"days": 7},
            headers=auth_headers
        )

        assert response.status_code == 404

    async def test_get_metrics_invalid_days_parameter(
        self, client: AsyncClient, test_project, auth_headers
    ):
        """Test metrics with invalid days parameter"""
        # Days too small
        response = await client.get(
            f"/api/v1/analytics/metrics/{test_project.id}",
            params={"days": 0},
            headers=auth_headers
        )
        assert response.status_code == 422

        # Days too large
        response = await client.get(
            f"/api/v1/analytics/metrics/{test_project.id}",
            params={"days": 400},
            headers=auth_headers
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestAnalyticsActivityEndpoint:
    """Test /analytics/activity/{project_id} endpoint"""

    async def test_get_activity_success(
        self, client: AsyncClient, db_session, test_project, test_user, auth_headers
    ):
        """Test successful retrieval of activity feed"""
        tracker = ActivityTracker(db_session)

        # Create various activity events
        await tracker.record_document_upload(
            user_id=test_user.id,
            project_id=test_project.id,
            document_id=1,
            filename="doc1.pdf",
            size_bytes=1024
        )

        await tracker.record_search(
            user_id=test_user.id,
            project_id=test_project.id,
            query="test query",
            results_count=5,
            search_type="semantic"
        )

        await tracker.record_chat_message(
            user_id=test_user.id,
            project_id=test_project.id,
            conversation_id=1,
            message_id=1
        )

        await db_session.commit()

        # Request activity feed
        response = await client.get(
            f"/api/v1/analytics/activity/{test_project.id}",
            params={"limit": 50, "offset": 0},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["project_id"] == test_project.id
        assert isinstance(data["activities"], list)
        assert len(data["activities"]) == 3
        assert data["total_count"] == 3
        assert data["limit"] == 50
        assert data["offset"] == 0

        # Verify activity structure
        activity = data["activities"][0]
        assert "id" in activity
        assert "user_id" in activity
        assert "event_type" in activity
        assert "event_data" in activity
        assert "created_at" in activity

    async def test_get_activity_pagination(
        self, client: AsyncClient, db_session, test_project, test_user, auth_headers
    ):
        """Test activity feed pagination"""
        tracker = ActivityTracker(db_session)

        # Create 10 events
        for i in range(10):
            await tracker.record_document_upload(
                user_id=test_user.id,
                project_id=test_project.id,
                document_id=i,
                filename=f"doc{i}.pdf",
                size_bytes=1024
            )

        await db_session.commit()

        # First page (5 items)
        response = await client.get(
            f"/api/v1/analytics/activity/{test_project.id}",
            params={"limit": 5, "offset": 0},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["activities"]) == 5
        assert data["total_count"] == 10

        # Second page (5 items)
        response = await client.get(
            f"/api/v1/analytics/activity/{test_project.id}",
            params={"limit": 5, "offset": 5},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["activities"]) == 5
        assert data["total_count"] == 10

    async def test_get_activity_empty_project(
        self, client: AsyncClient, test_project, auth_headers
    ):
        """Test activity feed for project with no activity"""
        response = await client.get(
            f"/api/v1/analytics/activity/{test_project.id}",
            params={"limit": 50, "offset": 0},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["activities"] == []
        assert data["total_count"] == 0


@pytest.mark.asyncio
class TestAnalyticsQualityScoreEndpoint:
    """Test /analytics/quality-score/{project_id} endpoint"""

    async def test_get_quality_score_with_activity(
        self, client: AsyncClient, db_session, test_project, test_user, auth_headers
    ):
        """Test quality score calculation with various activities"""
        tracker = ActivityTracker(db_session)

        # Create activity for past 7 days
        today = datetime.utcnow()
        for i in range(7):
            # 2 documents per day
            for j in range(2):
                await tracker.record_document_upload(
                    user_id=test_user.id,
                    project_id=test_project.id,
                    document_id=i * 10 + j,
                    filename=f"doc{i}_{j}.pdf",
                    size_bytes=1024
                )

            # 10 searches per day
            for j in range(10):
                await tracker.record_search(
                    user_id=test_user.id,
                    project_id=test_project.id,
                    query=f"query {i}_{j}",
                    results_count=5,
                    search_type="semantic"
                )

            # 5 chat messages per day
            for j in range(5):
                await tracker.record_chat_message(
                    user_id=test_user.id,
                    project_id=test_project.id,
                    conversation_id=1,
                    message_id=i * 10 + j
                )

        await db_session.commit()

        # Request quality score
        response = await client.get(
            f"/api/v1/analytics/quality-score/{test_project.id}",
            params={"days": 7},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["project_id"] == test_project.id
        assert data["period_days"] == 7
        assert "overall_score" in data
        assert "document_score" in data
        assert "search_score" in data
        assert "chat_score" in data
        assert "diversity_score" in data

        # Verify scores are in valid range (0-100)
        assert 0 <= data["overall_score"] <= 100
        assert 0 <= data["document_score"] <= 100
        assert 0 <= data["search_score"] <= 100
        assert 0 <= data["chat_score"] <= 100
        assert 0 <= data["diversity_score"] <= 100

        # With high activity, scores should be good
        assert data["document_score"] == 100  # 2 docs/day >= 1 target
        assert data["search_score"] == 100  # 10 searches/day >= 5 target
        assert data["chat_score"] == 100  # 5 messages/day >= 3 target

        # Verify metrics
        assert "metrics" in data
        assert data["metrics"]["total_documents"] == 14  # 2 * 7
        assert data["metrics"]["total_searches"] == 70  # 10 * 7
        assert data["metrics"]["total_messages"] == 35  # 5 * 7

    async def test_get_quality_score_low_activity(
        self, client: AsyncClient, db_session, test_project, test_user, auth_headers
    ):
        """Test quality score with minimal activity"""
        tracker = ActivityTracker(db_session)

        # Create minimal activity (below thresholds)
        await tracker.record_document_upload(
            user_id=test_user.id,
            project_id=test_project.id,
            document_id=1,
            filename="doc.pdf",
            size_bytes=1024
        )

        await db_session.commit()

        # Request quality score
        response = await client.get(
            f"/api/v1/analytics/quality-score/{test_project.id}",
            params={"days": 7},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # With minimal activity over 7 days, scores should be low
        assert data["overall_score"] < 50
        assert data["document_score"] < 100  # Less than 1/day
        assert data["search_score"] == 0  # No searches
        assert data["chat_score"] == 0  # No messages

    async def test_get_quality_score_no_activity(
        self, client: AsyncClient, test_project, auth_headers
    ):
        """Test quality score for project with no activity"""
        response = await client.get(
            f"/api/v1/analytics/quality-score/{test_project.id}",
            params={"days": 7},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # All scores should be 0
        assert data["overall_score"] == 0
        assert data["document_score"] == 0
        assert data["search_score"] == 0
        assert data["chat_score"] == 0
        assert data["diversity_score"] == 0


@pytest.mark.asyncio
class TestAnalyticsTrendsEndpoint:
    """Test /analytics/trends/{project_id} endpoint"""

    async def test_get_trends_with_data(
        self, client: AsyncClient, db_session, test_project, test_user, auth_headers
    ):
        """Test trends calculation with comparison periods"""
        tracker = ActivityTracker(db_session)

        # Create activity for current period (last 30 days)
        today = datetime.utcnow()
        for i in range(30):
            await tracker.record_document_upload(
                user_id=test_user.id,
                project_id=test_project.id,
                document_id=i,
                filename=f"doc{i}.pdf",
                size_bytes=1024
            )

        # Create less activity for previous period (30-60 days ago)
        for i in range(15):
            event_date = today - timedelta(days=45 + i)
            event = ActivityEvent(
                user_id=test_user.id,
                project_id=test_project.id,
                event_type=EventType.DOCUMENT_UPLOADED.value,
                event_data={"document_id": 100 + i, "filename": f"old_doc{i}.pdf"},
                created_at=event_date
            )
            db_session.add(event)

        await db_session.commit()

        # Request trends
        response = await client.get(
            f"/api/v1/analytics/trends/{test_project.id}",
            params={"days": 30},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["project_id"] == test_project.id
        assert data["period_days"] == 30

        # Verify trend data structure
        assert "documents_uploaded" in data
        doc_trend = data["documents_uploaded"]
        assert "current" in doc_trend
        assert "previous" in doc_trend
        assert "change_percent" in doc_trend

        # With 30 docs in current period vs 15 in previous, should show positive growth
        assert doc_trend["current"] == 30
        assert doc_trend["previous"] == 15
        assert doc_trend["change_percent"] == 100.0  # (30-15)/15 * 100 = 100%

    async def test_get_trends_no_previous_data(
        self, client: AsyncClient, db_session, test_project, test_user, auth_headers
    ):
        """Test trends when there's no previous period data"""
        tracker = ActivityTracker(db_session)

        # Create activity only in current period
        for i in range(10):
            await tracker.record_document_upload(
                user_id=test_user.id,
                project_id=test_project.id,
                document_id=i,
                filename=f"doc{i}.pdf",
                size_bytes=1024
            )

        await db_session.commit()

        # Request trends
        response = await client.get(
            f"/api/v1/analytics/trends/{test_project.id}",
            params={"days": 30},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        doc_trend = data["documents_uploaded"]
        assert doc_trend["current"] == 10
        assert doc_trend["previous"] == 0
        assert doc_trend["change_percent"] == 0.0  # No previous data = 0% change

    async def test_get_trends_negative_growth(
        self, client: AsyncClient, db_session, test_project, test_user, auth_headers
    ):
        """Test trends showing decline"""
        today = datetime.utcnow()

        # Create more activity in previous period (30-60 days ago)
        for i in range(50):
            event_date = today - timedelta(days=45 + (i % 30))
            event = ActivityEvent(
                user_id=test_user.id,
                project_id=test_project.id,
                event_type=EventType.SEARCH_PERFORMED.value,
                event_data={"query": f"search{i}", "results_count": 5},
                created_at=event_date
            )
            db_session.add(event)

        # Create less activity in current period (last 30 days)
        tracker = ActivityTracker(db_session)
        for i in range(25):
            await tracker.record_search(
                user_id=test_user.id,
                project_id=test_project.id,
                query=f"new_search{i}",
                results_count=5,
                search_type="semantic"
            )

        await db_session.commit()

        # Request trends
        response = await client.get(
            f"/api/v1/analytics/trends/{test_project.id}",
            params={"days": 30},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        search_trend = data["searches_performed"]
        assert search_trend["current"] == 25
        assert search_trend["previous"] == 50
        assert search_trend["change_percent"] == -50.0  # (25-50)/50 * 100 = -50%


@pytest.mark.asyncio
class TestAnalyticsAccessControl:
    """Test access control for analytics endpoints"""

    async def test_cannot_access_other_user_project(
        self, client: AsyncClient, db_session, test_project, second_user_headers
    ):
        """Test that users cannot access analytics for projects they don't own"""
        # second_user_headers belongs to a different user than test_project owner

        # Try to access metrics
        response = await client.get(
            f"/api/v1/analytics/metrics/{test_project.id}",
            params={"days": 7},
            headers=second_user_headers
        )
        assert response.status_code == 404  # Project not found for this user

        # Try to access activity
        response = await client.get(
            f"/api/v1/analytics/activity/{test_project.id}",
            params={"limit": 50, "offset": 0},
            headers=second_user_headers
        )
        assert response.status_code == 404

        # Try to access quality score
        response = await client.get(
            f"/api/v1/analytics/quality-score/{test_project.id}",
            params={"days": 7},
            headers=second_user_headers
        )
        assert response.status_code == 404

        # Try to access trends
        response = await client.get(
            f"/api/v1/analytics/trends/{test_project.id}",
            params={"days": 30},
            headers=second_user_headers
        )
        assert response.status_code == 404
