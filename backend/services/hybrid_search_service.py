"""
Hybrid Search Service with Reciprocal Rank Fusion (RRF)

Combines dense (vector) and sparse (BM25) retrieval using weighted RRF.
Part of TIER 1 Advanced RAG implementation.

Key Features:
- Parallel execution of dense + sparse search
- Reciprocal Rank Fusion (RRF) with k=60
- Configurable weights (default: 0.6 dense, 0.4 sparse)
- Unified result format
- Async interface

Reference: ALURON project hybrid RAG + RAG 2025 best practices
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class HybridSearchService:
    """
    Hybrid search combining dense (semantic) and sparse (keyword) retrieval.

    Uses Reciprocal Rank Fusion (RRF) to merge results from multiple sources:
    - Dense retrieval: BGE-M3 embeddings (semantic similarity)
    - Sparse retrieval: BM25 (keyword matching)

    RRF Formula:
        score(doc) = Σ weight_i * (1 / (k + rank_i + 1))
        where k=60 (universal constant), rank_i is position in result list i

    Default Weights:
        - Dense: 0.6 (semantic understanding)
        - Sparse: 0.4 (exact keyword matching)

    Usage:
        service = HybridSearchService(search_service)
        results, time = await service.search(db, query, project_id)
    """

    def __init__(self, search_service):
        """
        Initialize hybrid search service.

        Args:
            search_service: SearchService instance with dense & sparse methods
        """
        self.search_service = search_service

        # Default RRF parameters
        self.rrf_k = 60  # Universal constant (from literature)
        self.dense_weight = 0.6  # Semantic similarity weight
        self.sparse_weight = 0.4  # Keyword matching weight

    async def search(
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

        Args:
            db: Database session
            query: Search query text
            project_id: Project to search within
            limit: Final number of results to return
            top_k_retrieve: Number of candidates from each method
            min_similarity: Minimum similarity for dense search
            min_bm25_score: Minimum BM25 score for sparse search
            dense_weight: Override default dense weight
            sparse_weight: Override default sparse weight
            category_id: Optional category filter

        Returns:
            Tuple of (results list with RRF scores, execution time in ms)
        """
        import time
        start_time = time.time()

        # Use custom weights if provided
        d_weight = dense_weight if dense_weight is not None else self.dense_weight
        s_weight = sparse_weight if sparse_weight is not None else self.sparse_weight

        logger.info(
            f"🔀 Hybrid search: query='{query[:50]}...', "
            f"weights=[dense={d_weight:.2f}, sparse={s_weight:.2f}], "
            f"k={self.rrf_k}"
        )

        # Step 1: Parallel retrieval from both sources
        try:
            dense_results, sparse_results = await asyncio.gather(
                # Dense: Vector similarity search
                self._dense_search(
                    db, query, project_id, top_k_retrieve,
                    min_similarity, category_id
                ),
                # Sparse: BM25 keyword search
                self._sparse_search(
                    db, query, project_id, top_k_retrieve,
                    min_bm25_score
                ),
                return_exceptions=True
            )

            # Handle exceptions from parallel execution
            if isinstance(dense_results, Exception):
                logger.error(f"❌ Dense search failed: {dense_results}")
                dense_results = []

            if isinstance(sparse_results, Exception):
                logger.error(f"❌ Sparse search failed: {sparse_results}")
                sparse_results = []

            logger.info(
                f"  Retrieved: dense={len(dense_results)}, sparse={len(sparse_results)}"
            )

        except Exception as e:
            logger.error(f"❌ Hybrid search failed: {e}")
            return [], 0.0

        # Step 2: Reciprocal Rank Fusion
        fused_results = self._reciprocal_rank_fusion(
            result_lists=[dense_results, sparse_results],
            weights=[d_weight, s_weight],
            k=self.rrf_k
        )

        logger.info(
            f"  RRF fusion: {len(fused_results)} unique chunks, "
            f"top_score={fused_results[0]['rrf_score']:.4f if fused_results else 0:.4f}"
        )

        # Step 3: Return top-k results
        final_results = fused_results[:limit]

        execution_time = (time.time() - start_time) * 1000  # Convert to ms
        logger.info(
            f"✅ Hybrid search completed: {len(final_results)} results in {execution_time:.2f}ms"
        )

        return final_results, execution_time

    async def _dense_search(
        self,
        db: AsyncSession,
        query: str,
        project_id: int,
        top_k: int,
        min_similarity: float,
        category_id: Optional[int]
    ) -> List[dict]:
        """
        Perform dense vector similarity search.

        Args:
            db: Database session
            query: Search query
            project_id: Project ID
            top_k: Number of results
            min_similarity: Minimum similarity threshold
            category_id: Optional category filter

        Returns:
            List of dense search results
        """
        results, _ = await self.search_service.search(
            db=db,
            query=query,
            project_id=project_id,
            limit=top_k,
            min_similarity=min_similarity,
            category_id=category_id
        )

        # Mark as dense results
        for result in results:
            result["source"] = "dense"
            result["dense_score"] = result.get("similarity_score", 0.0)

        return results

    async def _sparse_search(
        self,
        db: AsyncSession,
        query: str,
        project_id: int,
        top_k: int,
        min_score: float
    ) -> List[dict]:
        """
        Perform sparse BM25 keyword search.

        Args:
            db: Database session
            query: Search query
            project_id: Project ID
            top_k: Number of results
            min_score: Minimum BM25 score

        Returns:
            List of sparse search results
        """
        results, _ = await self.search_service.search_sparse(
            db=db,
            query=query,
            project_id=project_id,
            limit=top_k,
            min_score=min_score
        )

        # Mark as sparse results
        for result in results:
            result["source"] = "sparse"
            result["sparse_score"] = result.get("similarity_score", 0.0)

        return results

    def _reciprocal_rank_fusion(
        self,
        result_lists: List[List[dict]],
        weights: List[float],
        k: int = 60
    ) -> List[dict]:
        """
        Combine multiple result lists using Reciprocal Rank Fusion (RRF).

        RRF Formula:
            score(doc) = Σ weight_i * (1 / (k + rank_i + 1))

        Args:
            result_lists: List of result lists (e.g., [dense_results, sparse_results])
            weights: Weights for each list (e.g., [0.6, 0.4])
            k: RRF constant (default: 60, universal value from literature)

        Returns:
            Fused and sorted list of results
        """
        scores = {}
        item_data = {}

        # Iterate through each result list with its weight
        for result_list, weight in zip(result_lists, weights):
            # Process each item in the list
            for rank, item in enumerate(result_list):
                # Use chunk_id as unique identifier
                item_id = item["chunk_id"]

                # Store item data (first occurrence)
                if item_id not in item_data:
                    item_data[item_id] = item.copy()

                # Initialize score
                if item_id not in scores:
                    scores[item_id] = 0.0

                # Calculate weighted RRF score
                # Formula: weight * (1 / (k + rank + 1))
                rrf_contribution = weight * (1.0 / (k + rank + 1))
                scores[item_id] += rrf_contribution

        # Sort by combined RRF score (descending)
        # Add deterministic tie-breaking by chunk_id
        sorted_items = sorted(
            scores.items(),
            key=lambda x: (x[1], -x[0]),  # Sort by score DESC, then by ID ASC
            reverse=True
        )

        # Build final results with RRF scores
        results = []
        for item_id, score in sorted_items:
            result = item_data[item_id]
            result["rrf_score"] = score

            # Mark as hybrid result if from both sources
            if "dense_score" in result and "sparse_score" in result:
                result["source"] = "hybrid"
            # Otherwise keep original source ("dense" or "sparse")

            results.append(result)

        return results

    def update_weights(self, dense_weight: float, sparse_weight: float) -> None:
        """
        Update default RRF weights.

        Args:
            dense_weight: Weight for dense retrieval (0-1)
            sparse_weight: Weight for sparse retrieval (0-1)
        """
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
        logger.info(f"Updated RRF weights: dense={dense_weight:.2f}, sparse={sparse_weight:.2f}")

    def get_config(self) -> Dict[str, Any]:
        """
        Get current hybrid search configuration.

        Returns:
            Dictionary with configuration parameters
        """
        return {
            "rrf_k": self.rrf_k,
            "dense_weight": self.dense_weight,
            "sparse_weight": self.sparse_weight,
            "algorithm": "Reciprocal Rank Fusion (RRF)"
        }
