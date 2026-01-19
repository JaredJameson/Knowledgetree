# Product Requirements Document (PRD)
## KnowledgeTree - AI-Powered Knowledge Repository Builder

**Version**: 1.0
**Date**: January 19, 2026
**Status**: Draft for Review

---

## Executive Summary

KnowledgeTree is an AI-powered knowledge repository builder that enables users to create structured, searchable knowledge bases from multiple sources. The platform combines automated web crawling, PDF processing, and RAG (Retrieval-Augmented Generation) technology to transform unstructured content into organized, queryable knowledge repositories.

### Product Vision

To democratize competitive intelligence and knowledge management by providing an affordable, AI-powered platform that automatically structures and indexes information from any source, enabling SMBs and product teams to access enterprise-grade knowledge management capabilities.

### Target Market

- **Primary**: Product managers conducting competitive analysis
- **Secondary**: SMB teams needing knowledge management solutions
- **Tertiary**: Research teams building domain-specific knowledge bases

### Value Proposition

**"From Chaos to Clarity in Minutes"** - Transform scattered information across websites, PDFs, and documents into a structured, AI-searchable knowledge base without manual organization.

---

## Product Goals & Success Metrics

### Business Objectives

1. **Revenue Target**: $169K Year 1 → $2M+ Year 3
2. **User Acquisition**: 500 free users → 150 paid subscribers (Year 1)
3. **Retention**: 85% MRR retention through demonstrated ROI
4. **Market Position**: Top 3 in competitive intelligence tools under $500/mo

### Key Performance Indicators (KPIs)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Sign-up Conversion | 12% | Visitors → Free accounts |
| Free→Paid Conversion | 30% | Free users → Paid subscribers |
| Avg. Processing Time | <15 min | PDF/website → Searchable KB |
| Search Accuracy | >85% | Relevant results in top 5 |
| User Retention (90d) | >70% | Active users after 90 days |
| NPS Score | >50 | User satisfaction |

---

## User Personas

### Persona 1: "Competitive Intelligence Manager" - Primary

**Profile**:
- **Role**: Product Manager at SaaS company (10-100 employees)
- **Age**: 28-42
- **Technical Level**: Moderate (comfortable with web tools)
- **Budget Authority**: $50-500/month for tools

**Pain Points**:
- Manually tracking 5-10 competitors across websites, blogs, docs
- Spending 4-8 hours/week copying information to Notion
- Missing important updates and feature launches
- Can't afford enterprise tools like Crayon ($34K/year)

**Jobs to Be Done**:
1. Monitor competitor product pages weekly
2. Track feature announcements and pricing changes
3. Generate competitive comparison reports for stakeholders
4. Search competitor documentation for specific features

**Success Criteria**:
- Reduce competitive research time from 8h/week → 1h/week
- Never miss major competitor updates
- Generate reports in <10 minutes instead of 2 hours

### Persona 2: "Knowledge Architect" - Secondary

**Profile**:
- **Role**: Operations Manager or Knowledge Manager
- **Age**: 30-50
- **Technical Level**: Low-Moderate
- **Budget Authority**: $100-300/month

**Pain Points**:
- Building internal knowledge bases is time-consuming
- Company documentation scattered across Google Drive, PDFs, wikis
- Onboarding new employees takes weeks due to information fragmentation
- Search functionality in existing tools is poor

**Jobs to Be Done**:
1. Centralize company knowledge from multiple sources
2. Make information easily searchable by employees
3. Keep knowledge base updated as documents change
4. Enable natural language queries ("How do we handle X?")

**Success Criteria**:
- Reduce onboarding time from 4 weeks → 2 weeks
- Employees find answers in <2 minutes instead of asking colleagues
- Knowledge base covers 80%+ of common questions

### Persona 3: "Research Analyst" - Tertiary

**Profile**:
- **Role**: Market Researcher or Academic Researcher
- **Age**: 25-45
- **Technical Level**: High (comfortable with APIs, technical tools)
- **Budget Authority**: $50-200/month

**Pain Points**:
- Processing dozens of research papers and technical documents
- Manual extraction of key information for literature reviews
- Difficult to search across multiple PDF documents
- Need embeddings for custom RAG applications

**Jobs to Be Done**:
1. Extract and structure data from technical documents
2. Build domain-specific knowledge bases for analysis
3. Export embeddings for custom AI applications
4. Search across hundreds of documents instantly

**Success Criteria**:
- Process 50+ PDFs in under 1 hour
- Find relevant passages across all documents in seconds
- Export clean embeddings for downstream AI tasks

---

## Product Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      KnowledgeTree Platform                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐         ┌──────────────────┐             │
│  │   React 19 UI    │────────▶│  FastAPI Backend │             │
│  │   (Category      │         │  (Orchestration) │             │
│  │    Editor)       │         │                  │             │
│  └──────────────────┘         └──────────┬───────┘             │
│                                           │                      │
│                                           ▼                      │
│                              ┌─────────────────────┐            │
│                              │  Agentic Workflow   │            │
│                              │    Orchestrator     │            │
│                              └──────────┬──────────┘            │
│                                         │                        │
│         ┌───────────────────────────────┼───────────────┐       │
│         ▼                               ▼               ▼       │
│  ┌─────────────┐             ┌──────────────┐   ┌─────────┐   │
│  │  Firecrawl  │             │  RAG-CREATOR │   │  Claude │   │
│  │   Crawler   │             │   Pipeline   │   │   API   │   │
│  │  (Web Data) │             │  (PDF→Vec)   │   │  (LLM)  │   │
│  └─────────────┘             └──────┬───────┘   └─────────┘   │
│                                     │                           │
│                                     ▼                           │
│                          ┌─────────────────────┐               │
│                          │  PostgreSQL + pgv   │               │
│                          │  (Vector Storage)   │               │
│                          │  BGE-M3 Embeddings  │               │
│                          └─────────────────────┘               │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Integration Strategy

