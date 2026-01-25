"""
Unit tests for Categories API endpoints

Tests CRUD operations for category tree management.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch
from fastapi import HTTPException

from api.routes.categories import (
    get_project_or_404,
    get_category_or_404,
    _build_tree_structure
)
from models.category import Category
from models.project import Project
from models.user import User
from schemas.category import CategoryTreeNode


class TestHelperFunctions:
    """Test helper functions"""

    async def test_get_project_or_404_success(self):
        """Test getting project successfully"""
        # Mock user
        user = Mock(spec=User)
        user.id = 1

        # Mock project
        project = Mock(spec=Project)
        project.id = 1
        project.owner_id = 1

        # Mock database - result_mock should be regular Mock, not AsyncMock
        db = AsyncMock()
        result_mock = Mock()  # FIXED: Regular Mock for synchronous methods
        result_mock.scalar_one_or_none.return_value = project
        db.execute.return_value = result_mock

        # Test
        result = await get_project_or_404(1, user, db)
        assert result == project

    async def test_get_project_or_404_not_found(self):
        """Test getting project that doesn't exist"""
        user = Mock(spec=User)
        user.id = 1

        # Mock database - no project
        db = AsyncMock()
        result_mock = Mock()  # FIXED: Regular Mock
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        # Test - should raise 404
        with pytest.raises(HTTPException) as exc_info:
            await get_project_or_404(1, user, db)

        assert exc_info.value.status_code == 404

    async def test_get_category_or_404_success(self):
        """Test getting category successfully"""
        user = Mock(spec=User)
        user.id = 1

        category = Mock(spec=Category)
        category.id = 1
        category.project_id = 1

        db = AsyncMock()
        result_mock = Mock()  # FIXED: Regular Mock
        result_mock.scalar_one_or_none.return_value = category
        db.execute.return_value = result_mock

        result = await get_category_or_404(1, user, db)
        assert result == category

    async def test_get_category_or_404_not_found(self):
        """Test getting category that doesn't exist"""
        user = Mock(spec=User)
        user.id = 1

        db = AsyncMock()
        result_mock = Mock()  # FIXED: Regular Mock
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        with pytest.raises(HTTPException) as exc_info:
            await get_category_or_404(1, user, db)

        assert exc_info.value.status_code == 404


class TestTreeBuilding:
    """Test tree structure building"""

    def test_build_tree_simple(self):
        """Test building simple tree"""
        # Create real Category objects (not mocks - Pydantic needs real objects)
        now = datetime.now(timezone.utc)
        
        root = Category(
            id=1,
            name="Root",
            parent_id=None,
            depth=0,
            order=0,
            color="#E6E6FA",
            icon="Book",
            project_id=1,
            created_at=now,
            updated_at=now
        )

        child1 = Category(
            id=2,
            name="Child 1",
            parent_id=1,
            depth=1,
            order=0,
            color="#FFE4E1",
            icon="BookOpen",
            project_id=1,
            created_at=now,
            updated_at=now
        )

        child2 = Category(
            id=3,
            name="Child 2",
            parent_id=1,
            depth=1,
            order=1,
            color="#E0FFE0",
            icon="BookOpen",
            project_id=1,
            created_at=now,
            updated_at=now
        )

        categories = [root, child1, child2]

        # Build tree
        tree = _build_tree_structure(categories, root_parent_id=None, max_depth=None)

        # Verify structure
        assert len(tree) == 1  # One root
        assert tree[0].id == 1
        assert len(tree[0].children) == 2  # Two children  # Two children  # Two children

    def test_build_tree_with_depth_limit(self):
        """Test building tree with depth limit"""
        now = datetime.now(timezone.utc)
        
        root = Category(
            id=1,
            name="Root",
            parent_id=None,
            depth=0,
            order=0,
            color="#E6E6FA",
            icon="Book",
            project_id=1,
            created_at=now,
            updated_at=now
        )

        child = Category(
            id=2,
            name="Child",
            parent_id=1,
            depth=1,
            order=0,
            color="#FFE4E1",
            icon="BookOpen",
            project_id=1,
            created_at=now,
            updated_at=now
        )

        grandchild = Category(
            id=3,
            name="Grandchild",
            parent_id=2,
            depth=2,
            order=0,
            color="#E0FFE0",
            icon="FileText",
            project_id=1,
            created_at=now,
            updated_at=now
        )

        categories = [root, child, grandchild]

        # Build tree with max_depth=1
        tree = _build_tree_structure(categories, root_parent_id=None, max_depth=1)

        # Verify depth limit enforced
        assert len(tree) == 1
        assert tree[0].id == 1
        assert len(tree[0].children) == 1
        assert tree[0].children[0].id == 2
        assert len(tree[0].children[0].children) == 0  # Grandchild excluded  # Grandchild excluded  # Grandchild excluded

    def test_build_tree_empty(self):
        """Test building tree from empty list"""
        categories = []
        tree = _build_tree_structure(categories, root_parent_id=None, max_depth=None)
        assert tree == []

    def test_build_tree_with_subtree_root(self):
        """Test building subtree from specific parent"""
        now = datetime.now(timezone.utc)
        
        root = Category(
            id=1,
            name="Root",
            parent_id=None,
            depth=0,
            order=0,
            color="#E6E6FA",
            icon="Book",
            project_id=1,
            created_at=now,
            updated_at=now
        )

        child = Category(
            id=2,
            name="Child",
            parent_id=1,
            depth=1,
            order=0,
            color="#FFE4E1",
            icon="BookOpen",
            project_id=1,
            created_at=now,
            updated_at=now
        )

        grandchild = Category(
            id=3,
            name="Grandchild",
            parent_id=2,
            depth=2,
            order=0,
            color="#E0FFE0",
            icon="FileText",
            project_id=1,
            created_at=now,
            updated_at=now
        )

        categories = [root, child, grandchild]

        # Build subtree starting from child (id=2)
        tree = _build_tree_structure(categories, root_parent_id=2, max_depth=None)

        # Should only get grandchild as root
        assert len(tree) == 1
        assert tree[0].id == 3


class TestCategoryValidation:
    """Test category validation logic"""

    def test_depth_validation(self):
        """Test depth validation rules"""
        # Root category should be depth 0
        root = Category(
            name="Root",
            depth=0,
            order=0,
            parent_id=None,
            project_id=1
        )
        assert root.depth == 0

        # Child of root should be depth 1
        child = Category(
            name="Child",
            depth=1,
            order=0,
            parent_id=1,
            project_id=1
        )
        assert child.depth == 1

    def test_order_validation(self):
        """Test order field"""
        cat1 = Category(
            name="First",
            depth=0,
            order=0,
            project_id=1
        )
        cat2 = Category(
            name="Second",
            depth=0,
            order=1,
            project_id=1
        )

        assert cat1.order < cat2.order


class TestCategoryColor:
    """Test category color assignment"""

    def test_default_color(self):
        """Test default color assignment"""
        cat = Category(
            name="Test",
            depth=0,
            order=0,
            project_id=1
        )
        # Default color from model
        assert cat.color == "#E6E6FA"  # Lavender

    def test_custom_color(self):
        """Test custom color assignment"""
        cat = Category(
            name="Test",
            color="#FFE4E1",  # Misty Rose
            depth=0,
            order=0,
            project_id=1
        )
        assert cat.color == "#FFE4E1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
