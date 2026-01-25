"""
Export-related Pydantic schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ExportProjectResponse(BaseModel):
    """Response schema for project export"""
    export_version: str
    export_date: str
    project: dict
    categories: List[dict]
    documents: List[dict]
    statistics: dict


class ExportDocumentResponse(BaseModel):
    """Response schema for document export"""
    filename: str
    content: str
    metadata: Optional[dict] = None


class SearchResultExport(BaseModel):
    """Schema for search result to be exported"""
    document_title: str = Field(..., description="Document filename")
    chunk_index: int = Field(..., description="Chunk index within document")
    page_number: Optional[int] = Field(None, description="Page number")
    similarity_score: float = Field(..., description="Similarity score (0-1)")
    chunk_text: str = Field(..., description="Full chunk text")

    class Config:
        json_schema_extra = {
            "example": {
                "document_title": "example.pdf",
                "chunk_index": 5,
                "page_number": 3,
                "similarity_score": 0.8542,
                "chunk_text": "This is the chunk content..."
            }
        }
