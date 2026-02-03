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
- Initializes FastAPI with lifespan context manager (lines 25-58)
- On startup, initializes BM25 sparse retrieval index and Cross-Encoder reranker
  - BM25: Sparse retrieval for keyword-based search (initialized from database chunks)
  - Cross-Encoder: Reranking model for relevance scoring (loads on first request)
  - Both use error handling - failures log warnings but don't prevent startup
- Includes routers for: auth, projects, documents, categories, search, chat, export, artifacts, usage, crawl, workflows, insights, subscriptions, api_keys, youtube, analytics
- Health check endpoint: `/health`
- API docs: `/docs` (Swagger UI), `/redoc` (ReDoc)

### Frontend Architecture

**Component-Based React** with TypeScript:
- **Pages** (`src/pages/`): Route-level components (Login, Dashboard, Projects, Documents, Search, Chat)
- **Components** (`src/components/`): Reusable UI components
  - **Analytics** (`src/components/analytics/`): TrendChart, ActivityFeed, QualityScoreCard (Phase 1)
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

**Analytics Services** (Phase 1 - Completed):
- `activity_tracker.py`: Event recording with 20+ event types (DOCUMENT_UPLOADED, SEARCH_PERFORMED, etc.)
- `analytics_service.py`: Metrics aggregation, quality scoring, trend analysis

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
- Test discovery patterns: `test_*.py` files, `Test*` classes, `test_*` functions
- Test structure:
  - `tests/e2e/`: End-to-end workflow tests (100% passing, 5 test suites, 38 steps)
    - Complete RAG workflow (upload → vectorize → search → chat)
    - Category management workflow
    - AI insights workflow
    - Multi-user access control
    - Error recovery workflow
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
- Run specific test function: `pytest tests/api/test_documents.py::TestDocumentUpload::test_upload_pdf -v`

**Frontend**:
- ESLint for code quality (`npm run lint`)
- TypeScript compilation check (`tsc -b`)
- Vite build verification (`npm run build`)
- Preview production build (`npm run preview`)
- Hot module replacement (HMR) in development mode for instant updates

### AI/ML Services Initialization

The backend automatically initializes AI/ML services on startup via the `lifespan` context manager in `main.py` (lines 25-58):

1. **BM25 Index** (`bm25_service.py`):
   - Initializes sparse retrieval index from existing database chunks
   - Used for keyword-based search in hybrid search pipeline
   - Initialization: Loads all chunks from database and builds BM25 index
   - Error handling: Logs warning and continues if initialization fails

2. **Cross-Encoder** (`cross_encoder_service.py`):
   - Loads reranking model for relevance scoring
   - Used in TIER 1 RAG pipeline (Phase 3 - Reranking)
   - Initialization: Downloads and loads model on first startup
   - Error handling: Logs warning and continues if initialization fails

**Important**: Both services use graceful degradation - if initialization fails, the backend starts normally but those features won't be available. Check startup logs for initialization status.

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

**Sprint 0-8**: Foundation through Advanced Features COMPLETED
**Completed**: Projects API, Category API, Document API, RAG pipeline, Search, Export, Chat, Workflows, Insights, Subscriptions
**Active Features**: All core features implemented through Sprint 8

**Sprint 9-11**: 3 Strategic Enhancements (9-11 weeks)
- **Phase 1**: Dashboard & Analytics ✅ **COMPLETED** (Week 1, 7 days)
- **Phase 2**: Content Workbench 🔄 **IN PROGRESS** (Weeks 2-5)
  - **Sprint 2A**: Backend Infrastructure ✅ **COMPLETED** (Week 2, Day 1)
  - **Sprint 2B**: Frontend Components ⏳ **PLANNED** (Week 2-3)
- **Phase 3**: Knowledge Graph Visualization ⏳ **PLANNED** (Weeks 6-9)

See root directory status reports for detailed progress.

---

## PLANNED ENHANCEMENTS (Sprint 9-11)

### Overview

Three strategic enhancements to transform KnowledgeTree from passive knowledge repository into active content creation and exploration platform:

1. **Dashboard & Analytics** - Strategic command center with real-time insights
2. **Content Workbench** - Transform passive reader into active content creator
3. **Knowledge Graph** - Visualize hidden connections and entity relationships

