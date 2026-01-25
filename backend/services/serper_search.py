"""
KnowledgeTree - Serper.dev Search Service
Google Search API integration for finding URLs to crawl
"""

import httpx
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from core.config import settings


@dataclass
class SearchResult:
    """Single search result from Serper.dev"""
    title: str
    link: str
    snippet: str
    position: int


@dataclass
class SearchResponse:
    """Complete search response"""
    query: str
    total_results: int
    results: List[SearchResult]
    related_searches: List[str]


class SerperSearchService:
    """
    Serper.dev Google Search API client

    Use cases:
    - Find URLs to crawl based on keywords
    - Discover related content
    - Research topics before crawling

    Pricing (2025):
    - Free: 100 searches/month
    - Starter: $5/month - 2,500 searches
    - Pro: $50/month - 25,000 searches

    Website: https://serper.dev
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: str = "https://google.serper.dev/search"
    ):
        self.api_key = api_key or settings.SERPER_API_KEY
        self.api_url = api_url

        if not self.api_key:
            print("Warning: SERPER_API_KEY not set. Serper.dev features will be disabled.")

    async def search(
        self,
        query: str,
        num_results: int = 10,
        country: str = "pl",
        language: str = "lang_pl",
        type: str = "search"  # search, images, news
    ) -> SearchResponse:
        """
        Perform Google search via Serper.dev API

        Args:
            query: Search query
            num_results: Number of results to return (max 100)
            country: Country code (pl, us, uk, de, fr)
            language: Language code (lang_pl, lang_en, lang_de)
            type: Search type (search, images, news)

        Returns:
            SearchResponse with results
        """
        if not self.api_key:
            return SearchResponse(
                query=query,
                total_results=0,
                results=[],
                related_searches=[]
            )

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                params = {
                    "q": query,
                    "apiKey": self.api_key,
                    "num": min(num_results, 100),
                    "gl": country,
                    "hl": language,
                }

                # Add type parameter if not default search
                if type != "search":
                    params["type"] = type

                response = await client.get(self.api_url, params=params, timeout=30.0)

                if response.status_code == 401:
                    raise Exception("Invalid Serper.dev API key")

                if response.status_code == 403:
                    raise Exception("Serper.dev quota exceeded")

                if response.status_code == 429:
                    raise Exception("Too many requests. Rate limited.")

                response.raise_for_status()
                data = response.json()

                # Parse results
                results = []
                organic_results = data.get("organic", [])

                for idx, item in enumerate(organic_results[:num_results]):
                    results.append(SearchResult(
                        title=item.get("title", ""),
                        link=item.get("link", ""),
                        snippet=item.get("snippet", ""),
                        position=idx + 1
                    ))

                # Extract related searches
                related_searches = []
                for people_also_search in data.get("peopleAlsoAsk", []):
                    question = people_also_search.get("question", "")
                    if question:
                        related_searches.append(question)

                return SearchResponse(
                    query=query,
                    total_results=len(results),
                    results=results,
                    related_searches=related_searches
                )

        except httpx.HTTPStatusError as e:
            raise Exception(f"Serper.dev HTTP error: {e.response.status_code}")
        except httpx.TimeoutException:
            raise Exception("Serper.dev request timeout")
        except Exception as e:
            raise Exception(f"Serper.dev search failed: {str(e)}")

    async def find_urls(
        self,
        query: str,
        num_results: int = 10,
        domain_filter: Optional[str] = None
    ) -> List[str]:
        """
        Quick search to find URLs (simplified interface)

        Args:
            query: Search query
            num_results: Number of URLs to return
            domain_filter: Only return results from this domain (optional)

        Returns:
            List of URLs
        """
        response = await self.search(query, num_results=num_results)

        urls = [result.link for result in response.results]

        # Apply domain filter if specified
        if domain_filter:
            urls = [url for url in urls if domain_filter in url]

        return urls


# Global instance
serper_search = SerperSearchService()
