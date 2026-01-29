"""
KnowledgeTree Backend - Categories Routes
Category CRUD operations and tree management endpoints
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from core.database import get_db
from models.user import User
from models.category import Category
from models.project import Project
from models.chunk import Chunk
from models.document_table import DocumentTable
from models.document_formula import DocumentFormula
from schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryTreeNode,
    CategoryListResponse,
    CategoryContentResponse,
)
from api.dependencies import get_current_active_user

router = APIRouter(prefix="/categories", tags=["Categories"])
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


async def get_category_or_404(
    category_id: int,
    current_user: User,
    db: AsyncSession
) -> Category:
    """
    Get category by ID with access control

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
            Category.id == category_id,
            Project.owner_id == current_user.id
        )
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found or access denied"
        )

    return category


@router.get("/{category_id}/content", response_model=CategoryContentResponse)
async def get_category_content(
    category_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get content assigned to a category (chunks, tables, formulas)

    Returns all chunks, tables, and formulas that belong to this category.
    Content is assigned based on page ranges during category tree generation.

    Args:
        category_id: Category ID

    Returns:
        CategoryContentResponse with all content items
    """
    # Get category with access control
    category = await get_category_or_404(category_id, current_user, db)

    # Get chunks for this category
    chunks_result = await db.execute(
        select(Chunk)
        .where(Chunk.category_id == category_id)
        .order_by(Chunk.chunk_index)
    )
    chunks = chunks_result.scalars().all()

    # Get tables for this category
    tables_result = await db.execute(
        select(DocumentTable)
        .where(DocumentTable.category_id == category_id)
        .order_by(DocumentTable.table_index)
    )
    tables = tables_result.scalars().all()

    # Get formulas for this category
    formulas_result = await db.execute(
        select(DocumentFormula)
        .where(DocumentFormula.category_id == category_id)
        .order_by(DocumentFormula.formula_index)
    )
    formulas = formulas_result.scalars().all()

    logger.info(
        f"Category {category_id} content: {len(chunks)} chunks, "
        f"{len(tables)} tables, {len(formulas)} formulas"
    )

    return CategoryContentResponse(
        category_id=category_id,
        category_name=category.name,
        chunks=[
            {
                "id": chunk.id,
                "text": chunk.text,
                "chunk_index": chunk.chunk_index,
            }
            for chunk in chunks
        ],
        tables=[
            {
                "id": table.id,
                "table_index": table.table_index,
                "page_number": table.page_number,
                "row_count": table.row_count,
                "col_count": table.col_count,
                "table_data": table.table_data,
            }
            for table in tables
        ],
        formulas=[
            {
                "id": formula.id,
                "formula_index": formula.formula_index,
                "page_number": formula.page_number,
                "latex_content": formula.latex_content,
                "context_before": formula.context_before,
                "context_after": formula.context_after,
            }
            for formula in formulas
        ],
        total_chunks=len(chunks),
        total_tables=len(tables),
        total_formulas=len(formulas),
    )


@router.get("/", response_model=CategoryListResponse)
async def list_categories(
    project_id: int,
    parent_id: Optional[int] = Query(None, description="Filter by parent category (null for root)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List categories in a project

    Supports filtering by parent_id to get specific subtree.
    Use parent_id=null to get only root categories.

    Args:
        project_id: Project ID to list categories from
        parent_id: Optional parent category ID filter
        page: Page number (1-based)
        page_size: Items per page (max 100)

    Returns:
        Paginated list of categories
    """
    # Verify project access
    await get_project_or_404(project_id, current_user, db)

    # Build query with parent filter
    query = select(Category).where(Category.project_id == project_id)

    if parent_id is not None:
        query = query.where(Category.parent_id == parent_id)
    else:
        # If parent_id not specified, return all categories
        pass

    # Get total count
    count_query = select(func.count(Category.id)).where(Category.project_id == project_id)
    if parent_id is not None:
        count_query = count_query.where(Category.parent_id == parent_id)

    count_result = await db.execute(count_query)
    total = count_result.scalar()

    # Get categories with pagination
    offset = (page - 1) * page_size
    result = await db.execute(
        query
        .order_by(Category.order.asc(), Category.id.asc())
        .limit(page_size)
        .offset(offset)
    )
    categories = result.scalars().all()

    return CategoryListResponse(
        categories=[CategoryResponse.model_validate(cat) for cat in categories],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/tree/{project_id}", response_model=List[CategoryTreeNode])
async def get_category_tree(
    project_id: int,
    parent_id: Optional[int] = Query(None, description="Root category to start from"),
    max_depth: Optional[int] = Query(None, ge=1, le=10, description="Maximum depth to fetch"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get hierarchical category tree for a project

    Returns nested tree structure with children populated recursively.

    Args:
        project_id: Project ID
        parent_id: Optional root category (null for full tree)
        max_depth: Optional maximum depth to fetch (1-10)

    Returns:
        List of root CategoryTreeNode objects with children populated
    """
    # Verify project access
    await get_project_or_404(project_id, current_user, db)

    # Get all categories for the project
    result = await db.execute(
        select(Category)
        .where(Category.project_id == project_id)
        .order_by(Category.order.asc(), Category.id.asc())
    )
    all_categories = result.scalars().all()

    if not all_categories:
        return []

    # Build tree structure
    tree = _build_tree_structure(all_categories, parent_id, max_depth)

    return tree


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get category by ID

    Args:
        category_id: Category ID

    Returns:
        Category details
    """
    category = await get_category_or_404(category_id, current_user, db)
    return CategoryResponse.model_validate(category)


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new category

    Args:
        category_data: Category creation data
        project_id: Project ID to create category in

    Returns:
        Created category

    Raises:
        400: Invalid parent_id or depth exceeds limit
        404: Project not found
    """
    # Verify project access
    await get_project_or_404(project_id, current_user, db)

    # Verify parent exists if specified
    if category_data.parent_id is not None:
        parent_result = await db.execute(
            select(Category).where(
                Category.id == category_data.parent_id,
                Category.project_id == project_id
            )
        )
        parent = parent_result.scalar_one_or_none()

        if not parent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent category not found in this project"
            )

        # Validate depth
        if parent.depth >= 9:  # Max depth is 10 (0-9)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot create category: parent depth {parent.depth} would exceed maximum depth of 10"
            )

        # Auto-calculate depth if not provided or incorrect
        expected_depth = parent.depth + 1
        if category_data.depth != expected_depth:
            logger.warning(
                f"Depth mismatch: provided {category_data.depth}, expected {expected_depth}. "
                f"Using expected depth."
            )
            category_data.depth = expected_depth

    else:
        # Root category
        if category_data.depth != 0:
            logger.warning(f"Root category depth should be 0, got {category_data.depth}. Setting to 0.")
            category_data.depth = 0

    try:
        # Create category
        category = Category(
            name=category_data.name,
            description=category_data.description,
            color=category_data.color,
            icon=category_data.icon,
            depth=category_data.depth,
            order=category_data.order,
            parent_id=category_data.parent_id,
            project_id=project_id
        )

        db.add(category)
        await db.commit()
        await db.refresh(category)

        logger.info(f"Created category: {category.id} - {category.name}")
        return CategoryResponse.model_validate(category)

    except Exception as e:
        logger.error(f"Category creation failed: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Category creation failed: {str(e)}"
        )


@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    update_data: CategoryUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update category metadata

    Note: Changing parent_id will affect the entire subtree.
    Depth recalculation is NOT automatic - use with caution.

    Args:
        category_id: Category ID to update
        update_data: Fields to update

    Returns:
        Updated category
    """
    category = await get_category_or_404(category_id, current_user, db)

    # Update fields
    if update_data.name is not None:
        category.name = update_data.name
    if update_data.description is not None:
        category.description = update_data.description
    if update_data.color is not None:
        category.color = update_data.color
    if update_data.icon is not None:
        category.icon = update_data.icon
    if update_data.order is not None:
        category.order = update_data.order

    # Handle parent_id change
    if update_data.parent_id is not None:
        # Verify new parent exists
        if update_data.parent_id != category.parent_id:
            parent_result = await db.execute(
                select(Category).where(
                    Category.id == update_data.parent_id,
                    Category.project_id == category.project_id
                )
            )
            new_parent = parent_result.scalar_one_or_none()

            if not new_parent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="New parent category not found"
                )

            # Prevent circular reference
            if update_data.parent_id == category_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Category cannot be its own parent"
                )

            # TODO: Add check for circular reference in ancestors
            # For now, just update
            category.parent_id = update_data.parent_id

            logger.warning(
                f"Changed parent of category {category_id} to {update_data.parent_id}. "
                f"Depth recalculation NOT automatic - verify tree structure."
            )

    await db.commit()
    await db.refresh(category)

    logger.info(f"Updated category: {category_id}")
    return CategoryResponse.model_validate(category)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    cascade: bool = Query(True, description="Delete all children (cascade)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete category

    By default, deletes all children recursively (cascade=true).
    If cascade=false and category has children, request will fail.

    Args:
        category_id: Category ID to delete
        cascade: Whether to delete children (default: true)

    Returns:
        204 No Content

    Raises:
        400: Category has children and cascade=false
    """
    category = await get_category_or_404(category_id, current_user, db)

    # Check for children
    children_result = await db.execute(
        select(func.count(Category.id)).where(Category.parent_id == category_id)
    )
    children_count = children_result.scalar()

    if children_count > 0 and not cascade:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category has {children_count} children. Use cascade=true to delete all."
        )

    # Delete category (cascade handled by SQLAlchemy relationship)
    await db.delete(category)
    await db.commit()

    logger.info(f"Deleted category: {category_id} (cascade={cascade})")
    return None


def _build_tree_structure(
    categories: List[Category],
    root_parent_id: Optional[int],
    max_depth: Optional[int]
) -> List[CategoryTreeNode]:
    """
    Build hierarchical tree from flat list of categories

    Args:
        categories: Flat list of all categories
        root_parent_id: Parent ID to start from (None for roots)
        max_depth: Maximum depth to include (None for unlimited)

    Returns:
        List of CategoryTreeNode with children populated
    """
    # Create lookup map
    category_map = {cat.id: cat for cat in categories}

    # Group by parent_id
    children_map = {}
    for cat in categories:
        parent_key = cat.parent_id
        if parent_key not in children_map:
            children_map[parent_key] = []
        children_map[parent_key].append(cat)

    def _build_node(category: Category, current_depth: int) -> CategoryTreeNode:
        """Recursively build tree node"""
        # Create node from category fields (avoid lazy loading)
        node = CategoryTreeNode(
            id=category.id,
            name=category.name,
            description=category.description,
            color=category.color,
            icon=category.icon,
            depth=category.depth,
            order=category.order,
            parent_id=category.parent_id,
            project_id=category.project_id,
            created_at=category.created_at,
            updated_at=category.updated_at,
            children=[]  # Will be populated below
        )

        # Check depth limit
        if max_depth is not None and current_depth >= max_depth:
            return node

        # Get children
        children = children_map.get(category.id, [])

        # Recursively build children
        node.children = [
            _build_node(child, current_depth + 1)
            for child in sorted(children, key=lambda c: (c.order, c.id))
        ]

        return node

    # Find root categories
    root_categories = children_map.get(root_parent_id, [])

    # Build tree
    tree = [
        _build_node(cat, 0)
        for cat in sorted(root_categories, key=lambda c: (c.order, c.id))
    ]

    return tree
