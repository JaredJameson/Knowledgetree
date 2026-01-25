"""
KnowledgeTree Backend - FastAPI Application
Main entry point for the application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.config import settings
from core.database import AsyncSessionLocal

# Import routers
from api.routes import auth_router, documents_router, categories_router, projects_router, search_router, chat_router, export_router, artifacts_router, usage_router, crawl_router, workflows_router
from api.routes.insights import router as insights_router
from api.routes.subscriptions import router as subscriptions_router
from api.routes.api_keys import router as api_keys_router
from api.routes.youtube import router as youtube_router

# Import services for initialization
from services.bm25_service import bm25_service
from services.cross_encoder_service import cross_encoder_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    print("🚀 KnowledgeTree backend starting up...")
    print(f"📦 Environment: {settings.ENVIRONMENT}")
    print(f"🔧 Debug mode: {settings.DEBUG}")

    # Initialize BM25 index for sparse retrieval (TIER 1 Advanced RAG - Phase 1)
    try:
        print("🔄 Initializing BM25 sparse retrieval index...")
        async with AsyncSessionLocal() as db:
            await bm25_service.initialize(db)
        print("✅ BM25 index initialized successfully")
    except Exception as e:
        print(f"⚠️ Failed to initialize BM25 index: {e}")
        print("   Sparse retrieval will not be available")

    # Initialize Cross-Encoder for reranking (TIER 1 Advanced RAG - Phase 3)
    try:
        print("🔄 Initializing Cross-Encoder reranking model...")
        cross_encoder_service.initialize()
        print("✅ Cross-Encoder initialized successfully")
    except Exception as e:
        print(f"⚠️ Failed to initialize Cross-Encoder: {e}")
        print("   Reranking will not be available")

    yield

    # Shutdown
    print("🛑 KnowledgeTree backend shutting down...")


# Create FastAPI application
app = FastAPI(
    title="KnowledgeTree API",
    description="AI-powered knowledge repository and RAG platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring
    """
    return {
        "status": "healthy",
        "service": "KnowledgeTree API",
        "version": "0.1.0",
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "KnowledgeTree API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }


# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(categories_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(export_router, prefix="/api/v1")
app.include_router(artifacts_router, prefix="/api/v1")
app.include_router(usage_router, prefix="/api/v1")
app.include_router(crawl_router, prefix="/api/v1")
app.include_router(workflows_router, prefix="/api/v1")
app.include_router(insights_router, prefix="/api/v1")
app.include_router(subscriptions_router, prefix="/api/v1")
app.include_router(api_keys_router, prefix="/api/v1")
app.include_router(youtube_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG,
    )
