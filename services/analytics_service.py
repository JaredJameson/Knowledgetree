"""
KnowledgeTree - Analytics Service
Aggregates activity events into metrics and generates insights
"""

import logging
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, distinct, case
from sqlalchemy.dialects.postgresql import insert

from models.activity import ActivityEvent, DailyMetric
from models.document import Document
from models.conversation import Conversation

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Service for analytics and metrics aggregation.

    Provides methods for:
    - Aggregating activity events into daily metrics
    - Calculating usage trends over time
    - Computing quality scores based on activity patterns
    - Real-time activity feed generation

    Example:
        service = AnalyticsService()
        await service.aggregate_daily_metrics(db, project_id=5, date=date.today())
        metrics = await service.get_metrics_for_period(db, project_id=5, days=30)
    """

    async def aggregate_daily_metrics(
        self,
        db: AsyncSession,
        project_id: int,
        target_date: date
    ) -> DailyMetric:
        """
        Aggregate activity events into daily metrics for a specific date.

        This method:
        1. Counts events by type for the target date
        2. Calculates unique active users
        3. Upserts into daily_metrics table

        Args:
            db: Database session
            project_id: Project to aggregate metrics for
            target_date: Date to aggregate (usually today or yesterday)

        Returns:
            DailyMetric instance with aggregated data

        Note:
            Should be run daily (e.g., via cron job or Celery beat)
            to keep metrics up to date.
        """
        try:
            # Define date range for the target date
            start_datetime = datetime.combine(target_date, datetime.min.time())
            end_datetime = datetime.combine(target_date, datetime.max.time())

            # Count documents uploaded
            documents_query = await db.execute(
                select(func.count(ActivityEvent.id))
                .where(
                    and_(
                        ActivityEvent.project_id == project_id,
                        ActivityEvent.event_type == "document.uploaded",
                        ActivityEvent.created_at >= start_datetime,
                        ActivityEvent.created_at <= end_datetime
                    )
                )
            )
            documents_uploaded = documents_query.scalar() or 0

            # Count searches performed
            searches_query = await db.execute(
                select(func.count(ActivityEvent.id))
                .where(
                    and_(
                        ActivityEvent.project_id == project_id,
                        ActivityEvent.event_type == "search.performed",
                        ActivityEvent.created_at >= start_datetime,
                        ActivityEvent.created_at <= end_datetime
                    )
                )
            )
            searches_performed = searches_query.scalar() or 0

            # Count chat messages sent
            messages_query = await db.execute(
                select(func.count(ActivityEvent.id))
                .where(
                    and_(
                        ActivityEvent.project_id == project_id,
                        ActivityEvent.event_type == "chat.message_sent",
                        ActivityEvent.created_at >= start_datetime,
                        ActivityEvent.created_at <= end_datetime
                    )
                )
            )
            chat_messages_sent = messages_query.scalar() or 0

            # Count insights generated
            insights_query = await db.execute(
                select(func.count(ActivityEvent.id))
                .where(
                    and_(
                        ActivityEvent.project_id == project_id,
                        ActivityEvent.event_type == "insight.generated",
                        ActivityEvent.created_at >= start_datetime,
                        ActivityEvent.created_at <= end_datetime
                    )
                )
            )
            insights_generated = insights_query.scalar() or 0

            # Count unique active users
            users_query = await db.execute(
                select(func.count(distinct(ActivityEvent.user_id)))
                .where(
                    and_(
                        ActivityEvent.project_id == project_id,
                        ActivityEvent.created_at >= start_datetime,
                        ActivityEvent.created_at <= end_datetime
                    )
                )
            )
            active_users = users_query.scalar() or 0

            # Upsert daily metrics (insert or update if exists)
            stmt = insert(DailyMetric).values(
                project_id=project_id,
                metric_date=target_date,
                documents_uploaded=documents_uploaded,
                searches_performed=searches_performed,
                chat_messages_sent=chat_messages_sent,
                insights_generated=insights_generated,
                active_users=active_users
            )

            stmt = stmt.on_conflict_do_update(
                constraint='uq_project_metric_date',
                set_={
                    'documents_uploaded': documents_uploaded,
                    'searches_performed': searches_performed,
                    'chat_messages_sent': chat_messages_sent,
                    'insights_generated': insights_generated,
                    'active_users': active_users
                }
            )

            await db.execute(stmt)
            await db.commit()

            # Retrieve the updated/created metric
            result = await db.execute(
                select(DailyMetric).where(
                    and_(
                        DailyMetric.project_id == project_id,
                        DailyMetric.metric_date == target_date
                    )
                )
            )
            metric = result.scalar_one()

            logger.info(
                f"Aggregated daily metrics for project {project_id}, "
                f"date {target_date}: {documents_uploaded} docs, "
                f"{searches_performed} searches, {chat_messages_sent} messages"
            )

            return metric

        except Exception as e:
            logger.error(f"Failed to aggregate daily metrics: {str(e)}")
            await db.rollback()
            raise

    async def get_metrics_for_period(
        self,
        db: AsyncSession,
        project_id: int,
        days: int = 30,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Get daily metrics for a time period.

        Args:
            db: Database session
            project_id: Project to get metrics for
            days: Number of days to retrieve (default: 30)
            end_date: End date for the period (default: today)

        Returns:
            List of daily metrics as dictionaries with date and values

        Example:
            metrics = await service.get_metrics_for_period(db, project_id=5, days=7)
            # Returns: [
            #   {"date": "2026-02-01", "documents_uploaded": 5, ...},
            #   {"date": "2026-02-02", "documents_uploaded": 3, ...},
            # ]
        """
        if end_date is None:
            end_date = date.today()

        start_date = end_date - timedelta(days=days - 1)

        result = await db.execute(
            select(DailyMetric)
            .where(
                and_(
                    DailyMetric.project_id == project_id,
                    DailyMetric.metric_date >= start_date,
                    DailyMetric.metric_date <= end_date
                )
            )
            .order_by(DailyMetric.metric_date.asc())
        )
        metrics = result.scalars().all()

        return [
            {
                "date": metric.metric_date.isoformat(),
                "documents_uploaded": metric.documents_uploaded or 0,
                "searches_performed": metric.searches_performed or 0,
                "chat_messages_sent": metric.chat_messages_sent or 0,
                "insights_generated": metric.insights_generated or 0,
                "active_users": metric.active_users or 0,
            }
            for metric in metrics
        ]

    async def get_recent_activity(
        self,
        db: AsyncSession,
        project_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get recent activity events for a project.

        Args:
            db: Database session
            project_id: Project to get activity for
            limit: Maximum number of events to return (default: 50)
            offset: Number of events to skip for pagination (default: 0)

        Returns:
            List of activity events with user and metadata

        Example:
            activities = await service.get_recent_activity(db, project_id=5, limit=20)
        """
        result = await db.execute(
            select(ActivityEvent)
            .where(ActivityEvent.project_id == project_id)
            .order_by(ActivityEvent.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        events = result.scalars().all()

        return [
            {
                "id": event.id,
                "user_id": event.user_id,
                "event_type": event.event_type,
                "event_data": event.event_data,
                "created_at": event.created_at.isoformat(),
            }
            for event in events
        ]

    async def calculate_quality_score(
        self,
        db: AsyncSession,
        project_id: int,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Calculate project quality score based on activity patterns.

        Quality score is calculated based on:
        - Document upload frequency (25%)
        - Search usage intensity (25%)
        - Chat engagement (25%)
        - Content diversity (number of documents) (25%)

        Args:
            db: Database session
            project_id: Project to calculate score for
            days: Number of days to analyze (default: 7)

        Returns:
            Dictionary with overall score (0-100) and component scores

        Example:
            score = await service.calculate_quality_score(db, project_id=5)
            # Returns: {
            #   "overall_score": 75,
            #   "document_score": 80,
            #   "search_score": 70,
            #   "chat_score": 75,
            #   "diversity_score": 75
            # }
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        # Get metrics for the period
        result = await db.execute(
            select(
                func.sum(DailyMetric.documents_uploaded).label('total_documents'),
                func.sum(DailyMetric.searches_performed).label('total_searches'),
                func.sum(DailyMetric.chat_messages_sent).label('total_messages'),
            )
            .where(
                and_(
                    DailyMetric.project_id == project_id,
                    DailyMetric.metric_date >= start_date,
                    DailyMetric.metric_date <= end_date
                )
            )
        )
        totals = result.one()

        # Get document count for diversity
        doc_result = await db.execute(
            select(func.count(Document.id))
            .where(Document.project_id == project_id)
        )
        document_count = doc_result.scalar() or 0

        # Calculate component scores (0-100)
        # Document score: 1+ docs per day = 100, 0 = 0
        docs_per_day = (totals.total_documents or 0) / days
        document_score = min(100, int(docs_per_day * 100))

        # Search score: 5+ searches per day = 100, 0 = 0
        searches_per_day = (totals.total_searches or 0) / days
        search_score = min(100, int(searches_per_day * 20))

        # Chat score: 3+ messages per day = 100, 0 = 0
        messages_per_day = (totals.total_messages or 0) / days
        chat_score = min(100, int(messages_per_day * 33))

        # Diversity score: 10+ documents = 100, 0 = 0
        diversity_score = min(100, document_count * 10)

        # Overall score (weighted average)
        overall_score = int(
            document_score * 0.25 +
            search_score * 0.25 +
            chat_score * 0.25 +
            diversity_score * 0.25
        )

        return {
            "overall_score": overall_score,
            "document_score": document_score,
            "search_score": search_score,
            "chat_score": chat_score,
            "diversity_score": diversity_score,
            "period_days": days,
            "metrics": {
                "total_documents": totals.total_documents or 0,
                "total_searches": totals.total_searches or 0,
                "total_messages": totals.total_messages or 0,
                "document_count": document_count,
            }
        }

    async def get_activity_trends(
        self,
        db: AsyncSession,
        project_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get activity trends with percentage changes.

        Compares the most recent period with the previous period
        to calculate growth rates.

        Args:
            db: Database session
            project_id: Project to analyze
            days: Number of days for each period (default: 30)

        Returns:
            Dictionary with current values and percentage changes

        Example:
            trends = await service.get_activity_trends(db, project_id=5, days=7)
            # Returns: {
            #   "documents_uploaded": {"current": 15, "previous": 10, "change_percent": 50.0},
            #   ...
            # }
        """
        end_date = date.today()
        current_start = end_date - timedelta(days=days - 1)
        previous_start = current_start - timedelta(days=days)
        previous_end = current_start - timedelta(days=1)

        # Get current period metrics
        current_result = await db.execute(
            select(
                func.sum(DailyMetric.documents_uploaded).label('documents'),
                func.sum(DailyMetric.searches_performed).label('searches'),
                func.sum(DailyMetric.chat_messages_sent).label('messages'),
                func.sum(DailyMetric.insights_generated).label('insights'),
            )
            .where(
                and_(
                    DailyMetric.project_id == project_id,
                    DailyMetric.metric_date >= current_start,
                    DailyMetric.metric_date <= end_date
                )
            )
        )
        current = current_result.one()

        # Get previous period metrics
        previous_result = await db.execute(
            select(
                func.sum(DailyMetric.documents_uploaded).label('documents'),
                func.sum(DailyMetric.searches_performed).label('searches'),
                func.sum(DailyMetric.chat_messages_sent).label('messages'),
                func.sum(DailyMetric.insights_generated).label('insights'),
            )
            .where(
                and_(
                    DailyMetric.project_id == project_id,
                    DailyMetric.metric_date >= previous_start,
                    DailyMetric.metric_date <= previous_end
                )
            )
        )
        previous = previous_result.one()

        def calc_change(current_val, previous_val):
            """Calculate percentage change, handling zero division."""
            current_val = current_val or 0
            previous_val = previous_val or 0

            if previous_val == 0:
                return 100.0 if current_val > 0 else 0.0

            return round(((current_val - previous_val) / previous_val) * 100, 1)

        return {
            "documents_uploaded": {
                "current": current.documents or 0,
                "previous": previous.documents or 0,
                "change_percent": calc_change(current.documents, previous.documents)
            },
            "searches_performed": {
                "current": current.searches or 0,
                "previous": previous.searches or 0,
                "change_percent": calc_change(current.searches, previous.searches)
            },
            "chat_messages_sent": {
                "current": current.messages or 0,
                "previous": previous.messages or 0,
                "change_percent": calc_change(current.messages, previous.messages)
            },
            "insights_generated": {
                "current": current.insights or 0,
                "previous": previous.insights or 0,
                "change_percent": calc_change(current.insights, previous.insights)
            },
            "period_days": days
        }
