"""
KnowledgeTree Backend - Documents Routes
Document upload, processing, and management endpoints
"""

import logging
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pathlib import Path
from core.database import get_db
from core.config import settings
from models.user import User
from models.document import Document, DocumentType, ProcessingStatus
from models.project import Project
from schemas.document import (
    DocumentUploadResponse,
    DocumentResponse,
    DocumentListResponse,
    DocumentUpdateRequest,
)
from schemas.category import (
    GenerateTreeRequest,
    GenerateTreeResponse,
    CategoryResponse,
)
from api.dependencies import (
    get_current_active_user,
    get_user_from_query_token,
    check_documents_limit,
    check_storage_limit,
    check_rate_limit,
    increment_rate_limit,
    get_user_subscription_plan,
)
from services.pdf_processor import PDFProcessor
from services.text_chunker import TextChunker
from services.embedding_generator import EmbeddingGenerator
from services.usage_service import usage_service
from services.category_tree_generator import generate_category_tree
from models.chunk import Chunk
from models.category import Category

router = APIRouter(prefix="/documents", tags=["Documents"])
logger = logging.getLogger(__name__)

# Initialize services
pdf_processor = PDFProcessor(upload_dir=settings.UPLOAD_DIR)
text_chunker = TextChunker()
embedding_generator = EmbeddingGenerator()


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    project_id: int = Form(...),
    category_id: int = Form(None),
    current_user: User = Depends(get_current_active_user),
    subscription_plan: str = Depends(get_user_subscription_plan),
    db: AsyncSession = Depends(get_db),
    _documents_limit: None = Depends(check_documents_limit()),
    _storage_limit: None = Depends(check_storage_limit()),
    _rate_limit: None = Depends(check_rate_limit("upload")),
):
    """
    Upload a document (PDF) for processing

    - Checks rate limits per subscription tier (5-1000 uploads/hour)
    - Checks subscription limits (documents count and storage space)
    - Validates file type and size
    - Saves file to disk
    - Creates database record
    - Tracks usage for billing and limits
    - Queues for text extraction and embedding generation
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )

    # Validate file size
    file_content = await file.read()
    file_size = len(file_content)
    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024  # Convert MB to bytes

    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB"
        )

    # Verify project exists and user has access
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
        # Create document record
        document = Document(
            filename=file.filename,
            title=Path(file.filename).stem,  # Use filename without extension as title
            source_type=DocumentType.PDF,
            file_size=file_size,
            processing_status=ProcessingStatus.PENDING,
            category_id=category_id,
            project_id=project_id,
        )

        db.add(document)
        await db.commit()
        await db.refresh(document)

        # Save file to disk
        file_path = pdf_processor.save_uploaded_file(
            file_content=file_content,
            filename=file.filename,
            document_id=document.id
        )

        # Update document with file path
        document.file_path = str(file_path)
        await db.commit()

        # Track usage for documents and storage
        await usage_service.increment_usage(
            db=db,
            user_id=current_user.id,
            metric="documents_uploaded",
            period="monthly",
            amount=1
        )

        # Track storage usage (convert bytes to GB, store in hundredths)
        # Storage is tracked as hundredths of GB: 0.01 GB = 1 unit, 1 GB = 100 units
        storage_gb = file_size / (1024 * 1024 * 1024)
        storage_units = max(1, int(storage_gb * 100))  # Minimum 1 unit (0.01 GB)
        await usage_service.increment_usage(
            db=db,
            user_id=current_user.id,
            metric="storage_gb",
            period="monthly",
            amount=storage_units
        )

        logger.info(f"Document uploaded: {document.id} - {document.filename}, size: {file_size} bytes ({storage_gb:.2f} GB)")

        # Increment rate limit counter
        await increment_rate_limit(
            action="upload",
            current_user=current_user,
            subscription_plan=subscription_plan,
            amount=1
        )

        return DocumentUploadResponse(
            id=document.id,
            filename=document.filename,
            file_size=document.file_size,
            processing_status=document.processing_status,
            message="Document uploaded successfully and queued for processing"
        )

    except Exception as e:
        logger.error(f"Document upload failed: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document upload failed: {str(e)}"
        )


@router.post("/{document_id}/process", response_model=DocumentResponse)
async def process_document(
    document_id: int,
    force: bool = False,
    current_user: User = Depends(get_current_active_user),
    subscription_plan: str = Depends(get_user_subscription_plan),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger document processing in background (text extraction, chunking, embedding generation)

    This endpoint starts a background Celery task to process the PDF document through:
    1. Extract text using Docling (with PyMuPDF fallback)
    2. Split text into chunks (1000 chars, 200 overlap)
    3. Generate BGE-M3 embeddings for each chunk (1024 dimensions)
    4. Store chunks with embeddings in database for vector search

    The processing runs asynchronously in a Celery worker to avoid blocking the API.
    Tasks are prioritized based on subscription tier (free=low, enterprise=highest).
    Poll the document status using GET /documents/{id} to check completion.

    Use force=true to re-process documents that are stuck in PROCESSING status.
    """
    from services.document_tasks import process_document_task
    from services.priority_helper import get_task_priority

    # Get document and verify access
    result = await db.execute(
        select(Document)
        .join(Project)
        .where(
            Document.id == document_id,
            Project.owner_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied"
        )

    if document.processing_status == ProcessingStatus.COMPLETED and not force:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document already processed. Use force=true to re-process."
        )

    if document.processing_status == ProcessingStatus.PROCESSING and not force:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document is already being processed. Use force=true to override."
        )

    try:
        # Update status to processing
        document.processing_status = ProcessingStatus.PROCESSING
        await db.commit()
        await db.refresh(document)

        # Get task priority based on subscription tier
        priority = get_task_priority(subscription_plan)
        logger.info(f"Queueing document {document_id} with priority {priority} (plan: {subscription_plan})")

        # Trigger background task (non-blocking) with priority
        task = process_document_task.apply_async(
            args=[document_id],
            priority=priority
        )

        # Store task_id in Redis for progress tracking (TTL: 1 hour)
        import redis
        redis_client = redis.from_url(settings.REDIS_URL)
        redis_client.setex(f"document_task:{document_id}", 3600, task.id)

        logger.info(
            f"Started background processing for document {document_id}, "
            f"task_id: {task.id}, priority: {priority} ({subscription_plan})"
        )

        # Return immediately with current document status
        return DocumentResponse.model_validate(document)

    except Exception as e:
        logger.error(f"Failed to start document processing: {str(e)}")
        document.processing_status = ProcessingStatus.FAILED
        document.error_message = f"Failed to start processing: {str(e)}"
        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start document processing: {str(e)}"
        )


