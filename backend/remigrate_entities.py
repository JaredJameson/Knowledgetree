"""
Re-migrate entities for existing documents using improved spaCy NER

This script:
1. Clears existing entities for selected documents
2. Re-runs entity extraction with new spaCy NER
3. Rebuilds entity relationships
4. Shows before/after statistics

Usage:
    python remigrate_entities.py                    # Re-migrate all documents
    python remigrate_entities.py --document-id 123  # Re-migrate specific document
    python remigrate_entities.py --project-id 1     # Re-migrate all docs in project
    python remigrate_entities.py --dry-run          # Show what would be done
"""

import sys
import os
import asyncio
import argparse
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import AsyncSessionLocal
from models.document import Document
from models.chunk import Chunk
from models.entity import Entity
from services.entity_migrator import EntityMigrator


async def get_migration_stats(db: AsyncSession, document_id: int = None, project_id: int = None):
    """Get current entity statistics"""

    # Build query for chunks
    query = select(Chunk)
    if document_id:
        query = query.where(Chunk.document_id == document_id)
    elif project_id:
        query = query.join(Document).where(Document.project_id == project_id)

    result = await db.execute(query)
    chunks = result.scalars().all()

    if not chunks:
        return {"documents": 0, "chunks": 0, "entities": 0, "unique_entities": 0}

    # Get project IDs from chunks
    doc_ids = list(set(chunk.document_id for chunk in chunks))

    # Get projects from documents
    doc_query = select(Document).where(Document.id.in_(doc_ids))
    result = await db.execute(doc_query)
    documents = result.scalars().all()
    project_ids = list(set(doc.project_id for doc in documents))

    # Count entities for these projects
    entity_query = select(func.count(Entity.id)).where(Entity.project_id.in_(project_ids))
    result = await db.execute(entity_query)
    entity_count = result.scalar()

    # Count unique entity names (entities are already unique per project)
    unique_query = select(func.count(Entity.id)).where(Entity.project_id.in_(project_ids))
    result = await db.execute(unique_query)
    unique_count = result.scalar()

    return {
        "documents": len(doc_ids),
        "chunks": len(chunks),
        "entities": entity_count,
        "unique_entities": unique_count
    }


async def clear_entities(db: AsyncSession, document_id: int = None, project_id: int = None):
    """Clear existing entities for selected documents"""

    # Get project IDs
    if project_id:
        project_ids = [project_id]
    elif document_id:
        # Get project from document
        doc_query = select(Document.project_id).where(Document.id == document_id)
        result = await db.execute(doc_query)
        project_id_result = result.scalar()
        if not project_id_result:
            return 0
        project_ids = [project_id_result]
    else:
        # Get all projects with documents
        doc_query = select(func.distinct(Document.project_id))
        result = await db.execute(doc_query)
        project_ids = [row[0] for row in result.all()]

    if not project_ids:
        return 0

    # Delete entities for these projects
    delete_query = delete(Entity).where(Entity.project_id.in_(project_ids))
    result = await db.execute(delete_query)
    await db.commit()

    return result.rowcount


async def remigrate_projects(db: AsyncSession, document_id: int = None, project_id: int = None, language: str = 'en'):
    """Re-migrate projects to entities using new NER"""

    # Get project IDs
    if project_id:
        project_ids = [project_id]
    elif document_id:
        # Get project from document
        doc_query = select(Document.project_id).where(Document.id == document_id)
        result = await db.execute(doc_query)
        project_id_result = result.scalar()
        if not project_id_result:
            print("⚠️  Document not found")
            return 0
        project_ids = [project_id_result]
    else:
        # Get all projects with documents
        doc_query = select(func.distinct(Document.project_id))
        result = await db.execute(doc_query)
        project_ids = [row[0] for row in result.all()]

    if not project_ids:
        print("⚠️  No projects found to migrate")
        return 0

    # Initialize migrator with spaCy NER
    migrator = EntityMigrator(db, use_spacy=True, language=language)

    # Migrate each project
    migrated_count = 0
    failed_count = 0
    total_entities = 0

    print(f"\n🔄 Migrating {len(project_ids)} project(s)...")

    for i, pid in enumerate(project_ids, 1):
        try:
            print(f"\n   Project {i}/{len(project_ids)} (ID: {pid})...")

            # Migrate project
            result = await migrator.migrate_project_entities(project_id=pid)

            entities_created = result.get('entities_created', 0)
            relationships_created = result.get('relationships_created', 0)

            print(f"   ✅ Created {entities_created} entities, {relationships_created} relationships")

            migrated_count += 1
            total_entities += entities_created

        except Exception as e:
            print(f"   ❌ Failed to migrate project {pid}: {e}")
            import traceback
            traceback.print_exc()
            failed_count += 1

    print(f"\n✅ Migration complete: {migrated_count} projects migrated, {failed_count} failed")
    print(f"   Total entities created: {total_entities}")

    return migrated_count


