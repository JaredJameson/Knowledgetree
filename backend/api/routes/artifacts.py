"""
Artifact API endpoints
CRUD operations for agent-generated artifacts
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
import json
from datetime import datetime

from core.database import get_db
from api.dependencies import get_current_user
from models.user import User
from models.artifact import Artifact, ArtifactType
from models.project import Project
from schemas.artifact import (
    ArtifactCreateRequest,
    ArtifactUpdateRequest,
    ArtifactRegenerateRequest,
    ArtifactResponse,
    ArtifactListItem,
    ArtifactListResponse,
)
from services.artifact_generator import artifact_generator

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


@router.post("", response_model=ArtifactResponse, status_code=201)
async def create_artifact(
    project_id: int = Query(..., description="Project ID"),
    request: ArtifactCreateRequest = ...,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new artifact

    Creates an agent-generated artifact (summary, article, extract, etc.)
    linked to a project and optionally to a conversation or category.

    Args:
        project_id: Project ID (required query parameter)
        request: Artifact creation data

    Returns:
        Created artifact with ID and timestamps
    """
    # Verify project exists and user has access
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Create artifact
    artifact = Artifact(
        type=request.type,
        title=request.title,
        content=request.content,
        version=1,
        artifact_metadata=json.dumps(request.metadata) if request.metadata else None,
        project_id=project_id,
        user_id=current_user.id,
        conversation_id=request.conversation_id,
        category_id=request.category_id,
    )

    db.add(artifact)
    await db.commit()
    await db.refresh(artifact)

    # Parse metadata back to dict
    metadata_dict = None
    if artifact.artifact_metadata:
        try:
            metadata_dict = json.loads(artifact.artifact_metadata)
        except json.JSONDecodeError:
            pass

    return ArtifactResponse(
        id=artifact.id,
        type=artifact.type,
        title=artifact.title,
        content=artifact.content,
        version=artifact.version,
        project_id=artifact.project_id,
        user_id=artifact.user_id,
        conversation_id=artifact.conversation_id,
        category_id=artifact.category_id,
        metadata=metadata_dict,
        created_at=artifact.created_at,
        updated_at=artifact.updated_at,
    )


