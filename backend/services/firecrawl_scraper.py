"""
KnowledgeTree - Firecrawl Scraper Service
Managed API scraper for difficult websites with anti-bot protection (5% of sites)
"""

import asyncio
import httpx
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import os

from services.content_extractor import content_extractor


@dataclass
class ScrapeResult:
    """Result from scraping a URL"""
    url: str
    title: str
    content: str
    text: str
    links: List[str]
    images: List[str]
    status_code: int
    quality_score: float = 0.0  # 0.0-1.0
    extraction_method: str = "basic"  # trafilatura | readability | basic
    error: Optional[str] = None


class FirecrawlScraper:
    """
    Firecrawl API scraper for difficult websites
    
    Use case: 5% of websites - anti-bot protection, CAPTCHA, complex auth
    Pros: Handles difficult sites, no maintenance overhead
    Cons: Paid service ($16-83/month), API rate limits
    
    Pricing (2024):
    - Free: 500 credits (one-time)
    - Hobby: $16/mo - 3,000 pages
    - Standard: $83/mo - 100,000 pages
    
    Website: https://www.firecrawl.dev
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: str = "https://api.firecrawl.dev/v1"
    ):
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
        self.api_url = api_url
        
        if not self.api_key:
            print("Warning: FIRECRAWL_API_KEY not set. Firecrawl features will be disabled.")
    
    async def scrape(
        self,
        url: str,
        extract_links: bool = True,
        extract_images: bool = False
    ) -> ScrapeResult:
        """
        Scrape a URL using Firecrawl API
        
        Args:
            url: URL to scrape
            extract_links: Whether to extract links
            extract_images: Whether to extract images
        
        Returns:
            ScrapeResult with scraped data
        """
        if not self.api_key:
            return ScrapeResult(
                url=url,
                title="",
                content="",
                text="",
                links=[],
                images=[],
                status_code=0,
                error="Firecrawl API key not configured"
            )
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.api_url}/scrape",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "url": url,
                        "formats": ["markdown", "html", "extract"],
                        "onlyMainContent": True,
                        "includeTags": ["a", "img"] if (extract_links or extract_images) else []
                    },
                    timeout=120.0
                )
                
                if response.status_code == 401:
                    return ScrapeResult(
                        url=url,
                        title="",
                        content="",
                        text="",
                        links=[],
                        images=[],
                        status_code=401,
                        error="Invalid Firecrawl API key"
                    )
                
                if response.status_code == 402:
                    return ScrapeResult(
                        url=url,
                        title="",
                        content="",
                        text="",
                        links=[],
                        images=[],
                        status_code=402,
                        error="Firecrawl credits exhausted"
                    )
                
                response.raise_for_status()
                data = response.json()
                
                if not data.get("success"):
                    return ScrapeResult(
                        url=url,
                        title="",
                        content="",
                        text="",
                        links=[],
                        images=[],
                        status_code=500,
                        error=data.get("error", "Unknown Firecrawl error")
                    )
                
                # Extract data from response
                result = data.get("data", {})
                metadata = result.get("metadata", {})

                # Calculate quality score for Firecrawl content
                text_content = result.get("markdown", "")
                quality_score = content_extractor._calculate_quality_score(text_content)

                return ScrapeResult(
                    url=result.get("url", url),
                    title=metadata.get("title", ""),
                    content=result.get("html", ""),
                    text=text_content,
                    links=metadata.get("links", []) if extract_links else [],
                    images=metadata.get("images", []) if extract_images else [],
                    status_code=200,
                    quality_score=quality_score,
                    extraction_method="firecrawl"
                )
        
        except httpx.HTTPStatusError as e:
            return ScrapeResult(
                url=url,
                title="",
                content="",
                text="",
                links=[],
                images=[],
                status_code=e.response.status_code if e.response else 0,
                error=f"Firecrawl HTTP error: {e.response.status_code if e.response else 'Unknown'}"
            )
        except httpx.TimeoutException:
            return ScrapeResult(
                url=url,
                title="",
                content="",
                text="",
                links=[],
                images=[],
                status_code=0,
                error="Firecrawl request timeout"
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
                error=f"Firecrawl error: {str(e)}"
            )
    
    async def batch_scrape(
        self,
        urls: List[str],
        **kwargs
    ) -> List[ScrapeResult]:
        """
        Scrape multiple URLs
        
        Note: Firecrawl has its own batch API, but for simplicity
        we'll use concurrent requests here.
        
        Args:
            urls: List of URLs to scrape
            **kwargs: Additional arguments for scrape()
        
        Returns:
            List of ScrapeResult
        """
        tasks = [self.scrape(url, **kwargs) for url in urls]
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
                    error=f"Exception: {str(result)}"
                ))
            else:
                final_results.append(result)
        
        return final_results
