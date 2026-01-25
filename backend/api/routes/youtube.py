"""
KnowledgeTree Backend - YouTube Processing Routes
API endpoints for YouTube video transcription and knowledge extraction
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.dependencies import get_current_user
from core.database import get_db
from core.config import settings
from models.user import User
from models.project import Project
from services.youtube_transcriber import YouTubeTranscriber, process_youtube_video

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/youtube", tags=["youtube"])


# ============================================================================
# Dependencies
# ============================================================================

async def get_project_or_404(
    project_id: int,
    current_user: User,
    db: AsyncSession
) -> Project:
    """
    Get project by ID with access control

    Args:
        project_id: Project ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Project object

    Raises:
        HTTPException: 404 if not found or access denied
    """
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

    return project


# ============================================================================
# Request/Response Schemas
# ============================================================================

class YouTubeProcessRequest(BaseModel):
    """Request to process YouTube video"""
    url: str = Field(..., description="YouTube video URL")
    language: str = Field(default="pl", description="Transcript language (pl, en)")
    project_context: Optional[str] = Field(None, description="Optional project context for better analysis")


class CategoryInfo(BaseModel):
    """Category information"""
    id: int
    name: str
    description: Optional[str]
    depth: int
    color: str
    icon: str


class DocumentInfo(BaseModel):
    """Document information"""
    id: int
    title: str
    filename: str
    source_type: str
    source_url: str


class YouTubeProcessResponse(BaseModel):
    """Response from YouTube processing"""
    status: str
    document: Optional[DocumentInfo] = None
    categories: list[CategoryInfo] = []
    metadata: dict = {}
    total_categories: int = 0
    error: Optional[str] = None


class VideoMetadataResponse(BaseModel):
    """Response from video metadata fetch"""
    video_id: str
    title: str
    description: str
    channel: str
    duration: int
    thumbnail_url: str
    url: str
    transcript_available: bool


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/process", response_model=YouTubeProcessResponse)
async def process_youtube(
    request: YouTubeProcessRequest,
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Process YouTube video - extract transcript and generate knowledge tree

    This endpoint:
    1. Extracts video ID from URL
    2. Fetches video metadata
    3. Downloads transcript with timestamps
    4. Analyzes content with Claude AI
    5. Generates hierarchical category tree
    6. Creates searchable chunks with embeddings

    Args:
        request: YouTube processing request
        project_id: Project ID
        current_user: Authenticated user
        db: Database session

    Returns:
        Processing result with document, categories, and metadata

    Raises:
        HTTPException: If processing fails
    """
    try:
        # Verify project access
        project = await get_project_or_404(project_id, current_user, db)

        # Validate URL
        transcriber = YouTubeTranscriber(settings.anthropic_api_key)
        video_id = transcriber.extract_video_id(request.url)

        if not video_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid YouTube URL format"
            )

        logger.info(f"Processing YouTube video {video_id} for project {project.id} by user {current_user.id}")

        # Process video
        document, categories, metadata = await process_youtube_video(
            url=request.url,
            project_id=project.id,
            db=db,
            anthropic_api_key=settings.anthropic_api_key,
            language=request.language,
            project_context=request.project_context
        )

        await transcriber.close()

        # Format response
        return YouTubeProcessResponse(
            status="success",
            document=DocumentInfo(
                id=document.id,
                title=document.title,
                filename=document.filename,
                source_type=document.source_type.value,
                source_url=document.source_url
            ),
            categories=[
                CategoryInfo(
                    id=cat.id,
                    name=cat.name,
                    description=cat.description,
                    depth=cat.depth,
                    color=cat.color,
                    icon=cat.icon
                )
                for cat in categories
            ],
            metadata=metadata,
            total_categories=len(categories)
        )

    except ValueError as e:
        logger.error(f"YouTube processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during YouTube processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process YouTube video: {str(e)}"
        )


@router.get("/metadata/{video_id}", response_model=VideoMetadataResponse)
async def get_video_metadata(
    video_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Fetch YouTube video metadata without processing

    Args:
        video_id: YouTube video ID (11 characters)
        current_user: Authenticated user

    Returns:
        Video metadata

    Raises:
        HTTPException: If video not found or fetch fails
    """
    try:
        transcriber = YouTubeTranscriber(settings.anthropic_api_key)

        # Fetch metadata
        metadata = await transcriber.fetch_video_metadata(video_id)

        await transcriber.close()

        # Check if transcript is available
        try:
            transcript = await transcriber.fetch_transcript(video_id, language="pl")
            transcript_available = True
        except Exception:
            transcript_available = False

        return VideoMetadataResponse(
            video_id=metadata.video_id,
            title=metadata.title,
            description=metadata.description,
            channel=metadata.channel,
            duration=metadata.duration,
            thumbnail_url=metadata.thumbnail_url,
            url=metadata.url,
            transcript_available=transcript_available
        )

    except Exception as e:
        logger.error(f"Failed to fetch video metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video not found or unavailable: {str(e)}"
        )


@router.post("/extract-id")
async def extract_video_id(
    url: str = Query(..., description="YouTube video URL"),
    current_user: User = Depends(get_current_user)
):
    """
    Extract video ID from YouTube URL

    Useful for validating URLs before processing

    Args:
        url: YouTube video URL in any format
        current_user: Authenticated user

    Returns:
        Video ID and validation status

    Raises:
        HTTPException: If URL is invalid
    """
    transcriber = YouTubeTranscriber(settings.anthropic_api_key)
    video_id = transcriber.extract_video_id(url)

    if not video_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid YouTube URL format"
        )

    return {
        "video_id": video_id,
        "valid": True,
        "url": url
    }
