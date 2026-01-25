"""
KnowledgeTree Backend - Text Chunking Service
Split documents into chunks for embedding generation
"""

import logging
import re
from typing import List, Dict
from core.config import settings

logger = logging.getLogger(__name__)


class TextChunker:
    """
    Text chunking service with overlap and contextual information

    TIER 1 Advanced RAG - Phase 4: Contextual Embeddings
    - Stores surrounding chunks (chunk_before, chunk_after)
    - Enables contextual embedding generation
    """

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        include_context: bool = True
    ):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        self.include_context = include_context  # TIER 1 Phase 4: Enable contextual info

    def chunk_text(self, text: str, document_id: int) -> List[Dict]:
        """
        Split text into chunks with overlap

        Args:
            text: Full document text
            document_id: Database document ID

        Returns:
            List of chunk dictionaries with metadata
        """
        if not text or not text.strip():
            logger.warning(f"Empty text provided for document {document_id}")
            return []

        # Clean text
        text = self._clean_text(text)

        # Split into chunks
        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            # Extract chunk
            end = start + self.chunk_size
            chunk_text = text[start:end]

            # Try to end at sentence boundary if possible
            if end < len(text):
                # Look for sentence endings within last 100 characters
                last_period = chunk_text.rfind('. ')
                last_newline = chunk_text.rfind('\n')
                boundary = max(last_period, last_newline)

                if boundary > self.chunk_size - 100:
                    # Use sentence boundary
                    chunk_text = chunk_text[:boundary + 1].strip()
                    end = start + len(chunk_text)

            # Create chunk metadata
            chunk = {
                "text": chunk_text.strip(),
                "chunk_index": chunk_index,
                "document_id": document_id,
                "chunk_metadata": {
                    "start_char": start,
                    "end_char": end,
                    "length": len(chunk_text),
                }
            }

            chunks.append(chunk)
            chunk_index += 1

            # Move to next chunk with overlap
            start = end - self.chunk_overlap

            # Avoid infinite loop
            if start >= len(text) - self.chunk_overlap:
                break

        # TIER 1 Phase 4: Add contextual information (chunk_before, chunk_after)
        if self.include_context and len(chunks) > 1:
            for i, chunk in enumerate(chunks):
                # Add previous chunk text (if not first chunk)
                if i > 0:
                    chunk["chunk_before"] = chunks[i - 1]["text"]
                else:
                    chunk["chunk_before"] = None

                # Add next chunk text (if not last chunk)
                if i < len(chunks) - 1:
                    chunk["chunk_after"] = chunks[i + 1]["text"]
                else:
                    chunk["chunk_after"] = None

            logger.info(
                f"Created {len(chunks)} chunks with contextual information for document {document_id}"
            )
        else:
            logger.info(f"Created {len(chunks)} chunks for document {document_id}")

        return chunks

    def _clean_text(self, text: str) -> str:
        """
        Clean text for chunking

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove control characters
        text = ''.join(char for char in text if char.isprintable() or char in '\n\r\t')

        # Normalize line breaks
        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r'\r', '\n', text)

        # Remove excessive newlines (keep max 2)
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()

    def chunk_by_pages(
        self,
        text: str,
        document_id: int,
        page_separator: str = "--- Page"
    ) -> List[Dict]:
        """
        Split text by pages, then chunk each page

        Args:
            text: Full document text with page markers
            document_id: Database document ID
            page_separator: Page marker string

        Returns:
            List of chunk dictionaries with page metadata
        """
        # Split by pages
        pages = text.split(page_separator)
        all_chunks = []
        global_chunk_index = 0

        for page_num, page_text in enumerate(pages):
            if not page_text.strip():
                continue

            # Extract page number from marker if present
            page_match = re.match(r'\s*(\d+)\s*---', page_text)
            if page_match:
                page_number = int(page_match.group(1))
                page_text = page_text[page_match.end():]
            else:
                page_number = page_num

            # Chunk this page
            page_chunks = self.chunk_text(page_text, document_id)

            # Add page metadata
            for chunk in page_chunks:
                chunk["chunk_index"] = global_chunk_index
                chunk["chunk_metadata"]["page_number"] = page_number
                all_chunks.append(chunk)
                global_chunk_index += 1

        logger.info(f"Created {len(all_chunks)} chunks from {len(pages)} pages for document {document_id}")
        return all_chunks
