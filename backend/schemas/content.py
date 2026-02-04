"""
Content Workbench Schemas
Pydantic models for content editing, versioning, and AI operations
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Enums

class ContentStatus(str, Enum):
    """Content workflow status"""
    DRAFT = "draft"
    REVIEW = "review"
    PUBLISHED = "published"


class ToneType(str, Enum):
    """Available tone types for rewriting"""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    TECHNICAL = "technical"
    FRIENDLY = "friendly"
    FORMAL = "formal"
    CONVERSATIONAL = "conversational"


class ReadingLevel(str, Enum):
    """Target reading levels for simplification"""
    BASIC = "basic"
    GENERAL = "general"
    ADVANCED = "advanced"


class QuoteType(str, Enum):
    """Types of extracted quotes"""
    FACT = "fact"
    OPINION = "opinion"
    DEFINITION = "definition"
    STATISTIC = "statistic"
    EXAMPLE = "example"


class TemplateType(str, Enum):
    """Content template categories"""
    HOW_TO = "how_to"
    FAQ = "faq"
    TUTORIAL = "tutorial"
    ARTICLE = "article"
    REFERENCE = "reference"


# Content Version Schemas

class ContentVersionBase(BaseModel):
    """Base content version schema"""
    content: str = Field(..., min_length=1)
    change_summary: Optional[str] = Field(None, max_length=500)


class ContentVersionResponse(BaseModel):
    """Content version response"""
    id: int
    category_id: int
    version_number: int
    content: str
    created_by: Optional[int]
    created_at: datetime
    change_summary: Optional[str]

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "category_id": 42,
                    "version_number": 5,
                    "content": "# Updated Content\n\nThis is version 5...",
                    "created_by": 1,
                    "created_at": "2026-02-02T12:00:00Z",
                    "change_summary": "Added new section on security"
                }
            ]
        }
    }


# Extracted Quote Schemas

class ExtractedQuoteResponse(BaseModel):
    """Extracted quote response"""
    id: int
    category_id: int
    quote_text: str
    context_before: Optional[str]
    context_after: Optional[str]
    quote_type: Optional[str]
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "category_id": 42,
                    "quote_text": "Security is not a feature, it's a foundation.",
                    "context_before": "When building applications, many developers...",
                    "context_after": "This means implementing security from day one...",
                    "quote_type": "opinion",
                    "created_at": "2026-02-02T12:00:00Z"
                }
            ]
        }
    }


# Content Template Schemas

class TemplateSectionCreate(BaseModel):
    """Template section structure"""
    title: str = Field(..., min_length=1, max_length=200)
    prompt: str = Field(..., min_length=1, max_length=1000)
    order: int = Field(..., ge=0)


class ContentTemplateCreate(BaseModel):
    """Schema for creating a content template"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    template_type: TemplateType
    sections: List[TemplateSectionCreate] = Field(..., min_items=1)
    is_public: bool = Field(default=True)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "How-To Guide Template",
                    "description": "Standard template for creating how-to guides",
                    "template_type": "how_to",
                    "sections": [
                        {
                            "title": "Introduction",
                            "prompt": "Explain what this guide covers and who it's for",
                            "order": 1
                        },
                        {
                            "title": "Prerequisites",
                            "prompt": "List required knowledge, tools, and setup",
                            "order": 2
                        },
                        {
                            "title": "Step-by-Step Instructions",
                            "prompt": "Provide detailed, numbered steps",
                            "order": 3
                        },
                        {
                            "title": "Troubleshooting",
                            "prompt": "Address common issues and solutions",
                            "order": 4
                        }
                    ],
                    "is_public": True
                }
            ]
        }
    }


class ContentTemplateResponse(BaseModel):
    """Content template response"""
    id: int
    name: str
    description: Optional[str]
    template_type: str
    structure: Dict[str, Any]  # JSONB field
    is_public: bool
    created_by: Optional[int]
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "name": "How-To Guide Template",
                    "description": "Standard template for creating how-to guides",
                    "template_type": "how_to",
                    "structure": {
                        "sections": [
                            {
                                "title": "Introduction",
                                "prompt": "Explain what this guide covers and who it's for",
                                "order": 1
                            }
                        ]
                    },
                    "is_public": True,
                    "created_by": 1,
                    "created_at": "2026-02-02T12:00:00Z"
                }
            ]
        }
    }


