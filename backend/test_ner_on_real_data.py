"""
Test NER improvements on real document data from database
Compare old pattern-based NER vs new spaCy NER
"""

import sys
import os
import asyncio
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import AsyncSessionLocal
from models.document import Document
from models.chunk import Chunk
from models.entity import Entity
from services.spacy_ner_service import SpacyNERService
from services.entity_migrator import EntityMigrator


async def get_database_stats():
    """Get current database statistics"""
    print("=" * 80)
    print("📊 Current Database Statistics")
    print("=" * 80)

    async with AsyncSessionLocal() as db:
        # Count documents
        result = await db.execute(select(func.count(Document.id)))
        doc_count = result.scalar()

        # Count chunks
        result = await db.execute(select(func.count(Chunk.id)))
        chunk_count = result.scalar()

        # Count entities
        result = await db.execute(select(func.count(Entity.id)))
        entity_count = result.scalar()

        # Count unique entity names
        result = await db.execute(select(func.count(func.distinct(Entity.name))))
        unique_entity_count = result.scalar()

        print(f"\n📄 Documents: {doc_count}")
        print(f"📦 Chunks: {chunk_count}")
        print(f"🏷️  Total Entities: {entity_count}")
        print(f"✨ Unique Entities: {unique_entity_count}")

        if entity_count > 0:
            dedup_ratio = (1 - unique_entity_count / entity_count) * 100
            print(f"📉 Deduplication Ratio: {dedup_ratio:.1f}%")

        return doc_count, chunk_count, entity_count


async def get_sample_chunks(limit: int = 5):
    """Get sample document chunks for testing"""
    async with AsyncSessionLocal() as db:
        # Get chunks with some content
        result = await db.execute(
            select(Chunk)
            .where(func.length(Chunk.text) > 500)
            .limit(limit)
        )
        chunks = result.scalars().all()
        return chunks


async def compare_ner_methods(chunk_text: str, language: str = 'en'):
    """Compare old pattern-based NER vs new spaCy NER"""

    print("\n" + "=" * 80)
    print(f"📝 Text Sample ({len(chunk_text)} chars):")
    print("=" * 80)
    print(f"{chunk_text[:300]}...")
    print()

    # Test new spaCy NER
    print("🆕 NEW: spaCy NER with deduplication")
    print("-" * 80)
    spacy_ner = SpacyNERService(default_language=language, fuzzy_threshold=0.85)

    # Without deduplication
    entities_raw = spacy_ner.extract_entities(chunk_text, language=language, deduplicate=False)
    print(f"Raw entities: {len(entities_raw)}")
    for name, etype in entities_raw[:10]:  # Show first 10
        print(f"   - {name:40s} [{etype}]")
    if len(entities_raw) > 10:
        print(f"   ... and {len(entities_raw) - 10} more")

    # With deduplication
    entities_dedup = spacy_ner.extract_entities(chunk_text, language=language, deduplicate=True)
    print(f"\nDeduplicated entities: {len(entities_dedup)}")
    for name, etype in entities_dedup[:10]:
        print(f"   - {name:40s} [{etype}]")
    if len(entities_dedup) > 10:
        print(f"   ... and {len(entities_dedup) - 10} more")

    # Calculate deduplication effectiveness
    if len(entities_raw) > 0:
        reduction = (1 - len(entities_dedup) / len(entities_raw)) * 100
        print(f"\n📊 Deduplication: {len(entities_raw)} → {len(entities_dedup)} ({reduction:.1f}% reduction)")

    # Test old pattern-based NER for comparison
    print("\n🔙 OLD: Pattern-based NER (fallback)")
    print("-" * 80)
    async with AsyncSessionLocal() as db:
        migrator = EntityMigrator(db, use_spacy=False)  # Disable spaCy to test old method
        old_entities = migrator._extract_entities_from_text(chunk_text)

    print(f"Entities found: {len(old_entities)}")
    for name, etype in old_entities[:10]:
        print(f"   - {name:40s} [{etype}]")
    if len(old_entities) > 10:
        print(f"   ... and {len(old_entities) - 10} more")

    # Comparison summary
    print("\n📈 Comparison Summary:")
    print(f"   Old method: {len(old_entities)} entities")
    print(f"   New method (raw): {len(entities_raw)} entities")
    print(f"   New method (dedup): {len(entities_dedup)} entities")

    if len(old_entities) > 0:
        improvement = ((len(entities_raw) - len(old_entities)) / len(old_entities)) * 100
        print(f"   Detection improvement: {improvement:+.1f}%")

    return entities_raw, entities_dedup, old_entities


