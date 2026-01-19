# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with the KnowledgeTree codebase.

---

## Project Overview

**KnowledgeTree** - AI-powered knowledge repository and RAG (Retrieval-Augmented Generation) platform for enterprises. Multi-tenant SaaS application enabling users to build searchable knowledge bases from PDFs, web content, and documents with AI-powered chat, insights, and agentic workflows.

**Business Model**: Freemium SaaS with 4 pricing tiers (Free, Starter $49/mo, Professional $149/mo, Enterprise $499/mo)

**Current Phase**: Pre-development (Sprint 0 planning)

**Key Documents**:
- **PRD.md** - Complete product requirements (11 features, user personas, business model)
- **TECH_STACK.md** - Technical architecture and stack decisions
- **DESIGN_SYSTEM.md** - Complete UI/UX specifications (60+ pages)
- **ROADMAP.md** - 20-week development roadmap with 9 sprints

---

## Development Status

**Current Sprint**: Sprint 0 - Foundation & Setup (Week 1-2)

**Next Milestone**: Free Tier MVP (Week 8) - Private Beta launch

**Development Team**: 1 developer (solo MVP phase)

**Timeline**: 20 weeks to production 1.0 launch

---

## Quick Start (When Development Begins)

### Frontend Setup
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Production build
npm run build
```

### Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Start FastAPI server
uvicorn main:app --reload

# Run database migrations
alembic upgrade head
```

### Docker Setup (Full Stack)
```bash
# Start all services
docker-compose up

# Stop all services
docker-compose down
```

---

## Architecture Overview

### Tech Stack

**Frontend**:
- React 19 + TypeScript 5.3+
- Vite 6.0+ (build tool)
- TailwindCSS 3.4+ (styling)
- shadcn/ui (component library)
- Inter font (same as Notion)
- Lucide React (professional SVG icons)
- Framer Motion (animations)
- react-i18next (Polish primary, English secondary)

**Backend**:
- FastAPI 0.109.0+ (Python 3.11+)
- PostgreSQL 16 + pgvector 0.7 (vector database)
- SQLAlchemy 2.0+ (async ORM)
- Alembic (database migrations)
- BGE-M3 embeddings (1024 dimensions, multilingual, local)

**AI & RAG**:
- BGE-M3 (BAAI/bge-m3) for embeddings
- Claude 3.5 Sonnet (Anthropic API) for chat
- Firecrawl API (web crawling)
- Google Custom Search API or Serper.dev (web search)

**PDF Processing** (from RAG-CREATOR):
- Docling (primary extraction)
- PyMuPDF (fallback)
- Chunking: 1000 characters, 200 overlap

**Infrastructure**:
- Railway.app (MVP phase)
- AWS (production: EC2, RDS, S3, CloudFront)
- Docker + Docker Compose

### System Architecture

```
Frontend (React 19)
    ↓ REST API
Backend (FastAPI)
    ↓
PostgreSQL + pgvector
    ↓
BGE-M3 Embeddings (local)
    ↓
Claude API (chat/insights)
```

---

## Design Principles

**CRITICAL UI/UX Requirements** (User Mandate):

1. **NO EMOJIS** - Professional, business-focused interface only
2. **Pastel Colors** - Soft, modern color palette (see DESIGN_SYSTEM.md)
3. **Inter Font** - Same typography as Notion
4. **Professional SVG Icons** - Lucide React library (1000+ icons)
5. **Dark/Light Mode** - Full theme support with system preference detection
6. **Modern Design** - Clean, spacious layouts with subtle animations
7. **Polish Language Primary** - Default UI in Polish, switchable to English

**Color Palette**:
- Primary Blue: `#3B82F6` (pastel)
- Success Green: `#22C55E`
- Warning Amber: `#F59E0B`
- Error Red: `#EF4444`
- Neutrals: `#FAFAFA` to `#171717` (grayscale)

**Typography**:
- Font Family: `'Inter', -apple-system, BlinkMacSystemFont, sans-serif`
- Weights: Regular (400), Medium (500), Semibold (600), Bold (700)
- Full Polish diacritics support (ą, ć, ę, ł, ń, ó, ś, ź, ż)

**Animations**:
- Duration: 100-300ms
- Easing: Spring physics (Framer Motion)
- Purpose: Smooth transitions, micro-interactions

See **DESIGN_SYSTEM.md** for complete specifications.

---

## Database Schema

**Multi-Tenant Architecture** - All data isolated by `project_id`

