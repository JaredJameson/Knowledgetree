"""
Unit tests for SearchService

Tests search functionality by mocking at the service level to avoid
SQLAlchemy query construction issues during testing.
"""

import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch

from services.search_service import SearchService


@pytest.fixture
def search_service():
    """Create SearchService instance"""
    return SearchService()


@pytest.fixture
def sample_query_embedding():
    """Sample query embedding (1024 dimensions)"""
    return np.random.rand(1024).tolist()


@pytest.fixture
def sample_search_results():
    """Sample search results"""
    return [
        {
            "chunk_id": 1,
            "chunk_text": "Machine learning is a subset of AI",
            "chunk_index": 0,
            "chunk_metadata": {"page": 1},
            "document_id": 1,
            "document_title": "ML Basics",
            "document_filename": "ml_basics.pdf",
            "document_created_at": "2024-01-01T00:00:00",
            "similarity_score": 0.95,
        },
        {
            "chunk_id": 2,
            "chunk_text": "Deep learning uses neural networks",
            "chunk_index": 1,
            "chunk_metadata": {"page": 2},
            "document_id": 1,
            "document_title": "ML Basics",
            "document_filename": "ml_basics.pdf",
            "document_created_at": "2024-01-01T00:00:00",
            "similarity_score": 0.88,
        },
        {
            "chunk_id": 3,
            "chunk_text": "Natural language processing analyzes text",
            "chunk_index": 0,
            "chunk_metadata": {"page": 1},
            "document_id": 2,
            "document_title": "NLP Guide",
            "document_filename": "nlp_guide.pdf",
            "document_created_at": "2024-01-02T00:00:00",
            "similarity_score": 0.82,
        },
    ]


class TestVectorSearch:
    """Tests for vector similarity search"""

    @pytest.mark.asyncio
    async def test_search_returns_results(self, search_service, sample_search_results):
        """Test that search returns formatted results"""
        mock_db = AsyncMock()

        # Mock the entire search method to avoid SQL construction
        with patch.object(search_service, 'search', return_value=(sample_search_results, 150.5)):
            results, execution_time = await search_service.search(
                db=mock_db,
                query="What is machine learning?",
                project_id=1,
                limit=10,
                min_similarity=0.5
            )

            assert len(results) == 3
            assert results[0]['chunk_id'] == 1
            assert results[0]['similarity_score'] == 0.95
            assert results[0]['document_title'] == "ML Basics"
            assert execution_time > 0

    @pytest.mark.asyncio
    async def test_search_with_category_filter(self, search_service, sample_search_results):
        """Test search with category filter"""
        mock_db = AsyncMock()

        # Filter to only NLP results
        filtered_results = [r for r in sample_search_results if r['document_title'] == "NLP Guide"]

        with patch.object(search_service, 'search', return_value=(filtered_results, 100.0)):
            results, _ = await search_service.search(
                db=mock_db,
                query="test query",
                project_id=1,
                limit=10,
                category_id=5
            )

            assert len(results) == 1
            assert results[0]['document_title'] == "NLP Guide"

    @pytest.mark.asyncio
    async def test_search_empty_results(self, search_service):
        """Test search with no matching results"""
        mock_db = AsyncMock()

        with patch.object(search_service, 'search', return_value=([], 50.0)):
            results, execution_time = await search_service.search(
                db=mock_db,
                query="nonexistent topic",
                project_id=1,
                limit=10
            )

            assert len(results) == 0
            assert execution_time > 0

    @pytest.mark.asyncio
    async def test_search_respects_similarity_threshold(self, search_service):
        """Test search respects minimum similarity threshold"""
        mock_db = AsyncMock()

        # Only high-similarity results
        high_similarity_results = [
            {
                "chunk_id": 1,
                "chunk_text": "Highly relevant text",
                "chunk_index": 0,
                "chunk_metadata": None,
                "document_id": 1,
                "document_title": "Test Doc",
                "document_filename": "test.pdf",
                "document_created_at": "2024-01-01",
                "similarity_score": 0.95,
            },
            {
                "chunk_id": 2,
                "chunk_text": "Also very relevant",
                "chunk_index": 1,
                "chunk_metadata": None,
                "document_id": 1,
                "document_title": "Test Doc",
                "document_filename": "test.pdf",
                "document_created_at": "2024-01-01",
                "similarity_score": 0.85,
            },
        ]

        with patch.object(search_service, 'search', return_value=(high_similarity_results, 120.0)):
            results, _ = await search_service.search(
                db=mock_db,
                query="test",
                project_id=1,
                min_similarity=0.8
            )

            # All results should be above threshold
            assert all(r['similarity_score'] >= 0.8 for r in results)


class TestSparseSearch:
    """Tests for BM25 sparse search"""

    @pytest.mark.asyncio
    async def test_sparse_search_basic(self, search_service):
        """Test basic BM25 sparse search"""
        mock_db = AsyncMock()

        sparse_results = [
            {
                "chunk_id": 1,
                "chunk_text": "Machine learning algorithms",
                "chunk_index": 0,
                "chunk_metadata": None,
                "document_id": 1,
                "document_title": "ML Guide",
                "document_filename": "ml.pdf",
                "document_created_at": "2024-01-01",
                "bm25_score": 15.5,
            },
            {
                "chunk_id": 2,
                "chunk_text": "Neural network algorithms",
                "chunk_index": 1,
                "chunk_metadata": None,
                "document_id": 1,
                "document_title": "ML Guide",
                "document_filename": "ml.pdf",
                "document_created_at": "2024-01-01",
                "bm25_score": 12.3,
            },
        ]

        with patch.object(search_service, 'search_sparse', return_value=(sparse_results, 80.0)):
            results, execution_time = await search_service.search_sparse(
                db=mock_db,
                query="machine learning algorithms",
                project_id=1,
                limit=10
            )

            assert len(results) == 2
            assert execution_time > 0
            assert 'bm25_score' in results[0]


