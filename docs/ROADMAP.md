# ROADMAP.md

**KnowledgeTree Platform - Development Roadmap**

Version: 1.0
Last Updated: 2026-01-19
Duration: 20 weeks (5 months)
Team Size: 1 developer (MVP phase)

---

## Executive Summary

**Timeline**: 20 weeks from project start to production 1.0 launch

**Key Milestones**:
- **Week 8**: Free Tier MVP (Private Beta)
- **Week 10**: Starter Tier (Public Beta + Revenue)
- **Week 12**: Professional Tier (Premium Features)
- **Week 20**: Production 1.0 Launch (All Tiers)

**Development Approach**:
- 9 x 2-week sprints (Sprint 0-9)
- Agile methodology with strict P0/P1/P2 prioritization
- Leverage existing RAG-CREATOR codebase (proven PDF pipeline, BGE-M3 embeddings)
- Revenue-focused: Starter Tier in Sprint 4 for early validation

**Critical Success Factors**:
1. Solid foundation in Sprint 0 (database, auth, design system)
2. Copy RAG-CREATOR pipeline exactly - don't reinvent
3. Early user feedback (10 beta users by Week 8)
4. Strict scope management (P0 first, defer P2/P3 if needed)
5. Polish UI from day 1 (Inter font, pastel colors, no emojis, dark mode)

---

## Feature List

All features from PRD.md mapped to sprints:

| ID | Feature | Priority | Sprint | Week | Tier |
|----|---------|----------|--------|------|------|
| F1 | Project Management | P0 | Sprint 1 | 3-4 | Free |
| F2 | PDF Upload & Vectorization | P0 | Sprint 2 | 5-6 | Free |
| F3 | Category Tree Editor | P0 | Sprint 1 | 3-4 | Free |
| F4 | Semantic Search | P0 | Sprint 3 | 7-8 | Free |
| F5 | Export Functionality | P1 | Sprint 3 | 7-8 | Free |
| F10 | AI-Powered Insights | P1 | Sprint 5 | 11-12 | Starter+ |
| F11 | RAG Chat Interface | P1 | Sprint 4 | 9-10 | Starter+ |
| F6 | Web Crawling | P1 | Sprint 6 | 13-14 | Professional+ |
| F7 | Deep Web Search Agent | P2 | Sprint 7 | 15-16 | Professional+ |
| F8 | Technical Document Analysis | P2 | Sprint 7 | 15-16 | Professional+ |
| F9 | Agentic Workflow Orchestration | P3 | Sprint 8 | 17-18 | Enterprise |

---

## Dependency Graph

### Tier 0: Foundation (Sprint 0)
```
Database Schema + Migrations
         ↓
Authentication System
         ↓
    (Everything depends on these)
```

### Tier 1: Core MVP (Sprint 1)
```
F1: Project Management → Enables all project-scoped features
         ↓
F3: Category Tree Editor → Required for organizing documents
```

### Tier 2: RAG Pipeline (Sprint 2)
```
F2: PDF Upload & Vectorization
         ↓
    (Enables F4, F11)
```

### Tier 3: Search & Export (Sprint 3)
```
F4: Semantic Search ← F2 (needs embeddings)
F5: Export (independent)
         ↓
    FREE TIER COMPLETE
```

### Tier 4: Chat & Insights (Sprint 4-5)
```
F11: RAG Chat ← F4 (needs search results)
F10: AI Insights ← F2 (needs document corpus)
         ↓
    STARTER TIER COMPLETE
```

### Tier 5: Premium Features (Sprint 6-7)
```
F6: Web Crawling (independent)
         ↓
F7: Deep Web Search Agent ← F6, F11
F8: Technical Doc Analysis ← F2
         ↓
    PROFESSIONAL TIER COMPLETE
```

### Tier 6: Enterprise (Sprint 8)
```
F9: Agentic Workflows ← F6, F7, F8 (orchestrates all agents)
         ↓
    ENTERPRISE TIER COMPLETE
```

---

## Sprint Breakdown

### Sprint 0: Foundation & Setup (Week 1-2) - 10 days

**Goal**: Establish solid technical foundation and design system

**Tasks**:
- **Day 1-2**: Project setup
  - Initialize Vite + React 19 + TypeScript
  - FastAPI project structure
  - Docker Compose (PostgreSQL + pgvector, Redis)
  - CI/CD pipeline (GitHub Actions)

