"""
KnowledgeTree - Intelligent Crawler Engine Selector
Automatically selects optimal crawl engine based on URL patterns and user task analysis
"""

import re
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse
from services.crawler_orchestrator import CrawlEngine
from services.claude_tool_client import AnthropicToolClient


class IntelligentCrawlerSelector:
    """
    Intelligently selects crawl engine based on:
    1. URL domain patterns (known static vs dynamic sites)
    2. User prompt analysis (task complexity, data requirements)
    3. Scoring system with confidence levels

    Decision Flow:
    - HTTP: Fast, static sites, simple extraction
    - Playwright: JavaScript-heavy, SPAs, dynamic content, interactions
    - Firecrawl: Premium quality (only if API key available)
    """

    # Known static sites that work well with HTTP
    STATIC_DOMAINS = {
        'wikipedia.org', 'docs.python.org', 'github.com', 'stackoverflow.com',
        'medium.com', 'dev.to', 'reddit.com', 'news.ycombinator.com',
        'arxiv.org', 'scholar.google.com', 'pubmed.ncbi.nlm.nih.gov'
    }

    # Known JavaScript-heavy sites requiring Playwright
    DYNAMIC_DOMAINS = {
        'twitter.com', 'x.com', 'facebook.com', 'instagram.com', 'linkedin.com',
        'youtube.com', 'tiktok.com', 'pinterest.com', 'airbnb.com', 'booking.com',
        'amazon.com', 'ebay.com', 'allegro.pl', 'olx.pl', 'otodom.pl'
    }

    # Keywords in user prompt suggesting need for Playwright
    DYNAMIC_TASK_KEYWORDS = [
        'interakcj', 'scroll', 'klik', 'dynamiczn', 'javascript', 'react', 'vue', 'angular',
        'social media', 'komentarz', 'post', 'feed', 'infinite scroll', 'lazy load',
        'interactive', 'real-time', 'live', 'aktualizacj'
    ]

    # Keywords suggesting simple extraction (HTTP sufficient)
    SIMPLE_TASK_KEYWORDS = [
        'artykuł', 'tekst', 'dokumentacj', 'tutorial', 'blog', 'newsy', 'informacj',
        'opis', 'definicj', 'wyjaśnien', 'przykład', 'kod', 'snippet', 'lista'
    ]

    # Keywords suggesting high-quality extraction need
    QUALITY_KEYWORDS = [
        'szczegółow', 'kompletny', 'dokładn', 'precyzyjn', 'wszystkie', 'każdy',
        'pełna lista', 'comprehensive', 'complete', 'exhaustive', 'detailed'
    ]

    def __init__(self, firecrawl_available: bool = False):
        """
        Args:
            firecrawl_available: Whether Firecrawl API key is configured
        """
        self.firecrawl_available = firecrawl_available
        self.claude = AnthropicToolClient()

    async def select_engine(
        self,
        urls: List[str],
        agent_prompt: str,
        use_ai_analysis: bool = True
    ) -> CrawlEngine:
        """
        Select optimal crawl engine for given URLs and task.

        Args:
            urls: List of URLs to crawl
            agent_prompt: User's extraction task description
            use_ai_analysis: Whether to use LLM for analysis (default: True)

        Returns:
            CrawlEngine: Selected engine (HTTP, PLAYWRIGHT, or FIRECRAWL)
        """
        # Quick heuristic-based decision
        heuristic_score = self._calculate_heuristic_score(urls, agent_prompt)

        # If confidence is high (>0.8), use heuristic result
        if heuristic_score['confidence'] > 0.8:
            return heuristic_score['engine']

        # Otherwise, use AI analysis for complex cases
        if use_ai_analysis:
            ai_decision = await self._ai_analysis(urls, agent_prompt, heuristic_score)
            return ai_decision

        # Fallback to heuristic
        return heuristic_score['engine']

    def _calculate_heuristic_score(
        self,
        urls: List[str],
        agent_prompt: str
    ) -> Dict[str, Any]:
        """
        Fast heuristic-based scoring without LLM.

        Returns:
            {
                'engine': CrawlEngine,
                'confidence': float (0.0-1.0),
                'reasoning': str
            }
        """
        scores = {
            'http': 0.0,
            'playwright': 0.0,
            'firecrawl': 0.0
        }

        reasons = []

        # 1. URL Domain Analysis (40% weight)
        for url in urls:
            domain = self._extract_domain(url)

            if domain in self.STATIC_DOMAINS:
                scores['http'] += 0.4
                reasons.append(f"Known static domain: {domain}")
            elif domain in self.DYNAMIC_DOMAINS:
                scores['playwright'] += 0.4
                reasons.append(f"Known dynamic domain: {domain}")
            else:
                # Unknown domain - neutral, slight preference for HTTP (faster)
                scores['http'] += 0.15
                scores['playwright'] += 0.1

        # 2. Prompt Keyword Analysis (40% weight)
        prompt_lower = agent_prompt.lower()

        # Check for dynamic/complex task indicators
        dynamic_matches = sum(1 for kw in self.DYNAMIC_TASK_KEYWORDS if kw in prompt_lower)
        if dynamic_matches > 0:
            scores['playwright'] += 0.2 * min(dynamic_matches, 2)
            reasons.append(f"Dynamic task keywords detected: {dynamic_matches}")

        # Check for simple extraction indicators
        simple_matches = sum(1 for kw in self.SIMPLE_TASK_KEYWORDS if kw in prompt_lower)
        if simple_matches > 0:
            scores['http'] += 0.2 * min(simple_matches, 2)
            reasons.append(f"Simple extraction keywords detected: {simple_matches}")

        # Check for high-quality requirements
        quality_matches = sum(1 for kw in self.QUALITY_KEYWORDS if kw in prompt_lower)
        if quality_matches > 0 and self.firecrawl_available:
            scores['firecrawl'] += 0.15 * min(quality_matches, 2)
            reasons.append(f"High quality requirements detected: {quality_matches}")

        # 3. URL Structure Analysis (20% weight)
        for url in urls:
            # Check for API endpoints or structured data
            if '/api/' in url or '.json' in url or '.xml' in url:
                scores['http'] += 0.2
                reasons.append("API/structured endpoint detected")

            # Check for complex query parameters (suggests dynamic content)
            if url.count('?') > 0 and url.count('&') > 2:
                scores['playwright'] += 0.1
                reasons.append("Complex query parameters detected")

        # Select engine with highest score
        selected_engine = max(scores.items(), key=lambda x: x[1])
        engine_name = selected_engine[0]
        confidence = selected_engine[1]

        # Map to enum
        engine_map = {
            'http': CrawlEngine.HTTP,
            'playwright': CrawlEngine.PLAYWRIGHT,
            'firecrawl': CrawlEngine.FIRECRAWL if self.firecrawl_available else CrawlEngine.PLAYWRIGHT
        }

        return {
            'engine': engine_map[engine_name],
            'confidence': min(confidence, 1.0),
            'reasoning': ' | '.join(reasons),
            'scores': scores
        }

    async def _ai_analysis(
        self,
        urls: List[str],
        agent_prompt: str,
        heuristic_result: Dict[str, Any]
    ) -> CrawlEngine:
        """
        Use LLM to analyze complex cases where heuristics are uncertain.

        Args:
            urls: Target URLs
            agent_prompt: User's task description
            heuristic_result: Result from heuristic analysis

        Returns:
            CrawlEngine: LLM-recommended engine
        """
        system_prompt = f"""You are a web scraping expert selecting the optimal crawl engine.

Available engines:
1. HTTP - Fast, lightweight, for static HTML sites, simple extraction
2. PLAYWRIGHT - Slower, for JavaScript-heavy sites, SPAs, dynamic content, requires browser automation
3. FIRECRAWL - Premium, highest quality (only if available: {self.firecrawl_available})

Heuristic analysis:
- Suggested engine: {heuristic_result['engine'].value}
- Confidence: {heuristic_result['confidence']:.2f}
- Reasoning: {heuristic_result['reasoning']}
- Scores: {heuristic_result['scores']}

Your task: Analyze the user's extraction task and target URLs, then recommend the BEST engine.

Return JSON:
{{
    "engine": "HTTP" | "PLAYWRIGHT" | "FIRECRAWL",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation in Polish"
}}"""

        user_input = f"""URLs: {', '.join(urls)}

User task (in Polish):
{agent_prompt}

Which engine should be used?"""

        try:
            response = await self.claude.execute_simple(
                prompt=user_input,
                system_prompt=system_prompt,
                model="claude-sonnet-4-20250514"
            )

            import json
            result = json.loads(response)
            engine_str = result.get('engine', 'HTTP').upper()

            # Map string to enum
            engine_map = {
                'HTTP': CrawlEngine.HTTP,
                'PLAYWRIGHT': CrawlEngine.PLAYWRIGHT,
                'FIRECRAWL': CrawlEngine.FIRECRAWL if self.firecrawl_available else CrawlEngine.PLAYWRIGHT
            }

            return engine_map.get(engine_str, CrawlEngine.HTTP)

        except Exception as e:
            # Fallback to heuristic result on error
            print(f"AI analysis failed: {e}, using heuristic result")
            return heuristic_result['engine']

    def _extract_domain(self, url: str) -> str:
        """Extract clean domain from URL."""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Remove www. prefix
        domain = re.sub(r'^www\.', '', domain)
        return domain

    def explain_selection(
        self,
        engine: CrawlEngine,
        heuristic_result: Dict[str, Any]
    ) -> str:
        """
        Generate human-readable explanation of engine selection.

        Args:
            engine: Selected engine
            heuristic_result: Heuristic analysis result

        Returns:
            Polish explanation string
        """
        explanations = {
            CrawlEngine.HTTP: "HTTP (szybki): Idealny dla statycznych stron, blogów, dokumentacji. Najszybszy i najtańszy.",
            CrawlEngine.PLAYWRIGHT: "Playwright (przeglądarka): Potrzebny dla stron z JavaScript, SPA, dynamicznej treści. Wolniejszy ale potężniejszy.",
            CrawlEngine.FIRECRAWL: "Firecrawl (premium): Najwyższa jakość ekstrakcji, idealne dla złożonych witryn wymagających doskonałych rezultatów."
        }

        base_explanation = explanations.get(engine, "Unknown engine")

        return f"""🔍 Wybrano engine: {engine.value}

{base_explanation}

Analiza heurystyczna:
- Pewność: {heuristic_result['confidence']:.0%}
- Powody: {heuristic_result['reasoning']}
- Wyniki punktacji: HTTP={heuristic_result['scores']['http']:.2f}, Playwright={heuristic_result['scores']['playwright']:.2f}, Firecrawl={heuristic_result['scores']['firecrawl']:.2f}
"""
