"""
Content Workbench API Routes
Content editing, versioning, AI operations, and template management
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from core.database import get_db
from models.user import User
from models.category import Category
from models.project import Project
from models.content import ContentVersion, ExtractedQuote, ContentTemplate
from schemas.content import (
    # Response schemas
    ContentVersionResponse,
    ExtractedQuoteResponse,
    ContentTemplateResponse,
    AIOperationResponse,
    VersionComparisonResponse,
    # Request schemas
    SaveDraftRequest,
    PublishContentRequest,
    RestoreVersionRequest,
    CompareVersionsRequest,
    SummarizeRequest,
    ExpandRequest,
    SimplifyRequest,
    RewriteToneRequest,
    ExtractQuotesRequest,
    GenerateOutlineRequest,
    ContentTemplateCreate,
)
from schemas.category import CategoryResponse
from api.dependencies import get_current_active_user
from services.content_editor_service import ContentEditorService
from services.content_rewriter_service import ContentRewriterService
from core.exceptions import NotFoundException, ValidationException

router = APIRouter(prefix="/content", tags=["Content Workbench"])
logger = logging.getLogger(__name__)


# Access Control Helpers

async def get_category_with_access(
    category_id: int,
    current_user: User,
    db: AsyncSession
) -> Category:
    """
    Get category by ID with access control.

    Verifies user owns the project that contains this category.

    Args:
        category_id: Category ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Category object

    Raises:
        HTTPException: 404 if not found or access denied
    """
    result = await db.execute(
        select(Category)
        .join(Project)
        .where(
            and_(
                Category.id == category_id,
                Project.owner_id == current_user.id
            )
        )
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found or access denied"
        )

    return category


# Content Editor Endpoints

@router.post(
    "/categories/{category_id}/draft",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Save draft content",
    description="Save draft content for a category with automatic version creation"
)
async def save_draft(
    category_id: int,
    request: SaveDraftRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Save draft content with optional versioning.

    Creates a new version snapshot if auto_version=True.
    Updates category.draft_content and category.updated_at.
    """
    # Verify access
    await get_category_with_access(category_id, current_user, db)

    # Save draft
    editor_service = ContentEditorService()
    category = await editor_service.save_draft(
        db=db,
        category_id=category_id,
        draft_content=request.draft_content,
        user_id=current_user.id,
        change_summary=request.change_summary,
        auto_version=request.auto_version
    )

    logger.info(f"User {current_user.id} saved draft for category {category_id}")

    return CategoryResponse.model_validate(category)


@router.post(
    "/categories/{category_id}/publish",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Publish content",
    description="Publish draft content (draft → published, status → published)"
)
async def publish_content(
    category_id: int,
    request: PublishContentRequest = PublishContentRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Publish draft content.

    Moves draft_content → published_content,
    sets status to 'published',
    records publication timestamp and reviewer.
    """
    # Verify access
    await get_category_with_access(category_id, current_user, db)

    # Publish
    editor_service = ContentEditorService()
    category = await editor_service.publish(
        db=db,
        category_id=category_id,
        user_id=current_user.id,
        create_version=request.create_version
    )

    logger.info(f"User {current_user.id} published category {category_id}")

    return CategoryResponse.model_validate(category)


@router.post(
    "/categories/{category_id}/unpublish",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Unpublish content",
    description="Set content status back to draft (keeps published_content intact)"
)
async def unpublish_content(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Unpublish content (set status back to draft).

    Useful for temporarily hiding content or making edits.
    """
    # Verify access
    await get_category_with_access(category_id, current_user, db)

    # Unpublish
    editor_service = ContentEditorService()
    category = await editor_service.unpublish(
        db=db,
        category_id=category_id,
        user_id=current_user.id
    )

    logger.info(f"User {current_user.id} unpublished category {category_id}")

    return CategoryResponse.model_validate(category)


# Version Management Endpoints

@router.get(
    "/categories/{category_id}/versions",
    response_model=List[ContentVersionResponse],
    status_code=status.HTTP_200_OK,
    summary="Get version history",
    description="Retrieve version history for a category (newest first)"
)
async def get_versions(
    category_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get version history for a category.

    Returns versions in reverse chronological order (newest first).
    """
    # Verify access
    await get_category_with_access(category_id, current_user, db)

    # Get versions
    editor_service = ContentEditorService()
    versions = await editor_service.get_versions(
        db=db,
        category_id=category_id,
        limit=limit,
        offset=offset
    )

    return [ContentVersionResponse.model_validate(v) for v in versions]


@router.get(
    "/categories/{category_id}/versions/{version_number}",
    response_model=ContentVersionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get specific version",
    description="Retrieve content from a specific version number"
)
async def get_version(
    category_id: int,
    version_number: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get specific version by number.
    """
    # Verify access
    await get_category_with_access(category_id, current_user, db)

    # Get version
    editor_service = ContentEditorService()
    version = await editor_service.get_version(
        db=db,
        category_id=category_id,
        version_number=version_number
    )

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version_number} not found"
        )

    return ContentVersionResponse.model_validate(version)


