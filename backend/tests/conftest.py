"""
Test fixtures and configuration for integration tests
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone

from core.database import Base, get_db
from core.config import settings
from core.security import get_password_hash, create_access_token
from main import app
from models.user import User
from models.project import Project
from models.category import Category


# Test database URL (separate from production)
TEST_DATABASE_URL = f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}_test"


@pytest.fixture(scope="function")
async def test_engine():
    """
    Create async engine for test database
    Function-scoped to ensure clean state for each test
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,  # Disable SQL logging in tests
        poolclass=NullPool,  # Disable connection pooling for tests
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a new database session for each test
    Uses transactions with rollback for test isolation
    """
    # Create session maker
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session_maker() as session:
        yield session
        # Rollback after test (automatic cleanup)
        await session.rollback()
        await session.close()


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create async HTTP client for testing FastAPI endpoints
    """
    # Override get_db dependency to use test database
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Create async client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    """
    Create a test user
    """
    user = User(
        email="test@example.com",
        full_name="Test User",
        password_hash=get_password_hash("testpassword"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
async def test_user_token(test_user: User) -> str:
    """
    Create JWT token for test user
    """
    return create_access_token(data={"sub": test_user.email})


@pytest.fixture(scope="function")
async def auth_headers(test_user_token: str) -> dict:
    """
    Create authorization headers with JWT token
    """
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture(scope="function")
async def test_project(db_session: AsyncSession, test_user: User) -> Project:
    """
    Create a test project owned by test user
    """
    project = Project(
        name="Test Project",
        description="Test project for integration tests",
        owner_id=test_user.id,
    )
    db_session.add(project)
    await db_session.flush()
    await db_session.refresh(project)
    return project


@pytest.fixture(scope="function")
async def test_categories(db_session: AsyncSession, test_project: Project) -> list[Category]:
    """
    Create a hierarchy of test categories

    Structure:
        - Root (depth=0)
            - Child 1 (depth=1)
                - Grandchild 1 (depth=2)
            - Child 2 (depth=1)
    """
    now = datetime.now(timezone.utc)

    # Root category
    root = Category(
        name="Root Category",
        description="Root category for tests",
        color="#E6E6FA",
        icon="Book",
        depth=0,
        order=0,
        parent_id=None,
        project_id=test_project.id,
        created_at=now,
        updated_at=now,
    )
    db_session.add(root)
    await db_session.flush()
    await db_session.refresh(root)

    # Child 1
    child1 = Category(
        name="Child 1",
        description="First child category",
        color="#FFE4E1",
        icon="BookOpen",
        depth=1,
        order=0,
        parent_id=root.id,
        project_id=test_project.id,
        created_at=now,
        updated_at=now,
    )
    db_session.add(child1)
    await db_session.flush()
    await db_session.refresh(child1)

    # Grandchild 1
    grandchild1 = Category(
        name="Grandchild 1",
        description="Grandchild category",
        color="#E0FFE0",
        icon="FileText",
        depth=2,
        order=0,
        parent_id=child1.id,
        project_id=test_project.id,
        created_at=now,
        updated_at=now,
    )
    db_session.add(grandchild1)
    await db_session.flush()
    await db_session.refresh(grandchild1)

    # Child 2
    child2 = Category(
        name="Child 2",
        description="Second child category",
        color="#FFE4B5",
        icon="BookOpen",
        depth=1,
        order=1,
        parent_id=root.id,
        project_id=test_project.id,
        created_at=now,
        updated_at=now,
    )
    db_session.add(child2)
    await db_session.flush()
    await db_session.refresh(child2)

    # Don't commit - keep in transaction for rollback

    return [root, child1, grandchild1, child2]


@pytest.fixture(scope="function")
async def second_test_user(db_session: AsyncSession) -> User:
    """
    Create a second test user (for access control tests)
    """
    user = User(
        email="other@example.com",
        full_name="Other User",
        password_hash=get_password_hash("otherpassword"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
async def second_user_token(second_test_user: User) -> str:
    """
    Create JWT token for second test user
    """
    return create_access_token(data={"sub": second_test_user.email})


@pytest.fixture(scope="function")
async def second_user_headers(second_user_token: str) -> dict:
    """
    Create authorization headers for second test user
    """
    return {"Authorization": f"Bearer {second_user_token}"}
