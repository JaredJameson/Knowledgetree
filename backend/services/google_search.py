"""
KnowledgeTree - Google Search Service
Google Custom Search API integration for URL discovery
"""

import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

import httpx


class GoogleSearchService:
    """
    Service for Google Custom Search API integration
    
    Enables automated URL discovery for research workflows.
    Requires Google Custom Search API key and Search Engine ID.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        search_engine_id: Optional[str] = None
    ):
        """
        Initialize Google Search service
        
        Args:
            api_key: Google API key (defaults to GOOGLE_API_KEY env var)
            search_engine_id: Custom Search Engine ID (defaults to GOOGLE_CSE_ID env var)
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.search_engine_id = search_engine_id or os.getenv("GOOGLE_CSE_ID")
        self.client = httpx.AsyncClient(timeout=30.0)
    
    @property
    def is_configured(self) -> bool:
        """Check if Google Search API is properly configured"""
        return bool(self.api_key and self.search_engine_id)
    
    async def search(
        self,
        query: str,
        num_results: int = 20,
        date_range: str = "any",
        language: str = "en",
        sort_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute Google Custom Search
        
        Args:
            query: Search query
            num_results: Number of results (1-100, limited by API tier)
            date_range: Date filter (day, week, month, year, any)
            language: Language code (e.g., en, pl, de)
            sort_by: Sort order (date, relevance)
        
        Returns:
            List of search results with metadata
        """
        if not self.is_configured:
            # Return mock results if not configured
            return await self._mock_search(query, num_results)
        
        try:
            # Build request URL
            url = "https://www.googleapis.com/customsearch/v1"
            
            params = {
                "key": self.api_key,
                "cx": self.search_engine_id,
                "q": query,
                "num": min(num_results, 100),  # API limit
                "lr": language,
            }
            
            # Add date range filter
            if date_range != "any":
                params["dateRestrict"] = self._get_date_restrict(date_range)
            
            # Add sort order
            if sort_by == "date":
                params["sort"] = "date"
            
            # Execute request
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse results
            results = []
            if "items" in data:
                for item in data["items"]:
                    result = {
                        "url": item.get("link", ""),
                        "title": item.get("title", ""),
                        "snippet": item.get("snippet", ""),
                        "relevance_score": self._calculate_relevance(item, query),
                        "source": "google_search",
                        "date": item.get("pagemap", {}).get("metatags", [{}])[0].get("article:published_time"),
                        "cache_id": item.get("cacheId")
                    }
                    results.append(result)
            
            return results
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                # API quota exceeded or invalid credentials
                print(f"⚠️ Google Search API error: {e}")
                return await self._mock_search(query, num_results)
            else:
                raise Exception(f"Google Search API error: {e}")
        except Exception as e:
            print(f"⚠️ Google Search error: {e}")
            return await self._mock_search(query, num_results)
    
    async def _mock_search(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """
        Return mock search results when API is not configured
        
        Useful for development and testing.
        """
        mock_domains = [
            "wikipedia.org",
            "example.com",
            "docs.python.org",
            "stackoverflow.com",
            "github.com",
            "medium.com",
            "dev.to",
            "reddit.com"
        ]
        
        results = []
        for i in range(min(num_results, len(mock_domains))):
            domain = mock_domains[i % len(mock_domains)]
            results.append({
                "url": f"https://{domain}/{query.replace(' ', '-').lower()}",
                "title": f"Example result {i+1} for: {query}",
                "snippet": f"This is a mock search result for '{query}'. Configure Google API for real results.",
                "relevance_score": 0.8 - (i * 0.05),
                "source": "mock_search",
                "date": datetime.utcnow().isoformat(),
                "is_mock": True
            })
        
        return results
    
    def _get_date_restrict(self, date_range: str) -> str:
        """Convert date_range to Google API dateRestrict format"""
        mapping = {
            "day": "d1",        # Past 24 hours
            "week": "w1",       # Past week
            "month": "m1",      # Past month
            "year": "y1"        # Past year
        }
        return mapping.get(date_range, "")
    
    def _calculate_relevance(self, item: Dict, query: str) -> float:
        """
        Calculate relevance score for search result
        
        Simple heuristic based on query matching in title/snippet.
        """
        title = item.get("title", "").lower()
        snippet = item.get("snippet", "").lower()
        query_lower = query.lower()
        
        score = 0.5  # Base score
        
        # Check for exact phrase match
        if query_lower in title:
            score += 0.3
        
        if query_lower in snippet:
            score += 0.2
        
        # Check for word matches
        query_words = set(query_lower.split())
        title_words = set(title.split())
        snippet_words = set(snippet.split())
        
        if query_words & title_words:
            score += 0.1 * len(query_words & title_words) / len(query_words)
        
        if query_words & snippet_words:
            score += 0.05 * len(query_words & snippet_words) / len(query_words)
        
        return min(score, 1.0)
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# ============================================================================
# Search Query Builder
# ============================================================================

class SearchQueryBuilder:
    """
    Build effective search queries for URL discovery
    """
    
    @staticmethod
    def build_research_query(
        topic: str,
        focus_area: Optional[str] = None,
        year: Optional[int] = None,
        source_type: Optional[str] = None
    ) -> str:
        """
        Build optimized search query
        
        Args:
            topic: Main research topic
            focus_area: Specific area to focus on
            year: Filter by year
            source_type: Type of source (paper, blog, news, etc.)
        
        Returns:
            Optimized search query string
        """
        query_parts = [topic]
        
        if focus_area:
            query_parts.append(focus_area)
        
        if year:
            query_parts.append(str(year))
        
        if source_type:
            source_mapping = {
                "paper": ["scholar", "research", "paper", "study"],
                "blog": ["blog", "tutorial", "guide"],
                "news": ["news", "article", "report"],
                "documentation": ["docs", "documentation", "api", "reference"]
            }
            
            if source_type in source_mapping:
                query_parts.extend(source_mapping[source_type])
        
        return " ".join(query_parts)
    
    @staticmethod
    def build_url_discovery_query(topic: str, depth: str = "broad") -> List[str]:
        """
        Build multiple queries for comprehensive URL discovery
        
        Args:
            topic: Research topic
            depth: Query depth (broad, medium, narrow)
        
        Returns:
            List of search queries
        """
        queries = [topic]
        
        if depth == "broad":
            queries.extend([
                f"{topic} tutorial",
                f"{topic} guide",
                f"{topic} overview",
                f"what is {topic}",
                f"{topic} examples"
            ])
        elif depth == "medium":
            queries.extend([
                f"{topic} best practices",
                f"{topic} implementation",
                f"{topic} architecture",
                f"{topic} case study"
            ])
        elif depth == "narrow":
            queries.extend([
                f"{topic} advanced techniques",
                f"{topic} optimization",
                f"{topic} specific use case"
            ])
        
        return queries


# ============================================================================
# Global singleton instance
# ============================================================================

_google_search_service: Optional[GoogleSearchService] = None


def get_google_search_service() -> GoogleSearchService:
    """Get or create global Google Search service instance"""
    global _google_search_service
    if _google_search_service is None:
        _google_search_service = GoogleSearchService()
    return _google_search_service
