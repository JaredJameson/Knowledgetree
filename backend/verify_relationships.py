"""
Verify entity relationships quality
"""

import sys
import os
import asyncio
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import AsyncSessionLocal
from models.entity import Entity, EntityRelationship


async def verify_relationships():
    """Verify quality of entity relationships"""

    print("=" * 80)
    print("🔗 Entity Relationship Verification")
    print("=" * 80)
    print()

    async with AsyncSessionLocal() as db:
        # Get total relationship count
        result = await db.execute(select(func.count(EntityRelationship.id)))
        total_relationships = result.scalar()

        print(f"📊 Total Relationships: {total_relationships}")
        print()

        # Get relationships grouped by strength
        result = await db.execute(
            select(
                EntityRelationship.co_occurrence_count,
                func.count(EntityRelationship.id)
            )
            .group_by(EntityRelationship.co_occurrence_count)
            .order_by(EntityRelationship.co_occurrence_count.desc())
        )
        strength_counts = result.all()

        print("📈 Relationship Strength Distribution:")
        for co_occurrence, count in strength_counts[:10]:
            print(f"   {co_occurrence:2d} co-occurrences: {count:3d} relationships")

        print()

        # Get top 10 strongest relationships
        result = await db.execute(
            select(EntityRelationship)
            .order_by(EntityRelationship.co_occurrence_count.desc())
            .limit(10)
        )
        top_relationships = result.scalars().all()

        print("🏆 Top 10 Strongest Relationships:")
        for i, rel in enumerate(top_relationships, 1):
            # Get entity names
            result1 = await db.execute(
                select(Entity).where(Entity.id == rel.source_entity_id)
            )
            entity1 = result1.scalar()

            result2 = await db.execute(
                select(Entity).where(Entity.id == rel.target_entity_id)
            )
            entity2 = result2.scalar()

            if entity1 and entity2:
                print(f"   {i:2d}. [{entity1.name}] ⇄ [{entity2.name}]")
                print(f"       Co-occurrences: {rel.co_occurrence_count}")
                print(f"       Types: {entity1.entity_type} ↔ {entity2.entity_type}")
                print()

        # Get relationship type distribution
        result = await db.execute(
            select(
                Entity.entity_type.label("type1"),
                func.count(EntityRelationship.id).label("count")
            )
            .select_from(EntityRelationship)
            .join(Entity, EntityRelationship.source_entity_id == Entity.id)
            .group_by(Entity.entity_type)
            .order_by(func.count(EntityRelationship.id).desc())
        )
        type_distribution = result.all()

        print("📊 Relationship Type Distribution (by entity1 type):")
        for entity_type, count in type_distribution:
            print(f"   {entity_type:20s}: {count:3d} relationships")

        print()

        # Show sample relationships for each type pair
        print("🔍 Sample Relationships by Type Pairs:")
        print()

        result = await db.execute(
            select(EntityRelationship)
            .limit(20)
        )
        sample_relationships = result.scalars().all()

        for rel in sample_relationships:
            result1 = await db.execute(
                select(Entity).where(Entity.id == rel.source_entity_id)
            )
            entity1 = result1.scalar()

            result2 = await db.execute(
                select(Entity).where(Entity.id == rel.target_entity_id)
            )
            entity2 = result2.scalar()

            if entity1 and entity2:
                print(f"   [{entity1.entity_type:12s}] {entity1.name:30s} ⇄ [{entity2.entity_type:12s}] {entity2.name}")

        print()
        print("=" * 80)

    print("✅ Relationship verification complete!")


if __name__ == "__main__":
    asyncio.run(verify_relationships())
