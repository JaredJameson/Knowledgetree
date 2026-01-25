"""
KnowledgeTree - AI Insights API Routes
REST API for AI-powered document and project insights
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from core.database import get_db
from api.dependencies import get_current_user
from models.user import User
from models.project import Project
from services.insights_service import insights_service, DocumentInsight, ProjectInsight


router = APIRouter(prefix='/insights', tags=['AI Insights'])


# ============================================================================
# Request/Response Schemas
# ============================================================================

class InsightRequest(BaseModel):
    """Request to generate insights"""
    document_id: int = Field(..., description="Document ID to analyze")
    force_refresh: bool = Field(False, description="Force regeneration of insights")


class ProjectInsightRequest(BaseModel):
    """Request to generate project-level insights"""
    project_id: int = Field(..., description="Project ID to analyze")
    max_documents: int = Field(10, description="Maximum documents to analyze", ge=1, le=50)
    include_categories: bool = Field(True, description="Include category analysis")
    force_refresh: bool = Field(False, description="Force regeneration")


class DocumentInsightResponse(BaseModel):
    """Response for document insights"""
    document_id: int
    title: str
    summary: str
    key_findings: List[str]
    topics: List[str]
    entities: List[str]
    sentiment: str
    action_items: List[str]
    importance_score: float
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class ProjectInsightResponse(BaseModel):
    """Response for project insights"""
    project_id: int
    project_name: str
    executive_summary: str
    total_documents: int
    key_themes: List[str]
    top_categories: List[dict]
    document_summaries: List[DocumentInsightResponse]
    patterns: List[str]
    recommendations: List[str]
    generated_at: datetime


class AvailabilityResponse(BaseModel):
    """Response for service availability check"""
    available: bool
    model: Optional[str] = None
    message: str


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/availability", response_model=AvailabilityResponse)
async def check_availability():
    """
    Check if AI Insights service is available
    
    Returns status of Anthropic API configuration.
    """
    status = insights_service.check_availability()
    return AvailabilityResponse(**status)


@router.post("/document/{document_id}", response_model=DocumentInsightResponse)
async def generate_document_insights(
    document_id: int,
    request: InsightRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate AI-powered insights for a single document
    
    Analyzes document content to extract:
    - Summary
    - Key findings
    - Topics and entities
    - Sentiment analysis
    - Action items
    
    **Example:**
    ```json
    {
        "document_id": 123,
        "force_refresh": false
    }
    ```
    """
    # Check if feature is enabled
    from core.config import settings
    if not settings.ENABLE_AI_INSIGHTS:
        raise HTTPException(
            status_code=503,
            detail="AI Insights feature is not enabled. Set ENABLE_AI_INSIGHTS=True in config."
        )
    
    try:
        insight = await insights_service.generate_document_insights(
            db=db,
            document_id=document_id,
            project_id=current_user.id
        )
        
        return DocumentInsightResponse(
            document_id=insight.document_id,
            title=insight.title,
            summary=insight.summary,
            key_findings=insight.key_findings,
            topics=insight.topics,
            entities=insight.entities,
            sentiment=insight.sentiment,
            action_items=insight.action_items,
            importance_score=insight.importance_score,
            generated_at=datetime.utcnow()
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")


@router.post("/project", response_model=ProjectInsightResponse)
async def generate_project_insights(
    request: ProjectInsightRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate AI-powered insights for entire project
    
    Analyzes multiple documents to provide:
    - Executive summary
    - Key themes across documents
    - Top categories
    - Individual document insights
    - Patterns and recommendations
    
    **Example:**
    ```json
    {
        "max_documents": 10,
        "include_categories": true,
        "force_refresh": false
    }
    ```
    """
    # Check if feature is enabled
    from core.config import settings
    if not settings.ENABLE_AI_INSIGHTS:
        raise HTTPException(
            status_code=503,
            detail="AI Insights feature is not enabled. Set ENABLE_AI_INSIGHTS=True in config."
        )

    # Verify project access
    result = await db.execute(
        select(Project).where(
            Project.id == request.project_id,
            Project.owner_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=404,
            detail=f"Project with id {request.project_id} not found or access denied"
        )

    try:
        insight = await insights_service.generate_project_insights(
            db=db,
            project_id=request.project_id,
            max_documents=request.max_documents,
            include_categories=request.include_categories
        )
        
        # Convert document insights
        doc_summaries = [
            DocumentInsightResponse(
                document_id=d.document_id,
                title=d.title,
                summary=d.summary,
                key_findings=d.key_findings,
                topics=d.topics,
                entities=d.entities,
                sentiment=d.sentiment,
                action_items=d.action_items,
                importance_score=d.importance_score,
                generated_at=d.generated_at
            )
            for d in insight.document_summaries
        ]
        
        return ProjectInsightResponse(
            project_id=insight.project_id,
            project_name=insight.project_name,
            executive_summary=insight.executive_summary,
            total_documents=insight.total_documents,
            key_themes=insight.key_themes,
            top_categories=insight.top_categories,
            document_summaries=doc_summaries,
            patterns=insight.patterns,
            recommendations=insight.recommendations,
            generated_at=insight.generated_at
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate project insights: {str(e)}")


@router.get("/project/recent")
async def get_recent_insights(
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get recent insights for the user's project
    
    Returns cached insights if available, otherwise triggers generation.
    """
    # Check if feature is enabled
    from core.config import settings
    if not settings.ENABLE_AI_INSIGHTS:
        raise HTTPException(
            status_code=503,
            detail="AI Insights feature is not enabled. Set ENABLE_AI_INSIGHTS=True in config."
        )
    
    # For now, just trigger new insights generation
    # In production, you'd cache results in the database
    try:
        insight = await insights_service.generate_project_insights(
            db=db,
            project_id=current_user.id,
            max_documents=limit,
            include_categories=True
        )
        
        return {
            "project_id": insight.project_id,
            "executive_summary": insight.executive_summary,
            "key_themes": insight.key_themes,
            "total_documents_analyzed": insight.total_documents,
            "generated_at": insight.generated_at.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get insights: {str(e)}")
