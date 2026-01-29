"""
KnowledgeTree Backend - Document Type Classification
Intelligently analyzes PDF documents to determine optimal extraction strategy
"""

import logging
import fitz  # PyMuPDF
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class DocumentType(str, Enum):
    """PDF document classification types"""
    ACADEMIC_PAPER = "academic_paper"       # Research papers, theses
    TECHNICAL_MANUAL = "technical_manual"   # User guides, specifications
    TEXTBOOK = "textbook"                   # Educational books
    BUSINESS_REPORT = "business_report"     # Corporate reports, presentations
    FORM = "form"                            # Fillable forms, applications
    SCANNED_DOCUMENT = "scanned_document"   # OCR-required documents
    PRESENTATION = "presentation"            # Slides, decks
    BOOK = "book"                            # General books, novels
    MIXED_CONTENT = "mixed_content"         # Complex multi-type documents
    UNKNOWN = "unknown"                      # Could not classify


class ExtractionTool(str, Enum):
    """Available extraction tools"""
    DOCLING = "docling"         # Best for: layout understanding, tables, formulas
    PYMUPDF = "pymupdf"         # Best for: fast text extraction, simple docs
    PDFPLUMBER = "pdfplumber"   # Best for: precise tables, forms
    PYTESSERACT = "pytesseract" # Best for: OCR scanned documents