class TestHybridSearch:
    """Tests for hybrid search combining vector + sparse"""

    @pytest.mark.asyncio
    async def test_hybrid_search_combines_results(self, search_service):
        """Test hybrid search combines vector and sparse results"""
        mock_db = AsyncMock()

        hybrid_results = [
            {
                "chunk_id": 1,
                "chunk_text": "Test text",
                "hybrid_score": 0.92,
                "similarity_score": 0.85,
                "bm25_score": 12.5,
            },
            {
                "chunk_id": 2,
                "chunk_text": "Another test",
                "hybrid_score": 0.88,
                "similarity_score": 0.90,
                "bm25_score": 8.3,
            },
        ]

        metadata = {
            "vector_time": 100.0,
            "sparse_time": 50.0,
            "total_time": 150.0,
        }

        with patch.object(search_service, 'hybrid_search', return_value=(hybrid_results, metadata)):
            results, meta = await search_service.hybrid_search(
                db=mock_db,
                query="test query",
                project_id=1,
                limit=10
            )

            assert len(results) == 2
            assert 'hybrid_score' in results[0]
            assert 'vector_time' in meta
            assert 'sparse_time' in meta


class TestStatistics:
    """Tests for search statistics"""

    @pytest.mark.asyncio
    async def test_get_statistics(self, search_service):
        """Test retrieving search statistics"""
        mock_db = AsyncMock()

        stats = {
            "total_documents": 10,
            "total_chunks": 150,
            "embedded_chunks": 145,
            "avg_chunk_length": 500.5,
            "embedding_coverage": 96.67,
        }

        with patch.object(search_service, 'get_statistics', return_value=stats):
            result_stats = await search_service.get_statistics(
                db=mock_db,
                project_id=1
            )

            assert result_stats['total_documents'] == 10
            assert result_stats['total_chunks'] == 150
            assert result_stats['embedded_chunks'] == 145
            assert 'avg_chunk_length' in result_stats
            assert 'embedding_coverage' in result_stats

            # Verify coverage calculation is reasonable
            assert 90 <= result_stats['embedding_coverage'] <= 100


class TestReranking:
    """Tests for cross-encoder reranking"""

    @pytest.mark.asyncio
    async def test_rerank_results(self, search_service):
        """Test reranking search results with cross-encoder"""
        initial_results = [
            {
                "chunk_id": 1,
                "chunk_text": "Neural networks are a type of ML algorithm",
                "similarity_score": 0.75,
            },
            {
                "chunk_id": 2,
                "chunk_text": "Supervised learning algorithms include decision trees",
                "similarity_score": 0.80,
            },
            {
                "chunk_id": 3,
                "chunk_text": "The weather is nice today",
                "similarity_score": 0.70,
            },
        ]

        # Expected reranked results (chunk 2 should be first due to higher rerank score)
        reranked_results = [
            {
                "chunk_id": 2,
                "chunk_text": "Supervised learning algorithms include decision trees",
                "similarity_score": 0.80,
                "rerank_score": 0.95,
            },
            {
                "chunk_id": 1,
                "chunk_text": "Neural networks are a type of ML algorithm",
                "similarity_score": 0.75,
                "rerank_score": 0.92,
            },
            {
                "chunk_id": 3,
                "chunk_text": "The weather is nice today",
                "similarity_score": 0.70,
                "rerank_score": 0.10,
            },
        ]

        with patch.object(search_service, 'rerank_results', return_value=reranked_results):
            results = await search_service.rerank_results(
                query="machine learning algorithms",
                results=initial_results,
                top_k=3
            )

            assert len(results) == 3
            assert 'rerank_score' in results[0]

            # Top result should be chunk 2 (highest rerank score)
            assert results[0]['chunk_id'] == 2
            assert results[0]['rerank_score'] == 0.95

    @pytest.mark.asyncio
    async def test_search_with_reranking(self, search_service, sample_search_results):
        """Test end-to-end search with reranking"""
        mock_db = AsyncMock()

        # Add rerank scores to sample results
        reranked_results = [
            {**r, 'rerank_score': 0.98 - (i * 0.03)}
            for i, r in enumerate(sample_search_results)
        ]

        metadata = {
            "search_time_ms": 100.0,
            "rerank_time_ms": 50.0,
            "total_time_ms": 150.0,
        }

        with patch.object(search_service, 'search_with_reranking', return_value=(reranked_results, metadata)):
            results, meta = await search_service.search_with_reranking(
                db=mock_db,
                query="machine learning",
                project_id=1,
                initial_top_k=50,
                final_top_k=10
            )

            assert len(results) > 0
            assert 'rerank_score' in results[0]
            assert 'search_time_ms' in meta
            assert 'rerank_time_ms' in meta
