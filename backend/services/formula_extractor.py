"""
KnowledgeTree Backend - Formula Extraction Service
Extracts mathematical formulas from PDF documents
"""

import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class FormulaExtractionMethod(str, Enum):
    """Method used for formula extraction"""
    DOCLING = "docling"
    REGEX = "regex"
    NONE = "none"


@dataclass
class ExtractedFormula:
    """Extracted mathematical formula with metadata"""
    formula_index: int
    page_number: Optional[int] = None
    latex_content: str = ""
    context_before: str = ""  # Text before formula
    context_after: str = ""   # Text after formula
    bbox: Optional[Dict[str, float]] = None  # {x, y, width, height}
    confidence: float = 1.0
    method: FormulaExtractionMethod = FormulaExtractionMethod.NONE


@dataclass
class FormulaExtractionResult:
    """Result of formula extraction from a document"""
    success: bool
    formulas: List[ExtractedFormula] = field(default_factory=list)
    method: FormulaExtractionMethod = FormulaExtractionMethod.NONE
    total_formulas: int = 0
    error: Optional[str] = None


class FormulaExtractor:
    """
    Extract mathematical formulas from PDF documents

    Methods:
    1. Docling - Advanced formula detection (primary)
    2. Regex - Pattern-based LaTeX extraction (fallback)
    """

    # LaTeX patterns for regex extraction
    LATEX_PATTERNS = [
        r'\$\$(.+?)\$\$',  # Display math: $$ ... $$
        r'\$(.+?)\$',      # Inline math: $ ... $
        r'\\begin\{equation\}(.+?)\\end\{equation\}',  # equation environment
        r'\\begin\{align\}(.+?)\\end\{align\}',        # align environment
        r'\\begin\{eqnarray\}(.+?)\\end\{eqnarray\}',  # eqnarray environment
        r'\\[(.+?)\\]',    # Display math: \[ ... \]
        r'\\((.+?)\\)',    # Inline math: \( ... \)
    ]

    def __init__(self):
        self.docling_available = self._check_docling()
        self.latex2mathml_available = self._check_latex2mathml()

        logger.info(
            f"FormulaExtractor initialized: "
            f"docling={'available' if self.docling_available else 'unavailable'}, "
            f"latex2mathml={'available' if self.latex2mathml_available else 'unavailable'}"
        )

    def _check_docling(self) -> bool:
        """Check if Docling is available"""
        try:
            import docling
            from docling.document_converter import DocumentConverter
            return True
        except ImportError:
            logger.warning("Docling not available for formula extraction")
            return False

    def _check_latex2mathml(self) -> bool:
        """Check if latex2mathml is available"""
        try:
            import latex2mathml
            return True
        except ImportError:
            logger.warning("latex2mathml not available for formula validation")
            return False

    def extract_formulas(
        self,
        pdf_path: str,
        max_formulas: int = 200,
        min_confidence: float = 0.5
    ) -> FormulaExtractionResult:
        """
        Extract formulas from PDF using available methods

        Args:
            pdf_path: Path to PDF file
            max_formulas: Maximum number of formulas to extract
            min_confidence: Minimum confidence score (0.0-1.0)

        Returns:
            FormulaExtractionResult with extracted formulas
        """
        if not Path(pdf_path).exists():
            return FormulaExtractionResult(
                success=False,
                error=f"PDF file not found: {pdf_path}"
            )

        # Try Docling first (most accurate)
        if self.docling_available:
            result = self._extract_with_docling(pdf_path, max_formulas, min_confidence)
            if result.success and result.total_formulas > 0:
                logger.info(
                    f"Extracted {result.total_formulas} formulas using Docling from {pdf_path}"
                )
                return result
            else:
                logger.info("Docling formula extraction returned no formulas, trying fallback")

        # Fallback to regex extraction
        result = self._extract_with_regex(pdf_path, max_formulas, min_confidence)
        if result.success and result.total_formulas > 0:
            logger.info(
                f"Extracted {result.total_formulas} formulas using regex from {pdf_path}"
            )
            return result
        else:
            logger.info("Regex formula extraction returned no formulas")

        # No formulas found
        return FormulaExtractionResult(
            success=True,
            formulas=[],
            method=FormulaExtractionMethod.NONE,
            total_formulas=0,
            error="No formulas found in PDF"
        )

    def _extract_with_docling(
        self,
        pdf_path: str,
        max_formulas: int,
        min_confidence: float
    ) -> FormulaExtractionResult:
        """
        Extract formulas using Docling

        Docling can detect formula regions in PDFs and extract their content
        """
        try:
            from docling.document_converter import DocumentConverter

            converter = DocumentConverter()
            result = converter.convert(pdf_path)

            formulas: List[ExtractedFormula] = []
            formula_index = 0

            for element in result.document.elements:
                if formula_index >= max_formulas:
                    break

                # Check if element is a formula/equation
                element_type = getattr(element, 'type', '').lower()
                if 'formula' in element_type or 'equation' in element_type or 'math' in element_type:
                    # Extract formula content
                    latex_content = getattr(element, 'text', '')
                    if not latex_content:
                        continue

                    # Get page number
                    page_number = getattr(element, 'page_number', None)

                    # Get bounding box
                    bbox = None
                    if hasattr(element, 'bbox'):
                        bbox = {
                            'x': element.bbox.x,
                            'y': element.bbox.y,
                            'width': element.bbox.width,
                            'height': element.bbox.height
                        }

                    # Get context (surrounding text)
                    context_before = ""
                    context_after = ""
                    # TODO: Extract context from surrounding elements

                    extracted_formula = ExtractedFormula(
                        formula_index=formula_index,
                        page_number=page_number,
                        latex_content=self._clean_latex(latex_content),
                        context_before=context_before,
                        context_after=context_after,
                        bbox=bbox,
                        confidence=0.85,  # Docling is accurate for formulas
                        method=FormulaExtractionMethod.DOCLING
                    )

                    if extracted_formula.confidence >= min_confidence:
                        formulas.append(extracted_formula)
                        formula_index += 1

            return FormulaExtractionResult(
                success=True,
                formulas=formulas,
                method=FormulaExtractionMethod.DOCLING,
                total_formulas=len(formulas)
            )

        except Exception as e:
            logger.error(f"Docling formula extraction failed: {str(e)}")
            return FormulaExtractionResult(
                success=False,
                error=f"Docling extraction error: {str(e)}"
            )

    def _extract_with_regex(
        self,
        pdf_path: str,
        max_formulas: int,
        min_confidence: float
    ) -> FormulaExtractionResult:
        """
        Extract formulas using regex pattern matching

        This method extracts LaTeX formulas from PDF text using regex patterns
        """
        try:
            import fitz  # PyMuPDF

            formulas: List[ExtractedFormula] = []
            formula_index = 0

            pdf = fitz.open(pdf_path)

            for page_num, page in enumerate(pdf):
                if formula_index >= max_formulas:
                    break

                # Extract text from page
                text = page.get_text()

                # Search for LaTeX patterns
                for pattern in self.LATEX_PATTERNS:
                    matches = re.finditer(pattern, text, re.DOTALL)

                    for match in matches:
                        if formula_index >= max_formulas:
                            break

                        latex_content = match.group(1)  # Extract formula content
                        if not latex_content.strip():
                            continue

                        # Get context (50 chars before and after)
                        context_start = max(0, match.start() - 50)
                        context_end = min(len(text), match.end() + 50)
                        context_before = text[context_start:match.start()].strip()
                        context_after = text[match.end():context_end].strip()

                        extracted_formula = ExtractedFormula(
                            formula_index=formula_index,
                            page_number=page_num + 1,  # 1-based page numbers
                            latex_content=self._clean_latex(latex_content),
                            context_before=context_before[-100:],  # Last 100 chars
                            context_after=context_after[:100],     # First 100 chars
                            confidence=0.6,  # Regex is less accurate
                            method=FormulaExtractionMethod.REGEX
                        )

                        # Validate LaTeX if possible
                        if self.latex2mathml_available:
                            if self._validate_latex(extracted_formula.latex_content):
                                extracted_formula.confidence = 0.7

                        if extracted_formula.confidence >= min_confidence:
                            formulas.append(extracted_formula)
                            formula_index += 1

            pdf.close()

            return FormulaExtractionResult(
                success=True,
                formulas=formulas,
                method=FormulaExtractionMethod.REGEX,
                total_formulas=len(formulas)
            )

        except Exception as e:
            logger.error(f"Regex formula extraction failed: {str(e)}")
            return FormulaExtractionResult(
                success=False,
                error=f"Regex extraction error: {str(e)}"
            )

    def _clean_latex(self, latex: str) -> str:
        """Clean and normalize LaTeX content"""
        # Remove excessive whitespace
        latex = re.sub(r'\s+', ' ', latex)
        # Trim whitespace
        latex = latex.strip()
        return latex

    def _validate_latex(self, latex: str) -> bool:
        """
        Validate LaTeX formula syntax

        Returns True if LaTeX is valid, False otherwise
        """
        try:
            from latex2mathml.converter import convert

            # Try to convert to MathML
            convert(latex)
            return True
        except Exception:
            return False