- **Day 3-4**: Database schema design
  - Design multi-tenant schema (project_id isolation)
  - Tables: users, projects, categories (tree), documents, chunks (with vector), conversations, messages, crawl_jobs, agent_workflows
  - Alembic migrations setup
  - Test migrations (up/down)

- **Day 5-6**: Authentication implementation
  - JWT authentication (access/refresh tokens)
  - User registration, login, logout
  - Password hashing (bcrypt)
  - Email verification (optional for MVP)

- **Day 7-8**: Design system setup
  - TailwindCSS configuration (pastel colors)
  - shadcn/ui installation
  - CSS variables (light/dark mode)
  - Inter font integration (Google Fonts)
  - Lucide React icons setup

- **Day 9-10**: Internationalization
  - react-i18next configuration
  - Polish translations (primary)
  - English translations (secondary)
  - Language switcher component
  - date-fns Polish locale

**Deliverables**:
- ✓ Working database with migrations
- ✓ Authentication flow (signup, login)
- ✓ Design system implemented
- ✓ i18n functional (Polish/English)

**Success Metrics**:
- Database schema supports multi-tenancy
- Auth tokens expire correctly (15m access, 7d refresh)
- Dark mode works across all components
- Polish UI is default language

**Documentation**:
- SETUP.md (installation guide)
- DATABASE.md (schema documentation)
- CONTRIBUTING.md (code conventions)

---

### Sprint 1: Project Management + Category Tree (Week 3-4) - 10 days

**Goal**: Implement F1 (Project Management) and F3 (Category Tree Editor)

**Tasks**:
- **Day 1-3**: F1 Project Management
  - Project CRUD API endpoints
  - Project list UI (create, edit, delete)
  - Project switching (dropdown in navbar)
  - Project settings (name, description, color)
  - PostgreSQL queries with project_id filtering

- **Day 4-7**: F3 Category Tree Editor
  - Copy Genetico category tree code
  - Adapt to KnowledgeTree (remove Genetico-specific logic)
  - Implement drag-and-drop (@dnd-kit)
  - Add/edit/delete categories
  - Undo/redo functionality
  - Tree validation (max depth 10, duplicate names)

- **Day 8-9**: Tree features
  - Category colors (8 pastel options)
  - Category icons (Lucide React)
  - Expand/collapse all nodes
  - Search categories (filter tree)
  - Category metadata (created_at, updated_at)

- **Day 10**: Polish & Testing
  - UI polish (animations, hover states)
  - Dark mode testing
  - Polish translation review
  - Integration testing (project → category flow)

**Deliverables**:
- ✓ Project management functional
- ✓ Category tree with drag-drop
- ✓ Undo/redo working
- ✓ Tree validation enforced

**Success Metrics**:
- User can create 3+ projects
- Category tree supports 10 levels
- Drag-drop works smoothly (60 fps)
- No data loss on undo/redo

**Documentation**:
- API.md (FastAPI endpoints)
- CATEGORY_TREE.md (tree operations)

---

### Sprint 2: PDF Upload & Vectorization (Week 5-6) - 10 days

**Goal**: Implement F2 (PDF Upload & Vectorization) - Copy RAG-CREATOR pipeline

**Tasks**:
- **Day 1-2**: File upload UI
  - Drag-and-drop PDF upload (react-dropzone)
  - File validation (PDF only, max 50MB)
  - Upload progress bar
  - Multi-file upload queue
  - Category assignment during upload

- **Day 3-5**: PDF processing backend
  - Copy RAG-CREATOR's PDF pipeline:
    - Stage 1: Validation (file type, size, corruption check)
    - Stage 2: Docling extraction (primary)
    - Stage 3: PyMuPDF fallback (if Docling fails)
    - Stage 4: Text chunking (1000 chars, 200 overlap)
  - Store document metadata (filename, size, page count, upload_date)
  - Background job processing (Celery or async tasks)

- **Day 6-8**: BGE-M3 embedding pipeline
  - Copy RAG-CREATOR's embedder.py
  - Load BAAI/bge-m3 model (1024 dimensions)
  - Batch embedding (32 chunks at a time)
  - Store embeddings in pgvector
  - Create IVFFlat index for vector similarity

