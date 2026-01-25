"""
Explainability Service for KnowledgeTree

TIER 2 Enhanced RAG - Phase 2: Result Explainability

Generates detailed explanations for search results to enhance user trust and debugging.
Shows contribution from each retrieval stage: dense (semantic), sparse (BM25),
RRF fusion, and cross-encoder reranking.

Key Features:
- Score decomposition (dense, sparse, RRF, cross-encoder)
- Matched keywords extraction
- Semantic similarity explanation
- Contribution analysis for each retrieval stage
- User-friendly explanations

Reference: RAG 2025 best practices - explainability and transparency
"""

import logging
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RetrievalExplanation:
    """
    Explanation for a single search result.

    Provides transparency into how the result was retrieved and ranked.
    """
    # Score breakdown
    final_score: float
    score_type: str  # "rrf_score", "cross_encoder_score", "similarity_score"

    # Dense retrieval (semantic)
    dense_score: Optional[float] = None
    dense_contribution: Optional[float] = None

    # Sparse retrieval (BM25)
    sparse_score: Optional[float] = None
    sparse_contribution: Optional[float] = None
    matched_keywords: List[str] = None

    # RRF fusion
    rrf_score: Optional[float] = None
    rrf_rank: Optional[int] = None

    # Cross-encoder reranking
    cross_encoder_score: Optional[float] = None
    original_rank: Optional[int] = None
    reranking_improvement: Optional[int] = None

    # Human-readable explanation
    explanation_text: str = ""

    def __post_init__(self):
        if self.matched_keywords is None:
            self.matched_keywords = []


