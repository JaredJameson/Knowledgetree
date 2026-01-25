"""
KnowledgeTree - API Key Encryption Service
Secure encryption/decryption for API keys using Fernet (AES-128)
"""

import os
import base64
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from models.api_key import APIKey, KeyType
from core.config import settings


class KeyEncryptionService:
    """
    Service for encrypting and decrypting API keys

    Uses Fernet symmetric encryption (AES-128) with PBKDF2 key derivation.
    Keys are encrypted at rest and only decrypted when needed.
    """

    def __init__(self):
        self._fernet: Optional[Fernet] = None
        self._init_encryption()

    def _init_encryption(self):
        """Initialize Fernet cipher with key from settings"""
        # Get encryption key from settings or environment
        key = settings.API_ENCRYPTION_KEY if hasattr(settings, 'API_ENCRYPTION_KEY') else os.getenv("API_ENCRYPTION_KEY")

        if not key:
            # Generate a warning - in production this should be set
            # For development, we'll use a derived key from SECRET_KEY
            import warnings
            warnings.warn(
                "API_ENCRYPTION_KEY not set. Using SECRET_KEY for derivation. "
                "Set API_ENCRYPTION_KEY in production for proper security."
            )
            secret = settings.SECRET_KEY if hasattr(settings, 'SECRET_KEY') else "dev-secret-key-change-in-production"
            # Derive a proper key from SECRET_KEY
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'knowledgetree-api-keys',  # Fixed salt for consistency
                iterations=100000,
            )
            key_bytes = kdf.derive(secret.encode())
            key = base64.urlsafe_b64encode(key_bytes)

        # Ensure key is properly formatted for Fernet (44 bytes base64)
        if isinstance(key, str):
            key_bytes = key.encode()
        else:
            key_bytes = key

        # Pad or truncate to 44 bytes (32 bytes after base64 decode)
        if len(key_bytes) < 44:
            # Pad with zeros
            key_bytes = key_bytes + b'=' * (44 - len(key_bytes))
        elif len(key_bytes) > 44:
            # Truncate - not recommended but handles edge case
            key_bytes = key_bytes[:44]

        try:
            self._fernet = Fernet(key_bytes)
        except Exception as e:
            # If Fernet initialization fails, try with proper key derivation
            import warnings
            warnings.warn(f"Fernet initialization failed: {e}. Using fallback key derivation.")
            # Derive proper 32-byte key
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'knowledgetree-api-keys-fallback',
                iterations=100000,
            )
            derived_key = kdf.derive(key_bytes[:32] if len(key_bytes) >= 32 else b'knowledgetree-fallback-key')
            fernet_key = base64.urlsafe_b64encode(derived_key)
            self._fernet = Fernet(fernet_key)

    def encrypt_key(self, api_key: str) -> str:
        """
        Encrypt an API key

        Args:
            api_key: Plain text API key

        Returns:
            Encrypted key as base64 string
        """
        if not self._fernet:
            self._init_encryption()

        encrypted = self._fernet.encrypt(api_key.encode())
        return encrypted.decode()

    def decrypt_key(self, encrypted_key: str) -> str:
        """
        Decrypt an API key

        Args:
            encrypted_key: Encrypted key as base64 string

        Returns:
            Plain text API key

        Raises:
            InvalidToken: If decryption fails (wrong key or corrupted data)
        """
        if not self._fernet:
            self._init_encryption()

        decrypted = self._fernet.decrypt(encrypted_key.encode())
        return decrypted.decode()

    def get_key_prefix(self, api_key: str, length: int = 8) -> str:
        """
        Get prefix of key for identification (e.g., "sk-ant-xxx...")

        Args:
            api_key: Plain text API key
            length: Number of characters to show

        Returns:
            Key prefix with ellipsis
        """
        if len(api_key) <= length:
            return api_key
        return f"{api_key[:length]}..."