- **Day 9-10**: Error handling & Status tracking
  - Document processing status (pending, processing, completed, failed)
  - Retry logic for failed documents
  - Error messages (corrupt PDF, extraction failed, etc.)
  - Processing queue UI (show status per document)

**Deliverables**:
- ✓ PDF upload with drag-drop
- ✓ 7-stage processing pipeline functional
- ✓ BGE-M3 embeddings stored in pgvector
- ✓ Error handling robust

**Success Metrics**:
- PDF processing success rate >95%
- Embedding generation time <30s per PDF (avg 10 pages)
- Vector search index created successfully
- No memory leaks during batch processing

**Documentation**:
- PDF_PIPELINE.md (processing stages)
- EMBEDDINGS.md (BGE-M3 configuration)

---

### Sprint 3: Semantic Search + Export → FREE TIER BETA (Week 7-8) - 10 days

**Goal**: Implement F4 (Semantic Search) and F5 (Export) - Launch Free Tier

**Tasks**:
- **Day 1-4**: F4 Semantic Search
  - Search UI (search bar, filters, results list)
  - Query embedding (BGE-M3 encode)
  - Vector similarity search (pgvector cosine distance)
  - Result ranking (top 20 results)
  - Category filtering (search within category)
  - Highlighting (show matching chunks)
  - Pagination (infinite scroll or load more)

- **Day 5-7**: F5 Export Functionality
  - Copy Genetico export utilities
  - Export formats:
    - JSON (full data structure)
    - Markdown (hierarchical documentation)
    - CSV (flat table for Excel)
  - Export UI (format selection, download button)
  - Export includes: categories, documents, search results

- **Day 8-9**: Integration testing
  - End-to-end flow: signup → create project → upload PDF → search → export
  - Test with diverse PDFs (text, scanned, multi-language)
  - Performance testing (search latency <200ms)
  - UI/UX polish (loading states, empty states)

- **Day 10**: Beta deployment
  - Deploy to Railway.app (Starter plan ~$20/mo)
  - Set up monitoring (error tracking, performance)
  - Create beta signup page
  - Invite 10 beta users
  - Collect feedback

**Deliverables**:
- ✓ Semantic search functional
- ✓ Export to JSON/MD/CSV
- ✓ Free Tier deployed
- ✓ 10 beta users invited

**Success Metrics**:
- Vector search precision >80% (tested with sample queries)
- Search latency <200ms (P95)
- Export files generated correctly
- Beta users upload 50+ PDFs total
- 200+ searches performed in first week

**Documentation**:
- USER_GUIDE.md (getting started)
- SEARCH_GUIDE.md (search best practices)
- EXPORT_GUIDE.md (format specifications)

---

### Sprint 4: RAG Chat Interface → STARTER TIER (Week 9-10) - 10 days

**Goal**: Implement F11 (RAG Chat) - Launch Starter Tier ($49/mo)

**Tasks**:
- **Day 1-3**: Chat UI
  - Chat interface (message list, input area)
  - Streaming response display (token-by-token)
  - Message formatting (Markdown support, code highlighting)
  - Conversation sidebar (list all conversations)
  - New conversation button
  - Framer Motion animations (smooth message appearance)

- **Day 4-6**: Claude API integration
  - Anthropic SDK setup
  - RAG pipeline:
    1. User query → BGE-M3 embedding
    2. Vector search top 5 relevant chunks
    3. Build context (system prompt + retrieved chunks + user query)
    4. Stream Claude 3.5 Sonnet response
  - Conversation context management (last 10 messages)
  - Error handling (rate limits, API errors)

- **Day 7-8**: Conversation features
  - Save conversation history (messages table)
  - Load past conversations
  - Delete conversations
  - Rename conversations
  - Export conversation (Markdown, PDF)

- **Day 9-10**: Monetization
  - Pricing page (Free vs Starter vs Pro vs Enterprise)
  - Stripe integration (subscription checkout)
  - User dashboard (current plan, usage limits)
  - Usage tracking (chat messages per month)
  - Upgrade/downgrade flows

**Deliverables**:
- ✓ RAG chat functional with streaming
- ✓ Stripe subscriptions live
- ✓ Starter Tier launched
- ✓ Public Beta open

