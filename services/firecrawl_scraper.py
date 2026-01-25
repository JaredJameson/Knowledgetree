"""
KnowledgeTree - Firecrawl Scraper Service
Managed API scraper for difficult sites (5% of use cases)
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class FirecrawlScraper:
    """
    Firecrawl API scraper for difficult cases.
    
    Use for:
    - Sites with aggressive anti-bot protection
    - Captcha challenges
    - Cloudflare anti-bot
    - Sites requiring IP rotation
    
    Pricing (2026):
    - Free: 500 credits (one-time)
    - Hobby: $16/month - 3,000 pages
    - Standard: $83/month - 100,000 pages
    
    Performance: Managed service (fast as their infrastructure)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.firecrawl.dev/v1"
    ):
        self.api_key = api_key
        self.base_url = base_url
        
        if not api_key:
            logger.warning("Firecrawl API key not provided - service will be disabled")
    
    async def scrape(
        self,
        url: str,
        formats: list[str] = None,
        only_main_content: bool = True,
        extract_depth: bool = True
    ) -> Dict[str, Any]:
        """
        Scrape a URL using Firecrawl API.
        
        Args:
            url: URL to scrape
            formats: Output formats ['markdown', 'html', 'extract']
            only_main_content: Extract only main content (skip nav/footer)
            extract_depth: Follow links for deeper extraction
            
        Returns:
            Dict with scraped data
        """
        if not self.api_key:
            raise ValueError("Firecrawl API key not configured")
        
        if formats is None:
            formats = ['markdown', 'html', 'extract']
        
        import httpx
        
        try:
            logger.info(f"Scraping with Firecrawl: {url}")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/scrape",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "url": url,
                        "formats": formats,
                        "onlyMainContent": only_main_content,
                        "extractDepth": extract_depth
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Parse Firecrawl response
                if data.get("success"):
                    result_data = data.get("data", {})
                    
                    return {
                        "url": url,
                        "title": result_data.get("metadata", {}).get("title", ""),
                        "markdown": result_data.get("markdown", ""),
                        "html": result_data.get("html", ""),
                        "extracted_content": result_data.get("llm_extraction", {}),
                        "links": result_data.get("links", []),
                        "metadata": {
                            "engine": "firecrawl",
                            "total_usage": data.get("usage", {}).get("totalTokens", 0)
                        }
                    }
                else:
                    error = data.get("error", "Unknown Firecrawl error")
                    raise Exception(f"Firecrawl error: {error}")
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Firecrawl HTTP error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Error scraping {url} with Firecrawl: {e}")
            raise
    
    async def crawl(
        self,
        url: str,
        limit: int = 100,
        max_depth: int = 2,
        allow_backward_crawling: bool = False
    ) -> Dict[str, Any]:
        """
        Crawl a website starting from URL.
        
        Args:
            url: Starting URL
            limit: Maximum pages to crawl
            max_depth: Maximum depth to follow links
            allow_backward_crawling: Allow crawling parent directories
            
        Returns:
            Dict with crawl results including all scraped pages
        """
        if not self.api_key:
            raise ValueError("Firecrawl API key not configured")
        
        import httpx
        
        try:
            logger.info(f"Crawling with Firecrawl: {url} (limit: {limit}, depth: {max_depth})")
            
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.base_url}/crawl",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "url": url,
                        "limit": limit,
                        "maxDepth": max_depth,
                        "allowBackwardCrawling": allow_backward_crawling,
                        "formats": ["markdown", "extract"]
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                if data.get("success"):
                    job_id = data.get("id")
                    logger.info(f"Firecrawl job started: {job_id}")
                    
                    # Poll for results
                    return await self._poll_crawl_results(client, job_id)
                else:
                    raise Exception(f"Firecrawl crawl error: {data.get('error')}")
                
        except Exception as e:
            logger.error(f"Error crawling {url} with Firecrawl: {e}")
            raise
    
    async def _poll_crawl_results(
        self,
        client: httpx.AsyncClient,
        job_id: str,
        max_wait: int = 300
    ) -> Dict[str, Any]:
        """Poll Firecrawl crawl job for completion."""
        import asyncio
        
        start_time = asyncio.get_event_loop().time()
        
        while True:
            if asyncio.get_event_loop().time() - start_time > max_wait:
                raise TimeoutError(f"Firecrawl job {job_id} timed out")
            
            response = await client.get(
                f"{self.base_url}/crawl/{job_id}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            response.raise_for_status()
            data = response.json()
            
            status = data.get("status")
            
            if status == "completed":
                logger.info(f"Firecrawl job {job_id} completed")
                return data
            elif status == "failed":
                raise Exception(f"Firecrawl job {job_id} failed: {data.get('error')}")
            elif status in ["pending", "processing", "scraping"]:
                await asyncio.sleep(2)
                continue
            else:
                raise Exception(f"Unknown Firecrawl status: {status}")
    
    async def check_usage(self) -> Dict[str, Any]:
        """Check Firecrawl API usage and remaining credits."""
        if not self.api_key:
            return {"enabled": False}
        
        import httpx
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/usage",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Error checking Firecrawl usage: {e}")
            return {"error": str(e)}
