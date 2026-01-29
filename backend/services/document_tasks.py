"""
KnowledgeTree - Document Processing Tasks
Celery tasks for background document processing
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy import select
from sqlalchemy.sql import func

from core.celery_app import celery_app
from core.database import AsyncSessionLocal
from models.document import Document, ProcessingStatus
from models.chunk import Chunk
from models.crawl_job import CrawlJob, CrawlStatus
from services.pdf_processor import PDFProcessor
from services.text_chunker import TextChunker
from services.embedding_generator import EmbeddingGenerator
from services.web_content_processor import web_content_processor
from services.agentic_crawl_workflow import agentic_crawl_workflow
from services.crawler_orchestrator import CrawlEngine
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



@celery_app.task(name="services.document_tasks.process_web_crawl_task", bind=True)
def process_web_crawl_task(self, crawl_job_id: int, max_pages: int = None) -> Dict[str, Any]:
    """
    Process a web crawl job in the background
    
    Workflow:
    1. Crawl URL(s) with smart content extraction
    2. Create Document with source_type=WEB
    3. Generate URL-based Category tree
    4. Process content: chunk → embed → store
    5. Update CrawlJob with results
    
    Args:
        crawl_job_id: ID of CrawlJob to process
        max_pages: Maximum pages to crawl (None = unlimited)
        
    Returns:
        Processing results with Document ID and statistics
    """
    # Run async function in new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            _process_web_crawl_async(self, crawl_job_id, max_pages)
        )
        return result
    except Exception as e:
        logger.error(f"Web crawl task failed for job {crawl_job_id}: {str(e)}")
        # Mark crawl job as failed
        loop.run_until_complete(_mark_crawl_job_failed(crawl_job_id, str(e)))
        raise
    finally:
        loop.close()


async def _process_web_crawl_async(task, crawl_job_id: int, max_pages: int = None) -> Dict[str, Any]:
    """Async implementation of web crawl processing"""
    async with AsyncSessionLocal() as db:
        # Get crawl job
        result = await db.execute(
            select(CrawlJob).where(CrawlJob.id == crawl_job_id)
        )
        crawl_job = result.scalar_one_or_none()
        
        if not crawl_job:
            return {"error": "CrawlJob not found", "crawl_job_id": crawl_job_id}
        
        try:
            # Update status to in_progress
            crawl_job.status = CrawlStatus.IN_PROGRESS
            await db.commit()
            
            logger.info(f"Starting web crawl: Job {crawl_job_id}, URL: {crawl_job.url}")
            
            # Step 1: Initial progress (5%)
            task.update_state(
                state='PROGRESS',
                meta={
                    'current': 1,
                    'total': 4,
                    'status': 'Starting web crawl',
                    'step': 'initialization',
                    'percentage': 5,
                    'url': crawl_job.url,
                    'message': f'Initializing crawl for {crawl_job.url}'
                }
            )
            
            # Step 2: Process crawl job through web_content_processor (5-60%)
            task.update_state(
                state='PROGRESS',
                meta={
                    'current': 1,
                    'total': 4,
                    'status': 'Crawling website',
                    'step': 'crawling',
                    'percentage': 10,
                    'url': crawl_job.url,
                    'message': f'Crawling {crawl_job.url}...'
                }
            )
            
            document = await web_content_processor.process_crawl_job(
                crawl_job=crawl_job,
                db=db,
                max_pages=max_pages
            )
            
            logger.info(
                f"Web crawl {crawl_job_id}: Created Document {document.id} "
                f"({crawl_job.urls_crawled} URLs crawled, {crawl_job.urls_failed} failed)"
            )
            
            # Step 3: Get statistics from database (60%)
            task.update_state(
                state='PROGRESS',
                meta={
                    'current': 3,
                    'total': 4,
                    'status': 'Gathering statistics',
                    'step': 'statistics',
                    'percentage': 60,
                    'document_id': document.id,
                    'urls_crawled': crawl_job.urls_crawled,
                    'message': f'Document {document.id} created, gathering statistics...'
                }
            )
            
            # Count categories created
            category_result = await db.execute(
                select(func.count()).select_from(
                    select(1).where(
                        Document.id == document.id
                    ).join(
                        Document.category
                    ).subquery()
                )
            )
            categories_count = category_result.scalar() or 0
            
            # Count chunks created
            chunk_result = await db.execute(
                select(func.count()).select_from(Chunk).where(
                    Chunk.document_id == document.id
                )
            )
            chunks_count = chunk_result.scalar() or 0
            
            # Step 4: Update CrawlJob status to completed (80%)
            task.update_state(
                state='PROGRESS',
                meta={
                    'current': 4,
                    'total': 4,
                    'status': 'Finalizing',
                    'step': 'finalization',
                    'percentage': 80,
                    'document_id': document.id,
                    'categories_count': categories_count,
                    'chunks_count': chunks_count,
                    'message': 'Finalizing crawl job...'
                }
            )
            
            crawl_job.status = CrawlStatus.COMPLETED
            await db.commit()
            await db.refresh(crawl_job)
            
            # Final progress update (100%)
            task.update_state(
                state='SUCCESS',
                meta={
                    'current': 4,
                    'total': 4,
                    'status': 'Crawl completed',
                    'step': 'completed',
                    'percentage': 100,
                    'document_id': document.id,
                    'urls_crawled': crawl_job.urls_crawled,
                    'urls_failed': crawl_job.urls_failed,
                    'categories_count': categories_count,
                    'chunks_count': chunks_count,
                    'message': f'Successfully crawled {crawl_job.urls_crawled} URLs into Document {document.id}'
                }
            )
            
            logger.info(
                f"Web crawl {crawl_job_id}: Completed - "
                f"Document {document.id}, {crawl_job.urls_crawled} URLs, "
                f"{categories_count} categories, {chunks_count} chunks"
            )
            
            return {
                "crawl_job_id": crawl_job_id,
                "document_id": document.id,
                "status": "completed",
                "urls_crawled": crawl_job.urls_crawled,
                "urls_failed": crawl_job.urls_failed,
                "categories_created": categories_count,
                "chunks_created": chunks_count
            }
            
        except Exception as e:
            logger.error(f"Web crawl {crawl_job_id}: Processing failed: {str(e)}")
            crawl_job.status = CrawlStatus.FAILED
            crawl_job.error_message = str(e)
            await db.commit()
            raise


async def _mark_crawl_job_failed(crawl_job_id: int, error_message: str):
    """Mark crawl job as failed in database"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(CrawlJob).where(CrawlJob.id == crawl_job_id)
        )
        crawl_job = result.scalar_one_or_none()

        if crawl_job:
            crawl_job.status = CrawlStatus.FAILED
            crawl_job.error_message = error_message
            await db.commit()