class ExplainabilityService:
    """
    Service for generating explanations for search results.

    Analyzes retrieval pipeline and generates user-friendly explanations
    showing why each result was retrieved and how it was ranked.
    """

    def __init__(self):
        """Initialize explainability service."""
        pass

    def explain_result(
        self,
        result: Dict[str, Any],
        query: str,
        pipeline_type: str = "dense"
    ) -> RetrievalExplanation:
        """
        Generate explanation for a single search result.

        Args:
            result: Search result dictionary with scores and metadata
            query: Original search query
            pipeline_type: Type of retrieval pipeline used
                          ("dense", "sparse", "hybrid", "reranked")

        Returns:
            RetrievalExplanation with detailed breakdown
        """
        explanation = RetrievalExplanation(
            final_score=0.0,
            score_type="unknown"
        )

        # Determine score type and extract scores
        if "cross_encoder_score" in result and result["cross_encoder_score"] is not None:
            # Reranked result
            explanation.score_type = "cross_encoder_score"
            explanation.final_score = result["cross_encoder_score"]
            explanation.cross_encoder_score = result["cross_encoder_score"]
            explanation.original_rank = result.get("original_rank")

            # Calculate reranking improvement
            if explanation.original_rank:
                current_rank = result.get("rank", 0)
                explanation.reranking_improvement = explanation.original_rank - current_rank

        elif "rrf_score" in result and result["rrf_score"] is not None:
            # Hybrid search result
            explanation.score_type = "rrf_score"
            explanation.final_score = result["rrf_score"]
            explanation.rrf_score = result["rrf_score"]

        else:
            # Dense or sparse only
            explanation.score_type = "similarity_score"
            explanation.final_score = result.get("similarity_score", 0.0)

        # Extract dense score
        if "dense_score" in result:
            explanation.dense_score = result["dense_score"]
        elif "similarity_score" in result and pipeline_type == "dense":
            explanation.dense_score = result["similarity_score"]

        # Extract sparse score and keywords
        if "sparse_score" in result:
            explanation.sparse_score = result["sparse_score"]

        # Extract matched keywords from chunk text
        explanation.matched_keywords = self._extract_matched_keywords(
            query=query,
            text=result.get("chunk_text", "")
        )

        # Calculate contribution percentages (if hybrid)
        if explanation.dense_score is not None and explanation.sparse_score is not None:
            total = explanation.dense_score + explanation.sparse_score
            if total > 0:
                explanation.dense_contribution = (explanation.dense_score / total) * 100
                explanation.sparse_contribution = (explanation.sparse_score / total) * 100

        # Generate human-readable explanation
        explanation.explanation_text = self._generate_explanation_text(explanation, pipeline_type)

        return explanation

    def explain_results(
        self,
        results: List[Dict[str, Any]],
        query: str,
        pipeline_type: str = "dense"
    ) -> List[Dict[str, Any]]:
        """
        Add explanations to all search results.

        Args:
            results: List of search results
            query: Original search query
            pipeline_type: Type of retrieval pipeline used

        Returns:
            Results with added 'explanation' field
        """
        explained_results = []

        for rank, result in enumerate(results, start=1):
            # Generate explanation
            explanation = self.explain_result(result, query, pipeline_type)

            # Add rank if not present
            if "rank" not in result:
                result["rank"] = rank

            # Convert explanation to dict and add to result
            result["explanation"] = self._explanation_to_dict(explanation)

            explained_results.append(result)

        logger.info(f"Generated explanations for {len(explained_results)} results")
        return explained_results

    def _extract_matched_keywords(self, query: str, text: str) -> List[str]:
        """
        Extract keywords from query that appear in result text.

        Args:
            query: Search query
            text: Result text

        Returns:
            List of matched keywords
        """
        # Normalize text
        query_lower = query.lower()
        text_lower = text.lower()

        # Split query into words
        query_words = re.findall(r'\b\w+\b', query_lower)

        # Find matches
        matched = []
        for word in query_words:
            if len(word) > 2 and word in text_lower:  # Skip short words
                matched.append(word)

        return list(set(matched))  # Remove duplicates

    def _generate_explanation_text(
        self,
        explanation: RetrievalExplanation,
        pipeline_type: str
    ) -> str:
        """
        Generate human-readable explanation text.

        Args:
            explanation: RetrievalExplanation object
            pipeline_type: Type of retrieval pipeline

        Returns:
            Human-readable explanation string
        """
        parts = []

        # Score type explanation
        if explanation.score_type == "cross_encoder_score":
            parts.append(
                f"Wynik reranking: {explanation.cross_encoder_score:.3f} "
                f"(dokładna ocena trafności przez cross-encoder)"
            )
            if explanation.reranking_improvement and explanation.reranking_improvement > 0:
                parts.append(
                    f"Pozycja poprawiona o {explanation.reranking_improvement} miejsc "
                    f"po rerankingu"
                )

        elif explanation.score_type == "rrf_score":
            parts.append(
                f"Wynik RRF: {explanation.rrf_score:.3f} "
                f"(fuzja wyszukiwania semantycznego + słów kluczowych)"
            )

        elif explanation.score_type == "similarity_score":
            parts.append(
                f"Podobieństwo semantyczne: {explanation.final_score:.3f}"
            )

        # Dense contribution
        if explanation.dense_score is not None:
            if explanation.dense_contribution:
                parts.append(
                    f"Wyszukiwanie semantyczne: {explanation.dense_score:.3f} "
                    f"({explanation.dense_contribution:.1f}% wkładu)"
                )
            else:
                parts.append(f"Wyszukiwanie semantyczne: {explanation.dense_score:.3f}")

        # Sparse contribution
        if explanation.sparse_score is not None:
            if explanation.sparse_contribution:
                parts.append(
                    f"Dopasowanie słów kluczowych (BM25): {explanation.sparse_score:.3f} "
                    f"({explanation.sparse_contribution:.1f}% wkładu)"
                )
            else:
                parts.append(f"Dopasowanie słów kluczowych: {explanation.sparse_score:.3f}")

        # Matched keywords
        if explanation.matched_keywords:
            keywords_str = ", ".join(f"'{kw}'" for kw in explanation.matched_keywords[:5])
            parts.append(f"Znalezione słowa kluczowe: {keywords_str}")

        return " | ".join(parts)

    def _explanation_to_dict(self, explanation: RetrievalExplanation) -> Dict[str, Any]:
        """
        Convert RetrievalExplanation to dictionary.

        Args:
            explanation: RetrievalExplanation object

        Returns:
            Dictionary representation
        """
        return {
            "final_score": explanation.final_score,
            "score_type": explanation.score_type,
            "dense_score": explanation.dense_score,
            "dense_contribution": explanation.dense_contribution,
            "sparse_score": explanation.sparse_score,
            "sparse_contribution": explanation.sparse_contribution,
            "matched_keywords": explanation.matched_keywords,
            "rrf_score": explanation.rrf_score,
            "rrf_rank": explanation.rrf_rank,
            "cross_encoder_score": explanation.cross_encoder_score,
            "original_rank": explanation.original_rank,
            "reranking_improvement": explanation.reranking_improvement,
            "explanation_text": explanation.explanation_text
        }

    def generate_pipeline_summary(
        self,
        results: List[Dict[str, Any]],
        pipeline_type: str,
        execution_time_ms: float
    ) -> Dict[str, Any]:
        """
        Generate summary of retrieval pipeline performance.

        Args:
            results: Search results with explanations
            pipeline_type: Type of retrieval pipeline
            execution_time_ms: Total execution time

        Returns:
            Pipeline summary dictionary
        """
        summary = {
            "pipeline_type": pipeline_type,
            "total_results": len(results),
            "execution_time_ms": execution_time_ms,
            "average_scores": {}
        }

        # Calculate average scores
        if results:
            # Dense scores
            dense_scores = [
                r.get("explanation", {}).get("dense_score")
                for r in results
                if r.get("explanation", {}).get("dense_score") is not None
            ]
            if dense_scores:
                summary["average_scores"]["dense"] = sum(dense_scores) / len(dense_scores)

            # Sparse scores
            sparse_scores = [
                r.get("explanation", {}).get("sparse_score")
                for r in results
                if r.get("explanation", {}).get("sparse_score") is not None
            ]
            if sparse_scores:
                summary["average_scores"]["sparse"] = sum(sparse_scores) / len(sparse_scores)

            # RRF scores
            rrf_scores = [
                r.get("explanation", {}).get("rrf_score")
                for r in results
                if r.get("explanation", {}).get("rrf_score") is not None
            ]
            if rrf_scores:
                summary["average_scores"]["rrf"] = sum(rrf_scores) / len(rrf_scores)

            # Cross-encoder scores
            ce_scores = [
                r.get("explanation", {}).get("cross_encoder_score")
                for r in results
                if r.get("explanation", {}).get("cross_encoder_score") is not None
            ]
            if ce_scores:
                summary["average_scores"]["cross_encoder"] = sum(ce_scores) / len(ce_scores)

        return summary


# Global singleton instance
explainability_service = ExplainabilityService()
