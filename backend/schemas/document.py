"""
KnowledgeTree Backend - Document Schemas
Pydantic models for document upload and management
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from models.document import DocumentType, ProcessingStatus


class DocumentUploadResponse(BaseModel):
    """Response after document upload"""
    id: int
    filename: str
    file_size: int
    processing_status: ProcessingStatus
    message: str

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "filename": "document.pdf",
                    "file_size": 1024000,
                    "processing_status": "PENDING",
                    "message": "Document uploaded successfully and queued for processing"
                }
            ]
        }
    }


class DocumentResponse(BaseModel):
    """Document response"""
    id: int
    filename: str
    title: Optional[str] = None
    source_type: DocumentType
    source_url: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    page_count: Optional[int] = None
    processing_status: ProcessingStatus
    error_message: Optional[str] = None
    category_id: Optional[int] = None
    project_id: int
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "filename": "research_paper.pdf",
                    "title": "AI Research Paper",
                    "source_type": "PDF",
                    "source_url": None,
                    "file_path": "/uploads/documents/1_research_paper.pdf",
                    "file_size": 2048000,
                    "page_count": 15,
                    "processing_status": "COMPLETED",
                    "error_message": None,
                    "category_id": 1,
                    "project_id": 1,
                    "created_at": "2026-01-19T22:00:00Z",
                    "updated_at": "2026-01-19T22:05:00Z",
                    "processed_at": "2026-01-19T22:05:00Z"
                }
            ]
        }
    }


class DocumentListResponse(BaseModel):
    """List of documents with pagination"""
    documents: list[DocumentResponse]
    total: int
    page: int
    page_size: int

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "documents": [],
                    "total": 0,
                    "page": 1,
                    "page_size": 20
                }
            ]
        }
    }


class DocumentUpdateRequest(BaseModel):
    """Request to update document metadata"""
    title: Optional[str] = None
    category_id: Optional[int] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Updated Document Title",
                    "category_id": 2
                }
            ]
        }
    }
