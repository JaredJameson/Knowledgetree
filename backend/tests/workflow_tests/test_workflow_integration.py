"""
KnowledgeTree - Workflow Integration Tests
Integration tests for LangGraph workflow orchestration
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json
import asyncio

from services.langgraph_orchestrator import LangGraphOrchestrator, get_langgraph_orchestrator
from services.langgraph_nodes import (
    classify_intent,
    create_plan,
    discover_urls,
    await_user_review,
    scrape_urls,
    extract_knowledge,
    build_tree,
    synthesize_results,
    handle_error
)
from schemas.workflow import AgentWorkflowState, WorkflowTaskType, TaskComplexity
from models.agent_workflow import AgentWorkflow, WorkflowStatus, WorkflowTemplate
from models.workflow_support import WorkflowState, URLCandidate


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
async def db_session():
    """Create test database session"""
    from core.database import Base, get_db

    # Use in-memory SQLite for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session


@pytest.fixture
def sample_state():
    """Sample workflow state for testing"""
    return {
        "workflow_id": 1,
        "user_id": 1,
        "project_id": 1,
        "user_query": "Research AI applications in healthcare",
        "task_type": WorkflowTaskType.RESEARCH,
        "complexity": TaskComplexity.MEDIUM,
        "current_step": "classify_intent",
        "status": "in_progress",
        "discovered_urls": [],
        "approved_urls": [],
        "scraped_content": [],
        "knowledge_points": [],
        "tree_structure": {},
        "error": None,
        "retry_count": 0,
        "max_retries": 3,
        "max_urls": 20,
        "timeout_seconds": 1800,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "metadata": {}
    }


@pytest.fixture
def orchestrator():
    """Get LangGraph orchestrator instance"""
    return get_langgraph_orchestrator()


# ============================================================================
# Node Function Tests
# ============================================================================


class TestClassifyIntentNode:
    """Tests for classify_intent node"""

    @pytest.mark.asyncio
    async def test_classify_research_query(self, sample_state, workflow_config):
        """Test classification of research query"""
        with patch('services.langgraph_nodes.AnthropicToolClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.execute_simple = AsyncMock(
                return_value=json.dumps({
                    "task_type": "research",
                    "complexity": "medium",
                    "reasoning": "Query requires research across multiple sources"
                })
            )
            mock_client.return_value = mock_instance

            result = await classify_intent(sample_state, workflow_config)

            assert result["task_type"] == WorkflowTaskType.RESEARCH
            assert result["complexity"] == TaskComplexity.MEDIUM
            assert result["current_step"] == "classify_intent"

    @pytest.mark.asyncio
    async def test_classify_scrape_query(self, sample_state, workflow_config):
        """Test classification of scrape query"""
        sample_state["user_query"] = "Scrape https://example.com/article"

        with patch('services.langgraph_nodes.AnthropicToolClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.execute_simple = AsyncMock(
                return_value=json.dumps({
                    "task_type": "scrape",
                    "complexity": "low",
                    "reasoning": "Direct URL scraping requested"
                })
            )
            mock_client.return_value = mock_instance

            result = await classify_intent(sample_state, workflow_config)

            assert result["task_type"] == WorkflowTaskType.SCRAPE
            assert result["complexity"] == TaskComplexity.LOW


class TestCreatePlanNode:
    """Tests for create_plan node"""

    @pytest.mark.asyncio
    async def test_create_plan_medium_complexity(self, sample_state, workflow_config):
        """Test plan creation for medium complexity task"""
        sample_state["task_type"] = WorkflowTaskType.RESEARCH
        sample_state["complexity"] = TaskComplexity.MEDIUM

        with patch('services.langgraph_nodes.AnthropicToolClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.execute_simple = AsyncMock(
                return_value=json.dumps({
                    "steps": [
                        "Search for relevant sources",
                        "Evaluate and rank URLs",
                        "Scrape approved sources",
                        "Extract knowledge",
                        "Build knowledge tree"
                    ],
                    "estimated_duration_minutes": 30,
                    "resource_requirements": "Google Search API, Claude API"
                })
            )
            mock_client.return_value = mock_instance

            result = await create_plan(sample_state, workflow_config)

            assert "execution_plan" in result
            assert len(result["execution_plan"]["steps"]) >= 3
            assert result["current_step"] == "create_plan"


class TestDiscoverURLsNode:
    """Tests for discover_urls node"""

    @pytest.mark.asyncio
    async def test_discover_urls_success(self, sample_state, db_session):
        """Test successful URL discovery"""
        sample_state["task_type"] = WorkflowTaskType.RESEARCH
        sample_state["max_urls"] = 10

        with patch('services.langgraph_nodes.get_google_search_service') as mock_search:
            mock_service = AsyncMock()
            mock_service.search = AsyncMock(return_value=[
                {
                    "url": "https://example.com/article1",
                    "title": "AI in Healthcare",
                    "snippet": "Overview of AI applications",
                    "relevance_score": 0.9
                },
                {
                    "url": "https://example.com/article2",
                    "title": "Machine Learning in Medicine",
                    "snippet": "ML diagnostic tools",
                    "relevance_score": 0.85
                }
            ])
            mock_search.return_value = mock_service

            result = await discover_urls(sample_state, {}, db=db_session)

            assert len(result["discovered_urls"]) == 2
            assert result["discovered_urls"][0]["url"] == "https://example.com/article1"
            assert result["current_step"] == "discover_urls"


class TestAwaitUserReviewNode:
    """Tests for await_user_review node"""

    @pytest.mark.asyncio
    async def test_await_user_review_with_urls(self, sample_state, workflow_config):
        """Test awaiting user review with discovered URLs"""
        sample_state["discovered_urls"] = [
            {"url": "https://example.com/1", "title": "Article 1", "relevance": 0.9},
            {"url": "https://example.com/2", "title": "Article 2", "relevance": 0.8}
        ]
        sample_state["require_approval"] = True

        result = await await_user_review(sample_state, workflow_config)

        assert result["status"] == "awaiting_approval"
        assert result["current_step"] == "await_user_review"


class TestScrapeURLsNode:
    """Tests for scrape_urls node"""

    @pytest.mark.asyncio
    async def test_scrape_approved_urls(self, sample_state, workflow_config):
        """Test scraping approved URLs"""
        sample_state["approved_urls"] = [
            "https://example.com/article1",
            "https://example.com/article2"
        ]

        with patch('services.langgraph_nodes.CrawlerOrchestrator') as mock_orchestrator:
            mock_instance = AsyncMock()
            mock_instance.batch_crawl = AsyncMock(return_value=[
                Mock(
                    url="https://example.com/article1",
                    title="Article 1",
                    text="Content of article 1",
                    links=[],
                    images=[],
                    engine=Mock(value="http"),
                    status_code=200,
                    error=None
                ),
                Mock(
                    url="https://example.com/article2",
                    title="Article 2",
                    text="Content of article 2",
                    links=[],
                    images=[],
                    engine=Mock(value="http"),
                    status_code=200,
                    error=None
                )
            ])
            mock_orchestrator.return_value = mock_instance

            result = await scrape_urls(sample_state, workflow_config)

            assert len(result["scraped_content"]) == 2
            assert result["scraped_content"][0]["success"] is True
            assert result["current_step"] == "scrape_urls"


class TestExtractKnowledgeNode:
    """Tests for extract_knowledge node"""

    @pytest.mark.asyncio
    async def test_extract_knowledge_from_scraped(self, sample_state, workflow_config):
        """Test knowledge extraction from scraped content"""
        sample_state["scraped_content"] = [
            {
                "url": "https://example.com/article1",
                "title": "AI in Healthcare",
                "text": "Dr. Smith developed an AI system for diagnosis.",
                "success": True
            }
        ]

        with patch('services.langgraph_nodes.AnthropicToolClient') as mock_client:
            mock_instance = AsyncMock()
            # Mock entity extraction
            mock_instance.execute_simple = AsyncMock(
                side_effect=[
                    # First call: entities
                    json.dumps({
                        "entities": [
                            {"name": "Dr. Smith", "type": "person", "confidence": 0.95},
                            {"name": "AI system", "type": "concept", "confidence": 0.90}
                        ]
                    }),
                    # Second call: relationships
                    json.dumps({
                        "relationships": [
                            {"source": "Dr. Smith", "target": "AI system", "type": "created"}
                        ]
                    }),
                    # Third call: insights
                    json.dumps({
                        "insights": [
                            {"insight": "AI diagnosis system developed", "importance": "high"}
                        ]
                    })
                ]
            )
            mock_client.return_value = mock_instance

            result = await extract_knowledge(sample_state, workflow_config)

            assert len(result["knowledge_points"]["entities"]) >= 0
            assert result["current_step"] == "extract_knowledge"


class TestBuildTreeNode:
    """Tests for build_tree node"""

    @pytest.mark.asyncio
    async def test_build_knowledge_tree(self, sample_state, workflow_config):
        """Test building knowledge tree"""
        sample_state["knowledge_points"] = {
            "entities": [{"name": "AI", "type": "concept"}],
            "relationships": [],
            "insights": []
        }

        with patch('services.langgraph_nodes.CategoryTreeGenerator') as mock_generator:
            mock_instance = AsyncMock()
            mock_instance.generate_tree = AsyncMock(
                return_value={"tree": "structure"}
            )
            mock_generator.return_value = mock_instance

            result = await build_tree(sample_state, workflow_config)

            assert "tree_structure" in result
            assert result["current_step"] == "build_tree"


class TestSynthesizeResultsNode:
    """Tests for synthesize_results node"""

    @pytest.mark.asyncio
    async def test_synthesize_final_results(self, sample_state, workflow_config):
        """Test final result synthesis"""
        sample_state["tree_structure"] = {
            "taxonomy": {"AI": {}},
            "entities": [],
            "insights": []
        }

        with patch('services.langgraph_nodes.AnthropicToolClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.execute_simple = AsyncMock(
                return_value="# Summary\n\nAI research completed successfully."
            )
            mock_client.return_value = mock_instance

            result = await synthesize_results(sample_state, workflow_config)

            assert result["status"] == "completed"
            assert "summary" in result
            assert result["current_step"] == "synthesize_results"


# ============================================================================
# Conditional Edge Tests
# ============================================================================


class TestConditionalEdges:
    """Tests for conditional edge routing"""

    def test_should_create_plan(self, sample_state):
        """Test should_create_plan edge"""
        from services.langgraph_nodes import should_create_plan

        # Medium complexity should create plan
        sample_state["complexity"] = TaskComplexity.MEDIUM
        result = should_create_plan(sample_state)
        assert result == "create_plan"

        # Low complexity should skip plan
        sample_state["complexity"] = TaskComplexity.LOW
        result = should_create_plan(sample_state)
        assert result == "discover_urls"

    def test_check_approval_required(self, sample_state):
        """Test check_approval_required edge"""
        from services.langgraph_nodes import check_approval_required

        # With discovered URLs and require_approval
        sample_state["discovered_urls"] = [{"url": "https://example.com"}]
        sample_state["require_approval"] = True
        result = check_approval_required(sample_state)
        assert result == "await_approval"

        # Without require_approval
        sample_state["require_approval"] = False
        result = check_approval_required(sample_state)
        assert result == "proceed"


# ============================================================================
# Orchestrator Integration Tests
# ============================================================================


class TestLangGraphOrchestrator:
    """Integration tests for LangGraphOrchestrator"""

    @pytest.mark.asyncio
    async def test_execute_workflow_simple(self, sample_state, workflow_config):
        """Test complete workflow execution (simplified)"""
        orchestrator = LangGraphOrchestrator()

        with patch.multiple(
            'services.langgraph_nodes',
            classify_intent=AsyncMock(side_effect=lambda s, c: {**s, "current_step": "classify_intent_done"}),
            create_plan=AsyncMock(side_effect=lambda s, c: {**s, "current_step": "create_plan_done"}),
            discover_urls=AsyncMock(side_effect=lambda s, c: {**s, "current_step": "discover_urls_done"}),
            await_user_review=AsyncMock(side_effect=lambda s, c: {**s, "current_step": "await_user_review_done", "status": "awaiting_approval"})
        ):
            result = await orchestrator.execute_workflow(
                workflow_id=1,
                user_id=1,
                project_id=1,
                user_query="Test query"
            )

            assert "workflow_id" in result
            assert result["workflow_id"] == 1

    @pytest.mark.asyncio
    async def test_resume_workflow_after_approval(self, sample_state, workflow_config):
        """Test resuming workflow after user approval"""
        orchestrator = LangGraphOrchestrator()

        # Mock database operations
        with patch('services.langgraph_orchestrator.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock()
            mock_session.execute = AsyncMock()
            mock_session.scalar_one_or_none = AsyncMock(
                return_value=Mock(
                    status=WorkflowStatus.AWAITING_APPROVAL,
                    updated_at=datetime.utcnow()
                )
            )
            mock_session.commit = AsyncMock()
            mock_session_local.return_value = mock_session

            # Mock state snapshot
            with patch('services.langgraph_orchestrator.WorkflowState') as mock_ws:
                mock_ws.scalar_one_or_none = AsyncMock(
                    return_value=Mock(
                        state_snapshot=json.dumps(sample_state)
                    )
                )

                result = await orchestrator.resume_workflow(
                    workflow_id=1,
                    user_action="approve",
                    user_data=None
                )

                assert "workflow_id" in result


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestErrorHandling:
    """Tests for error handling in workflow"""

    @pytest.mark.asyncio
    async def test_handle_error_node(self, sample_state, workflow_config):
        """Test handle_error node"""
        from services.langgraph_nodes import handle_error

        sample_state["error"] = "Test error message"
        sample_state["retry_count"] = 1

        result = await handle_error(sample_state, workflow_config)

        assert result["status"] in ["failed", "retrying"]
        assert result["current_step"] == "handle_error"

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, sample_state, workflow_config):
        """Test behavior when max retries exceeded"""
        from services.langgraph_nodes import handle_error

        sample_state["error"] = "Persistent error"
        sample_state["retry_count"] = 3
        sample_state["max_retries"] = 3

        result = await handle_error(sample_state, workflow_config)

        assert result["status"] == "failed"

    @pytest.mark.asyncio
    async def test_orchestrator_handles_exceptions(self):
        """Test orchestrator exception handling"""
        orchestrator = LangGraphOrchestrator()

        with patch('services.langgraph_orchestrator.AsyncSessionLocal') as mock_session:
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session.commit = AsyncMock(side_effect=Exception("Database error"))
            mock_session_local = AsyncMock(return_value=mock_session)

            result = await orchestrator.execute_workflow(
                workflow_id=1,
                user_id=1,
                project_id=1,
                user_query="Test"
            )

            # Should handle error gracefully
            assert "success" in result
            assert result["success"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
