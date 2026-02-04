"""
KnowledgeTree - Web Crawl Tree Generator
Generate category trees from agentic crawl entities and insights
"""

import json
import logging
from typing import List, Dict, Tuple
from collections import defaultdict
from sqlalchemy import select, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from models.chunk import Chunk
from models.category import Category

logger = logging.getLogger(__name__)


def _find_overlap_length(text1: str, text2: str, max_search: int = 300) -> int:
    """
    Find length of overlapping text between end of text1 and start of text2.

    Text chunker creates chunks with 200-char overlap, so consecutive chunks
    share content that needs to be deduplicated for smooth reading.

    Args:
        text1: First text (we check its end)
        text2: Second text (we check its beginning)
        max_search: Maximum characters to search for overlap

    Returns:
        Number of characters of overlap (0 if no significant overlap found)

    Example:
        text1 = "...making incremental progress in every session"
        text2 = "in every session, while leaving clear artifacts..."
        Returns: 20 (length of "in every session")
    """
    if not text1 or not text2:
        return 0

    # Search in last max_search chars of text1
    search_start = max(0, len(text1) - max_search)
    search_text = text1[search_start:]

    # Try to find longest match, starting from longest possible
    # Minimum 10 chars to avoid false positives from short words
    for overlap_len in range(len(search_text), 9, -1):
        suffix = search_text[-overlap_len:]
        if text2.startswith(suffix):
            logger.debug(f"Found overlap of {overlap_len} chars: '{suffix[:50]}...'")
            return overlap_len

    return 0


def _merge_article_chunks(chunks: List[Chunk]) -> str:
    """
    Intelligently merge article chunks into coherent text with overlap removal.

    Text chunker creates chunks with ~1000 chars and 200-char overlap.
    This function:
    1. Removes duplicate headers/source URLs
    2. Detects and removes overlap between consecutive chunks
    3. Joins text smoothly for reading experience

    Args:
        chunks: List of chunks for a single article

    Returns:
        Merged article content as markdown with smooth reading flow
    """
    if not chunks:
        return ""

    # Sort chunks by position in article
    sorted_chunks = sorted(
        chunks,
        key=lambda c: json.loads(c.chunk_metadata).get('chunk_in_article', 0)
    )

    # Extract header and source URL from first chunk ONCE
    first_chunk_text = sorted_chunks[0].text.strip()
    lines = first_chunk_text.split('\n')

    header = ""
    source_url = ""
    for line in lines[:5]:
        if line.startswith('# '):
            header = line
        elif line.startswith('Źródło:'):
            source_url = line

    # Remove header and source from all chunks
    clean_chunks = []
    for chunk in sorted_chunks:
        chunk_text = chunk.text.strip()

        # Remove header if present
        if header:
            chunk_text = chunk_text.replace(header, '', 1)  # Remove first occurrence
        # Remove source URL if present
        if source_url:
            chunk_text = chunk_text.replace(source_url, '', 1)

        # Clean up extra newlines and whitespace
        chunk_text = chunk_text.strip()

        if chunk_text:
            clean_chunks.append(chunk_text)

    if not clean_chunks:
        return ""

    # De-overlap and merge chunks intelligently
    merged_content = clean_chunks[0]

    for i in range(1, len(clean_chunks)):
        current_chunk = clean_chunks[i]

        # Find overlap between end of merged content and start of current chunk
        overlap_len = _find_overlap_length(merged_content, current_chunk)

        if overlap_len > 0:
            # Add only non-overlapping part
            non_overlapping = current_chunk[overlap_len:]
            merged_content += non_overlapping
            logger.debug(f"Chunk {i}: removed {overlap_len} chars overlap")
        else:
            # No overlap found - add with space to avoid word concatenation
            merged_content += " " + current_chunk
            logger.debug(f"Chunk {i}: no overlap, added with space")

    # Combine: header + source + merged content
    result_parts = []
    if header:
        result_parts.append(header)
    if source_url:
        result_parts.append(source_url)

    result_parts.append(merged_content)

    return '\n\n'.join(result_parts)