**Success Metrics**:
- Chat response latency <2s (first token)
- Conversation context maintained across 10+ messages
- 5 paying Starter users ($245 MRR)
- Churn rate <20%

**Documentation**:
- CHAT_GUIDE.md (conversation management)
- PRICING.md (tier comparison)

---

### Sprint 5: AI-Powered Insights (Week 11-12) - 10 days

**Goal**: Implement F10 (AI Insights) - Enhance Professional Tier value

**Tasks**:
- **Day 1-3**: Document summaries
  - Auto-generate executive summary for uploaded PDFs
  - Claude API: "Summarize this document in 3-5 sentences"
  - Store summaries in database
  - Display in document list (hover tooltip)
  - Regenerate summary on demand

- **Day 4-6**: Trend detection
  - Analyze document corpus for patterns
  - Keyword extraction (TF-IDF or Claude-based)
  - Topic clustering (identify related documents)
  - Trend visualization (word cloud, bar chart)
  - Update trends weekly (background job)

- **Day 7-8**: Citation network
  - Detect cross-references between documents
  - Build citation graph (D3.js or Recharts)
  - Interactive visualization (click node → view document)
  - Citation analytics (most cited documents)

- **Day 9-10**: Insights dashboard
  - New "Insights" tab in project view
  - Summary cards (document count, keyword trends, top citations)
  - Export insights (PDF report)
  - Professional Tier differentiation (basic insights in Starter)

**Deliverables**:
- ✓ AI summaries for all documents
- ✓ Trend detection functional
- ✓ Citation network visualized
- ✓ Insights dashboard polished

**Success Metrics**:
- AI insights generated for 90% of documents
- Trend detection identifies 5+ keywords per project
- Citation graph renders <1s
- 3 Professional users ($447 MRR)
- Upsell rate from Starter >30%

**Documentation**:
- INSIGHTS_GUIDE.md (interpreting AI analysis)

---

### Sprint 6: Web Crawling (Week 13-14) - 10 days

**Goal**: Implement F6 (Web Crawling) - Professional Tier feature

**Tasks**:
- **Day 1-3**: Firecrawl integration
  - Firecrawl API setup (API key, rate limits)
  - URL validation (valid format, accessible)
  - Crawl job creation (single URL or sitemap)
  - JavaScript rendering (SPA support)
  - Respect robots.txt

- **Day 4-6**: Crawl job management
  - Job queue (pending, in_progress, completed, failed)
  - Background processing (async tasks)
  - Retry logic (max 3 retries)
  - Rate limiting (max 10 URLs/minute)
  - Cost tracking (Firecrawl API costs)

- **Day 7-8**: Content extraction
  - Extract main content (remove ads, nav, footer)
  - Convert HTML to Markdown
  - Chunking (same as PDFs: 1000/200)
  - Generate embeddings (BGE-M3)
  - Store in same chunks table (source_type: "web")

- **Day 9-10**: Crawl UI
  - New "Web Sources" tab
  - Add URL form (single or batch)
  - Crawl history (list all jobs)
  - Job status indicators (progress bar)
  - Scheduling (daily, weekly, monthly)

**Deliverables**:
- ✓ Firecrawl integration functional
- ✓ Web content ingested into RAG
- ✓ Crawl scheduling working
- ✓ Cost monitoring dashboard

**Success Metrics**:
- Web crawl success rate >85%
- Firecrawl cost <$0.10 per URL
- Scheduled crawls execute on time
- Professional Tier users crawl 100+ URLs

**Documentation**:
- CRAWLING_GUIDE.md (URL patterns, scheduling)
- FIRECRAWL.md (API configuration)

---

### Sprint 7: Advanced AI Features (Week 15-16) - 10 days

**Goal**: Implement F7 (Deep Web Search Agent) and F8 (Technical Document Analysis)

**Tasks**:
- **Day 1-4**: F7 Deep Web Search Agent
  - Google Custom Search API integration (or Serper.dev)
  - Query reformulation (Claude suggests better search terms)
  - Search result aggregation (top 10 URLs)
  - Auto-crawl search results (Firecrawl)
  - Result synthesis (Claude summarizes findings)
  - Agent UI (query input, result display, citations)

