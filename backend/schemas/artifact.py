"""
Artifact-related Pydantic schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from models.artifact import ArtifactType


# Base schemas
class ArtifactBase(BaseModel):
    """Base artifact schema"""
    type: ArtifactType = Field(..., description="Artifact type (summary, article, extract, etc.)")
    title: str = Field(..., min_length=1, max_length=500, description="Artifact title")
    content: str = Field(..., min_length=1, description="Artifact content in Markdown format")
    conversation_id: Optional[int] = Field(None, description="Optional conversation that generated this artifact")
    category_id: Optional[int] = Field(None, description="Optional category (chapter/section) reference")


# Request schemas
class ArtifactCreateRequest(ArtifactBase):
    """Create artifact request"""
    metadata: Optional[dict] = Field(None, description="Optional metadata (source chapters, generation params, etc.)")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "summary",
                "title": "Chapter 3 Summary: Neural Networks",
                "content": "# Chapter 3 Summary\n\nNeural networks are...",
                "conversation_id": 42,
                "category_id": 15,
                "metadata": {
                    "source_chapters": [3],
                    "model": "claude-3-5-sonnet",
                    "generation_params": {"temperature": 0.7}
                }
            }
        }


class ArtifactUpdateRequest(BaseModel):
    """Update artifact request (all fields optional)"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = Field(None, min_length=1)
    type: Optional[ArtifactType] = None
    conversation_id: Optional[int] = None
    category_id: Optional[int] = None
    metadata: Optional[dict] = None


class ArtifactRegenerateRequest(BaseModel):
    """Regenerate artifact request (creates new version)"""
    metadata: Optional[dict] = Field(None, description="Updated generation parameters")

    class Config:
        json_schema_extra = {
            "example": {
                "metadata": {
                    "temperature": 0.9,
                    "max_tokens": 2000
                }
            }
        }


# Response schemas
class ArtifactResponse(ArtifactBase):
    """Full artifact response"""
    id: int
    version: int
    project_id: int
    user_id: int
    metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 123,
                "type": "summary",
                "title": "Chapter 3 Summary: Neural Networks",
                "content": "# Chapter 3 Summary\n\nNeural networks are...",
                "version": 1,
                "project_id": 5,
                "user_id": 10,
                "conversation_id": 42,
                "category_id": 15,
                "metadata": {"source_chapters": [3], "model": "claude-3-5-sonnet"},
                "created_at": "2026-01-21T10:00:00Z",
                "updated_at": "2026-01-21T10:00:00Z"
            }
        }


class ArtifactListItem(BaseModel):
    """Artifact list item (minimal info for listing)"""
    id: int
    type: ArtifactType
    title: str
    version: int
    conversation_id: Optional[int]
    category_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ArtifactListResponse(BaseModel):
    """Paginated artifact list response"""
    artifacts: List[ArtifactListItem]
    total: int
    page: int
    page_size: int
    has_more: bool

    class Config:
        json_schema_extra = {
            "example": {
                "artifacts": [
                    {
                        "id": 123,
                        "type": "summary",
                        "title": "Chapter 3 Summary",
                        "version": 1,
                        "conversation_id": 42,
                        "category_id": 15,
                        "created_at": "2026-01-21T10:00:00Z",
                        "updated_at": "2026-01-21T10:00:00Z"
                    }
                ],
                "total": 50,
                "page": 1,
                "page_size": 20,
                "has_more": True
            }
        }