**Total Implementation Timeline**: 43-52 days (9-11 weeks)
**Implementation Order**: Phase 1 → Phase 2 → Phase 3 (sequential)

---

### Phase 1: Dashboard & Analytics ✅ COMPLETED

**Timeline**: 14-16 days (3 weeks) - **ACTUAL: 7 days**
**Risk Level**: LOW
**Status**: ✅ **PRODUCTION READY**
**Value**: Foundation for visibility and data-driven decisions
**Completion Date**: 2026-02-02

#### New Database Tables

```sql
CREATE TABLE activity_events (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  project_id INTEGER REFERENCES projects(id),
  event_type VARCHAR(100) NOT NULL,
  event_data JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE daily_metrics (
  id SERIAL PRIMARY KEY,
  project_id INTEGER REFERENCES projects(id),
  metric_date DATE NOT NULL,
  documents_uploaded INTEGER DEFAULT 0,
  searches_performed INTEGER DEFAULT 0,
  chat_messages_sent INTEGER DEFAULT 0,
  insights_generated INTEGER DEFAULT 0,
  active_users INTEGER DEFAULT 0,
  UNIQUE(project_id, metric_date)
);
```

#### Implemented Backend Components ✅

**Models** (`backend/models/activity.py` - 85 lines):
- `ActivityEvent`: Track all user actions and system events (JSONB event_data)
- `DailyMetric`: Aggregated daily statistics with upsert support
- Relationships: CASCADE delete with users and projects

**Services** (`backend/services/`):
- `activity_tracker.py` (193 lines): Event recording with 20+ event types
  - `EventType` enum: DOCUMENT_UPLOADED, SEARCH_PERFORMED, CHAT_MESSAGE_SENT, etc.
  - Generic `record_event()` + 4 convenience methods
  - Supports project_id optional for global events
- `analytics_service.py` (419 lines): Analytics calculations
  - `aggregate_daily_metrics()`: Idempotent daily aggregation with ON CONFLICT DO UPDATE
  - `get_metrics_for_period()`: Time-series data for charts
  - `get_recent_activity()`: Activity feed with pagination
  - `calculate_quality_score()`: 4-component quality score (0-100)
    - Document score (25%): 1+ docs/day = 100
    - Search score (25%): 5+ searches/day = 100
    - Chat score (25%): 3+ messages/day = 100
    - Diversity score (25%): 10+ documents = 100
  - `get_activity_trends()`: Period-over-period percentage changes

**API Router** (`backend/api/routes/analytics.py`):
- `GET /api/v1/analytics/metrics/{project_id}` - Daily metrics with days parameter
- `GET /api/v1/analytics/activity/{project_id}` - Activity feed with limit/offset
- `GET /api/v1/analytics/quality-score/{project_id}` - Quality score calculation
- `GET /api/v1/analytics/trends/{project_id}` - Trend analysis with percentage changes

**Schemas** (`backend/schemas/analytics.py`):
- `DailyMetric`: date, documents_uploaded, searches_performed, chat_messages_sent, insights_generated, active_users
- `ActivityEventResponse`: id, user_id, event_type, event_data, created_at
- `QualityScoreResponse`: overall_score, component scores, period_days, metrics
- `TrendDataResponse`: current, previous, change_percent for each metric

#### Implemented Frontend Components ✅

**Dependencies** (Installed):
```bash
npm install recharts  # Charts and visualizations - INSTALLED
```

**Components** (`frontend/src/components/analytics/`):
- `TrendChart.tsx` (168 lines): Time-series line chart with recharts
  - 4 configurable metrics: documents, searches, messages, insights
  - Custom tooltip with Polish translations
  - Responsive design with CartesianGrid
  - Color-coded lines: blue (docs), green (searches), amber (messages), violet (insights)
- `ActivityFeed.tsx`: Real-time activity stream
  - Activity icons per event type
  - Relative timestamps
  - Polish translations for all event types
  - Responsive card layout
- `QualityScoreCard.tsx`: Quality score display
  - Overall score (0-100) with color-coded indicator
  - 4 component progress bars with percentages
  - Responsive grid layout
  - Polish labels and descriptions

**Pages**:
- `DashboardPage.tsx`: Enhanced with analytics integration
  - Fetches analytics data from all 4 endpoints
  - Displays TrendChart with 30-day metrics
  - Shows ActivityFeed with recent events
  - Displays QualityScoreCard with current score
  - Responsive 2-column grid layout