@dataclass
class DocumentFeatures:
    """Characteristics detected in PDF document"""

    # Basic metrics
    page_count: int = 0
    total_chars: int = 0
    avg_chars_per_page: float = 0.0

    # Structure detection
    has_toc: bool = False
    has_chapters: bool = False
    has_sections: bool = False

    # Content type indicators
    table_count: int = 0
    formula_count: int = 0
    image_count: int = 0
    citation_count: int = 0

    # Layout characteristics
    is_two_column: bool = False
    has_headers_footers: bool = False
    has_watermark: bool = False

    # Text quality
    text_density: float = 0.0  # Chars per page
    is_scanned: bool = False   # Low text, high images
    has_ocr_text: bool = False

    # Academic indicators
    has_abstract: bool = False
    has_references: bool = False
    has_equations: bool = False

    # Technical indicators
    has_code_blocks: bool = False
    has_diagrams: bool = False
    has_specifications: bool = False

    # Business indicators
    has_charts: bool = False
    has_executive_summary: bool = False
    has_financial_tables: bool = False

    # Metadata
    title: Optional[str] = None
    author: Optional[str] = None
    keywords: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/debugging"""
        return {
            "page_count": self.page_count,
            "total_chars": self.total_chars,
            "has_toc": self.has_toc,
            "table_count": self.table_count,
            "formula_count": self.formula_count,
            "image_count": self.image_count,
            "is_scanned": self.is_scanned,
            "has_abstract": self.has_abstract,
            "has_references": self.has_references,
            "text_density": self.text_density
        }


@dataclass
class ClassificationResult:
    """Result of document classification"""
    document_type: DocumentType
    confidence: float  # 0.0-1.0
    features: DocumentFeatures
    recommended_tools: List[ExtractionTool]
    reasoning: str  # Human-readable explanation

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "document_type": self.document_type.value,
            "confidence": self.confidence,
            "features": self.features.to_dict(),
            "recommended_tools": [tool.value for tool in self.recommended_tools],
            "reasoning": self.reasoning
        }


class DocumentClassifier:
    """
    Intelligent PDF document classifier

    Analyzes PDF characteristics to determine:
    1. Document type (academic, technical, book, etc.)
    2. Optimal extraction tools
    3. Extraction strategy

    Example:
        >>> classifier = DocumentClassifier()
        >>> result = classifier.classify(Path("paper.pdf"))
        >>> print(f"Type: {result.document_type}")
        >>> print(f"Tools: {result.recommended_tools}")
    """

    # Classification thresholds
    SCANNED_THRESHOLD = 50  # chars/page below = scanned
    TABLE_HEAVY_THRESHOLD = 3  # tables/page
    FORMULA_HEAVY_THRESHOLD = 2  # formulas/page

    def __init__(self):
        """Initialize classifier"""
        pass

    def analyze_features(self, pdf_path: Path) -> DocumentFeatures:
        """
        Analyze PDF to extract features for classification

        Args:
            pdf_path: Path to PDF file

        Returns:
            DocumentFeatures with detected characteristics
        """
        features = DocumentFeatures()

        try:
            doc = fitz.open(pdf_path)
            features.page_count = len(doc)

            # Analyze metadata
            metadata = doc.metadata
            features.title = metadata.get('title')
            features.author = metadata.get('author')
            if metadata.get('keywords'):
                features.keywords = metadata['keywords'].split(',')

            # Analyze TOC
            toc = doc.get_toc()
            features.has_toc = len(toc) > 0

            # Analyze pages
            total_text_length = 0
            image_count = 0
            table_indicators = 0
            formula_indicators = 0

            for page_num in range(min(features.page_count, 10)):  # Sample first 10 pages
                page = doc[page_num]
                text = page.get_text()
                total_text_length += len(text)

                # Count images
                image_count += len(page.get_images())

                # Detect tables (simple heuristic: presence of aligned pipes or tabs)
                if self._has_table_pattern(text):
                    table_indicators += 1

                # Detect formulas (mathematical symbols)
                if self._has_formula_pattern(text):
                    formula_indicators += 1

                # Detect abstract (first page)
                if page_num == 0 and self._has_abstract(text):
                    features.has_abstract = True

                # Detect references section (last pages)
                if page_num == features.page_count - 1:
                    if self._has_references(text):
                        features.has_references = True

                # Detect code blocks
                if self._has_code_pattern(text):
                    features.has_code_blocks = True

                # Detect citations
                features.citation_count += self._count_citations(text)

            doc.close()

            # Calculate metrics
            features.total_chars = total_text_length
            features.avg_chars_per_page = total_text_length / features.page_count if features.page_count > 0 else 0
            features.text_density = features.avg_chars_per_page

            # Determine if scanned (low text density + high image count)
            features.is_scanned = (
                features.avg_chars_per_page < self.SCANNED_THRESHOLD and
                image_count / max(features.page_count, 1) > 1
            )

            features.image_count = image_count
            features.table_count = table_indicators
            features.formula_count = formula_indicators

            # Structural indicators
            features.has_chapters = features.has_toc and len(toc) > 5
            features.has_equations = formula_indicators > 0

            logger.info(f"Features extracted: {features.to_dict()}")
            return features

        except Exception as e:
            logger.error(f"Feature extraction failed: {str(e)}")
            return features

    def classify(self, pdf_path: Path) -> ClassificationResult:
        """
        Classify document type and recommend extraction tools

        Args:
            pdf_path: Path to PDF file

        Returns:
            ClassificationResult with type and recommendations
        """
        features = self.analyze_features(pdf_path)

        # Classification logic using feature scoring
        scores = {
            DocumentType.ACADEMIC_PAPER: self._score_academic(features),
            DocumentType.TECHNICAL_MANUAL: self._score_technical(features),
            DocumentType.TEXTBOOK: self._score_textbook(features),
            DocumentType.BUSINESS_REPORT: self._score_business(features),
            DocumentType.BOOK: self._score_book(features),
            DocumentType.SCANNED_DOCUMENT: self._score_scanned(features),
            DocumentType.PRESENTATION: self._score_presentation(features)
        }

        # Get highest scoring type
        doc_type = max(scores, key=scores.get)
        confidence = scores[doc_type]

        # If confidence too low, classify as mixed or unknown
        if confidence < 0.3:
            if features.table_count > 0 or features.formula_count > 0:
                doc_type = DocumentType.MIXED_CONTENT
                confidence = 0.5
            else:
                doc_type = DocumentType.UNKNOWN
                confidence = 0.2

        # Recommend extraction tools based on type and features
        tools = self._recommend_tools(doc_type, features)
        reasoning = self._generate_reasoning(doc_type, features, confidence)

        result = ClassificationResult(
            document_type=doc_type,
            confidence=confidence,
            features=features,
            recommended_tools=tools,
            reasoning=reasoning
        )

        logger.info(f"Classification: {doc_type.value} (confidence: {confidence:.2f})")
        logger.info(f"Recommended tools: {[t.value for t in tools]}")

        return result

    def _score_academic(self, features: DocumentFeatures) -> float:
        """Score for academic paper classification"""
        score = 0.0

        if features.has_abstract:
            score += 0.3
        if features.has_references:
            score += 0.25
        if features.citation_count > 5:
            score += 0.15
        if features.formula_count > 0:
            score += 0.15
        if features.table_count > 0:
            score += 0.1
        if features.page_count > 5 and features.page_count < 50:
            score += 0.05

        return min(score, 1.0)

    def _score_technical(self, features: DocumentFeatures) -> float:
        """Score for technical manual classification"""
        score = 0.0

        if features.table_count >= 3:
            score += 0.3
        if features.has_toc:
            score += 0.2
        if features.has_diagrams or features.image_count > 10:
            score += 0.15
        if features.has_code_blocks:
            score += 0.15
        if features.has_specifications:
            score += 0.1
        if features.page_count > 20:
            score += 0.1

        return min(score, 1.0)

    def _score_textbook(self, features: DocumentFeatures) -> float:
        """Score for textbook classification"""
        score = 0.0

        if features.has_chapters:
            score += 0.3
        if features.page_count > 100:
            score += 0.2
        if features.formula_count > 5:
            score += 0.15
        if features.table_count > 5:
            score += 0.15
        if features.has_toc:
            score += 0.1
        if features.image_count > 20:
            score += 0.1

        return min(score, 1.0)

    def _score_business(self, features: DocumentFeatures) -> float:
        """Score for business report classification"""
        score = 0.0

        if features.has_executive_summary:
            score += 0.25
        if features.has_charts:
            score += 0.2
        if features.table_count > 2:
            score += 0.2
        if features.has_financial_tables:
            score += 0.15
        if features.page_count < 50:
            score += 0.1
        if "report" in features.title.lower() if features.title else False:
            score += 0.1

        return min(score, 1.0)

    def _score_book(self, features: DocumentFeatures) -> float:
        """Score for general book classification"""
        score = 0.0

        if features.has_chapters:
            score += 0.3
        if features.page_count > 50:
            score += 0.2
        if features.text_density > 1500:  # Dense text
            score += 0.2
        if features.table_count == 0 and features.formula_count == 0:
            score += 0.15  # Mostly narrative text
        if features.has_toc:
            score += 0.15

        return min(score, 1.0)

    def _score_scanned(self, features: DocumentFeatures) -> float:
        """Score for scanned document classification"""
        score = 0.0

        if features.is_scanned:
            score += 0.6
        if features.text_density < self.SCANNED_THRESHOLD:
            score += 0.2
        if features.image_count / max(features.page_count, 1) > 1:
            score += 0.2

        return min(score, 1.0)

    def _score_presentation(self, features: DocumentFeatures) -> float:
        """Score for presentation classification"""
        score = 0.0

        if features.text_density < 800:  # Lower text density
            score += 0.3
        if features.image_count / max(features.page_count, 1) > 0.8:
            score += 0.25
        if features.page_count > 10 and features.page_count < 100:
            score += 0.2
        if not features.has_toc and not features.has_chapters:
            score += 0.15
        if "slide" in features.title.lower() if features.title else False:
            score += 0.1

        return min(score, 1.0)

    def _recommend_tools(self, doc_type: DocumentType, features: DocumentFeatures) -> List[ExtractionTool]:
        """
        Recommend extraction tools based on document type and features

        Priority order in recommended list = execution order
        """
        tools = []

        if doc_type == DocumentType.SCANNED_DOCUMENT:
            # OCR required
            tools = [ExtractionTool.PYTESSERACT, ExtractionTool.DOCLING]

        elif doc_type == DocumentType.ACADEMIC_PAPER:
            # Formulas + tables + structure
            tools = [ExtractionTool.DOCLING, ExtractionTool.PYMUPDF]

        elif doc_type == DocumentType.TECHNICAL_MANUAL:
            # Tables + diagrams + structure
            tools = [ExtractionTool.DOCLING, ExtractionTool.PDFPLUMBER]

        elif doc_type == DocumentType.TEXTBOOK:
            # Complex layout + formulas + tables
            tools = [ExtractionTool.DOCLING, ExtractionTool.PYMUPDF]

        elif doc_type == DocumentType.BUSINESS_REPORT:
            # Tables + charts
            tools = [ExtractionTool.DOCLING, ExtractionTool.PDFPLUMBER]

        elif doc_type == DocumentType.PRESENTATION:
            # Simple text + images
            tools = [ExtractionTool.PYMUPDF, ExtractionTool.DOCLING]

        elif doc_type == DocumentType.BOOK:
            # Continuous text, simple layout
            tools = [ExtractionTool.PYMUPDF, ExtractionTool.DOCLING]

        else:
            # Unknown/Mixed: use comprehensive approach
            if features.table_count > 3 or features.formula_count > 2:
                tools = [ExtractionTool.DOCLING, ExtractionTool.PDFPLUMBER]
            else:
                tools = [ExtractionTool.DOCLING, ExtractionTool.PYMUPDF]

        return tools

    def _generate_reasoning(self, doc_type: DocumentType, features: DocumentFeatures, confidence: float) -> str:
        """Generate human-readable classification reasoning"""
        indicators = []

        if features.has_abstract and features.has_references:
            indicators.append("abstract and references section")
        if features.table_count > 0:
            indicators.append(f"{features.table_count} tables detected")
        if features.formula_count > 0:
            indicators.append(f"{features.formula_count} formulas detected")
        if features.has_toc:
            indicators.append("table of contents")
        if features.is_scanned:
            indicators.append("low text density (possibly scanned)")
        if features.citation_count > 0:
            indicators.append(f"{features.citation_count} citations")

        indicators_str = ", ".join(indicators) if indicators else "general document structure"

        return (
            f"Classified as {doc_type.value} with {confidence:.0%} confidence. "
            f"Key indicators: {indicators_str}. "
            f"Document has {features.page_count} pages with {features.avg_chars_per_page:.0f} chars/page avg."
        )

    # Pattern detection helpers

    def _has_table_pattern(self, text: str) -> bool:
        """Detect table-like structures in text"""
        # Look for patterns: aligned pipes, multiple tabs, grid-like structure
        lines = text.split('\n')

        # Count lines with table indicators
        table_lines = sum(1 for line in lines if '|' in line or '\t\t' in line)

        return table_lines > 3

    def _has_formula_pattern(self, text: str) -> bool:
        """Detect mathematical formulas"""
        math_symbols = ['∫', '∑', '∏', '√', '∂', '∞', '≈', '≤', '≥', '±', '×', '÷', '∈', '∀', '∃']
        math_patterns = [r'\b\w+\s*=\s*\w+[\+\-\*/]\w+', r'\(\w+\s*[\+\-\*/]\s*\w+\)']

        # Check for math symbols
        for symbol in math_symbols:
            if symbol in text:
                return True

        # Check for math patterns
        for pattern in math_patterns:
            if re.search(pattern, text):
                return True

        return False

    def _has_abstract(self, text: str) -> bool:
        """Detect abstract section"""
        abstract_keywords = ['abstract', 'summary', 'overview']
        text_lower = text.lower()

        return any(keyword in text_lower for keyword in abstract_keywords)

    def _has_references(self, text: str) -> bool:
        """Detect references section"""
        ref_keywords = ['references', 'bibliography', 'works cited', 'citations']
        text_lower = text.lower()

        return any(keyword in text_lower for keyword in ref_keywords)

    def _has_code_pattern(self, text: str) -> bool:
        """Detect code blocks"""
        code_indicators = [
            r'def \w+\(',  # Python
            r'function \w+\(',  # JavaScript
            r'public class \w+',  # Java
            r'#include <',  # C/C++
            r'import \w+',  # Python/Java
        ]

        for pattern in code_indicators:
            if re.search(pattern, text):
                return True

        return False

    def _count_citations(self, text: str) -> int:
        """Count citation-like patterns"""
        # Simple heuristic: [Author, Year] or (Author Year)
        patterns = [
            r'\[\w+,\s*\d{4}\]',
            r'\(\w+\s+\d{4}\)',
            r'\[\d+\]'  # Numbered citations
        ]

        count = 0
        for pattern in patterns:
            count += len(re.findall(pattern, text))

        return count
