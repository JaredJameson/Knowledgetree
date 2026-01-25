"""
KnowledgeTree Backend - Search Schemas
Pydantic models for semantic search requests and responses
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SearchRequest(BaseModel):
    """Search request with query and filters"""
    query: str = Field(..., min_length=1, max_length=1000, description="Search query text")
    project_id: int = Field(..., description="Project to search within")
    category_id: Optional[int] = Field(None, description="Optional category filter")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results")
    min_similarity: float = Field(0.5, ge=0.0, le=1.0, description="Minimum similarity threshold")


class SearchResult(BaseModel):
    """Single search result with chunk and metadata"""
    chunk_id: int = Field(..., description="Chunk ID")
    document_id: int = Field(..., description="Document ID")
    document_title: Optional[str] = Field(None, description="Document title")
    document_filename: str = Field(..., description="Document filename")
    chunk_text: str = Field(..., description="Chunk text content")
    chunk_index: int = Field(..., description="Chunk position in document")
    similarity_score: float = Field(..., description="Cosine similarity score (0-1)")
    chunk_metadata: Optional[dict] = Field(None, description="Chunk metadata (page, section, etc.)")
    document_created_at: datetime = Field(..., description="Document upload timestamp")

    # TIER 1 Advanced RAG - Hybrid Search fields
    rrf_score: Optional[float] = Field(None, description="RRF fusion score (for hybrid search)")
    source: Optional[str] = Field(None, description="Result source: dense, sparse, or hybrid")
    dense_score: Optional[float] = Field(None, description="Dense retrieval score")
    sparse_score: Optional[float] = Field(None, description="Sparse retrieval (BM25) score")

    # TIER 1 Advanced RAG - Cross-Encoder Reranking fields
    cross_encoder_score: Optional[float] = Field(None, description="Cross-encoder relevance score (0-1)")
    original_rank: Optional[int] = Field(None, description="Original rank before reranking")

    # TIER 2 Enhanced RAG - Conditional Reranking fields
    confidence_level: Optional[str] = Field(None, description="Confidence level: high, medium, or low")
    skip_metrics: Optional[dict] = Field(None, description="Conditional reranking skip metrics")

    # TIER 2 Enhanced RAG - Explainability fields
    explanation: Optional[dict] = Field(None, description="Detailed explanation of retrieval and ranking")
    rank: Optional[int] = Field(None, description="Result rank in final list")

    # TIER 2 Enhanced RAG - Query Expansion fields
    query_expansion: Optional[dict] = Field(None, description="Query expansion metadata")

    # TIER 2 Enhanced RAG - CRAG fields
    crag_evaluation: Optional[dict] = Field(None, description="CRAG retrieval quality evaluation")
    crag_improvement: Optional[dict] = Field(None, description="CRAG improvement metrics after correction")

    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    """Search response with results and metadata"""
    query: str = Field(..., description="Original search query")
    results: List[SearchResult] = Field(..., description="Search results")
    total_results: int = Field(..., description="Total number of results found")
    execution_time_ms: float = Field(..., description="Search execution time in milliseconds")
    filters_applied: dict = Field(..., description="Applied filters summary")

    # TIER 2 Enhanced RAG - Pipeline summary
    pipeline_summary: Optional[dict] = Field(None, description="Summary of retrieval pipeline performance")


class SearchStatistics(BaseModel):
    """Search statistics for a project"""
    total_documents: int = Field(..., description="Total documents in project")
    total_chunks: int = Field(..., description="Total chunks available for search")
    embedded_chunks: int = Field(..., description="Chunks with embeddings")
    average_chunk_length: float = Field(..., description="Average chunk text length")
    total_storage_mb: float = Field(..., description="Total vector storage size in MB")


class HybridSearchRequest(BaseModel):
    """
    Hybrid search request with dense + sparse retrieval (TIER 1 Advanced RAG)

    Combines semantic (vector) and keyword (BM25) search with Reciprocal Rank Fusion (RRF).
    """
    query: str = Field(..., min_length=1, max_length=1000, description="Search query text")
    project_id: int = Field(..., description="Project to search within")
    category_id: Optional[int] = Field(None, description="Optional category filter")
    limit: int = Field(10, ge=1, le=100, description="Final number of results to return")
    top_k_retrieve: int = Field(20, ge=1, le=100, description="Number of candidates from each method")
    min_similarity: float = Field(0.5, ge=0.0, le=1.0, description="Minimum similarity for dense search")
    min_bm25_score: float = Field(0.0, ge=0.0, description="Minimum BM25 score for sparse search")
    dense_weight: Optional[float] = Field(None, ge=0.0, le=1.0, description="Dense retrieval weight (default: 0.6)")
    sparse_weight: Optional[float] = Field(None, ge=0.0, le=1.0, description="Sparse retrieval weight (default: 0.4)")


class RerankSearchRequest(BaseModel):
    """
    Complete TIER 1 Advanced RAG search with cross-encoder reranking

    Three-stage pipeline:
    1. Hybrid retrieval (dense + sparse + RRF) → top-20 candidates
    2. Cross-encoder reranking → precise relevance scoring
    3. Return top-k most relevant results

    This is the most accurate search method.
    """
    query: str = Field(..., min_length=1, max_length=1000, description="Search query text")
    project_id: int = Field(..., description="Project to search within")
    category_id: Optional[int] = Field(None, description="Optional category filter")
    limit: int = Field(5, ge=1, le=20, description="Final number of results (default: 5)")
    retrieval_limit: int = Field(20, ge=5, le=100, description="Candidates from hybrid search (default: 20)")
    min_similarity: float = Field(0.5, ge=0.0, le=1.0, description="Minimum similarity for dense search")
    min_bm25_score: float = Field(0.0, ge=0.0, description="Minimum BM25 score for sparse search")
    min_cross_encoder_score: float = Field(0.0, ge=-10.0, le=10.0, description="Minimum cross-encoder score")
    dense_weight: Optional[float] = Field(None, ge=0.0, le=1.0, description="Dense retrieval weight (default: 0.6)")
    sparse_weight: Optional[float] = Field(None, ge=0.0, le=1.0, description="Sparse retrieval weight (default: 0.4)")

    # TIER 2 Enhanced RAG - Query Expansion parameters
    use_query_expansion: bool = Field(True, description="Enable query expansion with synonyms")
    expansion_strategy: str = Field("balanced", description="Expansion strategy: conservative, balanced, or aggressive")

    # TIER 2 Enhanced RAG - CRAG parameters
    use_crag: bool = Field(True, description="Enable CRAG (Corrective RAG) with self-reflection")
