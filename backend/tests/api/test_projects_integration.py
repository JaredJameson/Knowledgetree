"""
Integration tests for Projects API endpoints

Tests all 5 REST endpoints with real PostgreSQL database:
- GET /projects/ - List projects
- GET /projects/{project_id} - Get single project
- POST /projects/ - Create project
- PATCH /projects/{project_id} - Update project
- DELETE /projects/{project_id} - Delete project
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.project import Project
from models.user import User
from models.category import Category
from models.document import Document


class TestListProjects:
    """Test GET /projects/ endpoint"""

    @pytest.mark.asyncio
    async def test_list_projects_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
        test_project: Project,
        db_session: AsyncSession,
    ):
        """Test listing projects for authenticated user"""
        # Create additional project
        project2 = Project(
            name="Second Project",
            description="Another test project",
            color="#FFE4E1",
            owner_id=test_user.id,
        )
        db_session.add(project2)
        await db_session.flush()

        response = await client.get(
            "/api/v1/projects",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "projects" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert data["total"] == 2
        assert len(data["projects"]) == 2

        # Verify statistics fields are present
        for project in data["projects"]:
            assert "id" in project
            assert "name" in project
            assert "description" in project
            assert "color" in project
            assert "owner_id" in project
            assert "created_at" in project
            assert "updated_at" in project
            assert "document_count" in project
            assert "category_count" in project
            assert "total_chunks" in project

    @pytest.mark.asyncio
    async def test_list_projects_pagination(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
        test_project: Project,
        db_session: AsyncSession,
    ):
        """Test pagination"""
        # Create 3 more projects (total 4)
        for i in range(3):
            project = Project(
                name=f"Project {i + 2}",
                description=f"Test project {i + 2}",
                owner_id=test_user.id,
            )
            db_session.add(project)
        await db_session.flush()

        # Page 1, 2 items per page
        response = await client.get(
            "/api/v1/projects",
            params={"page": 1, "page_size": 2},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["projects"]) == 2
        assert data["total"] == 4
        assert data["page"] == 1
        assert data["page_size"] == 2

        # Page 2, 2 items per page
        response = await client.get(
            "/api/v1/projects",
            params={"page": 2, "page_size": 2},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["projects"]) == 2
        assert data["total"] == 4

    @pytest.mark.asyncio
    async def test_list_projects_empty(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test listing projects when user has no projects"""
        # Create new user without projects
        from core.security import get_password_hash, create_access_token

        user = User(
            email="empty@example.com",
            password_hash=get_password_hash("testpassword"),
            is_active=True,
        )
        db_session.add(user)
        await db_session.flush()
        await db_session.refresh(user)

        token = create_access_token(data={"sub": user.email})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get(
            "/api/v1/projects",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["projects"]) == 0

    @pytest.mark.asyncio
    async def test_list_projects_unauthorized(
        self,
        client: AsyncClient,
    ):
        """Test listing projects without authentication"""
        response = await client.get("/api/v1/projects")
        assert response.status_code == 401


