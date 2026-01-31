"""
Agentic Browser - Autonomous Web Browsing with AI Decision Making

This module implements a truly intelligent web browsing agent that:
1. OBSERVES: Uses Playwright to see the page (DOM snapshot or screenshot)
2. THINKS: Uses LLM (Claude) to analyze and decide next action
3. ACTS: Executes decisions (navigate, extract content, click, scroll)
4. REPEATS: Continues until goal is achieved

Unlike traditional scrapers that blindly follow links, this agent:
- Understands user intent
- Makes intelligent navigation decisions
- Extracts only relevant content
- Adapts to page structure dynamically
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from urllib.parse import urljoin, urlparse

import anthropic
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from services.playwright_scraper import PlaywrightScraper

logger = logging.getLogger(__name__)


@dataclass
class PageState:
    """Represents the current state of a web page"""
    url: str
    title: str
    text_content: str  # First 3000 chars of main content
    links: List[str]  # All available links
    link_texts: Dict[str, str]  # url -> link text mapping
    html_structure: str  # Simplified DOM structure
    screenshot: Optional[bytes] = None  # Full-page screenshot for vision
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class BrowsingDecision:
    """Represents an AI-made decision about next action"""
    action: str  # "extract", "navigate", "extract_and_navigate", "done"
    reasoning: str  # Why this decision
    target_urls: List[str] = field(default_factory=list)  # URLs to visit next
    content_extracted: bool = False
    confidence: float = 1.0


@dataclass
class ExtractedContent:
    """Content extracted from a page"""
    url: str
    title: str
    main_content: str
    structured_data: Dict[str, Any]  # Entities, insights, metadata
    extraction_method: str = "agentic_llm"
    timestamp: datetime = field(default_factory=datetime.utcnow)


class AgenticBrowser:
    """
    Autonomous web browsing agent with AI decision-making.

    The agent follows an observe-think-act loop:
    1. Navigate to URL (or start URL)
    2. Observe page state (Playwright snapshot)
    3. Think: Ask LLM "what should I do next?"
    4. Act: Execute LLM's decision
    5. Repeat until goal achieved or limits reached
    """

    def __init__(
        self,
        anthropic_api_key: str,
        max_pages: int = 20,
        max_depth: int = 3,
        headless: bool = True
    ):
        """
        Initialize agentic browser.

        Args:
            anthropic_api_key: Claude API key
            max_pages: Maximum pages to visit
            max_depth: Maximum navigation depth from start URL
            headless: Run Playwright in headless mode
        """
        self.anthropic_client = anthropic.AsyncAnthropic(api_key=anthropic_api_key)
        self.playwright_scraper = PlaywrightScraper(headless=headless)

        self.max_pages = max_pages
        self.max_depth = max_depth

        # State tracking
        self.visited_urls: Set[str] = set()
        self.extracted_content: List[ExtractedContent] = []
        self.navigation_history: List[tuple] = []  # (url, depth, timestamp)
        
        # Vision usage tracking (for cost optimization)
        self.pages_with_vision: int = 0
        self.pages_without_vision: int = 0
        self.user_intent_requires_vision: bool = False  # (url, depth, timestamp)

    def _analyze_user_intent(self, user_prompt: str) -> bool:
        """
        Analyze user intent to determine if vision capabilities are needed.
        
        This is PHASE 1 of hybrid decision: user intent analysis.
        
        Args:
            user_prompt: User's natural language prompt
            
        Returns:
            True if user intent suggests need for visual analysis
            
        Examples:
            ✅ "Wyciągnij dane z wykresów" → True
            ✅ "Extract data from charts and tables" → True
            ✅ "Analyze diagrams and visualizations" → True
            ❌ "Wyciągnij listę artykułów" → False
            ❌ "Get all blog post titles" → False
        """
        # Vision keywords in Polish and English
        vision_keywords = [
            # Polish
            "wykres", "wykresy", "graf", "grafy", "diagram", "diagramy",
            "tabela", "tabele", "wizualizacja", "wizualizacje",
            "infografika", "infografiki", "obrazek", "obrazki",
            "screenshot", "screenshoty", "dane wizualne", "visual",
            "chart", "charts", "graph", "graphs", "table", "tables",
            "visualization", "visualizations", "infographic", "infographics",
            # Context clues
            "metryki", "metrics", "performance data", "dane wydajnościowe",
            "porównanie", "comparison", "benchmark", "architecture",
            "architektura", "flow", "przepływ", "proces", "process"
        ]
        
        prompt_lower = user_prompt.lower()
        return any(keyword in prompt_lower for keyword in vision_keywords)

    def _should_use_vision(
        self,
        page_url: str,
        has_visual_elements: bool,
        visual_element_count: int
    ) -> bool:
        """
        Hybrid decision logic combining multiple factors to optimize vision usage.
        
        This is PHASE 2 of hybrid decision: intelligent optimization.
        
        Decision Factors:
        1. User Intent: Does user prompt suggest need for visual analysis?
        2. Page Content: Does page actually contain visual elements worth analyzing?
        3. Page Type: Is this a content page or navigation/listing page?
        4. Cost Optimization: Stay within ~30% vision usage quota
        
        Args:
            page_url: Current page URL
            has_visual_elements: Whether page has charts/tables/diagrams
            visual_element_count: Number of visual elements detected
            
        Returns:
            True if vision should be used for this page
            
        Optimization Strategy:
        - Always use vision if: user wants it AND page has visual elements
        - Never use vision if: user doesn't want it OR no visual elements
        - Smart quota: Limit vision to ~30% of pages to control costs
        """
        # Factor 1: User Intent (cached from prompt analysis)
        user_wants_vision = self.user_intent_requires_vision
        
        # Factor 2: Page Content Detection
        page_has_visual_content = has_visual_elements and visual_element_count > 0
        
        # Factor 3: Page Type Classification
        # Skip vision for navigation/listing pages (optimize for content pages)
        is_likely_content_page = any(indicator in page_url.lower() for indicator in [
            "/article", "/post", "/blog", "/news", "/doc", "/guide", 
            "/tutorial", "/research", "/paper", "/engineering"
        ])
        
        # Factor 4: Cost Optimization (30% vision quota)
        total_pages = self.pages_with_vision + self.pages_without_vision
        vision_ratio = self.pages_with_vision / max(total_pages, 1)
        quota_available = vision_ratio < 0.30  # Stay under 30% usage
        
        # DECISION LOGIC (Hybrid Intelligence)
        
        # Case 1: User explicitly wants visual analysis + page has visual content
        # → Use vision (highest priority)
        if user_wants_vision and page_has_visual_content:
            # But respect quota to prevent runaway costs
            if not quota_available:
                # Log warning but allow critical pages
                if visual_element_count >= 3:  # High visual density
                    logger.warning(
                        f"Vision quota exceeded ({vision_ratio:.1%}) but using vision "
                        f"for high-density page ({visual_element_count} elements)"
                    )
                    return True
                else:
                    logger.info(
                        f"Vision quota exceeded ({vision_ratio:.1%}), skipping page "
                        f"with {visual_element_count} visual elements"
                    )
                    return False
            return True
        
        # Case 2: User wants vision but page has NO visual content
        # → Don't waste resources
        if user_wants_vision and not page_has_visual_content:
            logger.debug(
                "User intent suggests vision but page has no visual elements, skipping"
            )
            return False
        
        # Case 3: User doesn't need vision
        # → Don't use vision (save costs)
        if not user_wants_vision:
            return False
        
        # Default: No vision
        return False

    def _extract_json_from_llm_response(self, content: str) -> dict:
        """
        Ultra-robust JSON extraction from LLM response with extensive fallback strategies.

        Handles all common LLM response formats:
        1. Markdown code blocks (```json or ```)
        2. Leading/trailing text and whitespace
        3. JSON embedded in conversational text
        4. Incomplete or malformed JSON
        5. Missing outer braces

        Args:
            content: Raw LLM response text

        Returns:
            Parsed JSON dictionary

        Raises:
            json.JSONDecodeError: If all extraction strategies fail
        """
        import re

        # STRATEGY 1: Extract from markdown code blocks
        if "```json" in content:
            try:
                json_str = content.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            except (IndexError, json.JSONDecodeError):
                pass  # Try next strategy

        if "```" in content:
            try:
                json_str = content.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
            except (IndexError, json.JSONDecodeError):
                pass  # Try next strategy

        # STRATEGY 2: Find FIRST { and LAST } - most aggressive
        # This handles JSON embedded anywhere in text
        first_brace = content.find('{')
        last_brace = content.rfind('}')

        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            try:
                json_str = content[first_brace:last_brace + 1]
                # Clean common formatting issues
                json_str = json_str.strip()
                # Remove trailing commas before closing braces/brackets
                json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass  # Try next strategy

        # STRATEGY 3: Regex for complete JSON object (non-greedy for nested)
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content)
        if json_match:
            try:
                json_str = json_match.group(0).strip()
                json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass  # Try next strategy

        # STRATEGY 4: Greedy regex (DOTALL for multiline)
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                json_str = json_match.group(0).strip()
                json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass  # Try next strategy

        # STRATEGY 5: Try parsing entire content (after aggressive cleaning)
        try:
            content = content.strip()
            # Remove common conversational prefixes
            content = re.sub(r'^(Here\'s|Here is|My decision|Decision):\s*', '', content, flags=re.IGNORECASE)
            return json.loads(content)
        except json.JSONDecodeError:
            pass  # Final failure

        # If all strategies failed, raise with helpful message
        raise json.JSONDecodeError(
            f"Failed to extract valid JSON from LLM response. "
            f"Content preview: {content[:300]}...",
            content,
            0
        )

    async def browse_with_intent(
        self,
        start_url: str,
        user_intent: str,
        db: Optional[AsyncSession] = None,
        workflow_id: Optional[int] = None,
        progress_callback: Optional[callable] = None
    ) -> List[ExtractedContent]:
        """
        Autonomously browse starting from start_url to fulfill user_intent.

        Args:
            start_url: Initial URL to start browsing
            user_intent: Natural language description of what to extract
                        Example: "wyciągnij wszystkie artykuły i ich treści"
            db: Database session for logging
            workflow_id: Workflow ID for progress tracking
            progress_callback: Optional callback for progress updates

        Returns:
            List of ExtractedContent from visited pages
        """
        logger.info(
            f"🤖 Agentic Browser: Starting with intent '{user_intent[:50]}...' "
            f"from {start_url}"
        )

        # PHASE 0: ANALYZE USER INTENT (Hybrid Vision Intelligence)
        # Determine if user prompt suggests need for visual analysis
        self.user_intent_requires_vision = self._analyze_user_intent(user_intent)

        if self.user_intent_requires_vision:
            logger.info(
                "🎨 Vision capabilities ENABLED: User intent suggests need for "
                "visual element analysis (charts, tables, diagrams)"
            )
        else:
            logger.info(
                "📝 Vision capabilities DISABLED: User intent focuses on text content, "
                "vision analysis not needed (cost optimization)"
            )

        # Initialize browsing queue: (url, depth, parent_url)
        queue = [(start_url, 0, None)]
        pages_visited = 0

        while queue and pages_visited < self.max_pages:
            url, depth, parent_url = queue.pop(0)

            # Skip if already visited or too deep
            if url in self.visited_urls or depth > self.max_depth:
                continue

            logger.info(f"🌐 Visiting [{pages_visited + 1}/{self.max_pages}]: {url} (depth={depth})")

            try:
                # PHASE 1: OBSERVE - Get page state
                page_state = await self._observe_page(url)

                if progress_callback:
                    await progress_callback(
                        status="observing",
                        url=url,
                        pages_visited=pages_visited + 1,
                        pages_total=self.max_pages
                    )

                # PHASE 2: THINK - LLM decides what to do
                decision = await self._decide_action(
                    page_state=page_state,
                    user_intent=user_intent,
                    depth=depth,
                    pages_visited=pages_visited
                )

                logger.info(
                    f"🧠 Decision: {decision.action} - {decision.reasoning[:100]}"
                )

                if progress_callback:
                    await progress_callback(
                        status="thinking",
                        url=url,
                        decision=decision.action,
                        reasoning=decision.reasoning[:100]
                    )

                # PHASE 3: ACT - Execute decision
                if decision.action in ["extract", "extract_and_navigate"]:
                    extracted = await self._extract_content(
                        page_state=page_state,
                        user_intent=user_intent
                    )
                    self.extracted_content.append(extracted)

                    logger.info(
                        f"📄 Extracted content from {url}: "
                        f"{len(extracted.main_content)} chars, "
                        f"{len(extracted.structured_data.get('entities', []))} entities"
                    )

                    if progress_callback:
                        await progress_callback(
                            status="extracted",
                            url=url,
                            content_length=len(extracted.main_content)
                        )

                if decision.action in ["navigate", "extract_and_navigate"]:
                    # Add discovered URLs to queue
                    for target_url in decision.target_urls[:5]:  # Limit per page
                        if target_url not in self.visited_urls:
                            queue.append((target_url, depth + 1, url))
                            logger.info(f"➕ Added to queue: {target_url}")

                if decision.action == "done":
                    logger.info("✅ Agent decided task is complete")
                    break

                # Mark as visited
                self.visited_urls.add(url)
                self.navigation_history.append((url, depth, datetime.utcnow()))
                pages_visited += 1

                # Small delay to be respectful
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"❌ Error processing {url}: {e}")
                continue

        # Calculate vision usage statistics
        total_pages = self.pages_with_vision + self.pages_without_vision
        vision_percentage = (self.pages_with_vision / max(total_pages, 1)) * 100

        logger.info(
            f"🏁 Agentic browsing complete: "
            f"{pages_visited} pages visited, "
            f"{len(self.extracted_content)} content items extracted"
        )

        logger.info(
            f"📊 Vision Usage Stats: "
            f"{self.pages_with_vision}/{total_pages} pages used vision ({vision_percentage:.1f}%), "
            f"{self.pages_without_vision} pages skipped vision (cost optimization)"
        )

        return self.extracted_content

    async def _observe_page(self, url: str) -> PageState:
        """
        Observe page state using Playwright with intelligent vision decision.

        This implements HYBRID VISION INTELLIGENCE:
        1. Analyze page URL patterns (heuristic)
        2. Scrape page and detect visual elements
        3. Decide whether screenshot was useful (post-hoc validation)
        4. Update metrics for cost tracking

        Args:
            url: URL to observe

        Returns:
            PageState with page information (and optional screenshot)
        """
        # HEURISTIC: Predict if this page likely needs vision
        # Based on URL patterns (content pages vs navigation pages)
        is_likely_content_page = any(indicator in url.lower() for indicator in [
            "/article", "/post", "/blog", "/news", "/doc", "/guide",
            "/tutorial", "/research", "/paper", "/engineering", "/technology"
        ])
        
        # DECISION: Capture screenshot if user wants vision AND likely content page
        # This is a heuristic - we'll validate post-scrape
        should_capture = self.user_intent_requires_vision and is_likely_content_page
        
        # Scrape with Playwright (conditional screenshot capture)
        scrape_result = await self.playwright_scraper.scrape(
            url=url,
            extract_links=True,
            extract_images=False,
            capture_screenshot=should_capture  # Intelligent decision
        )

        if scrape_result.error:
            raise ValueError(f"Failed to observe page: {scrape_result.error}")

        # POST-SCRAPE VALIDATION: Was screenshot actually useful?
        # Now we have actual page content data to validate decision
        if should_capture and scrape_result.screenshot:
            # We captured screenshot - was it worth it?
            if scrape_result.has_visual_elements:
                # Good decision! Page has visual content
                self.pages_with_vision += 1
                logger.info(
                    f"✅ Vision used: {scrape_result.visual_element_count} "
                    f"visual elements detected on {url}"
                )
            else:
                # False positive - wasted resources
                self.pages_with_vision += 1  # Still count it
                logger.warning(
                    f"⚠️ Vision wasted: No visual elements found on {url}, "
                    f"but screenshot was captured (heuristic false positive)"
                )
        else:
            # No screenshot captured
            self.pages_without_vision += 1
            if scrape_result.has_visual_elements and self.user_intent_requires_vision:
                # Missed opportunity - page has visual content but we skipped it
                logger.warning(
                    f"⚠️ Vision missed: {scrape_result.visual_element_count} "
                    f"visual elements on {url}, but no screenshot (URL heuristic failed)"
                )

        # Build link text mapping (for LLM context)
        link_texts = {}
        for link in scrape_result.links[:50]:  # Limit for LLM
            link_texts[link] = link  # Could extract anchor text with JS

        # Create simplified HTML structure representation
        html_structure = (
            f"Title: {scrape_result.title}\n"
            f"Links: {len(scrape_result.links)}\n"
            f"Content: {len(scrape_result.text)} chars\n"
            f"Visual Elements: {scrape_result.visual_element_count} "
            f"({'charts/tables/diagrams' if scrape_result.has_visual_elements else 'none'})"
        )

        return PageState(
            url=scrape_result.url,
            title=scrape_result.title or "",
            text_content=scrape_result.text[:3000],  # First 3K chars
            links=scrape_result.links[:50],  # Limit for LLM
            link_texts=link_texts,
            html_structure=html_structure,
            screenshot=scrape_result.screenshot  # May be None if vision not used
        )

    async def _decide_action(
        self,
        page_state: PageState,
        user_intent: str,
        depth: int,
        pages_visited: int
    ) -> BrowsingDecision:
        """
        Use LLM to decide next action based on page state.

        Args:
            page_state: Current page state
            user_intent: User's extraction goal
            depth: Current navigation depth
            pages_visited: Number of pages visited so far

        Returns:
            BrowsingDecision with action and reasoning
        """
        # Prepare context for LLM
        system_prompt = """You are an autonomous web browsing agent. Your task is to help extract information from websites according to user intent.

