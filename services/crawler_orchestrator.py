"""
KnowledgeTree - Crawler Orchestrator
Auto-selects the best scraping engine based on URL detection
"""

import logging
from typing import Optional, Dict, Any, Literal
from enum import Enum

from services.http_scraper import HTTPScraper
from services.playwright_scraper import PlaywrightScraper
from services.firecrawl_scraper import FirecrawlScraper

logger = logging.getLogger(__name__)


class CrawlEngine(str, Enum):
    """Available crawl engines"""
    HTTP = "http"
    PLAYWRIGHT = "playwright"
    FIRECRAWL = "firecrawl"


class CrawlerOrchestrator:
    """
    Intelligent crawler orchestrator that auto-selects the best engine.
    
    Selection Logic:
    1. Try HTTP scraper first (fastest, 80% of sites)
    2. Detect JavaScript requirement → Playwright
    3. Detect anti-bot protection → Firecrawl
    4. Allow manual override with force_engine
    """
    
    def __init__(
        self,
        firecrawl_api_key: Optional[str] = None
    ):
        self.http_scraper = HTTPScraper()
        self.playwright_scraper = PlaywrightScraper()
        self.firecrawl_scraper = FirecrawlScraper(api_key=firecrawl_api_key)
        
        # Known JS-heavy sites
        self.js_heavy_domains = {
            'twitter.com', 'x.com',
            'facebook.com', 'instagram.com',
            'linkedin.com',
            'youtube.com',
            'reddit.com',
            'amazon.com',
            'netflix.com',
            'spotify.com'
        }
        
        # Known difficult sites (anti-bot)
        self.difficult_domains = {
            'selenium.dev',
            'bot.sannysoft.com',
            'airbnb.com',  # Often has anti-bot
            'booking.com',
        }
    
    async def crawl(
        self,
        url: str,
        engine: Optional[CrawlEngine] = None,
        force_engine: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Crawl a URL with auto-selected engine.
        
        Args:
            url: URL to crawl
            engine: Force specific engine (None = auto-detect)
            force_engine: If True, skip detection and use specified engine
            **kwargs: Passed to selected scraper
            
        Returns:
            Dict with scraped data
        """
        # If engine forced, use it
        if force_engine and engine:
            logger.info(f"Using forced engine: {engine.value}")
            return await self._execute_with_engine(url, engine, **kwargs)
        
        # Auto-detect best engine
        detected = await self._detect_requirements(url)
        
        if detected.get("needs_firecrawl"):
            logger.info(f"Detected difficult site, using Firecrawl: {url}")
            return await self.firecrawl_scraper.scrape(url, **kwargs)
        
        elif detected.get("needs_playwright"):
            logger.info(f"Detected JS-heavy site, using Playwright: {url}")
            return await self.playwright_scraper.scrape(url, **kwargs)
        
        else:
            logger.info(f"Using default HTTP scraper: {url}")
            return await self.http_scraper.scrape(url, **kwargs)
    
    async def batch_crawl(
        self,
        urls: list[str],
        engine: Optional[CrawlEngine] = None,
        force_engine: bool = False,
        **kwargs
    ) -> list[Dict[str, Any]]:
        """
        Crawl multiple URLs with auto-selected engines.
        
        Args:
            urls: List of URLs to crawl
            engine: Force specific engine for all URLs
            force_engine: If True, skip detection
            **kwargs: Passed to scrapers
            
        Returns:
            List of scrape results
        """
        import asyncio
        
        results = []
        
        for url in urls:
            try:
                result = await self.crawl(url, engine=engine, force_engine=force_engine, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to crawl {url}: {e}")
                results.append({
                    "url": url,
                    "error": str(e),
                    "failed": True
                })
        
        return results
    
    async def _detect_requirements(self, url: str) -> Dict[str, bool]:
        """
        Detect what scraping engine is needed.
        
        Returns dict with:
        - needs_playwright: bool
        - needs_firecrawl: bool
        - confidence: float (0-1)
        """
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        result = {
            "needs_playwright": False,
            "needs_firecrawl": False,
            "confidence": 0.5,
            "reason": []
        }
        
        # Check if known difficult domain
        if domain in self.difficult_domains:
            result["needs_firecrawl"] = True
            result["confidence"] = 0.95
            result["reason"].append("Known difficult domain")
            return result
        
        # Check if known JS-heavy domain
        if domain in self.js_heavy_domains:
            result["needs_playwright"] = True
            result["confidence"] = 0.9
            result["reason"].append("Known JS-heavy domain")
            return result
        
        # Try HTTP scraper first to detect
        try:
            # Quick HEAD request to check response
            import httpx
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.head(url, follow_redirects=True)
                
                # Check content type
                content_type = response.headers.get('content-type', '').lower()
                
                if 'html' not in content_type:
                    # Not HTML, maybe JSON or other
                    result["needs_playwright"] = True
                    result["reason"].append("Non-HTML content type")
                
                # Check for server-side rendering indicators
                # If no SSR detected, might need Playwright
                # (This is a simple heuristic)
                
        except Exception as e:
            # If HEAD fails, might need more robust scraper
            result["needs_firecrawl"] = True
            result["confidence"] = 0.7
            result["reason"].append(f"HEAD request failed: {e}")
        
        return result
    
    async def _execute_with_engine(
        self,
        url: str,
        engine: CrawlEngine,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute crawl with specific engine."""
        if engine == CrawlEngine.HTTP:
            return await self.http_scraper.scrape(url, **kwargs)
        
        elif engine == CrawlEngine.PLAYWRIGHT:
            return await self.playwright_scraper.scrape(url, **kwargs)
        
        elif engine == CrawlEngine.FIRECRAWL:
            return await self.firecrawl_scraper.scrape(url, **kwargs)
        
        else:
            raise ValueError(f"Unknown engine: {engine}")
    
    async def close(self):
        """Cleanup resources."""
        await self.playwright_scraper.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
