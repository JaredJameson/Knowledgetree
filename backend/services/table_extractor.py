"""
KnowledgeTree Backend - Table Extraction Service
Extracts tables from PDF documents using waterfall approach
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class TableExtractionMethod(str, Enum):
    """Method used for table extraction"""
    DOCLING = "docling"
    PDFPLUMBER = "pdfplumber"
    NONE = "none"


@dataclass
class ExtractedTable:
    """Extracted table with metadata"""
    table_index: int
    page_number: Optional[int] = None
    headers: List[str] = field(default_factory=list)
    rows: List[List[str]] = field(default_factory=list)
    caption: Optional[str] = None
    bbox: Optional[Dict[str, float]] = None  # {x, y, width, height}
    confidence: float = 1.0
    method: TableExtractionMethod = TableExtractionMethod.NONE

    @property
    def row_count(self) -> int:
        return len(self.rows)

    @property
    def col_count(self) -> int:
        if self.headers:
            return len(self.headers)
        if self.rows:
            return max(len(row) for row in self.rows)
        return 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON storage"""
        return {
            "headers": self.headers,
            "rows": self.rows,
            "caption": self.caption
        }


@dataclass
class TableExtractionResult:
    """Result of table extraction from a document"""
    success: bool
    tables: List[ExtractedTable] = field(default_factory=list)
    method: TableExtractionMethod = TableExtractionMethod.NONE
    total_tables: int = 0
    error: Optional[str] = None


