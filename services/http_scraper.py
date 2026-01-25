"""
KnowledgeTree - HTTP Scraper Service
Fast HTTP-based scraper for static HTML pages (80% of use cases)
"""

import logging
import asyncio
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup
from lxml import etree

logger = logging.getLogger(__name__)


class HTTPScraper:
    """
    Fast HTTP scraper for static HTML content.
    
    Use for:
    - Blogs, documentation, news sites
    - Simple HTML pages without JavaScript
    - High-volume crawling (1000+ URLs)
    
    Performance: 100-500 requests/second
    Cost: $0
    """
    
    def __init__(
        self,
        timeout: float = 30.0,
        max_redirects: int = 5,
        user_agent: Optional[str] = None
    ):
        self.timeout = timeout
        self.max_redirects = max_redirects
        
        # Browser-like user agent
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
        
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,pl;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
    
    async def scrape(
        self,
        url: str,
        extract_links: bool = True,
        extract_images: bool = False
    ) -> Dict[str, Any]:
        """
        Scrape a single URL.
        
        Args:
            url: URL to scrape
            extract_links: Extract all links from the page
            extract_images: Extract image URLs
            
        Returns:
            Dict with scraped data:
            - url: Final URL (after redirects)
            - title: Page title
            - content: Main content (cleaned HTML)
            - text: Plain text content
            - links: List of links (if extract_links=True)
            - images: List of image URLs (if extract_images=True)
            - metadata: Response metadata (status, headers, etc.)
        """
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                max_redirects=self.max_redirects
            ) as client:
                
                logger.info(f"Scraping with HTTP scraper: {url}")
                
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                
                # Parse HTML
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Extract title
                title = soup.title.string.strip() if soup.title else ""
                
                # Remove script/style elements
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()
                
                # Get main content
                content = str(soup.body) if soup.body else str(soup)
                text = soup.get_text(separator='\n', strip=True)
                
                result = {
                    "url": str(response.url),
                    "title": title,
                    "content": content,
                    "text": text,
                    "metadata": {
                        "status_code": response.status_code,
                        "content_type": response.headers.get("content-type"),
                        "content_length": len(response.content),
                        "engine": "http_scraper"
                    }
                }
                
                # Extract links if requested
                if extract_links:
                    result["links"] = self._extract_links(soup, url)
                
                # Extract images if requested
                if extract_images:
                    result["images"] = self._extract_images(soup, url)
                
                logger.info(f"Successfully scraped {url} ({len(text)} chars)")
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error scraping {url}: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            raise
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> list[Dict[str, str]]:
        """Extract all links from the page."""
        links = []
        parsed_base = urlparse(base_url)
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            
            # Convert relative URLs to absolute
            if href.startswith('/'):
                href = f"{parsed_base.scheme}://{parsed_base.netloc}{href}"
            elif not href.startswith('http'):
                continue
            
            links.append({
                "url": href,
                "text": text
            })
        
        return links
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> list[str]:
        """Extract all image URLs from the page."""
        images = []
        parsed_base = urlparse(base_url)
        
        for img in soup.find_all('img', src=True):
            src = img['src']
            
            # Convert relative URLs to absolute
            if src.startswith('/'):
                src = f"{parsed_base.scheme}://{parsed_base.netloc}{src}"
            elif not src.startswith('http'):
                continue
            
            images.append(src)
        
        return images
    
    async def batch_scrape(
        self,
        urls: list[str],
        concurrency: int = 10,
        **kwargs
    ) -> list[Dict[str, Any]]:
        """
        Scrape multiple URLs concurrently.
        
        Args:
            urls: List of URLs to scrape
            concurrency: Max concurrent requests
            **kwargs: Passed to scrape()
            
        Returns:
            List of scrape results
        """
        semaphore = asyncio.Semaphore(concurrency)
        
        async def scrape_with_semaphore(url: str):
            async with semaphore:
                return await self.scrape(url, **kwargs)
        
        tasks = [scrape_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        return [r for r in results if not isinstance(r, Exception)]