# AI Rewriting Request Schemas

class SummarizeRequest(BaseModel):
    """Request for content summarization"""
    content: str = Field(..., min_length=1)
    max_length: Optional[int] = Field(None, ge=10, le=1000)
    focus: Optional[str] = Field(None, max_length=200)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "content": "Long article text here...",
                    "max_length": 150,
                    "focus": "technical implementation"
                }
            ]
        }
    }


class ExpandRequest(BaseModel):
    """Request for content expansion"""
    content: str = Field(..., min_length=1)
    target_length: Optional[int] = Field(None, ge=100, le=5000)
    add_details: Optional[str] = Field(None, max_length=200)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "content": "Brief summary to expand...",
                    "target_length": 500,
                    "add_details": "examples and code snippets"
                }
            ]
        }
    }


class SimplifyRequest(BaseModel):
    """Request for content simplification"""
    content: str = Field(..., min_length=1)
    reading_level: ReadingLevel = Field(default=ReadingLevel.GENERAL)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "content": "Complex technical text here...",
                    "reading_level": "basic"
                }
            ]
        }
    }


class RewriteToneRequest(BaseModel):
    """Request for tone rewriting"""
    content: str = Field(..., min_length=1)
    tone: ToneType
    preserve_facts: bool = Field(default=True)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "content": "Original text here...",
                    "tone": "professional",
                    "preserve_facts": True
                }
            ]
        }
    }


class ExtractQuotesRequest(BaseModel):
    """Request for quote extraction"""
    content: str = Field(..., min_length=1)
    max_quotes: int = Field(default=10, ge=1, le=50)
    quote_types: Optional[List[QuoteType]] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "content": "Document content to extract quotes from...",
                    "max_quotes": 10,
                    "quote_types": ["fact", "statistic"]
                }
            ]
        }
    }


class GenerateOutlineRequest(BaseModel):
    """Request for outline generation"""
    topic: str = Field(..., min_length=1, max_length=500)
    depth: int = Field(default=2, ge=1, le=3)
    style: TemplateType = Field(default=TemplateType.ARTICLE)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "topic": "Introduction to Microservices Architecture",
                    "depth": 2,
                    "style": "tutorial"
                }
            ]
        }
    }


# AI Operation Response Schemas

class AIOperationResponse(BaseModel):
    """Generic AI operation response"""
    result: str
    operation: str
    tokens_used: Optional[int] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "result": "Transformed content here...",
                    "operation": "summarize",
                    "tokens_used": 450
                }
            ]
        }
    }


# Content Editor Request Schemas

class SaveDraftRequest(BaseModel):
    """Request to save draft content"""
    draft_content: str = Field(..., min_length=1)
    change_summary: Optional[str] = Field(None, max_length=500)
    auto_version: bool = Field(default=True)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "draft_content": "# Updated Content\n\nNew section added...",
                    "change_summary": "Added troubleshooting section",
                    "auto_version": True
                }
            ]
        }
    }


class PublishContentRequest(BaseModel):
    """Request to publish content"""
    create_version: bool = Field(default=True)


class RestoreVersionRequest(BaseModel):
    """Request to restore a version"""
    version_number: int = Field(..., ge=1)
    create_new_version: bool = Field(default=True)


class CompareVersionsRequest(BaseModel):
    """Request to compare two versions"""
    version_a: int = Field(..., ge=1)
    version_b: int = Field(..., ge=1)


class VersionComparisonResponse(BaseModel):
    """Version comparison response"""
    version_a: Dict[str, Any]
    version_b: Dict[str, Any]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "version_a": {
                        "number": 3,
                        "content": "Version 3 content...",
                        "created_at": "2026-02-01T10:00:00Z",
                        "created_by": 1,
                        "change_summary": "Initial version"
                    },
                    "version_b": {
                        "number": 5,
                        "content": "Version 5 content...",
                        "created_at": "2026-02-02T12:00:00Z",
                        "created_by": 1,
                        "change_summary": "Added security section"
                    }
                }
            ]
        }
    }
