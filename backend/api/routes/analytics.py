"""
KnowledgeTree Backend - Analytics Routes
Activity metrics, trends, and quality scores
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from core.database import get_db
from models.user import User
from models.project import Project
from models.activity import ActivityEvent
from schemas.analytics import (
    MetricsResponse,
    DailyMetricResponse,
    ActivityFeedResponse,
    ActivityEventResponse,
    QualityScoreResponse,
    TrendsResponse,
    TrendDataPoint,
)
from api.dependencies import get_current_active_user
from services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])
logger = logging.getLogger(__name__)

# Initialize analytics service
analytics_service = AnalyticsService()


@router.get("/metrics/{project_id}", response_model=MetricsResponse)
async def get_project_metrics(
    project_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of days to retrieve (1-365)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get daily metrics for a project over a time period.

    Returns aggregated daily statistics including:
    - Documents uploaded per day
    - Searches performed per day
    - Chat messages sent per day
    - Insights generated per day
    - Active users per day

    **Query Parameters:**
    - `days`: Number of days to retrieve (default: 30, max: 365)

    **Returns:**
    - Daily metrics for the specified period
    - Totals across the entire period
    """
    # Verify project access
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )

    try:
        # Get metrics for period
        metrics_data = await analytics_service.get_metrics_for_period(
            db=db,
            project_id=project_id,
            days=days
        )

        # Calculate totals
        total_documents = sum(m["documents_uploaded"] for m in metrics_data)
        total_searches = sum(m["searches_performed"] for m in metrics_data)
        total_messages = sum(m["chat_messages_sent"] for m in metrics_data)
        total_insights = sum(m["insights_generated"] for m in metrics_data)

        # Format response
        metrics_list = [DailyMetricResponse(**m) for m in metrics_data]

        logger.info(f"Retrieved metrics for project {project_id}: {len(metrics_list)} days")

        return MetricsResponse(
            project_id=project_id,
            period_days=days,
            metrics=metrics_list,
            total_documents=total_documents,
            total_searches=total_searches,
            total_messages=total_messages,
            total_insights=total_insights
        )

    except Exception as e:
        logger.error(f"Failed to retrieve metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve metrics: {str(e)}"
        )


@router.get("/activity/{project_id}", response_model=ActivityFeedResponse)
async def get_project_activity(
    project_id: int,
    limit: int = Query(50, ge=1, le=100, description="Maximum events to return (1-100)"),
    offset: int = Query(0, ge=0, description="Number of events to skip (for pagination)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent activity events for a project.

    Returns a feed of recent user actions and system events:
    - Document uploads and deletions
    - Search operations
    - Chat messages
    - Category operations
    - Insight generations

    **Query Parameters:**
    - `limit`: Maximum events to return (default: 50, max: 100)
    - `offset`: Number of events to skip for pagination (default: 0)

    **Returns:**
    - List of activity events with metadata
    - Total count for pagination
    """
    # Verify project access
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )

    try:
        # Get total count for pagination
        count_result = await db.execute(
            select(func.count(ActivityEvent.id))
            .where(ActivityEvent.project_id == project_id)
        )
        total_count = count_result.scalar() or 0

        # Get activity events
        activities_data = await analytics_service.get_recent_activity(
            db=db,
            project_id=project_id,
            limit=limit,
            offset=offset
        )

        # Format response
        activities_list = [ActivityEventResponse(**a) for a in activities_data]

        logger.info(
            f"Retrieved activity feed for project {project_id}: "
            f"{len(activities_list)} events (offset: {offset}, total: {total_count})"
        )

        return ActivityFeedResponse(
            project_id=project_id,
            activities=activities_list,
            total_count=total_count,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"Failed to retrieve activity feed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve activity feed: {str(e)}"
        )


@router.get("/quality-score/{project_id}", response_model=QualityScoreResponse)
async def get_quality_score(
    project_id: int,
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze (1-90)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get project quality score based on activity patterns.

    Quality score is calculated from:
    - Document upload frequency (25%)
    - Search usage intensity (25%)
    - Chat engagement (25%)
    - Content diversity (25%)

    Scores range from 0-100, where:
    - 0-40: Low activity, needs improvement
    - 41-70: Moderate activity, good engagement
    - 71-100: High activity, excellent engagement

    **Query Parameters:**
    - `days`: Number of days to analyze (default: 7, max: 90)

    **Returns:**
    - Overall quality score (0-100)
    - Component scores for each factor
    - Supporting metrics
    """
    # Verify project access
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )

    try:
        # Calculate quality score
        score_data = await analytics_service.calculate_quality_score(
            db=db,
            project_id=project_id,
            days=days
        )

        logger.info(
            f"Calculated quality score for project {project_id}: "
            f"{score_data['overall_score']}/100"
        )

        return QualityScoreResponse(**score_data)

    except Exception as e:
        logger.error(f"Failed to calculate quality score: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate quality score: {str(e)}"
        )


@router.get("/trends/{project_id}", response_model=TrendsResponse)
async def get_activity_trends(
    project_id: int,
    days: int = Query(30, ge=1, le=90, description="Number of days per period (1-90)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get activity trends with percentage changes.

    Compares the most recent period with the previous period
    to show growth or decline in activity.

    **Query Parameters:**
    - `days`: Number of days per period (default: 30, max: 90)
      - Current period: last N days
      - Previous period: N days before that

    **Returns:**
    - Current and previous values for each metric
    - Percentage change (positive = growth, negative = decline)

    **Example:**
    - days=7
    - Current period: last 7 days
    - Previous period: 7 days before that
    - Returns: % change for each metric
    """
    # Verify project access
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )

    try:
        # Get activity trends
        trends_data = await analytics_service.get_activity_trends(
            db=db,
            project_id=project_id,
            days=days
        )

        # Format response
        response = TrendsResponse(
            project_id=project_id,
            period_days=days,
            documents_uploaded=TrendDataPoint(**trends_data["documents_uploaded"]),
            searches_performed=TrendDataPoint(**trends_data["searches_performed"]),
            chat_messages_sent=TrendDataPoint(**trends_data["chat_messages_sent"]),
            insights_generated=TrendDataPoint(**trends_data["insights_generated"])
        )

        logger.info(f"Retrieved trends for project {project_id} ({days} days)")

        return response

    except Exception as e:
        logger.error(f"Failed to retrieve trends: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve trends: {str(e)}"
        )