**Phase 1: Core Integration** (Weeks 1-4)
1. Migrate Genetico category editor to KnowledgeTree branding
2. Integrate RAG-CREATOR backend as microservice
3. Add project management layer on top of category tree
4. Implement user authentication and project isolation

**Phase 2: Feature Parity** (Weeks 5-8)
1. PDF upload interface with RAG-CREATOR pipeline
2. Basic vector search UI
3. Free tier: PDF processing with embedding model selection
4. Export functionality (embeddings, JSON, CSV)

**Phase 3: Premium Features** (Weeks 9-16)
1. Firecrawl integration for web crawling
2. Web search agent for deep research
3. Agentic workflow orchestration
4. AI-powered insights and summaries

---

## Feature Requirements

### Core Features (MVP - Free Tier)

#### F1: Project Management
**Priority**: P0 (Launch Blocker)
**User Story**: As a user, I want to create multiple knowledge base projects so that I can organize different research topics separately.

**Requirements**:
- Create, rename, delete projects
- Each project has independent category tree
- Each project has independent vector database namespace
- Dashboard showing all projects with stats (docs, chunks, size)
- Last modified timestamp and status indicator

**Acceptance Criteria**:
- User can create unlimited projects
- Projects are isolated (no data leakage)
- Deleting project removes all associated data
- Projects load in <1 second

---

#### F2: PDF Upload & Vectorization
**Priority**: P0 (Launch Blocker)
**User Story**: As a user, I want to upload PDF documents and have them automatically vectorized so that I can search them semantically.

**Requirements**:
- Drag-and-drop PDF upload interface
- Support files up to 100MB
- Multiple embedding model options:
  - **BGE-M3** (1024 dim, free, local) - default
  - **BGE-Large-EN** (1024 dim, English-only)
  - **OpenAI text-embedding-3-small** (1536 dim, paid API)
  - **OpenAI text-embedding-3-large** (3072 dim, premium)
- Real-time progress tracking via SSE
- Processing pipeline stages visible to user
- Error handling with retry capability

**Technical Specs**:
- Reuse RAG-CREATOR pipeline exactly as-is
- Processing stages: Validate → Split → Extract → Chunk → Embed → Store → Index
- Chunk size: 1000 chars, overlap: 200 chars (configurable)
- Batch embedding: 32 texts at a time
- PostgreSQL storage with pgvector

**Acceptance Criteria**:
- 100 page PDF processes in <5 minutes (BGE-M3, CPU)
- Progress updates every 2 seconds
- Success rate >95% for standard PDFs
- Failed uploads show clear error message

---

#### F3: Category Tree Editor (Inherited from Genetico)
**Priority**: P0 (Launch Blocker)
**User Story**: As a user, I want to organize my knowledge base hierarchically so that I can structure information logically.

**Requirements**:
- All existing Genetico features:
  - Hierarchical tree with unlimited depth
  - Drag-and-drop reorganization
  - Add/edit/delete categories
  - Undo/redo functionality
  - Search/filter tree
  - Expand/collapse nodes
- **New**: Link documents to categories
- **New**: Link chunks to categories
- **New**: Auto-suggest categories based on document content (AI)

**Acceptance Criteria**:
- All Genetico tests pass
- Can assign multiple documents to one category
- Tree updates in real-time when documents added

---

#### F4: Semantic Search (Basic)
**Priority**: P0 (Launch Blocker)
**User Story**: As a user, I want to search my knowledge base using natural language so that I can find relevant information quickly.

**Requirements**:
- Search input with natural language queries
- Vector similarity search using pgvector cosine distance
- Return top 10 results with:
  - Chunk text (with highlighting)
  - Source document name
  - Similarity score
  - Category breadcrumb
- Click result to view full context
- Search within specific category (filter)

**Technical Specs**:
- Query embedding using same model as documents
- pgvector IVFFlat index for performance
- Search response time <500ms for 10K chunks

**Acceptance Criteria**:
- Finds relevant results for >85% of test queries
- Search results appear in <1 second
- No false positives in top 5 results

---

#### F5: Export Functionality
**Priority**: P1 (High Priority)
**User Story**: As a user, I want to export my knowledge base in various formats so that I can use it in other tools.

**Requirements**:
- Export formats:
  - **JSON**: Full project data with embeddings
  - **CSV**: Chunks with metadata (for Excel analysis)
  - **Markdown**: Human-readable documentation
  - **JSONL**: Embeddings only (for RAG frameworks)
- Export scope:
  - Entire project
  - Specific category subtree
  - Search results
- Include metadata: source, category, timestamps

**Acceptance Criteria**:
- 10K chunk export completes in <30 seconds
- Exported files are valid and importable
- Embeddings maintain precision (no data loss)

---

### Premium Features (Paid Tiers)

#### F6: Web Crawling (Starter Tier)
**Priority**: P1 (High Priority)
**User Story**: As a competitive intelligence manager, I want to crawl competitor websites automatically so that I can build a searchable knowledge base of their content.

**Requirements**:
- Enter website URL
- Configure crawling:
  - Max pages (10, 50, 100, 500, unlimited)
  - Max depth (1-5 levels)
  - Include/exclude URL patterns
  - Respect robots.txt (optional)
  - JavaScript rendering (yes/no)
- Firecrawl API integration
- Real-time crawling progress
- Preview crawled pages before processing
- Schedule recurring crawls (daily, weekly, monthly)

**Technical Specs**:
- Firecrawl API at $1/1000 pages
- LLM-ready markdown output
- Store raw HTML + extracted markdown
- Automatic change detection (diff)

