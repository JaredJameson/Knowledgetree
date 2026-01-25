# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**KnowledgeTree** is an AI-powered enterprise knowledge repository and RAG (Retrieval-Augmented Generation) platform. It's a multi-tenant SaaS application enabling users to build searchable knowledge bases from PDFs, web content, and documents with AI-powered chat, insights, and agentic workflows.

**Tech Stack:**
- **Frontend**: React 19 + TypeScript 5.3+, Vite 6.0+, TailwindCSS 3.4+, shadcn/ui
- **Backend**: FastAPI 0.109.0+ (Python 3.11+), PostgreSQL 16 + pgvector 0.7
- **AI/RAG**: BGE-M3 embeddings (local, 1024 dims), Claude 3.5 Sonnet for chat
- **Infrastructure**: Docker Compose, Railway.app (MVP), AWS (production)

## Development Commands

### Full Stack (Docker)
```bash
# Start all services (db, redis, backend, frontend)
docker-compose up

# Rebuild and start
docker-compose up --build

# Stop all services
docker-compose down
```

### Backend
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run development server (auto-reload)
uvicorn main:app --reload

# Run tests
pytest                           # All tests
pytest tests/api/                # API tests only
pytest tests/services/           # Service tests only
pytest tests/e2e/                # E2E workflow tests (100% passing)
pytest tests/workflow_tests/     # LangGraph workflow tests
pytest -v                        # Verbose output
pytest --cov=.                   # With coverage

# Run specific test file
pytest tests/e2e/test_e2e_workflows.py -v

# Run specific test class/function
pytest tests/api/test_documents.py::TestDocumentUpload -v
pytest tests/api/test_documents.py::TestDocumentUpload::test_upload_pdf -v

# Database migrations
alembic upgrade head             # Apply migrations
alembic revision --autogenerate -m "message"  # Create migration

# Type checking
mypy .

# Linting
black .
flake8 .
```

### Frontend
```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev                      # Runs on http://localhost:5173

# Production build
npm run build

# Linting
npm run lint
```

### Manual API Testing
```bash
# In project root
./backend/test_projects_api.sh
./backend/test_category_api.sh
./backend/test_category_api_with_auth.sh
```

## Architecture

### Backend Architecture

**Clean Architecture Pattern** with separation of concerns:
- **Routes Layer** (`api/routes/`): FastAPI route handlers, input validation
- **Services Layer** (`services/`): Business logic, RAG pipeline, AI operations
- **Models Layer** (`models/`): SQLAlchemy ORM models
- **Schemas Layer** (`schemas/`): Pydantic request/response models
- **Core** (`core/`): Config, security, database connection

**Key Entry Point**: `backend/main.py`
- Initializes FastAPI with lifespan context manager
- Initializes BM25 sparse retrieval index and Cross-Encoder reranker on startup
- Includes routers for: auth, projects, documents, categories, search, chat, export, artifacts, usage, crawl, workflows, insights, subscriptions, api_keys, youtube
- Health check endpoint: `/health`
- API docs: `/docs` (Swagger UI), `/redoc` (ReDoc)

### Frontend Architecture

**Component-Based React** with TypeScript:
- **Pages** (`src/pages/`): Route-level components (Login, Dashboard, Projects, Documents, Search, Chat)
- **Components** (`src/components/`): Reusable UI components
- **Context** (`src/context/`): React Context providers (AuthContext, ThemeContext)
- **Lib** (`src/lib/`): Utilities, API clients
- **Locales** (`src/locales/`): i18n translations (Polish primary, English secondary)

**Key Entry Points**: `frontend/src/main.tsx` and `App.tsx`
- BrowserRouter with protected routes requiring authentication
- Route protection via ProtectedRoute component

### RAG Pipeline Architecture

**Advanced RAG Implementation** (TIER 1):

**Phase 1 - Sparse Retrieval**:
- `bm25_service.py`: BM25 sparse text indexing for keyword-based retrieval

**Phase 3 - Reranking**:
- `cross_encoder_service.py`: Cross-Encoder model for relevance reranking
- `reranking_optimizer.py`: Reranking optimization and tuning

**Core RAG Services**:
- `rag_service.py`: Main RAG orchestration
- `embedding_generator.py`: BGE-M3 document embeddings (1024 dimensions, multilingual)
- `search_service.py`: Vector similarity search
- `hybrid_search_service.py`: Combined vector + keyword search
- `pdf_processor.py`: Multi-stage PDF processing pipeline (PyMuPDF, docling, pdfplumber)

**Document Processing Services**:
- `text_chunker.py`: Text chunking with overlap
- `toc_extractor.py`: Table of Contents extraction
- `table_extractor.py`: Table extraction
- `formula_extractor.py`: Mathematical formula extraction
- `category_auto_generator.py`: Automatic category generation
- `category_tree_generator.py`: Hierarchical category tree generation

**Additional Services**:
- `youtube_transcriber.py`: YouTube video transcript extraction
- `langgraph_orchestrator.py`: LangGraph workflow orchestration
- `langgraph_nodes.py`: LangGraph workflow nodes
- `agents.py`: AI agent implementations
- `stripe_service.py`: Payment processing with Stripe
- `usage_service.py`: Usage tracking and limits
- `crawler_orchestrator.py`: Web crawling coordination
- `http_scraper.py`: Fast HTTP-based web scraping
- `playwright_scraper.py`: JavaScript-heavy site scraping
- `firecrawl_scraper.py`: Firecrawl API integration (optional)
- `google_search.py`: Google Custom Search integration
- `serper_search.py`: Serper.dev search API integration

### Database Architecture

**PostgreSQL 16 + pgvector** for vector storage:
- Async SQLAlchemy 2.0+ ORM
- Alembic for database migrations
- Vector columns for BGE-M3 embeddings (1024 dimensions)

**Migration Workflow**:
```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Service Ports (Docker Compose)
- **Frontend**: 3555 → 5173 (host:container, Vite dev server)
- **Backend**: 8765 → 8000 (host:container, FastAPI with auto-reload)
- **PostgreSQL**: 5437 → 5432 (host:container)
- **Redis**: 6381 → 6379 (host:container)