class TableExtractor:
    """
    Extract tables from PDF documents using multiple methods

    Waterfall approach:
    1. Docling TableFormer (primary - most accurate)
    2. pdfplumber (fallback - simpler but reliable)
    3. None (if all methods fail)
    """

    def __init__(self):
        self.docling_available = self._check_docling()
        self.pdfplumber_available = self._check_pdfplumber()

        logger.info(
            f"TableExtractor initialized: "
            f"docling={'available' if self.docling_available else 'unavailable'}, "
            f"pdfplumber={'available' if self.pdfplumber_available else 'unavailable'}"
        )

    def _check_docling(self) -> bool:
        """Check if Docling is available"""
        try:
            import docling
            from docling.document_converter import DocumentConverter
            return True
        except ImportError:
            logger.warning("Docling not available for table extraction")
            return False

    def _check_pdfplumber(self) -> bool:
        """Check if pdfplumber is available"""
        try:
            import pdfplumber
            return True
        except ImportError:
            logger.warning("pdfplumber not available for table extraction")
            return False

    def extract_tables(
        self,
        pdf_path: str,
        max_tables: int = 100,
        min_confidence: float = 0.5
    ) -> TableExtractionResult:
        """
        Extract tables from PDF using available methods

        Args:
            pdf_path: Path to PDF file
            max_tables: Maximum number of tables to extract
            min_confidence: Minimum confidence score (0.0-1.0)

        Returns:
            TableExtractionResult with extracted tables
        """
        if not Path(pdf_path).exists():
            return TableExtractionResult(
                success=False,
                error=f"PDF file not found: {pdf_path}"
            )

        # Try Docling first (most accurate)
        if self.docling_available:
            result = self._extract_with_docling(pdf_path, max_tables, min_confidence)
            if result.success and result.total_tables > 0:
                logger.info(
                    f"Extracted {result.total_tables} tables using Docling from {pdf_path}"
                )
                return result
            else:
                logger.info("Docling table extraction returned no tables, trying fallback")

        # Fallback to pdfplumber
        if self.pdfplumber_available:
            result = self._extract_with_pdfplumber(pdf_path, max_tables, min_confidence)
            if result.success and result.total_tables > 0:
                logger.info(
                    f"Extracted {result.total_tables} tables using pdfplumber from {pdf_path}"
                )
                return result
            else:
                logger.info("pdfplumber table extraction returned no tables")

        # No tables found
        return TableExtractionResult(
            success=True,
            tables=[],
            method=TableExtractionMethod.NONE,
            total_tables=0,
            error="No tables found in PDF"
        )

    def _extract_with_docling(
        self,
        pdf_path: str,
        max_tables: int,
        min_confidence: float
    ) -> TableExtractionResult:
        """
        Extract tables using Docling TableFormer

        Docling provides advanced table detection and structure recognition
        """
        try:
            from docling.datamodel.pipeline_options import PdfPipelineOptions
            from docling.document_converter import DocumentConverter

            # Configure Docling for table extraction
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_table_structure = True  # Enable TableFormer
            pipeline_options.table_structure_options.do_cell_matching = True

            converter = DocumentConverter(pipeline_options=pipeline_options)

            # Convert PDF
            result = converter.convert(pdf_path)

            # Extract tables from Docling document
            tables: List[ExtractedTable] = []
            table_index = 0

            for element in result.document.elements:
                if table_index >= max_tables:
                    break

                # Check if element is a table
                if hasattr(element, 'data') and isinstance(element.data, dict):
                    table_data = element.data.get('table')
                    if table_data:
                        # Extract table structure
                        extracted_table = self._parse_docling_table(
                            table_data=table_data,
                            table_index=table_index,
                            element=element
                        )

                        if extracted_table and extracted_table.confidence >= min_confidence:
                            tables.append(extracted_table)
                            table_index += 1

            return TableExtractionResult(
                success=True,
                tables=tables,
                method=TableExtractionMethod.DOCLING,
                total_tables=len(tables)
            )

        except Exception as e:
            logger.error(f"Docling table extraction failed: {str(e)}")
            return TableExtractionResult(
                success=False,
                error=f"Docling extraction error: {str(e)}"
            )

    def _parse_docling_table(
        self,
        table_data: Dict[str, Any],
        table_index: int,
        element: Any
    ) -> Optional[ExtractedTable]:
        """Parse table data from Docling format"""
        try:
            # Extract headers and rows from Docling table structure
            headers = []
            rows = []

            # Docling stores tables in various formats, adapt as needed
            if 'cells' in table_data:
                # Group cells by rows
                cells_by_row = {}
                for cell in table_data['cells']:
                    row_idx = cell.get('row', 0)
                    col_idx = cell.get('col', 0)
                    text = cell.get('text', '')

                    if row_idx not in cells_by_row:
                        cells_by_row[row_idx] = {}
                    cells_by_row[row_idx][col_idx] = text

                # Extract headers (first row)
                if 0 in cells_by_row:
                    header_row = cells_by_row[0]
                    headers = [header_row.get(i, '') for i in sorted(header_row.keys())]

                # Extract data rows
                for row_idx in sorted(cells_by_row.keys()):
                    if row_idx == 0:  # Skip header row
                        continue
                    row_data = cells_by_row[row_idx]
                    row = [row_data.get(i, '') for i in sorted(row_data.keys())]
                    rows.append(row)

            # Get page number if available
            page_number = getattr(element, 'page_number', None)

            # Get bounding box if available
            bbox = None
            if hasattr(element, 'bbox'):
                bbox = {
                    'x': element.bbox.x,
                    'y': element.bbox.y,
                    'width': element.bbox.width,
                    'height': element.bbox.height
                }

            # Get caption if available
            caption = getattr(element, 'caption', None)

            return ExtractedTable(
                table_index=table_index,
                page_number=page_number,
                headers=headers,
                rows=rows,
                caption=caption,
                bbox=bbox,
                confidence=0.9,  # Docling is highly accurate
                method=TableExtractionMethod.DOCLING
            )

        except Exception as e:
            logger.warning(f"Failed to parse Docling table: {str(e)}")
            return None

    def _extract_with_pdfplumber(
        self,
        pdf_path: str,
        max_tables: int,
        min_confidence: float
    ) -> TableExtractionResult:
        """
        Extract tables using pdfplumber

        pdfplumber provides simpler but reliable table extraction
        """
        try:
            import pdfplumber

            tables: List[ExtractedTable] = []
            table_index = 0

            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    if table_index >= max_tables:
                        break

                    # Extract tables from page
                    page_tables = page.extract_tables()

                    for page_table in page_tables:
                        if table_index >= max_tables:
                            break

                        if not page_table or len(page_table) < 2:
                            continue

                        # First row is headers
                        headers = [str(cell) if cell else '' for cell in page_table[0]]

                        # Remaining rows are data
                        rows = []
                        for row in page_table[1:]:
                            rows.append([str(cell) if cell else '' for cell in row])

                        # Get bounding box (simplified)
                        bbox = {
                            'x': 0,
                            'y': 0,
                            'width': float(page.width),
                            'height': float(page.height)
                        }

                        extracted_table = ExtractedTable(
                            table_index=table_index,
                            page_number=page_num + 1,  # 1-based page numbers
                            headers=headers,
                            rows=rows,
                            bbox=bbox,
                            confidence=0.7,  # pdfplumber is less accurate than Docling
                            method=TableExtractionMethod.PDFPLUMBER
                        )

                        if extracted_table.confidence >= min_confidence:
                            tables.append(extracted_table)
                            table_index += 1

            return TableExtractionResult(
                success=True,
                tables=tables,
                method=TableExtractionMethod.PDFPLUMBER,
                total_tables=len(tables)
            )

        except Exception as e:
            logger.error(f"pdfplumber table extraction failed: {str(e)}")
            return TableExtractionResult(
                success=False,
                error=f"pdfplumber extraction error: {str(e)}"
            )
