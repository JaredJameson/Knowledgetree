"""
KnowledgeTree Backend - Intelligent PDF Processing Service
Intelligently selects optimal extraction tools based on document type
Extracts text, tables, formulas, and TOC with smart fallback strategies
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import fitz  # PyMuPDF
from docling.document_converter import DocumentConverter

from .toc_extractor import TocExtractor, TocExtractionResult
from .table_extractor import TableExtractor, TableExtractionResult
from .formula_extractor import FormulaExtractor, FormulaExtractionResult
from .document_classifier import (
    DocumentClassifier,
    ClassificationResult,
    DocumentType,
    ExtractionTool
)

logger = logging.getLogger(__name__)


class PDFProcessor:
    """
    Intelligent PDF processing service

    Features:
    - Automatic document type detection
    - Smart tool selection based on content
    - Text extraction (Docling, PyMuPDF)
    - Table of Contents extraction
    - Table extraction (Docling, pdfplumber)
    - Formula extraction (Docling, regex)
    - Extraction metadata tracking
    - Intelligent fallback strategies
    """

    def __init__(self, upload_dir: str = "./uploads", toc_max_depth: int = 10):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        # Initialize document classifier
        self.classifier = DocumentClassifier()

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
        prefer_docling: bool = True,
        auto_detect: bool = True
    ) -> Tuple[str, int, Dict[str, Any]]:
        """
        Intelligently process PDF file and extract text

        Args:
            pdf_path: Path to PDF file
            prefer_docling: Prefer Docling if auto_detect is False
            auto_detect: Use intelligent document classification (recommended)

        Returns:
            Tuple of (extracted_text, page_count, extraction_metadata)

        Extraction metadata includes:
            - document_type: Classified document type
            - extraction_tool: Tool used for extraction
            - classification_confidence: Confidence score
            - features: Detected document features
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        if not pdf_path.suffix.lower() == '.pdf':
            raise ValueError(f"File is not a PDF: {pdf_path}")

        metadata = {
            "document_type": None,
            "extraction_tool": None,
            "classification_confidence": None,
            "classification_reasoning": None,
            "features": {}
        }

        try:
            if auto_detect:
                # INTELLIGENT MODE: Classify document and select optimal tools
                logger.info(f"🔍 Analyzing document type: {pdf_path.name}")
                classification = self.classifier.classify(pdf_path)

                metadata["document_type"] = classification.document_type.value
                metadata["classification_confidence"] = classification.confidence
                metadata["classification_reasoning"] = classification.reasoning
                metadata["features"] = classification.features.to_dict()

                logger.info(f"📋 {classification.reasoning}")

                # Try recommended tools in order
                text, page_count = self._extract_with_strategy(
                    pdf_path,
                    classification.recommended_tools,
                    metadata
                )

            else:
                # LEGACY MODE: Simple preference-based selection
                if prefer_docling:
                    try:
                        text, page_count = self.extract_text_docling(pdf_path)
                        metadata["extraction_tool"] = "docling"
                    except Exception as e:
                        logger.warning(f"Docling failed, falling back to PyMuPDF: {str(e)}")
                        text, page_count = self.extract_text_pymupdf(pdf_path)
                        metadata["extraction_tool"] = "pymupdf"
                else:
                    text, page_count = self.extract_text_pymupdf(pdf_path)
                    metadata["extraction_tool"] = "pymupdf"

            return text, page_count, metadata

        except Exception as e:
            logger.error(f"PDF processing failed for {pdf_path}: {str(e)}")
            raise

    def _extract_with_strategy(
        self,
        pdf_path: Path,
        recommended_tools: list[ExtractionTool],
        metadata: Dict[str, Any]
    ) -> Tuple[str, int]:
        """
        Extract text using recommended tools with fallback strategy

        Args:
            pdf_path: Path to PDF file
            recommended_tools: Ordered list of tools to try
            metadata: Metadata dict to update with used tool

        Returns:
            Tuple of (extracted_text, page_count)
        """
        last_error = None

        for tool in recommended_tools:
            try:
                logger.info(f"🔧 Attempting extraction with: {tool.value}")

                if tool == ExtractionTool.DOCLING:
                    text, page_count = self.extract_text_docling(pdf_path)
                    metadata["extraction_tool"] = "docling"
                    logger.info(f"✅ Successfully extracted with Docling")
                    return text, page_count

                elif tool == ExtractionTool.PYMUPDF:
                    text, page_count = self.extract_text_pymupdf(pdf_path)
                    metadata["extraction_tool"] = "pymupdf"
                    logger.info(f"✅ Successfully extracted with PyMuPDF")
                    return text, page_count

                elif tool == ExtractionTool.PDFPLUMBER:
                    # TODO: Implement pdfplumber extraction
                    logger.warning("pdfplumber not yet implemented, skipping")
                    continue

                elif tool == ExtractionTool.PYTESSERACT:
                    # TODO: Implement OCR extraction
                    logger.warning("pytesseract not yet implemented, skipping")
                    continue

            except Exception as e:
                last_error = e
                logger.warning(f"⚠️ {tool.value} failed: {str(e)}")
                continue

        # All tools failed - raise last error
        if last_error:
            raise last_error
        else:
            raise RuntimeError("No extraction tools succeeded")

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
        prefer_docling: bool = True,
        auto_detect: bool = True
    ) -> Dict[str, Any]:
        """
        Full PDF processing with intelligent tool selection

        Args:
            pdf_path: Path to PDF file
            extract_text: Extract text content
            extract_toc: Extract Table of Contents (Phase 1)
            extract_tables: Extract tables (Phase 2)
            extract_formulas: Extract formulas (Phase 2)
            prefer_docling: Prefer Docling if auto_detect is False
            auto_detect: Use intelligent document classification (recommended)

        Returns:
            Dictionary with processing results:
            {
                'text': str,
                'page_count': int,
                'extraction_metadata': {
                    'document_type': str,
                    'extraction_tool': str,
                    'classification_confidence': float,
                    'classification_reasoning': str,
                    'features': dict
                },
                'toc': TocExtractionResult,
                'tables': TableExtractionResult,
                'formulas': FormulaExtractionResult,
                'file_info': dict
            }
        """
        logger.info(f"🚀 Full PDF processing: {pdf_path.name}")

        results = {
            'text': None,
            'page_count': None,
            'extraction_metadata': {},
            'toc': None,
            'tables': None,
            'formulas': None,
            'file_info': self.get_file_info(pdf_path)
        }

        # Extract text with intelligent tool selection
        if extract_text:
            text, page_count, metadata = self.process_pdf(
                pdf_path,
                prefer_docling=prefer_docling,
                auto_detect=auto_detect
            )
            results['text'] = text
            results['page_count'] = page_count
            results['extraction_metadata'] = metadata

        # Extract ToC (Phase 1)
        if extract_toc:
            toc_result = self.extract_toc(pdf_path)
            results['toc'] = toc_result

        # Extract tables (Phase 2) - if document has tables
        if extract_tables:
            # Skip if classification says no tables
            if results.get('extraction_metadata', {}).get('features', {}).get('table_count', 0) > 0:
                tables_result = self.extract_tables(pdf_path)
                results['tables'] = tables_result
            else:
                logger.info("ℹ️ Skipping table extraction (no tables detected)")

        # Extract formulas (Phase 2) - if document has formulas
        if extract_formulas:
            # Skip if classification says no formulas
            if results.get('extraction_metadata', {}).get('features', {}).get('formula_count', 0) > 0:
                formulas_result = self.extract_formulas(pdf_path)
                results['formulas'] = formulas_result
            else:
                logger.info("ℹ️ Skipping formula extraction (no formulas detected)")

        logger.info(f"✅ PDF processing complete: {pdf_path.name}")
        return results