async def test_fuzzy_thresholds(chunk_text: str, thresholds: list = [0.70, 0.75, 0.80, 0.85, 0.90]):
    """Test different fuzzy deduplication thresholds"""

    print("\n" + "=" * 80)
    print("🔀 Testing Fuzzy Deduplication Thresholds")
    print("=" * 80)

    results = []

    for threshold in thresholds:
        ner = SpacyNERService(fuzzy_threshold=threshold)

        # Extract without dedup first
        entities_raw = ner.extract_entities(chunk_text, deduplicate=False)

        # Apply fuzzy dedup with specific threshold
        entities_dedup = ner.fuzzy_deduplicate(entities_raw, threshold=threshold)

        reduction = (1 - len(entities_dedup) / max(1, len(entities_raw))) * 100

        results.append({
            'threshold': threshold,
            'raw': len(entities_raw),
            'dedup': len(entities_dedup),
            'reduction': reduction
        })

        print(f"Threshold {threshold:.2f}: {len(entities_raw)} → {len(entities_dedup)} ({reduction:.1f}% reduction)")

    # Find optimal threshold
    print("\n🎯 Optimal Threshold Analysis:")
    for r in results:
        effectiveness = "⭐⭐⭐" if 15 <= r['reduction'] <= 40 else ("⭐⭐" if 5 <= r['reduction'] < 50 else "⭐")
        print(f"   {r['threshold']:.2f}: {r['reduction']:5.1f}% reduction {effectiveness}")

    return results


async def main():
    """Main test function"""
    print("\n🚀 Testing NER Improvements on Real Data")
    print("=" * 80)
    print()

    # Get database statistics
    doc_count, chunk_count, entity_count = await get_database_stats()

    if chunk_count == 0:
        print("\n⚠️  No document chunks found in database!")
        print("   Please upload some documents first to test NER on real data.")
        return

    print(f"\n📦 Testing on {min(3, chunk_count)} sample chunks...")

    # Get sample chunks
    chunks = await get_sample_chunks(limit=3)

    if not chunks:
        print("\n⚠️  No suitable chunks found (need chunks with >500 characters)")
        return

    # Test each chunk
    for i, chunk in enumerate(chunks, 1):
        print(f"\n{'='*80}")
        print(f"🔍 CHUNK {i}/{len(chunks)} (ID: {chunk.id})")
        print(f"{'='*80}")

        # Detect language (simple heuristic)
        language = 'pl' if any(word in chunk.text.lower() for word in ['jest', 'oraz', 'który', 'przez']) else 'en'
        print(f"Detected language: {language}")

        # Compare NER methods
        raw, dedup, old = await compare_ner_methods(chunk.text, language=language)

    # Test fuzzy thresholds on first chunk
    if chunks:
        print("\n" + "=" * 80)
        print("🔧 Fuzzy Threshold Optimization")
        print("=" * 80)
        print(f"\nTesting on first chunk (ID: {chunks[0].id})")

        await test_fuzzy_thresholds(chunks[0].text)

    # Final summary
    print("\n" + "=" * 80)
    print("✅ Testing Complete!")
    print("=" * 80)
    print("\n📋 Recommendations:")
    print("   1. Review entity detection quality above")
    print("   2. Check if deduplication is too aggressive or too conservative")
    print("   3. Adjust fuzzy_threshold based on threshold analysis")
    print("   4. Consider re-migrating existing documents with new NER")
    print()


if __name__ == "__main__":
    asyncio.run(main())
