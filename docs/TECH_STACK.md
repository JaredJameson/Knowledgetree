# Technical Stack Specification
## KnowledgeTree Platform

**Version**: 1.0
**Date**: January 19, 2026
**Status**: Architecture Definition

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Frontend Stack](#frontend-stack)
3. [Backend Stack](#backend-stack)
4. [Database & Vector Storage](#database--vector-storage)
5. [AI & ML Services](#ai--ml-services)
6. [External Integrations](#external-integrations)
7. [Infrastructure & DevOps](#infrastructure--devops)
8. [Development Tools](#development-tools)
9. [Integration Architecture](#integration-architecture)
10. [Deployment Strategy](#deployment-strategy)

---

## Architecture Overview

### System Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────────────┐
│                            User Interface Layer                             │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                     React 19 Frontend (SPA)                          │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐   │  │
│  │  │ Category Tree  │  │   RAG Chat     │  │  Search Interface  │   │  │
│  │  │   Editor       │  │   Interface    │  │   (Semantic)       │   │  │
│  │  └────────────────┘  └────────────────┘  └────────────────────┘   │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐   │  │
│  │  │ PDF Upload     │  │  Web Crawler   │  │  Insights          │   │  │
│  │  │ (Drag&Drop)    │  │  Config        │  │  Dashboard         │   │  │
│  │  └────────────────┘  └────────────────┘  └────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
│                                    ↓ REST API + SSE                         │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    FastAPI API Gateway (Python)                      │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐   │  │
│  │  │ Auth Middleware│  │ Rate Limiting  │  │  CORS Handler      │   │  │
│  │  └────────────────┘  └────────────────┘  └────────────────────┘   │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐   │  │
│  │  │ Project Router │  │ Document Router│  │  Search Router     │   │  │
│  │  └────────────────┘  └────────────────┘  └────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
└────────────────────────────────────┼─────────────────────────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ↓                ↓                ↓
    ┌────────────────────┐  ┌────────────────┐  ┌─────────────────┐
    │  RAG-CREATOR API   │  │  Agent Engine  │  │  External APIs  │
    │  (Microservice)    │  │  (Orchestrator)│  │                 │
    ├────────────────────┤  ├────────────────┤  ├─────────────────┤
    │ • PDF Processing   │  │ • Claude API   │  │ • Firecrawl API │
    │ • Text Extraction  │  │ • Web Search   │  │ • WebSearch API │
    │ • Chunking         │  │ • Workflows    │  │ • OAuth Providers│
    │ • BGE-M3 Embedding │  │ • Task Queue   │  │                 │
    │ • Vector Storage   │  │ • State Mgmt   │  │                 │
    └────────┬───────────┘  └────────┬───────┘  └─────────────────┘
             │                       │
             └───────────┬───────────┘
                         ↓
        ┌──────────────────────────────────────┐
        │   PostgreSQL 16 + pgvector 0.7       │
        ├──────────────────────────────────────┤
        │ • Projects (multi-tenant)            │
        │ • Categories (hierarchical tree)     │
        │ • Documents (PDFs, web pages)        │
        │ • Chunks (text + embeddings)         │
        │ • Users & Authentication             │
        │ • Agent Workflows (state)            │
        │ • IVFFlat Vector Indexes             │
        └──────────────────────────────────────┘
                         ↓
        ┌──────────────────────────────────────┐
        │        File Storage (S3/Local)       │
        ├──────────────────────────────────────┤
        │ • Uploaded PDFs                      │
        │ • Extracted text files               │
        │ • Crawled HTML pages                 │
        │ • Export files (JSON, CSV)           │
        └──────────────────────────────────────┘
```

### Architecture Principles

1. **Microservices**: RAG-CREATOR as separate service, API gateway for routing
2. **Shared Database**: PostgreSQL with schema isolation per service
3. **Async Processing**: Background tasks for long-running operations (crawling, embedding)
4. **Event-Driven**: SSE for real-time progress updates to frontend
5. **Stateless API**: JWT authentication, no server-side sessions
6. **Horizontal Scalability**: Stateless services can scale independently

---

## Frontend Stack

### Core Framework

**React 19.0.0**
- **Why**: Latest React with concurrent features, Server Components support (future)
- **Build Tool**: Vite 6.0+ (fast HMR, optimized builds)
- **Language**: TypeScript 5.3+
- **Styling**: TailwindCSS 3.4+ (utility-first)

### UI Component Library & Design System

**shadcn/ui**
- **Components**: 40+ pre-built components (Button, Input, Dialog, Tree, etc.)
- **Why**: Unstyled primitives with Radix UI, fully customizable, no runtime JS overhead
- **Theme**: CVA (class-variance-authority) for component variants
- **Icons**: lucide-react (professional SVG icons, 1000+ options)

**Design Principles**:
- **No Emojis**: Professional, business-focused UI without emoji decorations
- **Pastel Colors**: Soft, modern color palette with high readability
- **Dark/Light Mode**: Full theme support with system preference detection
- **Typography**: Inter font family (same as Notion) for consistency and readability
- **Animations**: Smooth, purposeful micro-interactions using Framer Motion
- **Modern Design**: Clean, spacious layouts with subtle shadows and blur effects

**Language Support**:
- **Primary Language**: Polish (default UI)
- **Secondary Language**: English (switchable)
- **Implementation**: react-i18next for internationalization

### State Management

**React Context + useReducer** (inherited from Genetico)
- **Why**: Sufficient for current needs, no additional dependencies
- **Pattern**: Single EditorContext with reducer for all state mutations
- **Migration Path**: If complexity grows → Zustand or Jotai (lightweight)

**State Structure**:
```typescript
interface AppState {
  // Project state
  currentProject: Project | null;
  projects: Project[];

  // Category tree state (from Genetico)
  categories: Category[];
  selectedCategoryId: string | null;
  expandedIds: Set<string>;

  // Document state
  documents: Document[];
  chunks: Chunk[];

  // UI state
  searchQuery: string;
  isModified: boolean;

  // History (undo/redo)
  history: {
    past: Category[][];
    present: Category[];
    future: Category[][];
  };
}
```

### Additional Frontend Libraries

**Drag & Drop**:
- `@dnd-kit/core` + `@dnd-kit/sortable` (from Genetico)
- Reorder categories, assign documents to categories

**File Upload**:
- `react-dropzone` - Drag-and-drop file uploads with progress

**Real-time Updates**:
- Native `EventSource` API for SSE (Server-Sent Events)
- Custom React hook: `useSSE(url)` for progress streaming

**Data Visualization**:
- `recharts` - Charts for insights dashboard (competitive matrix, trends)
- Alternative: `chart.js` if more control needed

**Animations & Motion**:
- `framer-motion` - Production-ready motion library for React
- Smooth page transitions, micro-interactions, loading states
- Spring physics for natural feel

**Internationalization**:
- `react-i18next` - i18n framework for React
- `i18next` - Core i18n library
- `i18next-browser-languagedetector` - Auto-detect user language
- Namespace-based translations (common, editor, search, etc.)

**Rich Text Editor** (Future):
- `@tiptap/react` - For editing notes, rationales, descriptions
- Markdown support with WYSIWYG

**Date/Time**:
- `date-fns` - Lightweight date manipulation (smaller than moment.js)
- `date-fns/locale/pl` - Polish locale for date formatting

### Frontend Architecture Patterns

**Directory Structure**:
```
frontend/src/
├── app/                    # Next.js App Router (future migration)
├── components/
│   ├── editor/             # Category tree editor (from Genetico)
│   │   ├── CategoryTree.tsx
│   │   ├── CategoryNode.tsx
│   │   ├── CategoryForm.tsx
│   │   └── StatisticsPanel.tsx
│   ├── knowledge/          # New: Knowledge base features
│   │   ├── DocumentUpload.tsx
│   │   ├── DocumentList.tsx
│   │   ├── SearchInterface.tsx
│   │   ├── SearchResults.tsx
│   │   └── VectorVisualization.tsx
│   ├── rag/                # New: RAG chat features
│   │   ├── ChatInterface.tsx
│   │   ├── MessageList.tsx
│   │   ├── SourceCitations.tsx
│   │   └── ConversationHistory.tsx
│   ├── crawler/            # New: Web crawling features
│   │   ├── CrawlerConfig.tsx
│   │   ├── CrawlProgress.tsx
│   │   ├── PagePreview.tsx
│   │   └── ScheduleManager.tsx
│   ├── insights/           # New: AI insights
│   │   ├── CompetitiveMatrix.tsx
│   │   ├── TrendAnalysis.tsx
│   │   ├── InsightsDashboard.tsx
│   │   └── ReportExport.tsx
│   └── ui/                 # shadcn/ui primitives
├── context/
│   ├── EditorContext.tsx   # From Genetico
│   ├── ProjectContext.tsx  # New: Multi-project management
│   ├── AuthContext.tsx     # New: User authentication
│   └── ThemeContext.tsx    # New: Dark mode support
├── hooks/
│   ├── useCategories.ts    # From Genetico
│   ├── useSearch.ts        # New: Vector search
│   ├── useRAGChat.ts       # New: RAG conversations
│   ├── useSSE.ts           # New: Server-Sent Events
│   └── useCrawler.ts       # New: Web crawling status
├── lib/
│   └── utils.ts            # Utility functions (cn, etc.)
├── services/
│   ├── api.ts              # API client (Axios instance)
│   ├── auth.ts             # Authentication
│   ├── projects.ts         # Project CRUD
│   ├── documents.ts        # Document operations
│   ├── search.ts           # Vector search
│   └── crawler.ts          # Firecrawl integration
├── types/
│   ├── editor.ts           # From Genetico (Category, etc.)
│   ├── rag.ts              # New: RAG types
│   ├── api.ts              # API response types
│   └── index.ts            # Re-exports
├── utils/
│   ├── treeUtils.ts        # From Genetico (tree operations)
│   ├── exportUtils.ts      # From Genetico (export functions)
│   ├── vectorUtils.ts      # New: Vector operations
│   └── dateUtils.ts        # New: Date formatting
└── main.tsx                # Entry point
```

---

## Backend Stack

### Core Framework

**FastAPI 0.109.0+**
- **Why**: High performance, async/await native, automatic OpenAPI docs, Pydantic validation
- **ASGI Server**: Uvicorn with `--reload` (dev), Gunicorn workers (prod)
- **Python Version**: 3.11+ (performance improvements)

### Backend Architecture

**API Gateway Pattern**:
- Single FastAPI instance as entry point
- Routes requests to:
  - RAG-CREATOR microservice (PDF processing)
  - Agent Engine (orchestration)
  - Direct database queries (search, CRUD)

**Microservice Communication**:
- HTTP REST between services (simple, debuggable)
- Shared PostgreSQL database (schema isolation)
- Background tasks via FastAPI `BackgroundTasks`

### Backend Libraries

**Web Framework**:
- `fastapi[standard]` - Core framework with extras
- `uvicorn[standard]` - ASGI server with WebSockets support
- `python-multipart` - File upload support
- `python-jose[cryptography]` - JWT token handling
- `passlib[bcrypt]` - Password hashing

**Database**:
- `sqlalchemy>=2.0.25` - ORM with async support
- `asyncpg>=0.29.0` - Async PostgreSQL driver
- `psycopg2-binary>=2.9.9` - Sync driver (for migrations)
- `pgvector>=0.2.4` - PostgreSQL vector extension support
- `alembic>=1.13.0` - Database migrations

**PDF Processing** (from RAG-CREATOR):
- `PyMuPDF>=1.23.0` - PDF text extraction (fallback)
- `docling>=2.0.0` - Structure-preserving PDF extraction (primary)

**Embeddings** (from RAG-CREATOR):
- `FlagEmbedding>=1.2.0` - BGE-M3 model wrapper
- `torch>=2.0.0` - PyTorch for model inference
- `sentence-transformers>=2.2.0` - Additional embedding utilities

**Configuration**:
- `pydantic>=2.6.0` - Settings validation
- `pydantic-settings>=2.1.0` - Environment variable loading
- `python-dotenv>=1.0.0` - .env file support

**Utilities**:
- `aiofiles>=23.2.1` - Async file operations
- `httpx>=0.26.0` - Async HTTP client (for external APIs)
- `python-dateutil>=2.8.2` - Date parsing
- `celery>=5.3.0` - Task queue (if needed for complex workflows)
- `redis>=5.0.0` - Celery broker + caching

### Backend Directory Structure

```
backend/
├── main.py                 # FastAPI app entry, CORS, lifespan
├── api/
│   ├── __init__.py
│   ├── routes/
│   │   ├── auth.py         # Authentication endpoints
│   │   ├── projects.py     # Project CRUD
│   │   ├── categories.py   # Category tree operations
│   │   ├── documents.py    # Document upload/management
│   │   ├── search.py       # Vector search
│   │   ├── crawler.py      # Web crawling
│   │   ├── insights.py     # AI-powered insights
│   │   ├── chat.py         # RAG chat interface
│   │   └── export.py       # Export functionality
│   └── dependencies.py     # FastAPI dependencies (auth, db)
├── core/
│   ├── __init__.py
│   ├── config.py           # Pydantic settings
│   ├── database.py         # SQLAlchemy engine, session
│   ├── security.py         # JWT, password hashing
│   └── constants.py        # Application constants
├── models/
│   ├── __init__.py
│   ├── user.py             # User model
│   ├── project.py          # Project model
│   ├── category.py         # Category model (from Genetico)
│   ├── document.py         # Document model
│   ├── chunk.py            # Chunk model with embedding
│   ├── conversation.py     # RAG chat conversations
│   └── workflow.py         # Agent workflow definitions
├── schemas/
│   ├── __init__.py
│   ├── auth.py             # Auth request/response schemas
│   ├── project.py          # Project schemas
│   ├── category.py         # Category schemas
│   ├── document.py         # Document schemas
│   ├── search.py           # Search request/response
│   └── chat.py             # Chat message schemas
├── services/
│   ├── __init__.py
│   ├── rag_creator/        # RAG-CREATOR integration (copied)
│   │   ├── pipeline.py     # Vectorization pipeline
│   │   ├── pdf_splitter.py
│   │   ├── text_extractor.py
│   │   ├── chunker.py
│   │   ├── embedder.py     # BGE-M3 embeddings
│   │   └── progress_manager.py
│   ├── crawler_service.py  # Firecrawl API wrapper
│   ├── search_service.py   # Vector similarity search
│   ├── agent_service.py    # Agent orchestration
│   ├── llm_service.py      # Claude API wrapper
│   ├── insight_service.py  # AI insights generation
│   └── export_service.py   # Export formats
├── utils/
│   ├── __init__.py
│   ├── vector_ops.py       # Vector operations (cosine similarity)
│   ├── tree_ops.py         # Tree operations (from Genetico)
│   └── text_processing.py  # Text utilities
├── migrations/             # Alembic migrations
│   ├── versions/
│   └── env.py
└── tests/
    ├── __init__.py
    ├── conftest.py         # Pytest fixtures
    ├── test_auth.py
    ├── test_projects.py
    ├── test_search.py
    └── test_pipeline.py
```

### API Design Patterns

**RESTful Conventions**:
- `GET /api/projects` - List projects
- `POST /api/projects` - Create project
- `GET /api/projects/{id}` - Get project details
- `PATCH /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project

**Nested Resources**:
- `POST /api/projects/{id}/documents/upload` - Upload document
- `GET /api/projects/{id}/search` - Search within project
- `GET /api/projects/{id}/categories` - Get category tree

**Real-time Updates**:
- `GET /api/projects/{id}/progress` - SSE stream for processing progress

**Authentication**:
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - Login (returns JWT)
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - Logout (revoke token)

**Rate Limiting**:
- 100 requests/minute per user (general endpoints)
- 10 requests/minute for expensive operations (crawling, insights)
- 429 Too Many Requests response with Retry-After header

---

## Database & Vector Storage

### PostgreSQL 16 + pgvector 0.7

**Why PostgreSQL**:
- Mature, reliable, open-source
- pgvector extension for vector operations
- JSONB support for flexible metadata
- Full-text search (PostgreSQL tsvector)
- Strong ACID guarantees

**Why pgvector**:
- Native vector similarity search in PostgreSQL
- IVFFlat and HNSW indexing for performance
- No additional service required (vs Pinecone, Qdrant)
- Supports up to 16,000 dimensions (enough for all embedding models)
- Cost-effective (no per-query charges)

### Database Schema

**Users Table**:
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    tier VARCHAR(20) DEFAULT 'free', -- free, starter, professional, enterprise
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false
);

CREATE INDEX idx_users_email ON users(email);
```

**Projects Table**:
```sql
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Embedding configuration
    embedding_model VARCHAR(50) DEFAULT 'bge-m3', -- bge-m3, bge-large-en, openai-small, openai-large
    embedding_dimensions INTEGER DEFAULT 1024,

    -- Processing configuration
    chunk_size INTEGER DEFAULT 1000,
    chunk_overlap INTEGER DEFAULT 200,

    -- Status
    status VARCHAR(20) DEFAULT 'active', -- active, archived, processing

    -- Statistics
    document_count INTEGER DEFAULT 0,
    chunk_count INTEGER DEFAULT 0,
    total_size_bytes BIGINT DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_accessed_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_projects_user ON projects(user_id);
CREATE INDEX idx_projects_status ON projects(status);
```

**Categories Table** (from Genetico):
```sql
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    parent_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,

    -- Category data
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Rationale (from Genetico)
    rationale_ux TEXT,
    rationale_seo TEXT,
    rationale_clinical TEXT, -- rename to "rationale_business" for generic use

    -- Visual
    highlight_color VARCHAR(7), -- hex color
    icon VARCHAR(50), -- icon name

    -- Tree metadata
    path VARCHAR(1000), -- materialized path: /1/5/12
    depth INTEGER DEFAULT 0,
    position INTEGER DEFAULT 0, -- sibling order

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_categories_project ON categories(project_id);
CREATE INDEX idx_categories_parent ON categories(parent_id);
CREATE INDEX idx_categories_path ON categories(path); -- for tree queries
```

**Documents Table**:
```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,

    -- Source
    source_type VARCHAR(20) NOT NULL, -- 'pdf', 'web', 'manual'
    source_url TEXT, -- original URL (for web) or file path (for PDF)
    filename VARCHAR(255),

    -- PDF metadata
    page_count INTEGER,
    file_size_bytes BIGINT,

    -- Web metadata
    crawled_at TIMESTAMP,
    last_modified_at TIMESTAMP, -- from HTTP headers

    -- Content
    title VARCHAR(500),
    raw_text TEXT, -- extracted text
    html_content TEXT, -- original HTML (for web)

    -- Processing status
    status VARCHAR(20) DEFAULT 'pending', -- pending, processing, completed, failed
    error_message TEXT,

    -- Statistics
    chunk_count INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_documents_project ON documents(project_id);
CREATE INDEX idx_documents_category ON documents(category_id);
CREATE INDEX idx_documents_source_type ON documents(source_type);
CREATE INDEX idx_documents_status ON documents(status);
```

**Chunks Table** (from RAG-CREATOR):
```sql
CREATE TABLE chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE, -- denormalized for queries
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,

    -- Positioning
    global_index INTEGER NOT NULL, -- index across entire project
    local_index INTEGER NOT NULL, -- index within document

    -- Content
    text TEXT NOT NULL,
    char_count INTEGER,
    char_start INTEGER, -- position in original document
    char_end INTEGER,

    -- Embedding
    embedding vector(1024), -- dimension varies by project.embedding_dimensions
    has_embedding INTEGER DEFAULT 0, -- 1 if embedding exists (for filtering)

    -- Metadata (JSONB for flexibility)
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_chunks_document ON chunks(document_id);
CREATE INDEX idx_chunks_project ON chunks(project_id);
CREATE INDEX idx_chunks_category ON chunks(category_id);
CREATE INDEX idx_chunks_global_index ON chunks(global_index);

-- Vector similarity index (created per-project after embedding)
-- CREATE INDEX idx_chunks_embedding_1024 ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

**Conversations Table** (RAG Chat):
```sql
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,

    title VARCHAR(255), -- auto-generated from first message

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_conversations_project ON conversations(project_id);
CREATE INDEX idx_conversations_user ON conversations(user_id);
```

**Messages Table** (RAG Chat):
```sql
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,

    role VARCHAR(20) NOT NULL, -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,

    -- RAG metadata
    retrieved_chunks JSONB, -- array of chunk IDs used for this response
    tokens_used INTEGER,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id);
```

**Crawl Jobs Table**:
```sql
CREATE TABLE crawl_jobs (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,

    -- Configuration
    start_url TEXT NOT NULL,
    max_pages INTEGER DEFAULT 50,
    max_depth INTEGER DEFAULT 2,
    include_patterns TEXT[], -- URL patterns to include
    exclude_patterns TEXT[], -- URL patterns to exclude
    respect_robots_txt BOOLEAN DEFAULT true,
    enable_js BOOLEAN DEFAULT true,

    -- Schedule
    schedule_type VARCHAR(20), -- 'once', 'daily', 'weekly', 'monthly'
    schedule_cron VARCHAR(50), -- cron expression
    next_run_at TIMESTAMP,

    -- Status
    status VARCHAR(20) DEFAULT 'pending', -- pending, running, completed, failed, cancelled
    progress INTEGER DEFAULT 0, -- 0-100
    pages_crawled INTEGER DEFAULT 0,
    pages_discovered INTEGER DEFAULT 0,
    error_message TEXT,

    -- Firecrawl
    firecrawl_job_id VARCHAR(100),

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_crawl_jobs_project ON crawl_jobs(project_id);
CREATE INDEX idx_crawl_jobs_status ON crawl_jobs(status);
CREATE INDEX idx_crawl_jobs_next_run ON crawl_jobs(next_run_at) WHERE status = 'pending';
```

**Agent Workflows Table**:
```sql
CREATE TABLE agent_workflows (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,

    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Workflow definition (JSONB)
    workflow_dag JSONB NOT NULL, -- nodes and edges

    -- Trigger configuration
    trigger_type VARCHAR(20), -- 'manual', 'scheduled', 'webhook', 'data_change'
    trigger_config JSONB,

    -- Status
    is_active BOOLEAN DEFAULT true,
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_workflows_project ON agent_workflows(project_id);
CREATE INDEX idx_workflows_active ON agent_workflows(is_active);
```

**Workflow Executions Table**:
```sql
CREATE TABLE workflow_executions (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER REFERENCES agent_workflows(id) ON DELETE CASCADE,

    status VARCHAR(20) DEFAULT 'running', -- running, completed, failed, cancelled
    progress INTEGER DEFAULT 0, -- 0-100

    -- Execution state (JSONB)
    state JSONB DEFAULT '{}',
    logs TEXT,
    error_message TEXT,

    -- Resources
    tokens_used INTEGER DEFAULT 0,
    api_calls_made INTEGER DEFAULT 0,

    -- Timestamps
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE INDEX idx_executions_workflow ON workflow_executions(workflow_id);
CREATE INDEX idx_executions_status ON workflow_executions(status);
```

### Vector Indexing Strategy

**IVFFlat vs HNSW**:
- **IVFFlat**: Faster build time, good for <1M vectors, used in RAG-CREATOR
- **HNSW**: Better query performance, scales to 10M+ vectors, higher memory
- **Decision**: Start with IVFFlat, migrate to HNSW at scale

**Index Creation** (per project):
```sql
-- Create index after embeddings are generated (not before)
-- For 1024-dimensional BGE-M3 embeddings:
CREATE INDEX idx_chunks_embedding_project_1
ON chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100)
WHERE project_id = 1;

-- For 1536-dimensional OpenAI embeddings:
CREATE INDEX idx_chunks_embedding_project_2
ON chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100)
WHERE project_id = 2;
```

**Query Example**:
```sql
-- Semantic search within project
SELECT c.id, c.text, c.embedding <=> $1::vector AS distance
FROM chunks c
WHERE c.project_id = $2 AND c.has_embedding = 1
ORDER BY c.embedding <=> $1::vector
LIMIT 10;
```

---

## AI & ML Services

### Embedding Models

**BGE-M3 (Default, Local)**:
- **Model**: BAAI/bge-m3
- **Dimensions**: 1024
- **Max Length**: 8192 tokens
- **Language**: Multilingual (100+ languages)
- **Cost**: Free (runs locally)
- **Hardware**: CPU: 5s per text, GPU: 0.5s per text
- **Use Case**: Free tier, cost-sensitive users, privacy-focused

**BGE-Large-EN (Alternative, Local)**:
- **Model**: BAAI/bge-large-en-v1.5
- **Dimensions**: 1024
- **Max Length**: 512 tokens
- **Language**: English only
- **Cost**: Free (runs locally)
- **Performance**: Slightly better than BGE-M3 for English
- **Use Case**: English-only knowledge bases

**OpenAI text-embedding-3-small (API)**:
- **Dimensions**: 1536
- **Max Length**: 8191 tokens
- **Cost**: $0.02 per 1M tokens (~$0.10 per 1K chunks)
- **Performance**: Competitive with BGE-M3
- **Use Case**: Paid tiers, users preferring OpenAI ecosystem

**OpenAI text-embedding-3-large (API)**:
- **Dimensions**: 3072
- **Max Length**: 8191 tokens
- **Cost**: $0.13 per 1M tokens (~$0.65 per 1K chunks)
- **Performance**: Best-in-class accuracy
- **Use Case**: Enterprise tier, maximum accuracy required

**Embedding Model Selection UI**:
```typescript
interface EmbeddingModelOption {
  id: string;
  name: string;
  dimensions: number;
  cost: string;
  speed: string;
  accuracy: string;
  languages: string;
  recommended: boolean;
}

const models: EmbeddingModelOption[] = [
  {
    id: 'bge-m3',
    name: 'BGE-M3 (Free)',
    dimensions: 1024,
    cost: 'Free',
    speed: 'Fast',
    accuracy: 'Good',
    languages: 'Multilingual',
    recommended: true
  },
  // ...
];
```

### Large Language Models (LLM)

**Claude 3.5 Sonnet (Primary)**:
- **Provider**: Anthropic
- **Context**: 200K tokens
- **Cost**: $3 per 1M input tokens, $15 per 1M output tokens
- **Latency**: ~2-5 seconds for typical responses
- **Use Cases**:
  - RAG chat responses
  - Insight generation (competitive matrix, summaries)
  - Agent reasoning and orchestration
  - Document analysis (feature extraction)
  - Search query expansion

**Claude 3 Opus (Enterprise Tier)**:
- **Context**: 200K tokens
- **Cost**: $15 per 1M input, $75 per 1M output
- **Quality**: Highest accuracy, complex reasoning
- **Use Case**: Enterprise customers requiring best quality

**Fallback**:
- OpenAI GPT-4 Turbo (if Claude unavailable)
- Cost: $10 per 1M input, $30 per 1M output

### AI Service Integration

**Claude API Client** (`services/llm_service.py`):
```python
from anthropic import AsyncAnthropic

class LLMService:
    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def generate_rag_response(
        self,
        query: str,
        retrieved_chunks: List[str],
        conversation_history: List[dict]
    ) -> dict:
        """Generate RAG response with citations."""
        # Format prompt with retrieved context
        context = "\n\n".join([f"[{i+1}] {chunk}" for i, chunk in enumerate(retrieved_chunks)])

        system_prompt = f"""You are a helpful assistant answering questions based on the provided context.
Always cite sources using [1], [2], etc."""

        messages = conversation_history + [
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
        ]

        response = await self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            system=system_prompt,
            messages=messages
        )

        return {
            "content": response.content[0].text,
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens
        }

    async def generate_competitive_matrix(
        self,
        company_name: str,
        competitor_chunks: Dict[str, List[str]]
    ) -> dict:
        """Generate competitive comparison matrix."""
        # Format prompt with competitor data
        # ...
        pass

    async def extract_structured_data(
        self,
        document_text: str,
        schema: dict
    ) -> dict:
        """Extract structured data from document using JSON schema."""
        # Use Claude with JSON mode
        # ...
        pass
```

---

## External Integrations

### Firecrawl API (Web Crawling)

**Service**: https://firecrawl.dev
**Pricing**: $49/mo (Starter) = 5K pages, $249/mo (Growth) = 30K pages

**Features Used**:
- `/v1/scrape` - Single page scraping with JS rendering
- `/v1/crawl` - Multi-page crawling with sitemap detection
- `/v1/crawl/status` - Real-time crawling progress
- Markdown output - LLM-ready format
- Metadata extraction - title, description, links, images

**Implementation** (`services/crawler_service.py`):
```python
import httpx
from typing import AsyncIterator

class CrawlerService:
    def __init__(self):
        self.api_key = settings.FIRECRAWL_API_KEY
        self.base_url = "https://api.firecrawl.dev/v1"
        self.client = httpx.AsyncClient(timeout=30.0)

    async def start_crawl(
        self,
        start_url: str,
        max_pages: int = 50,
        max_depth: int = 2,
        include_patterns: List[str] = None,
        exclude_patterns: List[str] = None
    ) -> str:
        """Start async crawling job, returns job_id."""
        response = await self.client.post(
            f"{self.base_url}/crawl",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "url": start_url,
                "maxPages": max_pages,
                "maxDepth": max_depth,
                "includePatterns": include_patterns or [],
                "excludePatterns": exclude_patterns or [],
                "options": {
                    "formats": ["markdown"],
                    "onlyMainContent": True,
                    "waitFor": 2000  # wait 2s for JS
                }
            }
        )
        data = response.json()
        return data["jobId"]

    async def get_crawl_status(self, job_id: str) -> dict:
        """Check crawling status and get results."""
        response = await self.client.get(
            f"{self.base_url}/crawl/{job_id}",
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return response.json()

    async def scrape_single(self, url: str) -> dict:
        """Scrape single page (synchronous, faster)."""
        response = await self.client.post(
            f"{self.base_url}/scrape",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "url": url,
                "formats": ["markdown", "html"],
                "onlyMainContent": True
            }
        )
        data = response.json()
        return {
            "url": data["url"],
            "title": data["metadata"]["title"],
            "markdown": data["markdown"],
            "html": data["html"]
        }
```

**Error Handling**:
- 429 Rate Limit → Queue request, retry after 60s
- 500 Server Error → Retry 3× with exponential backoff
- 402 Payment Required → Notify user, upgrade prompt
- Timeout → Cancel after 5 minutes, return partial results

---

### WebSearch API (Deep Research)

**Option 1: Google Custom Search API**
- **Cost**: Free tier (100 queries/day), Paid ($5 per 1000 queries)
- **Limits**: 10 results per query max
- **Use Case**: Basic web search for research agent

**Option 2: Serper.dev**
- **Cost**: $50/mo = 5K searches, better pricing than Google
- **Features**: Google results with metadata (snippets, dates, related searches)
- **Use Case**: Professional/Enterprise tiers

**Implementation** (`services/web_search_service.py`):
```python
class WebSearchService:
    async def search(
        self,
        query: str,
        num_results: int = 10
    ) -> List[dict]:
        """Search web using Google Custom Search API."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/customsearch/v1",
                params={
                    "key": settings.GOOGLE_API_KEY,
                    "cx": settings.GOOGLE_CX_ID,
                    "q": query,
                    "num": num_results
                }
            )
            data = response.json()

            return [
                {
                    "title": item["title"],
                    "url": item["link"],
                    "snippet": item["snippet"],
                    "published_date": item.get("pagemap", {}).get("metatags", [{}])[0].get("article:published_time")
                }
                for item in data.get("items", [])
            ]
```

---

### OAuth Providers (Authentication)

**Supported Providers**:
- Google OAuth 2.0 (primary, most popular)
- GitHub OAuth (for technical users)
- Microsoft OAuth (for enterprise)

**Library**: `authlib` (Python) or `next-auth` (Next.js)

**Implementation**:
```python
from authlib.integrations.starlette_client import OAuth

oauth = OAuth()
oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

@app.get('/auth/google')
async def google_login(request: Request):
    redirect_uri = request.url_for('google_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get('/auth/google/callback')
async def google_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get('userinfo')
    # Create or update user in database
    # Generate JWT token
    # Redirect to dashboard
```

---

## Infrastructure & DevOps

### Hosting Options

**Option 1: Railway.app (Recommended for MVP)**
- **Pros**: Simple deployment, PostgreSQL included, auto-scaling, $5/mo start
- **Cons**: Limited to 8GB RAM per service, US-only regions
- **Cost**: ~$50-100/mo for 3 services (frontend, backend, database)

**Option 2: Render.com**
- **Pros**: Similar to Railway, generous free tier, PostgreSQL included
- **Cons**: Cold starts on free tier, slower than Railway
- **Cost**: ~$40-80/mo for paid tier

**Option 3: AWS (Production/Scale)**
- **Pros**: Maximum flexibility, global CDN, enterprise-ready
- **Cons**: Complex setup, higher initial cost
- **Services**:
  - **Compute**: ECS Fargate (containers) or EC2 (VMs)
  - **Database**: RDS PostgreSQL with pgvector (db.t4g.medium = $50/mo)
  - **Storage**: S3 for file storage ($0.023 per GB)
  - **CDN**: CloudFront for frontend assets
  - **Monitoring**: CloudWatch
- **Cost**: ~$200-500/mo at 1000 users

**Recommendation**:
- **MVP (0-500 users)**: Railway.app
- **Growth (500-5K users)**: Render.com or Railway Pro
- **Scale (5K+ users)**: AWS with multi-region

### Deployment Architecture

**Multi-Service Deployment**:
```yaml
# railway.json or docker-compose.yml
services:
  frontend:
    build: ./frontend
    environment:
      - NEXT_PUBLIC_API_URL=https://api.knowledgetree.app
    expose:
      - 3000

  backend:
    build: ./backend
    environment:
      - DATABASE_URL=${{DATABASE_URL}}
      - ANTHROPIC_API_KEY=${{ANTHROPIC_API_KEY}}
    expose:
      - 8000
    depends_on:
      - database

  rag-creator:
    build: ./backend/services/rag_creator
    environment:
      - DATABASE_URL=${{DATABASE_URL}}
    expose:
      - 8001
    volumes:
      - ./uploads:/app/uploads
      - ./models:/app/models

  database:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_USER=knowledgetree
      - POSTGRES_PASSWORD=${{DB_PASSWORD}}
      - POSTGRES_DB=knowledgetree
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

### CI/CD Pipeline

**GitHub Actions** (free for public repos, $0.008/min for private):

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run backend tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest
      - name: Run frontend tests
        run: |
          cd frontend
          npm install
          npm run test

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Railway
        uses: railway-app/deploy@v1
        with:
          api-key: ${{ secrets.RAILWAY_API_KEY }}
```

### Monitoring & Observability

**Sentry** (Error Tracking):
- **Free tier**: 5K events/month
- **Paid**: $26/mo = 50K events
- Track backend exceptions, frontend errors
- Performance monitoring

**Posthog** (Product Analytics):
- **Free tier**: 1M events/month
- Track user behavior, feature usage, funnels
- Self-hosted option available

**Prometheus + Grafana** (Metrics):
- Free, open-source
- Track API latency, database queries, embedding throughput
- Alerting on anomalies

**Logging**:
- **Development**: Console logs
- **Production**: Structured JSON logs to stdout
  - Collected by Railway/Render logs
  - Optionally: Ship to Datadog, LogRocket

---

## Development Tools

### Code Quality

**Backend (Python)**:
- `black` - Code formatter (opinionated)
- `ruff` - Fast linter (replaces flake8, isort)
- `mypy` - Static type checking
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `coverage` - Test coverage reports

**Frontend (TypeScript)**:
- `eslint` - Linting (with TypeScript plugin)
- `prettier` - Code formatter
- `vitest` - Unit testing (Vite-native)
- `testing-library/react` - Component testing
- `playwright` - E2E testing

### Git Hooks (pre-commit)

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.1.0
    hooks:
      - id: black

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.15
    hooks:
      - id: ruff

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.1.0
    hooks:
      - id: prettier
        types_or: [javascript, typescript, tsx, jsx, json, css, markdown]
```

### Documentation

**API Documentation**:
- **FastAPI**: Automatic OpenAPI/Swagger docs at `/docs`
- **Redoc**: Alternative API docs at `/redoc`

**Code Documentation**:
- **Backend**: Python docstrings (Google style)
- **Frontend**: TSDoc comments for complex components

**User Documentation**:
- **GitBook** or **Docusaurus** for knowledge base
- Hosted at docs.knowledgetree.app

---

## Integration Architecture

### RAG-CREATOR Integration Strategy

**Approach**: Microservice with shared database

**Step 1: Copy RAG-CREATOR Code**
```bash
# Copy entire RAG-CREATOR backend to new project
cp -r /home/jarek/projects/RAG-CREATOR/backend/services/* \
     /home/jarek/projects/genetico/backend/services/rag_creator/

# Keep existing files:
# - pipeline.py
# - pdf_splitter.py
# - text_extractor.py
# - chunker.py
# - embedder.py
# - progress_manager.py
```

**Step 2: Add Multi-Tenancy**

Modify RAG-CREATOR models to add `project_id`:
```python
# backend/services/rag_creator/models/chunk.py
class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)  # NEW
    document_id = Column(Integer, ForeignKey("documents.id"))
    # ... rest of model
```

Add tenant filtering to all queries:
```python
# Before:
chunks = session.query(Chunk).filter(Chunk.document_id == doc_id).all()

# After:
chunks = session.query(Chunk).filter(
    Chunk.document_id == doc_id,
    Chunk.project_id == project_id  # Tenant isolation
).all()
```

**Step 3: Wrap with New API Layer**

Create unified API routes in main FastAPI app:
```python
# backend/api/routes/documents.py
from backend.services.rag_creator.pipeline import VectorizationPipeline

@router.post("/projects/{project_id}/documents/upload")
async def upload_document(
    project_id: int,
    file: UploadFile,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate project ownership
    project = get_project_or_404(project_id, user, db)

    # Save file
    file_path = save_uploaded_file(file, project_id)

    # Create document record
    document = Document(
        project_id=project_id,
        source_type="pdf",
        filename=file.filename,
        status="pending"
    )
    db.add(document)
    db.commit()

    # Start RAG-CREATOR pipeline in background
    pipeline = VectorizationPipeline(
        project_id=project_id,
        document_id=document.id,
        file_path=file_path,
        embedding_model=project.embedding_model
    )

    background_tasks.add_task(pipeline.run)

    return {"document_id": document.id, "status": "processing"}
```

**Step 4: Shared Database Schema**

Both services use same PostgreSQL database:
```
knowledgetree_db/
├── public/                    # Default schema
│   ├── users
│   ├── projects
│   ├── categories
│   ├── documents              # Shared by both
│   ├── chunks                 # Shared by both
│   ├── conversations
│   └── ...
```

**Step 5: Embedding Model Selection**

Add model parameter to pipeline:
```python
# backend/services/rag_creator/embedder.py
class Embedder:
    def __init__(self, model_name: str = "bge-m3"):
        self.model_name = model_name

        if model_name.startswith("openai-"):
            # Use OpenAI API
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.is_local = False
        else:
            # Use local BGE model
            from FlagEmbedding import BGEM3FlagModel
            self._model = BGEM3FlagModel(
                model_name_or_path=model_name,
                use_fp16=True,
                device=settings.EMBEDDING_DEVICE
            )
            self.is_local = True

    async def embed_single(self, text: str) -> List[float]:
        if self.is_local:
            return self._embed_local(text)
        else:
            return await self._embed_openai(text)
```

---

### Genetico Migration Strategy

**Goal**: Transform Genetico category editor into KnowledgeTree platform

**Phase 1: Rename & Rebrand** (Week 1)
- Update branding: Genetico → KnowledgeTree
- Change color scheme, logo, landing page
- Keep all existing functionality

**Phase 2: Add Projects Layer** (Week 2)
- Add `projects` table and CRUD APIs
- Wrap existing categories with project_id
- Add project switcher to UI
- Migrate localStorage to project-scoped storage

**Phase 3: Integrate RAG-CREATOR** (Week 3-4)
- Copy RAG-CREATOR services
- Add multi-tenancy to models
- Create unified API routes
- Add PDF upload UI

**Phase 4: Add Search** (Week 5)
- Implement vector search endpoint
- Create search UI component
- Connect to pgvector

**File Structure After Migration**:
```
knowledgetree/
├── frontend/                  # React 19 UI (from Genetico)
│   ├── src/
│   │   ├── components/
│   │   │   ├── editor/        # Category tree (unchanged from Genetico)
│   │   │   ├── knowledge/     # NEW: Document management
│   │   │   ├── rag/           # NEW: Chat interface
│   │   │   └── ui/            # shadcn/ui components
│   │   ├── context/
│   │   │   ├── EditorContext.tsx    # From Genetico
│   │   │   └── ProjectContext.tsx   # NEW
│   │   └── ...
├── backend/                   # FastAPI (new)
│   ├── api/
│   │   └── routes/
│   │       ├── projects.py    # NEW
│   │       ├── categories.py  # Adapted from Genetico
│   │       ├── documents.py   # NEW
│   │       └── search.py      # NEW
│   ├── models/
│   │   ├── project.py         # NEW
│   │   ├── category.py        # From Genetico
│   │   ├── document.py        # NEW
│   │   └── chunk.py           # NEW
│   ├── services/
│   │   ├── rag_creator/       # Copied from RAG-CREATOR
│   │   │   ├── pipeline.py
│   │   │   ├── embedder.py
│   │   │   └── ...
│   │   └── ...
│   └── ...
└── ...
```

---

## Deployment Strategy

### Environment Configuration

**Development** (`.env.development`):
```bash
# App
DEBUG=true
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql://knowledgetree:password@localhost:5432/knowledgetree_dev

# APIs
ANTHROPIC_API_KEY=sk-ant-...
FIRECRAWL_API_KEY=fc-...
GOOGLE_API_KEY=AIza...

# OAuth
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

# Embedding
EMBEDDING_DEVICE=cpu

# CORS
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

**Production** (`.env.production`):
```bash
# App
DEBUG=false
ENVIRONMENT=production
SECRET_KEY=<generated-secret>

# Database (from Railway)
DATABASE_URL=${{DATABASE_URL}}

# APIs
ANTHROPIC_API_KEY=${{ANTHROPIC_API_KEY}}
FIRECRAWL_API_KEY=${{FIRECRAWL_API_KEY}}

# OAuth
GOOGLE_CLIENT_ID=${{GOOGLE_CLIENT_ID}}
GOOGLE_CLIENT_SECRET=${{GOOGLE_CLIENT_SECRET}}

# Embedding
EMBEDDING_DEVICE=cpu  # or cuda if GPU available

# Security
ALLOWED_HOSTS=knowledgetree.app,www.knowledgetree.app
CORS_ORIGINS=https://knowledgetree.app,https://www.knowledgetree.app

# Monitoring
SENTRY_DSN=${{SENTRY_DSN}}
```

### Database Migrations

**Alembic** (SQLAlchemy migration tool):

```bash
# Create new migration
alembic revision --autogenerate -m "Add projects table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Deployment Checklist

**Pre-Launch**:
- [ ] All tests passing (backend + frontend)
- [ ] Database migrations applied
- [ ] Environment variables configured
- [ ] HTTPS certificates valid
- [ ] CORS settings correct
- [ ] Rate limiting configured
- [ ] Sentry error tracking enabled
- [ ] Monitoring dashboards created
- [ ] Backup strategy tested

**Launch Day**:
- [ ] Deploy to production
- [ ] Smoke test critical paths
- [ ] Monitor error rates
- [ ] Check API latency
- [ ] Verify database connections
- [ ] Test OAuth login flows

**Post-Launch**:
- [ ] Monitor user sign-ups
- [ ] Track conversion funnel
- [ ] Watch for errors in Sentry
- [ ] Check infrastructure costs
- [ ] Collect user feedback

---

## Security Considerations

### Authentication & Authorization

**JWT Token Strategy**:
- Access token: 15 minutes expiry
- Refresh token: 7 days expiry
- Tokens stored in httpOnly cookies (secure)
- Revocation via blacklist in Redis

**Password Security**:
- bcrypt hashing (12 rounds)
- Minimum length: 8 characters
- Complexity: 1 uppercase, 1 number, 1 special char

**API Security**:
- Rate limiting: 100 req/min per user
- CORS: Whitelist specific origins only
- HTTPS: Force TLS 1.3
- Headers: Security headers (HSTS, CSP, X-Frame-Options)

### Data Security

**Encryption**:
- At Rest: PostgreSQL encrypted volumes
- In Transit: TLS 1.3 for all connections
- Backups: Encrypted with AES-256

**Data Isolation**:
- Row-level security in PostgreSQL (per project_id)
- No cross-tenant queries possible
- API validates user owns project before every operation

**PII Handling**:
- Email addresses hashed in logs
- No sensitive data in error messages
- GDPR: Right to access, delete, export data

### Vulnerability Management

**Dependency Scanning**:
- Dependabot (GitHub) for automatic updates
- `pip-audit` for Python vulnerabilities
- `npm audit` for JavaScript vulnerabilities

**Code Scanning**:
- `bandit` (Python) - security linter
- `eslint-plugin-security` (JavaScript)
- SonarQube for code quality

**Penetration Testing**:
- Manual testing before launch
- Bug bounty program after 1000 users
- Annual third-party audit

---

## Performance Optimization

### Backend Optimization

**Database Query Optimization**:
- Connection pooling (10-20 connections)
- Prepared statements (SQLAlchemy ORM)
- Indexes on frequently queried columns
- EXPLAIN ANALYZE for slow queries

**Caching Strategy**:
- Redis for session storage
- Cache embedding results (7 days TTL)
- Cache Firecrawl responses (24 hours TTL)
- Cache LLM responses for identical queries (1 hour TTL)

**Async Processing**:
- Background tasks for long operations (crawling, embedding)
- Celery task queue for complex workflows
- SSE for real-time progress updates

### Frontend Optimization

**Code Splitting**:
- Lazy load routes with React.lazy()
- Dynamic imports for large components (RAG chat, insights)
- Tree shaking with Vite

**Asset Optimization**:
- Image compression (TinyPNG, Squoosh)
- WebP format with PNG fallback
- CDN for static assets (CloudFront, Cloudflare)

**Performance Budgets**:
- Initial load: <200KB JavaScript
- Time to Interactive: <3 seconds
- Lighthouse score: >90

---

## Cost Estimates

### Development Costs (3 Months MVP)

| Item | Cost |
|------|------|
| Developer time (1 FTE × 3 mo) | $30,000 |
| Design (UI/UX) | $3,000 |
| Domain + SSL | $50 |
| Hosting (Railway dev) | $150 |
| APIs (testing, Firecrawl, Claude) | $500 |
| **Total** | **$33,700** |

### Operational Costs (Monthly)

**MVP (500 users, 50 paid)**:
| Item | Cost |
|------|------|
| Hosting (Railway Pro) | $80 |
| Database (PostgreSQL) | Included |
| Firecrawl (5K pages) | $49 |
| Claude API (100K calls) | $150 |
| Sentry (50K events) | $26 |
| Domain + SSL | $2 |
| **Total** | **$307/mo** |

**At Scale (5K users, 1K paid)**:
| Item | Cost |
|------|------|
| Hosting (AWS ECS) | $300 |
| Database (RDS db.t4g.large) | $150 |
| S3 Storage (1TB) | $23 |
| Firecrawl (100K pages) | $499 |
| Claude API (5M calls) | $7,500 |
| Sentry | $99 |
| Monitoring (Datadog) | $180 |
| **Total** | **$8,751/mo** |

**Margin Analysis** (Year 1):
- Revenue: $190K
- COGS: $307 × 12 = $3,684
- Gross Margin: 98% (SaaS typical: 80-90%)

---

## Risks & Mitigation

### Technical Risks

**Risk 1: PostgreSQL + pgvector performance at scale**
- **Mitigation**: Benchmark at 100K, 500K, 1M chunks
- **Fallback**: Migrate to dedicated vector DB (Qdrant, Weaviate)

**Risk 2: BGE-M3 embedding quality insufficient**
- **Mitigation**: A/B test vs OpenAI in beta
- **Fallback**: Default to OpenAI for paid tiers

**Risk 3: Firecrawl API reliability issues**
- **Mitigation**: Implement retry logic, fallback to Playwright
- **Fallback**: Build in-house crawler (Phase 2)

### Business Risks

**Risk 1: OpenAI/Anthropic API cost explosion**
- **Mitigation**: Strict rate limits per tier, user budgets
- **Monitoring**: Alert if daily cost exceeds threshold

**Risk 2: Competitor launches similar product**
- **Mitigation**: Fast iteration, strong community, niche focus

---

## Next Steps

1. ✅ **Review and Approve Tech Stack**
2. 📋 **Create Detailed Implementation Roadmap**
   - Sprint planning (2-week sprints)
   - Task breakdown in linear/Jira
   - Assign dependencies
3. 🎨 **Design System & Mockups**
   - Figma designs for new features
   - User flow diagrams
4. 💻 **Phase 1 Development** (Weeks 1-4)
   - Setup repository
   - Database schema
   - RAG-CREATOR integration
   - Authentication system
5. 🧪 **Testing & QA** (Weeks 5-6)
   - Unit tests
   - Integration tests
   - User acceptance testing
6. 🚀 **Beta Launch** (Week 7-8)
   - Deploy to production
   - Invite beta users
   - Collect feedback
7. 📈 **Iterate & Scale** (Weeks 9-12)
   - Fix bugs
   - Add premium features
   - Optimize performance

---

**Document Version**: 1.0
**Last Updated**: January 19, 2026
**Next Review**: After PRD approval

---

*End of Technical Stack Specification*
