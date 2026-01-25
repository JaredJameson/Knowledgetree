"""
Unit tests for TocExtractor service

Tests ToC extraction from PDF documents using different methods.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from services.toc_extractor import (
    TocExtractor,
    TocEntry,
    TocExtractionResult,
    ExtractionMethod,
    extract_toc
)


class TestTocEntry:
    """Test TocEntry data structure"""

    def test_create_simple_entry(self):
        """Test creating a simple ToC entry"""
        entry = TocEntry(
            title="Chapter 1",
            level=0,
            page=1
        )

        assert entry.title == "Chapter 1"
        assert entry.level == 0
        assert entry.page == 1
        assert entry.children == []
        assert entry.metadata is None

    def test_create_entry_with_children(self):
        """Test creating entry with nested children"""
        child1 = TocEntry(title="Section 1.1", level=1, page=2)
        child2 = TocEntry(title="Section 1.2", level=1, page=5)

        parent = TocEntry(
            title="Chapter 1",
            level=0,
            page=1,
            children=[child1, child2]
        )

        assert len(parent.children) == 2
        assert parent.children[0].title == "Section 1.1"
        assert parent.children[1].title == "Section 1.2"

    def test_to_dict(self):
        """Test conversion to dictionary"""
        entry = TocEntry(
            title="Chapter 1",
            level=0,
            page=1,
            children=[
                TocEntry(title="Section 1.1", level=1, page=2)
            ]
        )

        result = entry.to_dict()

        assert result['title'] == "Chapter 1"
        assert result['level'] == 0
        assert result['page'] == 1
        assert len(result['children']) == 1
        assert result['children'][0]['title'] == "Section 1.1"

    def test_from_dict(self):
        """Test creation from dictionary"""
        data = {
            'title': "Chapter 1",
            'level': 0,
            'page': 1,
            'children': [
                {'title': "Section 1.1", 'level': 1, 'page': 2, 'children': []}
            ]
        }

        entry = TocEntry.from_dict(data)

        assert entry.title == "Chapter 1"
        assert entry.level == 0
        assert entry.page == 1
        assert len(entry.children) == 1
        assert entry.children[0].title == "Section 1.1"

    def test_flatten(self):
        """Test flattening hierarchical structure"""
        entry = TocEntry(
            title="Chapter 1",
            level=0,
            page=1,
            children=[
                TocEntry(title="Section 1.1", level=1, page=2),
                TocEntry(
                    title="Section 1.2",
                    level=1,
                    page=5,
                    children=[
                        TocEntry(title="Subsection 1.2.1", level=2, page=6)
                    ]
                )
            ]
        )

        flat = entry.flatten()

        assert len(flat) == 4
        assert flat[0].title == "Chapter 1"
        assert flat[1].title == "Section 1.1"
        assert flat[2].title == "Section 1.2"
        assert flat[3].title == "Subsection 1.2.1"

    def test_count_entries(self):
        """Test counting total entries"""
        entry = TocEntry(
            title="Chapter 1",
            level=0,
            page=1,
            children=[
                TocEntry(title="Section 1.1", level=1, page=2),
                TocEntry(
                    title="Section 1.2",
                    level=1,
                    page=5,
                    children=[
                        TocEntry(title="Subsection 1.2.1", level=2, page=6)
                    ]
                )
            ]
        )

        count = entry.count_entries()
        assert count == 4

    def test_max_depth(self):
        """Test calculating maximum depth"""
        entry = TocEntry(
            title="Chapter 1",
            level=0,
            page=1,
            children=[
                TocEntry(title="Section 1.1", level=1, page=2),
                TocEntry(
                    title="Section 1.2",
                    level=1,
                    page=5,
                    children=[
                        TocEntry(title="Subsection 1.2.1", level=2, page=6)
                    ]
                )
            ]
        )

        max_depth = entry.max_depth()
        assert max_depth == 2


class TestTocExtractionResult:
    """Test TocExtractionResult data structure"""

    def test_create_successful_result(self):
        """Test creating successful extraction result"""
        entries = [
            TocEntry(title="Chapter 1", level=0, page=1),
            TocEntry(title="Chapter 2", level=0, page=10)
        ]

        result = TocExtractionResult(
            method=ExtractionMethod.PYPDF,
            success=True,
            entries=entries
        )

        assert result.method == ExtractionMethod.PYPDF
        assert result.success is True
        assert len(result.entries) == 2
        assert result.total_entries == 2
        assert result.max_depth == 0
        assert result.error is None

    def test_create_failed_result(self):
        """Test creating failed extraction result"""
        result = TocExtractionResult(
            method=ExtractionMethod.PYPDF,
            success=False,
            entries=[],
            error="No outline found"
        )

        assert result.success is False
        assert result.total_entries == 0
        assert result.error == "No outline found"

    def test_to_dict(self):
        """Test conversion to dictionary"""
        entries = [TocEntry(title="Chapter 1", level=0, page=1)]

        result = TocExtractionResult(
            method=ExtractionMethod.PYPDF,
            success=True,
            entries=entries,
            metadata={'page_count': 100}
        )

        data = result.to_dict()

        assert data['method'] == 'pypdf'
        assert data['success'] is True
        assert len(data['entries']) == 1
        assert data['total_entries'] == 1
        assert data['metadata']['page_count'] == 100

    def test_flatten_entries(self):
        """Test flattening all entries"""
        entries = [
            TocEntry(
                title="Chapter 1",
                level=0,
                page=1,
                children=[
                    TocEntry(title="Section 1.1", level=1, page=2)
                ]
            ),
            TocEntry(title="Chapter 2", level=0, page=10)
        ]

        result = TocExtractionResult(
            method=ExtractionMethod.PYPDF,
            success=True,
            entries=entries
        )

        flat = result.flatten_entries()

        assert len(flat) == 3
        assert flat[0].title == "Chapter 1"
        assert flat[1].title == "Section 1.1"
        assert flat[2].title == "Chapter 2"


class TestTocExtractor:
    """Test TocExtractor service"""

    def test_init(self):
        """Test initializing extractor"""
        extractor = TocExtractor(max_depth=5)

        assert extractor.max_depth == 5
        assert extractor._docling_converter is None

    def test_extract_file_not_found(self):
        """Test extraction with non-existent file"""
        extractor = TocExtractor()
        result = extractor.extract(Path("/nonexistent/file.pdf"))

        assert result.success is False
        assert result.method == ExtractionMethod.NONE
        assert "not found" in result.error

    def test_extract_invalid_file(self, tmp_path):
        """Test extraction with non-PDF file"""
        # Create a non-PDF file that exists
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("not a pdf")

        extractor = TocExtractor()
        result = extractor.extract(txt_file)

        assert result.success is False
        assert result.method == ExtractionMethod.NONE
        assert "not a PDF" in result.error

    def test_build_hierarchy_simple(self):
        """Test building hierarchy from flat list"""
        extractor = TocExtractor()

        flat_entries = [
            TocEntry(title="Chapter 1", level=0, page=1),
            TocEntry(title="Section 1.1", level=1, page=2),
            TocEntry(title="Section 1.2", level=1, page=5),
            TocEntry(title="Chapter 2", level=0, page=10)
        ]

        roots = extractor._build_hierarchy(flat_entries)

        assert len(roots) == 2
        assert roots[0].title == "Chapter 1"
        assert len(roots[0].children) == 2
        assert roots[0].children[0].title == "Section 1.1"
        assert roots[0].children[1].title == "Section 1.2"
        assert roots[1].title == "Chapter 2"
        assert len(roots[1].children) == 0

    def test_build_hierarchy_deep(self):
        """Test building deep hierarchy"""
        extractor = TocExtractor()

        flat_entries = [
            TocEntry(title="Chapter 1", level=0, page=1),
            TocEntry(title="Section 1.1", level=1, page=2),
            TocEntry(title="Subsection 1.1.1", level=2, page=3),
            TocEntry(title="Sub-subsection 1.1.1.1", level=3, page=4)
        ]

        roots = extractor._build_hierarchy(flat_entries)

        assert len(roots) == 1
        assert roots[0].title == "Chapter 1"
        assert len(roots[0].children) == 1
        assert roots[0].children[0].title == "Section 1.1"
        assert len(roots[0].children[0].children) == 1
        assert roots[0].children[0].children[0].title == "Subsection 1.1.1"

    def test_build_hierarchy_empty(self):
        """Test building hierarchy from empty list"""
        extractor = TocExtractor()
        roots = extractor._build_hierarchy([])

        assert roots == []

    @patch('services.toc_extractor.PYPDF_AVAILABLE', False)
    @patch('services.toc_extractor.PYMUPDF_AVAILABLE', False)
    @patch('services.toc_extractor.DOCLING_AVAILABLE', False)
    def test_extract_hybrid_no_methods(self, tmp_path):
        """Test hybrid extraction when no methods are available"""
        # Create dummy PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("%PDF-1.4\n")

        extractor = TocExtractor()
        result = extractor._extract_hybrid(pdf_file)

        assert result.success is False
        assert result.method == ExtractionMethod.NONE
        assert "No ToC found" in result.error


class TestConvenienceFunction:
    """Test convenience function"""

    @patch('services.toc_extractor.TocExtractor')
    def test_extract_toc(self, mock_extractor_class):
        """Test extract_toc convenience function"""
        mock_extractor = Mock()
        mock_result = TocExtractionResult(
            method=ExtractionMethod.PYPDF,
            success=True,
            entries=[TocEntry(title="Test", level=0, page=1)]
        )
        mock_extractor.extract.return_value = mock_result
        mock_extractor_class.return_value = mock_extractor

        pdf_path = Path("/test/file.pdf")
        result = extract_toc(pdf_path, max_depth=5)

        mock_extractor_class.assert_called_once_with(max_depth=5)
        mock_extractor.extract.assert_called_once_with(pdf_path)
        assert result == mock_result


# Integration tests (require actual PDF files)
@pytest.mark.integration
class TestTocExtractorIntegration:
    """
    Integration tests for TocExtractor

    These tests require actual PDF files with ToC.
    Mark as integration tests to skip in regular test runs.
    """

    def test_extract_with_real_pdf(self):
        """Test extraction with a real PDF file"""
        # This test would require a sample PDF file
        # Skip if no sample file is available
        pytest.skip("Requires sample PDF file")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
