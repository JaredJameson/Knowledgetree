"""
KnowledgeTree Backend - Table of Contents (ToC) Extraction Service

Extracts hierarchical Table of Contents from PDF documents using multiple methods:
1. pypdf - Fast, accurate for PDFs with embedded outline/bookmarks
2. PyMuPDF (fitz) - Reliable fallback, already in use
3. Docling - Structure analysis for PDFs without explicit ToC

Author: KnowledgeTree Team
Date: 2026-01-20
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

# Import PDF libraries with graceful fallback
try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    logger.warning("pypdf not installed - pypdf ToC extraction disabled")
    PYPDF_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    logger.warning("PyMuPDF not installed - fitz ToC extraction disabled")
    PYMUPDF_AVAILABLE = False

try:
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
    DOCLING_AVAILABLE = True
except ImportError:
    logger.warning("Docling not installed - Docling ToC extraction disabled")
    DOCLING_AVAILABLE = False


class ExtractionMethod(str, Enum):
    """ToC extraction methods"""
    PYPDF = "pypdf"
    PYMUPDF = "pymupdf"
    DOCLING = "docling"
    NONE = "none"


@dataclass
class TocEntry:
    """
    Single Table of Contents entry with hierarchical structure

    Attributes:
        title: Chapter/section title
        level: Hierarchy depth (0-based: 0=chapter, 1=section, 2=subsection)
        page: Source page number (1-based), None if unavailable
        children: Nested child entries
        metadata: Additional information (optional)
    """
    title: str
    level: int
    page: Optional[int] = None
    children: List['TocEntry'] = field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = {
            'title': self.title,
            'level': self.level,
            'page': self.page,
        }
        if self.children:
            result['children'] = [child.to_dict() for child in self.children]
        if self.metadata:
            result['metadata'] = self.metadata
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TocEntry':
        """Create from dictionary"""
        children_data = data.get('children', [])
        children = [cls.from_dict(child) for child in children_data]

        return cls(
            title=data['title'],
            level=data['level'],
            page=data.get('page'),
            children=children,
            metadata=data.get('metadata')
        )

    def flatten(self) -> List['TocEntry']:
        """
        Flatten hierarchical structure to list

        Returns:
            List of all entries in depth-first order
        """
        result = [self]
        for child in self.children:
            result.extend(child.flatten())
        return result

    def count_entries(self) -> int:
        """Count total entries including children"""
        return 1 + sum(child.count_entries() for child in self.children)

    def max_depth(self) -> int:
        """Calculate maximum depth of hierarchy"""
        if not self.children:
            return self.level
        return max(child.max_depth() for child in self.children)


@dataclass
class TocExtractionResult:
    """
    Results from ToC extraction attempt

    Attributes:
        method: Extraction method used
        success: Whether extraction succeeded
        entries: Hierarchical ToC entries (can be empty list if failed)
        total_entries: Total count of entries (including nested)
        max_depth: Maximum hierarchy depth
        error: Error message if failed
        metadata: Additional information
    """
    method: ExtractionMethod
    success: bool
    entries: List[TocEntry]
    total_entries: int = 0
    max_depth: int = 0
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Calculate stats from entries"""
        if self.entries:
            self.total_entries = sum(e.count_entries() for e in self.entries)
            self.max_depth = max(e.max_depth() for e in self.entries) if self.entries else 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'method': self.method.value,
            'success': self.success,
            'entries': [entry.to_dict() for entry in self.entries],
            'total_entries': self.total_entries,
            'max_depth': self.max_depth,
            'error': self.error,
            'metadata': self.metadata or {}
        }

    def flatten_entries(self) -> List[TocEntry]:
        """Get flat list of all entries"""
        result = []
        for entry in self.entries:
            result.extend(entry.flatten())
        return result