#### Integration Points ✅

Activity tracking integrated in existing routes:
- `backend/api/routes/documents.py` - Tracks document uploads (DOCUMENT_UPLOADED)
- `backend/api/routes/search.py` - Tracks searches (SEARCH_PERFORMED)
- `backend/api/routes/chat.py` - Tracks chat messages (CHAT_MESSAGE_SENT)
- All events include project_id, user_id, and event-specific metadata in JSONB

#### Testing ✅

**Unit Tests** (`tests/services/test_activity_tracker.py` - 288 lines):
- 10 comprehensive test cases for ActivityTracker service
- Tests: basic events, project-less events, all convenience methods, JSONB storage, CASCADE deletes
- Manual verification: All event recording functionality confirmed working

**API Tests** (`tests/api/test_analytics.py`):
- 15 integration tests across 5 test classes
- Coverage: all 4 endpoints, success cases, edge cases, pagination, authorization, access control
- Test classes: TestAnalyticsMetricsEndpoint, TestAnalyticsActivityEndpoint, TestAnalyticsQualityScoreEndpoint, TestAnalyticsTrendsEndpoint, TestAnalyticsAccessControl

**Database Schema**:
- Migration applied successfully: `alembic upgrade head`
- Verified: unique constraint `uq_project_metric_date` on (project_id, metric_date)
- Verified: proper CASCADE relationships and indexes

**Production Verification**:
- Manual integration test completed successfully
- All 3 event types (document upload, search, chat) recorded correctly
- Analytics calculations verified (aggregation, quality score, trends)

---

### Phase 2: Content Workbench

**Timeline**: 14-18 days (3-4 weeks) | **Actual Sprint 2A**: 1 day
**Risk Level**: MEDIUM
**Value**: HIGH - Transform from passive reader to active creator
**Status**: Sprint 2A (Backend) ✅ COMPLETED | Sprint 2B (Frontend) ⏳ PLANNED

#### New Database Tables

