"""
KnowledgeTree Backend - PDF Processing Service
Extract text from PDF files using PyMuPDF and Docling
Extract Table of Contents for automatic category tree generation
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import fitz  # PyMuPDF
from docling.document_converter import DocumentConverter

from .toc_extractor import TocExtractor, TocExtractionResult
from .table_extractor import TableExtractor, TableExtractionResult
from .formula_extractor import FormulaExtractor, FormulaExtractionResult

logger = logging.getLogger(__name__)


class PDFProcessor:
    """
    PDF processing service

    Features:
    - Text extraction (PyMuPDF, Docling)
    - Table of Contents extraction
    - Table extraction (Phase 2)
    - Formula extraction (Phase 2)
    - File management
    """

    def __init__(self, upload_dir: str = "./uploads", toc_max_depth: int = 10):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Docling converter
        self.docling_converter = DocumentConverter()

        # Initialize ToC extractor (Phase 1)
        self.toc_extractor = TocExtractor(max_depth=toc_max_depth)

        # Initialize Table extractor (Phase 2)
        self.table_extractor = TableExtractor()

        # Initialize Formula extractor (Phase 2)
        self.formula_extractor = FormulaExtractor()

    def extract_text_pymupdf(self, pdf_path: Path) -> tuple[str, int]:
        """
        Extract text from PDF using PyMuPDF

        Args:
            pdf_path: Path to PDF file

        Returns:
            Tuple of (extracted_text, page_count)
        """
        try:
            doc = fitz.open(pdf_path)
            text_content = []
            page_count = len(doc)

            for page_num in range(page_count):
                page = doc[page_num]
                text = page.get_text()
                text_content.append(f"--- Page {page_num + 1} ---\n{text}")

            doc.close()
            full_text = "\n\n".join(text_content)

            logger.info(f"Extracted {len(full_text)} characters from {page_count} pages using PyMuPDF")
            return full_text, page_count

        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {str(e)}")
            raise

    def extract_text_docling(self, pdf_path: Path) -> tuple[str, int]:
        """
        Extract text from PDF using Docling (advanced layout understanding)

        Args:
            pdf_path: Path to PDF file

        Returns:
            Tuple of (extracted_text, page_count)
        """
        try:
            # Convert PDF to markdown using Docling
            result = self.docling_converter.convert(str(pdf_path))

            # Extract text content
            text_content = result.document.export_to_markdown()

            # Get page count (fallback to PyMuPDF if Docling doesn't provide it)
            page_count = len(result.document.pages) if hasattr(result.document, 'pages') else 0
            if page_count == 0:
                doc = fitz.open(pdf_path)
                page_count = len(doc)
                doc.close()

            logger.info(f"Extracted {len(text_content)} characters from {page_count} pages using Docling")
            return text_content, page_count

        except Exception as e:
            logger.error(f"Docling extraction failed: {str(e)}")
            raise

    def process_pdf(
        self,
        pdf_path: Path,
        prefer_docling: bool = True
    ) -> tuple[str, int]:
        """
        Process PDF file and extract text

        Args:
            pdf_path: Path to PDF file
            prefer_docling: Try Docling first, fallback to PyMuPDF

        Returns:
            Tuple of (extracted_text, page_count)
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        if not pdf_path.suffix.lower() == '.pdf':
            raise ValueError(f"File is not a PDF: {pdf_path}")

        try:
            if prefer_docling:
                # Try Docling first (better layout understanding)
                try:
                    return self.extract_text_docling(pdf_path)
                except Exception as e:
                    logger.warning(f"Docling failed, falling back to PyMuPDF: {str(e)}")
                    return self.extract_text_pymupdf(pdf_path)
            else:
                # Use PyMuPDF directly
                return self.extract_text_pymupdf(pdf_path)

        except Exception as e:
            logger.error(f"PDF processing failed for {pdf_path}: {str(e)}")
            raise

    def save_uploaded_file(
        self,
        file_content: bytes,
        filename: str,
        document_id: int
    ) -> Path:
        """
        Save uploaded file to disk

        Args:
            file_content: Raw file bytes
            filename: Original filename
            document_id: Database document ID

        Returns:
            Path to saved file
        """
        # Create documents subdirectory
        documents_dir = self.upload_dir / "documents"
        documents_dir.mkdir(parents=True, exist_ok=True)

        # Generate safe filename with document ID prefix
        safe_filename = f"{document_id}_{filename}"
        file_path = documents_dir / safe_filename

        # Write file
        file_path.write_bytes(file_content)
        logger.info(f"Saved uploaded file: {file_path}")

        return file_path

    def get_file_info(self, file_path: Path) -> dict:
        """
        Get file metadata

        Args:
            file_path: Path to file

        Returns:
            Dictionary with file info
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        stat = file_path.stat()
        return {
            "file_size": stat.st_size,
            "file_path": str(file_path),
            "filename": file_path.name,
        }

    def extract_toc(self, pdf_path: Path) -> TocExtractionResult:
        """
        Extract Table of Contents from PDF

        Uses hybrid waterfall approach:
        1. Try pypdf (fast, accurate for PDFs with outline)
        2. Fallback to PyMuPDF (reliable)
        3. Fallback to Docling (structure analysis)

        Args:
            pdf_path: Path to PDF file

        Returns:
            TocExtractionResult with extracted ToC entries

        Example:
            >>> processor = PDFProcessor()
            >>> result = processor.extract_toc(Path("book.pdf"))
            >>> if result.success:
            ...     print(f"Found {result.total_entries} ToC entries")
            ...     for entry in result.entries:
            ...         print(f"  {entry.title} (page {entry.page})")
        """
        logger.info(f"Extracting ToC from: {pdf_path.name}")

        try:
            result = self.toc_extractor.extract(pdf_path)

            if result.success:
                logger.info(
                    f"✅ ToC extracted: {result.total_entries} entries, "
                    f"max depth {result.max_depth}, method: {result.method.value}"
                )
            else:
                logger.warning(f"⚠️ ToC extraction failed: {result.error}")

            return result

        except Exception as e:
            logger.error(f"ToC extraction error: {str(e)}")
            raise

    def extract_tables(
        self,
        pdf_path: Path,
        max_tables: int = 100,
        min_confidence: float = 0.5
    ) -> TableExtractionResult:
        """
        Extract tables from PDF (Phase 2)

        Uses waterfall approach:
        1. Docling TableFormer (primary)
        2. pdfplumber (fallback)

        Args:
            pdf_path: Path to PDF file
            max_tables: Maximum number of tables to extract
            min_confidence: Minimum confidence score (0.0-1.0)

        Returns:
            TableExtractionResult with extracted tables
        """
        logger.info(f"Extracting tables from: {pdf_path.name}")

        try:
            result = self.table_extractor.extract_tables(
                str(pdf_path),
                max_tables=max_tables,
                min_confidence=min_confidence
            )

            if result.success:
                logger.info(
                    f"✅ Tables extracted: {result.total_tables} tables, "
                    f"method: {result.method.value}"
                )
            else:
                logger.warning(f"⚠️ Table extraction failed: {result.error}")

            return result

        except Exception as e:
            logger.error(f"Table extraction error: {str(e)}")
            raise

    def extract_formulas(
        self,
        pdf_path: Path,
        max_formulas: int = 200,
        min_confidence: float = 0.5
    ) -> FormulaExtractionResult:
        """
        Extract mathematical formulas from PDF (Phase 2)

        Uses waterfall approach:
        1. Docling (primary)
        2. Regex patterns (fallback)

        Args:
            pdf_path: Path to PDF file
            max_formulas: Maximum number of formulas to extract
            min_confidence: Minimum confidence score (0.0-1.0)

        Returns:
            FormulaExtractionResult with extracted formulas
        """
        logger.info(f"Extracting formulas from: {pdf_path.name}")

        try:
            result = self.formula_extractor.extract_formulas(
                str(pdf_path),
                max_formulas=max_formulas,
                min_confidence=min_confidence
            )

            if result.success:
                logger.info(
                    f"✅ Formulas extracted: {result.total_formulas} formulas, "
                    f"method: {result.method.value}"
                )
            else:
                logger.warning(f"⚠️ Formula extraction failed: {result.error}")

            return result

        except Exception as e:
            logger.error(f"Formula extraction error: {str(e)}")
            raise

    def process_pdf_full(
        self,
        pdf_path: Path,
        extract_text: bool = True,
        extract_toc: bool = True,
        extract_tables: bool = False,
        extract_formulas: bool = False,
        prefer_docling: bool = True
    ) -> Dict[str, Any]:
        """
        Full PDF processing with text, ToC, tables, and formulas extraction

        Args:
            pdf_path: Path to PDF file
            extract_text: Extract text content
            extract_toc: Extract Table of Contents (Phase 1)
            extract_tables: Extract tables (Phase 2)
            extract_formulas: Extract formulas (Phase 2)
            prefer_docling: Use Docling for text extraction

        Returns:
            Dictionary with processing results:
            {
                'text': str,
                'page_count': int,
                'toc': TocExtractionResult,
                'tables': TableExtractionResult,
                'formulas': FormulaExtractionResult,
                'file_info': dict
            }
        """
        logger.info(f"Full PDF processing: {pdf_path.name}")

        results = {
            'text': None,
            'page_count': None,
            'toc': None,
            'tables': None,
            'formulas': None,
            'file_info': self.get_file_info(pdf_path)
        }

        # Extract text
        if extract_text:
            text, page_count = self.process_pdf(pdf_path, prefer_docling=prefer_docling)
            results['text'] = text
            results['page_count'] = page_count

        # Extract ToC (Phase 1)
        if extract_toc:
            toc_result = self.extract_toc(pdf_path)
            results['toc'] = toc_result

        # Extract tables (Phase 2)
        if extract_tables:
            tables_result = self.extract_tables(pdf_path)
            results['tables'] = tables_result

        # Extract formulas (Phase 2)
        if extract_formulas:
            formulas_result = self.extract_formulas(pdf_path)
            results['formulas'] = formulas_result

        logger.info(f"✅ PDF processing complete: {pdf_path.name}")
        return results
