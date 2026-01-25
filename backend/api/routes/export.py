"""
Export functionality endpoints
Supports JSON, Markdown, and CSV export formats
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import json
import io
import csv
from datetime import datetime

from core.database import get_db
from api.dependencies import get_current_user
from models.user import User
from models.project import Project
from models.document import Document
from models.category import Category
from models.chunk import Chunk
from schemas.export import (
    ExportProjectResponse,
    ExportDocumentResponse,
    SearchResultExport
)

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/project/{project_id}/json")
async def export_project_json(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export entire project as JSON

    Includes:
    - Project metadata
    - All categories (tree structure)
    - All documents with metadata
    - Statistics
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
        raise HTTPException(status_code=404, detail="Project not found")

    # Get all categories
    categories_result = await db.execute(
        select(Category)
        .where(Category.project_id == project_id)
        .order_by(Category.order)
    )
    categories = categories_result.scalars().all()

    # Get all documents
    documents_result = await db.execute(
        select(Document)
        .where(Document.project_id == project_id)
        .order_by(Document.created_at)
    )
    documents = documents_result.scalars().all()

    # Build export data
    export_data = {
        "export_version": "1.0",
        "export_date": datetime.utcnow().isoformat(),
        "project": {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat() if project.updated_at else None
        },
        "categories": [
            {
                "id": cat.id,
                "name": cat.name,
                "parent_id": cat.parent_id,
                "depth": cat.depth,
                "order": cat.order,
                "description": cat.description,
                "color": cat.color,
                "icon": cat.icon
            }
            for cat in categories
        ],
        "documents": [
            {
                "id": doc.id,
                "filename": doc.filename,
                "title": doc.title,
                "source_type": doc.source_type.value if doc.source_type else None,
                "file_size": doc.file_size,
                "file_path": doc.file_path,
                "category_id": doc.category_id,
                "processing_status": doc.processing_status.value,
                "page_count": doc.page_count,
                "error_message": doc.error_message,
                "created_at": doc.created_at.isoformat(),
                "processed_at": doc.processed_at.isoformat() if doc.processed_at else None
            }
            for doc in documents
        ],
        "statistics": {
            "total_categories": len(categories),
            "total_documents": len(documents),
            "total_pages": sum(doc.page_count or 0 for doc in documents)
        }
    }

    # Create JSON file in memory
    json_content = json.dumps(export_data, indent=2, ensure_ascii=False)
    json_bytes = io.BytesIO(json_content.encode('utf-8'))

    filename = f"knowledgetree_project_{project.name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

    return StreamingResponse(
        json_bytes,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/document/{document_id}/markdown")
async def export_document_markdown(
    document_id: int,
    include_metadata: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export single document as Markdown

    Includes:
    - Document metadata (optional)
    - All chunks in order
    - Page breaks between pages
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
        raise HTTPException(status_code=404, detail="Document not found")

    # Get all chunks ordered by page and index
    chunks_result = await db.execute(
        select(Chunk)
        .where(Chunk.document_id == document_id)
        .order_by(Chunk.chunk_index)
    )
    chunks = chunks_result.scalars().all()

    # Build markdown content
    markdown_lines = []

    if include_metadata:
        markdown_lines.extend([
            f"# {document.filename}",
            "",
            "## Document Information",
            "",
            f"- **File Type**: {document.file_type}",
            f"- **File Size**: {document.file_size} bytes",
            f"- **Page Count**: {document.page_count}",
            f"- **Processed**: {document.processed_at.strftime('%Y-%m-%d %H:%M:%S') if document.processed_at else 'N/A'}",
            "",
            "---",
            ""
        ])

    # Add content by page
    current_page = None
    for chunk in chunks:
        # Extract page number from chunk metadata
        page_number = None
        if chunk.chunk_metadata:
            try:
                metadata = json.loads(chunk.chunk_metadata)
                page_number = metadata.get("page_number")
            except json.JSONDecodeError:
                pass

        if page_number != current_page and page_number is not None:
            current_page = page_number
            if include_metadata:
                markdown_lines.extend([
                    "",
                    f"## Page {current_page}",
                    ""
                ])

        markdown_lines.append(chunk.text)
        markdown_lines.append("")

    markdown_content = "\n".join(markdown_lines)
    markdown_bytes = io.BytesIO(markdown_content.encode('utf-8'))

    filename = f"{document.filename.rsplit('.', 1)[0]}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.md"

    return StreamingResponse(
        markdown_bytes,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.post("/search-results/csv")
async def export_search_results_csv(
    results: List[SearchResultExport],
    current_user: User = Depends(get_current_user)
):
    """
    Export search results as CSV

    Accepts search results from frontend and converts to CSV
    """
    if not results:
        raise HTTPException(status_code=400, detail="No results to export")

    # Create CSV in memory
    csv_buffer = io.StringIO()
    csv_writer = csv.writer(csv_buffer)

    # Write header
    csv_writer.writerow([
        "Rank",
        "Document Title",
        "Chunk Index",
        "Page Number",
        "Similarity Score",
        "Chunk Text (Preview)"
    ])

    # Write data
    for rank, result in enumerate(results, start=1):
        csv_writer.writerow([
            rank,
            result.document_title,
            result.chunk_index,
            result.page_number or "N/A",
            f"{result.similarity_score:.4f}",
            result.chunk_text[:200] + "..." if len(result.chunk_text) > 200 else result.chunk_text
        ])

    csv_content = csv_buffer.getvalue()
    csv_bytes = io.BytesIO(csv_content.encode('utf-8-sig'))  # BOM for Excel compatibility

    filename = f"search_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        csv_bytes,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