class TocExtractor:
    """
    Table of Contents extraction service

    Uses hybrid waterfall approach:
    1. Try pypdf (fastest, most reliable when outline exists)
    2. Fallback to PyMuPDF (reliable, already in use)
    3. Fallback to Docling (structure analysis, slower)
    """

    def __init__(self, max_depth: int = 10):
        """
        Initialize ToC extractor

        Args:
            max_depth: Maximum allowed hierarchy depth (default: 10)
        """
        self.max_depth = max_depth

        # Initialize Docling converter (lazy initialization)
        self._docling_converter = None

    @property
    def docling_converter(self) -> Optional[DocumentConverter]:
        """Lazy initialization of Docling converter"""
        if not DOCLING_AVAILABLE:
            return None

        if self._docling_converter is None:
            # Configure Docling with optimal settings
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_table_structure = False  # Not needed for ToC
            pipeline_options.do_ocr = False  # Not needed for ToC extraction

            self._docling_converter = DocumentConverter(
                format_options={
                    "pdf": PdfFormatOption(pipeline_options=pipeline_options)
                }
            )

        return self._docling_converter

    def extract(self, pdf_path: Path, method: Optional[ExtractionMethod] = None) -> TocExtractionResult:
        """
        Extract ToC from PDF using specified or automatic method

        Args:
            pdf_path: Path to PDF file
            method: Specific method to use, or None for hybrid waterfall

        Returns:
            TocExtractionResult with extracted entries
        """
        # Validate PDF path
        if not pdf_path.exists():
            return TocExtractionResult(
                method=ExtractionMethod.NONE,
                success=False,
                entries=[],
                error=f"PDF file not found: {pdf_path}"
            )

        if not pdf_path.suffix.lower() == '.pdf':
            return TocExtractionResult(
                method=ExtractionMethod.NONE,
                success=False,
                entries=[],
                error=f"File is not a PDF: {pdf_path}"
            )

        # Use specific method if requested
        if method == ExtractionMethod.PYPDF:
            return self._extract_with_pypdf(pdf_path)
        elif method == ExtractionMethod.PYMUPDF:
            return self._extract_with_pymupdf(pdf_path)
        elif method == ExtractionMethod.DOCLING:
            return self._extract_with_docling(pdf_path)

        # Hybrid waterfall approach
        return self._extract_hybrid(pdf_path)

    def _extract_hybrid(self, pdf_path: Path) -> TocExtractionResult:
        """
        Extract ToC using hybrid waterfall approach

        Priority:
        1. pypdf (fastest, most reliable)
        2. PyMuPDF (fallback)
        3. Docling (last resort)

        Args:
            pdf_path: Path to PDF file

        Returns:
            TocExtractionResult from first successful method
        """
        logger.info(f"Extracting ToC from: {pdf_path.name} (hybrid approach)")

        # Method 1: pypdf
        if PYPDF_AVAILABLE:
            result = self._extract_with_pypdf(pdf_path)
            if result.success and result.total_entries > 0:
                logger.info(f"✅ pypdf extracted {result.total_entries} entries")
                return result
            logger.debug(f"pypdf failed or found no entries: {result.error}")

        # Method 2: PyMuPDF
        if PYMUPDF_AVAILABLE:
            result = self._extract_with_pymupdf(pdf_path)
            if result.success and result.total_entries > 0:
                logger.info(f"✅ PyMuPDF extracted {result.total_entries} entries")
                return result
            logger.debug(f"PyMuPDF failed or found no entries: {result.error}")

        # Method 3: Docling
        if DOCLING_AVAILABLE:
            result = self._extract_with_docling(pdf_path)
            if result.success and result.total_entries > 0:
                logger.info(f"✅ Docling extracted {result.total_entries} entries")
                return result
            logger.debug(f"Docling failed or found no entries: {result.error}")

        # All methods failed
        logger.warning(f"⚠️ No ToC found in {pdf_path.name}")
        return TocExtractionResult(
            method=ExtractionMethod.NONE,
            success=False,
            entries=[],
            error="No ToC found - PDF may not have embedded outline. "
                  "Consider manual structure definition."
        )

    def _extract_with_pypdf(self, pdf_path: Path) -> TocExtractionResult:
        """
        Extract ToC using pypdf library

        pypdf can extract PDF outline/bookmarks which typically represent
        the document's table of contents.

        Args:
            pdf_path: Path to PDF file

        Returns:
            TocExtractionResult with extracted entries
        """
        if not PYPDF_AVAILABLE:
            return TocExtractionResult(
                method=ExtractionMethod.PYPDF,
                success=False,
                entries=[],
                error="pypdf not installed"
            )

        try:
            logger.debug(f"Trying pypdf extraction: {pdf_path.name}")

            with open(pdf_path, 'rb') as file:
                reader = pypdf.PdfReader(file)

                # Get outline/bookmarks
                outline = reader.outline

                if not outline:
                    return TocExtractionResult(
                        method=ExtractionMethod.PYPDF,
                        success=False,
                        entries=[],
                        error="No outline found in PDF",
                        metadata={
                            'page_count': len(reader.pages),
                            'encrypted': reader.is_encrypted
                        }
                    )

                # Parse outline recursively
                entries = self._parse_pypdf_outline(outline, reader)

                # Validate depth
                if entries and max(e.max_depth() for e in entries) > self.max_depth:
                    logger.warning(f"ToC depth exceeds max_depth ({self.max_depth})")

                return TocExtractionResult(
                    method=ExtractionMethod.PYPDF,
                    success=True,
                    entries=entries,
                    metadata={
                        'page_count': len(reader.pages),
                        'encrypted': reader.is_encrypted
                    }
                )

        except Exception as e:
            logger.error(f"pypdf extraction failed: {str(e)}")
            return TocExtractionResult(
                method=ExtractionMethod.PYPDF,
                success=False,
                entries=[],
                error=str(e)
            )

    def _parse_pypdf_outline(
        self,
        outline: List,
        reader: pypdf.PdfReader,
        level: int = 0
    ) -> List[TocEntry]:
        """
        Recursively parse pypdf outline structure

        pypdf outline is a list that can contain:
        - Destination objects (bookmarks)
        - Nested lists (sub-bookmarks)

        Args:
            outline: pypdf outline structure
            reader: PdfReader instance for page lookup
            level: Current hierarchy level (0-based)

        Returns:
            List of TocEntry objects
        """
        entries = []

        for item in outline:
            if isinstance(item, list):
                # Nested outline - recurse with increased level
                entries.extend(self._parse_pypdf_outline(item, reader, level + 1))
            else:
                # Bookmark destination
                try:
                    # Extract title
                    title = item.title if hasattr(item, 'title') else str(item)
                    if not title or not title.strip():
                        continue  # Skip empty titles

                    # Get page number
                    page_num = None
                    if hasattr(item, 'page'):
                        try:
                            page_obj = item.page
                            if page_obj:
                                # Get page index (0-based) and convert to 1-based
                                page_num = reader.pages.index(page_obj) + 1
                        except Exception as e:
                            logger.debug(f"Failed to get page number: {e}")

                    entry = TocEntry(
                        title=title.strip(),
                        level=level,
                        page=page_num
                    )
                    entries.append(entry)

                except Exception as e:
                    logger.debug(f"Failed to parse outline item: {e}")

        return entries

    def _extract_with_pymupdf(self, pdf_path: Path) -> TocExtractionResult:
        """
        Extract ToC using PyMuPDF (fitz) library

        PyMuPDF provides get_toc() method which extracts the document
        outline/table of contents.

        Args:
            pdf_path: Path to PDF file

        Returns:
            TocExtractionResult with extracted entries
        """
        if not PYMUPDF_AVAILABLE:
            return TocExtractionResult(
                method=ExtractionMethod.PYMUPDF,
                success=False,
                entries=[],
                error="PyMuPDF not installed"
            )

        try:
            logger.debug(f"Trying PyMuPDF extraction: {pdf_path.name}")

            doc = fitz.open(pdf_path)

            # Get ToC
            toc = doc.get_toc()

            if not toc:
                doc.close()
                return TocExtractionResult(
                    method=ExtractionMethod.PYMUPDF,
                    success=False,
                    entries=[],
                    error="No ToC found in PDF",
                    metadata={
                        'page_count': len(doc),
                        'encrypted': doc.is_encrypted
                    }
                )

            # Parse ToC
            # PyMuPDF ToC format: [[level, title, page], ...]
            entries = self._parse_pymupdf_toc(toc)

            # Validate depth
            if entries and max(e.max_depth() for e in entries) > self.max_depth:
                logger.warning(f"ToC depth exceeds max_depth ({self.max_depth})")

            metadata = {
                'page_count': len(doc),
                'encrypted': doc.is_encrypted
            }

            doc.close()

            return TocExtractionResult(
                method=ExtractionMethod.PYMUPDF,
                success=True,
                entries=entries,
                metadata=metadata
            )

        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {str(e)}")
            return TocExtractionResult(
                method=ExtractionMethod.PYMUPDF,
                success=False,
                entries=[],
                error=str(e)
            )

    def _parse_pymupdf_toc(self, toc: List) -> List[TocEntry]:
        """
        Parse PyMuPDF ToC structure into hierarchical entries

        PyMuPDF returns flat list: [[level, title, page], ...]
        Need to build hierarchy based on levels.

        Args:
            toc: PyMuPDF ToC list

        Returns:
            List of top-level TocEntry objects with nested children
        """
        if not toc:
            return []

        # Convert to flat TocEntry list
        flat_entries = []
        for item in toc:
            level, title, page = item

            # Skip empty titles
            if not title or not title.strip():
                continue

            entry = TocEntry(
                title=title.strip(),
                level=level - 1,  # PyMuPDF uses 1-based levels, we use 0-based
                page=page if page > 0 else None
            )
            flat_entries.append(entry)

        # Build hierarchy
        return self._build_hierarchy(flat_entries)

    def _build_hierarchy(self, flat_entries: List[TocEntry]) -> List[TocEntry]:
        """
        Build hierarchical structure from flat list of entries

        Algorithm:
        - Maintain stack of parent entries at each level
        - For each entry, find its parent (closest entry with lower level)
        - Add as child to parent

        Args:
            flat_entries: Flat list of TocEntry objects with levels

        Returns:
            List of top-level entries with nested children
        """
        if not flat_entries:
            return []

        # Root entries (level 0)
        roots = []

        # Stack: parent entry at each level
        stack: List[Optional[TocEntry]] = [None] * (self.max_depth + 1)

        for entry in flat_entries:
            level = entry.level

            # Validate level
            if level < 0 or level > self.max_depth:
                logger.warning(f"Entry level {level} out of bounds, skipping: {entry.title}")
                continue

            # Find parent (closest entry at lower level)
            parent = None
            for i in range(level - 1, -1, -1):
                if stack[i] is not None:
                    parent = stack[i]
                    break

            if parent is None:
                # Top-level entry
                roots.append(entry)
            else:
                # Add as child to parent
                parent.children.append(entry)

            # Update stack
            stack[level] = entry
            # Clear deeper levels
            for i in range(level + 1, len(stack)):
                stack[i] = None

        return roots

    def _extract_with_docling(self, pdf_path: Path) -> TocExtractionResult:
        """
        Extract ToC using Docling library

        Docling provides advanced document understanding including:
        - Document structure analysis
        - Heading detection
        - Section hierarchy

        This is a fallback method for PDFs without explicit ToC.

        Args:
            pdf_path: Path to PDF file

        Returns:
            TocExtractionResult with extracted entries
        """
        if not DOCLING_AVAILABLE or self.docling_converter is None:
            return TocExtractionResult(
                method=ExtractionMethod.DOCLING,
                success=False,
                entries=[],
                error="Docling not installed"
            )

        try:
            logger.debug(f"Trying Docling extraction: {pdf_path.name}")

            # Convert document
            result = self.docling_converter.convert(str(pdf_path))
            doc = result.document

            # Try to extract structure
            entries = []

            # Check for outline attribute
            if hasattr(doc, 'outline') and doc.outline:
                logger.debug("Docling: Found outline attribute")
                entries = self._parse_docling_structure(doc.outline)

            # Check for sections attribute
            elif hasattr(doc, 'sections') and doc.sections:
                logger.debug("Docling: Found sections attribute")
                entries = self._parse_docling_structure(doc.sections)

            # Check for headings
            elif hasattr(doc, 'headings') and doc.headings:
                logger.debug("Docling: Found headings attribute")
                entries = self._parse_docling_structure(doc.headings)

            if not entries:
                return TocExtractionResult(
                    method=ExtractionMethod.DOCLING,
                    success=False,
                    entries=[],
                    error="No ToC structure found in Docling output",
                    metadata={
                        'page_count': len(doc.pages) if hasattr(doc, 'pages') else None
                    }
                )

            return TocExtractionResult(
                method=ExtractionMethod.DOCLING,
                success=True,
                entries=entries,
                metadata={
                    'page_count': len(doc.pages) if hasattr(doc, 'pages') else None
                }
            )

        except Exception as e:
            logger.error(f"Docling extraction failed: {str(e)}")
            return TocExtractionResult(
                method=ExtractionMethod.DOCLING,
                success=False,
                entries=[],
                error=str(e)
            )

    def _parse_docling_structure(self, structure: Any) -> List[TocEntry]:
        """
        Parse Docling document structure

        Note: This is a placeholder implementation.
        Actual implementation depends on Docling's structure format.
        Will be refined after testing with real Docling output.

        Args:
            structure: Docling structure object

        Returns:
            List of TocEntry objects
        """
        # TODO: Implement based on actual Docling structure
        # This will be refined after testing
        logger.warning("Docling structure parsing not fully implemented yet")
        return []


# Convenience function for quick extraction
def extract_toc(pdf_path: Path, max_depth: int = 10) -> TocExtractionResult:
    """
    Quick ToC extraction using default settings

    Args:
        pdf_path: Path to PDF file
        max_depth: Maximum hierarchy depth

    Returns:
        TocExtractionResult
    """
    extractor = TocExtractor(max_depth=max_depth)
    return extractor.extract(pdf_path)