```sql
-- Add to categories table
ALTER TABLE categories
  ADD COLUMN draft_content TEXT,
  ADD COLUMN published_content TEXT,
  ADD COLUMN content_status VARCHAR(20) DEFAULT 'draft',
  ADD COLUMN published_at TIMESTAMP,
  ADD COLUMN reviewed_by INTEGER REFERENCES users(id),
  ADD COLUMN reviewed_at TIMESTAMP;

CREATE TABLE content_versions (
  id SERIAL PRIMARY KEY,
  category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  version_number INTEGER NOT NULL,
  created_by INTEGER REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW(),
  change_summary VARCHAR(500),
  UNIQUE(category_id, version_number)
);

CREATE TABLE extracted_quotes (
  id SERIAL PRIMARY KEY,
  category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
  quote_text TEXT NOT NULL,
  context_before TEXT,
  context_after TEXT,
  quote_type VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE content_templates (
  id SERIAL PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  description TEXT,
  template_type VARCHAR(50) NOT NULL,
  structure JSONB NOT NULL,
  is_public BOOLEAN DEFAULT true,
  created_by INTEGER REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### Sprint 2A: Backend Infrastructure ✅ COMPLETED

**Database Migration** (`backend/alembic/versions/bfa51eeeeb8c_*.py`):
- ✅ Extended `categories` table with 6 Content Workbench columns
- ✅ Created `content_versions` table (version history with unique constraint)
- ✅ Created `extracted_quotes` table (AI-extracted quotes with context)
- ✅ Created `content_templates` table (JSONB structure for templates)
- ✅ Applied migration successfully (`alembic upgrade head`)

**Models** (`backend/models/content.py` - 180 lines):
- ✅ `ContentVersion`: Version history with auto-incrementing version_number, unique constraint on (category_id, version_number)
- ✅ `ExtractedQuote`: Key quotes with context_before/after and quote_type classification
- ✅ `ContentTemplate`: Reusable templates with JSONB structure field

**Category Model Extensions** (`backend/models/category.py`):
- ✅ Added 6 workflow fields: draft_content, published_content, content_status, published_at, reviewed_by, reviewed_at
- ✅ Added 3 relationships: reviewer, content_versions, extracted_quotes

**Services** (`backend/services/` - ~950 lines total):
- ✅ `content_editor_service.py` (450 lines) - 9 methods:
  - save_draft() - Save draft with auto-versioning
  - publish() - Publish draft to published_content
  - unpublish() - Revert to draft status
  - get_versions() - Fetch version history (paginated)
  - get_version_count() - Count total versions
  - get_version() - Get specific version by number
  - restore_version() - Restore from historical version
  - compare_versions() - Compare two versions for diff
  - _create_version() - Internal version creation with auto-increment

- ✅ `content_rewriter_service.py` (500 lines) - 6 AI operations (OpenAI GPT-4o-mini):
  - summarize() - Create concise summaries with optional focus
  - expand() - Add detail and context with target length
  - simplify() - Adjust reading level (basic/general/advanced)
  - rewrite_tone() - Change tone (professional/casual/technical/friendly/formal/conversational)
  - extract_quotes() - AI-powered quote extraction with context (saves to DB)
  - generate_outline() - Generate content outline for topics

**Exception Handling** (`backend/core/exceptions.py` - 80 lines):
- ✅ `NotFoundException` (HTTP 404)
- ✅ `ValidationException` (HTTP 400)
- ✅ `UnauthorizedException` (HTTP 401)
- ✅ `ForbiddenException` (HTTP 403)
- ✅ `ConflictException` (HTTP 409)
- ✅ `ServiceUnavailableException` (HTTP 503)

**API Router** (`backend/api/routes/content.py` - 650 lines) - **18 endpoints**:

*Content Editor (3):*
- ✅ `POST /api/v1/content/categories/{id}/draft` - Save draft with versioning
- ✅ `POST /api/v1/content/categories/{id}/publish` - Publish content
- ✅ `POST /api/v1/content/categories/{id}/unpublish` - Unpublish to draft

*Version Management (5):*
- ✅ `GET /api/v1/content/categories/{id}/versions` - List versions (paginated)
- ✅ `GET /api/v1/content/categories/{id}/versions/{version_number}` - Get specific version
- ✅ `POST /api/v1/content/categories/{id}/versions/restore` - Restore version
- ✅ `POST /api/v1/content/categories/{id}/versions/compare` - Compare versions

*AI Operations (7):*
- ✅ `POST /api/v1/content/ai/summarize` - Summarize content
- ✅ `POST /api/v1/content/ai/expand` - Expand content
- ✅ `POST /api/v1/content/ai/simplify` - Simplify reading level
- ✅ `POST /api/v1/content/ai/rewrite-tone` - Change tone/style
- ✅ `POST /api/v1/content/categories/{id}/extract-quotes` - Extract quotes (AI)
- ✅ `GET /api/v1/content/categories/{id}/quotes` - Get saved quotes
- ✅ `POST /api/v1/content/ai/generate-outline` - Generate outline

*Template Management (3):*
- ✅ `POST /api/v1/content/templates` - Create template
- ✅ `GET /api/v1/content/templates` - List templates (filter by type)
- ✅ `GET /api/v1/content/templates/{id}` - Get template details

**Schemas** (`backend/schemas/content.py` - 550 lines) - **20+ schemas**:
- ✅ 5 Enums: ContentStatus, ToneType, ReadingLevel, QuoteType, TemplateType
- ✅ Response: ContentVersionResponse, ExtractedQuoteResponse, ContentTemplateResponse, AIOperationResponse, VersionComparisonResponse
- ✅ Request: SaveDraftRequest, PublishContentRequest, RestoreVersionRequest, CompareVersionsRequest, SummarizeRequest, ExpandRequest, SimplifyRequest, RewriteToneRequest, ExtractQuotesRequest, GenerateOutlineRequest, ContentTemplateCreate

**Updated Schemas** (`backend/schemas/category.py`):
- ✅ Extended CategoryResponse with 6 Content Workbench fields

**Testing** (`/tmp/test_content_workbench.sh` - comprehensive test suite):
- ✅ **19/19 tests passed** (100% success rate)
- ✅ Authentication & Authorization (JWT)
- ✅ Content Editor operations (save draft, publish, unpublish)
- ✅ Version management (list, get, compare, restore)
- ✅ AI operations (summarize, expand, simplify, rewrite, extract, outline)
- ✅ Template management (create, list, get, filter)
- ✅ Access control verification (user ownership)
- ✅ Database constraints validation (unique version numbers)

**Integration**:
- ✅ Registered router in `main.py`
- ✅ Backend restart successful
- ✅ All endpoints accessible via OpenAPI docs (`/docs`)

#### Sprint 2B: Frontend Components ⏳ PLANNED

#### New Frontend Components

**Dependencies**:
```bash
npm install @tiptap/react @tiptap/starter-kit @tiptap/extension-markdown
npm install @tiptap/extension-link @tiptap/extension-image
```

**Components** (`frontend/src/components/content/`):
- `ContentEditor.tsx` - Rich text editor (TipTap) with auto-save
- `EditorToolbar.tsx` - Formatting controls
- `RewriteDialog.tsx` - AI rewriting interface
- `QuoteExtractor.tsx` - Quote extraction UI
- `VersionHistory.tsx` - Version list & restore
- `PublishingPanel.tsx` - Draft/Review/Publish workflow
- `TemplateSelector.tsx` - Template picker
- `TemplateEditor.tsx` - Template-based editing

**Pages**:
- New `ContentWorkbenchPage.tsx` - Main editing interface

**Route**:
- Add route `/content/:categoryId` to `App.tsx`

#### AI Integration

Uses Claude API for:
- Content summarization
- Content expansion
- Language simplification
- Tone adjustment
- Quote extraction

#### Testing

- Unit tests: `tests/services/test_content_editor.py`, `test_content_rewriter.py`
- API tests: `tests/api/test_content.py`
- E2E tests: Draft → Edit → AI rewrite → Publish workflow

---

### Phase 3: Knowledge Graph Visualization

**Timeline**: 15-18 days (3-4 weeks)
**Risk Level**: HIGH (performance at scale)
**Value**: MEDIUM-HIGH - Discover hidden connections

#### New Database Tables

```sql
CREATE TABLE entities (
  id SERIAL PRIMARY KEY,
  name VARCHAR(500) NOT NULL,
  entity_type VARCHAR(100) NOT NULL,
  project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
  first_seen_document_id INTEGER REFERENCES documents(id),
  occurrence_count INTEGER DEFAULT 1,
  description TEXT,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE entity_relationships (
  id SERIAL PRIMARY KEY,
  from_entity_id INTEGER REFERENCES entities(id) ON DELETE CASCADE,
  to_entity_id INTEGER REFERENCES entities(id) ON DELETE CASCADE,
  relationship_type VARCHAR(100) NOT NULL,
  strength FLOAT DEFAULT 0.5,
  document_ids INTEGER[],
  first_seen_at TIMESTAMP DEFAULT NOW(),
  last_seen_at TIMESTAMP DEFAULT NOW(),
  occurrence_count INTEGER DEFAULT 1,
  UNIQUE(from_entity_id, to_entity_id, relationship_type)
);

CREATE VIEW entity_connections AS
  SELECT from_entity_id AS entity_id, to_entity_id AS connected_to,
         relationship_type, strength, 'outgoing' AS direction
  FROM entity_relationships
  UNION ALL
  SELECT to_entity_id AS entity_id, from_entity_id AS connected_to,
         relationship_type, strength, 'incoming' AS direction
  FROM entity_relationships;
```

#### New Backend Components

**Models** (`backend/models/graph.py`):
- `Entity`: Knowledge graph nodes
- `EntityRelationship`: Graph edges with strength

**Services** (`backend/services/`):
- `entity_migrator.py`: Migrate [ENTITY] chunks to entities table
- `graph_builder.py`: Build relationships, clustering, pathfinding

**API Router** (`backend/api/routes/graph.py`):
- `POST /graph/projects/{id}/build` - Build knowledge graph
- `GET /graph/projects/{id}/entities` - List entities
- `GET /graph/projects/{id}/relationships` - List relationships
- `GET /graph/entities/{id}` - Entity details with connections
- `GET /graph/path/{from_id}/{to_id}` - Find shortest path
- `GET /graph/projects/{id}/clusters` - Entity clusters

**Schemas** (`backend/schemas/graph.py`):
- `EntityResponse`
- `RelationshipResponse`
- `EntityDetailsResponse`
- `GraphStatsResponse`

#### Graph Algorithms

Implemented in `graph_builder.py`:
- **Co-occurrence Analysis**: Build relationships from entity co-occurrence in documents
- **Relationship Strength**: Calculate based on frequency (0.0-1.0 scale)
- **Connected Components**: DFS-based clustering with strength threshold
- **Shortest Path**: BFS pathfinding between entities
- **Entity Ranking**: By occurrence count

#### New Frontend Components

**Dependencies**:
```bash
npm install reactflow  # Graph visualization
npm install dagre      # Automatic graph layout
```

**Components** (`frontend/src/components/graph/`):
- `KnowledgeGraph.tsx` - Main graph visualization (React Flow)
- `EntityNode.tsx` - Custom node component
- `RelationshipEdge.tsx` - Custom edge component
- `GraphControls.tsx` - Zoom, filter, layout controls
- `EntityDetailsPanel.tsx` - Selected entity sidebar
- `PathFinder.tsx` - Find path between entities
- `ClusterView.tsx` - Cluster visualization

**Pages**:
- New `KnowledgeGraphPage.tsx` - Interactive graph explorer

**Route**:
- Add route `/graph` to `App.tsx`

#### Visualization Features

- **Interactive**: Click, zoom, pan
- **Force-directed layout**: Automatic positioning via dagre
- **Entity filtering**: By type (product, organization, concept, etc.)
- **Relationship filtering**: By strength threshold
- **Path finding**: Highlight shortest path between nodes
- **Entity search**: Find by name
- **Export**: Save graph as image/JSON

#### Performance Considerations

**Optimization Strategies**:
- Pagination for large graphs (limit to top N entities)
- Server-side clustering pre-calculation
- React Flow virtualization
- Progressive rendering with loading states
- Layout caching

**Scalability Limits**:
- Recommended: <1000 entities, <5000 relationships per view
- Above limits: Use filtering and pagination

#### Testing

- Unit tests: `tests/services/test_graph_builder.py` (algorithms)
- API tests: `tests/api/test_graph.py`
- E2E tests: Build graph → Explore → Find path workflow
- Performance tests: Large project graph building

---

### Feature Flags

New feature flags in `backend/core/config.py`:

```python
class Settings:
    # Phase 1
    FEATURE_ACTIVITY_TRACKING: bool = True

    # Phase 2
    FEATURE_CONTENT_WORKBENCH: bool = True
    FEATURE_AI_REWRITING: bool = True

    # Phase 3
    FEATURE_KNOWLEDGE_GRAPH: bool = True
```

### Deployment Strategy

**Phased Rollout**:
1. Phase 1: Low risk, deploy to production immediately
2. Phase 2: Medium risk, beta testing with select users first
3. Phase 3: High risk, opt-in rollout with performance monitoring

**Monitoring**:
- Track API endpoint performance (p50, p95, p99)
- Monitor database query times
- Alert on error rates >1%
- Track user adoption metrics

### Success Metrics

**Phase 1 (Dashboard)**:
- Daily dashboard views: >50% of active users
- Average time on dashboard: >2 minutes
- Activity feed engagement: >30% click-through

**Phase 2 (Content Workbench)**:
- Published content: >10 per week
- AI rewrite usage: >20% of edits
- Version restore rate: <5%

**Phase 3 (Knowledge Graph)**:
- Graph views: >5 per project per week
- Entity click-through: >40%
- Path finding usage: >10 per week

### Migration Notes

**Database Migrations**:
- 3 separate migration files (one per phase)
- Test on database copy before production
- Implement rollback procedures
- Run during low-traffic periods

**Data Migration**:
- Phase 3 requires migrating existing [ENTITY] chunks to entities table
- Run `entity_migrator.py` after schema migration
- Monitor for data consistency

### Risk Mitigation

**Technical Risks**:
1. **Rich Text Editor Complexity**: Start with basic TipTap, add features incrementally
2. **Graph Performance**: Implement pagination, caching, progressive rendering
3. **AI API Rate Limits**: Queue requests, add usage warnings, implement daily limits
4. **Activity Tracking Performance**: Use background tasks, batch inserts, partition by date

**Project Risks**:
1. **Scope Creep**: Strict adherence to defined scope, document future requests
2. **Timeline Delays**: Buffer time built into estimates (43-52 days range)
3. **Integration Challenges**: Comprehensive tests, code reviews, feature flags
