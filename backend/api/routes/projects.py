"""
KnowledgeTree Backend - Projects Routes
Project CRUD operations and management endpoints
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from core.database import get_db
from models.user import User
from models.project import Project
from models.document import Document
from models.category import Category
from models.chunk import Chunk
from schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectWithStats,
    ProjectListResponse,
)
from api.dependencies import get_current_active_user

router = APIRouter(prefix="/projects", tags=["Projects"])
logger = logging.getLogger(__name__)


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


async def get_project_stats(project_id: int, db: AsyncSession) -> dict:
    """
    Get project statistics (document count, chunk count, category count)

    Args:
        project_id: Project ID
        db: Database session

    Returns:
        Dictionary with statistics
    """
    # Count documents
    doc_result = await db.execute(
        select(func.count(Document.id)).where(Document.project_id == project_id)
    )
    document_count = doc_result.scalar() or 0

    # Count categories
    cat_result = await db.execute(
        select(func.count(Category.id)).where(Category.project_id == project_id)
    )
    category_count = cat_result.scalar() or 0

    # Count total chunks (from documents in this project)
    chunk_result = await db.execute(
        select(func.count(Chunk.id))
        .select_from(Chunk)
        .join(Document, Chunk.document_id == Document.id)
        .where(Document.project_id == project_id)
    )
    total_chunks = chunk_result.scalar() or 0

    return {
        "document_count": document_count,
        "category_count": category_count,
        "total_chunks": total_chunks,
    }


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all projects for the current user with statistics

    Returns paginated list of projects with document/category/chunk counts.
    """
    # Count total projects
    count_result = await db.execute(
        select(func.count(Project.id)).where(Project.owner_id == current_user.id)
    )
    total = count_result.scalar() or 0

    # Get paginated projects
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Project)
        .where(Project.owner_id == current_user.id)
        .order_by(Project.updated_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    projects = result.scalars().all()

    # Add statistics to each project
    projects_with_stats = []
    for project in projects:
        stats = await get_project_stats(project.id, db)
        project_dict = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "color": project.color,
            "owner_id": project.owner_id,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            **stats,
        }
        projects_with_stats.append(ProjectWithStats(**project_dict))

    return ProjectListResponse(
        projects=projects_with_stats,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{project_id}", response_model=ProjectWithStats)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific project by ID with statistics

    Returns project details with document/category/chunk counts.
    """
    project = await get_project_or_404(project_id, current_user, db)
    stats = await get_project_stats(project.id, db)

    project_dict = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "color": project.color,
        "owner_id": project.owner_id,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        **stats,
    }

    return ProjectWithStats(**project_dict)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new project

    Creates a new project owned by the current user.
    """
    # Create new project
    new_project = Project(
        name=project_data.name,
        description=project_data.description,
        color=project_data.color,
        owner_id=current_user.id,
    )

    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)

    logger.info(f"Project created: {new_project.id} by user {current_user.id}")

    return ProjectResponse.model_validate(new_project)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an existing project

    Updates project fields. Only provided fields will be updated.
    """
    project = await get_project_or_404(project_id, current_user, db)

    # Update fields if provided
    update_data = project_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    await db.commit()
    await db.refresh(project)

    logger.info(f"Project updated: {project.id} by user {current_user.id}")

    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a project

    Deletes the project and all associated data (categories, documents, conversations).
    This operation is irreversible.
    """
    project = await get_project_or_404(project_id, current_user, db)

    # Get statistics before deletion for logging
    stats = await get_project_stats(project.id, db)

    await db.delete(project)
    await db.commit()

    logger.info(
        f"Project deleted: {project.id} by user {current_user.id} "
        f"(had {stats['document_count']} documents, "
        f"{stats['category_count']} categories, "
        f"{stats['total_chunks']} chunks)"
    )

    return None