@celery_app.task(name="services.document_tasks.process_agentic_crawl_task", bind=True)
def process_agentic_crawl_task(
    self,
    crawl_job_id: int,
    urls: List[str],
    agent_prompt: str,
    project_id: int,
    engine: Optional[str] = None,
    category_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Process agentic crawl with custom AI extraction prompt.

    User provides URLs + custom prompt for extraction guidance.
    AI agents extract structured information according to the prompt.
    Results organized into knowledge tree and saved to project.

    Workflow:
    1. Content Acquisition: Scrape URLs or transcribe YouTube
    2. Prompt-Guided Extraction: Use AI with custom instructions
    3. Knowledge Organization: Build hierarchical tree
    4. Persistence: Save as Document + Chunks + Categories

    Args:
        crawl_job_id: ID of CrawlJob to process
        urls: List of URLs to process (can include YouTube)
        agent_prompt: Custom natural language prompt (e.g., "extract all companies with contact info")
        project_id: Project ID to save results
        engine: Optional crawl engine ("http", "playwright", "firecrawl")
        category_id: Optional parent category for organization

    Returns:
        Processing results with Document ID and extraction statistics
    """
    # Run async function in new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(
            _process_agentic_crawl_async(
                self, crawl_job_id, urls, agent_prompt, project_id, engine, category_id
            )
        )
        return result
    except Exception as e:
        logger.error(f"Agentic crawl task failed for job {crawl_job_id}: {str(e)}")
        loop.run_until_complete(_mark_crawl_job_failed(crawl_job_id, str(e)))
        raise
    finally:
        loop.close()


async def _process_agentic_crawl_async(
    task,
    crawl_job_id: int,
    urls: List[str],
    agent_prompt: str,
    project_id: int,
    engine: Optional[str],
    category_id: Optional[int]
):
    """Async implementation of agentic crawl workflow with progress reporting"""
    async with AsyncSessionLocal() as db:
        try:
            # Get CrawlJob
            result = await db.execute(
                select(CrawlJob).where(CrawlJob.id == crawl_job_id)
            )
            crawl_job = result.scalar_one_or_none()

            if not crawl_job:
                raise ValueError(f"CrawlJob {crawl_job_id} not found")

            logger.info(
                f"Agentic crawl {crawl_job_id}: Starting with prompt '{agent_prompt[:50]}...' "
                f"for {len(urls)} URLs"
            )

            # Step 1: Initialize (5%)
            task.update_state(
                state='PROGRESS',
                meta={
                    'current': 1,
                    'total': 5,
                    'status': 'Initializing agentic extraction',
                    'step': 'initialization',
                    'percentage': 5,
                    'urls_count': len(urls),
                    'message': f'Preparing to extract with prompt: {agent_prompt[:50]}...'
                }
            )

            # Step 2: Execute agentic workflow (10-80%)
            task.update_state(
                state='PROGRESS',
                meta={
                    'current': 2,
                    'total': 5,
                    'status': 'Extracting knowledge with AI',
                    'step': 'extraction',
                    'percentage': 10,
                    'message': 'Processing content with AI agents...'
                }
            )

            # Convert engine string to CrawlEngine enum
            crawl_engine = None
            if engine:
                try:
                    crawl_engine = CrawlEngine(engine)
                except ValueError:
                    logger.warning(f"Invalid engine '{engine}', using auto-selection")

            # Execute workflow
            workflow_result = await agentic_crawl_workflow.execute(
                db=db,
                crawl_job_id=crawl_job_id,
                urls=urls,
                agent_prompt=agent_prompt,
                project_id=project_id,
                engine=crawl_engine,
                category_id=category_id
            )

            logger.info(
                f"Agentic crawl {crawl_job_id}: Completed - "
                f"Document {workflow_result['document_id']}, "
                f"{workflow_result['entities_extracted']} entities, "
                f"{workflow_result['insights_extracted']} insights, "
                f"{workflow_result['categories_created']} categories"
            )

            # Step 3: Statistics (80%)
            task.update_state(
                state='PROGRESS',
                meta={
                    'current': 4,
                    'total': 5,
                    'status': 'Gathering statistics',
                    'step': 'statistics',
                    'percentage': 80,
                    'document_id': workflow_result['document_id'],
                    'entities_extracted': workflow_result['entities_extracted'],
                    'insights_extracted': workflow_result['insights_extracted'],
                    'message': f"Extracted {workflow_result['entities_extracted']} entities and {workflow_result['insights_extracted']} insights"
                }
            )

            # Step 4: Finalization (90%)
            task.update_state(
                state='PROGRESS',
                meta={
                    'current': 5,
                    'total': 5,
                    'status': 'Finalizing',
                    'step': 'finalization',
                    'percentage': 90,
                    'document_id': workflow_result['document_id'],
                    'message': 'Finalizing agentic extraction...'
                }
            )

            # Final progress update (100%)
            task.update_state(
                state='SUCCESS',
                meta={
                    'current': 5,
                    'total': 5,
                    'status': 'Extraction completed',
                    'step': 'completed',
                    'percentage': 100,
                    'document_id': workflow_result['document_id'],
                    'workflow_id': workflow_result['workflow_id'],
                    'urls_processed': workflow_result['urls_processed'],
                    'entities_extracted': workflow_result['entities_extracted'],
                    'insights_extracted': workflow_result['insights_extracted'],
                    'categories_created': workflow_result['categories_created'],
                    'chunks_created': workflow_result['chunks_created'],
                    'message': f"Successfully extracted knowledge from {workflow_result['urls_processed']} URLs with custom prompt"
                }
            )

            return {
                "crawl_job_id": crawl_job_id,
                "document_id": workflow_result["document_id"],
                "workflow_id": workflow_result["workflow_id"],
                "status": "completed",
                "urls_processed": workflow_result["urls_processed"],
                "entities_extracted": workflow_result["entities_extracted"],
                "insights_extracted": workflow_result["insights_extracted"],
                "categories_created": workflow_result["categories_created"],
                "chunks_created": workflow_result["chunks_created"]
            }

        except Exception as e:
            logger.error(f"Agentic crawl {crawl_job_id}: Processing failed: {str(e)}")
            raise
