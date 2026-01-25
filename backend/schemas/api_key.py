"""
KnowledgeTree - API Key Schemas
Request and response models for API key management
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class KeyType(str, Enum):
    """Supported API key types"""
    anthropic = "anthropic"
    google_search = "google_search"
    firecrawl = "firecrawl"
    openai = "openai"
    custom = "custom"


# ============================================================================
# Request Models
# ============================================================================


class APIKeyCreate(BaseModel):
    """Request model for creating an API key"""
    key_type: KeyType = Field(..., description="Type of API key")
    name: str = Field(..., min_length=1, max_length=255, description="User-friendly name for the key")
    api_key: str = Field(..., min_length=1, description="The API key value (will be encrypted)")
    is_default: bool = Field(False, description="Set as default key for this type")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration date")

    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()

    @validator('api_key')
    def api_key_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('API key cannot be empty')
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "key_type": "anthropic",
                "name": "Claude API Key - Production",
                "api_key": "sk-ant-api03-...",
                "is_default": True
            }
        }


class APIKeyUpdate(BaseModel):
    """Request model for updating an API key"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    api_key: Optional[str] = Field(None, min_length=1)
    is_default: Optional[bool] = None

    @validator('name')
    def name_must_not_be_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip() if v else v

    @validator('api_key')
    def api_key_must_not_be_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError('API key cannot be empty')
        return v.strip() if v else v

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated name",
                "is_default": True
            }
        }


class APIKeyRotate(BaseModel):
    """Request model for rotating an API key"""
    new_api_key: str = Field(..., min_length=1, description="New API key value")

    @validator('new_api_key')
    def api_key_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('API key cannot be empty')
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "new_api_key": "sk-ant-api03-NEW-KEY-VALUE"
            }
        }


# ============================================================================
# Response Models
# ============================================================================


class APIKeyResponse(BaseModel):
    """Response model for API key (without the actual key value)"""
    id: int
    key_type: str
    name: str
    key_prefix: str  # First 8 chars for identification
    is_active: bool
    is_default: bool
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

        json_schema_extra = {
            "example": {
                "id": 1,
                "key_type": "anthropic",
                "name": "Claude API Key - Production",
                "key_prefix": "sk-ant-a...",
                "is_active": True,
                "is_default": True,
                "last_used_at": "2024-01-22T10:30:00Z",
                "expires_at": None,
                "created_at": "2024-01-15T09:00:00Z",
                "updated_at": "2024-01-15T09:00:00Z"
            }
        }


class APIKeyDetailResponse(APIKeyResponse):
    """Response model with masked key value"""
    id: int
    key_type: str
    name: str
    key_prefix: str
    masked_key: str  # Masked version like "sk-ant-...xxxx"
    is_active: bool
    is_default: bool
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class APIKeyListResponse(BaseModel):
    """Response model for listing API keys"""
    keys: List[APIKeyResponse]
    total: int
    by_type: dict[str, int]  # Count of keys by type

    class Config:
        json_schema_extra = {
            "example": {
                "keys": [],
                "total": 5,
                "by_type": {
                    "anthropic": 2,
                    "google_search": 1,
                    "firecrawl": 2
                }
            }
        }


class APIKeyCreateResponse(BaseModel):
    """Response model for created API key"""
    id: int
    key_type: str
    name: str
    key_prefix: str
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "key_type": "anthropic",
                "name": "Claude API Key - Production",
                "key_prefix": "sk-ant-a...",
                "message": "API key created successfully"
            }
        }


class APIKeyValidationResponse(BaseModel):
    """Response model for key validation"""
    is_valid: bool
    key_type: str
    message: str
    last_validated: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "is_valid": True,
                "key_type": "anthropic",
                "message": "API key is valid and active",
                "last_validated": "2024-01-22T10:30:00Z"
            }
        }
