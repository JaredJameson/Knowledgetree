"""
Cross-Encoder Reranking Service for KnowledgeTree

Implements two-stage retrieval pipeline with cross-encoder reranking.
Part of TIER 1 Advanced RAG implementation (Phase 3).

Key Features:
- Multilingual cross-encoder model (mmarco-mMiniLMv2)
- Two-stage pipeline: retrieve (top-k) → rerank (top-n)
- Batch processing for efficiency
- Relevance scoring (0-1 scale)

Reference: RAG 2025 best practices + ALURON project
"""

import logging
from typing import List, Dict, Any, Optional
from sentence_transformers import CrossEncoder
import numpy as np

logger = logging.getLogger(__name__)


class CrossEncoderService:
    """
    Cross-encoder reranking service for improving retrieval precision.

    Uses cross-encoder model to score [query, document] pairs independently,
    providing more accurate relevance scores than bi-encoder retrieval alone.

    Pipeline:
        1. Retrieve top-k candidates (dense/sparse/hybrid)
        2. Score each [query, chunk] pair with cross-encoder
        3. Rerank by cross-encoder scores
        4. Return top-n results

    Model: cross-encoder/mmarco-mMiniLMv2-L12-H384-v1
    - Multilingual (supports Polish)
    - Size: 471MB
    - Max sequence length: 512 tokens
    - Output: Relevance scores (higher = more relevant)

    Usage:
        reranker = CrossEncoderService()
        reranked = await reranker.rerank(
            query="JWT authentication",
            results=hybrid_results,
            top_k=5
        )
    """

    def __init__(self, model_name: str = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"):
        """
        Initialize cross-encoder service.

        Args:
            model_name: Cross-encoder model identifier (HuggingFace)
        """
        self.model_name = model_name
        self.model: Optional[CrossEncoder] = None
        self.is_initialized = False

    def initialize(self) -> None:
        """
        Load cross-encoder model into memory.

        This should be called once at application startup.
        Model loading takes ~2-3 seconds.
        """
        if self.is_initialized:
            logger.info("✅ Cross-encoder already initialized")
            return

        try:
            logger.info(f"🔄 Loading cross-encoder model: {self.model_name}")
            self.model = CrossEncoder(self.model_name, max_length=512)
            self.is_initialized = True
            logger.info(
                f"✅ Cross-encoder loaded successfully "
                f"(model: {self.model_name}, max_length: 512)"
            )

        except Exception as e:
            logger.error(f"❌ Failed to load cross-encoder model: {e}")
            raise

    async def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int = 5,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Rerank search results using cross-encoder scoring.

        Args:
            query: Search query text
            results: List of search results (from hybrid/dense/sparse search)
            top_k: Number of top results to return after reranking
            min_score: Minimum cross-encoder score threshold (0-1)

        Returns:
            Reranked results with cross-encoder scores, sorted by relevance

        Example:
            Input: 20 results from hybrid search
            Output: Top-5 results reranked by cross-encoder scores
        """
        if not self.is_initialized or not self.model:
            logger.warning("⚠️ Cross-encoder not initialized - returning original results")
            return results[:top_k]

        if not results:
            logger.warning("⚠️ Empty results list - nothing to rerank")
            return []

        try:
            # Prepare [query, document] pairs for scoring
            pairs = []
            for result in results:
                chunk_text = result.get("chunk_text", "")
                pairs.append([query, chunk_text])

            # Batch scoring with cross-encoder
            logger.info(
                f"🔍 Cross-encoder reranking: query='{query[:50]}...', "
                f"candidates={len(pairs)}, top_k={top_k}"
            )

            scores = self.model.predict(pairs, show_progress_bar=False)

            # Convert numpy array to list of floats
            if isinstance(scores, np.ndarray):
                scores = scores.tolist()

            # Add cross-encoder scores to results
            for i, result in enumerate(results):
                result["cross_encoder_score"] = float(scores[i])
                result["original_rank"] = i + 1  # Store original ranking

            # Filter by min_score
            filtered_results = [
                r for r in results
                if r["cross_encoder_score"] >= min_score
            ]

            # Sort by cross-encoder score (descending)
            reranked = sorted(
                filtered_results,
                key=lambda x: x["cross_encoder_score"],
                reverse=True
            )

            # Return top-k
            top_results = reranked[:top_k]

            logger.info(
                f"✅ Cross-encoder reranking completed: "
                f"{len(top_results)} results, "
                f"top_score={top_results[0]['cross_encoder_score']:.4f if top_results else 0:.4f}"
            )

            return top_results

        except Exception as e:
            logger.error(f"❌ Cross-encoder reranking failed: {e}")
            # Fallback: return original results
            return results[:top_k]

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get cross-encoder model information.

        Returns:
            Dictionary with model metadata
        """
        return {
            "model_name": self.model_name,
            "initialized": self.is_initialized,
            "max_sequence_length": 512,
            "supports_multilingual": True,
            "supports_polish": True,
        }


# Global singleton instance (initialized at startup)
cross_encoder_service = CrossEncoderService()