async def main():
    """Main remigration function"""

    parser = argparse.ArgumentParser(description='Re-migrate entities using improved spaCy NER')
    parser.add_argument('--document-id', type=int, help='Re-migrate specific document')
    parser.add_argument('--project-id', type=int, help='Re-migrate all documents in project')
    parser.add_argument('--language', default='en', choices=['en', 'pl'], help='Language for NER (default: en)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')

    args = parser.parse_args()

    print("=" * 80)
    print("🚀 Entity Re-Migration Tool")
    print("=" * 80)
    print()

    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
        print()

    # Scope description
    if args.document_id:
        scope = f"Document ID: {args.document_id}"
    elif args.project_id:
        scope = f"Project ID: {args.project_id}"
    else:
        scope = "ALL documents"

    print(f"📋 Scope: {scope}")
    print(f"🌐 Language: {args.language}")
    print()

    async with AsyncSessionLocal() as db:
        # Get statistics before
        print("📊 Statistics BEFORE migration:")
        print("-" * 80)
        stats_before = await get_migration_stats(db, args.document_id, args.project_id)

        print(f"   Documents: {stats_before['documents']}")
        print(f"   Chunks: {stats_before['chunks']}")
        print(f"   Total Entities: {stats_before['entities']}")
        print(f"   Unique Entities: {stats_before['unique_entities']}")

        if stats_before['entities'] > 0:
            dedup_ratio = (1 - stats_before['unique_entities'] / stats_before['entities']) * 100
            print(f"   Deduplication Ratio: {dedup_ratio:.1f}%")

        if stats_before['chunks'] == 0:
            print("\n⚠️  No chunks found to migrate!")
            return

        if args.dry_run:
            print("\n🔍 DRY RUN: Would re-migrate these projects with new spaCy NER")
            print("   Run without --dry-run to actually perform migration")
            return

        # Confirm action
        print("\n⚠️  WARNING: This will DELETE existing entities and re-extract them!")
        print("   This operation cannot be undone.")

        response = input("\nProceed with re-migration? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Migration cancelled")
            return

        # Clear existing entities
        print("\n🗑️  Clearing existing entities...")
        deleted_count = await clear_entities(db, args.document_id, args.project_id)
        print(f"   Deleted {deleted_count} entities")

        # Re-migrate projects
        migrated_count = await remigrate_projects(db, args.document_id, args.project_id, args.language)

        # Get statistics after
        print("\n📊 Statistics AFTER migration:")
        print("-" * 80)
        stats_after = await get_migration_stats(db, args.document_id, args.project_id)

        print(f"   Documents: {stats_after['documents']}")
        print(f"   Chunks: {stats_after['chunks']}")
        print(f"   Total Entities: {stats_after['entities']}")
        print(f"   Unique Entities: {stats_after['unique_entities']}")

        if stats_after['entities'] > 0:
            dedup_ratio = (1 - stats_after['unique_entities'] / stats_after['entities']) * 100
            print(f"   Deduplication Ratio: {dedup_ratio:.1f}%")

        # Show comparison
        print("\n📈 Comparison:")
        print("-" * 80)

        entity_diff = stats_after['entities'] - stats_before['entities']
        unique_diff = stats_after['unique_entities'] - stats_before['unique_entities']

        print(f"   Total Entities: {stats_before['entities']} → {stats_after['entities']} ({entity_diff:+d})")
        print(f"   Unique Entities: {stats_before['unique_entities']} → {stats_after['unique_entities']} ({unique_diff:+d})")

        if stats_before['entities'] > 0 and stats_after['entities'] > 0:
            old_dedup = (1 - stats_before['unique_entities'] / stats_before['entities']) * 100
            new_dedup = (1 - stats_after['unique_entities'] / stats_after['entities']) * 100
            dedup_diff = new_dedup - old_dedup
            print(f"   Deduplication: {old_dedup:.1f}% → {new_dedup:.1f}% ({dedup_diff:+.1f}%)")

        print("\n✅ Re-migration completed successfully!")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
