"""
KnowledgeTree - Web Crawl Tree Generator
Generate category trees from agentic crawl entities and insights
"""

import json
import logging
from typing import List, Dict, Tuple
from collections import defaultdict
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.chunk import Chunk
from models.category import Category

logger = logging.getLogger(__name__)


# Entity type translations
ENTITY_TYPE_NAMES = {
    "product": "Produkty i Modele",
    "organization": "Firmy i Organizacje",
    "concept": "Koncepcje",
    "technology": "Technologie",
    "person": "Osoby",
    "location": "Lokalizacje",
    "other": "Pozostałe Encje"
}

# Insight importance translations
IMPORTANCE_NAMES = {
    "high": "Kluczowe Informacje",
    "medium": "Dodatkowe Informacje",
    "low": "Szczegóły"
}


async def generate_tree_from_web_crawl(
    document_id: int,
    project_id: int,
    db: AsyncSession,
    parent_id: int | None = None
) -> Tuple[List[Category], Dict]:
    """
    Generate category tree from web crawl entities and insights

    Args:
        document_id: Document ID to generate tree for
        project_id: Project ID for multi-tenant isolation
        db: Database session
        parent_id: Optional parent category ID

    Returns:
        Tuple of (categories_list, stats_dict)

    Raises:
        ValueError: If no structured data found
    """

    # Step 1: Fetch all chunks with entities and insights
    logger.info(f"Fetching structured chunks for document {document_id}")
    result = await db.execute(
        select(Chunk)
        .where(
            Chunk.document_id == document_id,
            or_(
                Chunk.text.like('[ENTITY]%'),
                Chunk.text.like('[INSIGHT]%')
            )
        )
        .order_by(Chunk.chunk_index)
    )
    chunks = result.scalars().all()

    if not chunks:
        raise ValueError(
            "Brak danych strukturalnych w dokumencie. "
            "Dokument nie zawiera wyciągniętych entities ani insights. "
            "Spróbuj uruchomić ponownie agentic crawl dla tego URL."
        )

    logger.info(f"Found {len(chunks)} structured chunks")

    # Step 2: Parse and group chunks by type
    entities_by_type = defaultdict(list)
    insights_by_importance = defaultdict(list)
    skipped = 0

    for chunk in chunks:
        try:
            if not chunk.chunk_metadata:
                skipped += 1
                continue

            metadata = json.loads(chunk.chunk_metadata)
            chunk_type = metadata.get("type")

            if chunk_type == "entity":
                entity_type = metadata.get("entity_type", "other")
                entities_by_type[entity_type].append(chunk)

            elif chunk_type == "insight":
                importance = metadata.get("importance", "medium")
                insights_by_importance[importance].append(chunk)

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Skipping chunk {chunk.id} - invalid metadata: {e}")
            skipped += 1
            continue

    if skipped > 0:
        logger.warning(f"Skipped {skipped} chunks due to invalid metadata")

    # Step 3: Create root category
    logger.info("Creating category tree structure")
    root = Category(
        name="Struktura Wiedzy",
        depth=0,
        parent_id=parent_id,
        project_id=project_id
    )
    db.add(root)
    await db.flush()  # Get root.id

    categories = [root]
    chunk_assignments = {}  # category -> [chunks]

    # Step 4: Create subcategories for entities
    for entity_type, entity_chunks in entities_by_type.items():
        if not entity_chunks:
            continue

        category_name = ENTITY_TYPE_NAMES.get(entity_type, entity_type.title())
        count = len(entity_chunks)

        cat = Category(
            name=f"{category_name}: {count} element{'ów' if count != 1 else ''}",
            depth=1,
            parent_id=root.id,
            project_id=project_id
        )
        db.add(cat)
        categories.append(cat)
        chunk_assignments[cat] = entity_chunks

    # Step 5: Create subcategories for insights
    for importance, insight_chunks in insights_by_importance.items():
        if not insight_chunks:
            continue

        category_name = IMPORTANCE_NAMES.get(importance, importance.title())
        count = len(insight_chunks)

        cat = Category(
            name=f"{category_name}: {count} element{'ów' if count != 1 else ''}",
            depth=1,
            parent_id=root.id,
            project_id=project_id
        )
        db.add(cat)
        categories.append(cat)
        chunk_assignments[cat] = insight_chunks

    # Flush to get all category IDs
    await db.flush()

    # Step 6: Assign chunks to categories
    logger.info("Assigning chunks to categories")
    assigned_count = 0
    for category, chunk_list in chunk_assignments.items():
        for chunk in chunk_list:
            chunk.category_id = category.id
            assigned_count += 1

    await db.commit()

    # Step 7: Generate stats
    stats = {
        "categories_created": len(categories),
        "tree_depth": 1,  # Root + subcategories
        "root_category_id": root.id,
        "chunks_assigned": assigned_count,
        "entities_by_type": {k: len(v) for k, v in entities_by_type.items()},
        "insights_by_importance": {k: len(v) for k, v in insights_by_importance.items()},
        "total_entities": sum(len(v) for v in entities_by_type.values()),
        "total_insights": sum(len(v) for v in insights_by_importance.values())
    }

    logger.info(f"✅ Generated tree: {len(categories)} categories, {assigned_count} chunks assigned")
    logger.info(f"   Entities: {stats['total_entities']}, Insights: {stats['total_insights']}")

    return categories, stats
