"""
KnowledgeTree Backend - Search Service
Vector similarity search using pgvector + BM25 sparse retrieval

TIER 1 Advanced RAG: Added BM25 sparse search capability
"""

import logging
import time
import json
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, text
from sqlalchemy.orm import joinedload

from models.chunk import Chunk
from models.document import Document
from services.embedding_generator import EmbeddingGenerator
from services.bm25_service import bm25_service
from services.cross_encoder_service import cross_encoder_service
from services.reranking_optimizer import reranking_optimizer
from services.explainability_service import explainability_service
from services.query_expansion_service import query_expansion_service
from services.crag_service import crag_service

logger = logging.getLogger(__name__)


class SearchService:
    """Hybrid search service with dense (vector) and sparse (BM25) retrieval"""

    def __init__(self):
        self.embedding_generator = EmbeddingGenerator()
        self.bm25_service = bm25_service
        self.cross_encoder_service = cross_encoder_service
        self._hybrid_service = None  # Lazy initialization to avoid circular import

    def _get_hybrid_service(self):
        """Lazy initialization of HybridSearchService to avoid circular imports."""
        if self._hybrid_service is None:
            from services.hybrid_search_service import HybridSearchService
            self._hybrid_service = HybridSearchService(self)
        return self._hybrid_service

    async def search(
        self,
        db: AsyncSession,
        query: str,
        project_id: int,
        limit: int = 10,
        min_similarity: float = 0.5,
        category_id: Optional[int] = None
    ) -> tuple[List[dict], float]:
        """
        Perform semantic search using vector similarity

        Args:
            db: Database session
            query: Search query text
            project_id: Project to search within
            limit: Maximum number of results
            min_similarity: Minimum similarity threshold (0-1)
            category_id: Optional category filter

        Returns:
            Tuple of (results list, execution time in ms)
        """
        start_time = time.time()

        # Step 1: Generate embedding for query
        logger.info(f"Generating embedding for query: {query[:50]}...")
        query_embedding = self.embedding_generator.generate_embedding(query)

        # Step 2: Build vector similarity query
        # Using cosine similarity: 1 - (embedding <=> query_embedding)
        # pgvector <=> operator returns cosine distance, so we convert to similarity
        similarity_expr = text("1 - (embedding <=> :query_embedding)")

        # Build base query
        stmt = (
            select(
                Chunk.id.label("chunk_id"),
                Chunk.text.label("chunk_text"),
                Chunk.chunk_index,
                Chunk.chunk_metadata,
                Chunk.document_id,
                Document.title.label("document_title"),
                Document.filename.label("document_filename"),
                Document.created_at.label("document_created_at"),
                similarity_expr.label("similarity_score")
            )
            .join(Document, Chunk.document_id == Document.id)
            .where(
                and_(
                    Document.project_id == project_id,
                    Chunk.has_embedding == 1,
                    similarity_expr >= min_similarity
                )
            )
            .order_by(text("similarity_score DESC"))
            .limit(limit)
        )

        # Add category filter if specified
        if category_id is not None:
            stmt = stmt.where(Document.category_id == category_id)

        # Step 3: Execute query
        logger.info(f"Executing vector search with limit={limit}, min_similarity={min_similarity}")
        result = await db.execute(
            stmt,
            {"query_embedding": query_embedding}
        )
        rows = result.fetchall()

        # Step 4: Format results
        results = []
        for row in rows:
            # Parse chunk metadata
            chunk_metadata = None
            if row.chunk_metadata:
                try:
                    chunk_metadata = json.loads(row.chunk_metadata)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse chunk metadata for chunk {row.chunk_id}")

            results.append({
                "chunk_id": row.chunk_id,
                "document_id": row.document_id,
                "document_title": row.document_title,
                "document_filename": row.document_filename,
                "chunk_text": row.chunk_text,
                "chunk_index": row.chunk_index,
                "similarity_score": float(row.similarity_score),
                "chunk_metadata": chunk_metadata,
                "document_created_at": row.document_created_at,
            })

        execution_time = (time.time() - start_time) * 1000  # Convert to ms
        logger.info(f"Search completed: {len(results)} results in {execution_time:.2f}ms")

        return results, execution_time

    async def get_statistics(
        self,
        db: AsyncSession,
        project_id: int
    ) -> dict:
        """
        Get search statistics for a project

        Args:
            db: Database session
            project_id: Project to get statistics for

        Returns:
            Dictionary with statistics
        """
        # Count total documents
        doc_count_result = await db.execute(
            select(func.count(Document.id))
            .where(Document.project_id == project_id)
        )
        total_documents = doc_count_result.scalar()

        # Count total chunks
        chunk_count_result = await db.execute(
            select(func.count(Chunk.id))
            .join(Document, Chunk.document_id == Document.id)
            .where(Document.project_id == project_id)
        )
        total_chunks = chunk_count_result.scalar()

        # Count embedded chunks
        embedded_count_result = await db.execute(
            select(func.count(Chunk.id))
            .join(Document, Chunk.document_id == Document.id)
            .where(
                and_(
                    Document.project_id == project_id,
                    Chunk.has_embedding == 1
                )
            )
        )
        embedded_chunks = embedded_count_result.scalar()

        # Calculate average chunk length
        avg_length_result = await db.execute(
            select(func.avg(func.length(Chunk.text)))
            .join(Document, Chunk.document_id == Document.id)
            .where(Document.project_id == project_id)
        )
        avg_length = avg_length_result.scalar() or 0.0

        # Estimate storage size (1024 dimensions * 4 bytes per float32)
        vector_size_bytes = embedded_chunks * 1024 * 4
        total_storage_mb = vector_size_bytes / (1024 * 1024)

        return {
            "total_documents": total_documents or 0,
            "total_chunks": total_chunks or 0,
            "embedded_chunks": embedded_chunks or 0,
            "average_chunk_length": float(avg_length),
            "total_storage_mb": round(total_storage_mb, 2),
        }

    async def search_sparse(
        self,
        db: AsyncSession,
        query: str,
        project_id: int,
        limit: int = 20,
        min_score: float = 0.0
    ) -> tuple[List[dict], float]:
        """
        Perform sparse retrieval using BM25 keyword matching.

        Part of TIER 1 Advanced RAG implementation.
        Complements dense vector search with exact keyword matching.

        Args:
            db: Database session
            query: Search query text
            project_id: Project to search within
            limit: Maximum number of results
            min_score: Minimum BM25 score threshold

        Returns:
            Tuple of (results list, execution time in ms)
        """
        start_time = time.time()

        if not self.bm25_service.is_initialized:
            logger.warning("⚠️ BM25 service not initialized - returning empty results")
            return [], 0.0

        # Perform BM25 search (over-fetch to compensate for project filtering)
        bm25_results = await self.bm25_service.search(
            query=query,
            top_k=limit * 3,
            min_score=min_score
        )

        # Get document IDs and metadata for this project (single query)
        doc_info_result = await db.execute(
            select(Document.id, Document.title, Document.filename, Document.created_at)
            .where(Document.project_id == project_id)
        )
        doc_info_map = {
            row[0]: {"title": row[1], "filename": row[2], "created_at": row[3]}
            for row in doc_info_result.fetchall()
        }
        project_doc_ids = set(doc_info_map.keys())

        # Filter results to only include chunks from this project
        filtered_results = []
        for result in bm25_results:
            if result["document_id"] not in project_doc_ids:
                continue

            doc_info = doc_info_map[result["document_id"]]

            filtered_results.append({
                "chunk_id": result["id"],
                "document_id": result["document_id"],
                "document_title": doc_info["title"] or result.get("title"),
                "document_filename": doc_info["filename"] or "",
                "chunk_text": result["content"],
                "chunk_index": result.get("chunk_index", 0),
                "similarity_score": result["score"],
                "chunk_metadata": result.get("chunk_metadata"),
                "document_created_at": doc_info["created_at"],
                "source": "sparse"
            })

            if len(filtered_results) >= limit:
                break

        execution_time = (time.time() - start_time) * 1000  # Convert to ms
        logger.info(
            f"Sparse search completed: {len(filtered_results)} results in {execution_time:.2f}ms "
            f"(query: '{query[:50]}...')"
        )

        return filtered_results, execution_time

    async def hybrid_search(
        self,
        db: AsyncSession,
        query: str,
        project_id: int,
        limit: int = 10,
        top_k_retrieve: int = 20,
        min_similarity: float = 0.5,
        min_bm25_score: float = 0.0,
        dense_weight: Optional[float] = None,
        sparse_weight: Optional[float] = None,
        category_id: Optional[int] = None
    ) -> tuple[List[dict], float]:
        """
        Perform hybrid search with dense + sparse retrieval and RRF fusion.

        TIER 1 Advanced RAG - Combines semantic and keyword search.

        Args:
            db: Database session
            query: Search query text
            project_id: Project to search within
            limit: Final number of results to return
            top_k_retrieve: Number of candidates from each method
            min_similarity: Minimum similarity for dense search
            min_bm25_score: Minimum BM25 score for sparse search
            dense_weight: Override default dense weight (0.6)
            sparse_weight: Override default sparse weight (0.4)
            category_id: Optional category filter

        Returns:
            Tuple of (results list with RRF scores, execution time in ms)
        """
        hybrid_service = self._get_hybrid_service()
        return await hybrid_service.search(
            db=db,
            query=query,
            project_id=project_id,
            limit=limit,
            top_k_retrieve=top_k_retrieve,
            min_similarity=min_similarity,
            min_bm25_score=min_bm25_score,
            dense_weight=dense_weight,
            sparse_weight=sparse_weight,
            category_id=category_id
        )

    async def search_with_reranking(
        self,
        db: AsyncSession,
        query: str,
        project_id: int,
        limit: int = 5,
        retrieval_limit: int = 20,
        min_similarity: float = 0.5,
        min_bm25_score: float = 0.0,
        min_cross_encoder_score: float = 0.0,
        dense_weight: Optional[float] = None,
        sparse_weight: Optional[float] = None,
        category_id: Optional[int] = None,
        use_query_expansion: bool = True,
        expansion_strategy: str = "balanced",
        use_crag: bool = True
    ) -> tuple[List[dict], float]:
        """
        Complete TIER 1 Advanced RAG pipeline: Hybrid Search + Cross-Encoder Reranking

        Three-stage retrieval pipeline:
        1. Hybrid retrieval (dense + sparse + RRF) → top-20 candidates
        2. Cross-encoder reranking → precise relevance scoring
        3. Return top-k most relevant results

        This is the most accurate search method, combining:
        - Dense retrieval (semantic understanding)
        - Sparse retrieval (keyword matching)
        - RRF fusion (balanced ranking)
        - Cross-encoder (precise relevance scoring)

        Args:
            db: Database session
            query: Search query text
            project_id: Project to search within
            limit: Final number of results to return (default: 5)
            retrieval_limit: Candidates from hybrid search (default: 20)
            min_similarity: Minimum similarity for dense search
            min_bm25_score: Minimum BM25 score for sparse search
            min_cross_encoder_score: Minimum cross-encoder score threshold
            dense_weight: Override dense weight (default: 0.6)
            sparse_weight: Override sparse weight (default: 0.4)
            category_id: Optional category filter

        Returns:
            Tuple of (reranked results, execution time in ms)

        Example:
            results, time = await search_service.search_with_reranking(
                db, "JWT authentication", project_id=1, limit=5
            )
        """
        start_time = time.time()

        # Step 0.5: TIER 2 Phase 3 - Query Expansion
        original_query = query
        expanded_query_obj = None

        if use_query_expansion:
            logger.info(f"🔍 TIER 2 Query Expansion: expanding query '{query[:50]}...'")
            expanded_query_obj = query_expansion_service.expand_query(
                query=query,
                expansion_strategy=expansion_strategy
            )

            # Use expanded query for sparse search (keywords benefit from expansion)
            # Keep original for dense search (embeddings capture semantic meaning)
            expanded_query_str = query_expansion_service.generate_expanded_query_string(
                expanded=expanded_query_obj,
                include_synonyms=True,
                include_entities=True
            )

            logger.info(
                f"📝 Expanded query: {len(expanded_query_obj.expanded_terms)} terms, "
                f"{len(expanded_query_obj.reformulated_queries)} reformulations"
            )

            # Use expanded query for BM25 search
            query = expanded_query_str

        # Step 1: Hybrid retrieval (dense + sparse + RRF)
        logger.info(
            f"🔀 TIER 1 Complete Pipeline: query='{query[:50]}...', "
            f"retrieval_limit={retrieval_limit}, final_limit={limit}"
        )

        hybrid_results, _ = await self.hybrid_search(
            db=db,
            query=query,
            project_id=project_id,
            limit=retrieval_limit,
            top_k_retrieve=retrieval_limit,
            min_similarity=min_similarity,
            min_bm25_score=min_bm25_score,
            dense_weight=dense_weight,
            sparse_weight=sparse_weight,
            category_id=category_id
        )

        if not hybrid_results:
            logger.warning("⚠️ No results from hybrid search - returning empty")
            return [], 0.0

        # Step 1.3: TIER 2 Phase 4 - CRAG (Corrective RAG)
        # Evaluate retrieval quality and apply corrective actions
        crag_evaluation = None
        crag_correction = None

        if use_crag:
            logger.info("🔍 TIER 2 CRAG: Evaluating retrieval quality")
            crag_evaluation = crag_service.evaluate_retrieval_quality(
                results=hybrid_results,
                score_field="rrf_score"
            )

            if crag_evaluation.should_apply_correction:
                logger.info(
                    f"🔧 TIER 2 CRAG: Applying correction - "
                    f"action={crag_evaluation.corrective_action.value}"
                )
                crag_correction = crag_service.apply_corrective_action(
                    results=hybrid_results,
                    evaluation=crag_evaluation,
                    query=query,
                    score_field="rrf_score"
                )

                # Use corrected results
                hybrid_results = crag_correction.corrected_results

                logger.info(
                    f"✅ TIER 2 CRAG: Correction applied - "
                    f"results: {crag_correction.improvement_metrics.get('original_count')} → "
                    f"{crag_correction.improvement_metrics.get('corrected_count')}"
                )

        # Step 1.5: TIER 2 Phase 1 - Conditional Reranking Optimization
        # Analyze RRF results and decide whether to skip cross-encoder reranking
        should_skip, skip_metrics = reranking_optimizer.should_skip_reranking(
            results=hybrid_results,
            score_field="rrf_score"
        )

        # Add confidence metrics to all results
        confidence_level = reranking_optimizer.get_confidence_level(skip_metrics)
        for result in hybrid_results:
            result["confidence_level"] = confidence_level
            result["skip_metrics"] = skip_metrics

            # TIER 2 Phase 3: Add query expansion metadata
            if expanded_query_obj:
                result["query_expansion"] = {
                    "used": True,
                    "original_query": original_query,
                    "expanded_terms_count": len(expanded_query_obj.expanded_terms),
                    "entities_found": expanded_query_obj.entities,
                    "expansion_strategy": expansion_strategy
                }
            else:
                result["query_expansion"] = {"used": False}

            # TIER 2 Phase 4: Add CRAG metadata
            if crag_evaluation:
                result["crag_evaluation"] = {
                    "quality_level": crag_evaluation.quality_level.value,
                    "confidence_score": crag_evaluation.confidence_score,
                    "corrective_action": crag_evaluation.corrective_action.value,
                    "reasoning": crag_evaluation.reasoning,
                    "correction_applied": crag_evaluation.should_apply_correction
                }
                if crag_correction:
                    result["crag_improvement"] = crag_correction.improvement_metrics
            else:
                result["crag_evaluation"] = {"used": False}

        if should_skip:
            # TIER 2 Optimization: Skip reranking for simple queries (30-50% latency reduction)
            logger.info(
                f"⚡ TIER 2 Optimization: Skipped cross-encoder reranking "
                f"(reason: {skip_metrics['skip_reason']})"
            )
            # Return top-k results from RRF directly
            final_results = hybrid_results[:limit]

            # TIER 2 Phase 2: Add explanations
            final_results = explainability_service.explain_results(
                results=final_results,
                query=query,
                pipeline_type="hybrid"
            )

            execution_time = (time.time() - start_time) * 1000  # Convert to ms

            logger.info(
                f"✅ TIER 2 Optimized Pipeline finished: {len(final_results)} results in {execution_time:.2f}ms "
                f"(hybrid only, skipped reranking - saved ~{200}ms)"
            )

            return final_results, execution_time

        # Step 2: Cross-encoder reranking (applied only if needed)
        logger.info("🔄 Applying cross-encoder reranking (confidence not sufficient)")
        reranked_results = await self.cross_encoder_service.rerank(
            query=query,
            results=hybrid_results,
            top_k=limit,
            min_score=min_cross_encoder_score
        )

        # Preserve confidence metrics in reranked results
        for result in reranked_results:
            result["confidence_level"] = confidence_level
            result["skip_metrics"] = skip_metrics

        # TIER 2 Phase 2: Add explanations
        reranked_results = explainability_service.explain_results(
            results=reranked_results,
            query=query,
            pipeline_type="reranked"
        )

        execution_time = (time.time() - start_time) * 1000  # Convert to ms

        logger.info(
            f"✅ TIER 1+2 Complete Pipeline finished: {len(reranked_results)} results in {execution_time:.2f}ms "
            f"(hybrid: {len(hybrid_results)} → reranked: {len(reranked_results)})"
        )

        return reranked_results, execution_time

    async def rerank_results(
        self,
        results: List[dict],
        query: str,
        boost_recent: bool = True,
        recency_weight: float = 0.1
    ) -> List[dict]:
        """
        Re-rank search results with additional signals

        Args:
            results: Initial search results
            query: Original search query
            boost_recent: Whether to boost recent documents
            recency_weight: Weight for recency signal (0-1)

        Returns:
            Re-ranked results
        """
        if not results or not boost_recent:
            return results

        # Find newest document timestamp
        newest_timestamp = max(r["document_created_at"].timestamp() for r in results)

        # Calculate combined scores
        for result in results:
            similarity = result["similarity_score"]

            # Recency signal (0-1, newer = higher)
            doc_timestamp = result["document_created_at"].timestamp()
            recency_signal = doc_timestamp / newest_timestamp if newest_timestamp > 0 else 0.0

            # Combined score
            combined_score = (
                similarity * (1 - recency_weight) +
                recency_signal * recency_weight
            )
            result["combined_score"] = combined_score

        # Sort by combined score
        results.sort(key=lambda x: x["combined_score"], reverse=True)

        return results
