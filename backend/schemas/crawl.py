"""
KnowledgeTree Backend - Web Crawling Schemas
Pydantic models for web crawling and content extraction with quality filtering
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ScheduleFrequency(str, Enum):
    """Schedule frequency for automated re-crawls"""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    MANUAL = "manual"


class ExtractionMethod(str, Enum):
    """Content extraction methods"""
    TRAFILATURA = "trafilatura"  # Best for articles, docs
    READABILITY = "readability"  # Good for news, blogs
    BASIC = "basic"  # Fallback with noise removal
    AUTO = "auto"  # Auto-select best method


class ContentFilters(BaseModel):
    """Content filtering options"""
    min_quality_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum content quality score (0.0-1.0)"
    )
    min_text_length: int = Field(
        default=200,
        ge=50,
        description="Minimum text length in characters"
    )
    exclude_selectors: Optional[List[str]] = Field(
        default=None,
        description="Additional CSS selectors to remove (e.g., ['.ads', '.comments'])"
    )
    require_selectors: Optional[List[str]] = Field(
        default=None,
        description="Required CSS selectors for content (e.g., ['article', 'main'])"
    )


class URLPatterns(BaseModel):
    """URL filtering patterns"""
    include: Optional[List[str]] = Field(
        default=None,
        description="Regex patterns to include (e.g., ['^https://example\\.com/docs/.*'])"
    )
    exclude: Optional[List[str]] = Field(
        default=None,
        description="Regex patterns to exclude (e.g., ['.*\\.pdf$', '.*/download/.*'])"
    )


class CrawlJobCreate(BaseModel):
    """Schema for creating a web crawl job"""
    url: str = Field(
        ...,
        min_length=1,
        description="Starting URL to crawl"
    )
    max_depth: int = Field(
        default=2,
        ge=1,
        le=5,
        description="Maximum crawl depth (1-5 levels)"
    )
    url_patterns: Optional[URLPatterns] = Field(
        default=None,
        description="URL filtering patterns"
    )
    content_filters: Optional[ContentFilters] = Field(
        default=None,
        description="Content quality filters"
    )
    extraction_method: ExtractionMethod = Field(
        default=ExtractionMethod.AUTO,
        description="Content extraction method"
    )
    schedule_frequency: ScheduleFrequency = Field(
        default=ScheduleFrequency.ONCE,
        description="Re-crawl schedule frequency"
    )
    auto_categorize: bool = Field(
        default=True,
        description="Automatically generate category tree from URL structure"
    )

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "url": "https://docs.python.org/3/",
                    "max_depth": 2,
                    "url_patterns": {
                        "include": ["^https://docs\\.python\\.org/3/tutorial/.*"],
                        "exclude": [".*\\.pdf$", ".*/download/.*"]
                    },
                    "content_filters": {
                        "min_quality_score": 0.7,
                        "min_text_length": 500,
                        "exclude_selectors": [".sidebar", ".advertisement"]
                    },
                    "extraction_method": "trafilatura",
                    "schedule_frequency": "weekly",
                    "auto_categorize": True
                }
            ]
        }
    }


class CrawlJobUpdate(BaseModel):
    """Schema for updating a crawl job"""
    schedule_frequency: Optional[ScheduleFrequency] = None
    content_filters: Optional[ContentFilters] = None


class CrawlJobStatus(str, Enum):
    """Crawl job status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    UP_TO_DATE = "up_to_date"


class CrawlJobResponse(BaseModel):
    """Crawl job response"""
    id: int
    url: str
    status: CrawlJobStatus
    max_depth: int
    url_patterns: Optional[Dict[str, Any]]
    content_filters: Optional[Dict[str, Any]]
    extraction_method: str
    schedule_frequency: ScheduleFrequency
    urls_crawled: int
    urls_failed: int
    urls_total: Optional[int]
    progress_percent: float
    document_id: Optional[int]
    project_id: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    next_scheduled_crawl: Optional[datetime]
    error_message: Optional[str]

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "url": "https://docs.python.org/3/",
                    "status": "in_progress",
                    "max_depth": 2,
                    "url_patterns": {"include": ["^https://docs\\.python\\.org/3/.*"]},
                    "content_filters": {"min_quality_score": 0.7},
                    "extraction_method": "trafilatura",
                    "schedule_frequency": "weekly",
                    "urls_crawled": 45,
                    "urls_failed": 2,
                    "urls_total": 120,
                    "progress_percent": 37.5,
                    "document_id": None,
                    "project_id": 1,
                    "created_at": "2026-01-29T10:00:00Z",
                    "started_at": "2026-01-29T10:00:30Z",
                    "completed_at": None,
                    "next_scheduled_crawl": None,
                    "error_message": None
                }
            ]
        }
    }


class CrawlJobListResponse(BaseModel):
    """List of crawl jobs"""
    crawl_jobs: List[CrawlJobResponse]
    total: int
    page: int
    page_size: int

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "crawl_jobs": [],
                    "total": 0,
                    "page": 1,
                    "page_size": 20
                }
            ]
        }
    }


class ReCrawlRequest(BaseModel):
    """Request to trigger re-crawl"""
    incremental: bool = Field(
        default=True,
        description="If True, only re-crawl changed pages (faster)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "incremental": True
                }
            ]
        }
    }


class CrawlHistoryEntry(BaseModel):
    """Single crawl history entry"""
    id: int
    crawl_job_id: int
    started_at: datetime
    completed_at: Optional[datetime]
    urls_processed: int
    urls_changed: int
    urls_new: int
    urls_removed: int
    status: str
    error_message: Optional[str]

    model_config = {"from_attributes": True}


class CrawlHistoryResponse(BaseModel):
    """Crawl history response"""
    history: List[CrawlHistoryEntry]
    total: int

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "history": [
                        {
                            "id": 1,
                            "crawl_job_id": 1,
                            "started_at": "2026-01-29T10:00:00Z",
                            "completed_at": "2026-01-29T10:15:00Z",
                            "urls_processed": 120,
                            "urls_changed": 5,
                            "urls_new": 0,
                            "urls_removed": 0,
                            "status": "completed",
                            "error_message": None
                        }
                    ],
                    "total": 1
                }
            ]
        }
    }