**Core Tables**:
- `users` - User accounts (email, password_hash, created_at)
- `projects` - User projects (name, description, owner_id, created_at)
- `categories` - Hierarchical tree (name, parent_id, project_id, depth, order)
- `documents` - Uploaded PDFs/web content (filename, project_id, category_id, status)
- `chunks` - Text chunks with embeddings (text, embedding[1024], document_id, has_embedding)
- `conversations` - Chat history (project_id, user_id, created_at)
- `messages` - Chat messages (conversation_id, role, content, created_at)
- `crawl_jobs` - Web crawling jobs (url, status, project_id, scheduled_at)
- `agent_workflows` - Enterprise workflows (template, status, execution_log)

**Vector Index**: IVFFlat index on `chunks.embedding` for fast similarity search

See **TECH_STACK.md** for complete schema SQL.

---

## Roadmap Summary

**9 Sprints (2 weeks each)**:

| Sprint | Weeks | Features | Deliverable |
|--------|-------|----------|-------------|
| **Sprint 0** | 1-2 | Foundation (DB, Auth, Design System) | Dev environment ready |
| **Sprint 1** | 3-4 | F1 Project Management + F3 Category Tree | Core UI functional |
| **Sprint 2** | 5-6 | F2 PDF Upload & Vectorization | RAG pipeline working |
| **Sprint 3** | 7-8 | F4 Semantic Search + F5 Export | **Free Tier MVP (Beta)** |
| **Sprint 4** | 9-10 | F11 RAG Chat + Stripe | **Starter Tier ($49/mo)** |
| **Sprint 5** | 11-12 | F10 AI Insights | Professional Tier value |
| **Sprint 6** | 13-14 | F6 Web Crawling | **Professional Tier ($149/mo)** |
| **Sprint 7** | 15-16 | F7 Web Search Agent + F8 Tech Docs | Advanced AI features |
| **Sprint 8** | 17-18 | F9 Agentic Workflows + Team | **Enterprise Tier ($499/mo)** |
| **Sprint 9** | 19-20 | Polish, Security, Docs | **Production 1.0 Launch** |

**Key Milestones**:
- Week 8: Private Beta (10 users)
- Week 10: Public Beta + Revenue ($245 MRR)
- Week 12: Professional Tier ($890 MRR)
- Week 20: Production Launch ($2,000 MRR target)

See **ROADMAP.md** for detailed sprint breakdowns.

---

## Feature Overview (11 Total)

### P0 - Launch Blockers (Free Tier)
- **F1: Project Management** - CRUD operations, multi-project support
- **F2: PDF Upload & Vectorization** - 7-stage pipeline, BGE-M3 embeddings
- **F3: Category Tree Editor** - Hierarchical organization, drag-drop
- **F4: Semantic Search** - Vector similarity, ranking, filtering

### P1 - High Priority (Paid Tiers)
- **F5: Export Functionality** - JSON, Markdown, CSV formats
- **F6: Web Crawling** - Firecrawl integration, scheduled jobs
- **F10: AI-Powered Insights** - Summaries, trends, citation network
- **F11: RAG Chat Interface** - Streaming chat with Claude API

### P2 - Professional Tier
- **F7: Deep Web Search Agent** - Google CSE integration, result synthesis
- **F8: Technical Document Analysis** - Equations, code blocks, diagrams

### P3 - Enterprise Tier
- **F9: Agentic Workflow Orchestration** - LangGraph, workflow templates

See **PRD.md** for complete feature specifications.

---

## Development Guidelines

### Code Organization (Planned)

**Frontend** (`frontend/src/`):
```
src/
├── components/
│   ├── project/       # Project management UI
│   ├── category/      # Category tree editor
│   ├── document/      # PDF upload, document list
│   ├── search/        # Search interface
│   ├── chat/          # RAG chat UI
│   └── ui/            # shadcn/ui primitives
├── context/           # React Context providers
├── hooks/             # Custom React hooks
├── lib/               # Utility functions
├── locales/           # i18n translations (pl, en)
│   ├── pl/
│   │   ├── common.json
│   │   └── editor.json
│   └── en/
├── styles/            # Global styles, theme
├── types.ts           # TypeScript interfaces
└── main.tsx
```

**Backend** (`backend/`):
```
backend/
├── api/
│   ├── routes/        # FastAPI endpoints
│   ├── dependencies/  # Auth, DB dependencies
│   └── middleware/    # CORS, logging
├── core/
│   ├── config.py      # Settings (DB, API keys)
│   └── security.py    # JWT, password hashing
├── models/            # SQLAlchemy models
├── schemas/           # Pydantic schemas
├── services/          # Business logic
│   ├── embedder.py    # BGE-M3 embedding service
│   ├── pdf_processor.py  # PDF pipeline
│   ├── rag.py         # RAG retrieval
│   └── crawler.py     # Web crawling
├── alembic/           # Database migrations
└── main.py            # FastAPI app entry
```

### Coding Patterns

