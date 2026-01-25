"""
CRAG Service for KnowledgeTree

TIER 2 Enhanced RAG - Phase 4: Corrective RAG (CRAG)

Implements self-corrective retrieval with quality evaluation and fallback strategies.
When retrieval quality is low, the system automatically applies corrective actions:
- Knowledge refinement (filter low-quality results)
- Query refinement (reformulate query)
- Web search fallback (external knowledge)

Key Features:
- Retrieval quality evaluation
- Self-reflection mechanism
- Corrective action strategies
- Automatic fallback handling
- Quality-based routing

Expected Impact: +10-15% robustness on challenging queries

Reference: CRAG paper (2024) - Corrective Retrieval Augmented Generation
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RetrievalQuality(Enum):
    """Retrieval quality levels"""
    EXCELLENT = "excellent"  # >0.8 confidence
    GOOD = "good"            # 0.6-0.8
    MODERATE = "moderate"    # 0.4-0.6
    POOR = "poor"            # <0.4


class CorrectiveAction(Enum):
    """Corrective action types"""
    NONE = "none"                          # Use results as-is
    KNOWLEDGE_REFINEMENT = "refinement"    # Filter low-quality results
    QUERY_REFINEMENT = "query_reform"      # Reformulate query
    WEB_SEARCH = "web_search"              # External knowledge fallback
    COMBINED = "combined"                  # Multiple actions


@dataclass
class RetrievalEvaluation:
    """
    Evaluation of retrieval quality.
    """
    quality_level: RetrievalQuality
    confidence_score: float
    corrective_action: CorrectiveAction

    # Quality metrics
    top_score: float
    score_variance: float
    result_count: int

    # Explanation
    reasoning: str
    should_apply_correction: bool


@dataclass
class CorrectedResults:
    """
    Results after CRAG correction.
    """
    original_results: List[Dict[str, Any]]
    corrected_results: List[Dict[str, Any]]
    evaluation: RetrievalEvaluation
    actions_applied: List[str]
    improvement_metrics: Dict[str, Any]


class CRAGService:
    """
    Corrective RAG service with self-reflection and quality evaluation.

    Implements CRAG algorithm:
    1. Evaluate retrieval quality
    2. Decide on corrective action
    3. Apply correction strategy
    4. Return corrected results
    """

    def __init__(
        self,
        excellent_threshold: float = 0.8,
        good_threshold: float = 0.6,
        moderate_threshold: float = 0.4,
        min_result_count: int = 3
    ):
        """
        Initialize CRAG service.

        Args:
            excellent_threshold: Threshold for excellent quality (default: 0.8)
            good_threshold: Threshold for good quality (default: 0.6)
            moderate_threshold: Threshold for moderate quality (default: 0.4)
            min_result_count: Minimum acceptable result count (default: 3)
        """
        self.excellent_threshold = excellent_threshold
        self.good_threshold = good_threshold
        self.moderate_threshold = moderate_threshold
        self.min_result_count = min_result_count

    def evaluate_retrieval_quality(
        self,
        results: List[Dict[str, Any]],
        score_field: str = "rrf_score"
    ) -> RetrievalEvaluation:
        """
        Evaluate quality of retrieved results.

        Args:
            results: Retrieved results
            score_field: Field name for scoring (default: "rrf_score")

        Returns:
            RetrievalEvaluation with quality assessment
        """
        if not results:
            return RetrievalEvaluation(
                quality_level=RetrievalQuality.POOR,
                confidence_score=0.0,
                corrective_action=CorrectiveAction.WEB_SEARCH,
                top_score=0.0,
                score_variance=0.0,
                result_count=0,
                reasoning="No results returned - need external knowledge",
                should_apply_correction=True
            )

        # Extract scores
        scores = [r.get(score_field, 0.0) for r in results]
        top_score = max(scores) if scores else 0.0
        avg_score = sum(scores) / len(scores) if scores else 0.0
        score_variance = self._calculate_variance(scores)
        result_count = len(results)

        # Calculate confidence score
        confidence_score = self._calculate_confidence(
            top_score=top_score,
            avg_score=avg_score,
            variance=score_variance,
            count=result_count
        )

        # Determine quality level
        quality_level = self._classify_quality(confidence_score)

        # Decide corrective action
        corrective_action = self._decide_corrective_action(
            quality_level=quality_level,
            confidence_score=confidence_score,
            result_count=result_count,
            top_score=top_score
        )

        # Generate reasoning
        reasoning = self._generate_reasoning(
            quality_level=quality_level,
            confidence_score=confidence_score,
            result_count=result_count,
            top_score=top_score
        )

        should_apply_correction = corrective_action != CorrectiveAction.NONE

        logger.info(
            f"🔍 CRAG Evaluation: quality={quality_level.value}, "
            f"confidence={confidence_score:.3f}, "
            f"action={corrective_action.value}"
        )

        return RetrievalEvaluation(
            quality_level=quality_level,
            confidence_score=confidence_score,
            corrective_action=corrective_action,
            top_score=top_score,
            score_variance=score_variance,
            result_count=result_count,
            reasoning=reasoning,
            should_apply_correction=should_apply_correction
        )

    def apply_corrective_action(
        self,
        results: List[Dict[str, Any]],
        evaluation: RetrievalEvaluation,
        query: str,
        score_field: str = "rrf_score"
    ) -> CorrectedResults:
        """
        Apply corrective action based on evaluation.

        Args:
            results: Original retrieved results
            evaluation: Quality evaluation
            query: Original query
            score_field: Field name for scoring

        Returns:
            CorrectedResults with corrected results and metrics
        """
        original_results = results.copy()
        corrected_results = results.copy()
        actions_applied = []

        if not evaluation.should_apply_correction:
            logger.info("✅ CRAG: No correction needed - results are good")
            return CorrectedResults(
                original_results=original_results,
                corrected_results=corrected_results,
                evaluation=evaluation,
                actions_applied=["none"],
                improvement_metrics={"correction_applied": False}
            )

        # Apply corrective actions
        if evaluation.corrective_action == CorrectiveAction.KNOWLEDGE_REFINEMENT:
            corrected_results = self._apply_knowledge_refinement(
                results=corrected_results,
                score_field=score_field
            )
            actions_applied.append("knowledge_refinement")

        elif evaluation.corrective_action == CorrectiveAction.QUERY_REFINEMENT:
            # Note: Query refinement would require re-running search
            # For now, we filter results and mark for query refinement
            corrected_results = self._apply_knowledge_refinement(
                results=corrected_results,
                score_field=score_field
            )
            actions_applied.append("knowledge_refinement")
            actions_applied.append("query_refinement_suggested")

        elif evaluation.corrective_action == CorrectiveAction.WEB_SEARCH:
            # Mark for web search fallback
            # Actual web search would be implemented separately
            actions_applied.append("web_search_required")

        elif evaluation.corrective_action == CorrectiveAction.COMBINED:
            corrected_results = self._apply_knowledge_refinement(
                results=corrected_results,
                score_field=score_field
            )
            actions_applied.extend([
                "knowledge_refinement",
                "query_refinement_suggested",
                "web_search_suggested"
            ])

        # Calculate improvement metrics
        improvement_metrics = self._calculate_improvement_metrics(
            original_results=original_results,
            corrected_results=corrected_results,
            score_field=score_field
        )

        logger.info(
            f"🔧 CRAG Correction: actions={actions_applied}, "
            f"results: {len(original_results)} → {len(corrected_results)}"
        )

        return CorrectedResults(
            original_results=original_results,
            corrected_results=corrected_results,
            evaluation=evaluation,
            actions_applied=actions_applied,
            improvement_metrics=improvement_metrics
        )

    def _calculate_confidence(
        self,
        top_score: float,
        avg_score: float,
        variance: float,
        count: int
    ) -> float:
        """
        Calculate overall confidence score.

        Args:
            top_score: Highest score
            avg_score: Average score
            variance: Score variance
            count: Number of results

        Returns:
            Confidence score (0-1)
        """
        # Weighted combination of factors
        score_component = top_score * 0.5 + avg_score * 0.3
        variance_component = max(0, 1.0 - variance) * 0.1
        count_component = min(count / self.min_result_count, 1.0) * 0.1

        confidence = score_component + variance_component + count_component
        return min(confidence, 1.0)

    def _classify_quality(self, confidence_score: float) -> RetrievalQuality:
        """Classify retrieval quality based on confidence score."""
        if confidence_score >= self.excellent_threshold:
            return RetrievalQuality.EXCELLENT
        elif confidence_score >= self.good_threshold:
            return RetrievalQuality.GOOD
        elif confidence_score >= self.moderate_threshold:
            return RetrievalQuality.MODERATE
        else:
            return RetrievalQuality.POOR

    def _decide_corrective_action(
        self,
        quality_level: RetrievalQuality,
        confidence_score: float,
        result_count: int,
        top_score: float
    ) -> CorrectiveAction:
        """
        Decide which corrective action to apply.

        Args:
            quality_level: Quality classification
            confidence_score: Overall confidence
            result_count: Number of results
            top_score: Highest score

        Returns:
            Recommended corrective action
        """
        # No correction needed for excellent results
        if quality_level == RetrievalQuality.EXCELLENT:
            return CorrectiveAction.NONE

        # Good results - minimal refinement
        if quality_level == RetrievalQuality.GOOD:
            return CorrectiveAction.KNOWLEDGE_REFINEMENT

        # Moderate results - try query refinement
        if quality_level == RetrievalQuality.MODERATE:
            if result_count < self.min_result_count:
                return CorrectiveAction.QUERY_REFINEMENT
            else:
                return CorrectiveAction.KNOWLEDGE_REFINEMENT

        # Poor results - need external knowledge or combined approach
        if quality_level == RetrievalQuality.POOR:
            if result_count == 0:
                return CorrectiveAction.WEB_SEARCH
            elif top_score < 0.3:
                return CorrectiveAction.COMBINED
            else:
                return CorrectiveAction.QUERY_REFINEMENT

        return CorrectiveAction.NONE

    def _generate_reasoning(
        self,
        quality_level: RetrievalQuality,
        confidence_score: float,
        result_count: int,
        top_score: float
    ) -> str:
        """Generate human-readable reasoning for evaluation."""
        if quality_level == RetrievalQuality.EXCELLENT:
            return f"Excellent retrieval quality (confidence={confidence_score:.3f}), no correction needed"

        elif quality_level == RetrievalQuality.GOOD:
            return f"Good retrieval quality (confidence={confidence_score:.3f}), minor refinement recommended"

        elif quality_level == RetrievalQuality.MODERATE:
            if result_count < self.min_result_count:
                return f"Moderate quality with few results ({result_count}), query refinement needed"
            else:
                return f"Moderate quality (confidence={confidence_score:.3f}), filtering low-quality results"

        else:  # POOR
            if result_count == 0:
                return "No results found - external knowledge search required"
            elif top_score < 0.3:
                return f"Poor retrieval quality (top_score={top_score:.3f}), combined correction needed"
            else:
                return f"Poor quality (confidence={confidence_score:.3f}), query reformulation recommended"

    def _apply_knowledge_refinement(
        self,
        results: List[Dict[str, Any]],
        score_field: str
    ) -> List[Dict[str, Any]]:
        """
        Filter out low-quality results.

        Args:
            results: Original results
            score_field: Score field name

        Returns:
            Filtered results
        """
        if not results:
            return results

        # Calculate threshold (mean - 0.5 * std)
        scores = [r.get(score_field, 0.0) for r in results]
        mean_score = sum(scores) / len(scores)
        std_score = (sum((s - mean_score) ** 2 for s in scores) / len(scores)) ** 0.5
        threshold = max(mean_score - 0.5 * std_score, 0.2)

        # Filter results
        filtered = [r for r in results if r.get(score_field, 0.0) >= threshold]

        logger.info(
            f"📊 Knowledge Refinement: threshold={threshold:.3f}, "
            f"filtered {len(results)} → {len(filtered)} results"
        )

        return filtered if filtered else results[:3]  # Keep at least top 3

    def _calculate_variance(self, scores: List[float]) -> float:
        """Calculate variance of scores."""
        if not scores or len(scores) < 2:
            return 0.0

        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        return variance

    def _calculate_improvement_metrics(
        self,
        original_results: List[Dict[str, Any]],
        corrected_results: List[Dict[str, Any]],
        score_field: str
    ) -> Dict[str, Any]:
        """Calculate metrics showing improvement from correction."""
        metrics = {
            "correction_applied": True,
            "original_count": len(original_results),
            "corrected_count": len(corrected_results),
            "results_filtered": len(original_results) - len(corrected_results)
        }

        if original_results:
            orig_scores = [r.get(score_field, 0.0) for r in original_results]
            metrics["original_avg_score"] = sum(orig_scores) / len(orig_scores)
            metrics["original_top_score"] = max(orig_scores)

        if corrected_results:
            corr_scores = [r.get(score_field, 0.0) for r in corrected_results]
            metrics["corrected_avg_score"] = sum(corr_scores) / len(corr_scores)
            metrics["corrected_top_score"] = max(corr_scores)

            if original_results:
                metrics["avg_score_improvement"] = (
                    metrics["corrected_avg_score"] - metrics["original_avg_score"]
                )

        return metrics


# Global singleton instance
crag_service = CRAGService()