class APIKeyService:
    """
    Service for managing API keys in the database

    Provides CRUD operations for encrypted API key storage.
    """

    def __init__(self):
        self.encryption = KeyEncryptionService()

    async def create_api_key(
        self,
        db: AsyncSession,
        user_id: int,
        key_type: KeyType,
        name: str,
        api_key: str,
        is_default: bool = False,
        expires_at: Optional[datetime] = None
    ) -> APIKey:
        """
        Create a new encrypted API key

        Args:
            db: Database session
            user_id: User ID
            key_type: Type of API key
            name: User-friendly name
            api_key: Plain text API key (will be encrypted)
            is_default: Whether this is the default key for this type
            expires_at: Optional expiration date

        Returns:
            Created APIKey record
        """
        # If setting as default, unset other defaults for this type
        if is_default:
            result = await db.execute(
                select(APIKey).where(
                    APIKey.user_id == user_id,
                    APIKey.key_type == key_type.value,
                    APIKey.is_default == True
                )
            )
            existing_defaults = result.scalars().all()
            for key in existing_defaults:
                key.is_default = False

        # Encrypt the key
        encrypted_key = self.encryption.encrypt_key(api_key)
        key_prefix = self.encryption.get_key_prefix(api_key)

        # Create record
        db_key = APIKey(
            user_id=user_id,
            key_type=key_type.value,
            name=name,
            encrypted_key=encrypted_key,
            key_prefix=key_prefix,
            is_default=is_default,
            expires_at=expires_at
        )

        db.add(db_key)
        await db.commit()
        await db.refresh(db_key)

        return db_key

    async def get_api_key(
        self,
        db: AsyncSession,
        key_id: int,
        user_id: int
    ) -> Optional[APIKey]:
        """
        Get API key by ID (without decrypting)

        Args:
            db: Database session
            key_id: Key ID
            user_id: User ID for authorization

        Returns:
            APIKey record or None
        """
        result = await db.execute(
            select(APIKey).where(
                APIKey.id == key_id,
                APIKey.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_decrypted_key(
        self,
        db: AsyncSession,
        key_id: int,
        user_id: int
    ) -> Optional[str]:
        """
        Get decrypted API key value

        Args:
            db: Database session
            key_id: Key ID
            user_id: User ID for authorization

        Returns:
            Decrypted API key or None
        """
        db_key = await self.get_api_key(db, key_id, user_id)
        if not db_key:
            return None

        try:
            return self.encryption.decrypt_key(db_key.encrypted_key)
        except InvalidToken:
            return None

    async def list_user_keys(
        self,
        db: AsyncSession,
        user_id: int,
        key_type: Optional[KeyType] = None
    ) -> list[APIKey]:
        """
        List all API keys for a user

        Args:
            db: Database session
            user_id: User ID
            key_type: Optional filter by key type

        Returns:
            List of APIKey records
        """
        query = select(APIKey).where(APIKey.user_id == user_id)

        if key_type:
            query = query.where(APIKey.key_type == key_type.value)

        query = query.order_by(APIKey.created_at.desc())

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_default_key(
        self,
        db: AsyncSession,
        user_id: int,
        key_type: KeyType
    ) -> Optional[str]:
        """
        Get the default API key for a user and type

        Args:
            db: Database session
            user_id: User ID
            key_type: Type of key to get

        Returns:
            Decrypted API key or None
        """
        result = await db.execute(
            select(APIKey).where(
                APIKey.user_id == user_id,
                APIKey.key_type == key_type.value,
                APIKey.is_default == True,
                APIKey.is_active == True
            ).order_by(APIKey.created_at.desc())
        )
        db_key = result.scalars().first()

        if not db_key:
            return None

        try:
            # Update last used
            db_key.last_used_at = datetime.utcnow()
            await db.commit()

            return self.encryption.decrypt_key(db_key.encrypted_key)
        except InvalidToken:
            return None

    async def update_api_key(
        self,
        db: AsyncSession,
        key_id: int,
        user_id: int,
        name: Optional[str] = None,
        api_key: Optional[str] = None,
        is_default: Optional[bool] = None
    ) -> Optional[APIKey]:
        """
        Update an API key

        Args:
            db: Database session
            key_id: Key ID
            user_id: User ID
            name: New name
            api_key: New key value (will be encrypted)
            is_default: New default status

        Returns:
            Updated APIKey or None
        """
        db_key = await self.get_api_key(db, key_id, user_id)
        if not db_key:
            return None

        if name is not None:
            db_key.name = name

        if api_key is not None:
            db_key.encrypted_key = self.encryption.encrypt_key(api_key)
            db_key.key_prefix = self.encryption.get_key_prefix(api_key)

        if is_default is not None:
            if is_default:
                # Unset other defaults for this type
                result = await db.execute(
                    select(APIKey).where(
                        APIKey.user_id == user_id,
                        APIKey.key_type == db_key.key_type,
                        APIKey.id != key_id,
                        APIKey.is_default == True
                    )
                )
                for key in result.scalars().all():
                    key.is_default = False

            db_key.is_default = is_default

        await db.commit()
        await db.refresh(db_key)

        return db_key

    async def delete_api_key(
        self,
        db: AsyncSession,
        key_id: int,
        user_id: int
    ) -> bool:
        """
        Delete an API key

        Args:
            db: Database session
            key_id: Key ID
            user_id: User ID

        Returns:
            True if deleted, False otherwise
        """
        db_key = await self.get_api_key(db, key_id, user_id)
        if not db_key:
            return False

        await db.delete(db_key)
        await db.commit()

        return True

    async def rotate_key(
        self,
        db: AsyncSession,
        key_id: int,
        user_id: int,
        new_api_key: str
    ) -> Optional[APIKey]:
        """
        Rotate an API key (update with new value)

        Args:
            db: Database session
            key_id: Key ID
            user_id: User ID
            new_api_key: New API key value

        Returns:
            Updated APIKey or None
        """
        return await self.update_api_key(db, key_id, user_id, api_key=new_api_key)


# Singleton instance
_api_key_service: Optional[APIKeyService] = None


def get_api_key_service() -> APIKeyService:
    """Get global API key service instance"""
    global _api_key_service
    if _api_key_service is None:
        _api_key_service = APIKeyService()
    return _api_key_service


async def get_api_key_for_agent(
    db: AsyncSession,
    user_id: int,
    key_type: KeyType,
    env_fallback: str
) -> Optional[str]:
    """
    Get API key for agent use with fallback to environment variable

    This is the primary function that agents should use to get API keys.
    It tries to get the key from the database first, then falls back to
    environment variables for backward compatibility.

    Args:
        db: Database session
        user_id: User ID
        key_type: Type of key to retrieve
        env_fallback: Environment variable name to check as fallback

    Returns:
        API key value or None

    Example:
        ```python
        anthropic_key = await get_api_key_for_agent(
            db, user_id, KeyType.ANTHROPIC, "ANTHROPIC_API_KEY"
        )
        ```
    """
    service = get_api_key_service()

    # Try to get from database
    db_key = await service.get_default_key(db, user_id, key_type)
    if db_key:
        return db_key

    # Fallback to environment variable
    import os
    return os.getenv(env_fallback)