@router.post("/generate", response_model=ArtifactResponse, status_code=201)
async def generate_artifact(
    project_id: int = Query(..., description="Project ID"),
    artifact_type: ArtifactType = Query(..., description="Type of artifact to generate"),
    title: str = Query(..., min_length=1, max_length=500, description="Artifact title"),
    query: str = Query(..., min_length=1, description="Search query for content retrieval"),
    category_id: Optional[int] = Query(None, description="Optional category filter"),
    conversation_id: Optional[int] = Query(None, description="Optional conversation reference"),
    instructions: Optional[str] = Query(None, description="Optional custom generation instructions"),
    temperature: Optional[float] = Query(0.7, ge=0.0, le=1.0, description="Claude API temperature"),
    max_tokens: Optional[int] = Query(4096, ge=256, le=8192, description="Maximum tokens in response"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate artifact using Claude API with RAG

    Retrieves relevant document chunks and generates artifact content using Claude API.

    Args:
        project_id: Project ID (required query parameter)
        artifact_type: Type of artifact (summary, article, notes, etc.)
        title: Artifact title
        query: Search query for retrieving relevant content (e.g., "chapter 3 neural networks")
        category_id: Optional category filter (e.g., specific chapter)
        conversation_id: Optional conversation that requested this artifact
        instructions: Optional custom generation instructions
        temperature: Claude API temperature (default: 0.7)
        max_tokens: Maximum tokens in response (default: 4096)

    Returns:
        Generated artifact with content, metadata, and ID

    Raises:
        404: Project not found
        500: Generation failed

    Example:
        POST /api/v1/artifacts/generate?project_id=1&artifact_type=summary&title=Chapter+3+Summary&query=chapter+3&category_id=15
    """
    # Verify project exists and user has access
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Generate artifact content using artifact generator
    try:
        content, retrieved_chunks, generation_metadata = await artifact_generator.generate_artifact(
            db=db,
            artifact_type=artifact_type,
            title=title,
            project_id=project_id,
            query=query,
            category_id=category_id,
            instructions=instructions,
            temperature=temperature,
            max_tokens=max_tokens
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate artifact: {str(e)}"
        )

    # Create artifact in database
    artifact = Artifact(
        type=artifact_type,
        title=title,
        content=content,
        version=1,
        artifact_metadata=json.dumps(generation_metadata),
        project_id=project_id,
        user_id=current_user.id,
        conversation_id=conversation_id,
        category_id=category_id,
    )

    db.add(artifact)
    await db.commit()
    await db.refresh(artifact)

    # Parse metadata back to dict
    metadata_dict = None
    if artifact.artifact_metadata:
        try:
            metadata_dict = json.loads(artifact.artifact_metadata)
        except json.JSONDecodeError:
            pass

    return ArtifactResponse(
        id=artifact.id,
        type=artifact.type,
        title=artifact.title,
        content=artifact.content,
        version=artifact.version,
        project_id=artifact.project_id,
        user_id=artifact.user_id,
        conversation_id=artifact.conversation_id,
        category_id=artifact.category_id,
        metadata=metadata_dict,
        created_at=artifact.created_at,
        updated_at=artifact.updated_at,
    )


@router.get("", response_model=ArtifactListResponse)
async def list_artifacts(
    project_id: int = Query(..., description="Project ID"),
    type: Optional[ArtifactType] = Query(None, description="Filter by artifact type"),
    conversation_id: Optional[int] = Query(None, description="Filter by conversation"),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List artifacts with filtering and pagination

    Retrieve artifacts for a project with optional filters by type, conversation, or category.

    Args:
        project_id: Project ID (required)
        type: Optional artifact type filter
        conversation_id: Optional conversation filter
        category_id: Optional category filter
        page: Page number (default: 1)
        page_size: Items per page (default: 20, max: 100)

    Returns:
        Paginated list of artifacts
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
        raise HTTPException(status_code=404, detail="Project not found")

    # Build query
    query = select(Artifact).where(Artifact.project_id == project_id)

    if type:
        query = query.where(Artifact.type == type)
    if conversation_id is not None:
        query = query.where(Artifact.conversation_id == conversation_id)
    if category_id is not None:
        query = query.where(Artifact.category_id == category_id)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Add pagination and sorting
    offset = (page - 1) * page_size
    query = query.order_by(Artifact.created_at.desc()).offset(offset).limit(page_size)

    # Execute query
    result = await db.execute(query)
    artifacts = result.scalars().all()

    # Convert to list items
    artifact_items = [
        ArtifactListItem(
            id=artifact.id,
            type=artifact.type,
            title=artifact.title,
            version=artifact.version,
            conversation_id=artifact.conversation_id,
            category_id=artifact.category_id,
            created_at=artifact.created_at,
            updated_at=artifact.updated_at,
        )
        for artifact in artifacts
    ]

    return ArtifactListResponse(
        artifacts=artifact_items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + len(artifacts)) < total,
    )


@router.get("/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(
    artifact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get artifact by ID

    Retrieve a single artifact with full content.

    Args:
        artifact_id: Artifact ID

    Returns:
        Full artifact data with content
    """
    # Get artifact with project check
    result = await db.execute(
        select(Artifact)
        .join(Project)
        .where(
            Artifact.id == artifact_id,
            Project.owner_id == current_user.id
        )
    )
    artifact = result.scalar_one_or_none()

    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # Parse metadata
    metadata_dict = None
    if artifact.artifact_metadata:
        try:
            metadata_dict = json.loads(artifact.artifact_metadata)
        except json.JSONDecodeError:
            pass

    return ArtifactResponse(
        id=artifact.id,
        type=artifact.type,
        title=artifact.title,
        content=artifact.content,
        version=artifact.version,
        project_id=artifact.project_id,
        user_id=artifact.user_id,
        conversation_id=artifact.conversation_id,
        category_id=artifact.category_id,
        metadata=metadata_dict,
        created_at=artifact.created_at,
        updated_at=artifact.updated_at,
    )


@router.patch("/{artifact_id}", response_model=ArtifactResponse)
async def update_artifact(
    artifact_id: int,
    request: ArtifactUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update artifact

    Update artifact fields (title, content, type, etc.).
    Updates the updated_at timestamp but does not increment version.

    Args:
        artifact_id: Artifact ID
        request: Update data (all fields optional)

    Returns:
        Updated artifact
    """
    # Get artifact with project check
    result = await db.execute(
        select(Artifact)
        .join(Project)
        .where(
            Artifact.id == artifact_id,
            Project.owner_id == current_user.id
        )
    )
    artifact = result.scalar_one_or_none()

    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # Update fields if provided
    if request.title is not None:
        artifact.title = request.title
    if request.content is not None:
        artifact.content = request.content
    if request.type is not None:
        artifact.type = request.type
    if request.conversation_id is not None:
        artifact.conversation_id = request.conversation_id
    if request.category_id is not None:
        artifact.category_id = request.category_id
    if request.metadata is not None:
        artifact.artifact_metadata = json.dumps(request.metadata)

    await db.commit()
    await db.refresh(artifact)

    # Parse metadata
    metadata_dict = None
    if artifact.artifact_metadata:
        try:
            metadata_dict = json.loads(artifact.artifact_metadata)
        except json.JSONDecodeError:
            pass

    return ArtifactResponse(
        id=artifact.id,
        type=artifact.type,
        title=artifact.title,
        content=artifact.content,
        version=artifact.version,
        project_id=artifact.project_id,
        user_id=artifact.user_id,
        conversation_id=artifact.conversation_id,
        category_id=artifact.category_id,
        metadata=metadata_dict,
        created_at=artifact.created_at,
        updated_at=artifact.updated_at,
    )


@router.post("/{artifact_id}/regenerate", response_model=ArtifactResponse, status_code=201)
async def regenerate_artifact(
    artifact_id: int,
    request: ArtifactRegenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Regenerate artifact (create new version)

    Creates a new version of the artifact with updated generation parameters.
    Uses the artifact generator service to regenerate content with Claude API.

    Args:
        artifact_id: Original artifact ID
        request: Regeneration parameters (optional metadata overrides)

    Returns:
        New artifact with incremented version and regenerated content

    Raises:
        404: Artifact not found
        500: Generation failed
    """
    # Get original artifact
    result = await db.execute(
        select(Artifact)
        .join(Project)
        .where(
            Artifact.id == artifact_id,
            Project.owner_id == current_user.id
        )
    )
    original_artifact = result.scalar_one_or_none()

    if not original_artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # Parse original metadata
    original_metadata = {}
    if original_artifact.artifact_metadata:
        try:
            original_metadata = json.loads(original_artifact.artifact_metadata)
        except json.JSONDecodeError:
            pass

    # Extract temperature and max_tokens from request metadata if provided
    temperature = None
    max_tokens = None
    new_instructions = None

    if request.metadata:
        temperature = request.metadata.get("temperature")
        max_tokens = request.metadata.get("max_tokens")
        new_instructions = request.metadata.get("instructions")

    # Regenerate content using artifact generator
    try:
        regenerated_content, retrieved_chunks, generation_metadata = await artifact_generator.regenerate_artifact(
            db=db,
            original_content=original_artifact.content,
            original_metadata=original_metadata,
            artifact_type=original_artifact.type,
            title=original_artifact.title,
            project_id=original_artifact.project_id,
            new_instructions=new_instructions,
            temperature=temperature,
            max_tokens=max_tokens
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to regenerate artifact: {str(e)}"
        )

    # Create new version
    new_version = original_artifact.version + 1

    # Merge metadata (original + generation metadata + request overrides)
    new_metadata = {**original_metadata, **generation_metadata}
    if request.metadata:
        new_metadata.update(request.metadata)

    # Create new artifact with incremented version
    new_artifact = Artifact(
        type=original_artifact.type,
        title=f"{original_artifact.title} (v{new_version})",
        content=regenerated_content,
        version=new_version,
        artifact_metadata=json.dumps(new_metadata),
        project_id=original_artifact.project_id,
        user_id=current_user.id,
        conversation_id=original_artifact.conversation_id,
        category_id=original_artifact.category_id,
    )

    db.add(new_artifact)
    await db.commit()
    await db.refresh(new_artifact)

    # Parse metadata
    metadata_dict = None
    if new_artifact.artifact_metadata:
        try:
            metadata_dict = json.loads(new_artifact.artifact_metadata)
        except json.JSONDecodeError:
            pass

    return ArtifactResponse(
        id=new_artifact.id,
        type=new_artifact.type,
        title=new_artifact.title,
        content=new_artifact.content,
        version=new_artifact.version,
        project_id=new_artifact.project_id,
        user_id=new_artifact.user_id,
        conversation_id=new_artifact.conversation_id,
        category_id=new_artifact.category_id,
        metadata=metadata_dict,
        created_at=new_artifact.created_at,
        updated_at=new_artifact.updated_at,
    )


@router.delete("/{artifact_id}", status_code=204)
async def delete_artifact(
    artifact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete artifact

    Permanently delete an artifact.

    Args:
        artifact_id: Artifact ID

    Returns:
        204 No Content on success
    """
    # Get artifact with project check
    result = await db.execute(
        select(Artifact)
        .join(Project)
        .where(
            Artifact.id == artifact_id,
            Project.owner_id == current_user.id
        )
    )
    artifact = result.scalar_one_or_none()

    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    await db.delete(artifact)
    await db.commit()
