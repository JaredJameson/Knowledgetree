"""
KnowledgeTree Backend - Configuration
Settings loaded from environment variables
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """

    # ========================================================================
    # Application Settings
    # ========================================================================
    APP_NAME: str = "KnowledgeTree"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_VERSION: str = "v1"

    # ========================================================================
    # Server Settings
    # ========================================================================
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # ========================================================================
    # Database Settings
    # ========================================================================
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "knowledgetree"
    DB_PASSWORD: str = "knowledgetree_secret"
    DB_NAME: str = "knowledgetree"

    @property
    def DATABASE_URL(self) -> str:
        """
        Construct async PostgreSQL connection string
        """
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # ========================================================================
    # Security Settings
    # ========================================================================
    SECRET_KEY: str = "dev_secret_key_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ========================================================================
    # CORS Settings
    # ========================================================================
    @property
    def CORS_ORIGINS(self) -> List[str]:
        """
        Allowed CORS origins (frontend URLs)
        """
        return [
            "http://localhost:5173",  # Vite dev server
            "http://localhost:3000",  # Alternative frontend port
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ]

    # ========================================================================
    # BGE-M3 Embeddings Settings
    # ========================================================================
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    EMBEDDING_DIMENSIONS: int = 1024
    EMBEDDING_DEVICE: str = "cpu"  # or "cuda" for GPU
    HF_HOME: str = "./models"  # HuggingFace cache directory

    # ========================================================================
    # PDF Processing Settings
    # ========================================================================
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    MAX_FILE_SIZE_MB: int = 50
    UPLOAD_DIR: str = "./uploads"

    # ========================================================================
    # AI Services - Anthropic Claude API
    # ========================================================================
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"

    # ========================================================================
    # Web Crawling - Firecrawl API (Sprint 6+)
    # ========================================================================
    FIRECRAWL_API_KEY: str = ""

    # ========================================================================
    # Web Search - Google CSE or Serper.dev (Sprint 7+)
    # ========================================================================
    GOOGLE_CSE_API_KEY: str = ""
    GOOGLE_CSE_ID: str = ""
    SERPER_API_KEY: str = ""

    # ========================================================================
    # Redis Settings (Optional)
    # ========================================================================
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    # ========================================================================
    # Email Settings (Optional - for user verification)
    # ========================================================================
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@knowledgetree.com"

    # ========================================================================
    # Stripe Payment Integration (Sprint 4+)
    # ========================================================================
    STRIPE_PUBLIC_KEY: str = ""
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # ========================================================================
    # Monitoring & Analytics (Production)
    # ========================================================================
    SENTRY_DSN: str = ""
    LOGROCKET_APP_ID: str = ""

    # ========================================================================
    # Feature Flags
    # ========================================================================
    ENABLE_WEB_CRAWLING: bool = False
    ENABLE_AI_INSIGHTS: bool = False
    ENABLE_AGENTIC_WORKFLOWS: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create global settings instance
settings = Settings()