@router.get("/{document_id}/progress")
async def get_document_progress(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current processing progress for a document (polling endpoint)
    
    Returns task status and progress information including:
    - percentage: 0-100% progress
    - step: current processing step (extraction, chunking, embeddings, storage, completed)
    - message: detailed status message
    - chunks_processed/chunks_total: for embedding generation
    
    Use this endpoint to poll for progress updates every 1-2 seconds.
    For real-time streaming, use the /progress/stream endpoint instead.
    """
    import redis
    from celery.result import AsyncResult
    
    # Verify document access
    result = await db.execute(
        select(Document)
        .join(Project)
        .where(
            Document.id == document_id,
            Project.owner_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied"
        )
    
    # Get task_id from Redis
    redis_client = redis.from_url(settings.REDIS_URL)
    task_id = redis_client.get(f"document_task:{document_id}")
    
    if not task_id:
        # No task found - check document status
        return {
            "status": document.processing_status.value,
            "percentage": 100 if document.processing_status == ProcessingStatus.COMPLETED else 0,
            "step": "completed" if document.processing_status == ProcessingStatus.COMPLETED else "pending",
            "message": document.error_message if document.processing_status == ProcessingStatus.FAILED else "No active task"
        }
    
    # Get task result from Celery
    task_result = AsyncResult(task_id.decode('utf-8'), app=celery_app)
    
    if task_result.state == 'PENDING':
        return {
            "status": "pending",
            "percentage": 0,
            "step": "pending",
            "message": "Task is queued and waiting to start"
        }
    elif task_result.state == 'PROGRESS':
        return {
            "status": "processing",
            **task_result.info  # Contains: percentage, step, message, etc.
        }
    elif task_result.state == 'SUCCESS':
        return {
            "status": "completed",
            "percentage": 100,
            "step": "completed",
            "message": "Processing complete",
            **task_result.info
        }
    elif task_result.state == 'FAILURE':
        return {
            "status": "failed",
            "percentage": 0,
            "step": "failed",
            "message": str(task_result.info)
        }
    else:
        return {
            "status": task_result.state.lower(),
            "percentage": 0,
            "step": task_result.state.lower(),
            "message": f"Task state: {task_result.state}"
        }


@router.get("/{document_id}/progress/stream")
async def stream_document_progress(
    document_id: int,
    current_user: User = Depends(get_user_from_query_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Stream real-time processing progress via Server-Sent Events (SSE)
    
    This endpoint streams progress updates in real-time using Server-Sent Events.
    The client should use EventSource to connect and receive updates.
    
    Events are sent every 500ms with current progress information:
    - percentage: 0-100% progress
    - step: current processing step
    - message: detailed status message
    
    The stream automatically closes when processing completes or fails.
    """
    import redis
    import asyncio
    from celery.result import AsyncResult
    from sse_starlette.sse import EventSourceResponse
    
    # Verify document access
    result = await db.execute(
        select(Document)
        .join(Project)
        .where(
            Document.id == document_id,
            Project.owner_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied"
        )
    
    # Get task_id from Redis
    redis_client = redis.from_url(settings.REDIS_URL)
    task_id = redis_client.get(f"document_task:{document_id}")
    
    if not task_id:
        # Return immediate response if no task
        async def no_task_generator():
            status = document.processing_status.value
            yield {
                "event": "progress",
                "data": json.dumps({
                    "status": status,
                    "percentage": 100 if status == "completed" else 0,
                    "step": status,
                    "message": "No active processing task"
                })
            }
            yield {"event": "close", "data": ""}
        
        return EventSourceResponse(no_task_generator())
    
    # Stream progress updates
    async def event_generator():
        from core.celery_app import celery_app
        task_result = AsyncResult(task_id.decode('utf-8'), app=celery_app)
        last_state = None
        last_info = None

        while True:
            try:
                current_state = task_result.state
                current_info = task_result.info if task_result.info else {}

                # Check if we should send an update
                # Send if: state changed OR (in PROGRESS and info changed)
                should_send = (current_state != last_state) or \
                             (current_state == 'PROGRESS' and current_info != last_info)

                if should_send:
                    if current_state == 'PENDING':
                        data = {
                            "status": "pending",
                            "percentage": 0,
                            "step": "pending",
                            "message": "Task queued, waiting to start"
                        }
                    elif current_state == 'PROGRESS':
                        data = {
                            "status": "processing",
                            **task_result.info
                        }
                    elif current_state == 'SUCCESS':
                        data = {
                            "status": "completed",
                            "percentage": 100,
                            "step": "completed",
                            "message": "Processing complete",
                            **task_result.info
                        }
                        yield {"event": "progress", "data": json.dumps(data)}
                        yield {"event": "close", "data": ""}
                        break
                    elif current_state == 'FAILURE':
                        data = {
                            "status": "failed",
                            "percentage": 0,
                            "step": "failed",
                            "message": str(task_result.info)
                        }
                        yield {"event": "progress", "data": json.dumps(data)}
                        yield {"event": "close", "data": ""}
                        break
                    else:
                        data = {
                            "status": current_state.lower(),
                            "message": f"Task state: {current_state}"
                        }
                    
                    yield {"event": "progress", "data": json.dumps(data)}
                    last_state = current_state
                    last_info = current_info

                # Poll every 500ms
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error streaming progress: {str(e)}")
                yield {
                    "event": "error",
                    "data": json.dumps({"message": str(e)})
                }
                break
    
    return EventSourceResponse(event_generator())


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get document by ID"""
    result = await db.execute(
        select(Document)
        .join(Project)
        .where(
            Document.id == document_id,
            Project.owner_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied"
        )

    return DocumentResponse.model_validate(document)


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    project_id: int,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List documents in a project"""
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

    # Get total count
    count_result = await db.execute(
        select(func.count(Document.id)).where(Document.project_id == project_id)
    )
    total = count_result.scalar()

    # Get documents
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Document)
        .where(Document.project_id == project_id)
        .order_by(Document.created_at.desc())
        .limit(page_size)
        .offset(offset)
    )
    documents = result.scalars().all()

    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(doc) for doc in documents],
        total=total,
        page=page,
        page_size=page_size
    )