async def _generate_from_article_structure(
    chunks: List[Chunk],
    project_id: int,
    parent_id: int | None,
    db: AsyncSession
) -> Tuple[List[Category], Dict]:
    """
    Generate category tree from article structure in chunk metadata

    Fallback method for web crawl documents that don't have entities/insights
    but have article structure metadata (source_url, article_title).

    Args:
        chunks: All chunks from document
        project_id: Project ID for multi-tenant isolation
        parent_id: Optional parent category ID
        db: Database session

    Returns:
        Tuple of (categories_list, stats_dict)
    """
    logger.info(f"Generating tree from article structure ({len(chunks)} chunks)")

    # Group chunks by article (source_url)
    articles = {}
    chunks_without_structure = 0

    for chunk in chunks:
        try:
            if not chunk.chunk_metadata:
                chunks_without_structure += 1
                continue

            metadata = json.loads(chunk.chunk_metadata)
            source_url = metadata.get('source_url')
            article_title = metadata.get('article_title')

            if not source_url or not article_title:
                chunks_without_structure += 1
                continue

            if source_url not in articles:
                articles[source_url] = {
                    'title': article_title,
                    'chunks': []
                }
            articles[source_url]['chunks'].append(chunk)

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Skipping chunk {chunk.id} - invalid metadata: {e}")
            chunks_without_structure += 1
            continue

    if not articles:
        raise ValueError(
            f"Brak struktury artykułów w dokumencie. "
            f"Sprawdzono {len(chunks)} chunków, ale żaden nie ma prawidłowej metadata "
            f"z source_url i article_title."
        )

    logger.info(f"Found {len(articles)} articles in document")

    # Create root category
    root = Category(
        name="Artykuły",
        depth=0,
        parent_id=parent_id,
        project_id=project_id
    )
    db.add(root)
    await db.flush()  # Get root.id

    categories = [root]
    total_assigned = 0

    # Create category for each article
    for article_url, article_data in articles.items():
        article_title = article_data['title']
        article_chunks = article_data['chunks']
        chunk_count = len(article_chunks)

        # Sort chunks by chunk_in_article if available
        try:
            article_chunks.sort(
                key=lambda c: json.loads(c.chunk_metadata).get('chunk_in_article', c.chunk_index)
            )
        except Exception:
            # Fallback to chunk_index
            article_chunks.sort(key=lambda c: c.chunk_index)

        # Merge chunks into full article content
        merged_article_text = _merge_article_chunks(article_chunks)
        
        # Create category for this article
        cat = Category(
            name=f"{article_title} ({chunk_count} fragment{'y' if chunk_count in [2,3,4] else 'ów'})",
            depth=1,
            parent_id=root.id,
            project_id=project_id,
            merged_content=merged_article_text  # Full article for UI display
        )
        db.add(cat)
        categories.append(cat)

    # Flush to get all category IDs
    await db.flush()

    # Assign chunks to categories
    for article_url, article_data in articles.items():
        # Find category for this article
        article_title = article_data['title']
        category = next(
            cat for cat in categories
            if cat.name.startswith(article_title)
        )

        for chunk in article_data['chunks']:
            chunk.category_id = category.id
            total_assigned += 1

    await db.commit()

    # Generate stats
    stats = {
        "categories_created": len(categories),
        "tree_depth": 1,
        "root_category_id": root.id,
        "chunks_assigned": total_assigned,
        "articles_found": len(articles),
        "chunks_without_metadata": chunks_without_structure,
        "source": "article_structure"
    }

    logger.info(f"✅ Generated tree from {len(articles)} articles, {total_assigned} chunks assigned")

    return categories, stats


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

    # Step 0: Clean up existing category trees for this document/project
    logger.info(f"Cleaning up existing category trees for project {project_id}")
    
    # Find all root categories with typical tree names
    roots_query = await db.execute(
        select(Category).where(
            Category.project_id == project_id,
            Category.parent_id.is_(None),
            or_(
                Category.name == "Artykuły",
                Category.name == "Struktura Wiedzy"
            )
        )
    )
    old_roots = roots_query.scalars().all()
    
    if old_roots:
        logger.info(f"Found {len(old_roots)} old category trees to delete")
        
        # Clear all chunk assignments for this document first
        chunks_result = await db.execute(
            select(Chunk).where(Chunk.document_id == document_id)
        )
        all_doc_chunks = chunks_result.scalars().all()
        for ch in all_doc_chunks:
            ch.category_id = None
        
        # Delete old root categories (CASCADE will delete children)
        for root in old_roots:
            await db.execute(delete(Category).where(Category.id == root.id))
        
        await db.flush()
    
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
        # Fallback: Try article structure from metadata
        logger.info("No entities/insights found, trying article structure fallback")

        result_all = await db.execute(
            select(Chunk)
            .where(Chunk.document_id == document_id)
            .order_by(Chunk.chunk_index)
        )
        all_chunks = result_all.scalars().all()

        if not all_chunks:
            raise ValueError(
                "Dokument nie zawiera żadnych chunków. "
                "Dokument nie został poprawnie przetworzony."
            )

        # Try to generate from article structure
        try:
            return await _generate_from_article_structure(
                chunks=all_chunks,
                project_id=project_id,
                db=db,
                parent_id=parent_id
            )
        except ValueError:
            # Article structure also failed
            raise ValueError(
                "Brak danych strukturalnych w dokumencie. "
                "Ten dokument nie zawiera ani wyciągniętych entities/insights, "
                "ani struktury artykułów w metadata. "
                f"Dokument ma {len(all_chunks)} chunków tekstowych."
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
