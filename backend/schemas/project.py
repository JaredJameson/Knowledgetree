"""
KnowledgeTree Backend - Project Schemas
Pydantic models for Project API requests and responses
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class ProjectBase(BaseModel):
    """Base project schema with common fields"""
    name: str = Field(..., min_length=1, max_length=200, description="Project name")
    description: Optional[str] = Field(None, max_length=2000, description="Project description")
    color: str = Field(default="#3B82F6", pattern="^#[0-9A-Fa-f]{6}$", description="Hex color code")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate project name is not empty after stripping whitespace"""
        if not v.strip():
            raise ValueError("Project name cannot be empty or whitespace only")
        return v.strip()


class ProjectCreate(ProjectBase):
    """Schema for creating a new project"""
    pass


class ProjectUpdate(BaseModel):
    """Schema for updating an existing project"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate project name if provided"""
        if v is not None and not v.strip():
            raise ValueError("Project name cannot be empty or whitespace only")
        return v.strip() if v else v


class ProjectResponse(ProjectBase):
    """Schema for project response with all fields"""
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectWithStats(ProjectResponse):
    """Schema for project response with statistics"""
    document_count: int = Field(default=0, description="Number of documents in project")
    total_chunks: int = Field(default=0, description="Total number of chunks across all documents")
    category_count: int = Field(default=0, description="Number of categories in project")

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    """Schema for paginated project list response"""
    projects: list[ProjectWithStats]
    total: int = Field(..., description="Total number of projects")
    page: int = Field(default=1, ge=1, description="Current page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Number of items per page")