@router.post(
    "/categories/{category_id}/versions/restore",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Restore version",
    description="Restore content from a specific version to draft"
)
async def restore_version(
    category_id: int,
    request: RestoreVersionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Restore content from a specific version.

    Sets category.draft_content to the content from the specified version.
    """
    # Verify access
    await get_category_with_access(category_id, current_user, db)

    # Restore
    editor_service = ContentEditorService()
    category = await editor_service.restore_version(
        db=db,
        category_id=category_id,
        version_number=request.version_number,
        user_id=current_user.id,
        create_new_version=request.create_new_version
    )

    logger.info(
        f"User {current_user.id} restored category {category_id} "
        f"to version {request.version_number}"
    )

    return CategoryResponse.model_validate(category)


@router.post(
    "/categories/{category_id}/versions/compare",
    response_model=VersionComparisonResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare versions",
    description="Get content from two versions for comparison"
)
async def compare_versions(
    category_id: int,
    request: CompareVersionsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get content from two versions for comparison.

    Useful for diff visualization in frontend.
    """
    # Verify access
    await get_category_with_access(category_id, current_user, db)

    # Compare
    editor_service = ContentEditorService()
    comparison = await editor_service.compare_versions(
        db=db,
        category_id=category_id,
        version_a=request.version_a,
        version_b=request.version_b
    )

    return comparison


# AI Rewriting Endpoints

@router.post(
    "/ai/summarize",
    response_model=AIOperationResponse,
    status_code=status.HTTP_200_OK,
    summary="Summarize content",
    description="Create concise summary using AI"
)
async def summarize(
    request: SummarizeRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Create concise summary of content.
    """
    rewriter_service = ContentRewriterService()
    result = await rewriter_service.summarize(
        content=request.content,
        max_length=request.max_length,
        focus=request.focus
    )

    logger.info(f"User {current_user.id} summarized content")

    return AIOperationResponse(
        result=result,
        operation="summarize"
    )


@router.post(
    "/ai/expand",
    response_model=AIOperationResponse,
    status_code=status.HTTP_200_OK,
    summary="Expand content",
    description="Add detail and context using AI"
)
async def expand(
    request: ExpandRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Expand content with additional detail and context.
    """
    rewriter_service = ContentRewriterService()
    result = await rewriter_service.expand(
        content=request.content,
        target_length=request.target_length,
        add_details=request.add_details
    )

    logger.info(f"User {current_user.id} expanded content")

    return AIOperationResponse(
        result=result,
        operation="expand"
    )


@router.post(
    "/ai/simplify",
    response_model=AIOperationResponse,
    status_code=status.HTTP_200_OK,
    summary="Simplify content",
    description="Make content more accessible using AI"
)
async def simplify(
    request: SimplifyRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Simplify content for better accessibility.
    """
    rewriter_service = ContentRewriterService()
    result = await rewriter_service.simplify(
        content=request.content,
        reading_level=request.reading_level.value
    )

    logger.info(f"User {current_user.id} simplified content")

    return AIOperationResponse(
        result=result,
        operation="simplify"
    )


@router.post(
    "/ai/rewrite-tone",
    response_model=AIOperationResponse,
    status_code=status.HTTP_200_OK,
    summary="Rewrite tone",
    description="Change content tone/style using AI"
)
async def rewrite_tone(
    request: RewriteToneRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Rewrite content in a different tone or style.
    """
    rewriter_service = ContentRewriterService()
    result = await rewriter_service.rewrite_tone(
        content=request.content,
        tone=request.tone.value,
        preserve_facts=request.preserve_facts
    )

    logger.info(f"User {current_user.id} rewrote content tone to {request.tone.value}")

    return AIOperationResponse(
        result=result,
        operation="rewrite_tone"
    )


@router.post(
    "/categories/{category_id}/extract-quotes",
    response_model=List[ExtractedQuoteResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Extract quotes",
    description="AI-powered quote extraction with context"
)
async def extract_quotes(
    category_id: int,
    request: ExtractQuotesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Extract key quotes from content using AI.

    Saves quotes to database with context.
    """
    # Verify access
    await get_category_with_access(category_id, current_user, db)

    # Extract quotes
    rewriter_service = ContentRewriterService()
    quote_types = [qt.value for qt in request.quote_types] if request.quote_types else None

    quotes = await rewriter_service.extract_quotes(
        db=db,
        category_id=category_id,
        content=request.content,
        max_quotes=request.max_quotes,
        quote_types=quote_types
    )

    logger.info(f"User {current_user.id} extracted {len(quotes)} quotes for category {category_id}")

    return [ExtractedQuoteResponse.model_validate(q) for q in quotes]


@router.get(
    "/categories/{category_id}/quotes",
    response_model=List[ExtractedQuoteResponse],
    status_code=status.HTTP_200_OK,
    summary="Get extracted quotes",
    description="Retrieve all quotes for a category"
)
async def get_quotes(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all extracted quotes for a category.
    """
    # Verify access
    await get_category_with_access(category_id, current_user, db)

    # Get quotes
    result = await db.execute(
        select(ExtractedQuote)
        .where(ExtractedQuote.category_id == category_id)
        .order_by(ExtractedQuote.created_at.desc())
    )
    quotes = result.scalars().all()

    return [ExtractedQuoteResponse.model_validate(q) for q in quotes]


@router.post(
    "/ai/generate-outline",
    response_model=AIOperationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate outline",
    description="Generate content outline for a topic using AI"
)
async def generate_outline(
    request: GenerateOutlineRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate content outline for a topic.

    Useful for planning content structure before writing.
    """
    rewriter_service = ContentRewriterService()
    result = await rewriter_service.generate_outline(
        topic=request.topic,
        depth=request.depth,
        style=request.style.value
    )

    logger.info(f"User {current_user.id} generated outline for: {request.topic}")

    return AIOperationResponse(
        result=result,
        operation="generate_outline"
    )


# Template Management Endpoints

@router.post(
    "/templates",
    response_model=ContentTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create template",
    description="Create a new content template"
)
async def create_template(
    request: ContentTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new content template.
    """
    # Convert sections to JSONB structure
    structure = {
        "sections": [
            {
                "title": section.title,
                "prompt": section.prompt,
                "order": section.order
            }
            for section in request.sections
        ]
    }

    # Create template
    template = ContentTemplate(
        name=request.name,
        description=request.description,
        template_type=request.template_type.value,
        structure=structure,
        is_public=request.is_public,
        created_by=current_user.id
    )

    db.add(template)
    await db.commit()
    await db.refresh(template)

    logger.info(f"User {current_user.id} created template: {template.name}")

    return ContentTemplateResponse.model_validate(template)


@router.get(
    "/templates",
    response_model=List[ContentTemplateResponse],
    status_code=status.HTTP_200_OK,
    summary="List templates",
    description="Get all available content templates"
)
async def get_templates(
    template_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all available content templates.

    Returns public templates and user's private templates.
    """
    # Build query
    conditions = [
        or_(
            ContentTemplate.is_public == True,
            ContentTemplate.created_by == current_user.id
        )
    ]

    if template_type:
        conditions.append(ContentTemplate.template_type == template_type)

    # Execute query
    result = await db.execute(
        select(ContentTemplate)
        .where(and_(*conditions))
        .order_by(ContentTemplate.created_at.desc())
    )
    templates = result.scalars().all()

    return [ContentTemplateResponse.model_validate(t) for t in templates]


@router.get(
    "/templates/{template_id}",
    response_model=ContentTemplateResponse,
    status_code=status.HTTP_200_OK,
    summary="Get template",
    description="Get a specific content template"
)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific content template.
    """
    result = await db.execute(
        select(ContentTemplate)
        .where(
            and_(
                ContentTemplate.id == template_id,
                or_(
                    ContentTemplate.is_public == True,
                    ContentTemplate.created_by == current_user.id
                )
            )
        )
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found or access denied"
        )

    return ContentTemplateResponse.model_validate(template)
