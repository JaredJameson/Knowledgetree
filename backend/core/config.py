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
    DB_PORT: int = 5437
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
        import os
        
        # Check if CORS_ORIGINS is set as environment variable
        cors_origins_env = os.getenv("CORS_ORIGINS")
        if cors_origins_env:
            # Parse comma-separated origins from environment
            return [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
        
        # Default origins
        origins = [
            "http://localhost:5173",  # Vite dev server
            "http://localhost:3000",  # Alternative frontend port
            "http://localhost:3555",  # Custom frontend port
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3555",
            self.FRONTEND_URL,  # Frontend URL from config
        ]
        # Filter out empty strings
        return [origin for origin in origins if origin]

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
    # AI Services - OpenAI API (Primary LLM)
    # ========================================================================
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

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
    STRIPE_API_KEY: str = ""
    STRIPE_PUBLIC_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    FRONTEND_URL: str = "http://localhost:3555"

    # ========================================================================
    # Monitoring & Analytics (Production)
    # ========================================================================
    SENTRY_DSN: str = ""
    LOGROCKET_APP_ID: str = ""

    # ========================================================================
    # Feature Flags
    # ========================================================================
    ENABLE_WEB_CRAWLING: bool = True  # Enable web crawling with Firecrawl + Serper
    ENABLE_AI_INSIGHTS: bool = True   # Enable AI-powered document and project insights
    ENABLE_AGENTIC_WORKFLOWS: bool = True  # Enable AI agent workflows for complex tasks

    # ========================================================================
    # Demo Mode (Testing without subscription limits)
    # ========================================================================
    DEMO_MODE: bool = False  # When true, all features are unlocked without limits

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables not defined in Settings


# Create global settings instance
settings = Settings()
