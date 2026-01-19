"""
KnowledgeTree Backend - FastAPI Application
Main entry point for the application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.config import settings

# Import routers (will be added in later sprints)
# from api.routes import auth, projects, categories, documents, search, chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    print("🚀 KnowledgeTree backend starting up...")
    print(f"📦 Environment: {settings.ENVIRONMENT}")
    print(f"🔧 Debug mode: {settings.DEBUG}")

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


# Include routers (will be uncommented in later sprints)
# app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
# app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
# app.include_router(categories.router, prefix="/api/categories", tags=["Categories"])
# app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
# app.include_router(search.router, prefix="/api/search", tags=["Search"])
# app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG,
    )
