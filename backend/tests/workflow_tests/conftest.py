"""
KnowledgeTree - Workflow Tests Configuration
Pytest configuration and shared fixtures for workflow testing
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncSession as SQLAlchemyAsyncSession
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


# ============================================================================
# Async Event Loop Configuration
# ============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Database Fixtures
# ============================================================================


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create test database session

    Uses in-memory SQLite for fast, isolated testing.
    Creates tables using raw SQL to avoid JSONB issues with SQLite.
    """
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import text

    # Create in-memory SQLite database
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False}
    )

    # Create workflow tables using raw SQL
    create_tables_sql = """
    CREATE TABLE agent_workflows (
        id INTEGER PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        template VARCHAR(50) NOT NULL,
        status VARCHAR(50) NOT NULL,
        config TEXT,
        project_id INTEGER NOT NULL,
        estimated_duration_minutes INTEGER,
        actual_duration_minutes INTEGER,
        user_query TEXT,
        agent_type VARCHAR(50),
        parent_workflow_id INTEGER,
        error_message TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        completed_at DATETIME
    );

    CREATE TABLE workflow_states (
        id INTEGER PRIMARY KEY,
        workflow_id INTEGER NOT NULL REFERENCES agent_workflows(id) ON DELETE CASCADE,
        step VARCHAR(100) NOT NULL,
        state_snapshot TEXT NOT NULL,
        status VARCHAR(50),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE workflow_tools (
        id INTEGER PRIMARY KEY,
        workflow_id INTEGER NOT NULL REFERENCES agent_workflows(id) ON DELETE CASCADE,
        tool_name VARCHAR(100) NOT NULL,
        agent_type VARCHAR(50),
        input TEXT,
        output TEXT,
        status VARCHAR(50) NOT NULL,
        error_message TEXT,
        duration_ms INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE url_candidates (
        id INTEGER PRIMARY KEY,
        workflow_id INTEGER NOT NULL REFERENCES agent_workflows(id) ON DELETE CASCADE,
        url VARCHAR(2048) NOT NULL,
        title VARCHAR(500),
        relevance_score DECIMAL(3,2),
        source VARCHAR(100),
        meta_data TEXT,
        user_approval VARCHAR(20) DEFAULT 'pending',
        reviewed_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE research_tasks (
        id INTEGER PRIMARY KEY,
        workflow_id INTEGER NOT NULL REFERENCES agent_workflows(id) ON DELETE CASCADE,
        task_type VARCHAR(100) NOT NULL,
        description TEXT,
        status VARCHAR(50) NOT NULL,
        assigned_agent VARCHAR(50),
        result TEXT,
        started_at DATETIME,
        completed_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE agent_messages (
        id INTEGER PRIMARY KEY,
        workflow_id INTEGER NOT NULL REFERENCES agent_workflows(id) ON DELETE CASCADE,
        agent_type VARCHAR(50) NOT NULL,
        step VARCHAR(100) NOT NULL,
        content TEXT NOT NULL,
        reasoning TEXT,
        meta_data TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """

    # Create tables
    async with engine.begin() as conn:
        await conn.execute(text(create_tables_sql))

    # Create session
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session

    # Cleanup
    await engine.dispose()


@pytest.fixture(scope="function")
def sync_db_session() -> Generator[Session, None, None]:
    """
    Create synchronous test database session

    Uses in-memory SQLite for fast testing.
    """
    from core.database import Base

    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False}
    )

    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()
    engine.dispose()


# ============================================================================
# API Client Fixtures
# ============================================================================


