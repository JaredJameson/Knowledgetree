"""
KnowledgeTree - API Keys Management Routes
REST API for encrypted API key storage and management
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from datetime import datetime

from core.database import get_db
from api.dependencies import get_current_user
from models.user import User
from models.api_key import APIKey, KeyType as ModelKeyType
from schemas.api_key import (
    APIKeyCreate,
    APIKeyCreateResponse,
    APIKeyUpdate,
    APIKeyRotate,
    APIKeyResponse,
    APIKeyDetailResponse,
    APIKeyListResponse,
    APIKeyValidationResponse,
    KeyType as SchemaKeyType,
)
from services.api_key_service import get_api_key_service


router = APIRouter(prefix='/api-keys', tags=['API Keys'])


# ============================================================================
# Helper Functions
# ============================================================================


def map_key_type(schema_type: SchemaKeyType) -> ModelKeyType:
    """Map schema KeyType to model KeyType"""
    return ModelKeyType(schema_type.value)


async def get_api_key(
    key_id: int,
    user_id: int,
    db: AsyncSession
) -> APIKey:
    """Get API key by ID with user authorization check"""
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == key_id,
            APIKey.user_id == user_id
        )
    )
    key = result.scalar_one_or_none()

    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    return key


def mask_api_key(key_prefix: str, length: int = 4) -> str:
    """Create masked version of API key"""
    return f"{key_prefix}...xxxx"


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("", response_model=APIKeyCreateResponse, status_code=201)
async def create_api_key(
    key_data: APIKeyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new encrypted API key

    Stores API key with AES-256 encryption. The key is encrypted at rest
    and only decrypted when needed by services.

    **Example:**
    ```json
    {
        "key_type": "anthropic",
        "name": "Claude API Key - Production",
        "api_key": "sk-ant-api03-...",
        "is_default": true
    }
    ```
    """
    service = get_api_key_service()

    # Check if key already exists with same name for this user
    result = await db.execute(
        select(APIKey).where(
            APIKey.user_id == current_user.id,
            APIKey.name == key_data.name
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="API key with this name already exists"
        )

    # Create encrypted key
    db_key = await service.create_api_key(
        db=db,
        user_id=current_user.id,
        key_type=map_key_type(key_data.key_type),
        name=key_data.name,
        api_key=key_data.api_key,
        is_default=key_data.is_default,
        expires_at=key_data.expires_at
    )

    return APIKeyCreateResponse(
        id=db_key.id,
        key_type=db_key.key_type,
        name=db_key.name,
        key_prefix=db_key.key_prefix or "****",
        message="API key created successfully"
    )


@router.get("", response_model=APIKeyListResponse)
async def list_api_keys(
    key_type: Optional[SchemaKeyType] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all API keys for current user

    Returns paginated list of encrypted API keys with optional type filter.
    Note: Actual key values are never returned - only prefixes for identification.
    """
    service = get_api_key_service()

    # Get filtered keys
    key_type_filter = map_key_type(key_type) if key_type else None
    keys = await service.list_user_keys(db, current_user.id, key_type_filter)

    # Get counts by type
    count_result = await db.execute(
        select(APIKey.key_type, func.count(APIKey.id))
        .where(APIKey.user_id == current_user.id)
        .group_by(APIKey.key_type)
    )
    by_type = {row[0]: row[1] for row in count_result.all()}

    # Apply pagination
    total = len(keys)
    paginated_keys = keys[skip:skip + limit]

    return APIKeyListResponse(
        keys=[
            APIKeyResponse(
                id=key.id,
                key_type=key.key_type,
                name=key.name,
                key_prefix=key.key_prefix or "****",
                is_active=key.is_active,
                is_default=key.is_default,
                last_used_at=key.last_used_at,
                expires_at=key.expires_at,
                created_at=key.created_at,
                updated_at=key.updated_at
            )
            for key in paginated_keys
        ],
        total=total,
        by_type=by_type
    )


@router.get("/{key_id}", response_model=APIKeyDetailResponse)
async def get_api_key_detail(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get API key details by ID

    Returns key information with masked key value.
    Actual key value is never returned via API.
    """
    key = await get_api_key(key_id, current_user.id, db)

    return APIKeyDetailResponse(
        id=key.id,
        key_type=key.key_type,
        name=key.name,
        key_prefix=key.key_prefix or "****",
        masked_key=mask_api_key(key.key_prefix or "****"),
        is_active=key.is_active,
        is_default=key.is_default,
        last_used_at=key.last_used_at,
        expires_at=key.expires_at,
        created_at=key.created_at,
        updated_at=key.updated_at
    )


@router.patch("/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: int,
    key_data: APIKeyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an API key

    Can update name, key value (encrypted), or default status.
    """
    service = get_api_key_service()

    # Check if new name conflicts with existing key
    if key_data.name:
        result = await db.execute(
            select(APIKey).where(
                APIKey.user_id == current_user.id,
                APIKey.name == key_data.name,
                APIKey.id != key_id
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="API key with this name already exists"
            )

    updated_key = await service.update_api_key(
        db=db,
        key_id=key_id,
        user_id=current_user.id,
        name=key_data.name,
        api_key=key_data.api_key,
        is_default=key_data.is_default
    )

    if not updated_key:
        raise HTTPException(status_code=404, detail="API key not found")

    return APIKeyResponse(
        id=updated_key.id,
        key_type=updated_key.key_type,
        name=updated_key.name,
        key_prefix=updated_key.key_prefix or "****",
        is_active=updated_key.is_active,
        is_default=updated_key.is_default,
        last_used_at=updated_key.last_used_at,
        expires_at=updated_key.expires_at,
        created_at=updated_key.created_at,
        updated_at=updated_key.updated_at
    )


@router.post("/{key_id}/rotate", response_model=APIKeyResponse)
async def rotate_api_key(
    key_id: int,
    rotate_data: APIKeyRotate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Rotate an API key

    Updates the key with a new value while keeping other properties.
    Useful for periodic key rotation without reconfiguring the entire key.
    """
    service = get_api_key_service()

    rotated_key = await service.rotate_key(
        db=db,
        key_id=key_id,
        user_id=current_user.id,
        new_api_key=rotate_data.new_api_key
    )

    if not rotated_key:
        raise HTTPException(status_code=404, detail="API key not found")

    return APIKeyResponse(
        id=rotated_key.id,
        key_type=rotated_key.key_type,
        name=rotated_key.name,
        key_prefix=rotated_key.key_prefix or "****",
        is_active=rotated_key.is_active,
        is_default=rotated_key.is_default,
        last_used_at=rotated_key.last_used_at,
        expires_at=rotated_key.expires_at,
        created_at=rotated_key.created_at,
        updated_at=rotated_key.updated_at
    )


@router.delete("/{key_id}")
async def delete_api_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete an API key

    Permanently removes the API key from storage.
    This action cannot be undone.
    """
    service = get_api_key_service()

    success = await service.delete_api_key(db, key_id, current_user.id)

    if not success:
        raise HTTPException(status_code=404, detail="API key not found")

    return {
        "message": "API key deleted successfully",
        "key_id": key_id
    }


@router.get("/default/{key_type}", response_model=APIKeyValidationResponse)
async def get_default_key_status(
    key_type: SchemaKeyType,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check if default key exists for a type

    Validates that the user has a default API key configured for the specified type.
    """
    service = get_api_key_service()

    default_key = await service.get_default_key(
        db=db,
        user_id=current_user.id,
        key_type=map_key_type(key_type)
    )

    if default_key:
        return APIKeyValidationResponse(
            is_valid=True,
            key_type=key_type.value,
            message=f"Default {key_type.value} API key is configured",
            last_validated=datetime.utcnow()
        )
    else:
        return APIKeyValidationResponse(
            is_valid=False,
            key_type=key_type.value,
            message=f"No default {key_type.value} API key found. Please configure one.",
            last_validated=None
        )


@router.post("/{key_id}/validate", response_model=APIKeyValidationResponse)
async def validate_api_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validate an API key

    Attempts to decrypt and validate the stored API key.
    """
    service = get_api_key_service()

    # Get the key
    db_key = await get_api_key(key_id, current_user.id, db)

    # Try to decrypt
    try:
        decrypted = await service.get_decrypted_key(db, key_id, current_user.id)

        if decrypted:
            return APIKeyValidationResponse(
                is_valid=True,
                key_type=db_key.key_type,
                message="API key is valid and can be decrypted",
                last_validated=datetime.utcnow()
            )
        else:
            return APIKeyValidationResponse(
                is_valid=False,
                key_type=db_key.key_type,
                message="API key decryption failed",
                last_validated=datetime.utcnow()
            )
    except Exception as e:
        return APIKeyValidationResponse(
            is_valid=False,
            key_type=db_key.key_type,
            message=f"Validation failed: {str(e)}",
            last_validated=datetime.utcnow()
        )