- **Day 5-7**: F8 Technical Document Analysis
  - Equation parsing (LaTeX detection, MathJax rendering)
  - Code block extraction (syntax highlighting, language detection)
  - Diagram recognition (OCR for images, bounding boxes)
  - Table extraction (preserve structure)
  - Technical glossary generation (Claude identifies terms)

- **Day 8-10**: Professional Tier polish
  - Advanced search filters (date range, file type, source)
  - Search analytics (popular queries, zero-result queries)
  - API access (REST API for Professional users)
  - Team features (invite collaborators, share projects)

**Deliverables**:
- ✓ Deep Web Search Agent functional
- ✓ Technical document parsing working
- ✓ API access enabled
- ✓ Team collaboration features

**Success Metrics**:
- Web search agent finds relevant results >80% accuracy
- Technical parsing extracts equations/code correctly
- API requests <500ms latency
- 5+ Professional users ($745 MRR)

**Documentation**:
- AGENT_GUIDE.md (using search agent)
- API_REFERENCE.md (REST API docs)

---

### Sprint 8: Enterprise Features (Week 17-18) - 10 days

**Goal**: Implement F9 (Agentic Workflow Orchestration) - Enterprise Tier

**Tasks**:
- **Day 1-5**: F9 Agentic Workflows
  - LangGraph integration (workflow engine)
  - Workflow templates:
    - Competitive Intelligence (crawl competitors → analyze → report)
    - Research Synthesis (search papers → extract findings → summarize)
    - Compliance Audit (scan documents → identify risks → generate report)
  - Workflow builder UI (drag-drop nodes, connect edges)
  - Workflow execution (run scheduled or on-demand)
  - Monitoring dashboard (execution logs, status, errors)

- **Day 6-8**: Team collaboration
  - User roles (owner, admin, editor, viewer)
  - Permission system (who can edit categories, upload docs, etc.)
  - Shared projects (multi-user access)
  - Activity log (audit trail: who did what when)
  - Notifications (email alerts for workflow completion)

- **Day 9-10**: Enterprise admin controls
  - SSO integration (SAML, OAuth)
  - Billing management (invoice history, payment methods)
  - Usage analytics (storage, API calls, costs)
  - White-labeling (custom logo, colors - optional)

**Deliverables**:
- ✓ Agentic workflows functional
- ✓ Team collaboration enabled
- ✓ Enterprise Tier launched
- ✓ SSO integration working

**Success Metrics**:
- Workflow execution success rate >90%
- 1 Enterprise user ($499 MRR)
- Team collaboration used by 5+ teams
- SSO login works with Google/Microsoft

**Documentation**:
- WORKFLOWS.md (creating workflows)
- TEAM_GUIDE.md (collaboration features)
- ENTERPRISE.md (SSO, billing)

---

### Sprint 9: Polish & Production Launch (Week 19-20) - 10 days

**Goal**: Production-ready 1.0 launch

**Tasks**:
- **Day 1-3**: Performance optimization
  - Bundle size reduction (code splitting, lazy loading)
  - Image optimization (WebP, lazy loading)
  - Database query optimization (indexes, caching)
  - CDN setup (CloudFront or Cloudflare)
  - Caching strategy (Redis for API responses)

- **Day 4-6**: Security audit
  - OWASP Top 10 review
  - SQL injection prevention
  - XSS protection
  - CSRF tokens
  - Rate limiting (API endpoints, login attempts)
  - Penetration testing (manual or automated)
  - Dependency vulnerability scan (npm audit, Snyk)

- **Day 7-8**: Documentation finalization
  - User guides (comprehensive tutorials)
  - API documentation (Swagger/OpenAPI)
  - Admin documentation (deployment, scaling)
  - Video tutorials (getting started, advanced features)
  - FAQ page
  - Knowledge base (common issues, solutions)

- **Day 9-10**: Production deployment & Launch
  - Migrate to AWS (EC2, RDS, S3, CloudFront)
  - Set up monitoring (CloudWatch, Sentry, LogRocket)
  - Database backups (daily automated)
  - Disaster recovery plan
  - Load testing (1000 concurrent users)
  - Production launch announcement
  - Marketing campaign (Product Hunt, HN, LinkedIn)

**Deliverables**:
- ✓ Performance optimized (page load <2s)
- ✓ Security hardened (zero critical vulnerabilities)
- ✓ Documentation complete
- ✓ Production deployed on AWS
- ✓ 1.0 officially launched

