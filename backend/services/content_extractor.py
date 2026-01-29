"""
KnowledgeTree - Smart Content Extractor
Intelligent extraction of valuable content from HTML with quality scoring
"""

import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from bs4 import BeautifulSoup
import trafilatura
from readability import Document


@dataclass
class ExtractedContent:
    """Result from content extraction"""
    text: str
    title: str
    method: str  # trafilatura | readability | basic
    quality_score: float  # 0.0-1.0
    metadata: Dict[str, Any]


class SmartContentExtractor:
    """
    Intelligent content extraction with noise filtering
    
    Uses multiple extraction methods with fallback:
    1. Trafilatura (best for articles, docs)
    2. Readability (good for news, blogs)
    3. Basic extraction with noise removal (fallback)
    """
    
    # CSS selectors to remove (noise)
    NOISE_SELECTORS = [
        'nav', 'header', 'footer', 'aside',
        '.advertisement', '.ad', '.ads',
        '.cookie-banner', '.cookie-notice',
        '.social-share', '.social-sharing',
        '.comments', '.comment-section',
        '#sidebar', '#navigation',
        '.newsletter-signup', '.newsletter',
        '.related-articles', '.recommended',
        '#cookie-consent', '.gdpr-notice',
        'script', 'style', 'noscript',
        '.breadcrumb', '.breadcrumbs',
        '.author-bio', '.author-info',
        '.share-buttons', '.sharing',
        '.popup', '.modal', '.overlay'
    ]
    
    def __init__(
        self,
        min_text_length: int = 200,
        min_quality_score: float = 0.5,
        prefer_trafilatura: bool = True
    ):
        self.min_text_length = min_text_length
        self.min_quality_score = min_quality_score
        self.prefer_trafilatura = prefer_trafilatura
    
    def extract(
        self,
        html: str,
        url: str,
        custom_noise_selectors: Optional[List[str]] = None
    ) -> ExtractedContent:
        """
        Extract valuable content from HTML
        
        Args:
            html: Raw HTML content
            url: Source URL (for trafilatura)
            custom_noise_selectors: Additional CSS selectors to remove
        
        Returns:
            ExtractedContent with extracted text and quality score
        """
        # Try extraction methods in order of quality
        
        # Method 1: Trafilatura (best)
        if self.prefer_trafilatura:
            result = self._extract_trafilatura(html, url)
            if result and result.quality_score >= self.min_quality_score:
                return result
        
        # Method 2: Readability (good)
        result = self._extract_readability(html)
        if result and result.quality_score >= self.min_quality_score:
            return result
        
        # Method 3: Basic extraction with noise removal (fallback)
        return self._extract_basic(
            html, 
            custom_noise_selectors or []
        )
    
    def _extract_trafilatura(self, html: str, url: str) -> Optional[ExtractedContent]:
        """Extract using trafilatura library"""
        try:
            # Trafilatura extraction with optimal settings
            text = trafilatura.extract(
                html,
                url=url,
                include_comments=False,  # No comment sections
                include_tables=True,     # Keep tables (data!)
                include_images=False,    # Text only
                no_fallback=False,       # Allow fallback
                favor_recall=False,      # Precision > recall (less noise)
                deduplicate=True,        # Remove duplicate content
                target_language='pl'     # Polish preference
            )
            
            if not text or len(text) < self.min_text_length:
                return None
            
            # Extract title
            title = self._extract_title_trafilatura(html, url)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(text)
            
            return ExtractedContent(
                text=text,
                title=title,
                method="trafilatura",
                quality_score=quality_score,
                metadata={
                    "length": len(text),
                    "word_count": len(text.split())
                }
            )
        
        except Exception as e:
            print(f"Trafilatura extraction failed: {e}")
            return None
    
    def _extract_title_trafilatura(self, html: str, url: str) -> str:
        """Extract title using trafilatura metadata"""
        try:
            metadata = trafilatura.extract_metadata(html, url=url)
            if metadata and metadata.title:
                return metadata.title
        except:
            pass
        
        # Fallback to BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        
        return ""
    
    def _extract_readability(self, html: str) -> Optional[ExtractedContent]:
        """Extract using Mozilla's readability algorithm"""
        try:
            doc = Document(html)
            title = doc.title()
            summary_html = doc.summary()
            
            # Convert HTML to text
            soup = BeautifulSoup(summary_html, 'lxml')
            text = soup.get_text(separator='\n', strip=True)
            
            if not text or len(text) < self.min_text_length:
                return None
            
            quality_score = self._calculate_quality_score(text)
            
            return ExtractedContent(
                text=text,
                title=title or "",
                method="readability",
                quality_score=quality_score,
                metadata={
                    "length": len(text),
                    "word_count": len(text.split())
                }
            )
        
        except Exception as e:
            print(f"Readability extraction failed: {e}")
            return None
    
    def _extract_basic(
        self, 
        html: str,
        custom_selectors: List[str]
    ) -> ExtractedContent:
        """Basic extraction with noise removal (fallback)"""
        soup = BeautifulSoup(html, 'lxml')
        
        # Extract title
        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        
        # Remove noise elements
        all_selectors = self.NOISE_SELECTORS + custom_selectors
        for selector in all_selectors:
            for element in soup.select(selector):
                element.decompose()
        
        # Try to find main content area
        main_content = None
        for tag in ['main', 'article', '[role="main"]', '.main-content', '#content']:
            main_content = soup.select_one(tag)
            if main_content:
                break
        
        # Extract text
        if main_content:
            text = main_content.get_text(separator='\n', strip=True)
        else:
            # Fallback to body
            body = soup.find('body')
            text = body.get_text(separator='\n', strip=True) if body else ""
        
        # Clean up text
        text = self._clean_text(text)
        
        quality_score = self._calculate_quality_score(text)
        
        return ExtractedContent(
            text=text,
            title=title,
            method="basic",
            quality_score=quality_score,
            metadata={
                "length": len(text),
                "word_count": len(text.split()),
                "warning": "Basic extraction used - may contain noise"
            }
        )
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        
        # Remove common noise patterns
        text = re.sub(r'Cookie (Policy|Notice|Consent).*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'(Share|Tweet|Pin|Like) on .*', '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def _calculate_quality_score(self, text: str) -> float:
        """
        Calculate content quality score (0.0-1.0)
        
        Factors:
        - Length (optimal: 200-5000 chars)
        - Word count (optimal: 50-2000 words)
        - Sentence structure
        - Paragraph structure
        - Text diversity (not too repetitive)
        """
        score = 0.0
        
        if not text:
            return 0.0
        
        # 1. Length score (0.25)
        length = len(text)
        if 200 <= length <= 5000:
            score += 0.25
        elif 5000 < length <= 10000:
            score += 0.20
        elif length > 10000:
            score += 0.15
        elif length >= 100:
            score += 0.10
        
        # 2. Word count score (0.25)
        words = text.split()
        word_count = len(words)
        if 50 <= word_count <= 2000:
            score += 0.25
        elif 2000 < word_count <= 5000:
            score += 0.20
        elif word_count >= 20:
            score += 0.10
        
        # 3. Sentence structure score (0.20)
        sentences = text.count('.') + text.count('!') + text.count('?')
        if sentences >= 5:
            avg_words_per_sentence = word_count / sentences
            if 10 <= avg_words_per_sentence <= 30:
                score += 0.20
            elif 5 <= avg_words_per_sentence <= 50:
                score += 0.15
        
        # 4. Paragraph structure score (0.15)
        paragraphs = text.count('\n\n') + 1
        if paragraphs >= 3:
            score += 0.15
        elif paragraphs >= 2:
            score += 0.10
        
        # 5. Text diversity score (0.15)
        # Check for repetitive content
        if word_count > 0:
            unique_words = len(set(words))
            diversity_ratio = unique_words / word_count
            if diversity_ratio >= 0.5:
                score += 0.15
            elif diversity_ratio >= 0.3:
                score += 0.10
            elif diversity_ratio >= 0.2:
                score += 0.05
        
        return min(score, 1.0)
    
    def should_index(self, extracted: ExtractedContent) -> bool:
        """
        Decide if extracted content is valuable enough to index
        
        Args:
            extracted: ExtractedContent result
        
        Returns:
            True if content should be indexed
        """
        # Quality threshold
        if extracted.quality_score < self.min_quality_score:
            return False
        
        # Length threshold
        if len(extracted.text) < self.min_text_length:
            return False
        
        # Must have meaningful content (not just navigation/footer)
        words = extracted.text.split()
        if len(words) < 20:
            return False
        
        return True


# Singleton instance
content_extractor = SmartContentExtractor(
    min_text_length=200,
    min_quality_score=0.5,
    prefer_trafilatura=True
)
