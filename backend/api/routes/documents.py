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
from api.dependencies import get_current_active_user, check_documents_limit, check_storage_limit
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
    db: AsyncSession = Depends(get_db),
    _documents_limit: None = Depends(check_documents_limit()),
    _storage_limit: None = Depends(check_storage_limit())
):
    """
    Upload a document (PDF) for processing

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

        # Track storage usage (convert bytes to GB)
        storage_gb = file_size / (1024 * 1024 * 1024)
        await usage_service.increment_usage(
            db=db,
            user_id=current_user.id,
            metric="storage_gb",
            period="monthly",
            amount=int(storage_gb) if storage_gb >= 1 else 1  # Minimum 1 GB per document
        )

        logger.info(f"Document uploaded: {document.id} - {document.filename}, size: {file_size} bytes ({storage_gb:.2f} GB)")

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
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger document processing (text extraction, chunking, and embedding generation)

    This endpoint processes a PDF document through the complete pipeline:
    1. Extract text using Docling (with PyMuPDF fallback)
    2. Split text into chunks (1000 chars, 200 overlap)
    3. Generate BGE-M3 embeddings for each chunk (1024 dimensions)
    4. Store chunks with embeddings in database for vector search

    In production, this would be handled by a background worker.
    """
    # Get document
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

    if document.processing_status == ProcessingStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document already processed"
        )

    try:
        # Update status to processing
        document.processing_status = ProcessingStatus.PROCESSING
        await db.commit()

        # Step 1: Extract text from PDF
        pdf_path = Path(document.file_path)
        extracted_text, page_count = pdf_processor.process_pdf(pdf_path)
        logger.info(f"Extracted text from {page_count} pages")

        # Step 2: Chunk the text (TIER 1 Phase 4: with contextual info)
        chunks_data = text_chunker.chunk_text(extracted_text, document.id)
        logger.info(f"Created {len(chunks_data)} chunks with contextual information")

        # Step 3: Generate contextual embeddings for chunks (TIER 1 Phase 4)
        logger.info("Generating contextual embeddings (including chunk_before + text + chunk_after)...")
        embeddings = []
        for chunk_data in chunks_data:
            try:
                # Generate contextual embedding
                embedding = embedding_generator.generate_contextual_embedding(
                    text=chunk_data["text"],
                    chunk_before=chunk_data.get("chunk_before"),
                    chunk_after=chunk_data.get("chunk_after")
                )
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Failed to generate contextual embedding for chunk: {e}")
                embeddings.append(None)

        logger.info(f"Generated contextual embeddings for {len([e for e in embeddings if e])} chunks")

        # Step 4: Store chunks with contextual embeddings in database
        for i, chunk_data in enumerate(chunks_data):
            embedding = embeddings[i]

            # Skip if embedding generation failed (None)
            if embedding is None:
                logger.warning(f"Skipping chunk {i} - embedding generation failed")
                continue

            chunk = Chunk(
                text=chunk_data["text"],
                chunk_metadata=json.dumps(chunk_data["chunk_metadata"]),  # Serialize to JSON
                chunk_before=chunk_data.get("chunk_before"),  # TIER 1 Phase 4
                chunk_after=chunk_data.get("chunk_after"),    # TIER 1 Phase 4
                embedding=embedding,  # Contextual embedding
                has_embedding=1,
                chunk_index=chunk_data["chunk_index"],
                document_id=document.id
            )
            db.add(chunk)

        # Update document status
        document.page_count = page_count
        document.processing_status = ProcessingStatus.COMPLETED
        document.processed_at = func.now()
        await db.commit()
        await db.refresh(document)

        logger.info(f"Document processed successfully: {document.id} - {page_count} pages, {len(chunks_data)} chunks")

        return DocumentResponse.model_validate(document)

    except Exception as e:
        logger.error(f"Document processing failed: {str(e)}")
        document.processing_status = ProcessingStatus.FAILED
        document.error_message = str(e)
        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {str(e)}"
        )


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
