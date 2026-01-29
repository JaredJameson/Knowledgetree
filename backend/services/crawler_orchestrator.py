"""
KnowledgeTree - Crawler Orchestrator
Auto-selects the best scraping engine based on URL detection
"""

import asyncio
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass

from services.http_scraper import HTTPScraper, ScrapeResult as HTTPResult
from services.playwright_scraper import PlaywrightScraper, ScrapeResult as PlaywrightResult
from services.firecrawl_scraper import FirecrawlScraper, ScrapeResult as FirecrawlResult


class CrawlEngine(str, Enum):
    """Available scraping engines"""
    HTTP = "http"  # Fast HTTP scraper (80% of sites)
    PLAYWRIGHT = "playwright"  # Browser automation (15% of sites)
    FIRECRAWL = "firecrawl"  # Managed API (5% of sites)


@dataclass
class ScrapeResult:
    """Unified scrape result"""
    url: str
    title: str
    content: str
    text: str
    links: List[str]
    images: List[str]
    status_code: int
    engine: CrawlEngine
    quality_score: float = 0.0  # 0.0-1.0
    extraction_method: str = "basic"  # trafilatura | readability | basic
    error: Optional[str] = None


class CrawlerOrchestrator:
    """
    Auto-selecting crawler orchestrator
    
    Automatically chooses the best scraping engine based on:
    - URL pattern detection
    - Domain heuristics
    - Manual override options
    """
    
    # Known JavaScript-heavy domains (require Playwright)
    JS_HEAVY_DOMAINS = {
        'twitter.com', 'x.com', 'facebook.com', 'instagram.com',
        'linkedin.com', 'reddit.com', 'youtube.com',
        'amazon.com', 'ebay.com', 'etsy.com',
        'react.dev', 'vuejs.org', 'angular.io',
        'nextjs.org', 'gatsbyjs.com'
    }
    
    # Known difficult domains (require Firecrawl)
    DIFFICULT_DOMAINS = {
        'selenium.dev',
        'bot.sannysoft.com',
        'airbnb.com',
        'glassdoor.com',
        'indeed.com'
    }
    
    def __init__(
        self,
        firecrawl_api_key: Optional[str] = None,
        default_timeout: float = 30.0
    ):
        self.http_scraper = HTTPScraper(timeout=default_timeout)
        self.playwright_scraper = PlaywrightScraper(timeout=default_timeout * 1000)
        self.firecrawl_scraper = FirecrawlScraper(api_key=firecrawl_api_key)
    
    async def _detect_requirements(self, url: str) -> Dict[str, Any]:
        """
        Detect which scraping engine is needed
        
        Returns dict with:
        - needs_playwright: bool
        - needs_firecrawl: bool
        - confidence: float (0-1)
        """
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Check for difficult domains
        for difficult_domain in self.DIFFICULT_DOMAINS:
            if difficult_domain in domain:
                return {
                    "needs_playwright": False,
                    "needs_firecrawl": True,
                    "confidence": 0.95,
                    "reason": f"Known difficult domain: {difficult_domain}"
                }
        
        # Check for JS-heavy domains
        for js_domain in self.JS_HEAVY_DOMAINS:
            if js_domain in domain:
                return {
                    "needs_playwright": True,
                    "needs_firecrawl": False,
                    "confidence": 0.90,
                    "reason": f"Known JS-heavy domain: {js_domain}"
                }
        
        # Check for URL patterns indicating SPA
        spa_indicators = ['#!/', '#/', '/app/', '/spa/', 'nextjs', 'react']
        if any(indicator in url.lower() for indicator in spa_indicators):
            return {
                "needs_playwright": True,
                "needs_firecrawl": False,
                "confidence": 0.75,
                "reason": "URL indicates SPA architecture"
            }
        
        # Default to HTTP scraper
        return {
            "needs_playwright": False,
            "needs_firecrawl": False,
            "confidence": 0.60,
            "reason": "Defaulting to HTTP scraper"
        }
    
    async def _execute_with_engine(
        self,
        url: str,
        engine: CrawlEngine,
        **kwargs
    ) -> ScrapeResult:
        """Execute crawl with specific engine"""
        try:
            if engine == CrawlEngine.HTTP:
                result: HTTPResult = await self.http_scraper.scrape(url, **kwargs)
                return ScrapeResult(
                    url=result.url,
                    title=result.title,
                    content=result.content,
                    text=result.text,
                    links=result.links,
                    images=result.images,
                    status_code=result.status_code,
                    engine=engine,
                    quality_score=result.quality_score,
                    extraction_method=result.extraction_method,
                    error=result.error
                )
            
            elif engine == CrawlEngine.PLAYWRIGHT:
                result: PlaywrightResult = await self.playwright_scraper.scrape(url, **kwargs)
                return ScrapeResult(
                    url=result.url,
                    title=result.title,
                    content=result.content,
                    text=result.text,
                    links=result.links,
                    images=result.images,
                    status_code=result.status_code,
                    engine=engine,
                    quality_score=result.quality_score,
                    extraction_method=result.extraction_method,
                    error=result.error
                )
            
            elif engine == CrawlEngine.FIRECRAWL:
                result: FirecrawlResult = await self.firecrawl_scraper.scrape(url, **kwargs)
                return ScrapeResult(
                    url=result.url,
                    title=result.title,
                    content=result.content,
                    text=result.text,
                    links=result.links,
                    images=result.images,
                    status_code=result.status_code,
                    engine=engine,
                    quality_score=result.quality_score,
                    extraction_method=result.extraction_method,
                    error=result.error
                )
        
        except Exception as e:
            return ScrapeResult(
                url=url,
                title="",
                content="",
                text="",
                links=[],
                images=[],
                status_code=0,
                engine=engine,
                error=f"Engine error: {str(e)}"
            )
    
    async def crawl(
        self,
        url: str,
        engine: Optional[CrawlEngine] = None,
        force_engine: bool = False,
        **kwargs
    ) -> ScrapeResult:
        """
        Crawl a URL with auto or manual engine selection
        
        Args:
            url: URL to crawl
            engine: Specific engine to use (if None, auto-detect)
            force_engine: If True, skip auto-detection and use specified engine
            **kwargs: Additional arguments for the scraper
        
        Returns:
            ScrapeResult with crawled data
        """
        # If engine forced or manual selection
        if force_engine and engine:
            return await self._execute_with_engine(url, engine, **kwargs)
        
        # Auto-detect engine
        if engine:
            return await self._execute_with_engine(url, engine, **kwargs)
        
        detection = await self._detect_requirements(url)
        
        if detection.get("needs_firecrawl"):
            return await self._execute_with_engine(url, CrawlEngine.FIRECRAWL, **kwargs)
        elif detection.get("needs_playwright"):
            return await self._execute_with_engine(url, CrawlEngine.PLAYWRIGHT, **kwargs)
        else:
            return await self._execute_with_engine(url, CrawlEngine.HTTP, **kwargs)
    
    async def batch_crawl(
        self,
        urls: List[str],
        engine: Optional[CrawlEngine] = None,
        force_engine: bool = False,
        concurrency: int = 5,
        **kwargs
    ) -> List[ScrapeResult]:
        """
        Crawl multiple URLs
        
        Args:
            urls: List of URLs to crawl
            engine: Specific engine to use for all URLs
            force_engine: If True, use same engine for all URLs
            concurrency: Maximum concurrent crawls
            **kwargs: Additional arguments for scrapers
        
        Returns:
            List of ScrapeResult
        """
        semaphore = asyncio.Semaphore(concurrency)
        
        async def crawl_with_semaphore(url: str) -> ScrapeResult:
            async with semaphore:
                return await self.crawl(url, engine=engine, force_engine=force_engine, **kwargs)
        
        tasks = [crawl_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(ScrapeResult(
                    url=urls[i],
                    title="",
                    content="",
                    text="",
                    links=[],
                    images=[],
                    status_code=0,
                    engine=CrawlEngine.HTTP,
                    error=f"Exception: {str(result)}"
                ))
            else:
                final_results.append(result)
        
        return final_results


# Singleton instance
orchestrator = CrawlerOrchestrator(
    firecrawl_api_key=None  # Set via FIRECRAWL_API_KEY env var
)