**Acceptance Criteria**:
- 50 page website crawls in <5 minutes
- JavaScript-heavy sites render correctly
- Crawl resumes after interruption
- Change detection shows new/modified content

---

#### F7: Deep Web Search Agent (Professional Tier)
**Priority**: P2 (Medium Priority)
**User Story**: As a researcher, I want an AI agent to search the web for specific topics and build a knowledge base so that I don't have to manually research.

**Requirements**:
- Natural language research query
  - Example: "Find all information about MongoDB vector search capabilities"
- Agent workflow:
  1. Generate search terms from query
  2. Perform web searches (Google/Bing API)
  3. Visit top 20 results
  4. Extract relevant content
  5. Filter out low-quality sources
  6. Crawl linked pages if relevant
  7. Summarize findings
- Progress tracking with agent reasoning visible
- User can approve/reject sources during research
- Agent suggests follow-up research directions

**Technical Specs**:
- Claude API for agent reasoning
- WebSearch integration (Google Custom Search API)
- Firecrawl for content extraction
- Recursive search up to 3 levels deep
- Budget controls (max API calls, max pages)

**Acceptance Criteria**:
- Completes research query in <10 minutes
- Finds >80% of relevant public information
- Filters out 90%+ irrelevant results
- Final knowledge base has 30-100 high-quality chunks

---

#### F8: Technical Document Analysis (Professional Tier)
**Priority**: P2 (Medium Priority)
**User Story**: As a technical analyst, I want to extract structured data from technical documents (API docs, spec sheets, research papers) so that I can compare products systematically.

**Requirements**:
- Upload technical documents (PDF, HTML, MD)
- AI agent extracts:
  - Feature lists
  - Technical specifications
  - API endpoints and parameters
  - Performance benchmarks
  - Pricing information
- Output to structured JSON
- Populate comparison matrices automatically
- Link to source chunks for verification

**Technical Specs**:
- Claude API with custom system prompts
- Schema definition for extraction
- Validation rules for data quality
- Human-in-the-loop for ambiguous cases

**Acceptance Criteria**:
- Extracts 90%+ of features from standard docs
- Structured data is 95% accurate
- Ambiguous cases flagged for review
- Processing time <2 minutes per document

---

#### F9: Agentic Workflow Orchestration (Enterprise Tier)
**Priority**: P3 (Nice to Have)
**User Story**: As a power user, I want to create custom workflows combining multiple AI agents so that I can automate complex research processes.

**Requirements**:
- Visual workflow builder (nodes + edges)
- Agent types:
  - Web Crawler Agent
  - Search Agent
  - Extraction Agent
  - Summarization Agent
  - Comparison Agent
- Trigger conditions:
  - Manual
  - Scheduled (cron)
  - Webhook
  - Data change detected
- Workflow state management
- Error handling and retries
- Output routing to categories

**Technical Specs**:
- Workflow DAG execution engine
- Agent communication via message queue
- State persistence in PostgreSQL
- Webhook support for integrations

**Acceptance Criteria**:
- User can create 5-step workflow in <10 minutes
- Workflows execute reliably (99% success rate)
- Failures gracefully handled with notifications
- Execution logs available for debugging

---

#### F10: AI-Powered Insights (All Paid Tiers)
**Priority**: P1 (High Priority)
**User Story**: As a product manager, I want AI-generated insights from my knowledge base so that I can quickly understand competitive positioning without reading everything.

**Requirements**:
- Auto-generate insights:
  - **Competitive Comparison Matrix**: Compare features across competitors
  - **Trend Analysis**: Identify common themes and changes over time
  - **Gap Analysis**: Find what competitors have that you don't
  - **Summary Reports**: Executive summaries of knowledge base
- Insights dashboard with visualizations
- Refresh insights on-demand
- Export insights to presentation format

**Technical Specs**:
- Claude API for analysis
- RAG retrieval for context
- Structured output (JSON)
- Visualization with Chart.js or Recharts

**Acceptance Criteria**:
- Comparison matrix generated in <60 seconds
- Insights are 90%+ accurate vs manual analysis
- Visualizations are presentation-ready
- Updates reflect latest data within 5 minutes

---

#### F11: RAG Chat Interface (All Paid Tiers)
**Priority**: P1 (High Priority)
**User Story**: As a user, I want to ask questions about my knowledge base in natural language so that I can get instant answers.

**Requirements**:
- Chat interface with conversation history
- Natural language questions
- AI retrieves relevant chunks from knowledge base
- Answers cite sources with links
- Conversation context maintained (follow-up questions)
- Share conversations with team members

**Technical Specs**:
- RAG pattern: Query → Embed → Search → Retrieve → Generate
- Claude API for response generation
- Context window: 5 previous messages
- Source citations inline and as footnotes

**Acceptance Criteria**:
- Answers appear in <3 seconds
- 85%+ of answers are accurate and helpful
- Sources are always cited
- Conversations feel natural (handles follow-ups)

---

## User Flows

### Flow 1: First-Time User Onboarding (Free Tier)

**Goal**: Get user from signup to first searchable knowledge base in <10 minutes

**Steps**:
1. **Landing Page** → Sign up with email
2. **Email Verification** → Click link, confirm account
3. **Welcome Screen**:
   - Brief video: "What is KnowledgeTree?" (30 seconds)
   - Call to action: "Create Your First Knowledge Base"
4. **Project Creation**:
   - Enter project name (e.g., "Competitor Analysis")
   - Optional: Select template (pre-built category structure)
5. **Upload PDF**:
   - Drag-and-drop interface with sample PDF offered
   - Select embedding model (BGE-M3 recommended for free tier)
   - Click "Process Document"
6. **Processing Screen**:
   - Real-time progress bar
   - Stage descriptions
   - Estimated time remaining