**React Component Pattern**:
```typescript
import { Button } from '@/components/ui/button';
import { useTranslation } from 'react-i18next';

export function MyComponent() {
  const { t } = useTranslation();

  return (
    <div className="p-4 bg-neutral-50 dark:bg-neutral-900">
      <Button variant="primary">
        {t('actions.save')}
      </Button>
    </div>
  );
}
```

**FastAPI Endpoint Pattern**:
```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.project import Project

router = APIRouter()

@router.get("/projects/{project_id}")
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db)
) -> Project:
    # Multi-tenant isolation
    project = await db.get(Project, project_id)
    return project
```

**Tree Operations Pattern** (from Genetico):
```typescript
// All tree operations are immutable
function updateCategoryInTree(
  categories: Category[],
  targetId: string,
  updates: Partial<Category>
): Category[] {
  return categories.map(cat => {
    if (cat.id === targetId) {
      return { ...cat, ...updates, updatedAt: Date.now() };
    }
    if (cat.subcategories) {
      return {
        ...cat,
        subcategories: updateCategoryInTree(cat.subcategories, targetId, updates)
      };
    }
    return cat;
  });
}
```

### Internationalization (i18n)

**Setup**:
```typescript
// i18n.ts
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      pl: { common: plCommon, editor: plEditor },
      en: { common: enCommon, editor: enEditor }
    },
    fallbackLng: 'pl',  // Polish as default
    defaultNS: 'common'
  });
```

**Usage**:
```typescript
// Component
const { t } = useTranslation();

<h1>{t('app.name')}</h1>  // "KnowledgeTree"
<Button>{t('actions.create')}</Button>  // "Utwórz"
```

**Translations** (`locales/pl/common.json`):
```json
{
  "app": {
    "name": "KnowledgeTree",
    "tagline": "Platforma zarządzania wiedzą"
  },
  "actions": {
    "create": "Utwórz",
    "edit": "Edytuj",
    "delete": "Usuń",
    "save": "Zapisz"
  }
}
```

### RAG Pipeline (from RAG-CREATOR)

**7-Stage PDF Processing**:
1. **Validation** - File type, size, corruption check
2. **Split** - Page-level split for parallel processing
3. **Extract** - Docling (primary) or PyMuPDF (fallback)
4. **Chunk** - 1000 chars, 200 overlap
5. **Embed** - BGE-M3 batch encoding (1024 dim)
6. **Store** - PostgreSQL with pgvector
7. **Index** - IVFFlat for fast similarity search

**Embedding Service** (`backend/services/embedder.py`):
```python
from FlagEmbedding import BGEM3FlagModel

class EmbedderService:
    def __init__(self):
        self.model = BGEM3FlagModel(
            'BAAI/bge-m3',
            use_fp16=True,
            device='cpu'  # or 'cuda' for GPU
        )

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        output = self.model.encode(
            texts,
            batch_size=32,
            max_length=8192,
            return_dense=True
        )
        return [vec.tolist() for vec in output['dense_vecs']]
```

**Vector Search** (PostgreSQL + pgvector):
```sql
-- Find top 20 similar chunks
SELECT
  c.id, c.text, c.document_id,
  1 - (c.embedding <=> $1::vector) AS similarity
FROM chunks c
WHERE c.project_id = $2 AND c.has_embedding = 1
ORDER BY c.embedding <=> $1::vector
LIMIT 20;
```

---

## Testing Strategy

**Test Coverage Targets**:
- Backend: >80% (unit + integration)
- Frontend: >60% (component + E2E)

**Testing Tools**:
- Backend: pytest, pytest-asyncio
- Frontend: Vitest, React Testing Library
- E2E: Playwright
- Load Testing: Locust or k6

**Critical Test Scenarios**:
- PDF processing success rate >95%
- Vector search precision >80%
- Chat response latency <2s
- Multi-tenant isolation (no data leakage between projects)

---

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Page Load Time** | <2s | Lighthouse (3G network) |
| **Search Latency** | <200ms | P95 percentile |
| **Chat Response** | <2s | Time to first token |
| **PDF Processing** | <30s | Avg 10-page PDF |
| **Uptime** | >99.5% | Production monitoring |

---

## Security Requirements

**Authentication**:
- JWT tokens (access 15m, refresh 7d)
- Password hashing (bcrypt)
- Email verification (optional for MVP)

**Authorization**:
- Multi-tenant isolation (project_id filtering)
- User roles (owner, admin, editor, viewer)
- API rate limiting (100 req/min per user)

**Data Protection**:
- HTTPS only (TLS 1.3)
- No sensitive data in logs
- Regular dependency updates (npm audit, safety)

**OWASP Top 10 Compliance**:
- SQL injection prevention (parameterized queries)
- XSS protection (React default escaping)
- CSRF tokens (for state-changing operations)

