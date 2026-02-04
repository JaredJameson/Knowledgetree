"""
KnowledgeTree Backend - Search Routes
Semantic search endpoints using vector similarity
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from models.user import User
from models.project import Project
from schemas.search import (
    SearchRequest,
    SearchResult,
    SearchResponse,
    SearchStatistics,
    HybridSearchRequest,
    RerankSearchRequest,
)
from api.dependencies import get_current_active_user
from services.search_service import SearchService
from services.explainability_service import explainability_service
from services.activity_tracker import ActivityTracker

router = APIRouter(prefix="/search", tags=["Search"])
logger = logging.getLogger(__name__)

# Initialize search service
search_service = SearchService()


@router.post("/", response_model=SearchResponse)
async def search_documents(
    search_request: SearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Perform semantic search across documents in a project

    This endpoint:
    1. Generates an embedding for the query using BGE-M3
    2. Performs vector similarity search using pgvector (cosine similarity)
    3. Filters by project (and optionally by category)
    4. Returns ranked results with similarity scores

    **Query Parameters:**
    - `query`: Search text (1-1000 characters)
    - `project_id`: Project to search within
    - `category_id`: Optional category filter
    - `limit`: Maximum results (1-100, default: 10)
    - `min_similarity`: Minimum similarity threshold (0-1, default: 0.5)

    **Returns:**
    - List of matching chunks with document metadata
    - Similarity scores (0-1, higher = more similar)
    - Execution time and applied filters
    """
    # Verify project access
    result = await db.execute(
        select(Project).where(
            Project.id == search_request.project_id,
            Project.owner_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )

    try:
        # Perform search
        results, execution_time = await search_service.search(
            db=db,
            query=search_request.query,
            project_id=search_request.project_id,
            limit=search_request.limit,
            min_similarity=search_request.min_similarity,
            category_id=search_request.category_id
        )

        # Re-rank results with recency boost
        results = await search_service.rerank_results(
            results=results,
            query=search_request.query,
            boost_recent=True,
            recency_weight=0.1
        )

        # Format response
        search_results = [SearchResult(**result) for result in results]

        filters_applied = {
            "project_id": search_request.project_id,
            "category_id": search_request.category_id,
            "min_similarity": search_request.min_similarity,
            "limit": search_request.limit,
        }

        logger.info(
            f"Search completed for user {current_user.id}: "
            f"query='{search_request.query[:50]}', "
            f"results={len(search_results)}, "
            f"time={execution_time:.2f}ms"
        )

        # Track activity event
        activity_tracker = ActivityTracker(db)
        await activity_tracker.record_search(
            user_id=current_user.id,
            project_id=search_request.project_id,
            query=search_request.query,
            results_count=len(search_results),
            search_type="semantic",
            response_time_ms=int(execution_time)
        )

        return SearchResponse(
            query=search_request.query,
            results=search_results,
            total_results=len(search_results),
            execution_time_ms=round(execution_time, 2),
            filters_applied=filters_applied
        )

    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/statistics/{project_id}", response_model=SearchStatistics)
async def get_search_statistics(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get search statistics for a project

    Returns metrics about documents, chunks, and vector storage:
    - Total documents and chunks
    - Number of embedded chunks ready for search
    - Average chunk text length
    - Total vector storage size in MB
    """
    # Verify project access
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )

    try:
        stats = await search_service.get_statistics(
            db=db,
            project_id=project_id
        )

        logger.info(f"Retrieved search statistics for project {project_id}")

        return SearchStatistics(**stats)

    except Exception as e:
        logger.error(f"Failed to get search statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.post("/sparse", response_model=SearchResponse)
async def search_sparse(
    search_request: SearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Perform sparse (BM25) keyword-based search (TIER 1 Advanced RAG)

    This endpoint:
    1. Tokenizes query for BM25 matching
    2. Performs keyword-based retrieval using BM25Okapi algorithm
    3. Filters by project (and optionally by category)
    4. Returns ranked results with BM25 scores

    **Query Parameters:**
    - `query`: Search text (1-1000 characters)
    - `project_id`: Project to search within
    - `category_id`: Optional category filter
    - `limit`: Maximum results (1-100, default: 10)
    - `min_similarity`: Used as min_bm25_score threshold

    **Returns:**
    - List of matching chunks with document metadata
    - BM25 scores (higher = better keyword match)
    - Execution time and applied filters
    """
    # Verify project access
    result = await db.execute(
        select(Project).where(
            Project.id == search_request.project_id,
            Project.owner_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )

    try:
        # Perform sparse search
        results, execution_time = await search_service.search_sparse(
            db=db,
            query=search_request.query,
            project_id=search_request.project_id,
            limit=search_request.limit,
            min_score=search_request.min_similarity  # Reuse min_similarity field
        )

        # Format response
        search_results = [SearchResult(**result) for result in results]

        filters_applied = {
            "project_id": search_request.project_id,
            "category_id": search_request.category_id,
            "min_bm25_score": search_request.min_similarity,
            "limit": search_request.limit,
            "search_type": "sparse (BM25)",
        }

        logger.info(
            f"Sparse search completed for user {current_user.id}: "
            f"query='{search_request.query[:50]}', "
            f"results={len(search_results)}, "
            f"time={execution_time:.2f}ms"
        )

        return SearchResponse(
            query=search_request.query,
            results=search_results,
            total_results=len(search_results),
            execution_time_ms=round(execution_time, 2),
            filters_applied=filters_applied
        )

    except Exception as e:
        logger.error(f"Sparse search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sparse search failed: {str(e)}"
        )


@router.post("/hybrid", response_model=SearchResponse)
async def search_hybrid(
    search_request: HybridSearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Perform hybrid search with dense + sparse retrieval and RRF fusion (TIER 1 Advanced RAG)

    This endpoint implements state-of-the-art hybrid RAG retrieval:
    1. **Parallel Retrieval**: Simultaneously performs:
       - Dense (semantic): BGE-M3 vector similarity search
       - Sparse (keyword): BM25Okapi keyword matching
    2. **RRF Fusion**: Combines results using Reciprocal Rank Fusion algorithm
       - Formula: score(doc) = Σ weight_i * (1 / (k + rank_i + 1))
       - Universal constant k=60
       - Default weights: 0.6 dense, 0.4 sparse
    3. Returns top-k fused results with RRF scores

    **Query Parameters:**
    - `query`: Search text (1-1000 characters)
    - `project_id`: Project to search within
    - `category_id`: Optional category filter
    - `limit`: Final number of results to return (default: 10)
    - `top_k_retrieve`: Candidates from each method (default: 20)
    - `min_similarity`: Minimum similarity for dense search (default: 0.5)
    - `min_bm25_score`: Minimum BM25 score for sparse search (default: 0.0)
    - `dense_weight`: Override dense weight (default: 0.6)
    - `sparse_weight`: Override sparse weight (default: 0.4)

    **Returns:**
    - Fused results with RRF scores
    - Source attribution (dense/sparse/hybrid)
    - Individual scores for transparency
    - Execution time and applied filters

    **Performance Target**: ~500ms total (300ms retrieval + 200ms fusion)
    """
    # Verify project access
    result = await db.execute(
        select(Project).where(
            Project.id == search_request.project_id,
            Project.owner_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )

    try:
        # Perform hybrid search
        results, execution_time = await search_service.hybrid_search(
            db=db,
            query=search_request.query,
            project_id=search_request.project_id,
            limit=search_request.limit,
            top_k_retrieve=search_request.top_k_retrieve,
            min_similarity=search_request.min_similarity,
            min_bm25_score=search_request.min_bm25_score,
            dense_weight=search_request.dense_weight,
            sparse_weight=search_request.sparse_weight,
            category_id=search_request.category_id
        )

        # Format response
        search_results = [SearchResult(**result) for result in results]

        filters_applied = {
            "project_id": search_request.project_id,
            "category_id": search_request.category_id,
            "top_k_retrieve": search_request.top_k_retrieve,
            "min_similarity": search_request.min_similarity,
            "min_bm25_score": search_request.min_bm25_score,
            "limit": search_request.limit,
            "dense_weight": search_request.dense_weight or 0.6,
            "sparse_weight": search_request.sparse_weight or 0.4,
            "search_type": "hybrid (dense + sparse + RRF)",
        }

        # TIER 2 Phase 2: Generate pipeline summary
        pipeline_summary = explainability_service.generate_pipeline_summary(
            results=results,
            pipeline_type="hybrid",
            execution_time_ms=execution_time
        )

        logger.info(
            f"Hybrid search completed for user {current_user.id}: "
            f"query='{search_request.query[:50]}', "
            f"results={len(search_results)}, "
            f"time={execution_time:.2f}ms"
        )

        return SearchResponse(
            query=search_request.query,
            results=search_results,
            total_results=len(search_results),
            execution_time_ms=round(execution_time, 2),
            filters_applied=filters_applied,
            pipeline_summary=pipeline_summary
        )

    except Exception as e:
        logger.error(f"Hybrid search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hybrid search failed: {str(e)}"
        )


@router.post("/reranked", response_model=SearchResponse)
async def search_with_reranking(
    search_request: RerankSearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Complete TIER 1 Advanced RAG pipeline: Hybrid + Cross-Encoder Reranking

    **Three-Stage Retrieval Pipeline:**

    1. **Hybrid Retrieval** (Stage 1):
       - Dense: BGE-M3 semantic embeddings
       - Sparse: BM25Okapi keyword matching
       - Fusion: Reciprocal Rank Fusion (RRF, k=60)
       - Output: Top-20 candidates (configurable)

    2. **Cross-Encoder Reranking** (Stage 2):
       - Model: mmarco-mMiniLMv2-L12-H384-v1 (multilingual)
       - Scores each [query, document] pair independently
       - More accurate than bi-encoder retrieval
       - Output: Precise relevance scores (0-1)

    3. **Final Selection** (Stage 3):
       - Sort by cross-encoder scores
       - Return top-k most relevant results

    **This is the most accurate search method available (TIER 1 complete).**

    **Query Parameters:**
    - `query`: Search text (1-1000 characters)
    - `project_id`: Project to search within
    - `category_id`: Optional category filter
    - `limit`: Final number of results (default: 5, max: 20)
    - `retrieval_limit`: Candidates for reranking (default: 20, max: 100)
    - `min_similarity`: Minimum similarity for dense search (default: 0.5)
    - `min_bm25_score`: Minimum BM25 score (default: 0.0)
    - `min_cross_encoder_score`: Minimum cross-encoder score (default: 0.0)
    - `dense_weight`: Override dense weight (default: 0.6)
    - `sparse_weight`: Override sparse weight (default: 0.4)

    **Returns:**
    - Reranked results with cross-encoder scores
    - Original ranks for comparison
    - Individual scores for transparency (dense, sparse, RRF, cross-encoder)
    - Execution time and applied filters

    **Performance Target**: ~700ms total (500ms hybrid + 200ms reranking)

    **Expected Accuracy**: 80-85% (vs. 60-70% for dense-only search)
    """
    # Verify project access
    result = await db.execute(
        select(Project).where(
            Project.id == search_request.project_id,
            Project.owner_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )

    try:
        # Perform complete TIER 1 pipeline
        # Perform complete TIER 1+2 pipeline (with query expansion + CRAG)
        results, execution_time = await search_service.search_with_reranking(
            db=db,
            query=search_request.query,
            project_id=search_request.project_id,
            limit=search_request.limit,
            retrieval_limit=search_request.retrieval_limit,
            min_similarity=search_request.min_similarity,
            min_bm25_score=search_request.min_bm25_score,
            min_cross_encoder_score=search_request.min_cross_encoder_score,
            dense_weight=search_request.dense_weight,
            sparse_weight=search_request.sparse_weight,
            category_id=search_request.category_id,
            use_query_expansion=search_request.use_query_expansion,
            expansion_strategy=search_request.expansion_strategy,
            use_crag=search_request.use_crag
        )

        # Format response
        search_results = [SearchResult(**result) for result in results]

        filters_applied = {
            "project_id": search_request.project_id,
            "category_id": search_request.category_id,
            "retrieval_limit": search_request.retrieval_limit,
            "min_similarity": search_request.min_similarity,
            "min_bm25_score": search_request.min_bm25_score,
            "min_cross_encoder_score": search_request.min_cross_encoder_score,
            "limit": search_request.limit,
            "dense_weight": search_request.dense_weight or 0.6,
            "sparse_weight": search_request.sparse_weight or 0.4,
            "search_type": "TIER 1 complete (hybrid + reranking)",
            "pipeline_stages": ["dense", "sparse", "RRF", "cross-encoder"],
        }

        # TIER 2 Phase 2: Generate pipeline summary
        pipeline_summary = explainability_service.generate_pipeline_summary(
            results=results,
            pipeline_type="reranked",
            execution_time_ms=execution_time
        )

        logger.info(
            f"TIER 1 Complete search for user {current_user.id}: "
            f"query='{search_request.query[:50]}', "
            f"results={len(search_results)}, "
            f"time={execution_time:.2f}ms"
        )

        return SearchResponse(
            query=search_request.query,
            results=search_results,
            total_results=len(search_results),
            execution_time_ms=round(execution_time, 2),
            filters_applied=filters_applied,
            pipeline_summary=pipeline_summary
        )

    except Exception as e:
        logger.error(f"Reranked search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reranked search failed: {str(e)}"
        )
