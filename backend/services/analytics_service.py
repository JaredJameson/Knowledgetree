"""
Analytics Service
Aggregates and calculates analytics metrics for projects
"""

from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import select, func, distinct, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from models.activity import ActivityEvent, DailyMetric
from models.document import Document
from services.activity_tracker import EventType


class AnalyticsService:
    """Service for calculating and retrieving analytics metrics"""

    async def aggregate_daily_metrics(
        self,
        db: AsyncSession,
        project_id: int,
        target_date: date
    ) -> DailyMetric:
        """
        Aggregate activity events into daily metrics for a specific date.
        Uses upsert pattern to make aggregation idempotent.

        Args:
            db: Database session
            project_id: Project ID to aggregate for
            target_date: Date to aggregate

        Returns:
            DailyMetric instance
        """
        # Calculate start and end datetime for the target date
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())

        # Count documents uploaded
        result = await db.execute(
            select(func.count(ActivityEvent.id))
            .where(
                and_(
                    ActivityEvent.project_id == project_id,
                    ActivityEvent.event_type == EventType.DOCUMENT_UPLOADED.value,
                    ActivityEvent.created_at >= start_datetime,
                    ActivityEvent.created_at <= end_datetime
                )
            )
        )
        documents_uploaded = result.scalar() or 0

        # Count searches performed
        result = await db.execute(
            select(func.count(ActivityEvent.id))
            .where(
                and_(
                    ActivityEvent.project_id == project_id,
                    ActivityEvent.event_type == EventType.SEARCH_PERFORMED.value,
                    ActivityEvent.created_at >= start_datetime,
                    ActivityEvent.created_at <= end_datetime
                )
            )
        )
        searches_performed = result.scalar() or 0

        # Count chat messages sent
        result = await db.execute(
            select(func.count(ActivityEvent.id))
            .where(
                and_(
                    ActivityEvent.project_id == project_id,
                    ActivityEvent.event_type == EventType.CHAT_MESSAGE_SENT.value,
                    ActivityEvent.created_at >= start_datetime,
                    ActivityEvent.created_at <= end_datetime
                )
            )
        )
        chat_messages_sent = result.scalar() or 0

        # Count insights generated
        result = await db.execute(
            select(func.count(ActivityEvent.id))
            .where(
                and_(
                    ActivityEvent.project_id == project_id,
                    ActivityEvent.event_type == EventType.INSIGHT_GENERATED.value,
                    ActivityEvent.created_at >= start_datetime,
                    ActivityEvent.created_at <= end_datetime
                )
            )
        )
        insights_generated = result.scalar() or 0

        # Count distinct active users
        result = await db.execute(
            select(func.count(distinct(ActivityEvent.user_id)))
            .where(
                and_(
                    ActivityEvent.project_id == project_id,
                    ActivityEvent.created_at >= start_datetime,
                    ActivityEvent.created_at <= end_datetime
                )
            )
        )
        active_users = result.scalar() or 0

        # Upsert daily metric (INSERT ... ON CONFLICT DO UPDATE)
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
            index_elements=['project_id', 'metric_date'],
            set_=dict(
                documents_uploaded=documents_uploaded,
                searches_performed=searches_performed,
                chat_messages_sent=chat_messages_sent,
                insights_generated=insights_generated,
                active_users=active_users
            )
        )

        await db.execute(stmt)
        await db.commit()

        # Retrieve and return the metric
        result = await db.execute(
            select(DailyMetric)
            .where(
                and_(
                    DailyMetric.project_id == project_id,
                    DailyMetric.metric_date == target_date
                )
            )
        )

        return result.scalar_one()

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
            project_id: Project ID
            days: Number of days to retrieve (default 30)
            end_date: End date for the period (default today)

        Returns:
            List of daily metrics dictionaries
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
                "documents_uploaded": metric.documents_uploaded,
                "searches_performed": metric.searches_performed,
                "chat_messages_sent": metric.chat_messages_sent,
                "insights_generated": metric.insights_generated,
                "active_users": metric.active_users
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
            project_id: Project ID
            limit: Maximum number of events to return
            offset: Offset for pagination

        Returns:
            List of activity event dictionaries
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
                "created_at": event.created_at.isoformat()
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

        Scoring algorithm (0-100):
        - Document score (25%): Upload frequency (1+ docs/day = 100)
        - Search score (25%): Search intensity (5+ searches/day = 100)
        - Chat score (25%): Chat engagement (3+ messages/day = 100)
        - Diversity score (25%): Content breadth (10+ documents = 100)

        Args:
            db: Database session
            project_id: Project ID
            days: Number of days to analyze (default 7)

        Returns:
            Quality score dictionary with overall and component scores
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        # Get metrics for the period
        result = await db.execute(
            select(DailyMetric)
            .where(
                and_(
                    DailyMetric.project_id == project_id,
                    DailyMetric.metric_date >= start_date,
                    DailyMetric.metric_date <= end_date
                )
            )
        )
        metrics = result.scalars().all()

        # Calculate totals
        total_documents = sum(m.documents_uploaded for m in metrics)
        total_searches = sum(m.searches_performed for m in metrics)
        total_messages = sum(m.chat_messages_sent for m in metrics)

        # Calculate daily averages
        docs_per_day = total_documents / days if days > 0 else 0
        searches_per_day = total_searches / days if days > 0 else 0
        messages_per_day = total_messages / days if days > 0 else 0

        # Calculate component scores (0-100)
        document_score = min(int((docs_per_day / 1.0) * 100), 100) if docs_per_day > 0 else 0
        search_score = min(int((searches_per_day / 5.0) * 100), 100) if searches_per_day > 0 else 0
        chat_score = min(int((messages_per_day / 3.0) * 100), 100) if messages_per_day > 0 else 0

        # Diversity score: number of documents in project
        result = await db.execute(
            select(func.count(Document.id))
            .where(Document.project_id == project_id)
        )
        document_count = result.scalar() or 0
        diversity_score = min(int((document_count / 10.0) * 100), 100) if document_count > 0 else 0

        # Overall score (weighted average)
        overall_score = int(
            (document_score * 0.25) +
            (search_score * 0.25) +
            (chat_score * 0.25) +
            (diversity_score * 0.25)
        )

        return {
            "project_id": project_id,
            "overall_score": overall_score,
            "document_score": document_score,
            "search_score": search_score,
            "chat_score": chat_score,
            "diversity_score": diversity_score,
            "period_days": days,
            "metrics": {
                "total_documents": total_documents,
                "total_searches": total_searches,
                "total_messages": total_messages,
                "document_count": document_count
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

        Compares current period vs previous period of same length.

        Args:
            db: Database session
            project_id: Project ID
            days: Period length in days (default 30)

        Returns:
            Trends dictionary with current, previous, and change percentages
        """
        end_date = date.today()
        current_start = end_date - timedelta(days=days - 1)
        previous_end = current_start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=days - 1)

        # Get current period metrics
        result = await db.execute(
            select(func.sum(DailyMetric.documents_uploaded),
                   func.sum(DailyMetric.searches_performed),
                   func.sum(DailyMetric.chat_messages_sent),
                   func.sum(DailyMetric.insights_generated))
            .where(
                and_(
                    DailyMetric.project_id == project_id,
                    DailyMetric.metric_date >= current_start,
                    DailyMetric.metric_date <= end_date
                )
            )
        )
        current_row = result.one()
        current_docs = current_row[0] or 0
        current_searches = current_row[1] or 0
        current_messages = current_row[2] or 0
        current_insights = current_row[3] or 0

        # Get previous period metrics
        result = await db.execute(
            select(func.sum(DailyMetric.documents_uploaded),
                   func.sum(DailyMetric.searches_performed),
                   func.sum(DailyMetric.chat_messages_sent),
                   func.sum(DailyMetric.insights_generated))
            .where(
                and_(
                    DailyMetric.project_id == project_id,
                    DailyMetric.metric_date >= previous_start,
                    DailyMetric.metric_date <= previous_end
                )
            )
        )
        previous_row = result.one()
        previous_docs = previous_row[0] or 0
        previous_searches = previous_row[1] or 0
        previous_messages = previous_row[2] or 0
        previous_insights = previous_row[3] or 0

        # Calculate percentage changes
        def calc_change(current: int, previous: int) -> float:
            if previous == 0:
                return 0.0
            return round(((current - previous) / previous) * 100, 1)

        return {
            "project_id": project_id,
            "period_days": days,
            "documents_uploaded": {
                "current": current_docs,
                "previous": previous_docs,
                "change_percent": calc_change(current_docs, previous_docs)
            },
            "searches_performed": {
                "current": current_searches,
                "previous": previous_searches,
                "change_percent": calc_change(current_searches, previous_searches)
            },
            "chat_messages_sent": {
                "current": current_messages,
                "previous": previous_messages,
                "change_percent": calc_change(current_messages, previous_messages)
            },
            "insights_generated": {
                "current": current_insights,
                "previous": previous_insights,
                "change_percent": calc_change(current_insights, previous_insights)
            }
        }