You observe web pages and decide what to do next to fulfill the user's goal.

Available actions:
1. "extract" - Extract content from current page (it's relevant to user intent)
2. "navigate" - Navigate to other pages (current page has links to relevant content)
3. "extract_and_navigate" - Both extract current page AND navigate to more pages
4. "done" - Task is complete, no more pages needed

Return your decision as JSON:
{{
    "action": "extract" | "navigate" | "extract_and_navigate" | "done",
    "reasoning": "Brief explanation of why this action",
    "target_urls": ["url1", "url2", ...],  // URLs to visit next (if navigate/extract_and_navigate)
    "confidence": 0.9  // Your confidence in this decision (0-1)
}}

Decision guidelines:
- Prioritize content extraction over navigation
- If page contains target content → extract
- If page has links to target content → navigate
- Choose URLs that match user intent based on link text/URL patterns
- Avoid navigation links (about, contact, privacy, etc.)
- Stop when you've gathered sufficient content for user intent
- Max depth from start: {max_depth}
- Pages visited so far: {pages_visited}/{max_pages}"""

        user_message = f"""USER INTENT: {user_intent}

CURRENT PAGE:
URL: {page_state.url}
Title: {page_state.title}
Depth: {depth}/{self.max_depth}

CONTENT PREVIEW (first 1000 chars):
{page_state.text_content[:1000]}

AVAILABLE LINKS ({len(page_state.links)} total):
{self._format_links_for_llm(page_state.links[:20])}

VISITED PAGES: {len(self.visited_urls)}
EXTRACTED CONTENT ITEMS: {len(self.extracted_content)}

Decide the next action to fulfill user intent. Return JSON only."""

        try:
            # Build message content (text + optional screenshot for vision)
            message_content = []

            # Add screenshot if available (for visual analysis)
            if page_state.screenshot:
                import base64
                message_content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": base64.b64encode(page_state.screenshot).decode('utf-8')
                    }
                })
                # Add note about visual content
                user_message = "VISUAL CONTENT: See screenshot above for charts, diagrams, tables, and visual elements.\n\n" + user_message

            # Add text message
            message_content.append({
                "type": "text",
                "text": user_message
            })

            # CRITICAL: Debug BEFORE API call to _make_decision
            logger.info(f"🔍 DECISION PRE-API: About to call Anthropic API for decision...")
            logger.info(f"🔍 DECISION PRE-API: Message content items: {len(message_content)}")
            
            response = await self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                temperature=0,
                system=system_prompt.format(
                    max_depth=self.max_depth,
                    pages_visited=pages_visited,
                    max_pages=self.max_pages
                ),
                messages=[{"role": "user", "content": message_content}]
            )
            
            # CRITICAL: API call completed successfully
            logger.info(f"🔍 DECISION POST-API: API call completed successfully!")
            
            # Debug: Log response structure
            logger.info(f"🔍 DEBUG: Response type: {type(response)}")
            logger.info(f"🔍 DEBUG: Response.content type: {type(response.content)}")
            logger.info(f"🔍 DEBUG: Response.content length: {len(response.content)}")
            
            # CRITICAL: Try to access response.content[0] with detailed error handling
            try:
                logger.info(f"🔍 DEBUG: Accessing response.content[0]...")
                content_block = response.content[0]
                logger.info(f"🔍 DEBUG: content_block type: {type(content_block)}")
                logger.info(f"🔍 DEBUG: content_block attributes: {dir(content_block)}")
                
                # Try to get text attribute
                logger.info(f"🔍 DEBUG: Accessing .text attribute...")
                content = content_block.text
                logger.info(f"🔍 DEBUG: Successfully got text! Length: {len(content)}")
                
            except KeyError as ke:
                logger.error(f"🚨 KeyError when accessing response: {ke}")
                logger.error(f"🚨 KeyError args: {ke.args}")
                logger.error(f"🚨 Response content: {response.content}")
                raise
            except AttributeError as ae:
                logger.error(f"🚨 AttributeError when accessing .text: {ae}")
                logger.error(f"🚨 content_block: {content_block}")
                raise
            except Exception as e:
                logger.error(f"🚨 Unexpected error accessing response: {type(e).__name__}: {e}")
                logger.error(f"🚨 Full response: {response}")
                raise

            # Ultra-aggressive debug logging
            logger.info(f"🔍 DEBUG: Raw LLM response (first 500 chars): {content[:500]}")

            try:
                decision_data = self._extract_json_from_llm_response(content)
                logger.info(f"✅ JSON extraction SUCCESS: {decision_data}")
            except Exception as extract_err:
                logger.error(f"❌ JSON extraction FAILED: {type(extract_err).__name__}: {extract_err}")
                logger.error(f"📄 Full raw content: {content}")
                raise extract_err

            return BrowsingDecision(
                action=decision_data.get("action", "done"),
                reasoning=decision_data.get("reasoning", ""),
                target_urls=decision_data.get("target_urls", []),
                confidence=decision_data.get("confidence", 1.0)
            )

        except Exception as e:
            logger.error(f"LLM decision failed: {type(e).__name__}: {e}, using fallback")

            # Fallback: extract current page, don't navigate
            return BrowsingDecision(
                action="extract",
                reasoning=f"Fallback decision due to error: {str(e)}",
                confidence=0.5
            )

    async def _extract_content(
        self,
        page_state: PageState,
        user_intent: str
    ) -> ExtractedContent:
        """
        Extract relevant content from page using LLM.

        Args:
            page_state: Page to extract from
            user_intent: User's extraction goal

        Returns:
            ExtractedContent with structured data
        """
        system_prompt = """You are an expert content extraction agent with vision capabilities. Extract relevant information from web pages according to user intent.

IMPORTANT: If a screenshot is provided, analyze visual elements like:
- Charts, graphs, and data visualizations
- Tables with numerical data
- Architecture diagrams and flow charts
- Code screenshots and terminal outputs
- Infographics and visual data representations

Return structured JSON:
{
    "title": "Main title/heading",
    "main_content": "Full extracted text content + data from visual elements",
    "entities": [
        {"type": "person/org/concept/metric/...", "value": "entity name or value", "context": "...", "source": "text|chart|table|diagram"},
        ...
    ],
    "insights": [
        {"category": "finding/trend/methodology/performance", "text": "insight description", "importance": "high/medium/low", "source": "text|visual"},
        ...
    ],
    "metadata": {
        "author": "...",
        "date": "...",
        "tags": ["tag1", "tag2"],
        "visual_elements": ["charts", "tables", "diagrams"],
        ...
    }
}

Extract ALL relevant content that matches user intent. Be thorough. Include data from BOTH text and visual elements."""

        user_message = f"""USER INTENT: {user_intent}

PAGE TO EXTRACT:
URL: {page_state.url}
Title: {page_state.title}

CONTENT:
{page_state.text_content}

Extract all relevant information according to user intent. Return JSON only."""

        try:
            # Build message content (text + optional screenshot for vision)
            message_content = []

            # Add screenshot if available (for extracting data from visual elements)
            if page_state.screenshot:
                import base64
                message_content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": base64.b64encode(page_state.screenshot).decode('utf-8')
                    }
                })
                # Add note about visual content
                user_message = "VISUAL CONTENT: See screenshot above. Extract data from charts, tables, diagrams, and other visual elements.\n\n" + user_message

            # Add text message
            message_content.append({
                "type": "text",
                "text": user_message
            })

            response = await self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                temperature=0,
                system=system_prompt,
                messages=[{"role": "user", "content": message_content}]
            )

            # Parse LLM response with robust JSON extraction
            # CRITICAL: Try to access response.content[0] with detailed error handling
            try:
                logger.info(f"🔍 EXTRACT: Accessing response.content[0]...")
                content_block = response.content[0]
                logger.info(f"🔍 EXTRACT: content_block type: {type(content_block)}")
                logger.info(f"🔍 EXTRACT: content_block attributes: {dir(content_block)}")
                
                # Try to get text attribute
                logger.info(f"🔍 EXTRACT: Accessing .text attribute...")
                content = content_block.text
                logger.info(f"🔍 EXTRACT: Successfully got text! Length: {len(content)}")
                
            except KeyError as ke:
                logger.error(f"🚨 EXTRACT KeyError: {ke}")
                logger.error(f"🚨 EXTRACT KeyError args: {ke.args}")
                logger.error(f"🚨 EXTRACT Response content: {response.content}")
                raise
            except AttributeError as ae:
                logger.error(f"🚨 EXTRACT AttributeError: {ae}")
                logger.error(f"🚨 EXTRACT content_block: {content_block}")
                raise
            except Exception as e:
                logger.error(f"🚨 EXTRACT Unexpected error: {type(e).__name__}: {e}")
                logger.error(f"🚨 EXTRACT Full response: {response}")
                raise
            
            extracted_data = self._extract_json_from_llm_response(content)

            return ExtractedContent(
                url=page_state.url,
                title=extracted_data.get("title", page_state.title),
                main_content=extracted_data.get("main_content", page_state.text_content),
                structured_data={
                    "entities": extracted_data.get("entities", []),
                    "insights": extracted_data.get("insights", []),
                    "metadata": extracted_data.get("metadata", {})
                }
            )

        except Exception as e:
            logger.error(f"Content extraction failed: {e}, using fallback")

            # Fallback: return raw page content
            return ExtractedContent(
                url=page_state.url,
                title=page_state.title,
                main_content=page_state.text_content,
                structured_data={"entities": [], "insights": [], "metadata": {}}
            )

    def _format_links_for_llm(self, links: List[str]) -> str:
        """Format links for LLM readability"""
        formatted = []
        for i, link in enumerate(links[:20], 1):
            # Show just the path for brevity
            parsed = urlparse(link)
            path = parsed.path or "/"
            formatted.append(f"{i}. {path} → {link}")

        return "\n".join(formatted)

    def get_statistics(self) -> Dict[str, Any]:
        """Get browsing statistics"""
        return {
            "pages_visited": len(self.visited_urls),
            "content_extracted": len(self.extracted_content),
            "max_depth_reached": max((depth for _, depth, _ in self.navigation_history), default=0),
            "total_content_length": sum(len(c.main_content) for c in self.extracted_content),
            "total_entities": sum(len(c.structured_data.get("entities", [])) for c in self.extracted_content),
            "total_insights": sum(len(c.structured_data.get("insights", [])) for c in self.extracted_content)
        }
