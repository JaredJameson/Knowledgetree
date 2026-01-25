"""
KnowledgeTree - Playwright Scraper Service
Browser-based scraper for JavaScript-heavy pages (15% of use cases)
"""

import logging
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

logger = logging.getLogger(__name__)


class PlaywrightScraper:
    """
    Browser-based scraper using Playwright.
    
    Use for:
    - React/Vue/Angular SPA applications
    - Pages with dynamic content (infinite scroll, lazy loading)
    - Sites requiring user interaction (click, scroll)
    - Pages with heavy JavaScript rendering
    
    Performance: 10-50 pages/second
    Cost: $0 (CPU/memory intensive)
    """
    
    def __init__(
        self,
        headless: bool = True,
        timeout: float = 30000,
        user_data_dir: Optional[str] = None
    ):
        self.headless = headless
        self.timeout = timeout
        self.user_data_dir = user_data_dir
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
    
    async def _get_browser_context(self) -> BrowserContext:
        """Get or create browser context."""
        if self._context is None:
            playwright = await async_playwright().start()
            
            # Launch browser
            self._browser = await playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            # Create context with stealth settings
            self._context = await self._browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=(
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/122.0.0.0 Safari/537.36'
                ),
                locale='en-US',
                timezone_id='America/New_York'
            )
            
            # Add stealth scripts to avoid detection
            await self._context.add_init_script("""
                // Remove webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Mock plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                // Mock languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            """)
        
        return self._context
    
    async def scrape(
        self,
        url: str,
        wait_for_selector: Optional[str] = None,
        wait_for_timeout: int = 5000,
        screenshot: bool = False,
        extract_links: bool = False
    ) -> Dict[str, Any]:
        """
        Scrape a URL using Playwright.
        
        Args:
            url: URL to scrape
            wait_for_selector: CSS selector to wait for before scraping
            wait_for_timeout: Max time to wait for selector (ms)
            screenshot: Take screenshot of the page
            extract_links: Extract all links from the page
            
        Returns:
            Dict with scraped data
        """
        context = await self._get_browser_context()
        page = await context.new_page()
        
        try:
            logger.info(f"Scraping with Playwright: {url}")
            
            # Navigate to URL
            await page.goto(url, wait_until='networkidle', timeout=self.timeout)
            
            # Wait for specific selector if provided
            if wait_for_selector:
                try:
                    await page.wait_for_selector(
                        wait_for_selector,
                        timeout=wait_for_timeout
                    )
                except Exception as e:
                    logger.warning(f"Selector {wait_for_selector} not found: {e}")
            
            # Wait a bit for dynamic content
            await page.wait_for_timeout(2000)
            
            # Get page content
            title = await page.title()
            content = await page.content()
            
            # Get plain text
            text = await page.evaluate('() => document.body.innerText')
            
            # Get accessibility snapshot (useful for MCP)
            accessibility_tree = await page.accessibility.snapshot()
            
            result = {
                "url": page.url,
                "title": title,
                "content": content,
                "text": text,
                "accessibility_tree": accessibility_tree,
                "metadata": {
                    "engine": "playwright",
                    "headless": self.headless
                }
            }
            
            # Extract links if requested
            if extract_links:
                result["links"] = await self._extract_links(page)
            
            # Take screenshot if requested
            if screenshot:
                screenshot_bytes = await page.screenshot(full_page=True)
                result["screenshot"] = screenshot_bytes.hex()
            
            logger.info(f"Successfully scraped {url} with Playwright ({len(text)} chars)")
            return result
            
        except Exception as e:
            logger.error(f"Error scraping {url} with Playwright: {e}")
            raise
        finally:
            await page.close()
    
    async def _extract_links(self, page: Page) -> list[Dict[str, str]]:
        """Extract all links from the page."""
        links = await page.evaluate('''() => {
            const links = [];
            document.querySelectorAll('a[href]').forEach(a => {
                links.push({
                    url: a.href,
                    text: a.textContent.trim()
                });
            });
            return links;
        }''')
        return links
    
    async def scrape_with_interaction(
        self,
        url: str,
        actions: list[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Scrape a URL with custom interactions.
        
        Actions format:
        [
            {"type": "click", "selector": "#load-more"},
            {"type": "scroll", "direction": "down", "amount": 500},
            {"type": "wait", "timeout": 2000},
            {"type": "fill", "selector": "#search", "value": "query"}
        ]
        """
        context = await self._get_browser_context()
        page = await context.new_page()
        
        try:
            logger.info(f"Scraping with interactions: {url}")
            
            await page.goto(url, wait_until='networkidle', timeout=self.timeout)
            
            # Execute actions
            for action in actions:
                action_type = action.get("type")
                
                if action_type == "click":
                    await page.click(action["selector"])
                elif action_type == "scroll":
                    if action.get("direction") == "down":
                        await page.evaluate(f'window.scrollBy(0, {action.get("amount", 500)})')
                    else:
                        await page.evaluate(f'window.scrollBy(0, -{action.get("amount", 500)})')
                elif action_type == "wait":
                    await page.wait_for_timeout(action.get("timeout", 1000))
                elif action_type == "fill":
                    await page.fill(action["selector"], action["value"])
                elif action_type == "hover":
                    await page.hover(action["selector"])
                
                # Wait a bit after each action
                await page.wait_for_timeout(500)
            
            # Get final content
            title = await page.title()
            content = await page.content()
            text = await page.evaluate('() => document.body.innerText')
            
            return {
                "url": page.url,
                "title": title,
                "content": content,
                "text": text,
                "metadata": {
                    "engine": "playwright",
                    "actions_executed": len(actions)
                }
            }
            
        finally:
            await page.close()
    
    async def close(self):
        """Close browser and cleanup resources."""
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