---

## Infrastructure & Deployment

**MVP Phase** (Week 1-8):
- Platform: Railway.app Starter (~$20/mo)
- Database: PostgreSQL 16 with pgvector
- Compute: 1 FastAPI instance, 1 React build

**Beta Phase** (Week 9-12):
- Platform: Railway.app Pro (~$70/mo)
- Database: PostgreSQL Pro (10GB storage)
- Compute: 2 FastAPI instances (load balanced)

**Production Phase** (Week 13-20):
- Platform: AWS
- Compute: EC2 t3.medium x2 ($60/mo)
- Database: RDS PostgreSQL db.t3.micro ($15/mo)
- Storage: S3 ($1/mo)
- CDN: CloudFront ($85/mo)
- **Total**: ~$191/month

**Scaling Triggers**:
- >80% CPU usage → Add EC2 instance
- >80% DB storage → Upgrade RDS
- >5,000 users → Consider EKS (Kubernetes)

---

## Documentation Standards

**Code Comments**:
- Document complex logic, not obvious code
- Use JSDoc/docstrings for public APIs
- Polish language allowed in comments for team communication

**API Documentation**:
- FastAPI auto-generates Swagger docs
- Document all endpoints with examples
- Include error response schemas

**User Documentation**:
- User guides in Polish (primary) and English
- Video tutorials for key features
- FAQ and troubleshooting guides

**Developer Documentation**:
- Setup instructions (SETUP.md)
- Architecture diagrams (ARCHITECTURE.md)
- Database schema (DATABASE.md)
- API reference (API.md)

---

## Cost Management

**Variable Costs** (Per User Per Month):

| Tier | Claude API | Firecrawl | Total | Margin |
|------|------------|-----------|-------|--------|
| **Free** | $0 | $0 | $0.10 | N/A |
| **Starter** ($49) | $2 | $0 | $3 | $46 (94%) |
| **Professional** ($149) | $5 | $3 | $8 | $141 (95%) |
| **Enterprise** ($499) | $15 | $10 | $25 | $474 (95%) |

**Cost Monitoring**:
- Track Claude API usage per user (implement caching)
- Alert when Firecrawl costs exceed $100/week
- Monitor AWS costs daily (CloudWatch billing alerts)

**Optimization Strategies**:
- Cache Claude responses for common queries
- Rate limit Firecrawl to 10 URLs/minute
- Use BGE-M3 locally (zero API costs for embeddings)

---

## Known Constraints

**Technical**:
- BGE-M3 on CPU is slower than GPU (consider upgrade if needed)
- pgvector IVFFlat index requires periodic rebuilding (VACUUM)
- Claude API has rate limits (5 req/sec for Tier 1)

**Business**:
- Solo developer (limited bandwidth, no 24/7 coverage)
- MVP budget (~$1,000 for 6 months infrastructure)
- Enterprise sales cycle is long (3-6 months)

**Product**:
- Free tier has limited storage (1GB, 100 documents)
- Search quality depends on document quality
- Web crawling respects robots.txt (may miss content)

---

## Critical Success Factors

1. **Leverage RAG-CREATOR** - Copy proven PDF pipeline, don't reinvent
2. **Strict Scope Management** - P0 features first, defer P2/P3 if needed
3. **Early User Feedback** - 10 beta users by Week 8
4. **Polish UI from Day 1** - Design system in Sprint 0
5. **Revenue Focus** - Starter Tier in Sprint 4 for validation
6. **Document Everything** - Write docs parallel to development
7. **Monitor Costs** - Track API usage, implement caching

---

## Next Steps

**Sprint 0 (Starting Now)**:
1. Set up GitHub repository (mono-repo or separate frontend/backend)
2. Initialize Vite + React 19 + TypeScript (frontend)
3. Initialize FastAPI project structure (backend)
4. Create Docker Compose (PostgreSQL + pgvector, Redis)
5. Design database schema (multi-tenant with project_id)
6. Implement JWT authentication
7. Set up TailwindCSS + shadcn/ui + Inter font
8. Configure react-i18next (Polish/English)

**Week 1 Deliverable**: Dev environment ready, design system functional

See **ROADMAP.md** for complete Sprint 0 task breakdown.

---

## References

- **PRD.md** - Product requirements and business model
- **TECH_STACK.md** - Complete technical architecture
- **DESIGN_SYSTEM.md** - UI/UX specifications (60+ pages)
- **ROADMAP.md** - 20-week development roadmap
- **RAG-CREATOR** - Existing RAG system at `/home/jarek/projects/RAG-CREATOR/`

---

**Last Updated**: 2026-01-19
**Current Phase**: Pre-development (Sprint 0 planning)
**Next Milestone**: Free Tier MVP (Week 8)
