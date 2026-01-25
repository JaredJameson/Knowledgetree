"""
KnowledgeTree Backend - Category Tree Generator Service
Convert ToC entries from PDFs to Category tree structure
"""

import logging
import re
from typing import List, Optional, Dict, Tuple
from collections import defaultdict

from models.category import Category
from services.toc_extractor import TocEntry, TocExtractionResult

logger = logging.getLogger(__name__)


class CategoryTreeGenerator:
    """
    Service for generating Category tree from ToC extraction results

    Features:
    - Maps TocEntry → Category with proper hierarchy
    - Generates URL-friendly slugs from titles
    - Assigns colors and icons automatically
    - Validates depth limits and duplicate names
    - Preserves ToC structure and page numbers
    """

    # 8 pastel colors for categories (from design system)
    PASTEL_COLORS = [
        "#E6E6FA",  # Lavender
        "#FFE4E1",  # Misty Rose
        "#E0FFE0",  # Light Green
        "#FFE4B5",  # Moccasin
        "#E0F4FF",  # Light Blue
        "#FFE4FF",  # Light Pink
        "#FFEAA7",  # Light Yellow
        "#DCD0FF",  # Light Purple
    ]

    # Icons by depth level
    DEPTH_ICONS = {
        0: "Book",           # Root level (chapters)
        1: "BookOpen",       # First level (sections)
        2: "FileText",       # Second level (subsections)
        3: "File",           # Third level
        4: "FileCode",       # Fourth level
        5: "FileJson",       # Fifth level
    }
    DEFAULT_ICON = "Folder"  # For depth > 5

    MAX_DEPTH = 10  # Category tree max depth

    def __init__(self):
        """Initialize the generator"""
        self._color_index = 0
        self._slug_counters: Dict[str, int] = defaultdict(int)

    def generate_tree(
        self,
        toc_result: TocExtractionResult,
        project_id: int,
        parent_id: Optional[int] = None,
        validate_depth: bool = True
    ) -> Tuple[List[Category], Dict[str, any]]:
        """
        Generate Category tree from ToC extraction result

        Args:
            toc_result: ToC extraction result with entries
            project_id: Project ID for categories
            parent_id: Optional parent category ID (for appending to existing tree)
            validate_depth: Validate max depth limit

        Returns:
            Tuple of (list of Category objects, metadata dict)

        Raises:
            ValueError: If ToC extraction failed or depth exceeds limit

        Example:
            >>> generator = CategoryTreeGenerator()
            >>> toc_result = extractor.extract(pdf_path)
            >>> categories, metadata = generator.generate_tree(toc_result, project_id=1)
            >>> # categories is list of Category objects ready for db.add()
        """
        if not toc_result.success:
            raise ValueError(f"ToC extraction failed: {toc_result.error}")

        if not toc_result.entries:
            raise ValueError("No ToC entries found in extraction result")

        # Validate depth
        if validate_depth and toc_result.max_depth >= self.MAX_DEPTH:
            logger.warning(
                f"ToC depth ({toc_result.max_depth}) exceeds recommended limit ({self.MAX_DEPTH}). "
                f"Categories beyond depth {self.MAX_DEPTH - 1} will be skipped."
            )

        # Reset state for new tree generation
        self._color_index = 0
        self._slug_counters.clear()

        # Convert ToC entries to categories
        categories: List[Category] = []
        stats = {
            "total_entries": toc_result.total_entries,
            "total_created": 0,
            "skipped_depth": 0,
            "max_depth": 0,
        }

        for entry in toc_result.entries:
            converted = self._convert_entry_to_category(
                entry=entry,
                project_id=project_id,
                parent_id=parent_id,
                base_depth=0 if parent_id is None else 1,
                stats=stats
            )
            categories.extend(converted)

        logger.info(
            f"Generated {stats['total_created']} categories from {stats['total_entries']} ToC entries "
            f"(skipped {stats['skipped_depth']} due to depth limit)"
        )

        return categories, stats

    def _convert_entry_to_category(
        self,
        entry: TocEntry,
        project_id: int,
        parent_id: Optional[int],
        base_depth: int,
        stats: Dict[str, int]
    ) -> List[Category]:
        """
        Recursively convert TocEntry to Category objects

        Args:
            entry: TocEntry to convert
            project_id: Project ID
            parent_id: Parent category ID (None for root)
            base_depth: Base depth offset (0 for root, 1 if appending)
            stats: Statistics dict to update

        Returns:
            List of Category objects (parent + all descendants)
        """
        current_depth = base_depth + entry.level

        # Skip if depth exceeds limit
        if current_depth >= self.MAX_DEPTH:
            logger.warning(f"Skipping entry '{entry.title}' - depth {current_depth} exceeds limit {self.MAX_DEPTH}")
            stats["skipped_depth"] += 1
            return []

        # Update max depth
        stats["max_depth"] = max(stats["max_depth"], current_depth)

        # Create category
        category = Category(
            name=self._clean_title(entry.title),
            description=self._generate_description(entry),
            color=self._get_next_color(),
            icon=self._get_icon_for_depth(current_depth),
            depth=current_depth,
            order=stats["total_created"],  # Sequential order
            parent_id=parent_id,
            project_id=project_id,
        )

        stats["total_created"] += 1

        result = [category]

        # Process children recursively
        # Note: We can't set parent_id to category.id yet (not in DB)
        # The API endpoint will need to handle this in two passes
        if entry.children:
            for child_entry in entry.children:
                child_categories = self._convert_entry_to_category(
                    entry=child_entry,
                    project_id=project_id,
                    parent_id=None,  # Will be set after parent is inserted
                    base_depth=base_depth,
                    stats=stats
                )
                result.extend(child_categories)

        return result

    def _clean_title(self, title: str) -> str:
        """
        Clean and normalize ToC title for category name

        Args:
            title: Raw title from ToC

        Returns:
            Cleaned title (max 200 chars)
        """
        # Remove common prefixes (chapter numbers, etc.)
        # "1.2.3 Section Title" -> "Section Title"
        cleaned = re.sub(r'^[\d\.\s\-]+', '', title)

        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        # Truncate if too long
        if len(cleaned) > 200:
            cleaned = cleaned[:197] + "..."

        return cleaned or title[:200]  # Fallback to original if cleaning removes everything

    def _generate_description(self, entry: TocEntry) -> Optional[str]:
        """
        Generate category description from ToC entry

        Args:
            entry: ToC entry

        Returns:
            Description with page reference
        """
        parts = []

        if entry.page:
            parts.append(f"Page {entry.page}")

        if entry.metadata:
            # Add any useful metadata
            if "page_range" in entry.metadata:
                parts.append(f"Pages {entry.metadata['page_range']}")

        if parts:
            return " | ".join(parts)

        return None

    def _get_next_color(self) -> str:
        """
        Get next color from pastel palette (round-robin)

        Returns:
            Hex color string
        """
        color = self.PASTEL_COLORS[self._color_index % len(self.PASTEL_COLORS)]
        self._color_index += 1
        return color

    def _get_icon_for_depth(self, depth: int) -> str:
        """
        Get appropriate icon for depth level

        Args:
            depth: Category depth (0-based)

        Returns:
            Lucide icon name
        """
        return self.DEPTH_ICONS.get(depth, self.DEFAULT_ICON)

    def generate_slug(self, name: str) -> str:
        """
        Generate URL-friendly slug from category name

        Handles duplicates by appending counter.

        Args:
            name: Category name

        Returns:
            URL-friendly slug

        Example:
            >>> generator.generate_slug("Chapter 1: Introduction")
            'chapter-1-introduction'
            >>> generator.generate_slug("Chapter 1: Introduction")  # duplicate
            'chapter-1-introduction-2'
        """
        # Convert to lowercase
        slug = name.lower()

        # Replace special characters with hyphens
        slug = re.sub(r'[^a-z0-9]+', '-', slug)

        # Remove leading/trailing hyphens
        slug = slug.strip('-')

        # Truncate to reasonable length
        slug = slug[:100]

        # Handle duplicates
        base_slug = slug
        counter = self._slug_counters[base_slug]

        if counter > 0:
            slug = f"{base_slug}-{counter + 1}"

        self._slug_counters[base_slug] += 1

        return slug


# Convenience function
def generate_category_tree(
    toc_result: TocExtractionResult,
    project_id: int,
    parent_id: Optional[int] = None
) -> Tuple[List[Category], Dict[str, any]]:
    """
    Convenience function to generate category tree from ToC

    Args:
        toc_result: ToC extraction result
        project_id: Project ID
        parent_id: Optional parent category ID

    Returns:
        Tuple of (categories list, metadata dict)

    Example:
        >>> from services import extract_toc, generate_category_tree
        >>> toc_result = extract_toc(pdf_path)
        >>> categories, stats = generate_category_tree(toc_result, project_id=1)
    """
    generator = CategoryTreeGenerator()
    return generator.generate_tree(toc_result, project_id, parent_id)
