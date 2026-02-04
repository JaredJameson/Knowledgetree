"""
Verify quality of re-migrated entities
"""

import sys
import os
import asyncio
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import AsyncSessionLocal
from models.entity import Entity
from models.project import Project


async def verify_entities():
    """Verify quality of entities"""

    print("=" * 80)
    print("🔍 Entity Quality Verification")
    print("=" * 80)
    print()

    async with AsyncSessionLocal() as db:
        # Get all entities grouped by project
        result = await db.execute(
            select(Entity.project_id, func.count(Entity.id))
            .group_by(Entity.project_id)
        )
        project_counts = dict(result.all())

        for project_id, count in project_counts.items():
            # Get project name
            project_result = await db.execute(
                select(Project).where(Project.id == project_id)
            )
            project = project_result.scalar()

            print(f"📁 Project: {project.name if project else 'Unknown'} (ID: {project_id})")
            print(f"   Total Entities: {count}")
            print()

            # Get entities by type
            result = await db.execute(
                select(Entity.entity_type, func.count(Entity.id))
                .where(Entity.project_id == project_id)
                .group_by(Entity.entity_type)
            )
            type_counts = dict(result.all())

            print("   By Type:")
            for etype, ecount in sorted(type_counts.items(), key=lambda x: -x[1]):
                print(f"      {etype:20s}: {ecount:3d}")

            print()

            # Show top 10 entities by occurrence
            result = await db.execute(
                select(Entity)
                .where(Entity.project_id == project_id)
                .order_by(Entity.occurrence_count.desc())
                .limit(10)
            )
            top_entities = result.scalars().all()

            print("   Top 10 Entities (by occurrence):")
            for i, entity in enumerate(top_entities, 1):
                print(f"      {i:2d}. {entity.name:40s} [{entity.entity_type:15s}] x{entity.occurrence_count}")

            print()

            # Show all entities (for small projects)
            if count <= 50:
                result = await db.execute(
                    select(Entity)
                    .where(Entity.project_id == project_id)
                    .order_by(Entity.entity_type, Entity.name)
                )
                all_entities = result.scalars().all()

                print("   All Entities:")
                current_type = None
                for entity in all_entities:
                    if entity.entity_type != current_type:
                        current_type = entity.entity_type
                        print(f"\n      {current_type.upper()}:")
                    print(f"         • {entity.name} (x{entity.occurrence_count})")

            print("\n" + "=" * 80 + "\n")

    print("✅ Verification complete!")


if __name__ == "__main__":
    asyncio.run(verify_entities())