7. **Success Screen**:
   - "Your knowledge base is ready!"
   - Quick tour of features:
     - Search
     - Category tree
     - Export
   - Prompt: "Try searching for [suggested query based on document]"
8. **First Search**:
   - Enter natural language query
   - See results with highlighting
   - Click result to view context
9. **Upgrade Prompt**:
   - "Want to crawl websites too? Upgrade to Starter for $49/mo"

**Success Metrics**:
- 80% of signups complete flow to first search
- Average time to first search: <8 minutes
- 30% click "Upgrade" within first session

---

### Flow 2: Competitive Intelligence Workflow (Paid User)

**Goal**: Monitor competitor websites and get weekly insights

**Steps**:
1. **Create Project**: "Acme Corp Competitive Intelligence"
2. **Add Competitors**:
   - Enter competitor URLs (e.g., competitor1.com, competitor2.com)
   - Configure crawling: max pages = 50, depth = 2, enable JS rendering
   - Schedule: Weekly on Mondays at 9 AM
3. **Initial Crawl**:
   - System crawls all competitors (takes 10-15 minutes)
   - User receives email: "Initial crawl complete"
4. **Organize in Categories**:
   - System suggests categories based on site structure
   - User refines category tree (drag-and-drop)
   - Link crawled pages to categories