@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    update_data: DocumentUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update document metadata"""
    result = await db.execute(
        select(Document)
        .join(Project)
        .where(
            Document.id == document_id,
            Project.owner_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied"
        )

    # Update fields
    if update_data.title is not None:
        document.title = update_data.title
    if update_data.category_id is not None:
        document.category_id = update_data.category_id

    await db.commit()
    await db.refresh(document)

    return DocumentResponse.model_validate(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete document"""
    result = await db.execute(
        select(Document)
        .join(Project)
        .where(
            Document.id == document_id,
            Project.owner_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied"
        )

    # Delete file from disk
    try:
        if document.file_path:
            file_path = Path(document.file_path)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted file: {file_path}")
    except Exception as e:
        logger.error(f"Failed to delete file: {str(e)}")

    # Decrement usage counters
    from services.usage_service import UsageService

    # Decrement documents_uploaded counter
    await UsageService.decrement_usage(
        db=db,
        user_id=current_user.id,
        metric="documents_uploaded",
        period="monthly",
        amount=1
    )

    # Decrement storage_gb counter (convert bytes to GB, use hundredths)
    if document.file_size:
        storage_gb = document.file_size / (1024 ** 3)  # bytes to GB
        storage_units = max(1, int(storage_gb * 100))  # Match increment logic
        await UsageService.decrement_usage(
            db=db,
            user_id=current_user.id,
            metric="storage_gb",
            period="monthly",
            amount=storage_units
        )

    # Delete from database
    await db.delete(document)
    await db.commit()

    logger.info(f"Deleted document: {document_id}")
    return None


@router.post("/{document_id}/generate-tree", response_model=GenerateTreeResponse)
async def generate_category_tree_from_toc(
    document_id: int,
    request: GenerateTreeRequest = GenerateTreeRequest(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate category tree from PDF Table of Contents

    This endpoint:
    1. Extracts ToC from the PDF document using hybrid waterfall (pypdf → PyMuPDF → Docling)
    2. Converts ToC entries to Category tree structure
    3. Inserts categories into database with proper hierarchy
    4. Optionally assigns document to root category

    Args:
        document_id: Document ID to extract ToC from
        request: Generation options (parent_id, validate_depth, auto_assign_document)

    Returns:
        GenerateTreeResponse with created categories and statistics

    Raises:
        404: Document not found or access denied
        400: Document not processed yet, or ToC extraction failed
        500: Tree generation failed
    """
    # Get document with access control
    result = await db.execute(
        select(Document)
        .join(Project)
        .where(
            Document.id == document_id,
            Project.owner_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied"
        )

    # Verify document is PDF
    if document.source_type != DocumentType.PDF:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF documents support ToC extraction"
        )

    # Verify file exists
    if not document.file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document file not found"
        )

    pdf_path = Path(document.file_path)
    if not pdf_path.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"PDF file not found: {pdf_path}"
        )

    try:
        # Step 1: Extract ToC from PDF
        logger.info(f"Extracting ToC from document {document_id}: {pdf_path.name}")
        toc_result = pdf_processor.extract_toc(pdf_path)

        if not toc_result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"ToC extraction failed: {toc_result.error}"
            )

        logger.info(
            f"✅ ToC extracted: {toc_result.total_entries} entries, "
            f"max depth {toc_result.max_depth}, method: {toc_result.method.value}"
        )

        # Step 2: Generate category tree from ToC
        logger.info("Generating category tree from ToC entries...")
        categories_to_create, stats = generate_category_tree(
            toc_result=toc_result,
            project_id=document.project_id,
            parent_id=request.parent_id
        )

        if not categories_to_create:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No categories generated from ToC"
            )

        # Step 3: Insert categories into database with proper parent-child relationships
        # We need to insert in hierarchical order: parents before children
        logger.info(f"Inserting {len(categories_to_create)} categories into database...")

        # Build hierarchy map from original ToC entries
        hierarchy_map = _build_hierarchy_map(toc_result.entries)

        # Insert categories level by level
        inserted_categories = await _insert_categories_hierarchical(
            db=db,
            toc_entries=toc_result.entries,
            categories=categories_to_create,
            hierarchy_map=hierarchy_map,
            project_id=document.project_id,
            parent_id=request.parent_id
        )

        # Step 4: Optionally assign document to root category
        root_category_id = None
        if request.auto_assign_document and inserted_categories:
            # Find root category (depth 0 or first category)
            root_category = next(
                (cat for cat in inserted_categories if cat.depth == 0),
                inserted_categories[0]
            )
            root_category_id = root_category.id

            document.category_id = root_category_id
            await db.commit()
            logger.info(f"Assigned document {document_id} to root category {root_category_id}")

        await db.commit()

        logger.info(
            f"✅ Category tree generated: {len(inserted_categories)} categories created, "
            f"max depth {stats['max_depth']}"
        )

        return GenerateTreeResponse(
            success=True,
            message=f"Generated {len(inserted_categories)} categories from ToC",
            categories=[CategoryResponse.model_validate(cat) for cat in inserted_categories],
            stats=stats
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Category tree generation failed: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Category tree generation failed: {str(e)}"
        )


def _build_hierarchy_map(entries: list) -> dict:
    """
    Build map of ToC entry titles to their children for hierarchy tracking

    Args:
        entries: List of TocEntry objects

    Returns:
        Dict mapping entry title to list of child titles
    """
    hierarchy = {}

    def _process_entry(entry):
        hierarchy[entry.title] = [child.title for child in entry.children]
        for child in entry.children:
            _process_entry(child)

    for entry in entries:
        _process_entry(entry)

    return hierarchy


async def _insert_categories_hierarchical(
    db: AsyncSession,
    toc_entries: list,
    categories: list,
    hierarchy_map: dict,
    project_id: int,
    parent_id: Optional[int]
) -> list:
    """
    Insert categories into database in hierarchical order (parents before children)

    Args:
        db: Database session
        toc_entries: Original ToC entries (for structure reference)
        categories: List of Category objects to insert
        hierarchy_map: Map of entry title to child titles
        project_id: Project ID
        parent_id: Optional parent category ID

    Returns:
        List of inserted Category objects with IDs
    """
    # Create mapping of title to Category object
    title_to_category = {cat.name: cat for cat in categories}

    # Track inserted categories and their database IDs
    title_to_id = {}
    inserted = []

    # Process ToC entries recursively to maintain order
    async def _process_entry(entry, parent_db_id):
        # Find corresponding category
        # Note: We cleaned titles in generator, so need to match cleaned version
        from services.category_tree_generator import CategoryTreeGenerator
        generator = CategoryTreeGenerator()
        cleaned_title = generator._clean_title(entry.title)

        category = title_to_category.get(cleaned_title)
        if not category:
            logger.warning(f"Category not found for entry: {entry.title}")
            return

        # Set parent_id from database
        category.parent_id = parent_db_id

        # Insert category
        db.add(category)
        await db.flush()  # Get ID without committing
        await db.refresh(category)

        # Track mapping
        title_to_id[cleaned_title] = category.id
        inserted.append(category)

        logger.debug(f"Inserted category: {category.name} (id={category.id}, parent_id={parent_db_id}, depth={category.depth})")

        # Process children recursively
        for child_entry in entry.children:
            await _process_entry(child_entry, category.id)

    # Process root entries
    for entry in toc_entries:
        await _process_entry(entry, parent_id)

    return inserted
