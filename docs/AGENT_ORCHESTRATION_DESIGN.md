# KnowledgeTree - Agent Orchestration System Design Document

**Version**: 1.0
**Date**: 2026-01-22
**Status**: Design Phase - Awaiting Approval
**Author**: Claude (SuperClaude Framework)

---

## Executive Summary

### Overview
Kompleksowy system agentowej orkiestracji oparty na LangGraph, umożliwiający użytkownikom wykonywanie złożonych zadań research, scrapingu i budowy drzew wiedzy poprzez conversational interface.

### Key Objectives
- Transformacja systemu z command-based na agent-based
- Implementacja multi-agent workflows z LangGraph
- Tool calling z Claude API
- Automated URL discovery i web scraping
- Knowledge extraction i tree generation

### Investment Summary
- **Development Cost**: $47,000 - $70,000 (jednorazowo)
- **Operational Cost**: ~$36,000/month (dla 1000 users)
- **Implementation Timeline**: 11 weeks (5 faz)
- **Break-even**: ~1,800 paying users (12-15 months)
- **Expected ROI**: 300%+ (Year 2)

---

## Table of Contents

1. [Requirements Analysis](#1-requirements-analysis)
2. [Current Architecture Gap](#2-current-architecture-gap)
3. [Target Architecture](#3-target-architecture)
4. [Database Design](#4-database-design)
5. [LangGraph Integration](#5-langgraph-integration)
6. [Tool Calling Layer](#6-tool-calling-layer)
7. [Multi-Agent System](#7-multi-agent-system)
8. [API Design](#8-api-design)
9. [Implementation Plan](#9-implementation-plan)
10. [Security Considerations](#10-security-considerations)
11. [Testing Strategy](#11-testing-strategy)
12. [Performance & Monitoring](#12-performance--monitoring)
13. [Cost Analysis](#13-cost-analysis)
14. [Migration Strategy](#14-migration-strategy)
15. [Decision Points](#15-decision-points)

---

## 1. Requirements Analysis

### 1.1 User Workflow (User's Vision)

#### Primary Use Case: Deep Research with Knowledge Tree Generation

**Step 1: User initiates research**
```
User (chat): "Potrzebuję zrobić deep research na temat AI w medycynie"
```

**Step 2: Agent discovers sources**
```
System: Automated URL discovery via Google Search
Output: Table with 20 candidate URLs
        - URL, title, relevance score, date, source
```

**Step 3: User reviews and approves**
```
User: Approves 15 URLs, rejects 5
System: Saves approved URLs to database
```

**Step 4: Agent scrapes content**
```
System: Parallel web scraping (HTTP/Playwright/Firecrawl)
Output: 15 documents saved to database
```

**Step 5: Agent extracts knowledge**
```
System: LLM-based knowledge extraction
Output: Structured knowledge points with relationships
```

**Step 6: Agent builds knowledge tree**
```
System: Category tree generation
Output: Hierarchical knowledge tree with dependencies
```

### 1.2 Functional Requirements

#### FR1: Intent Classification
- System MUST classify user queries into task types
- Supported tasks: research, scrape, analyze, full_pipeline
- Classification accuracy: >90%

#### FR2: URL Discovery
- System MUST discover relevant URLs automatically
- Sources: Google Search API, Knowledge Base queries
- Return: 10-50 URLs with relevance scores
- Filtering: By date, domain, language

#### FR3: Web Scraping
- System MUST support 3 scraping engines
  - HTTP Scraper (80% of sites)
  - Playwright (15% - JavaScript-heavy)
  - Firecrawl (5% - anti-bot protected)
- Parallel processing: 5-20 concurrent operations
- Error handling: Retry with fallback

#### FR4: Knowledge Extraction
- System MUST extract structured knowledge from unstructured text
- Extraction: Entities, relationships, concepts, insights
- Quality: Relevance score >0.7
- Format: JSON with metadata

#### FR5: Knowledge Tree Generation
- System MUST generate hierarchical category trees
- Features: Auto-categorization, relationship mapping
- Integration: Existing category_tree_generator service
- Output: Tree with nodes, edges, metadata

#### FR6: Human-in-the-Loop
- System MUST support user approval checkpoints
- Checkpoints: URL approval, category review, final validation
- UI: Table view with approve/reject/modify actions
- Feedback: User modifications incorporated into workflow

#### FR7: Progress Tracking
- System MUST provide real-time workflow progress
- Metrics: Current step, progress %, current agent, reasoning
- Updates: WebSocket or polling (1-5s intervals)
- Transparency: Full agent reasoning chain

#### FR8: Error Handling
- System MUST handle errors gracefully
- Strategy: Retry with fallback, human escalation, partial completion
- Logging: All errors with context
- Recovery: State checkpointing for resume capability

### 1.3 Non-Functional Requirements

#### NFR1: Performance
- Tool call latency: <5s (95th percentile)
- Node execution: <30s (95th percentile)
- Simple workflow: <2 minutes
- Complex workflow: <10 minutes

#### NFR2: Scalability
- Concurrent workflows: 10+ (Free), 50+ (Pro), 200+ (Enterprise)
- Horizontal scaling: Kubernetes HPA
- Database: Connection pooling, read replicas

#### NFR3: Security
- URL validation: Block internal networks, malicious domains
- Rate limiting: Per user, per tool
- Data privacy: PII filtering, robots.txt compliance
- Multi-tenant isolation: project_id-based scoping

#### NFR4: Reliability
- Availability: 99.9% uptime
- Error rate: <1% for critical operations
- Recovery: Automatic retry, checkpoint rollback
- Monitoring: Prometheus metrics, structured logging

#### NFR5: Maintainability
- Code coverage: >70% unit tests
- Documentation: API docs, architecture diagrams
- Debugging: Full reasoning chains, tool call logs
- Modularity: Clear separation of concerns

### 1.4 Required Subsystems

#### Subsystem 1: Intent Classifier
- **Purpose**: Classify user queries into task types
- **Input**: User message text
- **Output**: Task type, complexity level, required tools
- **Technology**: Claude API with few-shot prompting
- **Complexity**: Low

#### Subsystem 2: URL Discovery Service
- **Purpose**: Automatically find relevant URLs
- **Input**: Research query, parameters
- **Output**: List of URLs with metadata
- **Technology**: Google Custom Search API
- **Complexity**: Medium

#### Subsystem 3: Multi-Engine Scraper
- **Purpose**: Scrape web content with auto-detection
- **Input**: URLs
- **Output**: Structured content with metadata
- **Technology**: httpx, Playwright, Firecrawl (✓ already implemented)
- **Complexity**: Medium

#### Subsystem 4: Tool Calling Layer
- **Purpose**: Enable Claude to call external tools
- **Input**: User message, available tools
- **Output**: Tool execution results
- **Technology**: Anthropic API, LangChain
- **Complexity**: High

#### Subsystem 5: LangGraph Orchestrator
- **Purpose**: Coordinate multi-step workflows
- **Input**: Task configuration, user query
- **Output**: Workflow execution results
- **Technology**: LangGraph, StateGraph
- **Complexity**: Very High

#### Subsystem 6: Multi-Agent System
- **Purpose**: Specialized agents for different tasks
- **Input**: Workflow state
- **Output**: Agent-specific results
- **Technology**: LangGraph agents
- **Complexity**: Very High

#### Subsystem 7: Knowledge Extraction Engine
- **Purpose**: Extract structured knowledge from text
- **Input**: Scraped content
- **Output**: Knowledge points with relationships
- **Technology**: Claude API, BGE-M3 embeddings
- **Complexity**: High

#### Subsystem 8: State Management
- **Purpose**: Persist workflow state across execution
- **Input**: State snapshots
- **Output**: Checkpointed state
- **Technology**: PostgreSQL, Celery
- **Complexity**: Medium

---

## 2. Current Architecture Gap

### 2.1 Current System (Command-Based)

```
User Message
    ↓
CommandParser (is_command?)
    ↓
    ├─→ YES → ArtifactGenerator → Generate artifact → Return to user
    │
    └─→ NO → RAGService → Vector search → Claude API → Return response
```

**Limitations**:
- ❌ No tool calling capability
- ❌ No multi-step reasoning
- ❌ No workflow automation
- ❌ No state persistence between messages
- ❌ Cannot execute actions (only respond with text)
- ❌ No URL discovery
- ❌ Cannot coordinate multiple operations

### 2.2 Target System (Agent-Based)

```
User Message
    ↓
IntentClassifier (Claude)
    ↓
LangGraph StateGraph
    ↓
    ├─→ classify_intent → Determine task type
    ├─→ create_plan → Generate execution plan (Claude)
    ├─→ discover_urls → Google Search API
    ├─→ await_user_review → Human-in-the-loop
    ├─→ scrape_urls → Multi-engine scraper
    ├─→ extract_knowledge → Claude + embeddings
    ├─→ build_tree → Category tree generator
    └─→ synthesize_results → Final summary (Claude)
```

**Key Differences**:
- ✅ Tool calling with Claude API
- ✅ Multi-step reasoning with LangGraph
- ✅ State persistence with checkpointing
- ✅ Automated URL discovery
- ✅ Parallel execution capability
- ✅ Human-in-the-loop checkpoints
- ✅ Full transparency (reasoning chains)

### 2.3 Gap Summary

| Component | Current | Target | Gap |
|-----------|---------|--------|-----|
| Orchestration | CommandParser | LangGraph StateGraph | ⚠️ Very High |
| Tool Calling | None | Claude Tool Use | ⚠️ Very High |
| URL Discovery | None | Google Search API | ⚠️ High |
| State Management | Stateless | Checkpointing | ⚠️ High |
| Multi-Agent | None | 4 specialized agents | ⚠️ Very High |
| Scraping | HTTP/Playwright | ✓ Complete | ✅ Done |
| RAG | ✓ Working | Keep as-is | ✅ OK |
| Chat | ✓ Working | Integrate with agents | ⚠️ Medium |

---

## 3. Target Architecture

### 3.1 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ Chat UI      │  │ Workflow UI  │  │ Knowledge Tree UI    │ │
│  └──────┬───────┘  └──────┬───────┘  └──────────────────────┘ │
└─────────┼──────────────────┼──────────────────────────────────┘
          │                  │
          │ REST API         │ WebSocket (optional)
          ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Layer (FastAPI)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ /chat        │  │/agent-workflows│ │ /crawl, /search     │ │
│  └──────────────┘  └──────┬───────┘  └──────────────────────┘ │
└──────────────────────────────────┼─────────────────────────────┘
                                   │
          ┌────────────────────────┼────────────────────────┐
          │                        │                        │
          ▼                        ▼                        ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ LangGraph        │    │ Tool Calling     │    │ Background Jobs  │
│ Orchestrator     │    │ Layer            │    │ (Celery)         │
└─────────┬────────┘    └────────┬─────────┘    └─────────┬────────┘
          │                      │                        │
          │              ┌───────┴───────┐                │
          │              │               │                │
          ▼              ▼               ▼                ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐
    │Research  │  │Scraper   │  │Analyzer  │  │Organizer         │
    │Agent     │  │Agent     │  │Agent     │  │Agent             │
    └─────┬────┘  └─────┬────┘  └─────┬────┘  └──────────────────┘
          │             │             │
          └─────────────┴─────────────┘
                        │
          ┌─────────────┼─────────────┐
          │             │             │
          ▼             ▼             ▼
    ┌─────────┐  ┌─────────┐  ┌─────────┐
    │ Claude  │  │ Google  │  │ Scraper │
    │ API     │  │ Search  │  │ Engines │
    └─────────┘  └─────────┘  └─────────┘
          │             │             │
          └─────────────┴─────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │  PostgreSQL     │
              │  + pgvector     │
              │  + Redis        │
              └─────────────────┘
```

### 3.2 Component Responsibilities

#### Frontend
- **Chat UI**: Conversational interface for agent interactions
- **Workflow UI**: Progress tracking, approval checkpoints
- **Knowledge Tree UI**: Visualization of generated trees

#### API Layer
- **REST Endpoints**: 8 new endpoints for workflow management
- **WebSocket**: Real-time progress updates (optional)
- **Authentication**: JWT-based user authentication

#### LangGraph Orchestrator
- **State Management**: AgentWorkflowState with all fields
- **Node Coordination**: 9 node functions with conditional routing
- **Checkpointing**: State persistence across execution

#### Tool Calling Layer
- **Tool Registry**: 5 base tools (search, scrape, create, query, save)
- **Execution Strategies**: Sequential, parallel, conditional, retry
- **Error Handling**: Fallback mechanisms, retry logic

#### Multi-Agent System
- **ResearchAgent**: URL discovery, source verification
- **ScraperAgent**: Web scraping execution, error handling
- **AnalyzerAgent**: Knowledge extraction, relationship mapping
- **OrganizerAgent**: Tree building, categorization

#### Background Jobs
- **Celery Workers**: Async workflow execution
- **Task Queue**: Redis-backed task queue
- **Monitoring**: Task status tracking

---

## 4. Database Design

### 4.1 New Tables

#### Table 1: `workflow_states`
**Purpose**: Store state snapshots for checkpointing

```sql
CREATE TABLE workflow_states (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER NOT NULL REFERENCES agent_workflows(id) ON DELETE CASCADE,
    step VARCHAR(100) NOT NULL,
    state_snapshot JSONB NOT NULL,
    status VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_workflow_states_workflow_id (workflow_id),
    INDEX idx_workflow_states_step (step)
);
```

**Storage Estimate**: ~10KB per snapshot, ~100MB/year for 10K workflows

#### Table 2: `workflow_tools`
**Purpose**: Log all tool executions

```sql
CREATE TABLE workflow_tools (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER NOT NULL REFERENCES agent_workflows(id) ON DELETE CASCADE,
    tool_name VARCHAR(100) NOT NULL,
    agent_type VARCHAR(50),
    input JSONB,
    output JSONB,
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_workflow_tools_workflow_id (workflow_id),
    INDEX idx_workflow_tools_tool_name (tool_name)
);
```

**Storage Estimate**: ~5KB per call, ~250MB/year for 50K tool calls

#### Table 3: `url_candidates`
**Purpose**: Store discovered URLs for user review

```sql
CREATE TABLE url_candidates (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER NOT NULL REFERENCES agent_workflows(id) ON DELETE CASCADE,
    url VARCHAR(2048) NOT NULL,
    title VARCHAR(500),
    relevance_score DECIMAL(3,2),
    source VARCHAR(100),
    metadata JSONB,
    user_approval VARCHAR(20), -- 'pending', 'approved', 'rejected'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_url_candidates_workflow_id (workflow_id),
    INDEX idx_url_candidates_approval (user_approval)
);
```

**Storage Estimate**: ~2KB per URL, ~100MB/year for 50K URLs

#### Table 4: `research_tasks`
**Purpose**: Track research progress

```sql
CREATE TABLE research_tasks (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER NOT NULL REFERENCES agent_workflows(id) ON DELETE CASCADE,
    task_type VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL,
    assigned_agent VARCHAR(50),
    result JSONB,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    INDEX idx_research_tasks_workflow_id (workflow_id),
    INDEX idx_research_tasks_status (status)
);
```

**Storage Estimate**: ~3KB per task, ~50MB/year for 15K tasks

#### Table 5: `agent_messages`
**Purpose**: Store agent reasoning chains

```sql
CREATE TABLE agent_messages (
    id SERIAL PRIMARY KEY,
    workflow_id INTEGER NOT NULL REFERENCES agent_workflows(id) ON DELETE CASCADE,
    agent_type VARCHAR(50) NOT NULL,
    step VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    reasoning TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX idx_agent_messages_workflow_id (workflow_id),
    INDEX idx_agent_messages_agent (agent_type)
);
```

**Storage Estimate**: ~1KB per message, ~150MB/year for 150K messages

### 4.2 Modified Tables

#### Update: `agent_workflows`
```sql
ALTER TABLE agent_workflows
ADD COLUMN agent_type VARCHAR(50),
ADD COLUMN parent_workflow_id INTEGER REFERENCES agent_workflows(id),
ADD COLUMN estimated_duration_minutes INTEGER,
ADD COLUMN actual_duration_minutes INTEGER;
```

### 4.3 Total Storage Estimate

**Per Year (assuming 1000 active users)**:
- workflow_states: ~100MB
- workflow_tools: ~250MB
- url_candidates: ~100MB
- research_tasks: ~50MB
- agent_messages: ~150MB

**Total**: ~650MB/year + overhead

---

## 5. LangGraph Integration

### 5.1 AgentState Definition

```python
from typing import TypedDict, List, Dict, Any, Optional, Literal
from datetime import datetime

class AgentWorkflowState(TypedDict):
    """Complete state for LangGraph workflow"""

    # Core identifiers
    workflow_id: int
    user_id: int
    project_id: int

    # Task definition
    user_query: str
    task_type: Literal["research", "scrape", "analyze", "full_pipeline"]
    complexity: Literal["low", "medium", "high"]

    # Workflow control
    current_step: str
    status: Literal["pending", "in_progress", "completed", "failed", "awaiting_approval"]
    current_agent: Optional[str]

    # URL discovery
    discovered_urls: List[Dict[str, Any]]
    approved_urls: List[str]
    rejected_urls: List[int]

    # Scraping results
    scraped_content: List[Dict[str, Any]]
    scraping_errors: List[Dict[str, Any]]

    # Knowledge extraction
    knowledge_points: List[Dict[str, Any]]
    entity_relationships: List[Dict[str, Any]]

    # Tree generation
    category_tree_id: Optional[int]

    # Planning
    execution_plan: Optional[Dict[str, Any]]
    completed_steps: List[str]
    remaining_steps: List[str]

    # Metadata
    error_message: Optional[str]
    retry_count: int
    start_time: datetime
    last_update: datetime
```

### 5.2 Node Functions

#### Node 1: classify_intent
```python
async def classify_intent(state: AgentWorkflowState, db: AsyncSession) -> AgentWorkflowState:
    """
    Classify user query into task type and complexity
    Uses Claude API with few-shot prompting
    """
    claude_client = AnthropicClient()

    prompt = f"""Classify this user query:

Query: "{state['user_query']}"

Task types: research, scrape, analyze, full_pipeline
Complexity: low, medium, high

Respond with JSON: {{"task_type": "...", "complexity": "...", "reasoning": "..."}}"""

    result = await claude_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )

    classification = json.loads(result.content[0].text)

    state["task_type"] = classification["task_type"]
    state["complexity"] = classification["complexity"]
    state["current_step"] = "create_plan"

    # Log agent reasoning
    await log_agent_message(
        db=db,
        workflow_id=state["workflow_id"],
        agent_type="IntentClassifier",
        step="classify_intent",
        content=f"Classified as {classification['task_type']} ({classification['complexity']})",
        reasoning=classification["reasoning"]
    )

    return state
```

#### Node 2: create_plan
```python
async def create_plan(state: AgentWorkflowState, db: AsyncSession) -> AgentWorkflowState:
    """
    Generate execution plan using Claude
    """
    if state["task_type"] == "research":
        steps = [
            "discover_urls",
            "await_user_review",
            "scrape_urls",
            "extract_knowledge",
            "build_tree",
            "synthesize_results"
        ]
    elif state["task_type"] == "scrape":
        steps = ["scrape_urls", "extract_knowledge"]
    # ... other task types

    state["execution_plan"] = {
        "steps": steps,
        "estimated_duration_minutes": len(steps) * 5
    }
    state["remaining_steps"] = steps
    state["current_step"] = steps[0]

    return state
```

#### Node 3: discover_urls
```python
async def discover_urls(state: AgentWorkflowState, db: AsyncSession) -> AgentWorkflowState:
    """
    Discover URLs using Google Search API
    """
    search_service = GoogleSearchService()

    # Extract search query from user message
    query = extract_search_query(state["user_query"])

    # Search with filters
    results = await search_service.search(
        query=query,
        num_results=20,
        date_range="last_year" if "2024" in query else "any",
        language="pl"
    )

    # Store URL candidates
    url_ids = []
    for result in results:
        candidate = URLCandidate(
            workflow_id=state["workflow_id"],
            url=result["url"],
            title=result["title"],
            relevance_score=result["score"],
            source="google_search",
            user_approval="pending"
        )
        db.add(candidate)
        await db.flush()
        url_ids.append(candidate.id)

    state["discovered_urls"] = [
        {
            "id": url_id,
            "url": result["url"],
            "title": result["title"],
            "score": result["score"]
        }
        for url_id, result in zip(url_ids, results)
    ]
    state["current_step"] = "await_user_review"
    state["status"] = "awaiting_approval"

    return state
```

#### Node 4: await_user_review
```python
async def await_user_review(state: AgentWorkflowState, db: AsyncSession) -> AgentWorkflowState:
    """
    Human-in-the-loop checkpoint
    This node waits for user approval
    """
    # Get user's approval decisions
    approvals = await db.execute(
        select(URLCandidate).where(
            URLCandidate.workflow_id == state["workflow_id"],
            URLCandidate.user_approval == "approved"
        )
    )

    state["approved_urls"] = [url.url for url in approvals.scalars().all()]
    state["current_step"] = "scrape_urls"
    state["status"] = "in_progress"

    return state
```

#### Node 5: scrape_urls
```python
async def scrape_urls(state: AgentWorkflowState, db: AsyncSession) -> AgentWorkflowState:
    """
    Scrape approved URLs using multi-engine orchestrator
    """
    orchestrator = CrawlerOrchestrator()

    # Parallel scraping
    results = await orchestrator.batch_crawl(
        urls=state["approved_urls"],
        concurrency=5,
        extract_links=True,
        extract_images=False
    )

    # Process results
    scraped_content = []
    errors = []

    for result in results:
        if result.error:
            errors.append({
                "url": result.url,
                "error": result.error,
                "engine": result.engine.value
            })
        else:
            scraped_content.append({
                "url": result.url,
                "title": result.title,
                "text": result.text,
                "engine": result.engine.value,
                "length": len(result.text)
            })

    state["scraped_content"] = scraped_content
    state["scraping_errors"] = errors
    state["current_step"] = "extract_knowledge"

    return state
```

#### Node 6: extract_knowledge
```python
async def extract_knowledge(state: AgentWorkflowState, db: AsyncSession) -> AgentWorkflowState:
    """
    Extract structured knowledge using Claude
    """
    claude_client = AnthropicClient()

    knowledge_points = []
    entity_relationships = []

    for content in state["scraped_content"]:
        prompt = f"""Extract knowledge from this text:

Title: {content['title']}
URL: {content['url']}
Text: {content['text'][:5000]}  # Truncate for token limit

Extract:
1. Key entities (people, organizations, concepts)
2. Relationships between entities
3. Important facts and insights
4. Categories and classifications

Respond with JSON structure."""

        result = await claude_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000
        )

        extracted = json.loads(result.content[0].text)

        knowledge_points.extend(extracted.get("facts", []))
        entity_relationships.extend(extracted.get("relationships", []))

    # Generate embeddings for knowledge points
    embedding_generator = EmbeddingGenerator()
    for point in knowledge_points:
        embedding = await embedding_generator.embed_text(point["text"])
        point["embedding"] = embedding

    state["knowledge_points"] = knowledge_points
    state["entity_relationships"] = entity_relationships
    state["current_step"] = "build_tree"

    return state
```

#### Node 7: build_tree
```python
async def build_tree(state: AgentWorkflowState, db: AsyncSession) -> AgentWorkflowState:
    """
    Generate category tree from extracted knowledge
    Uses existing category_tree_generator service
    """
    from services.category_tree_generator import CategoryTreeGenerator

    tree_generator = CategoryTreeGenerator()

    # Build tree from knowledge points
    tree = await tree_generator.generate_tree(
        knowledge_points=state["knowledge_points"],
        relationships=state["entity_relationships"],
        project_id=state["project_id"]
    )

    state["category_tree_id"] = tree.id
    state["current_step"] = "synthesize_results"

    return state
```

#### Node 8: synthesize_results
```python
async def synthesize_results(state: AgentWorkflowState, db: AsyncSession) -> AgentWorkflowState:
    """
    Generate final summary using Claude
    """
    claude_client = AnthropicClient()

    prompt = f"""Synthesize research results:

User Query: {state['user_query']}

URLs Discovered: {len(state['discovered_urls'])}
URLs Scraped: {len(state['scraped_content'])}
Knowledge Points: {len(state['knowledge_points'])}
Relationships: {len(state['entity_relationships'])}

Provide a comprehensive summary of findings."""

    result = await claude_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000
    )

    summary = result.content[0].text

    # Save final results
    await save_workflow_results(
        db=db,
        workflow_id=state["workflow_id"],
        summary=summary,
        knowledge_tree_id=state["category_tree_id"]
    )

    state["current_step"] = "completed"
    state["status"] = "completed"

    return state
```

#### Node 9: handle_error
```python
async def handle_error(state: AgentWorkflowState, db: AsyncSession) -> AgentWorkflowState:
    """
    Error handling and recovery
    """
    state["status"] = "failed"
    state["retry_count"] += 1

    if state["retry_count"] < 3:
        # Retry from last successful step
        state["status"] = "in_progress"
        # Determine retry logic based on error type

    return state
```

### 5.3 StateGraph Construction

```python
from langgraph.graph import StateGraph, END

def build_workflow_graph() -> StateGraph:
    """Build LangGraph StateGraph for agent workflows"""

    # Create graph
    workflow = StateGraph(AgentWorkflowState)

    # Add nodes
    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("create_plan", create_plan)
    workflow.add_node("discover_urls", discover_urls)
    workflow.add_node("await_user_review", await_user_review)
    workflow.add_node("scrape_urls", scrape_urls)
    workflow.add_node("extract_knowledge", extract_knowledge)
    workflow.add_node("build_tree", build_tree)
    workflow.add_node("synthesize_results", synthesize_results)
    workflow.add_node("handle_error", handle_error)

    # Define entry point
    workflow.set_entry_point("classify_intent")

    # Add conditional edges
    workflow.add_conditional_edges(
        "classify_intent",
        should_create_plan,
        {
            "create_plan": "create_plan",
            "handle_error": "handle_error"
        }
    )

    workflow.add_conditional_edges(
        "create_plan",
        determine_next_step,
        {
            "discover_urls": "discover_urls",
            "scrape_urls": "scrape_urls",
            "handle_error": "handle_error"
        }
    )

    workflow.add_conditional_edges(
        "discover_urls",
        check_approval_required,
        {
            "await_approval": "await_user_review",
            "scrape_urls": "scrape_urls"
        }
    )

    workflow.add_conditional_edges(
        "await_user_review",
        check_user_response,
        {
            "approved": "scrape_urls",
            "rejected": END,
            "modified": "discover_urls"
        }
    )

    # Add direct edges
    workflow.add_edge("scrape_urls", "extract_knowledge")
    workflow.add_edge("extract_knowledge", "build_tree")
    workflow.add_edge("build_tree", "synthesize_results")
    workflow.add_edge("synthesize_results", END)

    return workflow.compile()
```

---

## 6. Tool Calling Layer

### 6.1 Claude Tool Use Integration

```python
from anthropic import Anthropic
from typing import Dict, Any, List, Callable

class AnthropicToolClient:
    """Client for Claude API with tool calling"""

    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.tools: Dict[str, Callable] = {}

    def register_tool(self, name: str, func: Callable, schema: Dict[str, Any]):
        """Register a tool for Claude to call"""
        self.tools[name] = {
            "function": func,
            "schema": schema
        }

    async def execute_with_tools(
        self,
        user_message: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute Claude with tool calling
        Handles multi-turn conversations for tool use
        """
        messages = [{"role": "user", "content": user_message}]

        max_turns = 10  # Prevent infinite loops
        tool_calls = []
        tool_results = []

        for turn in range(max_turns):
            # Call Claude API
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                messages=messages,
                tools=[tool["schema"] for tool in self.tools.values()],
                max_tokens=4096
            )

            # Check if Claude wants to use tools
            if response.stop_reason == "tool_use":
                # Extract tool calls
                for block in response.content:
                    if block.type == "tool_use":
                        tool_calls.append({
                            "id": block.id,
                            "name": block.name,
                            "input": block.input
                        })

                        # Execute tool
                        tool_func = self.tools[block.name]["function"]
                        result = await tool_func(**block.input)

                        tool_results.append({
                            "tool_use_id": block.id,
                            "content": str(result)
                        })

                # Add assistant message with tool_use blocks
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                # Add tool results message
                messages.append({
                    "role": "user",
                    "content": tool_results
                })

            else:
                # Claude is done, return final response
                return {
                    "response": response.content[0].text,
                    "tool_calls": tool_calls,
                    "tool_results": tool_results
                }

        raise Exception("Max tool use turns exceeded")
```

### 6.2 Tool Definitions

#### Tool 1: search_web
```python
search_web_schema = {
    "name": "search_web",
    "description": "Search the web for URLs related to a query",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query"
            },
            "num_results": {
                "type": "integer",
                "description": "Number of results (1-50)",
                "default": 20
            },
            "date_range": {
                "type": "string",
                "description": "Date range filter",
                "enum": ["day", "week", "month", "year", "any"]
            }
        },
        "required": ["query"]
    }
}

async def search_web(
    query: str,
    num_results: int = 20,
    date_range: str = "any"
) -> Dict[str, Any]:
    """Execute web search"""
    service = GoogleSearchService()
    results = await service.search(
        query=query,
        num_results=num_results,
        date_range=date_range
    )

    return {
        "urls": [r["url"] for r in results],
        "total": len(results),
        "query": query
    }
```

#### Tool 2: scrape_urls
```python
scrape_urls_schema = {
    "name": "scrape_urls",
    "description": "Scrape content from multiple URLs",
    "input_schema": {
        "type": "object",
        "properties": {
            "urls": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of URLs to scrape"
            },
            "engine": {
                "type": "string",
                "description": "Scraping engine",
                "enum": ["auto", "http", "playwright", "firecrawl"],
                "default": "auto"
            },
            "concurrency": {
                "type": "integer",
                "description": "Concurrent scraping operations",
                "default": 5
            }
        },
        "required": ["urls"]
    }
}

async def scrape_urls(
    urls: List[str],
    engine: str = "auto",
    concurrency: int = 5
) -> Dict[str, Any]:
    """Scrape multiple URLs"""
    orchestrator = CrawlerOrchestrator()

    results = await orchestrator.batch_crawl(
        urls=urls,
        concurrency=concurrency,
        force_engine=CrawlEngine[engine.upper()] if engine != "auto" else None
    )

    return {
        "scraped": [r.dict() for r in results if not r.error],
        "failed": [r.dict() for r in results if r.error],
        "total": len(results)
    }
```

#### Tool 3: create_knowledge_tree
```python
create_knowledge_tree_schema = {
    "name": "create_knowledge_tree",
    "description": "Generate a hierarchical knowledge tree from content",
    "input_schema": {
        "type": "object",
        "properties": {
            "knowledge_points": {
                "type": "array",
                "description": "Knowledge points to organize"
            },
            "project_id": {
                "type": "integer",
                "description": "Project ID for the tree"
            },
            "category_id": {
                "type": "integer",
                "description": "Parent category ID (optional)"
            }
        },
        "required": ["knowledge_points", "project_id"]
    }
}

async def create_knowledge_tree(
    knowledge_points: List[Dict[str, Any]],
    project_id: int,
    category_id: Optional[int] = None
) -> Dict[str, Any]:
    """Generate knowledge tree"""
    from services.category_tree_generator import CategoryTreeGenerator

    generator = CategoryTreeGenerator()
    tree = await generator.generate_tree(
        knowledge_points=knowledge_points,
        project_id=project_id,
        parent_category_id=category_id
    )

    return {
        "tree_id": tree.id,
        "node_count": tree.node_count,
        "depth": tree.depth
    }
```

#### Tool 4: query_knowledge_base
```python
query_knowledge_base_schema = {
    "name": "query_knowledge_base",
    "description": "Search the knowledge base using vector search",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query"
            },
            "project_id": {
                "type": "integer",
                "description": "Project ID to search"
            },
            "limit": {
                "type": "integer",
                "description": "Number of results",
                "default": 10
            }
        },
        "required": ["query", "project_id"]
    }
}

async def query_knowledge_base(
    query: str,
    project_id: int,
    limit: int = 10
) -> Dict[str, Any]:
    """Search knowledge base"""
    from services.search_service import SearchService

    service = SearchService()
    results = await service.hybrid_search(
        query=query,
        project_id=project_id,
        limit=limit
    )

    return {
        "results": [r.dict() for r in results],
        "total": len(results)
    }
```

#### Tool 5: save_to_database
```python
save_to_database_schema = {
    "name": "save_to_database",
    "description": "Save data to the database",
    "input_schema": {
        "type": "object",
        "properties": {
            "entity_type": {
                "type": "string",
                "description": "Type of entity to save",
                "enum": ["document", "category", "knowledge_point"]
            },
            "data": {
                "type": "object",
                "description": "Data to save"
            },
            "project_id": {
                "type": "integer",
                "description": "Project ID"
            }
        },
        "required": ["entity_type", "data", "project_id"]
    }
}

async def save_to_database(
    entity_type: str,
    data: Dict[str, Any],
    project_id: int
) -> Dict[str, Any]:
    """Save to database"""
    async with AsyncSessionLocal() as db:
        if entity_type == "document":
            entity = Document(project_id=project_id, **data)
        elif entity_type == "category":
            entity = Category(project_id=project_id, **data)
        # ... other types

        db.add(entity)
        await db.commit()
        await db.refresh(entity)

        return {
            "id": entity.id,
            "type": entity_type,
            "status": "saved"
        }
```

### 6.3 Tool Execution Strategies

```python
class ToolExecutionStrategy:
    """Strategies for tool execution"""

    @staticmethod
    async def sequential(tools: List[Callable], inputs: List[Dict]) -> List[Any]:
        """Execute tools one after another"""
        results = []
        for tool, input_data in zip(tools, inputs):
            result = await tool(**input_data)
            results.append(result)
        return results

    @staticmethod
    async def parallel(tools: List[Callable], inputs: List[Dict]) -> List[Any]:
        """Execute tools concurrently"""
        tasks = [tool(**input) for tool, input in zip(tools, inputs)]
        return await asyncio.gather(*tasks)

    @staticmethod
    async def conditional(
        condition: Callable,
        true_tool: Callable,
        false_tool: Callable,
        input_data: Dict
    ) -> Any:
        """Execute tool based on condition"""
        if await condition(**input_data):
            return await true_tool(**input_data)
        else:
            return await false_tool(**input_data)

    @staticmethod
    async def retry(
        tool: Callable,
        input_data: Dict,
        max_retries: int = 3,
        backoff: float = 1.0
    ) -> Any:
        """Execute tool with retry logic"""
        for attempt in range(max_retries):
            try:
                return await tool(**input_data)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(backoff * (2 ** attempt))

    @staticmethod
    async def fallback(
        primary_tool: Callable,
        fallback_tool: Callable,
        input_data: Dict
    ) -> Any:
        """Execute fallback tool if primary fails"""
        try:
            return await primary_tool(**input_data)
        except Exception:
            return await fallback_tool(**input_data)
```

---

## 7. Multi-Agent System

### 7.1 Agent Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Agent Orchestrator                     │
│  (LangGraph StateGraph - Coordination Layer)           │
└────────┬────────────────────────────────────────────────┘
         │
    ┌────┴────┬──────────┬──────────┬──────────┐
    │         │          │          │          │
    ▼         ▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│Research│ │Scraper │ │Analyzer│ │Organize│ │ Error  │
│ Agent  │ │ Agent  │ │ Agent  │ │ Agent  │ │ Handler│
└────────┘ └────────┘ └────────┘ └────────┘ └────────┘
    │         │          │          │          │
    └─────────┴──────────┴──────────┴──────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │  Tool Layer  │
                  └──────────────┘
```

### 7.2 Agent Implementations

#### ResearchAgent
```python
class ResearchAgent:
    """
    Agent responsible for URL discovery and source verification
    """

    def __init__(self):
        self.name = "ResearchAgent"
        self.tools = ["search_web", "query_knowledge_base"]

    async def discover_sources(
        self,
        query: str,
        db: AsyncSession,
        workflow_id: int
    ) -> Dict[str, Any]:
        """Discover relevant sources"""
        # Log reasoning
        await self._log_reasoning(
            db=db,
            workflow_id=workflow_id,
            step="discover_sources",
            content=f"Searching for: {query}",
            reasoning="Starting broad search to gather initial sources"
        )

        # Execute search
        search_service = GoogleSearchService()
        results = await search_service.search(
            query=query,
            num_results=20,
            date_range="year"
        )

        # Filter and rank sources
        approved = self._filter_sources(results)

        # Save to database
        await self._save_candidates(
            db=db,
            workflow_id=workflow_id,
            sources=approved
        )

        return {
            "discovered": len(approved),
            "sources": approved
        }

    def _filter_sources(self, sources: List[Dict]) -> List[Dict]:
        """Filter sources by relevance and quality"""
        approved = []

        for source in sources:
            # Apply filters
            if source.get("score", 0) > 0.6:  # Relevance threshold
                if self._is_valid_domain(source["url"]):
                    approved.append(source)

        return approved

    def _is_valid_domain(self, url: str) -> bool:
        """Check if domain is valid and safe"""
        parsed = urlparse(url)

        # Block internal IPs
        if parsed.hostname in ['localhost', '127.0.0.1']:
            return False

        # Block private networks
        try:
            ip = ipaddress.ip_address(parsed.hostname)
            if ip.is_private:
                return False
        except ValueError:
            pass

        return True
```

#### ScraperAgent
```python
class ScraperAgent:
    """
    Agent responsible for web scraping execution
    """

    def __init__(self):
        self.name = "ScraperAgent"
        self.tools = ["scrape_urls"]
        self.orchestrator = CrawlerOrchestrator()

    async def scrape_sources(
        self,
        urls: List[str],
        db: AsyncSession,
        workflow_id: int
    ) -> Dict[str, Any]:
        """Scrape multiple URLs"""
        await self._log_reasoning(
            db=db,
            workflow_id=workflow_id,
            step="scrape_sources",
            content=f"Scraping {len(urls)} URLs",
            reasoning="Using auto-detection for optimal engine selection"
        )

        # Determine best engine for each URL
        engine_plan = await self._plan_engines(urls)

        # Execute scraping
        results = await self.orchestrator.batch_crawl(
            urls=urls,
            concurrency=5
        )

        # Process results
        successful = []
        failed = []

        for result in results:
            if result.error:
                failed.append(result.url)
                # Retry with fallback
                if await self._should_retry(result):
                    retry_result = await self._retry_with_fallback(result.url)
                    if not retry_result.error:
                        successful.append(retry_result)
            else:
                successful.append(result)

        return {
            "successful": len(successful),
            "failed": len(failed),
            "results": successful
        }

    async def _plan_engines(self, urls: List[str]) -> Dict[str, CrawlEngine]:
        """Plan which engine to use for each URL"""
        plan = {}

        for url in urls:
            # Auto-detect requirements
            detected = await self.orchestrator._detect_requirements(url)

            if detected.get("needs_firecrawl"):
                plan[url] = CrawlEngine.FIRECRAWL
            elif detected.get("needs_playwright"):
                plan[url] = CrawlEngine.PLAYWRIGHT
            else:
                plan[url] = CrawlEngine.HTTP

        return plan

    async def _should_retry(self, result: ScrapeResult) -> bool:
        """Determine if scraping should be retried"""
        # Retry on transient errors
        if result.error and any(
            phrase in result.error.lower()
            for phrase in ["timeout", "connection", "temporary"]
        ):
            return True
        return False
```

#### AnalyzerAgent
```python
class AnalyzerAgent:
    """
    Agent responsible for knowledge extraction and analysis
    """

    def __init__(self):
        self.name = "AnalyzerAgent"
        self.tools = ["query_knowledge_base"]
        self.claude_client = AnthropicClient()
        self.embedding_generator = EmbeddingGenerator()

    async def extract_knowledge(
        self,
        content: List[Dict[str, Any]],
        db: AsyncSession,
        workflow_id: int
    ) -> Dict[str, Any]:
        """Extract structured knowledge from content"""
        await self._log_reasoning(
            db=db,
            workflow_id=workflow_id,
            step="extract_knowledge",
            content=f"Extracting knowledge from {len(content)} documents",
            reasoning="Using Claude for entity extraction and relationship mapping"
        )

        knowledge_points = []
        relationships = []

        for doc in content:
            # Extract entities and relationships
            extracted = await self._extract_from_document(doc)

            knowledge_points.extend(extracted["entities"])
            relationships.extend(extracted["relationships"])

        # Generate embeddings
        await self._generate_embeddings(knowledge_points)

        # Deduplicate
        knowledge_points = self._deduplicate(knowledge_points)

        return {
            "knowledge_points": knowledge_points,
            "relationships": relationships,
            "total_entities": len(knowledge_points)
        }

    async def _extract_from_document(
        self,
        document: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract knowledge from single document"""
        prompt = f"""Extract structured knowledge from this text:

Title: {document['title']}
URL: {document['url']}
Text: {document['text'][:8000]}

Extract:
1. Named entities (people, organizations, locations, concepts)
2. Relationships between entities
3. Key facts and insights
4. Categories and classifications

Format as JSON."""

        response = await self.claude_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=3000
        )

        return json.loads(response.content[0].text)

    async def _generate_embeddings(
        self,
        knowledge_points: List[Dict[str, Any]]
    ):
        """Generate embeddings for knowledge points"""
        for point in knowledge_points:
            embedding = await self.embedding_generator.embed_text(
                point["text"]
            )
            point["embedding"] = embedding
```

#### OrganizerAgent
```python
class OrganizerAgent:
    """
    Agent responsible for building knowledge trees
    """

    def __init__(self):
        self.name = "OrganizerAgent"
        self.tools = ["create_knowledge_tree", "save_to_database"]

    async def build_tree(
        self,
        knowledge_points: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        project_id: int,
        db: AsyncSession,
        workflow_id: int
    ) -> Dict[str, Any]:
        """Build hierarchical knowledge tree"""
        await self._log_reasoning(
            db=db,
            workflow_id=workflow_id,
            step="build_tree",
            content=f"Building tree from {len(knowledge_points)} points",
            reasoning="Using existing category_tree_generator service"
        )

        from services.category_tree_generator import CategoryTreeGenerator

        generator = CategoryTreeGenerator()

        # Build tree
        tree = await generator.generate_tree(
            knowledge_points=knowledge_points,
            relationships=relationships,
            project_id=project_id
        )

        return {
            "tree_id": tree.id,
            "node_count": tree.node_count,
            "depth": tree.depth
        }
```

---

## 8. API Design

### 8.1 Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/agent-workflows/start` | Start new workflow |
| GET | `/api/v1/agent-workflows/{id}` | Get workflow status |
| POST | `/api/v1/agent-workflows/{id}/approve` | Approve/reject checkpoint |
| GET | `/api/v1/agent-workflows/{id}/messages` | Get agent reasoning |
| GET | `/api/v1/agent-workflows/{id}/tools` | Get tool calls |
| POST | `/api/v1/agent-workflows/{id}/stop` | Stop workflow |
| GET | `/api/v1/agent-workflows` | List workflows |
| GET | `/api/v1/agent-workflows/{id}/results` | Get final results |

### 8.2 Request/Response Schemas

#### POST /agent-workflows/start
```python
class WorkflowStartRequest(BaseModel):
    task_type: WorkflowTaskType  # research, scrape, analyze, full_pipeline
    user_query: str = Field(..., min_length=10, max_length=2000)
    config: Optional[WorkflowConfig] = None

class WorkflowConfig(BaseModel):
    max_urls: int = Field(20, ge=1, le=200)
    scrape_parallel: bool = True
    require_approval: bool = True
    category_id: Optional[int] = None
    date_range: str = "any"  # day, week, month, year, any
    language: str = "pl"

class WorkflowStartResponse(BaseModel):
    workflow_id: int
    status: WorkflowStatus
    estimated_steps: int
    current_step: str
    current_agent: Optional[str]
    estimated_duration_minutes: int
    message: str
```

#### GET /agent-workflows/{id}
```python
class WorkflowStatusResponse(BaseModel):
    id: int
    name: str
    status: WorkflowStatus
    task_type: WorkflowTaskType
    current_step: str
    current_agent: Optional[str]
    progress: ProgressInfo
    agent_reasoning: Optional[AgentReasoning]
    results: Optional[WorkflowResults]
    created_at: datetime
    updated_at: datetime

class ProgressInfo(BaseModel):
    completed_steps: int
    total_steps: int
    percentage: float
    current_operation: str

class AgentReasoning(BaseModel):
    agent: str
    step: str
    message: str
    reasoning: str
    timestamp: datetime

class WorkflowResults(BaseModel):
    urls_discovered: int
    urls_scraped: int
    knowledge_points: int
    relationships: int
    knowledge_tree_id: Optional[int]
```

#### POST /agent-workflows/{id}/approve
```python
class ApprovalRequest(BaseModel):
    decision: Literal["approve", "reject", "modify"]
    modifications: Optional[ApprovalModifications] = None

class ApprovalModifications(BaseModel):
    add_urls: Optional[List[str]] = None
    remove_urls: Optional[List[int]] = None
    modify_config: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None

class ApprovalResponse(BaseModel):
    message: str
    workflow_id: int
    status: WorkflowStatus
    next_step: str
```

---

## 9. Implementation Plan

### Phase 1: Foundation (2 weeks)

**Goals**: Infrastructure setup without agents

**Tasks**:
- [ ] Database migration (5 new tables)
- [ ] Update AgentWorkflow model
- [ ] Create base service classes
- [ ] Setup Celery + Redis
- [ ] Create base API scaffolding

**Deliverables**:
- Migration scripts
- Empty service implementations
- Basic API structure

**Testing**:
- Unit tests for models
- Migration testing
- Database connectivity

**Risk**: Low

### Phase 2: Tool Calling Layer (2 weeks)

**Goals**: Claude with function calling

**Tasks**:
- [ ] Implement AnthropicToolClient
- [ ] Create 5 base tools
- [ ] Implement execution strategies
- [ ] Google Search API integration
- [ ] Tool validation and error handling

**Deliverables**:
- Working tool calling
- Integration tests
- Error handling

**Testing**:
- Tool execution tests
- Claude API integration tests
- Error handling tests

**Risk**: Medium

### Phase 3: LangGraph Core (3 weeks)

**Goals**: LangGraph workflow orchestration

**Tasks**:
- [ ] Install LangGraph + LangChain
- [ ] Define AgentState
- [ ] Implement 9 node functions
- [ ] Build StateGraph
- [ ] Implement checkpointing
- [ ] Background execution with Celery

**Deliverables**:
- Working LangGraph workflows
- State persistence
- Error recovery

**Testing**:
- Workflow execution tests
- State persistence tests
- Error recovery tests

**Risk**: High

### Phase 4: Multi-Agent System (2 weeks)

**Goals**: 4 specialized agents

**Tasks**:
- [ ] Implement ResearchAgent
- [ ] Implement ScraperAgent
- [ ] Implement AnalyzerAgent
- [ ] Implement OrganizerAgent
- [ ] Agent coordination layer
- [ ] Reasoning chain tracking

**Deliverables**:
- 4 working agents
- Agent collaboration
- Full transparency

**Testing**:
- Multi-agent workflow tests
- Agent communication tests
- Reasoning logging tests

**Risk**: High

### Phase 5: API & Frontend (2 weeks)

**Goals**: Complete API and frontend

**Tasks**:
- [ ] Implement 8 REST endpoints
- [ ] Real-time progress (WebSocket/polling)
- [ ] Human-in-the-loop UI
- [ ] Workflow visualization
- [ ] Error handling UI
- [ ] Documentation

**Deliverables**:
- Complete REST API
- Frontend components
- User docs

**Testing**:
- E2E tests
- Frontend integration tests
- User acceptance tests

**Risk**: Medium

---

## 10. Security Considerations

### 10.1 Critical Security Measures

#### URL Validation
```python
def validate_url(url: str) -> bool:
    """Validate URL before scraping"""
    parsed = urlparse(url)

    # Block internal IPs
    blocked = ['localhost', '127.0.0.1', '0.0.0.0', '::1']
    if parsed.hostname in blocked:
        return False

    # Block private networks
    try:
        ip = ipaddress.ip_address(parsed.hostname)
        if ip.is_private or ip.is_loopback:
            return False
    except ValueError:
        pass

    # Block non-http/https
    if parsed.scheme not in ['http', 'https']:
        return False

    return True
```

#### Rate Limiting
```python
from slowapi import Limiter

limiter = Limiter(key_func=get_user_id)

@router.post("/agent-workflows/start")
@limiter.limit("10/minute")
async def start_workflow(...):
    """Max 10 workflows per minute per user"""
    ...
```

#### Resource Limits
```python
class WorkflowLimits(BaseModel):
    max_urls: int = 20  # Free tier
    max_tool_calls: int = 100
    max_duration: int = 3600  # seconds
    max_llm_tokens: int = 1000000
```

### 10.2 Security Checklist

- [ ] URL validation before scraping
- [ ] Rate limiting per user
- [ ] Resource exhaustion prevention
- [ ] Prompt injection mitigation
- [ ] Multi-tenant isolation (project_id)
- [ ] API key protection (environment variables)
- [ ] PII filtering before database save
- [ ] robots.txt compliance
- [ ] Audit logging for all operations
- [ ] Input validation on all endpoints
- [ ] Output encoding for XSS prevention
- [ ] SQL injection prevention (parameterized queries)

---

## 11. Testing Strategy

### 11.1 Test Coverage Targets

- **Unit Tests**: 70%+ code coverage
- **Integration Tests**: All tool combinations
- **E2E Tests**: 3 critical workflows
- **Performance Tests**: Max concurrent users

### 11.2 Test Suites

#### Unit Tests
```python
# tests/unit/test_agent_tools.py
def test_search_web_tool_validation()
def test_scrape_urls_rate_limiting()
def test_research_agent_url_filtering()

# tests/unit/test_langgraph_nodes.py
def test_classify_intent_node()
def test_conditional_edges()
def test_workflow_state_checkpointing()
```

#### Integration Tests
```python
# tests/integration/test_tool_execution.py
async def test_full_tool_calling_pipeline()
async def test_database_persistence()

# tests/integration/test_agent_coordination.py
async def test_research_to_scraper_handoff()
async def test_multi_agent_collaboration()
```

#### E2E Tests
```python
# tests/e2e/test_full_workflows.py
@pytest.mark.e2e
async def test_deep_research_workflow()
async def test_scrape_and_analyze_workflow()
async def test_full_pipeline_with_approval()

# tests/e2e/test_ui_integration.py
async def test_human_approval_workflow()
async def test_workflow_status_display()
```

---

## 12. Performance & Monitoring

### 12.1 Performance Budgets

| Metric | Target | 95th Percentile |
|--------|--------|-----------------|
| Tool call | <5s | <10s |
| Node execution | <30s | <60s |
| Simple workflow | <2 min | <5 min |
| Complex workflow | <10 min | <20 min |
| API response | <500ms | <1s |

### 12.2 Monitoring Setup

#### Prometheus Metrics
```python
from prometheus_client import Counter, Histogram, Gauge

workflow_duration = Histogram(
    'workflow_duration_seconds',
    'Workflow execution duration',
    ['task_type', 'status']
)

tool_calls_total = Counter(
    'tool_calls_total',
    'Total tool calls',
    ['tool_name', 'status']
)

active_workflows = Gauge(
    'active_workflows',
    'Number of active workflows'
)
```

#### Structured Logging
```python
import structlog

logger = structlog.get_logger()

logger.info(
    "workflow_started",
    workflow_id=workflow_id,
    user_id=user_id,
    task_type=task_type
)
```

---

## 13. Cost Analysis

### 13.1 Development Costs (One-time)

| Role | Rate | Hours | Total |
|------|------|-------|-------|
| Backend Dev | $80-120/h | 320h | $25,600-38,400 |
| Frontend Dev | $60-90/h | 160h | $9,600-14,400 |
| DevOps | $70-100/h | 80h | $5,600-8,000 |
| QA | $50-70/h | 120h | $6,000-8,400 |
| **Total** | | | **$47K-70K** |

### 13.2 Monthly Operating Costs

| Component | Cost (1000 users) |
|-----------|-------------------|
| Claude API | $27,000 |
| Google Search | $7,500 |
| Firecrawl | $830 |
| Infrastructure | $1,500 |
| **Total** | **~$36,500** |

### 13.3 Pricing Strategy

| Tier | Price | Limits | Cost/User | Margin |
|------|-------|--------|-----------|--------|
| Free | $0 | 10 workflows/month | $5 | -100% |
| Starter | $29 | 50 workflows | $25 | 14% |
| Professional | $99 | 200 workflows | $55 | 44% |
| Enterprise | $499 | Unlimited | $200 | 60% |

### 13.4 ROI Projections

**Break-even**: ~1,800 paying users (12-15 months)

**Year 2** (10,000 users, 30% conversion):
- Revenue: $270,000/month
- Cost: $100,000/month
- Profit: $170,000/month
- **Annual ROI**: 300%+

---

## 14. Migration Strategy

### 14.1 5-Step Migration

1. **Database Migration** (Alembic)
2. **Legacy Data Migration**
3. **Backward Compatibility Layer**
4. **Gradual Rollout** (feature flags)
5. **Deprecation Timeline** (5 months)

### 14.2 Rollback Plan

```python
# Instant feature flag rollback
if await feature_flags.is_enabled("emergency_rollback"):
    return await legacy_handler(request)

# Database rollback
alembic downgrade -1

# Code rollback
kubectl rollout undo deployment/knowledgetree-backend
```

---

## 15. Decision Points

### 15.1 Critical Decisions Required

#### 1. Scope Selection
- **Option A**: Full multi-agent system (11 weeks, $47-70K)
- **Option B**: Single-agent system (6 weeks, ~$30K) ⭐ RECOMMENDED
- **Option C**: Hybrid (Phase 1: Single, Phase 2: Multi)

#### 2. Phased Rollout
- **Yes**: Gradual deployment with testing
- **No**: Big bang launch

#### 3. Budget Approval
- **Development**: $47-70K one-time
- **Operating**: ~$36K/month for 1000 users
- **Alternatives**: Self-hosting LLM, cheaper APIs

#### 4. Timeline Acceptance
- **11 weeks** (full system)
- **6 weeks** (single-agent)
- Custom timeline?

#### 5. Must-Have Features
- URL discovery? (Yes/No)
- Multi-agent? (Yes/No)
- Human-in-the-loop? (Yes/No)
- Real-time updates? (Yes/No)

### 15.2 Recommendation

**START WITH OPTION B (Single-Agent)**

**Rationale**:
- Lower risk
- Faster time-to-market (6 weeks)
- Lower costs ($30K dev, $20K/month)
- Faster user feedback
- Can upgrade to multi-agent later

**Path Forward**:
1. Implement single-agent with tool calling
2. Deploy to beta users
3. Gather feedback and usage data
4. Decide on multi-agent upgrade based on real needs

---

## Appendix

### A. Technology Stack

**Core**:
- Python 3.11+
- FastAPI 0.109+
- LangGraph 0.0.20+
- LangChain 0.1+

**Database**:
- PostgreSQL 16
- pgvector 0.7
- Redis 7+

**Background Jobs**:
- Celery 5.3+
- Redis broker

**AI/ML**:
- Claude 3.5 Sonnet API
- BGE-M3 embeddings
- FlagEmbedding 1.2+

**Monitoring**:
- Prometheus
- Grafana
- Structlog

### B. References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Anthropic Tool Use](https://docs.anthropic.com/claude/docs/tool-use)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [Celery Documentation](https://docs.celeryq.dev/)

---

**Document Status**: Ready for Review
**Next Steps**: User approval required before implementation
**Contact**: jarek@knowledgetree.com
