"""
KnowledgeTree Backend - Embedding Generation Service
Generate BGE-M3 embeddings for text chunks
"""

import logging
import numpy as np
from typing import List, Union
from FlagEmbedding import BGEM3FlagModel
from core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    BGE-M3 embedding generation service with contextual embeddings support

    TIER 1 Advanced RAG - Phase 4: Contextual Embeddings
    - Supports generating embeddings with surrounding context
    - Improves semantic understanding by including chunk_before + text + chunk_after
    """

    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL
        self.dimensions = settings.EMBEDDING_DIMENSIONS
        self.device = settings.EMBEDDING_DEVICE
        self.model = None

    def load_model(self):
        """
        Load BGE-M3 model

        This is called lazily on first use to avoid loading
        the model on application startup
        """
        if self.model is None:
            logger.info(f"Loading BGE-M3 model: {self.model_name}")
            self.model = BGEM3FlagModel(
                self.model_name,
                use_fp16=(self.device == "cuda")  # Use FP16 on GPU
            )
            logger.info(f"Model loaded successfully on {self.device}")

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Input text

        Returns:
            List of floats (embedding vector)
        """
        if not text or not text.strip():
            raise ValueError("Cannot generate embedding for empty text")

        # Load model if not already loaded
        self.load_model()

        # Generate embedding
        embeddings = self.model.encode(
            [text],
            batch_size=1,
            max_length=8192  # BGE-M3 supports up to 8192 tokens
        )

        # Extract dense embedding (1024 dimensions)
        embedding = embeddings['dense_vecs'][0]

        # Ensure correct dimensions
        if len(embedding) != self.dimensions:
            raise ValueError(f"Embedding dimension mismatch: {len(embedding)} != {self.dimensions}")

        # Convert to list
        return embedding.tolist()

    def generate_contextual_embedding(
        self,
        text: str,
        chunk_before: str = None,
        chunk_after: str = None
    ) -> List[float]:
        """
        Generate contextual embedding with surrounding chunks (TIER 1 Phase 4)

        Combines chunk_before + text + chunk_after to create richer semantic context.
        Improves retrieval accuracy by embedding chunks with their surrounding context.

        Args:
            text: Main chunk text
            chunk_before: Previous chunk text (optional)
            chunk_after: Next chunk text (optional)

        Returns:
            List of floats (contextual embedding vector)

        Example:
            chunk_before = "JWT stands for JSON Web Token..."
            text = "Authentication in modern web applications..."
            chunk_after = "The token contains three parts..."

            # Generates embedding for:
            # "[BEFORE] JWT stands for JSON Web Token... [MAIN] Authentication in modern web applications... [AFTER] The token contains three parts..."
        """
        if not text or not text.strip():
            raise ValueError("Cannot generate embedding for empty text")

        # Build contextual text
        contextual_parts = []

        if chunk_before and chunk_before.strip():
            contextual_parts.append(f"[BEFORE] {chunk_before.strip()}")

        contextual_parts.append(f"[MAIN] {text.strip()}")

        if chunk_after and chunk_after.strip():
            contextual_parts.append(f"[AFTER] {chunk_after.strip()}")

        contextual_text = " ".join(contextual_parts)

        # Log context usage
        logger.debug(
            f"Generating contextual embedding: "
            f"before={'✓' if chunk_before else '✗'}, "
            f"after={'✓' if chunk_after else '✗'}, "
            f"total_length={len(contextual_text)}"
        )

        # Generate embedding using standard method
        return self.generate_embedding(contextual_text)

    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches

        Args:
            texts: List of input texts
            batch_size: Number of texts to process at once

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # Filter out empty texts
        valid_indices = [i for i, text in enumerate(texts) if text and text.strip()]
        valid_texts = [texts[i] for i in valid_indices]

        if not valid_texts:
            logger.warning("All texts are empty, returning empty list")
            return [None] * len(texts)

        # Load model if not already loaded
        self.load_model()

        # Generate embeddings in batches
        all_embeddings = []
        for i in range(0, len(valid_texts), batch_size):
            batch = valid_texts[i:i + batch_size]
            logger.info(f"Processing batch {i // batch_size + 1}/{(len(valid_texts) + batch_size - 1) // batch_size}")

            embeddings = self.model.encode(
                batch,
                batch_size=batch_size,
                max_length=8192
            )

            # Extract dense embeddings
            batch_embeddings = embeddings['dense_vecs']
            all_embeddings.extend([emb.tolist() for emb in batch_embeddings])

        # Reconstruct full list with None for empty texts
        result = [None] * len(texts)
        for i, idx in enumerate(valid_indices):
            result[idx] = all_embeddings[i]

        logger.info(f"Generated {len(all_embeddings)} embeddings from {len(texts)} texts")
        return result

    def get_model_info(self) -> dict:
        """
        Get model information

        Returns:
            Dictionary with model metadata
        """
        return {
            "model_name": self.model_name,
            "dimensions": self.dimensions,
            "device": self.device,
            "loaded": self.model is not None
        }
