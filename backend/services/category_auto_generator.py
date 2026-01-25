"""
KnowledgeTree Backend - Category Auto-Generator Service

Automatically generates category tree from PDF Table of Contents.
Converts TocEntry hierarchy to Category database records.

Features:
- Recursive category creation from ToC structure
- Automatic depth and order assignment
- Color rotation from predefined palette
- Icon assignment based on hierarchy level
- Duplicate name handling with suffixes

Author: KnowledgeTree Team
Date: 2026-01-21
"""

import logging
from typing import List, Optional, Dict, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.category import Category
from models.project import Project
from services.toc_extractor import TocEntry, TocExtractionResult

logger = logging.getLogger(__name__)


# Pastel color palette for categories (8 colors)
PASTEL_COLORS = [
    "#E6E6FA",  # Lavender (default)
    "#FFE4E1",  # Misty Rose
    "#E0FFE0",  # Light Green
    "#E0F4FF",  # Light Blue
    "#FFF4E0",  # Light Yellow
    "#FFE0F0",  # Light Pink
    "#E0F0FF",  # Light Cyan
    "#F0E0FF",  # Light Purple
]

# Icon mapping by hierarchy level
LEVEL_ICONS = {
    0: "BookOpen",      # Root chapters
    1: "FileText",      # Sections
    2: "File",          # Subsections
    3: "FileCode",      # Sub-subsections
    4: "FileCheck",     # Deep nesting (rare)
}
DEFAULT_ICON = "Folder"


