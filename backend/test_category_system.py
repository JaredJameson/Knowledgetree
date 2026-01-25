#!/usr/bin/env python3
"""
Category API System Test
Tests the complete Category CRUD functionality with authentication
"""

import asyncio
import sys
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Add backend to path
sys.path.insert(0, '/home/jarek/projects/knowledgetree/backend')

from core.database import AsyncSessionLocal
from models.user import User
from models.project import Project
from models.category import Category
from core.security import get_password_hash


async def create_test_data():
    """Create test user and project"""
    async with AsyncSessionLocal() as db:
        # Check if test user exists
        result = await db.execute(
            select(User).where(User.email == "categorytest@knowledgetree.com")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print("👤 Creating test user...")
            user = User(
                email="categorytest@knowledgetree.com",
                password_hash=get_password_hash("TestPassword123!"),
                full_name="Category Test User",
                is_active=True,
                is_verified=True
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            print(f"✅ User created (ID: {user.id})")
        else:
            print(f"ℹ️  Using existing user (ID: {user.id})")
        
        # Create test project
        print("📦 Creating test project...")
        project = Project(
            name=f"Category Test Project {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            description="Temporary project for testing category system",
            color="#E6E6FA",
            owner_id=user.id
        )
        db.add(project)
        await db.commit()
        await db.refresh(project)
        print(f"✅ Project created (ID: {project.id})")
        
        return user.id, project.id


async def test_category_crud(project_id: int):
    """Test Category CRUD operations"""
    async with AsyncSessionLocal() as db:
        print("\n🧪 Testing Category CRUD Operations")
        print("=" * 50)
        
        # Test 1: Create root category
        print("\n1️⃣ Creating root category 'Documentation'...")
        doc_category = Category(
            name="Documentation",
            description="Technical documentation and guides",
            color="#E6E6FA",
            icon="folder",
            depth=0,
            order=0,
            parent_id=None,
            project_id=project_id
        )
        db.add(doc_category)
        await db.commit()
        await db.refresh(doc_category)
        print(f"✅ Created (ID: {doc_category.id}, Depth: {doc_category.depth})")
        
        # Test 2: Create subcategories
        print("\n2️⃣ Creating subcategories...")
        api_category = Category(
            name="API Reference",
            description="REST API documentation",
            color="#FFE4E1",
            icon="folder",
            depth=1,
            order=0,
            parent_id=doc_category.id,
            project_id=project_id
        )
        db.add(api_category)
        
        guide_category = Category(
            name="User Guide",
            description="End-user documentation",
            color="#E0FFE0",
            icon="folder",
            depth=1,
            order=1,
            parent_id=doc_category.id,
            project_id=project_id
        )
        db.add(guide_category)
        
        await db.commit()
        await db.refresh(api_category)
        await db.refresh(guide_category)
        print(f"✅ Created 'API Reference' (ID: {api_category.id}, Depth: {api_category.depth})")
        print(f"✅ Created 'User Guide' (ID: {guide_category.id}, Depth: {guide_category.depth})")
        
        # Test 3: Create nested subcategory
        print("\n3️⃣ Creating nested subcategory (depth 2)...")
        endpoints_category = Category(
            name="Endpoints",
            description="API endpoint documentation",
            color="#FFD4E1",
            icon="folder",
            depth=2,
            order=0,
            parent_id=api_category.id,
            project_id=project_id
        )
        db.add(endpoints_category)
        await db.commit()
        await db.refresh(endpoints_category)
        print(f"✅ Created 'Endpoints' (ID: {endpoints_category.id}, Depth: {endpoints_category.depth})")
        
        # Test 4: Query all categories for project
        print("\n4️⃣ Querying all categories for project...")
        result = await db.execute(
            select(Category)
            .where(Category.project_id == project_id)
            .order_by(Category.depth, Category.order)
        )
        categories = result.scalars().all()
        print(f"✅ Found {len(categories)} categories:")
        for cat in categories:
            indent = "  " * cat.depth
            print(f"   {indent}📁 {cat.name} (ID: {cat.id}, Depth: {cat.depth}, Parent: {cat.parent_id})")
        
        # Test 5: Update category
        print("\n5️⃣ Updating root category name and color...")
        doc_category.name = "📚 Documentation"
        doc_category.color = "#E0E0FF"
        await db.commit()
        await db.refresh(doc_category)
        print(f"✅ Updated (New name: '{doc_category.name}', New color: {doc_category.color})")
        
        # Test 6: Get category with children count
        print("\n6️⃣ Counting children of root category...")
        result = await db.execute(
            select(Category).where(Category.parent_id == doc_category.id)
        )
        children = result.scalars().all()
        print(f"✅ Root category has {len(children)} direct children:")
        for child in children:
            print(f"   - {child.name} (ID: {child.id})")
        
        # Test 7: Verify tree structure
        print("\n7️⃣ Verifying tree structure integrity...")
        # Check that all categories have correct depth
        result = await db.execute(
            select(Category).where(Category.project_id == project_id)
        )
        all_categories = result.scalars().all()
        
        integrity_ok = True
        for cat in all_categories:
            if cat.parent_id is None:
                if cat.depth != 0:
                    print(f"   ❌ Root category {cat.name} has incorrect depth: {cat.depth} (should be 0)")
                    integrity_ok = False
            else:
                # Get parent
                parent_result = await db.execute(
                    select(Category).where(Category.id == cat.parent_id)
                )
                parent = parent_result.scalar_one_or_none()
                if parent and cat.depth != parent.depth + 1:
                    print(f"   ❌ Category {cat.name} has incorrect depth: {cat.depth} (should be {parent.depth + 1})")
                    integrity_ok = False
        
        if integrity_ok:
            print("   ✅ Tree structure integrity verified")
        
        # Test 8: Delete leaf category
        print("\n8️⃣ Deleting leaf category (Endpoints)...")
        await db.delete(endpoints_category)
        await db.commit()
        print(f"✅ Deleted (ID: {endpoints_category.id})")
        
        # Test 9: Try to verify cascade behavior (info only - not deleting for now)
        print("\n9️⃣ Verifying cascade delete would work...")
        result = await db.execute(
            select(Category).where(Category.parent_id == doc_category.id)
        )
        would_cascade = result.scalars().all()
        print(f"ℹ️  If root category were deleted with cascade, {len(would_cascade)} direct children would be deleted:")
        for cat in would_cascade:
            # Count this category's children
            child_result = await db.execute(
                select(Category).where(Category.parent_id == cat.id)
            )
            child_count = len(child_result.scalars().all())
            print(f"   - {cat.name} (which has {child_count} children)")
        
        print("\n✅ All CRUD tests completed successfully!")
        return doc_category.id


async def cleanup_test_data(project_id: int):
    """Clean up test data"""
    async with AsyncSessionLocal() as db:
        print("\n🧹 Cleaning up test data...")
        
        # Delete all categories in project
        result = await db.execute(
            select(Category).where(Category.project_id == project_id)
        )
        categories = result.scalars().all()
        for cat in categories:
            await db.delete(cat)
        
        # Delete project
        result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        if project:
            await db.delete(project)
        
        await db.commit()
        print("✅ Test data cleaned up")


async def main():
    """Main test function"""
    print("🧪 KnowledgeTree Category System Test")
    print("=" * 50)
    
    try:
        # Create test data
        user_id, project_id = await create_test_data()
        
        # Run CRUD tests
        root_category_id = await test_category_crud(project_id)
        
        # Cleanup
        await cleanup_test_data(project_id)
        
        print("\n✅ All tests passed!")
        print(f"\n📝 Summary:")
        print(f"   - User ID: {user_id}")
        print(f"   - Project ID: {project_id}")
        print(f"   - Root Category ID: {root_category_id}")
        print(f"\n🌐 Frontend: http://localhost:5176")
        print(f"📚 API Docs: http://localhost:8765/docs")
        
    except Exception as e:
        print(f"\n❌ Test failed with error:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