**Success Metrics**:
- Test coverage >80% backend, >60% frontend
- Uptime >99.5% in final 2 weeks
- 100 total users (70 free, 20 starter, 8 pro, 2 enterprise)
- $2,000 MRR at launch
- NPS score >50
- Page load time <2s (3G network)

**Documentation**:
- DEPLOYMENT.md (production setup)
- SECURITY.md (security measures)
- SCALING.md (how to scale)

---

## Milestones & Release Strategy

### Milestone 1: Foundation Complete (Week 2)
- **Deliverable**: Database, Auth, Design System functional
- **Gate**: All migrations work, dark mode works, Polish UI default
- **Risk**: If auth is buggy, delay Sprint 1 by 2-3 days

### Milestone 2: Free Tier MVP (Week 8) - CRITICAL
- **Deliverable**: F1, F2, F3, F4, F5 functional → Private Beta
- **Gate**: 10 beta users can upload PDFs and search successfully
- **Risk**: If search quality is poor, iterate for 1 week before public beta
- **Marketing**: Email beta users, gather feedback

### Milestone 3: Starter Tier (Week 10) - REVENUE VALIDATION
- **Deliverable**: F11 RAG Chat + Stripe integration → Public Beta
- **Gate**: 5 paying users, churn <20%
- **Risk**: If no conversions, revisit pricing or add more value
- **Marketing**: Launch on Product Hunt, HN, LinkedIn

### Milestone 4: Professional Tier (Week 12)
- **Deliverable**: F6, F10 → Professional Tier value clear
- **Gate**: 3 Professional users, upsell rate >30%
- **Risk**: If upsell is low, add more Professional features
- **Marketing**: Case studies, testimonials

### Milestone 5: Enterprise Tier (Week 18)
- **Deliverable**: F7, F8, F9 → Enterprise features complete
- **Gate**: 1 Enterprise user, team collaboration working
- **Risk**: Enterprise sales cycle is long (may take 3-6 months)
- **Marketing**: Direct sales outreach, webinars

### Milestone 6: Production 1.0 (Week 20) - OFFICIAL LAUNCH
- **Deliverable**: All features (F1-F11), production-ready
- **Gate**: >99.5% uptime, zero critical bugs, $2,000 MRR
- **Risk**: Last-minute bugs could delay launch by 1-2 weeks
- **Marketing**: Major launch campaign (PR, ads, partnerships)

---

## Risk Management

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| BGE-M3 CPU performance too slow | Medium | High | Document GPU upgrade path ($50-100/mo), benchmark early |
| PostgreSQL pgvector scaling issues | Low | High | Use IVFFlat indexing, monitor query performance |
| Firecrawl API costs exceed budget | Medium | Medium | Implement rate limiting, cost alerts, usage caps |
| Claude API rate limits | Low | Medium | Implement streaming, retry logic, caching |
| Docker setup complexity | Low | Low | Copy RAG-CREATOR docker-compose.yml exactly |

### Business Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| No beta user signups | Low | High | Reach out to professional networks, offer incentives |
| No Starter Tier conversions | Medium | High | Revisit pricing, add free trial, improve onboarding |
| High churn rate (>30%) | Medium | High | User interviews, improve features, reduce bugs |
| Slow Enterprise sales | High | Medium | Focus on Starter/Pro tiers for revenue, Enterprise is bonus |

### Schedule Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Solo developer burnout | Medium | High | Realistic sprint planning, 2-week buffer built in |
| Sprint scope creep | High | Medium | Strict P0/P1/P2 prioritization, defer non-critical features |
| Dependencies on external APIs | Medium | Medium | Fallback strategies, test APIs early |
| Beta feedback requires major pivot | Low | High | Launch MVP quickly (Week 8), iterate based on feedback |

---

## Success Metrics & KPIs

### Technical KPIs (Track Weekly)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **PDF Processing Success Rate** | >95% | Processed / Total Uploaded |
| **Vector Search Precision** | >80% | Relevant Results / Total Results (manual review) |
| **Chat Response Latency** | <2s | Time to First Token (P95) |
| **Search Latency** | <200ms | Query to Results (P95) |
| **Uptime** | >99.5% | Monitoring (Sentry, CloudWatch) |
| **Error Rate** | <0.5% | 5xx Errors / Total Requests |
| **Page Load Time** | <2s | Lighthouse score (3G network) |