class CategoryAutoGenerator:
    """
    Automatic category tree generator from PDF Table of Contents

    Converts ToC structure into hierarchical Category records with:
    - Automatic depth tracking
    - Sequential ordering within siblings
    - Color rotation for visual distinction
    - Icon assignment by level
    - Duplicate name resolution
    """

    def __init__(
        self,
        db_session: AsyncSession,
        color_palette: Optional[List[str]] = None,
        icon_mapping: Optional[Dict[int, str]] = None
    ):
        """
        Initialize category auto-generator

        Args:
            db_session: SQLAlchemy async database session
            color_palette: Custom color palette (hex colors), uses PASTEL_COLORS if None
            icon_mapping: Custom icon mapping by level, uses LEVEL_ICONS if None
        """
        self.db = db_session
        self.color_palette = color_palette or PASTEL_COLORS
        self.icon_mapping = icon_mapping or LEVEL_ICONS

        # Track created categories for duplicate detection
        self._created_names: Dict[Tuple[int, Optional[int]], List[str]] = {}

    def _get_color(self, index: int) -> str:
        """Get color from palette by index (rotates if exceeds palette size)"""
        return self.color_palette[index % len(self.color_palette)]

    def _get_icon(self, level: int) -> str:
        """Get icon for hierarchy level"""
        return self.icon_mapping.get(level, DEFAULT_ICON)

    def _make_unique_name(
        self,
        name: str,
        project_id: int,
        parent_id: Optional[int]
    ) -> str:
        """
        Ensure unique category name within parent scope

        If name exists in same parent, appends " (2)", " (3)", etc.

        Args:
            name: Proposed category name
            project_id: Project ID for tracking
            parent_id: Parent category ID (None for root)

        Returns:
            Unique category name
        """
        key = (project_id, parent_id)

        if key not in self._created_names:
            self._created_names[key] = []

        existing = self._created_names[key]

        # Check if name already used in this parent
        if name not in existing:
            self._created_names[key].append(name)
            return name

        # Find unique suffix
        counter = 2
        while f"{name} ({counter})" in existing:
            counter += 1

        unique_name = f"{name} ({counter})"
        self._created_names[key].append(unique_name)

        logger.debug(f"Renamed duplicate: '{name}' → '{unique_name}'")
        return unique_name

    async def generate_from_toc(
        self,
        toc_result: TocExtractionResult,
        project_id: int,
        color_start_index: int = 0,
        max_categories: int = 1000
    ) -> List[Category]:
        """
        Generate category tree from ToC extraction result

        Creates hierarchical Category records matching ToC structure.
        Categories are created recursively with proper parent-child relationships.

        Args:
            toc_result: ToC extraction result containing TocEntry hierarchy
            project_id: Project ID to associate categories with
            color_start_index: Starting index for color rotation (default: 0)
            max_categories: Maximum number of categories to create (safety limit)

        Returns:
            List of created root Category objects

        Raises:
            ValueError: If ToC extraction failed or project not found
            RuntimeError: If max_categories limit exceeded

        Example:
            >>> generator = CategoryAutoGenerator(db_session)
            >>> categories = await generator.generate_from_toc(toc_result, project_id=1)
            >>> print(f"Created {len(categories)} root categories")
        """
        # Validate ToC result
        if not toc_result.success:
            raise ValueError(f"ToC extraction failed: {toc_result.error}")

        if not toc_result.entries:
            logger.warning("ToC extraction succeeded but no entries found")
            return []

        # Verify project exists
        project_result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = project_result.scalar_one_or_none()

        if not project:
            raise ValueError(f"Project {project_id} not found")

        # Reset duplicate tracking
        self._created_names = {}

        # Create categories recursively
        logger.info(
            f"Generating categories from ToC: {toc_result.total_entries} entries, "
            f"max depth {toc_result.max_depth}"
        )

        created_categories = []
        category_count = 0

        for idx, toc_entry in enumerate(toc_result.entries):
            color_index = color_start_index + idx

            # Create category tree recursively
            categories = await self._create_category_recursive(
                toc_entry=toc_entry,
                project_id=project_id,
                parent_id=None,
                order=idx,
                color_index=color_index,
                max_categories=max_categories,
                current_count=category_count
            )

            created_categories.extend(categories)
            category_count += sum(1 + len(cat.children) for cat in categories)

            # Safety check
            if category_count > max_categories:
                raise RuntimeError(
                    f"Exceeded max_categories limit ({max_categories}). "
                    f"ToC may be too large or malformed."
                )

        # Commit all categories
        await self.db.commit()

        logger.info(f"✅ Created {category_count} categories from ToC")
        return created_categories

    async def _create_category_recursive(
        self,
        toc_entry: TocEntry,
        project_id: int,
        parent_id: Optional[int],
        order: int,
        color_index: int,
        max_categories: int,
        current_count: int
    ) -> List[Category]:
        """
        Recursively create Category from TocEntry with children

        Args:
            toc_entry: ToC entry to convert
            project_id: Project ID
            parent_id: Parent category ID (None for root)
            order: Display order within siblings
            color_index: Index for color palette
            max_categories: Maximum total categories allowed
            current_count: Current number of categories created

        Returns:
            List containing created category (with children populated)
        """
        # Safety check
        if current_count >= max_categories:
            logger.warning(f"Reached max_categories limit: {max_categories}")
            return []

        # Create unique name
        unique_name = self._make_unique_name(
            name=toc_entry.title,
            project_id=project_id,
            parent_id=parent_id
        )

        # Create category
        category = Category(
            name=unique_name,
            description=f"Auto-generated from PDF ToC (page {toc_entry.page or 'N/A'})",
            color=self._get_color(color_index),
            icon=self._get_icon(toc_entry.level),
            depth=toc_entry.level,
            order=order,
            parent_id=parent_id,
            project_id=project_id
        )

        # Add to session and flush to get ID
        self.db.add(category)
        await self.db.flush()
        await self.db.refresh(category)

        logger.debug(
            f"Created category: '{category.name}' (ID: {category.id}, "
            f"level: {category.depth}, parent: {parent_id})"
        )

        # Create children recursively
        for child_idx, child_entry in enumerate(toc_entry.children):
            child_color_index = color_index + child_idx + 1

            await self._create_category_recursive(
                toc_entry=child_entry,
                project_id=project_id,
                parent_id=category.id,  # Parent is this category
                order=child_idx,
                color_index=child_color_index,
                max_categories=max_categories,
                current_count=current_count + 1 + child_idx
            )

        # Refresh to get children relationship populated
        await self.db.refresh(category, attribute_names=['children'])

        return [category]

    async def preview_categories(
        self,
        toc_result: TocExtractionResult,
        color_start_index: int = 0
    ) -> List[Dict]:
        """
        Preview category structure without creating database records

        Useful for UI preview before user confirms auto-generation.

        Args:
            toc_result: ToC extraction result
            color_start_index: Starting color index

        Returns:
            List of category dictionaries with:
                - name, level, color, icon, children (nested)
        """
        if not toc_result.success or not toc_result.entries:
            return []

        def _entry_to_dict(entry: TocEntry, idx: int, parent_level: int = -1) -> Dict:
            """Convert TocEntry to preview dictionary"""
            color_index = color_start_index + idx

            return {
                'name': entry.title,
                'level': entry.level,
                'page': entry.page,
                'color': self._get_color(color_index),
                'icon': self._get_icon(entry.level),
                'children': [
                    _entry_to_dict(child, idx + i + 1, entry.level)
                    for i, child in enumerate(entry.children)
                ]
            }

        return [
            _entry_to_dict(entry, idx)
            for idx, entry in enumerate(toc_result.entries)
        ]


# Convenience function for quick category generation
async def generate_categories_from_toc(
    toc_result: TocExtractionResult,
    project_id: int,
    db_session: AsyncSession
) -> List[Category]:
    """
    Quick category generation from ToC result

    Args:
        toc_result: ToC extraction result
        project_id: Project ID
        db_session: Database session

    Returns:
        List of created root Category objects
    """
    generator = CategoryAutoGenerator(db_session)
    return await generator.generate_from_toc(toc_result, project_id)
