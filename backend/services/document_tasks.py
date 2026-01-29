"""
KnowledgeTree - Document Processing Tasks
Celery tasks for background document processing
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from sqlalchemy import select
from sqlalchemy.sql import func

from core.celery_app import celery_app
from core.database import AsyncSessionLocal
from models.document import Document, ProcessingStatus
from models.chunk import Chunk
from services.pdf_processor import PDFProcessor
from services.text_chunker import TextChunker
from services.embedding_generator import EmbeddingGenerator
import logging

logger = logging.getLogger(__name__)

# Initialize services
pdf_processor = PDFProcessor()
text_chunker = TextChunker()
embedding_generator = EmbeddingGenerator()


@celery_app.task(name="services.document_tasks.process_document_task", bind=True)
def process_document_task(self, document_id: int) -> Dict[str, Any]:
    """
    Process a document in the background (PDF extraction, chunking, embeddings)

    This task runs in a Celery worker process to avoid blocking the FastAPI event loop.

    Args:
        document_id: ID of document to process

    Returns:
        Processing results with status
    """
    # Run async function in new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(
            _process_document_async(self, document_id)
        )
        return result
    except Exception as e:
        logger.error(f"Document processing task failed: {str(e)}")
        # Update document status to failed
        loop.run_until_complete(_mark_document_failed(document_id, str(e)))
        raise
    finally:
        loop.close()


async def _process_document_async(task, document_id: int) -> Dict[str, Any]:
    """Async implementation of document processing"""
    async with AsyncSessionLocal() as db:
        # Get document
        result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()

        if not document:
            return {"error": "Document not found", "document_id": document_id}

        try:
            # Update status to processing
            document.processing_status = ProcessingStatus.PROCESSING
            await db.commit()

            logger.info(f"Starting document processing: {document_id}")

            # Step 1: Extract text from PDF with intelligent tool selection
            pdf_path = Path(document.file_path)
            if not pdf_path.exists():
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")

            # Run PDF processing in thread to avoid event loop conflicts with Docling
            extracted_text, page_count, extraction_metadata = await asyncio.to_thread(
                pdf_processor.process_pdf,
                pdf_path,
                auto_detect=True  # Enable intelligent document classification
            )

            # Log extraction metadata
            doc_type = extraction_metadata.get('document_type', 'unknown')
            tool_used = extraction_metadata.get('extraction_tool', 'unknown')
            confidence = extraction_metadata.get('classification_confidence', 0)
            reasoning = extraction_metadata.get('classification_reasoning', '')

            logger.info(
                f"Document {document_id}: Extracted text from {page_count} pages\n"
                f"  Type: {doc_type} (confidence: {confidence:.0%})\n"
                f"  Tool: {tool_used}\n"
                f"  Reasoning: {reasoning}"
            )

            # Store extraction metadata in document record
            document.extraction_metadata = extraction_metadata
            await db.commit()

            # Update progress (Step 1: 10% complete)
            task.update_state(
                state='PROGRESS',
                meta={
                    'current': 1,
                    'total': 3,
                    'status': 'Text extraction complete',
                    'step': 'extraction',
                    'percentage': 10,
                    'page_count': page_count,
                    'document_type': doc_type,
                    'extraction_tool': tool_used,
                    'message': f'Extracted text from {page_count} pages using {tool_used} ({doc_type})'
                }
            )

            # Step 2: Chunk the text with contextual information
            chunks_data = text_chunker.chunk_text(extracted_text, document.id)
            logger.info(f"Document {document_id}: Created {len(chunks_data)} chunks")

            # Update progress (Step 2: 15% complete)
            task.update_state(
                state='PROGRESS',
                meta={
                    'current': 2,
                    'total': 3,
                    'status': 'Chunking complete',
                    'step': 'chunking',
                    'percentage': 15,
                    'chunk_count': len(chunks_data),
                    'message': f'Created {len(chunks_data)} text chunks'
                }
            )

            # Step 3: Generate contextual embeddings for chunks
            logger.info(f"Document {document_id}: Generating embeddings...")
            embeddings = []
            for i, chunk_data in enumerate(chunks_data):
                try:
                    # Generate contextual embedding (5-7 seconds per chunk)
                    embedding = embedding_generator.generate_contextual_embedding(
                        text=chunk_data["text"],
                        chunk_before=chunk_data.get("chunk_before"),
                        chunk_after=chunk_data.get("chunk_after")
                    )
                    embeddings.append(embedding)

                    # Update progress every chunk (embedding is the longest step: 15-90%)
                    # Calculate percentage: 15% (start) + 75% * (progress / total)
                    percentage = 15 + int(75 * (i + 1) / len(chunks_data))
                    task.update_state(
                        state='PROGRESS',
                        meta={
                            'current': 2,
                            'total': 3,
                            'status': 'Generating embeddings',
                            'step': 'embeddings',
                            'percentage': percentage,
                            'chunks_processed': i + 1,
                            'chunks_total': len(chunks_data),
                            'message': f'Generated {i+1}/{len(chunks_data)} embeddings ({percentage}%)'
                        }
                    )
                except Exception as e:
                    logger.error(f"Document {document_id}: Failed to generate embedding for chunk {i}: {e}")
                    embeddings.append(None)

            logger.info(f"Document {document_id}: Generated {len([e for e in embeddings if e])} embeddings")

            # Step 4: Store chunks with embeddings in database (90-95%)
            task.update_state(
                state='PROGRESS',
                meta={
                    'current': 3,
                    'total': 3,
                    'status': 'Storing chunks in database',
                    'step': 'storage',
                    'percentage': 90,
                    'message': f'Storing {len(chunks_data)} chunks in database'
                }
            )
            
            chunks_created = 0
            for i, chunk_data in enumerate(chunks_data):
                embedding = embeddings[i]

                # Skip if embedding generation failed
                if embedding is None:
                    logger.warning(f"Document {document_id}: Skipping chunk {i} - embedding generation failed")
                    continue

                chunk = Chunk(
                    text=chunk_data["text"],
                    chunk_metadata=json.dumps(chunk_data["chunk_metadata"]),
                    chunk_before=chunk_data.get("chunk_before"),
                    chunk_after=chunk_data.get("chunk_after"),
                    embedding=embedding,
                    has_embedding=1,
                    chunk_index=chunk_data["chunk_index"],
                    document_id=document.id
                )
                db.add(chunk)
                chunks_created += 1

            # Update document status to completed
            document.page_count = page_count
            document.processing_status = ProcessingStatus.COMPLETED
            document.processed_at = func.now()
            await db.commit()
            
            # Final progress update (100%)
            task.update_state(
                state='SUCCESS',
                meta={
                    'current': 3,
                    'total': 3,
                    'status': 'Processing complete',
                    'step': 'completed',
                    'percentage': 100,
                    'page_count': page_count,
                    'chunks_created': chunks_created,
                    'message': f'Successfully processed {page_count} pages into {chunks_created} chunks'
                }
            )
            
            logger.info(f"Document {document_id}: Processing completed - {page_count} pages, {chunks_created} chunks")

            return {
                "document_id": document_id,
                "status": "completed",
                "page_count": page_count,
                "chunks_created": chunks_created,
                "chunks_failed": len(chunks_data) - chunks_created
            }

        except Exception as e:
            logger.error(f"Document {document_id}: Processing failed: {str(e)}")
            document.processing_status = ProcessingStatus.FAILED
            document.error_message = str(e)
            await db.commit()
            raise


async def _mark_document_failed(document_id: int, error_message: str):
    """Mark document as failed in database"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()

        if document:
            document.processing_status = ProcessingStatus.FAILED
            document.error_message = error_message
            await db.commit()
