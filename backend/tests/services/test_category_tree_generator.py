"""
Unit tests for CategoryTreeGenerator service

Tests category tree generation from ToC extraction results.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock

from services.category_tree_generator import CategoryTreeGenerator, generate_category_tree
from services.toc_extractor import TocEntry, TocExtractionResult, ExtractionMethod


class TestCategoryTreeGenerator:
    """Test CategoryTreeGenerator service"""

    def test_init(self):
        """Test initializing generator"""
        generator = CategoryTreeGenerator()

        assert generator._color_index == 0
        assert len(generator._slug_counters) == 0
        assert len(generator.PASTEL_COLORS) == 8
        assert generator.MAX_DEPTH == 10

    def test_generate_tree_success(self):
        """Test successful tree generation"""
        generator = CategoryTreeGenerator()

        # Create mock ToC result
        toc_entries = [
            TocEntry(
                title="Chapter 1: Introduction",
                level=0,
                page=1,
                children=[
                    TocEntry(title="Section 1.1: Background", level=1, page=2),
                    TocEntry(title="Section 1.2: Objectives", level=1, page=5),
                ]
            ),
            TocEntry(title="Chapter 2: Methods", level=0, page=10),
        ]

        toc_result = TocExtractionResult(
            method=ExtractionMethod.PYPDF,
            success=True,
            entries=toc_entries
        )

        # Generate tree
        categories, stats = generator.generate_tree(toc_result, project_id=1)

        # Verify categories created
        assert len(categories) > 0
        assert stats['total_entries'] == 4  # 2 chapters + 2 sections
        assert stats['total_created'] > 0
        assert stats['skipped_depth'] == 0
        assert stats['max_depth'] >= 0

        # Verify first category
        first_cat = categories[0]
        assert "Introduction" in first_cat.name
        assert first_cat.depth == 0
        assert first_cat.project_id == 1
        assert first_cat.color in generator.PASTEL_COLORS
        assert first_cat.icon == "Book"  # depth 0

    def test_generate_tree_failed_extraction(self):
        """Test tree generation with failed ToC extraction"""
        generator = CategoryTreeGenerator()

        toc_result = TocExtractionResult(
            method=ExtractionMethod.NONE,
            success=False,
            entries=[],
            error="No ToC found"
        )

        with pytest.raises(ValueError, match="ToC extraction failed"):
            generator.generate_tree(toc_result, project_id=1)

    def test_generate_tree_no_entries(self):
        """Test tree generation with no ToC entries"""
        generator = CategoryTreeGenerator()

        toc_result = TocExtractionResult(
            method=ExtractionMethod.PYPDF,
            success=True,
            entries=[]
        )

        with pytest.raises(ValueError, match="No ToC entries found"):
            generator.generate_tree(toc_result, project_id=1)

    def test_generate_tree_depth_limit(self):
        """Test tree generation respects depth limit"""
        generator = CategoryTreeGenerator()

        # Create deeply nested ToC (11 levels - should exceed limit)
        entry = TocEntry(title="Level 0", level=0, page=1)
        current = entry
        for i in range(1, 12):
            child = TocEntry(title=f"Level {i}", level=i, page=i+1)
            current.children = [child]
            current = child

        toc_result = TocExtractionResult(
            method=ExtractionMethod.PYPDF,
            success=True,
            entries=[entry]
        )

        # Generate tree
        categories, stats = generator.generate_tree(toc_result, project_id=1)

        # Should skip entries beyond depth 10
        assert stats['skipped_depth'] > 0
        assert stats['max_depth'] < generator.MAX_DEPTH

    def test_clean_title(self):
        """Test title cleaning"""
        generator = CategoryTreeGenerator()

        # Test various title formats
        assert generator._clean_title("1.2.3 Section Title") == "Section Title"
        assert generator._clean_title("  Chapter   1  ") == "Chapter 1"  # Normalizes whitespace
        assert generator._clean_title("1. Introduction") == "Introduction"

        # Test long title truncation
        long_title = "A" * 250
        cleaned = generator._clean_title(long_title)
        assert len(cleaned) <= 200
        assert cleaned.endswith("...")

    def test_generate_description(self):
        """Test description generation"""
        generator = CategoryTreeGenerator()

        # Test with page number
        entry = TocEntry(title="Chapter 1", level=0, page=5)
        desc = generator._generate_description(entry)
        assert "Page 5" in desc

        # Test with metadata
        entry = TocEntry(
            title="Chapter 1",
            level=0,
            page=5,
            metadata={"page_range": "5-15"}
        )
        desc = generator._generate_description(entry)
        assert "Pages 5-15" in desc

        # Test without page
        entry = TocEntry(title="Chapter 1", level=0, page=None)
        desc = generator._generate_description(entry)
        assert desc is None

    def test_color_assignment(self):
        """Test color assignment (round-robin)"""
        generator = CategoryTreeGenerator()

        # Get colors in sequence
        colors = [generator._get_next_color() for _ in range(10)]

        # Verify round-robin
        assert colors[0] == generator.PASTEL_COLORS[0]
        assert colors[7] == generator.PASTEL_COLORS[7]
        assert colors[8] == generator.PASTEL_COLORS[0]  # Wraps around

    def test_icon_assignment(self):
        """Test icon assignment by depth"""
        generator = CategoryTreeGenerator()

        # Test depth-specific icons
        assert generator._get_icon_for_depth(0) == "Book"
        assert generator._get_icon_for_depth(1) == "BookOpen"
        assert generator._get_icon_for_depth(2) == "FileText"
        assert generator._get_icon_for_depth(10) == "Folder"  # Default

    def test_slug_generation(self):
        """Test slug generation with duplicates"""
        generator = CategoryTreeGenerator()

        # Test basic slug
        slug1 = generator.generate_slug("Chapter 1: Introduction")
        assert slug1 == "chapter-1-introduction"

        # Test duplicate handling
        slug2 = generator.generate_slug("Chapter 1: Introduction")
        assert slug2 == "chapter-1-introduction-2"

        slug3 = generator.generate_slug("Chapter 1: Introduction")
        assert slug3 == "chapter-1-introduction-3"

    def test_slug_special_characters(self):
        """Test slug generation with special characters"""
        generator = CategoryTreeGenerator()

        slug = generator.generate_slug("Section 1.2.3: A/B Testing & Results!")
        assert slug == "section-1-2-3-a-b-testing-results"
        assert "/" not in slug
        assert "&" not in slug

    def test_generate_tree_with_parent(self):
        """Test tree generation with parent category"""
        generator = CategoryTreeGenerator()

        toc_entries = [
            TocEntry(title="Chapter 1", level=0, page=1)
        ]

        toc_result = TocExtractionResult(
            method=ExtractionMethod.PYPDF,
            success=True,
            entries=toc_entries
        )

        # Generate with parent_id
        categories, stats = generator.generate_tree(
            toc_result,
            project_id=1,
            parent_id=99
        )

        # Root category should have parent_id set
        assert categories[0].parent_id == 99
        assert categories[0].depth == 1  # Depth offset


class TestConvenienceFunction:
    """Test convenience function"""

    def test_generate_category_tree(self):
        """Test generate_category_tree convenience function"""
        toc_entries = [
            TocEntry(title="Chapter 1", level=0, page=1),
        ]

        toc_result = TocExtractionResult(
            method=ExtractionMethod.PYPDF,
            success=True,
            entries=toc_entries
        )

        categories, stats = generate_category_tree(toc_result, project_id=1)

        assert len(categories) > 0
        assert stats['total_created'] > 0
        assert categories[0].project_id == 1


class TestHierarchicalConversion:
    """Test hierarchical ToC → Category conversion"""

    def test_simple_hierarchy(self):
        """Test simple parent-child hierarchy"""
        generator = CategoryTreeGenerator()

        toc_entries = [
            TocEntry(
                title="Parent",
                level=0,
                page=1,
                children=[
                    TocEntry(title="Child 1", level=1, page=2),
                    TocEntry(title="Child 2", level=1, page=3),
                ]
            )
        ]

        toc_result = TocExtractionResult(
            method=ExtractionMethod.PYPDF,
            success=True,
            entries=toc_entries
        )

        categories, stats = generator.generate_tree(toc_result, project_id=1)

        # Should have 3 categories (1 parent + 2 children)
        assert len(categories) == 3
        assert stats['total_created'] == 3

        # Verify depth levels
        depths = [cat.depth for cat in categories]
        assert 0 in depths  # Parent
        assert 1 in depths  # Children

    def test_deep_hierarchy(self):
        """Test deeply nested hierarchy"""
        generator = CategoryTreeGenerator()

        toc_entries = [
            TocEntry(
                title="Level 0",
                level=0,
                page=1,
                children=[
                    TocEntry(
                        title="Level 1",
                        level=1,
                        page=2,
                        children=[
                            TocEntry(title="Level 2", level=2, page=3)
                        ]
                    )
                ]
            )
        ]

        toc_result = TocExtractionResult(
            method=ExtractionMethod.PYPDF,
            success=True,
            entries=toc_entries
        )

        categories, stats = generator.generate_tree(toc_result, project_id=1)

        # Should have 3 categories
        assert len(categories) == 3
        assert stats['max_depth'] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
