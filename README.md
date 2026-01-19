# KnowledgeTree

**AI-powered knowledge repository and RAG platform for enterprises**

Multi-tenant SaaS application enabling users to build searchable knowledge bases from PDFs, web content, and documents with AI-powered chat, insights, and agentic workflows.

---

## Project Status

**Current Sprint**: Sprint 0 - Foundation & Setup (Week 1-2)
**Next Milestone**: Free Tier MVP (Week 8) - Private Beta
**Development Team**: 1 developer (solo MVP phase)
**Timeline**: 20 weeks to production 1.0 launch

---

## Tech Stack

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

**Infrastructure**:
- Railway.app (MVP phase)
- AWS (production: EC2, RDS, S3, CloudFront)
- Docker + Docker Compose

---

## Quick Start

### Prerequisites
- Node.js 20+ and npm
- Python 3.11+
- Docker and Docker Compose
- PostgreSQL 16 with pgvector extension

### Development Setup

**1. Clone repository**:
```bash
git clone <repo-url>
cd knowledgetree
```

**2. Environment variables**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

**3. Start with Docker (Recommended)**:
```bash
docker-compose up
```

**4. Manual setup (Alternative)**:

**Frontend**:
```bash
cd frontend
npm install
npm run dev
# Frontend runs on http://localhost:5173
```

**Backend**:
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
# Backend runs on http://localhost:8000
```

**Database migrations**:
```bash
cd backend
alembic upgrade head
```

---

## Project Structure

```
knowledgetree/
├── frontend/          # React 19 + TypeScript frontend
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── context/     # React Context providers
│   │   ├── hooks/       # Custom hooks
│   │   ├── locales/     # i18n translations (pl, en)
│   │   ├── lib/         # Utilities
│   │   ├── styles/      # Global styles
│   │   └── types.ts     # TypeScript interfaces
│   ├── package.json
│   └── vite.config.ts
│
├── backend/           # FastAPI backend
│   ├── api/           # API routes
│   ├── core/          # Config, security
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic schemas
│   ├── services/      # Business logic
│   ├── alembic/       # Database migrations
│   └── main.py        # FastAPI app
│
├── docker/            # Dockerfiles
│   ├── Dockerfile.frontend
│   └── Dockerfile.backend
│
├── scripts/           # Utility scripts
├── docs/              # Project documentation
├── docker-compose.yml # Docker orchestration
└── README.md          # This file
```

---

## Documentation

- **docs/PRD.md** - Product Requirements Document (11 features, business model)
- **docs/TECH_STACK.md** - Complete technical architecture
- **docs/DESIGN_SYSTEM.md** - UI/UX specifications (60+ pages)
- **docs/ROADMAP.md** - 20-week development roadmap (9 sprints)
- **docs/CLAUDE.md** - Developer guide for Claude Code

---

## Features

### P0 - Launch Blockers (Free Tier)
- ✅ F1: Project Management - CRUD operations, multi-project support
- ✅ F2: PDF Upload & Vectorization - 7-stage pipeline, BGE-M3 embeddings
- ✅ F3: Category Tree Editor - Hierarchical organization, drag-drop
- ✅ F4: Semantic Search - Vector similarity, ranking, filtering

### P1 - High Priority (Paid Tiers)
- ✅ F5: Export Functionality - JSON, Markdown, CSV formats
- ✅ F6: Web Crawling - Firecrawl integration, scheduled jobs
- ✅ F10: AI-Powered Insights - Summaries, trends, citation network
- ✅ F11: RAG Chat Interface - Streaming chat with Claude API

### P2 - Professional Tier
- ✅ F7: Deep Web Search Agent - Google CSE integration, result synthesis
- ✅ F8: Technical Document Analysis - Equations, code blocks, diagrams

### P3 - Enterprise Tier
- ✅ F9: Agentic Workflow Orchestration - LangGraph, workflow templates

---

## Development Roadmap

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

See **docs/ROADMAP.md** for detailed sprint breakdowns.

---

## Testing

**Test Coverage Targets**:
- Backend: >80% (unit + integration)
- Frontend: >60% (component + E2E)

**Run tests**:
```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test

# E2E tests
npm run test:e2e
```

---

## Deployment

**MVP Phase** (Week 1-8):
- Platform: Railway.app Starter (~$20/mo)
- Database: PostgreSQL 16 with pgvector

**Production Phase** (Week 13-20):
- Platform: AWS (EC2, RDS, S3, CloudFront)
- Cost: ~$191/month

See **docs/ROADMAP.md** for complete deployment strategy.

---

## Contributing

This is a solo MVP project. Contributions will be considered post-launch.

---

## License

Proprietary - All rights reserved

---

## Contact

For inquiries: [contact information]

---

**Last Updated**: 2026-01-19
**Current Phase**: Sprint 0 (Foundation & Setup)
**Next Milestone**: Free Tier MVP (Week 8)
