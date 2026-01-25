"""
KnowledgeTree - Playwright Scraper Service
Browser automation scraper for JavaScript-heavy websites (15% of sites)
"""

import asyncio
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin, urlparse
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


class PlaywrightScraper:
    """
    Browser-based scraper using Playwright
    
    Use case: 15% of websites - SPAs (React/Vue/Angular), infinite scroll, dynamic content
    Pros: Executes JavaScript, handles complex interactions
    Cons: Slower, more resource intensive
    """
    
    def __init__(
        self,
        headless: bool = True,
        timeout: float = 30000,  # 30 seconds
        viewport: Optional[Dict[str, int]] = None
    ):
        self.headless = headless
        self.timeout = timeout
        self.viewport = viewport or {'width': 1920, 'height': 1080}
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    
    async def scrape(
        self,
        url: str,
        wait_for_selector: Optional[str] = None,
        wait_for_timeout: int = 5000,
        extract_links: bool = True,
        extract_images: bool = False
    ) -> ScrapeResult:
        """
        Scrape a URL using Playwright
        
        Args:
            url: URL to scrape
            wait_for_selector: CSS selector to wait for before scraping
            wait_for_timeout: Max time to wait for selector (ms)
            extract_links: Whether to extract links
            extract_images: Whether to extract images
        
        Returns:
            ScrapeResult with scraped data
        """
        try:
            from playwright.async_api import async_playwright, Page
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                
                # Create context with realistic settings
                context = await browser.new_context(
                    viewport=self.viewport,
                    user_agent=self.user_agent,
                    locale='en-US',
                    timezone_id='America/New_York'
                )
                
                # Add stealth scripts to avoid detection
                await context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                """)
                
                page = await context.new_page()
                
                # Navigate to URL
                try:
                    await page.goto(url, wait_until='networkidle', timeout=self.timeout)
                except Exception as e:
                    await browser.close()
                    return ScrapeResult(
                        url=url,
                        title="",
                        content="",
                        text="",
                        links=[],
                        images=[],
                        status_code=0,
                        error=f"Navigation timeout: {str(e)}"
                    )
                
                # Wait for specific selector if provided
                if wait_for_selector:
                    try:
                        await page.wait_for_selector(wait_for_selector, timeout=wait_for_timeout)
                    except:
                        pass  # Continue even if selector not found
                
                # Extract data
                result_url = page.url
                title = await page.title()
                
                # Extract text content
                text = await page.evaluate('() => document.body.innerText')
                
                # Extract HTML content
                content = await page.evaluate('() => document.body.innerHTML')
                
                # Extract links
                links = []
                if extract_links:
                    links = await page.evaluate('''() => {
                        const links = [];
                        document.querySelectorAll('a[href]').forEach(a => {
                            links.push(a.href);
                        });
                        return links;
                    }''')
                
                # Extract images
                images = []
                if extract_images:
                    images = await page.evaluate('''() => {
                        const images = [];
                        document.querySelectorAll('img[src]').forEach(img => {
                            images.push(img.src);
                        });
                        return images;
                    }''')
                
                await browser.close()
                
                return ScrapeResult(
                    url=result_url,
                    title=title or "",
                    content=content,
                    text=text,
                    links=links,
                    images=images,
                    status_code=200
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
                error=f"Playwright error: {str(e)}"
            )
    
    async def batch_scrape(
        self,
        urls: List[str],
        concurrency: int = 3,  # Lower for browser-based scraping
        **kwargs
    ) -> List[ScrapeResult]:
        """
        Scrape multiple URLs concurrently
        
        Args:
            urls: List of URLs to scrape
            concurrency: Maximum concurrent browsers
            **kwargs: Additional arguments for scrape()
        
        Returns:
            List of ScrapeResult
        """
        semaphore = asyncio.Semaphore(concurrency)
        
        async def scrape_with_semaphore(url: str) -> ScrapeResult:
            async with semaphore:
                return await self.scrape(url, **kwargs)
        
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