### User KPIs (Track Weekly)

| Metric | Week 8 Target | Week 12 Target | Week 20 Target |
|--------|---------------|----------------|----------------|
| **Total Users** | 10 (beta) | 50 | 100 |
| **Active Users (WAU)** | 8 | 35 | 70 |
| **Documents Uploaded** | 50 | 500 | 2,000 |
| **Searches Performed** | 200 | 2,000 | 10,000 |
| **Chat Conversations** | 0 | 150 | 1,000 |
| **Avg Session Time** | >10 min | >15 min | >20 min |

### Business KPIs (Track Weekly)

| Metric | Week 10 Target | Week 12 Target | Week 20 Target |
|--------|----------------|----------------|----------------|
| **MRR (Monthly Recurring Revenue)** | $245 (5 Starter) | $890 | $2,000 |
| **Free Users** | 10 | 30 | 70 |
| **Starter Users ($49/mo)** | 5 | 10 | 20 |
| **Professional Users ($149/mo)** | 0 | 3 | 8 |
| **Enterprise Users ($499/mo)** | 0 | 0 | 2 |
| **Churn Rate** | <20% | <15% | <10% |
| **Upsell Rate (Free→Starter)** | N/A | >20% | >30% |
| **LTV (Lifetime Value)** | $294 (6mo avg) | $1,788 (1yr avg) | $2,500 |
| **CAC (Customer Acquisition Cost)** | $0 (beta) | <$50 | <$100 |

---

## Cost Projections

### Infrastructure Costs (Monthly)

| Phase | Platform | Services | Cost | Users |
|-------|----------|----------|------|-------|
| **MVP (Week 1-8)** | Railway.app | FastAPI, PostgreSQL, Redis | $20 | 50 |
| **Beta (Week 9-12)** | Railway.app Pro | 2x FastAPI, PostgreSQL Pro, Redis | $70 | 300 |
| **Production (Week 13-20)** | AWS | EC2 (t3.medium x2), RDS (db.t3.micro), S3, CloudFront, ALB | $191 | 1,000-2,000 |

### Variable Costs (Per User Per Month)

| Tier | Claude API | Firecrawl | Total Variable | Margin |
|------|------------|-----------|----------------|--------|
| **Free** | $0 | $0 | $0.10 (infrastructure) | N/A |
| **Starter** ($49) | $2 (50 chat msgs) | $0 | $3 | $46 (94%) |
| **Professional** ($149) | $5 (150 msgs) | $3 (30 URLs) | $8 | $141 (95%) |
| **Enterprise** ($499) | $15 (500 msgs) | $10 (100 URLs) | $25 | $474 (95%) |

### Break-even Analysis

**Fixed Costs**: $191/month (AWS infrastructure)

**Break-even Scenarios**:
- 4 Starter users ($196 revenue) → $5 profit
- 2 Professional users ($298 revenue) → $107 profit
- 1 Enterprise user ($499 revenue) → $308 profit

**Target Month 3** (Week 12):
- Revenue: $890 MRR (10 Starter + 3 Pro)
- Costs: $70 (infrastructure) + $110 (variable) = $180
- Profit: $710 (80% margin)

**Target Launch** (Week 20):
- Revenue: $2,000 MRR (20 Starter + 8 Pro + 2 Enterprise)
- Costs: $191 (infrastructure) + $356 (variable) = $547
- Profit: $1,453 (73% margin)

---

## Critical Success Factors

### 1. Leverage Existing Code (HIGH PRIORITY)
- **RAG-CREATOR**: Copy PDF pipeline, BGE-M3 embeddings, pgvector setup exactly as-is
- **Genetico**: Reuse category tree editor, export utilities, drag-drop logic
- **Don't Reinvent**: If it works in RAG-CREATOR, copy it. Focus on multi-tenancy and UI polish.

### 2. Strict Scope Management
- **P0 Features First**: F1, F2, F3, F4 must ship by Week 8 (Free Tier)
- **Defer P2/P3**: If sprints slip, cut F7, F8, F9 (Enterprise features)
- **No Scope Creep**: Resist adding "nice to have" features during development

