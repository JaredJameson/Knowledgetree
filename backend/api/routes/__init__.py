"""
KnowledgeTree Backend - API Routes
"""

from api.routes.auth import router as auth_router
from api.routes.documents import router as documents_router
from api.routes.categories import router as categories_router
from api.routes.projects import router as projects_router
from api.routes.search import router as search_router
from api.routes.chat import router as chat_router
from api.routes.export import router as export_router
from api.routes.artifacts import router as artifacts_router
from api.routes.usage import router as usage_router
from api.routes.crawl import router as crawl_router
from api.routes.workflows import router as workflows_router

__all__ = ["auth_router", "documents_router", "categories_router", "projects_router", "search_router", "chat_router", "export_router", "artifacts_router", "usage_router", "crawl_router", "workflows_router"]