5. **Generate Insights**:
   - Click "Generate Competitive Matrix"
   - AI compares features across competitors
   - View matrix with green/red indicators (we have / we don't have)
6. **Weekly Updates**:
   - Monday 9 AM: Automated recrawl
   - System detects changes (new pages, modified content)
   - Email notification: "3 changes detected at Competitor1"
   - User reviews changes in diff view
7. **Export Report**:
   - Click "Generate Report"
   - AI creates executive summary
   - Download as PDF or share link

**Success Metrics**:
- 70% of users set up recurring crawls
- 60% generate insights weekly
- 50% export reports monthly

---

### Flow 3: Research Knowledge Base Building (Professional User)

**Goal**: Build comprehensive knowledge base on a technical topic

**Steps**:
1. **Create Project**: "MongoDB Vector Search Research"
2. **Upload Documents**:
   - Drag-and-drop 10 PDFs (research papers, technical docs)
   - Select BGE-M3 for multilingual support
   - Batch process all documents
3. **Launch Deep Web Search**:
   - Query: "Find all information about MongoDB vector search and Atlas Vector Search"
   - Agent workflow visible:
     - Searching Google for "MongoDB vector search"
     - Visiting mongodb.com/docs/atlas/vector-search
     - Crawling linked pages
     - Found 15 relevant pages
     - Extracting content...
   - User approves sources
4. **Technical Document Analysis**:
   - Upload MongoDB Atlas pricing page
   - Agent extracts: features, limits, pricing tiers
   - Data populates structured comparison table
5. **Organize Knowledge**:
   - Auto-generated categories: Architecture, API, Pricing, Benchmarks
   - User refines structure
6. **RAG Chat**:
   - Ask: "What are the performance characteristics of Atlas Vector Search?"
   - AI answers with citations from multiple sources
   - Follow-up: "How does it compare to Pinecone?"
7. **Export for Analysis**:
   - Export embeddings as JSONL
   - Export structured data as JSON
   - Use in custom RAG application

**Success Metrics**:
- 80% of Professional users use deep web search
- 70% use technical document analysis
- 50% export embeddings for custom apps

---

## Technical Requirements

### Non-Functional Requirements

#### Performance
- **Response Time**: <1s for UI interactions, <3s for search queries
- **Processing Speed**:
  - 100-page PDF: <5 minutes (BGE-M3, CPU)
  - 50-page website: <10 minutes (Firecrawl)
  - Deep web search: <15 minutes (20 pages)
- **Scalability**: Support 10K projects, 1M chunks per project
- **Concurrent Users**: 100 simultaneous users without degradation

#### Reliability
- **Uptime**: 99.5% availability (43.8 hours downtime/year)
- **Data Durability**: 99.99% (PostgreSQL with daily backups)
- **Error Handling**: All errors logged, user-facing error messages
- **Recovery**: Automatic retry for transient failures (3 attempts)

#### Security
- **Authentication**: Email + password, JWT tokens, optional OAuth
- **Authorization**: Role-based access control (owner, editor, viewer)
- **Data Isolation**: Projects isolated at database namespace level
- **Encryption**: TLS 1.3 for transit, AES-256 for sensitive data at rest
- **API Security**: Rate limiting (100 req/min per user), API key authentication

#### Usability
- **Onboarding**: <10 minutes to first knowledge base
- **Learning Curve**: Core features usable without documentation
- **Accessibility**: WCAG 2.1 AA compliance
- **Mobile**: Responsive design, usable on tablets (search + view)

#### Visual Design & UI/UX
- **Design Language**: Clean, professional, business-focused (no emojis)
- **Color Palette**: Pastel colors for reduced eye strain, soft shadows
- **Typography**: Inter font (same as Notion) for consistency and readability
- **Icons**: Professional SVG icons (Lucide React library, 1000+ options)
- **Dark Mode**: Full light/dark theme support with system preference detection
- **Animations**: Smooth, purposeful micro-interactions (Framer Motion)
- **Modern Aesthetics**: Spacious layouts, subtle blur effects, glassmorphism accents
- **Primary Language**: Polish (default UI with full Polish translations)
- **Secondary Language**: English (switchable via language toggle)

#### Compliance
- **GDPR**: Right to access, delete, export data
- **CCPA**: Privacy policy, opt-out mechanisms
- **Data Retention**: User-controlled, default 2 years
- **Terms of Service**: Usage limits, acceptable use policy

---

### Integration Requirements

#### RAG-CREATOR Integration
**Status**: Existing system to be integrated
**Approach**: Microservice architecture with API gateway

**Integration Points**:
1. **Authentication**: Share JWT tokens between services
2. **Project ID Mapping**: Map KnowledgeTree projects → RAG-CREATOR projects
3. **API Endpoints**: Wrap RAG-CREATOR endpoints with new auth layer
4. **Database**: Shared PostgreSQL with schema separation
5. **File Storage**: Unified upload directory with project namespacing

**Changes to RAG-CREATOR**:
- Add `project_id` to all database tables
- Add tenant isolation to queries
- Add embedding model selection API
- Keep existing pipeline unchanged

---

#### Firecrawl Integration
**Service**: Third-party API for web crawling
**API**: https://firecrawl.dev/docs

**Requirements**:
- Account: Starter plan ($49/mo, 5K pages)
- Authentication: API key in environment variables
- Endpoints used:
  - `/v1/scrape` - Single page crawling
  - `/v1/crawl` - Multi-page crawling
  - `/v1/crawl/status` - Progress tracking
- Configuration:
  - Enable JavaScript rendering
  - Return markdown format
  - Extract metadata (title, description, links)
  - Respect robots.txt (configurable)

**Error Handling**:
- 429 Rate Limit: Queue and retry
- 500 Server Error: Retry with exponential backoff (3 attempts)
- 402 Payment Required: Notify user, upgrade prompt
- Timeout: Cancel after 5 minutes, partial results

---

#### Claude API Integration
**Service**: Anthropic Claude API for LLM
**Model**: Claude 3.5 Sonnet (default), Claude 3 Opus (enterprise)

**Use Cases**:
1. **Agentic Workflows**: Multi-step reasoning and decision making
2. **Insight Generation**: Competitive analysis and summaries
3. **RAG Chat**: Question answering with retrieved context
4. **Document Analysis**: Structured data extraction
5. **Search Query Expansion**: Improve search recall

**Requirements**:
- API Key: Stored in environment variables
- Rate Limits: 50 req/min (Tier 2), 500K tokens/min
- Context Window: 200K tokens
- Cost Tracking: Monitor usage per project
- Fallback: Graceful degradation if API unavailable

---

#### PostgreSQL + pgvector Setup
**Database**: PostgreSQL 16 with pgvector extension
**Version**: pgvector 0.7.0+

**Schema Design**:
```sql
-- Projects (user workspaces)
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    embedding_model VARCHAR(50) DEFAULT 'bge-m3',
    embedding_dimensions INTEGER DEFAULT 1024,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Categories (hierarchical tree from Genetico)
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    parent_id INTEGER REFERENCES categories(id),
    name VARCHAR(255) NOT NULL,
    rationale_ux TEXT,
    rationale_seo TEXT,
    rationale_clinical TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Documents (PDF parts or web pages)
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    source_type VARCHAR(20) NOT NULL, -- 'pdf', 'web', 'manual'
    source_url TEXT,
    filename VARCHAR(255),
    page_count INTEGER,
    raw_text TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Chunks (text chunks with embeddings)
CREATE TABLE chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id),
    global_index INTEGER NOT NULL,
    local_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    char_count INTEGER,
    embedding vector(1024), -- dimension varies by model
    has_embedding INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_chunks_document ON chunks(document_id);
CREATE INDEX idx_chunks_category ON chunks(category_id);
CREATE INDEX idx_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

**Performance Optimizations**:
- IVFFlat indexing for vector similarity search
- Partial indexes on active projects only
- Connection pooling (10-20 connections)
- Query optimization with EXPLAIN ANALYZE

---

### Data Requirements

#### Data Storage Estimates

**Per Project**:
- Metadata: <1 KB
- Category tree: ~10 KB (avg 50 categories)
- Documents: 100 docs × 500 KB avg = 50 MB
- Chunks: 5K chunks × 5 KB avg = 25 MB
- Embeddings: 5K chunks × 1024 dim × 4 bytes = 20 MB
- **Total per project**: ~95 MB

**Platform Scale**:
- Year 1: 500 projects = 47.5 GB
- Year 3: 5000 projects = 475 GB
- Database size: 1 TB (includes indexes, logs, backups)

#### Backup Strategy
- **Frequency**: Daily full backup, hourly incrementals
- **Retention**: 30 days rolling, 12 monthly archives
- **Recovery Time Objective (RTO)**: <4 hours
- **Recovery Point Objective (RPO)**: <1 hour
- **Testing**: Monthly disaster recovery drills

---

## Pricing & Business Model

### Tier Structure

#### Free Tier (Freemium)
**Price**: $0/month
**Target**: Individual users, hobbyists, trial users

**Limits**:
- 3 projects
- 10 documents per project (PDF only)
- 50K chunks total
- BGE-M3 embeddings only (local, free)
- Basic search (vector similarity)
- Export: JSON, CSV (no embeddings)

**Revenue Strategy**: Convert 30% to paid tiers within 90 days

---

#### Starter Tier
**Price**: $49/month ($470/year, save 20%)
**Target**: Individual product managers, small teams (1-3 users)

**Features**:
- Everything in Free, plus:
- 10 projects
- Unlimited PDF documents
- 500K chunks total
- Web crawling: 1K pages/month (Firecrawl)
- Scheduled crawls: 4 per project
- Embedding models: BGE-M3, BGE-Large-EN, OpenAI small
- AI insights: Competitive matrix, trend analysis
- RAG chat: 100 messages/month
- Export: All formats including embeddings
- Email support

**ROI Calculation for Customer**:
- Saves 6 hours/week on manual research = $300/week @ $50/hr
- Monthly savings: $1200
- **ROI: 2350%**

---

#### Professional Tier
**Price**: $149/month ($1,430/year, save 20%)
**Target**: Product teams, consultants, researchers (3-10 users)

**Features**:
- Everything in Starter, plus:
- 50 projects
- 2M chunks total
- Web crawling: 5K pages/month
- Deep web search: 10 research queries/month
- Technical document analysis: 50 docs/month
- Embedding models: All (including OpenAI large)
- AI insights: Unlimited
- RAG chat: 500 messages/month
- Team collaboration: 5 users
- API access (REST)
- Priority email + chat support

**ROI Calculation**:
- Replaces tools: Visualping ($40) + Notion AI ($10) + Manual research ($500)
- Competitive intelligence value: $2000/month
- **ROI: 1240%**

---

#### Enterprise Tier
**Price**: $499/month or custom
**Target**: Large teams, agencies, enterprises (10+ users)

**Features**:
- Everything in Professional, plus:
- Unlimited projects and chunks
- Web crawling: 25K pages/month (or custom)
- Deep web search: Unlimited
- Agentic workflow orchestration
- Custom workflow builder
- Advanced security: SSO, audit logs
- Custom embedding models
- Dedicated infrastructure (if needed)
- SLA: 99.9% uptime
- Dedicated account manager
- Phone + email support
- Custom integrations

---

### Revenue Projections

**Year 1 Assumptions**:
- 500 free signups
- 30% conversion to paid (150 customers)
- Distribution: 100 Starter, 40 Professional, 10 Enterprise

**Year 1 Revenue**:
- Starter: 100 × $49 × 12 = $58,800
- Professional: 40 × $149 × 12 = $71,520
- Enterprise: 10 × $499 × 12 = $59,880
- **Total Year 1: $190,200**

**Year 3 Revenue** (with growth):
- 5000 free users
- 1000 paid customers (20% conversion)
- Distribution: 600 Starter, 300 Professional, 100 Enterprise
- **Total Year 3: $2,034,000**

---

## Go-to-Market Strategy

### Launch Plan (3 Months)

**Month 1: Private Beta**
- Recruit 20 beta users (Product Hunt, LinkedIn outreach)
- Goal: Validate core workflows, identify bugs
- Success: 15+ users complete first knowledge base
- Collect feedback via weekly surveys

**Month 2: Public Beta**
- Launch on Product Hunt
- Goal: 200 signups, 50 active users
- Content marketing: Blog posts, case studies
- Social proof: Testimonials from beta users

**Month 3: Official Launch**
- Paid tiers go live
- Goal: 500 free users, 50 paid customers ($7,500 MRR)
- Launch promotions: 50% off first 3 months
- PR campaign: Submit to SaaS directories, tech blogs

---

### Marketing Channels

1. **Content Marketing** (Primary):
   - Blog: "How to track competitors without enterprise tools"
   - YouTube: Tutorial videos, competitive analysis case studies
   - SEO: Target "competitive intelligence tools", "RAG knowledge base"

2. **Product Hunt Launch**:
   - Goal: Top 5 product of the day
   - Prep: Golden Kitty campaign, upvote coordination
   - Follow-up: Engage with comments, offer beta access

3. **LinkedIn Outreach** (B2B):
   - Target: Product managers, market researchers
   - DM campaign: Personalized messages with free trial
   - Content: Thought leadership posts on competitive strategy

4. **Community Building**:
   - Slack/Discord community for users
   - Weekly office hours with founder
   - User spotlight: Feature customer success stories

5. **Partnerships**:
   - Integrate with PM tools (Jira, Linear, Notion)
   - Affiliate program: 20% commission for referrals
   - Marketplace listings: Zapier, Make.com

---

### Competitive Positioning

| Competitor | Price | Strengths | Our Advantage |
|------------|-------|-----------|---------------|
| **Crayon** | $34K/year | Enterprise features, analyst support | 93% cheaper, same core features |
| **Klue** | $20K/year | Battlecards, sales enablement | Better for research, not just sales |
| **Visualping** | $40/mo | Simple change tracking | AI-powered analysis, not just alerts |
| **Notion AI** | $10/user/mo | Great for docs, basic search | Semantic search, automatic crawling |
| **ChatGPT Enterprise** | $60/user/mo | General AI, file uploads | Purpose-built for knowledge management |

**Unique Value Props**:
1. **10x cheaper** than enterprise competitive intelligence tools
2. **Automatic web crawling** vs manual copy-paste (Notion)
3. **Semantic search** vs keyword search (most tools)
4. **Open embeddings** - export for custom AI apps
5. **Agentic workflows** - no code automation

---

## Success Criteria & KPIs

### Product Metrics (First 90 Days)

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Sign-ups | 500 | TBD | 🎯 |
| Activation (first KB) | 60% | TBD | 🎯 |
| Weekly Active Users | 200 | TBD | 🎯 |
| Free→Paid Conversion | 10% | TBD | 🎯 |
| Paid Customers | 50 | TBD | 🎯 |
| MRR | $5K | TBD | 🎯 |
| Churn Rate | <10% | TBD | 🎯 |
| NPS Score | >50 | TBD | 🎯 |

### User Engagement Metrics

- **Time to First Knowledge Base**: <10 minutes (90th percentile)
- **Projects per Active User**: 2.5 average
- **Documents per Project**: 25 average
- **Searches per Week**: 15 per active user
- **RAG Chat Usage**: 40% of paid users
- **Export Usage**: 60% of paid users
- **Recurring Crawls**: 70% of Starter+ users

### Quality Metrics

- **Search Accuracy**: >85% relevant in top 5 results
- **Processing Success Rate**: >95% for PDFs
- **Crawl Success Rate**: >90% for websites
- **Agent Task Completion**: >80% success rate
- **API Uptime**: >99.5%
- **Support Response Time**: <4 hours

---

## Risks & Mitigation

### Technical Risks

**Risk 1: Firecrawl API costs exceed budget**
- **Probability**: Medium
- **Impact**: High (affects margins)
- **Mitigation**:
  1. Implement strict page limits per tier
  2. Cache crawled pages (refresh only on schedule)
  3. Negotiate volume discounts with Firecrawl
  4. Fallback: Build in-house crawler with Playwright (Phase 2)

**Risk 2: BGE-M3 embedding quality insufficient**
- **Probability**: Low
- **Impact**: High (core feature)
- **Mitigation**:
  1. A/B test vs OpenAI embeddings in beta
  2. Offer OpenAI as premium option
  3. Monitor search accuracy metrics
  4. Collect user feedback on relevance

**Risk 3: PostgreSQL scalability limits**
- **Probability**: Medium (at scale)
- **Impact**: Medium
- **Mitigation**:
  1. Partition tables by project_id
  2. Archive old projects to cold storage
  3. Implement read replicas for queries
  4. Migrate to dedicated vector DB if needed (Qdrant, Weaviate)

---

### Business Risks

**Risk 1: Low free→paid conversion**
- **Probability**: High (typical for SaaS)
- **Impact**: High (revenue)
- **Mitigation**:
  1. Aggressive free tier limits (3 projects, no web crawling)
  2. In-app upgrade prompts at friction points
  3. Time-limited trials of premium features
  4. Email drip campaign highlighting ROI

**Risk 2: High churn rate**
- **Probability**: Medium
- **Impact**: High
- **Mitigation**:
  1. Onboarding excellence (first-week email sequence)
  2. Usage monitoring (flag at-risk users)
  3. Proactive outreach to inactive users
  4. Quarterly business reviews for Enterprise

**Risk 3: Competitive response**
- **Probability**: Medium (Notion, ChatGPT could add features)
- **Impact**: High
- **Mitigation**:
  1. Build strong moat: agentic workflows, integrations
  2. Focus on niche (competitive intelligence) vs general
  3. Fast iteration based on customer feedback
  4. Community building (switching costs)

---

### Regulatory Risks

**Risk 1: Web scraping legal issues**
- **Probability**: Low (using legitimate API)
- **Impact**: High (shutdown risk)
- **Mitigation**:
  1. Use Firecrawl (they handle legal compliance)
  2. Respect robots.txt by default
  3. Terms of Service: User responsible for compliance
  4. Prohibit scraping of sites with explicit anti-scraping terms

**Risk 2: GDPR/CCPA compliance gaps**
- **Probability**: Medium (complex regulations)
- **Impact**: High (fines)
- **Mitigation**:
  1. Legal review before launch
  2. Implement data deletion workflows
  3. Privacy policy aligned with regulations
  4. User consent for data processing

---

## User Experience Requirements

### Design Philosophy

**Professional & Business-Focused**
- Clean, minimal interface without decorative elements
- **No emojis** - pure functionality and professionalism
- Information-dense but not cluttered
- Prioritize readability and scannability

**Modern & Timeless Aesthetics**
- Inspired by Notion's clean design language
- Soft, pastel color palette for reduced eye strain
- Subtle shadows and blur effects (glassmorphism accents)
- Smooth, purposeful animations (no gratuitous motion)

### Visual Design Specifications

**Color System**:
- **Primary Palette**: Pastel blue (#3B82F6 variants) for actions and links
- **Success**: Pastel green (#22C55E) for positive feedback
- **Warning**: Pastel amber (#F59E0B) for warnings and pending states
- **Error**: Pastel red (#EF4444) for errors and destructive actions
- **Neutrals**: Gray scale from #FAFAFA to #171717 for backgrounds and text
- **Category Highlights**: Soft pastels (lavender, mint, peach, sky, rose, lemon, sage, lilac)

**Typography**:
- **Font Family**: **Inter** (same as Notion) for consistency and readability
  - Regular (400), Medium (500), Semibold (600), Bold (700)
- **Type Scale**: 12px to 72px with clear hierarchy
- **Line Heights**: 1.25 (headings), 1.5 (body), 1.75 (long-form)
- **Polish Language Support**: Full diacritics support (ą, ć, ę, ł, ń, ó, ś, ź, ż)

**Iconography**:
- **Library**: Lucide React (1000+ professional SVG icons)
- **Style**: Outline icons with consistent 2px stroke width
- **Sizes**: 12px, 16px, 20px (default), 24px, 32px, 48px
- **Usage**: Semantic icons only (no decorative icons)

**Spacing & Layout**:
- **Base Unit**: 8px spacing scale
- **Layout Grids**: 12-column responsive grid
- **Border Radius**: 4px (inputs) to 16px (cards), full rounded for pills
- **Shadows**: Subtle elevation (0-5 levels) for depth hierarchy

**Animations**:
- **Library**: Framer Motion for smooth transitions
- **Duration**: 100-300ms (micro-interactions to page transitions)
- **Easing**: Spring physics for natural feel
- **Purpose**: Feedback, relationships, attention, perceived performance

### Dark Mode

**Full Theme Support**:
- Light mode (default)
- Dark mode (manual toggle or system preference)
- Seamless switching with persistent user preference
- Dark-optimized colors (darker shadows, adjusted contrast ratios)

**Implementation**:
- CSS variables for theme tokens
- `data-theme` attribute on root element
- Theme toggle in settings/header
- Respect `prefers-color-scheme` media query

### Internationalization (i18n)

**Supported Languages**:
- **Polish** (Primary) - Default UI language
- **English** (Secondary) - Full translation available

**Language Switcher**:
- Accessible language toggle (PL/EN) in header/settings
- Persistent language preference (localStorage)
- All UI text, messages, tooltips translated
- Date/time formatting localized (Polish formats by default)

**Translation Coverage**:
- Navigation, buttons, forms
- Error messages, success notifications
- Help text, tooltips, placeholders
- Email templates, notifications

### Accessibility (WCAG 2.1 AA)

**Color Contrast**:
- Text: 4.5:1 minimum contrast ratio
- UI elements: 3:1 minimum
- Large text (18pt+): 3:1 minimum

**Keyboard Navigation**:
- All features accessible via keyboard
- Visible focus indicators (2px primary-500 outline)
- Logical tab order
- Skip links for screen readers

**Screen Reader Support**:
- Semantic HTML (`<nav>`, `<main>`, `<aside>`)
- ARIA labels for icons and interactive elements
- ARIA live regions for dynamic content (search results, notifications)
- Descriptive link text (no "click here")

**Responsive Design**:
- Mobile-first approach
- Breakpoints: 640px (sm), 768px (md), 1024px (lg), 1280px (xl)
- Touch-friendly targets (44px minimum)
- Optimized for tablets (primary use case for mobile)

### Component Library

**shadcn/ui** - Unstyled, accessible component primitives:
- Button (primary, secondary, ghost, destructive variants)
- Input (text, number, email with validation states)
- Card (elevation, borders, spacing)
- Dialog/Modal (blur overlay, focus trap)
- Tree View (expandable, draggable, selectable)
- Toast Notifications (success, error, warning, info)
- Progress Bar (determinate, indeterminate)
- Dropdown Menu (keyboard navigable)
- Tabs, Accordion, Tooltip, Badge

**Custom Components**:
- Category Tree Editor (from Genetico, enhanced)
- PDF Upload Zone (drag-and-drop with progress)
- Search Interface (semantic search with filters)
- RAG Chat Interface (message bubbles with citations)
- Insight Dashboard (charts, competitive matrix)
- Crawler Configuration (URL inputs, schedule picker)

### User Experience Principles

**Feedback & Confirmation**:
- Immediate feedback for all actions (loading states, success/error messages)
- Confirmation dialogs for destructive actions (delete, overwrite)
- Progress indicators for long-running operations (crawling, embedding)
- Toast notifications for background completions

**Error Handling**:
- Clear error messages in plain language (Polish/English)
- Actionable error states (suggest fixes, provide retry buttons)
- Inline validation for forms (real-time feedback)
- Graceful degradation (partial results if API fails)

**Performance Perception**:
- Skeleton loaders for content (shimmer effect)
- Optimistic UI updates (assume success, revert on error)
- Smooth page transitions (200ms fade/slide)
- Lazy loading for images and heavy components

**Consistency**:
- Single source of truth for design tokens
- Uniform spacing and sizing throughout
- Consistent interaction patterns (hover, active, disabled states)
- Predictable navigation structure

---

## Open Questions & Decisions Needed

1. **Embedding Model Strategy**:
   - Should we offer fine-tuned BGE models for specific domains?
   - What's the cost threshold for switching from local to API embeddings?

2. **Multi-tenancy Architecture**:
   - Row-level security in PostgreSQL vs separate databases per enterprise?
   - How to handle resource isolation for Enterprise tier?

3. **Agentic Workflow Pricing**:
   - Charge per workflow execution or included in tier?
   - How to prevent abuse (infinite loops, excessive API calls)?

4. **White-labeling**:
   - Should we offer white-label option for agencies/consultants?
   - Pricing model: % of their revenue or flat fee?

5. **Mobile Apps**:
   - Native iOS/Android apps or PWA only?
   - If native, what features are essential vs web-only?

6. **API Rate Limits**:
   - What are appropriate rate limits per tier?
   - How to handle bursts (e.g., batch uploads)?

---

## Appendices

### Appendix A: Technology Stack (Summary)

See separate TECH_STACK.md document for detailed specifications.

**Core Technologies**:
- **Frontend**: React 19, TypeScript, TailwindCSS, shadcn/ui
- **Backend**: FastAPI (Python), asyncio, Pydantic
- **Database**: PostgreSQL 16 + pgvector 0.7
- **Embeddings**: BGE-M3 (BAAI), FlagEmbedding library
- **LLM**: Claude 3.5 Sonnet (Anthropic)
- **Crawling**: Firecrawl API
- **Hosting**: Railway.app or Render (MVP), AWS (scale)

---

### Appendix B: Glossary

- **BGE-M3**: BAAI General Embedding model v3, multilingual, 1024 dimensions
- **Chunk**: Text segment (typically 1000 chars) with embeddings for search
- **Firecrawl**: Third-party web crawling service with JavaScript rendering
- **IVFFlat**: Inverted file index with flat storage, pgvector indexing method
- **pgvector**: PostgreSQL extension for vector similarity search
- **RAG**: Retrieval-Augmented Generation, AI technique using knowledge retrieval
- **SSE**: Server-Sent Events, HTTP protocol for real-time server→client updates
- **Vector Embedding**: Numerical representation of text in high-dimensional space

---

### Appendix C: Research References

- **Market Size**: Vector database market report (Verified Market Research, 2024)
- **Competitive Pricing**: Public pricing pages (Crayon, Klue, Notion, as of Jan 2026)
- **Embedding Benchmarks**: MTEB Leaderboard (Massive Text Embedding Benchmark)
- **User Research**: 15 interviews with product managers (Dec 2025)
- **Technical Benchmarks**: Internal tests with RAG-CREATOR pipeline

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1 | 2026-01-19 | Claude | Initial draft based on requirements |
| 1.0 | 2026-01-19 | Claude | Comprehensive PRD with user flows, features, pricing |

---

**Next Steps**:
1. ✅ Review and approve PRD
2. 🎯 Define detailed technical stack (TECH_STACK.md)
3. 📋 Create implementation roadmap (project plan)
4. 💻 Begin Phase 1 development (core integration)

---

*End of PRD*