### 3. Early User Feedback
- **Beta Users by Week 8**: Invite 10 real users to test Free Tier
- **Iterate Based on Feedback**: Spend Week 9 fixing critical issues before Starter Tier launch
- **User Interviews**: Talk to beta users weekly, understand pain points

### 4. Design System from Day 1
- **Polish UI Requirements**: Inter font, pastel colors, no emojis, dark mode
- **Implement in Sprint 0**: Don't defer design system - it's foundational
- **Consistency**: Use shadcn/ui components, enforce design tokens

### 5. Revenue Focus
- **Starter Tier in Sprint 4**: Revenue validation is critical
- **Stripe Integration Early**: Don't delay monetization
- **Monitor Metrics**: Track MRR, churn, upsell rate weekly

### 6. Documentation Parallel to Development
- **Don't Defer Docs**: Write user guides, API docs, setup guides as you build
- **Video Tutorials**: Record demos while features are fresh
- **Knowledge Base**: Anticipate user questions, create FAQ

### 7. Test with Real Data
- **Diverse PDFs**: Test with 50+ PDFs (text, scanned, multi-language, large files)
- **Search Quality**: Manually review top 20 search results for 10 queries
- **Performance**: Load test with 1000 concurrent users before launch

### 8. Monitor Costs
- **Claude API**: Track usage per user, implement caching to reduce costs
- **Firecrawl**: Set rate limits, alert when costs exceed $100/week
- **Infrastructure**: Monitor AWS costs daily, optimize before scaling

---

## Next Actions (Immediate)

### Week 1 (Starting Now)

**Day 1-2**:
1. Set up GitHub repository (mono-repo: frontend + backend)
2. Initialize Vite + React 19 + TypeScript
3. Initialize FastAPI project structure
4. Create Docker Compose (PostgreSQL + pgvector, Redis)
5. Set up CI/CD (GitHub Actions for linting, type-checking)

**Day 3-4**:
1. Design database schema (all tables, relationships)
2. Create Alembic migrations (initial schema)
3. Test migrations (up/down, rollback)
4. Document schema in DATABASE.md

**Day 5-6**:
1. Implement JWT authentication (backend)
2. User registration, login, logout endpoints
3. Password hashing (bcrypt)
4. Test auth flow (Postman or pytest)

**Day 7-8**:
1. Set up TailwindCSS (pastel color palette)
2. Install shadcn/ui (Button, Input, Dialog, Tree)
3. Implement dark mode (ThemeProvider)
4. Integrate Inter font (Google Fonts)
5. Install Lucide React icons

**Day 9-10**:
1. Configure react-i18next
2. Create Polish translations (common.json, editor.json)
3. Create English translations
4. Implement language switcher
5. Test i18n (switch languages, check all UI text)

**Deliverable**: Foundation complete, ready for Sprint 1

---

## Appendix: Technology Stack Reference

### Frontend
- React 19 + TypeScript 5.3+
- Vite 6.0+ (build tool)
- TailwindCSS 3.4+ (styling)
- shadcn/ui (components)
- Inter font (typography)
- Lucide React (icons)
- Framer Motion (animations)
- react-i18next (i18n)
- @dnd-kit (drag-drop)

### Backend
- FastAPI 0.109.0+ (Python 3.11+)
- PostgreSQL 16 + pgvector 0.7
- SQLAlchemy 2.0+ (async ORM)
- Alembic (migrations)
- Pydantic (validation)
- Celery or async tasks (background jobs)

### RAG & AI
- BGE-M3 (BAAI/bge-m3) - 1024 dimensions
- FlagEmbedding (model loading)
- PyTorch (inference)
- Claude 3.5 Sonnet (Anthropic API)
- Firecrawl API (web crawling)
- Google Custom Search API or Serper.dev (web search)

### PDF Processing
- Docling (primary)
- PyMuPDF (fallback)
- Chunking: 1000 chars, 200 overlap

### Infrastructure
- Railway.app (MVP, Beta)
- AWS (Production: EC2, RDS, S3, CloudFront, ALB)
- Docker + Docker Compose
- GitHub Actions (CI/CD)
- Sentry (error tracking)
- CloudWatch (monitoring)

---

**End of Roadmap**

For detailed design specifications, see DESIGN_SYSTEM.md.
For technical architecture, see TECH_STACK.md.
For product requirements, see PRD.md.
For development guide, see CLAUDE.md (to be updated).
