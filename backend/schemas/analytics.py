"""
KnowledgeTree - Analytics Schemas
Pydantic models for analytics API requests/responses
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class DailyMetricResponse(BaseModel):
    """Daily metrics for a single date"""
    date: str = Field(..., description="Date in ISO format (YYYY-MM-DD)")
    documents_uploaded: int = Field(0, ge=0)
    searches_performed: int = Field(0, ge=0)
    chat_messages_sent: int = Field(0, ge=0)
    insights_generated: int = Field(0, ge=0)
    active_users: int = Field(0, ge=0)


class MetricsResponse(BaseModel):
    """Metrics for a time period"""
    project_id: int
    period_days: int
    metrics: List[DailyMetricResponse]
    total_documents: int = Field(0, ge=0)
    total_searches: int = Field(0, ge=0)
    total_messages: int = Field(0, ge=0)
    total_insights: int = Field(0, ge=0)


class ActivityEventResponse(BaseModel):
    """Single activity event"""
    id: int
    user_id: int
    event_type: str
    event_data: Dict[str, Any]
    created_at: str


class ActivityFeedResponse(BaseModel):
    """Activity feed for a project"""
    project_id: int
    activities: List[ActivityEventResponse]
    total_count: int = Field(..., ge=0, description="Total number of activities (for pagination)")
    limit: int
    offset: int


class QualityScoreResponse(BaseModel):
    """Project quality score breakdown"""
    project_id: int
    overall_score: int = Field(..., ge=0, le=100)
    document_score: int = Field(..., ge=0, le=100)
    search_score: int = Field(..., ge=0, le=100)
    chat_score: int = Field(..., ge=0, le=100)
    diversity_score: int = Field(..., ge=0, le=100)
    period_days: int
    metrics: Dict[str, int]


class TrendDataPoint(BaseModel):
    """Trend data for a single metric"""
    current: int = Field(..., ge=0)
    previous: int = Field(..., ge=0)
    change_percent: float


class TrendsResponse(BaseModel):
    """Activity trends with percentage changes"""
    project_id: int
    period_days: int
    documents_uploaded: TrendDataPoint
    searches_performed: TrendDataPoint
    chat_messages_sent: TrendDataPoint
    insights_generated: TrendDataPoint