**Connection URLs**:
- Frontend: http://localhost:3555
- Backend API: http://localhost:8765
- API Docs: http://localhost:8765/docs
- Database: postgresql://knowledgetree:knowledgetree_secret@localhost:5437/knowledgetree

### Environment Configuration

**Backend** (`.env`):
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT signing key
- `ANTHROPIC_API_KEY`: Claude API for chat
- `OPENAI_API_KEY`: OpenAI API (gpt-4o-mini for primary LLM)
- `FIRECRAWL_API_KEY`: Web crawling (optional, paid)
- `SERPER_API_KEY`: Serper.dev search API (alternative to Google)
- `GOOGLE_CSE_API_KEY`: Google Custom Search API
- `STRIPE_API_KEY`: Stripe payment processing
- `EMBEDDING_MODEL`: BAAI/bge-m3
- `EMBEDDING_DIMENSIONS`: 1024
- `DEMO_MODE`: Enable demo mode (default: false)

**Frontend**:
- `VITE_API_URL`: Backend API URL

### Testing Infrastructure

**Backend (pytest)**:
- Async mode enabled (`pytest.ini`: `asyncio_mode = auto`)
- Test structure:
  - `tests/e2e/`: End-to-end workflow tests (100% passing, 5 test suites, 38 steps)
  - `tests/api/`: API endpoint tests, integration tests (~30% coverage)
  - `tests/services/`: Service layer unit tests
  - `tests/workflow_tests/`: LangGraph workflow and agent tests
- Manual test scripts: `test_*.sh` in backend root (projects, categories, API keys)
- Run specific test suites:
  - `pytest tests/e2e/` - E2E workflow tests (100% passing)
  - `pytest tests/api/` - API tests only
  - `pytest tests/services/` - Service tests only
  - `pytest tests/workflow_tests/` - Workflow tests only
- Run specific test file: `pytest tests/e2e/test_e2e_workflows.py -v`
- Run specific test class: `pytest tests/api/test_documents.py::TestDocumentUpload -v`

**Frontend**:
- ESLint for code quality (`npm run lint`)
- TypeScript compilation check (`tsc -b`)
- Vite build verification (`npm run build`)
- Preview production build (`npm run preview`)
- Hot module replacement (HMR) in development mode for instant updates

### AI/ML Services Initialization

The backend automatically initializes on startup:
1. **BM25 Index**: Sparse retrieval for keyword-based search
2. **Cross-Encoder**: Relevance reranking for improved results

Both are initialized in `main.py` lifespan context manager with error handling - failures log warnings but don't prevent startup.

### Code Style & Patterns

**Backend**:
- Async/await throughout for performance
- Type hints with Pydantic validation
- Dependency injection via FastAPI dependencies
- Service layer pattern for business logic

**Frontend**:
- Functional components with hooks
- TypeScript strict mode
- TailwindCSS for styling
- shadcn/ui component library patterns

### Language Support

**Primary**: Polish (`pl`)
**Secondary**: English (`en`)

Configure via `react-i18next` in `frontend/src/locales/`

### Important Implementation Notes

**Async/Await Pattern**:
- All database operations use async SQLAlchemy
- FastAPI route handlers are async
- Service methods that interact with DB or external APIs are async
- Use `AsyncSessionLocal()` for database sessions

**Dependency Injection**:
- Use FastAPI's dependency injection for DB sessions, auth, etc.
- See `api/dependencies/` for reusable dependencies
- Authentication via `get_current_user` dependency

**Error Handling**:
- Use FastAPI's HTTPException for API errors
- Service layer should raise appropriate exceptions
- Lifespan errors (BM25, Cross-Encoder initialization) are logged but don't prevent startup

**Background Jobs**:
- Celery configured for long-running tasks (crawling, workflow execution)
- Redis used as message broker and result backend

### Production Deployment

**Deployment Scripts** (`scripts/` directory):
- `deploy.sh`: Zero-downtime deployment with health checks and rollback capability
- `setup-ssl.sh`: Automated Let's Encrypt SSL certificate setup
- `vps-setup.sh`: VPS initialization script for Ubuntu 22.04+

**Production Configuration**:
- Use `docker-compose.production.yml` for production deployment
- Configuration template: `.env.production.template`
- Nginx reverse proxy with rate limiting and security headers
- Automatic SSL renewal via Let's Encrypt

**Deployment Commands**:
```bash
# Setup SSL (first time only)
./scripts/setup-ssl.sh your-domain.com admin@example.com

# Deploy with zero downtime
./scripts/deploy.sh

# Verify deployment
curl https://api.your-domain.com/health
```

### Current Sprint Status

**Sprint 0-3**: Foundation, Projects, Categories, PDF Upload & Vectorization, Search & Export
**Completed**: Projects API, Category API, Document API, RAG pipeline, Search, Export, Chat, Workflows
**Active Features**: All core features implemented through Sprint 8

See root directory status reports for detailed progress.