@pytest.fixture
async def api_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create test API client with database override

    Automatically overrides database dependency with test session.
    """
    from main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def authenticated_client(api_client: AsyncClient, mock_user) -> AsyncClient:
    """
    Create authenticated API client

    Mocks authentication and returns client with auth headers.
    """
    from fastapi import FastAPI
    from main import app
    from api.dependencies import get_current_user

    async def override_get_current_user():
        return mock_user

    app.dependency_overrides[get_current_user] = override_get_current_user

    return api_client


# ============================================================================
# Mock Fixtures
# ============================================================================


@pytest.fixture
def mock_user():
    """Create mock user for authentication"""
    from models.user import User
    from datetime import datetime

    user = User(
        id=1,
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        is_active=True,
        is_superuser=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    return user


@pytest.fixture
def mock_project():
    """Create mock project"""
    from models.project import Project
    from datetime import datetime

    project = Project(
        id=1,
        name="Test Project",
        description="Test project description",
        user_id=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    return project


@pytest.fixture
def mock_workflow():
    """Create mock agent workflow"""
    from models.agent_workflow import AgentWorkflow, WorkflowStatus, WorkflowTemplate
    from datetime import datetime

    workflow = AgentWorkflow(
        id=1,
        name="Test Workflow",
        template=WorkflowTemplate.RESEARCH,
        status=WorkflowStatus.PENDING,
        config='{"max_urls": 20}',
        project_id=1,
        user_query="Test query",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    return workflow


# ============================================================================
# Test Data Fixtures
# ============================================================================


@pytest.fixture
def sample_urls():
    """Sample URLs for testing"""
    return [
        "https://example.com/article1",
        "https://blog.example.com/post2",
        "https://twitter.com/user/status/123",
        "https://linkedin.com/post/456",
        "https://amazon.com/product/789"
    ]


@pytest.fixture
def sample_scraped_data():
    """Sample scraped data for testing"""
    return [
        {
            "url": "https://example.com/article1",
            "title": "AI in Healthcare 2024",
            "text": "Artificial Intelligence is revolutionizing healthcare. "
                   "Machine learning algorithms can diagnose diseases with 95% accuracy. "
                   "Dr. Smith at Johns Hopkins University has developed a new system.",
            "links": ["https://example.com/related"],
            "images": ["https://example.com/image.jpg"],
            "engine": "http",
            "status_code": 200,
            "error": None,
            "success": True
        },
        {
            "url": "https://blog.example.com/post2",
            "title": "Future of Medicine",
            "text": "The future of medicine lies in personalized treatments. "
                   "AI-powered diagnostics are becoming mainstream. "
                   "Hospitals are adopting these technologies rapidly.",
            "links": [],
            "images": [],
            "engine": "http",
            "status_code": 200,
            "error": None,
            "success": True
        }
    ]


@pytest.fixture
def sample_workflow_state():
    """Sample workflow state for testing"""
    from schemas.workflow import AgentWorkflowState, WorkflowTaskType, TaskComplexity
    from datetime import datetime

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


# ============================================================================
# Mock Services Fixtures
# ============================================================================


@pytest.fixture
def mock_google_search():
    """Mock Google Search service"""
    from services.google_search import GoogleSearchService

    service = GoogleSearchService()
    service.search = AsyncMock(return_value=[
        {
            "url": "https://example.com/article1",
            "title": "AI in Healthcare",
            "snippet": "Overview of AI healthcare applications",
            "relevance_score": 0.9
        },
        {
            "url": "https://example.com/article2",
            "title": "Machine Learning in Medicine",
            "snippet": "ML diagnostic applications",
            "relevance_score": 0.85
        }
    ])
    return service


@pytest.fixture
def mock_crawler_orchestrator():
    """Mock crawler orchestrator"""
    from services.crawler_orchestrator import CrawlerOrchestrator, ScrapeResult, CrawlEngine

    orchestrator = CrawlerOrchestrator()
    orchestrator.batch_crawl = AsyncMock(return_value=[
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
    ])
    return orchestrator


@pytest.fixture
def mock_claude_client():
    """Mock Claude tool client"""
    from services.claude_tool_client import AnthropicToolClient

    client = AnthropicToolClient()
    client.execute_simple = AsyncMock(
        return_value='{"result": "success"}'
    )
    client.execute_with_tools = AsyncMock(
        return_value={
            "response": "Test response",
            "tool_calls": []
        }
    )
    return client


# ============================================================================
# Pytest Configuration
# ============================================================================


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers",
        "unit: Unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers",
        "integration: Integration tests (database, services)"
    )
    config.addinivalue_line(
        "markers",
        "e2e: End-to-end tests (slow, full workflow)"
    )
    config.addinivalue_line(
        "markers",
        "slow: Slow-running tests"
    )
    config.addinivalue_line(
        "markers",
        "agent: Agent-specific tests (research, scraper, analyzer, organizer)"
    )


# ============================================================================
# Test Helpers
# ============================================================================


class TestHelpers:
    """Helper methods for testing"""

    @staticmethod
    async def create_test_workflow(db: AsyncSession, **kwargs) -> "AgentWorkflow":
        """Create test workflow in database"""
        from models.agent_workflow import AgentWorkflow, WorkflowStatus, WorkflowTemplate
        from datetime import datetime

        workflow = AgentWorkflow(
            name=kwargs.get("name", "Test Workflow"),
            template=WorkflowTemplate(kwargs.get("template", "research")),
            status=WorkflowStatus(kwargs.get("status", "pending")),
            config=kwargs.get("config", "{}"),
            project_id=kwargs.get("project_id", 1),
            user_query=kwargs.get("user_query", "Test query"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(workflow)
        await db.flush()
        await db.refresh(workflow)

        return workflow

    @staticmethod
    async def create_test_url_candidates(
        db: AsyncSession,
        workflow_id: int,
        count: int = 5
    ) -> list:
        """Create test URL candidates in database"""
        from models.workflow_support import URLCandidate
        from datetime import datetime

        candidates = []
        for i in range(count):
            candidate = URLCandidate(
                workflow_id=workflow_id,
                url=f"https://example.com/page{i}",
                title=f"Page {i}",
                relevance_score=0.9 - (i * 0.1),
                source="test",
                user_approval="pending",
                created_at=datetime.utcnow()
            )
            db.add(candidate)
            candidates.append(candidate)

        await db.flush()

        return candidates

    @staticmethod
    def assert_valid_workflow_state(state: dict) -> None:
        """Assert that workflow state is valid"""
        required_fields = [
            "workflow_id", "user_id", "project_id", "user_query",
            "task_type", "complexity", "current_step", "status"
        ]

        for field in required_fields:
            assert field in state, f"Missing required field: {field}"

        assert state["workflow_id"] > 0
        assert state["user_id"] > 0
        assert state["project_id"] > 0
        assert len(state["user_query"]) > 0
        assert state["status"] in ["pending", "in_progress", "completed", "failed", "awaiting_approval"]


@pytest.fixture
def test_helpers():
    """Provide test helpers to tests"""
    return TestHelpers


@pytest.fixture
def workflow_config(db_session):
    """Config dict for LangGraph node functions"""
    return {"db": db_session}
