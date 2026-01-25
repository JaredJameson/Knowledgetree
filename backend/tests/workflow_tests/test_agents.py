"""
KnowledgeTree - Agent Unit Tests
Unit tests for all multi-agent system components
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import json

from services.agents import (
    ResearchAgent,
    ScraperAgent,
    AnalyzerAgent,
    OrganizerAgent,
    AgentFactory,
    get_agent
)
from models.workflow_support import URLCandidate, ResearchTask, AgentMessage


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
async def mock_db():
    """Mock database session"""
    db = AsyncMock(spec=AsyncSession)
    db.add = Mock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def sample_urls():
    """Sample URLs for testing"""
    return [
        "https://example.com/article1",
        "https://twitter.com/user/status/123",
        "https://linkedin.com/post/456",
        "https://blog.example.com/post",
        "https://amazon.com/product/123"
    ]


@pytest.fixture
def sample_scraped_data():
    """Sample scraped data for testing"""
    return [
        {
            "url": "https://example.com/article1",
            "title": "AI in Healthcare 2024",
            "text": "Artificial Intelligence is revolutionizing healthcare. Machine learning algorithms can diagnose diseases with 95% accuracy. Dr. Smith at Johns Hopkins University has developed a new system.",
            "links": ["https://example.com/related"],
            "images": [],
            "engine": "http",
            "status_code": 200,
            "error": None,
            "success": True
        },
        {
            "url": "https://blog.example.com/post",
            "title": "Future of Medicine",
            "text": "The future of medicine lies in personalized treatments. AI-powered diagnostics are becoming mainstream. Hospitals are adopting these technologies rapidly.",
            "links": [],
            "images": [],
            "engine": "http",
            "status_code": 200,
            "error": None,
            "success": True
        }
    ]


@pytest.fixture
def workflow_id():
    """Sample workflow ID"""
    return 1


# ============================================================================
# ResearchAgent Tests
# ============================================================================


class TestResearchAgent:
    """Unit tests for ResearchAgent"""

    @pytest.fixture
    def agent(self):
        return ResearchAgent()

    @pytest.mark.asyncio
    async def test_analyze_query(self, agent, mock_db, workflow_id):
        """Test query analysis functionality"""
        with patch.object(agent, 'claude') as mock_claude:
            mock_claude.execute_simple = AsyncMock(return_value=json.dumps({
                "search_queries": ["AI in healthcare", "machine learning medicine"],
                "expected_urls": 25,
                "complexity": "medium",
                "strategy": "deep",
                "reasoning": "Query requires in-depth research"
            }))

            result = await agent.analyze_query(
                mock_db, workflow_id, "AI applications in healthcare"
            )

            assert result["expected_urls"] == 25
            assert result["complexity"] == "medium"
            assert result["strategy"] == "deep"
            assert len(result["search_queries"]) == 2

    @pytest.mark.asyncio
    async def test_discover_urls(self, agent, mock_db, workflow_id):
        """Test URL discovery with Google Search"""
        with patch.object(agent, 'google_search') as mock_search:
            mock_search.search = AsyncMock(return_value=[
                {
                    "url": "https://example.com/article1",
                    "title": "AI in Healthcare",
                    "snippet": "Introduction to AI healthcare applications",
                    "relevance_score": 0.9
                },
                {
                    "url": "https://example.com/article2",
                    "title": "Machine Learning in Medicine",
                    "snippet": "ML applications in medical diagnosis",
                    "relevance_score": 0.85
                }
            ])

            candidates = await agent.discover_urls(
                mock_db, workflow_id, "AI healthcare", num_results=10
            )

            assert len(candidates) == 2
            assert candidates[0].url == "https://example.com/article1"
            assert candidates[0].relevance_score == 0.9
            assert candidates[0].source == "google_search"

    @pytest.mark.asyncio
    async def test_rank_urls(self, agent, mock_db, workflow_id):
        """Test URL ranking by relevance"""
        candidates = [
            URLCandidate(
                id=1,
                workflow_id=workflow_id,
                url="https://example.com/article1",
                title="High Quality Article",
                relevance_score=0.7
            ),
            URLCandidate(
                id=2,
                workflow_id=workflow_id,
                url="https://example.com/article2",
                title="Low Quality Article",
                relevance_score=0.4
            )
        ]

        with patch.object(agent, 'claude') as mock_claude:
            mock_claude.execute_simple = AsyncMock(return_value=json.dumps({
                "rankings": [
                    {"id": 1, "relevance_score": 0.95, "reason": "Highly relevant"},
                    {"id": 2, "relevance_score": 0.6, "reason": "Less relevant"}
                ],
                "filtered_out": []
            }))

            ranked = await agent.rank_urls(mock_db, workflow_id, candidates)

            assert len(ranked) == 2
            assert ranked[0].relevance_score >= ranked[1].relevance_score


# ============================================================================
# ScraperAgent Tests
# ============================================================================


class TestScraperAgent:
    """Unit tests for ScraperAgent"""

    @pytest.fixture
    def agent(self):
        return ScraperAgent()

    @pytest.mark.asyncio
    async def test_analyze_urls(self, agent, mock_db, workflow_id, sample_urls):
        """Test URL analysis and engine classification"""
        strategy = await agent.analyze_urls(mock_db, workflow_id, sample_urls)

        # Verify classification
        assert "http" in strategy
        assert "playwright" in strategy
        assert "firecrawl" in strategy

        # Twitter and LinkedIn should use Playwright
        assert any("twitter.com" in url for url in strategy["playwright"])
        assert any("linkedin.com" in url for url in strategy["playwright"])

        # Amazon should use Firecrawl
        assert any("amazon.com" in url for url in strategy["firecrawl"])

        # Regular URLs should use HTTP
        assert len(strategy["http"]) >= 2

    @pytest.mark.asyncio
    async def test_scrape_batch(self, agent, mock_db, workflow_id):
        """Test batch scraping functionality"""
        with patch.object(agent.orchestrator, 'batch_crawl') as mock_batch:
            # Mock crawl results
            from services.crawler_orchestrator import ScrapeResult, CrawlEngine

            mock_batch.return_value = [
                ScrapeResult(
                    url="https://example.com/article1",
                    title="Test Article",
                    content="<html>Article content here</html>",
                    text="Article content here",
                    links=[],
                    images=[],
                    engine=CrawlEngine.HTTP,
                    status_code=200,
                    error=None
                )
            ]

            results = await agent.scrape_batch(
                mock_db, workflow_id,
                ["https://example.com/article1"],
                engine=None,
                concurrency=5
            )

            assert len(results) == 1
            assert results[0]["success"] is True
            assert results[0]["title"] == "Test Article"
            assert results[0]["text"] == "Article content here"


# ============================================================================
# AnalyzerAgent Tests
# ============================================================================


class TestAnalyzerAgent:
    """Unit tests for AnalyzerAgent"""

    @pytest.fixture
    def agent(self):
        return AnalyzerAgent()

    @pytest.mark.asyncio
    async def test_extract_entities(self, agent, mock_db, workflow_id):
        """Test entity extraction from text"""
        text = "Dr. Smith at Johns Hopkins University developed an AI system for healthcare diagnosis."

        with patch.object(agent, 'claude') as mock_claude:
            mock_claude.execute_simple = AsyncMock(return_value=json.dumps({
                "entities": [
                    {
                        "name": "Dr. Smith",
                        "type": "person",
                        "attributes": {"affiliation": "Johns Hopkins University"},
                        "confidence": 0.95,
                        "context": "Developer of AI system"
                    },
                    {
                        "name": "Johns Hopkins University",
                        "type": "organization",
                        "attributes": {"type": "university"},
                        "confidence": 0.98,
                        "context": "Institution where Dr. Smith works"
                    },
                    {
                        "name": "AI system",
                        "type": "concept",
                        "attributes": {"purpose": "healthcare diagnosis"},
                        "confidence": 0.90,
                        "context": "System developed for medical diagnosis"
                    }
                ]
            }))

            entities = await agent.extract_entities(
                mock_db, workflow_id, text, "https://example.com"
            )

            assert len(entities) == 3
            assert entities[0]["name"] == "Dr. Smith"
            assert entities[0]["type"] == "person"
            assert entities[0]["confidence"] == 0.95

    @pytest.mark.asyncio
    async def test_extract_relationships(self, agent, mock_db, workflow_id):
        """Test relationship extraction between entities"""
        entities = [
            {"name": "Dr. Smith", "type": "person"},
            {"name": "Johns Hopkins University", "type": "organization"}
        ]
        text = "Dr. Smith works at Johns Hopkins University."

        with patch.object(agent, 'claude') as mock_claude:
            mock_claude.execute_simple = AsyncMock(return_value=json.dumps({
                "relationships": [
                    {
                        "source": "Dr. Smith",
                        "target": "Johns Hopkins University",
                        "type": "part_of",
                        "description": "Employment relationship",
                        "confidence": 0.95
                    }
                ]
            }))

            relationships = await agent.extract_relationships(
                mock_db, workflow_id, text, entities
            )

            assert len(relationships) == 1
            assert relationships[0]["source"] == "Dr. Smith"
            assert relationships[0]["target"] == "Johns Hopkins University"
            assert relationships[0]["type"] == "part_of"

    @pytest.mark.asyncio
    async def test_extract_insights(self, agent, mock_db, workflow_id):
        """Test insight extraction"""
        text = """
        AI in healthcare is growing rapidly. Machine learning can diagnose diseases
        with 95% accuracy. This represents a major breakthrough in medical technology.
        Hospitals are expected to adopt these systems within 2-3 years.
        """

        with patch.object(agent, 'claude') as mock_claude:
            mock_claude.execute_simple = AsyncMock(return_value=json.dumps({
                "insights": [
                    {
                        "insight": "AI diagnostic systems achieve 95% accuracy",
                        "importance": "high",
                        "category": "finding",
                        "evidence": ["Machine learning can diagnose diseases with 95% accuracy"],
                        "actionable": True
                    },
                    {
                        "insight": "Hospitals will adopt AI systems in 2-3 years",
                        "importance": "medium",
                        "category": "trend",
                        "evidence": ["Hospitals are expected to adopt these systems within 2-3 years"],
                        "actionable": True
                    }
                ]
            }))

            insights = await agent.extract_insights(mock_db, workflow_id, text)

            assert len(insights) == 2
            assert insights[0]["importance"] == "high"
            assert insights[0]["category"] == "finding"
            assert insights[0]["actionable"] is True


# ============================================================================
# OrganizerAgent Tests
# ============================================================================


class TestOrganizerAgent:
    """Unit tests for OrganizerAgent"""

    @pytest.fixture
    def agent(self):
        return OrganizerAgent()

    @pytest.mark.asyncio
    async def test_design_taxonomy(self, agent, mock_db, workflow_id):
        """Test taxonomy design"""
        entities = [{"name": "AI", "type": "concept"}]
        insights = [{"insight": "AI is growing", "importance": "high"}]

        with patch.object(agent, 'claude') as mock_claude:
            mock_claude.execute_simple = AsyncMock(return_value=json.dumps({
                "taxonomy": {
                    "AI Applications": {
                        "Healthcare": {
                            "Diagnostics": {
                                "description": "AI diagnostic tools",
                                "examples": ["Medical imaging AI", "Symptom checker AI"]
                            }
                        }
                    }
                },
                "reasoning": "Hierarchical structure based on application domains"
            }))

            taxonomy = await agent.design_taxonomy(
                mock_db, workflow_id, "AI in healthcare", entities, insights
            )

            assert "AI Applications" in taxonomy
            assert "Healthcare" in taxonomy["AI Applications"]
            assert "Diagnostics" in taxonomy["AI Applications"]["Healthcare"]

    @pytest.mark.asyncio
    async def test_synthesize_summary(self, agent, mock_db, workflow_id):
        """Test summary synthesis"""
        tree_structure = {
            "taxonomy": {
                "AI in Healthcare": {
                    "Diagnostics": {},
                    "Treatment": {}
                }
            },
            "entities": [],
            "relationships": [],
            "insights": [
                {"insight": "AI diagnostics achieve 95% accuracy", "importance": "high"}
            ]
        }

        with patch.object(agent, 'claude') as mock_claude:
            mock_claude.execute_simple = AsyncMock(
                return_value="# AI in Healthcare Summary\n\nAI is revolutionizing healthcare with 95% diagnostic accuracy."
            )

            summary = await agent.synthesize_summary(
                mock_db, workflow_id, "AI in healthcare", tree_structure
            )

            assert summary is not None
            assert len(summary) > 0
            assert "AI" in summary or "healthcare" in summary.lower()


# ============================================================================
# AgentFactory Tests
# ============================================================================


class TestAgentFactory:
    """Unit tests for AgentFactory"""

    def test_create_research_agent(self):
        """Test ResearchAgent creation"""
        agent = AgentFactory.create_agent("research")
        assert isinstance(agent, ResearchAgent)
        assert agent.name == "ResearchAgent"

    def test_create_scraper_agent(self):
        """Test ScraperAgent creation"""
        agent = AgentFactory.create_agent("scraper")
        assert isinstance(agent, ScraperAgent)
        assert agent.name == "ScraperAgent"

    def test_create_analyzer_agent(self):
        """Test AnalyzerAgent creation"""
        agent = AgentFactory.create_agent("analyzer")
        assert isinstance(agent, AnalyzerAgent)
        assert agent.name == "AnalyzerAgent"

    def test_create_organizer_agent(self):
        """Test OrganizerAgent creation"""
        agent = AgentFactory.create_agent("organizer")
        assert isinstance(agent, OrganizerAgent)
        assert agent.name == "OrganizerAgent"

    def test_invalid_agent_type(self):
        """Test invalid agent type raises error"""
        with pytest.raises(ValueError, match="Unknown agent type"):
            AgentFactory.create_agent("invalid")

    def test_get_available_agents(self):
        """Test getting available agent types"""
        agents = AgentFactory.get_available_agents()
        assert "research" in agents
        assert "scraper" in agents
        assert "analyzer" in agents
        assert "organizer" in agents
        assert len(agents) == 4

    def test_get_agent_singleton(self):
        """Test get_agent returns singleton instances"""
        agent1 = get_agent("research")
        agent2 = get_agent("research")
        assert agent1 is agent2


# ============================================================================
# Integration Tests
# ============================================================================


class TestAgentIntegration:
    """Integration tests for agent workflows"""

    @pytest.mark.asyncio
    async def test_research_to_scraper_workflow(self, mock_db, workflow_id):
        """Test workflow from research to scraping"""
        research_agent = ResearchAgent()
        scraper_agent = ScraperAgent()

        # Mock search results
        with patch.object(research_agent, 'google_search') as mock_search:
            mock_search.search = AsyncMock(return_value=[
                {"url": "https://example.com", "title": "Test", "snippet": "Test", "relevance_score": 0.9}
            ])

            # Step 1: Discover URLs
            candidates = await research_agent.discover_urls(
                mock_db, workflow_id, "test query", num_results=5
            )

            assert len(candidates) == 1
            urls = [c.url for c in candidates]

        # Step 2: Analyze URLs for scraping
        strategy = await scraper_agent.analyze_urls(mock_db, workflow_id, urls)
        assert "http" in strategy
        assert len(strategy["http"]) > 0

    @pytest.mark.asyncio
    async def test_scraper_to_analyzer_workflow(self, mock_db, workflow_id, sample_scraped_data):
        """Test workflow from scraping to analysis"""
        scraper_agent = ScraperAgent()
        analyzer_agent = AnalyzerAgent()

        # Mock scraper results
        with patch.object(scraper_agent.orchestrator, 'batch_crawl') as mock_batch:
            from services.crawler_orchestrator import ScrapeResult, CrawlEngine

            mock_batch.return_value = [
                ScrapeResult(
                    url=data["url"],
                    title=data["title"],
                    content=data.get("content", "<html>Default content</html>"),
                    text=data["text"],
                    links=data["links"],
                    images=data["images"],
                    engine=CrawlEngine.HTTP,
                    status_code=data["status_code"],
                    error=data["error"]
                )
                for data in sample_scraped_data
            ]

            # Step 1: Scrape URLs
            urls = [d["url"] for d in sample_scraped_data]
            results = await scraper_agent.scrape_batch(
                mock_db, workflow_id, urls, engine=CrawlEngine.HTTP
            )

            assert len(results) == 2
            assert all(r["success"] for r in results)

        # Step 2: Analyze scraped content
        with patch.object(analyzer_agent, 'claude') as mock_claude:
            mock_claude.execute_simple = AsyncMock(
                return_value=json.dumps({"entities": [], "relationships": [], "insights": []})
            )

            analysis = await analyzer_agent.analyze_content(
                mock_db, workflow_id, results
            )

            assert analysis["success"] is True
            assert analysis["pages_analyzed"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
