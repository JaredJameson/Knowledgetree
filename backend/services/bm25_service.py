"""
BM25 Sparse Retrieval Service for KnowledgeTree

Implements BM25Okapi keyword-based search to complement dense vector retrieval.
Part of TIER 1 Advanced RAG implementation.

Key Features:
- Polish-aware tokenization (simple word splitting for MVP)
- In-memory BM25 index for fast keyword matching
- Async interface compatible with FastAPI
- Returns results with BM25 scores

Reference: ALURON project hybrid RAG implementation
"""

from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
import numpy as np
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.chunk import Chunk

logger = logging.getLogger(__name__)


class BM25Service:
    """
    BM25Okapi sparse retrieval service.

    Provides keyword-based search using BM25 algorithm to capture exact term matches
    that semantic embeddings might miss.

    Usage:
        bm25 = BM25Service()
        await bm25.initialize(db_session)
        results = await bm25.search("JWT authentication API", top_k=20)
    """

    def __init__(self):
        """Initialize BM25 service (index built during initialize())."""
        self.bm25_index: Optional[BM25Okapi] = None
        self.doc_ids: List[int] = []
        self.documents: List[Chunk] = []
        self.is_initialized = False

    async def initialize(self, db_session: AsyncSession) -> None:
        """
        Build BM25 index from all document chunks in database.

        This should be called once at application startup.

        Args:
            db_session: Database session for fetching chunks
        """
        logger.info("🔄 Initializing BM25 index...")

        try:
            # Fetch all document chunks with embeddings
            stmt = select(Chunk).where(Chunk.has_embedding == 1).order_by(Chunk.id)
            result = await db_session.execute(stmt)
            chunks = result.scalars().all()

            if not chunks:
                logger.warning("⚠️ No chunks found in database - BM25 index empty")
                self.is_initialized = True
                return

            # Tokenize corpus for BM25
            tokenized_corpus = [
                self._tokenize(chunk.text)  # Use 'text' field from Chunk model
                for chunk in chunks
            ]

            # Build BM25 index
            self.bm25_index = BM25Okapi(tokenized_corpus)
            self.doc_ids = [chunk.id for chunk in chunks]
            self.documents = list(chunks)  # Store chunks for retrieval

            self.is_initialized = True
            logger.info(f"✅ BM25 index built with {len(chunks)} chunks")

        except Exception as e:
            logger.error(f"❌ Failed to initialize BM25 index: {e}")
            raise

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text for BM25 indexing.

        Current implementation: Simple lowercase word splitting.
        Future enhancement: Polish-aware stemming/lemmatization with spaCy.

        Args:
            text: Input text to tokenize

        Returns:
            List of tokens (lowercase words)
        """
        # MVP: Simple tokenization
        # Remove punctuation and split on whitespace
        import re
        text = text.lower()
        # Keep alphanumeric characters and spaces
        text = re.sub(r'[^a-ząćęłńóśźż0-9\s]', ' ', text)
        tokens = text.split()
        return tokens

    async def search(
        self,
        query: str,
        top_k: int = 20,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search documents using BM25 keyword matching.

        Args:
            query: Search query string
            top_k: Number of top results to return
            min_score: Minimum BM25 score threshold (optional filter)

        Returns:
            List of search results with BM25 scores, sorted by relevance

        Example:
            results = await bm25.search("JWT authentication", top_k=20)
            # [
            #     {
            #         "id": 123,
            #         "chunk_id": "chunk_abc",
            #         "content": "JWT authentication...",
            #         "score": 15.42,
            #         "source": "sparse"
            #     },
            #     ...
            # ]
        """
        if not self.is_initialized:
            logger.warning("⚠️ BM25 not initialized - returning empty results")
            return []

        if not self.bm25_index:
            logger.warning("⚠️ BM25 index is empty - returning empty results")
            return []

        try:
            # Tokenize query
            query_tokens = self._tokenize(query)

            if not query_tokens:
                logger.warning(f"⚠️ Query tokenization resulted in empty tokens: {query}")
                return []

            # Get BM25 scores for all documents
            scores = self.bm25_index.get_scores(query_tokens)

            # Get top-k indices sorted by score (descending)
            top_indices = np.argsort(scores)[-top_k:][::-1]

            # Build results
            results = []
            for idx in top_indices:
                score = float(scores[idx])

                # Apply min_score filter
                if score < min_score:
                    continue

                # Get document chunk
                chunk = self.documents[idx]

                result = {
                    "id": chunk.id,
                    "chunk_id": chunk.id,  # Use chunk.id as chunk_id
                    "document_id": chunk.document_id,
                    "document_type": None,  # Not available in Chunk model
                    "title": None,  # Not available in Chunk model
                    "content": chunk.text,  # Use 'text' field from Chunk model
                    "page_number": None,  # Not available in Chunk model
                    "section_name": None,  # Not available in Chunk model
                    "product_codes": None,  # Not available in Chunk model
                    "parameters": None,  # Not available in Chunk model
                    "standards": None,  # Not available in Chunk model
                    "chunk_metadata": chunk.chunk_metadata,  # Metadata JSON string
                    "score": score,
                    "source": "sparse",  # Mark as BM25 result
                }
                results.append(result)

            logger.info(
                f"🔍 BM25 search: query='{query[:50]}...', "
                f"tokens={len(query_tokens)}, results={len(results)}, "
                f"top_score={results[0]['score']:.2f if results else 0:.2f}"
            )

            return results

        except Exception as e:
            logger.error(f"❌ BM25 search failed: {e}")
            return []

    async def rebuild_index(self, db_session: AsyncSession) -> None:
        """
        Rebuild BM25 index from scratch.

        Use this when documents are added/updated/deleted.

        Args:
            db_session: Database session for fetching chunks
        """
        logger.info("🔄 Rebuilding BM25 index...")
        self.is_initialized = False
        self.bm25_index = None
        self.doc_ids = []
        self.documents = []

        await self.initialize(db_session)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get BM25 index statistics.

        Returns:
            Statistics dictionary with index info
        """
        return {
            "initialized": self.is_initialized,
            "num_documents": len(self.documents),
            "index_size_mb": len(str(self.doc_ids)) / (1024 * 1024) if self.doc_ids else 0,
        }


# Global singleton instance (initialized at startup)
bm25_service = BM25Service()
