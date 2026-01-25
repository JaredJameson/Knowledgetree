"""
KnowledgeTree - HTTP Scraper Service
Fast HTTP-based scraper for static HTML websites (80% of sites)
"""

import asyncio
import httpx
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin, urlparse
import re
from dataclasses import dataclass


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
    error: Optional[str] = None


class HTTPScraper:
    """
    Fast HTTP scraper for static HTML websites
    
    Use case: 80% of websites - blogs, documentation, news sites, e-commerce
    Pros: Fast, free, low resource usage
    Cons: Doesn't execute JavaScript
    """
    
    def __init__(
        self,
        timeout: float = 30.0,
        max_content_length: int = 10_000_000,  # 10MB
        user_agent: Optional[str] = None
    ):
        self.timeout = timeout
        self.max_content_length = max_content_length
        self.headers = {
            "User-Agent": user_agent or (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
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
    ) -> ScrapeResult:
        """
        Scrape a single URL
        
        Args:
            url: URL to scrape
            extract_links: Whether to extract links from the page
            extract_images: Whether to extract images from the page
        
        Returns:
            ScrapeResult with scraped data
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self.headers, follow_redirects=True)
                response.raise_for_status()
                
                # Check content length
                content_length = len(response.content)
                if content_length > self.max_content_length:
                    return ScrapeResult(
                        url=str(response.url),
                        title="",
                        content="",
                        text="",
                        links=[],
                        images=[],
                        status_code=response.status_code,
                        error=f"Content too large: {content_length} bytes"
                    )
                
                # Parse HTML
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Extract title
                title = ""
                if soup.title:
                    title = soup.title.string.strip() if soup.title.string else ""
                
                # Extract main content
                content = self._extract_main_content(soup)
                
                # Extract text (for RAG/indexing)
                text = soup.get_text(separator='\n', strip=True)
                
                # Extract links
                links = []
                if extract_links:
                    links = self._extract_links(url, soup)
                
                # Extract images
                images = []
                if extract_images:
                    images = self._extract_images(url, soup)
                
                return ScrapeResult(
                    url=str(response.url),
                    title=title,
                    content=content,
                    text=text,
                    links=links,
                    images=images,
                    status_code=response.status_code
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
                error=f"HTTP error: {e.response.status_code if e.response else 'Unknown'}"
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
                error="Request timeout"
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
                error=f"Scraping error: {str(e)}"
            )
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from HTML"""
        # Try to find main content area
        for tag in ['main', 'article', '[role="main"]']:
            main = soup.find(tag)
            if main:
                return main.get_text(separator='\n', strip=True)
        
        # Fallback to body
        body = soup.find('body')
        if body:
            return body.get_text(separator='\n', strip=True)
        
        return ""
    
    def _extract_links(self, base_url: str, soup: BeautifulSoup) -> List[str]:
        """Extract all links from the page"""
        links = []
        base_domain = urlparse(base_url).netloc
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            absolute_url = urljoin(base_url, href)
            
            # Filter out fragments, mailto, tel
            if absolute_url.startswith(('#', 'mailto:', 'tel:', 'javascript:')):
                continue
            
            # Optionally filter to same domain
            # if urlparse(absolute_url).netloc != base_domain:
            #     continue
            
            links.append(absolute_url)
        
        return links
    
    def _extract_images(self, base_url: str, soup: BeautifulSoup) -> List[str]:
        """Extract all images from the page"""
        images = []
        
        for img in soup.find_all('img', src=True):
            src = img['src']
            absolute_url = urljoin(base_url, src)
            images.append(absolute_url)
        
        return images
    
    async def batch_scrape(
        self,
        urls: List[str],
        concurrency: int = 10,
        extract_links: bool = True,
        extract_images: bool = False
    ) -> List[ScrapeResult]:
        """
        Scrape multiple URLs concurrently
        
        Args:
            urls: List of URLs to scrape
            concurrency: Maximum concurrent requests
            extract_links: Whether to extract links
            extract_images: Whether to extract images
        
        Returns:
            List of ScrapeResult (same order as input)
        """
        semaphore = asyncio.Semaphore(concurrency)
        
        async def scrape_with_semaphore(url: str) -> ScrapeResult:
            async with semaphore:
                return await self.scrape(url, extract_links, extract_images)
        
        tasks = [scrape_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
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