class TestGetProject:
    """Test GET /projects/{project_id} endpoint"""

    @pytest.mark.asyncio
    async def test_get_project_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
        test_categories: list[Category],
        db_session: AsyncSession,
    ):
        """Test getting a single project with statistics"""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_project.id
        assert data["name"] == test_project.name
        assert data["description"] == test_project.description
        assert data["color"] == test_project.color
        assert data["owner_id"] == test_project.owner_id
        assert "created_at" in data
        assert "updated_at" in data
        # Verify statistics
        assert "document_count" in data
        assert "category_count" in data
        assert data["category_count"] == 4  # From test_categories fixture
        assert "total_chunks" in data

    @pytest.mark.asyncio
    async def test_get_project_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting non-existent project"""
        response = await client.get(
            "/api/v1/projects/99999",
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_project_access_denied(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
        db_session: AsyncSession,
    ):
        """Test getting another user's project"""
        # Create another user
        from core.security import get_password_hash, create_access_token

        other_user = User(
            email="other@example.com",
            password_hash=get_password_hash("testpassword"),
            is_active=True,
        )
        db_session.add(other_user)
        await db_session.flush()

        # Create project owned by other user
        other_project = Project(
            name="Other User's Project",
            description="Should not be accessible",
            owner_id=other_user.id,
        )
        db_session.add(other_project)
        await db_session.flush()
        await db_session.refresh(other_project)

        # Try to access with test_user's token
        response = await client.get(
            f"/api/v1/projects/{other_project.id}",
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_project_unauthorized(
        self,
        client: AsyncClient,
        test_project: Project,
    ):
        """Test getting project without authentication"""
        response = await client.get(f"/api/v1/projects/{test_project.id}")
        assert response.status_code == 401


class TestCreateProject:
    """Test POST /projects/ endpoint"""

    @pytest.mark.asyncio
    async def test_create_project_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
        db_session: AsyncSession,
    ):
        """Test creating a new project"""
        project_data = {
            "name": "New Test Project",
            "description": "A newly created project",
            "color": "#E0FFE0",
        }

        response = await client.post(
            "/api/v1/projects",
            json=project_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == project_data["name"]
        assert data["description"] == project_data["description"]
        assert data["color"] == project_data["color"]
        assert data["owner_id"] == test_user.id
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

        # Verify in database
        result = await db_session.execute(
            select(Project).where(Project.id == data["id"])
        )
        db_project = result.scalar_one_or_none()
        assert db_project is not None
        assert db_project.name == project_data["name"]

    @pytest.mark.asyncio
    async def test_create_project_minimal(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
    ):
        """Test creating project with minimal data (only name)"""
        project_data = {"name": "Minimal Project"}

        response = await client.post(
            "/api/v1/projects",
            json=project_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == project_data["name"]
        assert data["description"] is None
        assert data["color"] == "#3B82F6"  # Default color
        assert data["owner_id"] == test_user.id

    @pytest.mark.asyncio
    async def test_create_project_invalid_name_empty(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test creating project with empty name"""
        project_data = {"name": ""}

        response = await client.post(
            "/api/v1/projects",
            json=project_data,
            headers=auth_headers,
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_project_invalid_name_whitespace(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test creating project with whitespace-only name"""
        project_data = {"name": "   "}

        response = await client.post(
            "/api/v1/projects",
            json=project_data,
            headers=auth_headers,
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_project_invalid_color(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test creating project with invalid hex color"""
        project_data = {
            "name": "Test Project",
            "color": "invalid-color",
        }

        response = await client.post(
            "/api/v1/projects",
            json=project_data,
            headers=auth_headers,
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_project_unauthorized(
        self,
        client: AsyncClient,
    ):
        """Test creating project without authentication"""
        project_data = {"name": "Test Project"}

        response = await client.post(
            "/api/v1/projects",
            json=project_data,
        )

        assert response.status_code == 401


class TestUpdateProject:
    """Test PATCH /projects/{project_id} endpoint"""

    @pytest.mark.asyncio
    async def test_update_project_all_fields(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
        db_session: AsyncSession,
    ):
        """Test updating all project fields"""
        update_data = {
            "name": "Updated Project Name",
            "description": "Updated description",
            "color": "#FFE4B5",
        }

        response = await client.patch(
            f"/api/v1/projects/{test_project.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_project.id
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["color"] == update_data["color"]

        # Verify in database
        await db_session.refresh(test_project)
        assert test_project.name == update_data["name"]
        assert test_project.description == update_data["description"]
        assert test_project.color == update_data["color"]

    @pytest.mark.asyncio
    async def test_update_project_partial(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
        db_session: AsyncSession,
    ):
        """Test updating only some fields"""
        original_color = test_project.color
        update_data = {"name": "New Name Only"}

        response = await client.patch(
            f"/api/v1/projects/{test_project.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["color"] == original_color  # Unchanged

    @pytest.mark.asyncio
    async def test_update_project_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test updating non-existent project"""
        update_data = {"name": "Updated Name"}

        response = await client.patch(
            "/api/v1/projects/99999",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_project_access_denied(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
        db_session: AsyncSession,
    ):
        """Test updating another user's project"""
        # Create another user
        from core.security import get_password_hash

        other_user = User(
            email="other2@example.com",
            password_hash=get_password_hash("testpassword"),
            is_active=True,
        )
        db_session.add(other_user)
        await db_session.flush()

        # Create project owned by other user
        other_project = Project(
            name="Other User's Project",
            owner_id=other_user.id,
        )
        db_session.add(other_project)
        await db_session.flush()
        await db_session.refresh(other_project)

        update_data = {"name": "Hacked Name"}

        response = await client.patch(
            f"/api/v1/projects/{other_project.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_project_invalid_name(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
    ):
        """Test updating project with invalid name"""
        update_data = {"name": "   "}  # Whitespace only

        response = await client.patch(
            f"/api/v1/projects/{test_project.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_project_unauthorized(
        self,
        client: AsyncClient,
        test_project: Project,
    ):
        """Test updating project without authentication"""
        update_data = {"name": "Updated Name"}

        response = await client.patch(
            f"/api/v1/projects/{test_project.id}",
            json=update_data,
        )

        assert response.status_code == 401


class TestDeleteProject:
    """Test DELETE /projects/{project_id} endpoint"""

    @pytest.mark.asyncio
    async def test_delete_project_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
        db_session: AsyncSession,
    ):
        """Test deleting a project"""
        project_id = test_project.id

        response = await client.delete(
            f"/api/v1/projects/{project_id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify deletion in database
        result = await db_session.execute(
            select(Project).where(Project.id == project_id)
        )
        deleted_project = result.scalar_one_or_none()
        assert deleted_project is None

    @pytest.mark.asyncio
    async def test_delete_project_with_categories_cascade(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
        test_categories: list[Category],
        db_session: AsyncSession,
    ):
        """Test deleting project cascades to categories"""
        project_id = test_project.id
        category_ids = [cat.id for cat in test_categories]

        response = await client.delete(
            f"/api/v1/projects/{project_id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify categories were also deleted
        result = await db_session.execute(
            select(Category).where(Category.id.in_(category_ids))
        )
        remaining_categories = result.scalars().all()
        assert len(remaining_categories) == 0

    @pytest.mark.asyncio
    async def test_delete_project_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test deleting non-existent project"""
        response = await client.delete(
            "/api/v1/projects/99999",
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_project_access_denied(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
        db_session: AsyncSession,
    ):
        """Test deleting another user's project"""
        # Create another user
        from core.security import get_password_hash

        other_user = User(
            email="other3@example.com",
            password_hash=get_password_hash("testpassword"),
            is_active=True,
        )
        db_session.add(other_user)
        await db_session.flush()

        # Create project owned by other user
        other_project = Project(
            name="Other User's Project",
            owner_id=other_user.id,
        )
        db_session.add(other_project)
        await db_session.flush()
        await db_session.refresh(other_project)

        response = await client.delete(
            f"/api/v1/projects/{other_project.id}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_project_unauthorized(
        self,
        client: AsyncClient,
        test_project: Project,
    ):
        """Test deleting project without authentication"""
        response = await client.delete(
            f"/api/v1/projects/{test_project.id}"
        )

        assert response.status_code == 401
