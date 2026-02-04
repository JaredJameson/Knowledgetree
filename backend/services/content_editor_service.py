"""
Content Editor Service
Manages content drafting, publishing workflow, and version history
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.category import Category
from models.content import ContentVersion
from core.exceptions import NotFoundException, ValidationException


class ContentEditorService:
    """
    Service for managing content editing workflow.

    Handles draft/review/publish workflow, version history, and content restoration.

    Workflow States:
    - draft: Content is being edited (default)
    - review: Content submitted for review
    - published: Content is live and visible

    Version Creation:
    - Automatically creates version on every save_draft() call
    - Version numbers are auto-incremented (1, 2, 3, ...)
    - Each version stores full content snapshot + change summary
    """

    async def save_draft(
        self,
        db: AsyncSession,
        category_id: int,
        draft_content: str,
        user_id: int,
        change_summary: Optional[str] = None,
        auto_version: bool = True
    ) -> Category:
        """
        Save draft content for a category.

        Automatically creates a new version if auto_version=True.
        Updates category.draft_content and category.updated_at.

        Args:
            db: Database session
            category_id: Category ID to update
            draft_content: New draft content (markdown/HTML)
            user_id: User making the change
            change_summary: Optional description of changes
            auto_version: Create version snapshot (default: True)

        Returns:
            Updated Category instance

        Raises:
            NotFoundException: If category doesn't exist
        """
        # Fetch category
        result = await db.execute(
            select(Category).where(Category.id == category_id)
        )
        category = result.scalar_one_or_none()

        if not category:
            raise NotFoundException(f"Category {category_id} not found")

        # Update draft content
        category.draft_content = draft_content
        category.updated_at = datetime.utcnow()

        # Create version snapshot if requested
        if auto_version:
            await self._create_version(
                db=db,
                category_id=category_id,
                content=draft_content,
                user_id=user_id,
                change_summary=change_summary
            )

        await db.commit()
        await db.refresh(category)

        return category

    async def publish(
        self,
        db: AsyncSession,
        category_id: int,
        user_id: int,
        create_version: bool = True
    ) -> Category:
        """
        Publish draft content.

        Moves draft_content → published_content, sets status to 'published',
        records publication timestamp and user.

        Args:
            db: Database session
            category_id: Category ID to publish
            user_id: User performing publication
            create_version: Create version before publishing (default: True)

        Returns:
            Updated Category instance

        Raises:
            NotFoundException: If category doesn't exist
            ValidationException: If no draft content to publish
        """
        # Fetch category
        result = await db.execute(
            select(Category).where(Category.id == category_id)
        )
        category = result.scalar_one_or_none()

        if not category:
            raise NotFoundException(f"Category {category_id} not found")

        if not category.draft_content:
            raise ValidationException("No draft content to publish")

        # Create version before publishing
        if create_version:
            await self._create_version(
                db=db,
                category_id=category_id,
                content=category.draft_content,
                user_id=user_id,
                change_summary="Published version"
            )

        # Publish content
        category.published_content = category.draft_content
        category.content_status = "published"
        category.published_at = datetime.utcnow()
        category.reviewed_by = user_id
        category.reviewed_at = datetime.utcnow()
        category.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(category)

        return category

    async def unpublish(
        self,
        db: AsyncSession,
        category_id: int,
        user_id: int
    ) -> Category:
        """
        Unpublish content (set status back to draft).

        Keeps published_content intact but changes status to 'draft'.
        Useful for temporarily hiding content or making edits.

        Args:
            db: Database session
            category_id: Category ID to unpublish
            user_id: User performing unpublish

        Returns:
            Updated Category instance

        Raises:
            NotFoundException: If category doesn't exist
        """
        result = await db.execute(
            select(Category).where(Category.id == category_id)
        )
        category = result.scalar_one_or_none()

        if not category:
            raise NotFoundException(f"Category {category_id} not found")

        category.content_status = "draft"
        category.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(category)

        return category

    async def get_versions(
        self,
        db: AsyncSession,
        category_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[ContentVersion]:
        """
        Get version history for a category.

        Returns versions in reverse chronological order (newest first).
        Includes creator relationship for user information.

        Args:
            db: Database session
            category_id: Category ID
            limit: Maximum versions to return (default: 50)
            offset: Pagination offset (default: 0)

        Returns:
            List of ContentVersion instances
        """
        result = await db.execute(
            select(ContentVersion)
            .where(ContentVersion.category_id == category_id)
            .options(selectinload(ContentVersion.creator))
            .order_by(ContentVersion.version_number.desc())
            .limit(limit)
            .offset(offset)
        )

        return list(result.scalars().all())

    async def get_version_count(
        self,
        db: AsyncSession,
        category_id: int
    ) -> int:
        """
        Get total version count for a category.

        Args:
            db: Database session
            category_id: Category ID

        Returns:
            Total number of versions
        """
        result = await db.execute(
            select(func.count(ContentVersion.id))
            .where(ContentVersion.category_id == category_id)
        )

        return result.scalar() or 0

    async def get_version(
        self,
        db: AsyncSession,
        category_id: int,
        version_number: int
    ) -> Optional[ContentVersion]:
        """
        Get specific version by number.

        Args:
            db: Database session
            category_id: Category ID
            version_number: Version number to retrieve

        Returns:
            ContentVersion instance or None
        """
        result = await db.execute(
            select(ContentVersion)
            .where(
                and_(
                    ContentVersion.category_id == category_id,
                    ContentVersion.version_number == version_number
                )
            )
            .options(selectinload(ContentVersion.creator))
        )

        return result.scalar_one_or_none()

    async def restore_version(
        self,
        db: AsyncSession,
        category_id: int,
        version_number: int,
        user_id: int,
        create_new_version: bool = True
    ) -> Category:
        """
        Restore content from a specific version.

        Sets category.draft_content to the content from the specified version.
        Optionally creates a new version marking this restoration.

        Args:
            db: Database session
            category_id: Category ID
            version_number: Version number to restore
            user_id: User performing restoration
            create_new_version: Create new version after restore (default: True)

        Returns:
            Updated Category instance

        Raises:
            NotFoundException: If category or version doesn't exist
        """
        # Fetch version
        version = await self.get_version(db, category_id, version_number)
        if not version:
            raise NotFoundException(
                f"Version {version_number} not found for category {category_id}"
            )

        # Fetch category
        result = await db.execute(
            select(Category).where(Category.id == category_id)
        )
        category = result.scalar_one_or_none()

        if not category:
            raise NotFoundException(f"Category {category_id} not found")

        # Restore content to draft
        category.draft_content = version.content
        category.updated_at = datetime.utcnow()

        # Create new version marking restoration
        if create_new_version:
            await self._create_version(
                db=db,
                category_id=category_id,
                content=version.content,
                user_id=user_id,
                change_summary=f"Restored from version {version_number}"
            )

        await db.commit()
        await db.refresh(category)

        return category

    async def _create_version(
        self,
        db: AsyncSession,
        category_id: int,
        content: str,
        user_id: int,
        change_summary: Optional[str] = None
    ) -> ContentVersion:
        """
        Internal method to create a new version.

        Automatically determines next version number by incrementing max(version_number) + 1.

        Args:
            db: Database session
            category_id: Category ID
            content: Content snapshot
            user_id: User creating version
            change_summary: Optional change description

        Returns:
            Created ContentVersion instance
        """
        # Get next version number
        result = await db.execute(
            select(func.max(ContentVersion.version_number))
            .where(ContentVersion.category_id == category_id)
        )
        max_version = result.scalar()
        next_version = (max_version or 0) + 1

        # Create version
        version = ContentVersion(
            category_id=category_id,
            version_number=next_version,
            content=content,
            created_by=user_id,
            change_summary=change_summary
        )

        db.add(version)
        await db.flush()  # Get ID without committing

        return version

    async def compare_versions(
        self,
        db: AsyncSession,
        category_id: int,
        version_a: int,
        version_b: int
    ) -> Dict[str, Any]:
        """
        Get content from two versions for comparison.

        Useful for diff visualization in frontend.

        Args:
            db: Database session
            category_id: Category ID
            version_a: First version number
            version_b: Second version number

        Returns:
            Dict with version_a, version_b content and metadata

        Raises:
            NotFoundException: If either version doesn't exist
        """
        # Fetch both versions
        v_a = await self.get_version(db, category_id, version_a)
        v_b = await self.get_version(db, category_id, version_b)

        if not v_a:
            raise NotFoundException(f"Version {version_a} not found")
        if not v_b:
            raise NotFoundException(f"Version {version_b} not found")

        return {
            "version_a": {
                "number": v_a.version_number,
                "content": v_a.content,
                "created_at": v_a.created_at.isoformat(),
                "created_by": v_a.created_by,
                "change_summary": v_a.change_summary
            },
            "version_b": {
                "number": v_b.version_number,
                "content": v_b.content,
                "created_at": v_b.created_at.isoformat(),
                "created_by": v_b.created_by,
                "change_summary": v_b.change_summary
            }
        }
