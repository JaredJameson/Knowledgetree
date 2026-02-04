"""
KnowledgeTree Backend - Category Schemas
Pydantic models for category tree management
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CategoryBase(BaseModel):
    """Base category schema"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    color: str = Field(default="#E6E6FA", pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: str = Field(default="Folder", min_length=1, max_length=50)


class CategoryCreate(CategoryBase):
    """Schema for creating a category"""
    parent_id: Optional[int] = None
    depth: int = Field(default=0, ge=0, le=10)
    order: int = Field(default=0, ge=0)


class CategoryUpdate(BaseModel):
    """Schema for updating a category"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, min_length=1, max_length=50)
    parent_id: Optional[int] = None
    order: Optional[int] = Field(None, ge=0)


class CategoryResponse(CategoryBase):
    """Category response with metadata"""
    id: int
    depth: int
    order: int
    parent_id: Optional[int]
    project_id: int
    merged_content: Optional[str] = None  # Full merged article content for UI display

    # Content Workbench fields (Phase 2)
    draft_content: Optional[str] = None
    published_content: Optional[str] = None
    content_status: str = "draft"
    published_at: Optional[datetime] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "name": "Introduction",
                    "description": "Page 1",
                    "color": "#E6E6FA",
                    "icon": "Book",
                    "depth": 0,
                    "order": 0,
                    "parent_id": None,
                    "project_id": 1,
                    "created_at": "2026-01-20T10:00:00Z",
                    "updated_at": "2026-01-20T10:00:00Z"
                }
            ]
        }
    }


class CategoryTreeNode(CategoryResponse):
    """Category with children for tree representation"""
    children: List['CategoryTreeNode'] = []

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "name": "Chapter 1",
                    "description": "Page 1",
                    "color": "#E6E6FA",
                    "icon": "Book",
                    "depth": 0,
                    "order": 0,
                    "parent_id": None,
                    "project_id": 1,
                    "created_at": "2026-01-20T10:00:00Z",
                    "updated_at": "2026-01-20T10:00:00Z",
                    "children": [
                        {
                            "id": 2,
                            "name": "Section 1.1",
                            "description": "Page 3",
                            "color": "#FFE4E1",
                            "icon": "BookOpen",
                            "depth": 1,
                            "order": 1,
                            "parent_id": 1,
                            "project_id": 1,
                            "created_at": "2026-01-20T10:00:00Z",
                            "updated_at": "2026-01-20T10:00:00Z",
                            "children": []
                        }
                    ]
                }
            ]
        }
    }


class GenerateTreeRequest(BaseModel):
    """Request to generate category tree from ToC"""
    parent_id: Optional[int] = Field(
        None,
        description="Optional parent category ID to append tree under"
    )
    validate_depth: bool = Field(
        True,
        description="Validate and enforce max depth limit (10 levels)"
    )
    auto_assign_document: bool = Field(
        True,
        description="Automatically assign document to root category after generation"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "parent_id": None,
                    "validate_depth": True,
                    "auto_assign_document": True
                }
            ]
        }
    }


class GenerateTreeResponse(BaseModel):
    """Response after generating category tree"""
    success: bool
    message: str
    categories: List[CategoryResponse]
    stats: dict

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "message": "Generated 15 categories from ToC",
                    "categories": [],
                    "stats": {
                        "total_entries": 15,
                        "total_created": 15,
                        "skipped_depth": 0,
                        "max_depth": 3
                    }
                }
            ]
        }
    }


class CategoryListResponse(BaseModel):
    """List of categories with pagination"""
    categories: List[CategoryResponse]
    total: int
    page: int
    page_size: int

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "categories": [],
                    "total": 0,
                    "page": 1,
                    "page_size": 50
                }
            ]
        }
    }


class CategoryContentResponse(BaseModel):
    """Category content with chunks, tables, and formulas"""
    category_id: int
    category_name: str
    merged_content: Optional[str] = None  # Full merged article content for UI display
    chunks: List[dict]
    tables: List[dict]
    formulas: List[dict]
    total_chunks: int
    total_tables: int
    total_formulas: int

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "category_id": 1,
                    "category_name": "Introduction",
                    "merged_content": "# Introduction\n\nComplete article text...",
                    "chunks": [
                        {
                            "id": 1,
                            "text": "Sample text chunk...",
                            "chunk_index": 0
                        }
                    ],
                    "tables": [],
                    "formulas": [],
                    "total_chunks": 1,
                    "total_tables": 0,
                    "total_formulas": 0
                }
            ]
        }
    }
