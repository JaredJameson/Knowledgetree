"""
KnowledgeTree - Multi-Agent System
Specialized agents for agentic workflow orchestration
"""

from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import json
import asyncio
from abc import abstractmethod

from core.database import AsyncSessionLocal
from models.agent_workflow import AgentWorkflow, WorkflowStatus
from models.workflow_support import (
    WorkflowState,
    WorkflowTool,
    URLCandidate,
    ResearchTask,
    AgentMessage
)
from services.agent_base import BaseAgent
from services.claude_tool_client import AnthropicToolClient
from services.google_search import GoogleSearchService
from services.crawler_orchestrator import CrawlerOrchestrator, CrawlEngine
from services.category_tree_generator import CategoryTreeGenerator
from schemas.workflow import AgentWorkflowState


# ============================================================================
# ResearchAgent - Deep Research & URL Discovery
# ============================================================================


class ResearchAgent(BaseAgent):
    """
    ResearchAgent - Deep research and URL discovery specialist

    Capabilities:
    - Analyze user query and determine research strategy
    - Execute Google Custom Search with optimized queries
    - Discover relevant URLs with relevance scoring
    - Filter and rank results by quality
    - Handle multiple search iterations for comprehensive coverage

    Tools:
    - search_web (via Google Custom Search API)
    - query_knowledge_base (check existing knowledge)
    """

    name = "ResearchAgent"
    description = "Deep research and URL discovery specialist"

    def __init__(self):
        super().__init__()
        self.claude = AnthropicToolClient()
        self.google_search: Optional[GoogleSearchService] = None

    async def initialize(self):
        """Initialize research agent with Google Search service"""
        self.google_search = GoogleSearchService()
        await self.google_search.initialize()

    async def analyze_query(
        self,
        db: AsyncSession,
        workflow_id: int,
        user_query: str
    ) -> Dict[str, Any]:
        """
        Analyze user query to determine research strategy

        Returns:
            Dict with:
            - search_queries: List of optimized search queries
            - expected_urls: Estimated number of URLs to find
            - complexity: Research complexity (low/medium/high)
            - strategy: Research strategy (broad/deep/targeted)
        """
        system_prompt = """You are a research strategy expert. Analyze the user's query and determine:
1. The best search queries to find relevant information
2. How many URLs we should target (10-50 depending on scope)
3. Research complexity (low/simple, medium/moderate, high/comprehensive)
4. Research strategy (broad=many general sources, deep=few detailed sources, targeted=specific focus)

Return JSON with this structure:
{
    "search_queries": ["query1", "query2", ...],
    "expected_urls": number,
    "complexity": "low|medium|high",
    "strategy": "broad|deep|targeted",
    "reasoning": "explanation of strategy"
}"""

        await self.log_reasoning(
            db, workflow_id, "analyze_query",
            content=f"Analyzing research query: {user_query}",
            reasoning="Determining optimal search strategy based on query complexity and scope"
        )

        response = await self.claude.execute_simple(
            user_query=user_query,
            system_prompt=system_prompt,
            model="claude-3-5-sonnet-20241022"
        )

        try:
            result = json.loads(response)
            await self.log_reasoning(
                db, workflow_id, "analyze_query",
                content=f"Strategy determined: {result['strategy']}, complexity: {result['complexity']}",
                reasoning=result.get("reasoning", "Strategy based on query analysis")
            )
            return result
        except json.JSONDecodeError:
            # Fallback strategy
            return {
                "search_queries": [user_query],
                "expected_urls": 20,
                "complexity": "medium",
                "strategy": "broad",
                "reasoning": "Fallback strategy due to parsing error"
            }

    async def discover_urls(
        self,
        db: AsyncSession,
        workflow_id: int,
        query: str,
        num_results: int = 20,
        date_range: str = "any",
        language: str = "pl"
    ) -> List[URLCandidate]:
        """
        Discover relevant URLs using Google Custom Search

        Args:
            db: Database session
            workflow_id: Workflow ID
            query: Search query
            num_results: Number of results to return
            date_range: Date filter (day, week, month, year, any)
            language: Search language

        Returns:
            List of URLCandidate objects
        """
        await self.log_reasoning(
            db, workflow_id, "discover_urls",
            content=f"Searching for: {query} ({num_results} results)",
            reasoning=f"Using Google Custom Search API to discover {num_results} relevant URLs"
        )

        if not self.google_search:
            await self.initialize()

        results = await self.google_search.search(
            query=query,
            num_results=num_results,
            date_range=date_range,
            language=language
        )

        candidates = []
        for result in results:
            candidate = URLCandidate(
                workflow_id=workflow_id,
                url=result["url"],
                title=result.get("title", "")[:500],
                relevance_score=float(result.get("relevance_score", 0.8)),
                source="google_search",
                metadata=json.dumps({
                    "snippet": result.get("snippet", ""),
                    "query": query,
                    "discovered_at": datetime.utcnow().isoformat()
                })
            )
            db.add(candidate)
            candidates.append(candidate)

        await self.log_reasoning(
            db, workflow_id, "discover_urls",
            content=f"Discovered {len(candidates)} URLs",
            reasoning=f"URL discovery completed using query: {query}"
        )

        return candidates

    async def rank_urls(
        self,
        db: AsyncSession,
        workflow_id: int,
        candidates: List[URLCandidate]
    ) -> List[URLCandidate]:
        """
        Rank and filter discovered URLs by relevance and quality

        Uses Claude to analyze URL titles and snippets for relevance.
        """
        await self.log_reasoning(
            db, workflow_id, "rank_urls",
            content=f"Ranking {len(candidates)} discovered URLs",
            reasoning="Using Claude AI to analyze relevance and quality of discovered URLs"
        )

        # Prepare URL data for analysis
        url_data = []
        for candidate in candidates:
            metadata = json.loads(candidate.meta_data) if candidate.meta_data else {}
            url_data.append({
                "id": candidate.id,
                "url": candidate.url,
                "title": candidate.title,
                "snippet": metadata.get("snippet", "")
            })

        # Use Claude to rank URLs
        system_prompt = """You are a relevance ranking expert. Given a list of search results,
rank them by relevance to the research goal. Return JSON with:
{
    "rankings": [{"id": number, "relevance_score": 0.0-1.0, "reason": "explanation"}],
    "filtered_out": [ids to remove]
}

Criteria:
- Relevance to research topic (40%)
- Source credibility (30%)
- Content quality indicators (20%)
- Freshness if time-sensitive (10%)
"""

        response = await self.claude.execute_simple(
            user_query=json.dumps(url_data[:20]),  # Limit to 20 for cost
            system_prompt=system_prompt,
            model="claude-3-5-sonnet-20241022"
        )

        try:
            result = json.loads(response)

            # Update relevance scores
            for ranking in result.get("rankings", []):
                for candidate in candidates:
                    if candidate.id == ranking["id"]:
                        candidate.relevance_score = ranking["relevance_score"]
                        break

            # Filter out low-quality URLs
            filtered_ids = set(result.get("filtered_out", []))
            ranked_candidates = [
                c for c in candidates
                if c.id not in filtered_ids and c.relevance_score >= 0.5
            ]

            # Sort by relevance
            ranked_candidates.sort(key=lambda x: x.relevance_score or 0, reverse=True)

            await self.log_reasoning(
                db, workflow_id, "rank_urls",
                content=f"Ranked {len(ranked_candidates)} URLs (filtered {len(candidates) - len(ranked_candidates)})",
                reasoning="Completed relevance ranking with Claude AI"
            )

            return ranked_candidates

        except json.JSONDecodeError:
            # Fallback: return original list sorted by existing score
            candidates.sort(key=lambda x: x.relevance_score or 0, reverse=True)
            return candidates

    async def execute_research(
        self,
        db: AsyncSession,
        workflow_id: int,
        user_query: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute complete research workflow

        Args:
            db: Database session
            workflow_id: Workflow ID
            user_query: User's research query
            config: Research configuration

        Returns:
            Dict with research results
        """
        # Step 1: Analyze query
        strategy = await self.analyze_query(db, workflow_id, user_query)

        # Step 2: Discover URLs for each search query
        all_candidates = []
        for search_query in strategy["search_queries"][:3]:  # Max 3 search iterations
            candidates = await self.discover_urls(
                db=db,
                workflow_id=workflow_id,
                query=search_query,
                num_results=config.get("max_urls", 20) // len(strategy["search_queries"]),
                date_range=config.get("date_range", "any"),
                language=config.get("language", "pl")
            )
            all_candidates.extend(candidates)

        await db.commit()

        # Step 3: Rank and filter URLs
        ranked_candidates = await self.rank_urls(db, workflow_id, all_candidates)

        # Step 4: Create research task record
        research_task = ResearchTask(
            workflow_id=workflow_id,
            task_type="url_discovery",
            description=f"URL discovery for: {user_query}",
            status="completed",
            assigned_agent=self.name,
            result=json.dumps({
                "strategy": strategy,
                "discovered_count": len(all_candidates),
                "ranked_count": len(ranked_candidates),
                "top_urls": [c.url for c in ranked_candidates[:10]]
            }),
            completed_at=datetime.utcnow()
        )
        db.add(research_task)

        return {
            "success": True,
            "strategy": strategy,
            "discovered_urls": len(all_candidates),
            "ranked_urls": len(ranked_candidates),
            "top_candidates": ranked_candidates[:20]
        }


# ============================================================================
# ScraperAgent - Multi-Engine Web Scraping
# ============================================================================


class ScraperAgent(BaseAgent):
    """
    ScraperAgent - Multi-engine web scraping specialist

    Capabilities:
    - Intelligent engine selection (HTTP, Playwright, Firecrawl)
    - Parallel batch scraping with concurrency control
    - Content extraction and cleaning
    - Error handling and retry logic
    - Support for JavaScript-heavy sites

    Tools:
    - scrape_urls (multi-engine scraping)
    """

    name = "ScraperAgent"
    description = "Multi-engine web scraping specialist"

    def __init__(self):
        super().__init__()
        self.orchestrator = CrawlerOrchestrator()

    async def analyze_urls(
        self,
        db: AsyncSession,
        workflow_id: int,
        urls: List[str]
    ) -> Dict[str, List[str]]:
        """
        Analyze URLs and determine optimal scraping strategy

        Returns:
            Dict with url groups by engine:
            - http: Static HTML sites (fastest)
            - playwright: JavaScript-heavy sites
            - firecrawl: Difficult sites with anti-bot
        """
        await self.log_reasoning(
            db, workflow_id, "analyze_urls",
            content=f"Analyzing {len(urls)} URLs for scraping strategy",
            reasoning="Determining optimal scraping engine for each URL based on domain patterns"
        )

        # Known domains that require JavaScript
        js_domains = {
            "twitter.com", "x.com", "facebook.com", "instagram.com",
            "linkedin.com", "youtube.com", "tiktok.com", "reddit.com"
        }

        http_urls = []
        playwright_urls = []
        firecrawl_urls = []

        for url in urls:
            # Check domain patterns
            if any(domain in url.lower() for domain in js_domains):
                playwright_urls.append(url)
            elif any(difficult in url.lower() for difficult in ["amazon", "ebay"]):
                firecrawl_urls.append(url)
            else:
                http_urls.append(url)

        strategy = {
            "http": http_urls,
            "playwright": playwright_urls,
            "firecrawl": firecrawl_urls
        }

        await self.log_reasoning(
            db, workflow_id, "analyze_urls",
            content=f"Scraping strategy: HTTP={len(http_urls)}, Playwright={len(playwright_urls)}, Firecrawl={len(firecrawl_urls)}",
            reasoning="URL classification based on domain patterns and known technical requirements"
        )

        return strategy

    async def scrape_batch(
        self,
        db: AsyncSession,
        workflow_id: int,
        urls: List[str],
        engine: CrawlEngine = None,
        concurrency: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Scrape a batch of URLs with specified engine

        Args:
            db: Database session
            workflow_id: Workflow ID
            urls: URLs to scrape
            engine: CrawlEngine to use (None = auto-select)
            concurrency: Max concurrent scrapes

        Returns:
            List of scrape results
        """
        await self.log_reasoning(
            db, workflow_id, "scrape_batch",
            content=f"Scraping {len(urls)} URLs with engine={engine.value if engine else 'auto'}",
            reasoning=f"Parallel scraping with concurrency={concurrency}"
        )

        results = await self.orchestrator.batch_crawl(
            urls=urls,
            engine=engine,
            force_engine=False,
            concurrency=concurrency
        )

        # Log results
        success_count = sum(1 for r in results if not r.error)
        error_count = len(results) - success_count

        await self.log_reasoning(
            db, workflow_id, "scrape_batch",
            content=f"Scraping complete: {success_count} succeeded, {error_count} failed",
            reasoning=f"Completed scraping batch with {concurrency} concurrent workers"
        )

        return [
            {
                "url": r.url,
                "title": r.title,
                "text": r.text,
                "links": r.links,
                "images": r.images,
                "engine": r.engine.value,
                "status_code": r.status_code,
                "error": r.error,
                "success": not r.error
            }
            for r in results
        ]

    async def execute_scraping(
        self,
        db: AsyncSession,
        workflow_id: int,
        urls: List[str],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute complete scraping workflow

        Args:
            db: Database session
            workflow_id: Workflow ID
            urls: URLs to scrape
            config: Scraping configuration

        Returns:
            Dict with scraping results
        """
        # Step 1: Analyze URLs
        strategy = await self.analyze_urls(db, workflow_id, urls)

        # Step 2: Scrape each group with optimal engine
        all_results = []
        concurrency = config.get("concurrency", 5)

        if strategy["http"]:
            results = await self.scrape_batch(
                db, workflow_id,
                strategy["http"],
                engine=CrawlEngine.HTTP,
                concurrency=concurrency
            )
            all_results.extend(results)

        if strategy["playwright"]:
            results = await self.scrape_batch(
                db, workflow_id,
                strategy["playwright"],
                engine=CrawlEngine.PLAYWRIGHT,
                concurrency=max(1, concurrency // 2)  # Lower concurrency for Playwright
            )
            all_results.extend(results)

        if strategy["firecrawl"] and config.get("use_firecrawl"):
            results = await self.scrape_batch(
                db, workflow_id,
                strategy["firecrawl"],
                engine=CrawlEngine.FIRECRAWL,
                concurrency=1  # Serial for Firecrawl (API limits)
            )
            all_results.extend(results)

        # Step 3: Create research task record
        success_count = sum(1 for r in all_results if r["success"])

        research_task = ResearchTask(
            workflow_id=workflow_id,
            task_type="web_scraping",
            description=f"Scraped {len(urls)} URLs",
            status="completed",
            assigned_agent=self.name,
            result=json.dumps({
                "total_urls": len(urls),
                "successful": success_count,
                "failed": len(urls) - success_count,
                "results": [
                    {
                        "url": r["url"],
                        "success": r["success"],
                        "text_length": len(r.get("text", ""))
                    }
                    for r in all_results
                ]
            }),
            completed_at=datetime.utcnow()
        )
        db.add(research_task)

        return {
            "success": True,
            "total_urls": len(urls),
            "successful": success_count,
            "failed": len(urls) - success_count,
            "results": all_results
        }


# ============================================================================
# AnalyzerAgent - Knowledge Extraction & Analysis
# ============================================================================


class AnalyzerAgent(BaseAgent):
    """
    AnalyzerAgent - Knowledge extraction and analysis specialist

    Capabilities:
    - Extract entities, relationships, and facts from text
    - Identify key insights and patterns
    - Perform sentiment analysis
    - Generate structured knowledge representations
    - Cross-reference and validate information

    Tools:
    - query_knowledge_base (vector search)
    - Claude API for advanced analysis
    """

    name = "AnalyzerAgent"
    description = "Knowledge extraction and analysis specialist"

    def __init__(self):
        super().__init__()
        self.claude = AnthropicToolClient()

    async def extract_entities(
        self,
        db: AsyncSession,
        workflow_id: int,
        text: str,
        url: str
    ) -> List[Dict[str, Any]]:
        """
        Extract entities from text using Claude

        Returns:
            List of entities with types and attributes
        """
        await self.log_reasoning(
            db, workflow_id, "extract_entities",
            content=f"Extracting entities from {url}",
            reasoning="Using Claude NLP to identify and categorize entities"
        )

        system_prompt = """You are an expert entity extractor. Extract all important entities from the text.
Return JSON with:
{
    "entities": [
        {
            "name": "entity name",
            "type": "person|organization|location|concept|event|other",
            "attributes": {"key": "value"},
            "confidence": 0.0-1.0,
            "context": "mentioning context"
        }
    ]
}

Focus on entities that are:
- Central to the topic
- Frequently mentioned
- Have clear definitions
- Are actionable insights
"""

        response = await self.claude.execute_simple(
            user_query=text[:8000],  # Limit for API
            system_prompt=system_prompt,
            model="claude-3-5-sonnet-20241022"
        )

        try:
            result = json.loads(response)
            entities = result.get("entities", [])

            await self.log_reasoning(
                db, workflow_id, "extract_entities",
                content=f"Extracted {len(entities)} entities",
                reasoning=f"Entity extraction completed with {len(entities)} entities found"
            )

            return entities
        except json.JSONDecodeError:
            return []

    async def extract_relationships(
        self,
        db: AsyncSession,
        workflow_id: int,
        text: str,
        entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract relationships between entities

        Returns:
            List of relationships with types and confidence
        """
        await self.log_reasoning(
            db, workflow_id, "extract_relationships",
            content="Extracting relationships between entities",
            reasoning="Using Claude to identify semantic relationships"
        )

        system_prompt = f"""You are a relationship extraction expert. Given these entities:
{json.dumps(entities, ensure_ascii=False)}

Extract relationships from the text. Return JSON:
{{
    "relationships": [
        {{
            "source": "entity1",
            "target": "entity2",
            "type": "causes|enables|part_of|related_to|contradicts|example_of|other",
            "description": "relationship description",
            "confidence": 0.0-1.0
        }}
    ]
}}"""

        response = await self.claude.execute_simple(
            user_query=text[:8000],
            system_prompt=system_prompt,
            model="claude-3-5-sonnet-20241022"
        )

        try:
            result = json.loads(response)
            relationships = result.get("relationships", [])

            await self.log_reasoning(
                db, workflow_id, "extract_relationships",
                content=f"Extracted {len(relationships)} relationships",
                reasoning=f"Relationship extraction completed with {len(relationships)} relationships"
            )

            return relationships
        except json.JSONDecodeError:
            return []

    async def extract_insights(
        self,
        db: AsyncSession,
        workflow_id: int,
        text: str
    ) -> List[Dict[str, Any]]:
        """
        Extract key insights and findings

        Returns:
            List of insights with importance ratings
        """
        await self.log_reasoning(
            db, workflow_id, "extract_insights",
            content="Extracting key insights",
            reasoning="Using Claude to identify actionable insights"
        )

        system_prompt = """You are an insight extraction expert. Extract the most important insights from the text.
Return JSON:
{
    "insights": [
        {
            "insight": "key finding",
            "importance": "high|medium|low",
            "category": "finding|trend|opportunity|risk|other",
            "evidence": ["supporting quotes"],
            "actionable": true/false
        }
    ]
}

Focus on:
- Novel information
- Actionable recommendations
- Important trends
- Key findings
- Critical insights
"""

        response = await self.claude.execute_simple(
            user_query=text[:8000],
            system_prompt=system_prompt,
            model="claude-3-5-sonnet-20241022"
        )

        try:
            result = json.loads(response)
            insights = result.get("insights", [])

            await self.log_reasoning(
                db, workflow_id, "extract_insights",
                content=f"Extracted {len(insights)} insights",
                reasoning=f"Insight extraction completed with {len(insights)} insights"
            )

            return insights
        except json.JSONDecodeError:
            return []

    async def analyze_content(
        self,
        db: AsyncSession,
        workflow_id: int,
        scraped_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze scraped content and extract knowledge

        Args:
            db: Database session
            workflow_id: Workflow ID
            scraped_data: List of scraped page data

        Returns:
            Dict with extracted knowledge
        """
        all_entities = []
        all_relationships = []
        all_insights = []

        for page in scraped_data:
            if not page.get("text") or page.get("error"):
                continue

            text = page["text"]
            url = page["url"]

            # Extract entities
            entities = await self.extract_entities(db, workflow_id, text, url)
            all_entities.extend(entities)

            # Extract relationships
            if entities:
                relationships = await self.extract_relationships(db, workflow_id, text, entities)
                all_relationships.extend(relationships)

            # Extract insights
            insights = await self.extract_insights(db, workflow_id, text)
            all_insights.extend(insights)

        # Create research task record
        research_task = ResearchTask(
            workflow_id=workflow_id,
            task_type="knowledge_extraction",
            description=f"Analyzed {len(scraped_data)} scraped pages",
            status="completed",
            assigned_agent=self.name,
            result=json.dumps({
                "pages_analyzed": len(scraped_data),
                "entities_extracted": len(all_entities),
                "relationships_extracted": len(all_relationships),
                "insights_extracted": len(all_insights)
            }),
            completed_at=datetime.utcnow()
        )
        db.add(research_task)

        return {
            "success": True,
            "entities": all_entities,
            "relationships": all_relationships,
            "insights": all_insights,
            "pages_analyzed": len(scraped_data)
        }


# ============================================================================
# OrganizerAgent - Knowledge Tree Construction
# ============================================================================


class OrganizerAgent(BaseAgent):
    """
    OrganizerAgent - Knowledge tree construction specialist

    Capabilities:
    - Build hierarchical knowledge structures
    - Organize entities into categories
    - Create semantic relationships
    - Generate knowledge taxonomies
    - Optimize for navigation and search

    Tools:
    - create_knowledge_tree (CategoryTreeGenerator)
    - save_to_database (persistence)
    """

    name = "OrganizerAgent"
    description = "Knowledge tree construction specialist"

    def __init__(self):
        super().__init__()
        self.claude = AnthropicToolClient()
        self.tree_generator = CategoryTreeGenerator()

    async def design_taxonomy(
        self,
        db: AsyncSession,
        workflow_id: int,
        user_query: str,
        entities: List[Dict[str, Any]],
        insights: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Design optimal taxonomy for knowledge organization

        Returns:
            Dict with taxonomy structure
        """
        await self.log_reasoning(
            db, workflow_id, "design_taxonomy",
            content="Designing knowledge taxonomy",
            reasoning="Using Claude to design optimal hierarchical structure"
        )

        system_prompt = f"""You are a knowledge architecture expert. Design a taxonomy for organizing this research.

User Query: {user_query}

Entities Sample: {json.dumps(entities[:20], ensure_ascii=False)}

Insights Sample: {json.dumps(insights[:10], ensure_ascii=False)}

Design a 3-4 level deep taxonomy. Return JSON:
{{
    "taxonomy": {{
        "Level 1 Category": {{
            "Level 2 Subcategory": {{
                "Level 3 Topic": {{
                    "description": "what goes here",
                    "examples": ["item1", "item2"]
                }}
            }}
        }}
    }},
    "reasoning": "explanation of structure"
}}

Guidelines:
- Logical hierarchy from general to specific
- Balanced categories (not too broad, not too narrow)
- Clear naming conventions
- Easy to navigate
"""

        response = await self.claude.execute_simple(
            user_query="Design the taxonomy",
            system_prompt=system_prompt,
            model="claude-3-5-sonnet-20241022"
        )

        try:
            result = json.loads(response)
            taxonomy = result.get("taxonomy", {})

            await self.log_reasoning(
                db, workflow_id, "design_taxonomy",
                content=f"Taxonomy designed with {len(taxonomy)} top-level categories",
                reasoning=result.get("reasoning", "Taxonomy based on content analysis")
            )

            return taxonomy
        except json.JSONDecodeError:
            # Fallback simple taxonomy
            return {
                "Main Topic": {
                    "Key Concepts": {},
                    "Findings": {},
                    "Resources": {}
                }
            }

    async def build_knowledge_tree(
        self,
        db: AsyncSession,
        workflow_id: int,
        project_id: int,
        user_query: str,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        insights: List[Dict[str, Any]],
        taxonomy: Optional[Dict[str, Any]] = None,
        category_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Build complete knowledge tree structure

        Args:
            db: Database session
            workflow_id: Workflow ID
            project_id: Project ID for saving
            user_query: Original user query
            entities: Extracted entities
            relationships: Extracted relationships
            insights: Extracted insights
            taxonomy: Optional pre-designed taxonomy
            category_id: Parent category ID

        Returns:
            Dict with tree structure and metadata
        """
        await self.log_reasoning(
            db, workflow_id, "build_knowledge_tree",
            content="Building knowledge tree structure",
            reasoning="Organizing extracted knowledge into hierarchical structure"
        )

        # Design taxonomy if not provided
        if not taxonomy:
            taxonomy = await self.design_taxonomy(
                db, workflow_id, user_query, entities, insights
            )

        # Convert entities and insights to tree structure
        tree_structure = {
            "query": user_query,
            "taxonomy": taxonomy,
            "entities": entities,
            "relationships": relationships,
            "insights": insights,
            "metadata": {
                "entity_count": len(entities),
                "relationship_count": len(relationships),
                "insight_count": len(insights),
                "created_at": datetime.utcnow().isoformat()
            }
        }

        # Save to database if category_id provided
        saved_category_id = None
        if category_id:
            try:
                # Use CategoryTreeGenerator to create tree
                from models.category import Category

                # Create main category
                main_category = Category(
                    project_id=project_id,
                    parent_id=category_id,
                    name=user_query[:100],
                    description=f"Knowledge tree for: {user_query}",
                    color="#4A90E2"
                )
                db.add(main_category)
                await db.flush()
                saved_category_id = main_category.id

                # Recursively create subcategories from taxonomy
                await self._create_taxonomy_categories(
                    db, project_id, saved_category_id, taxonomy
                )

                await db.commit()

                await self.log_reasoning(
                    db, workflow_id, "build_knowledge_tree",
                    content=f"Saved knowledge tree to database (category_id={saved_category_id})",
                    reasoning="Persisted tree structure in Category table"
                )

            except Exception as e:
                await db.rollback()
                await self.log_reasoning(
                    db, workflow_id, "build_knowledge_tree",
                    content=f"Failed to save tree: {str(e)}",
                    reasoning="Database save failed, continuing with in-memory tree"
                )

        # Create research task record
        research_task = ResearchTask(
            workflow_id=workflow_id,
            task_type="tree_building",
            description=f"Built knowledge tree for: {user_query}",
            status="completed",
            assigned_agent=self.name,
            result=json.dumps({
                "category_id": saved_category_id,
                "entity_count": len(entities),
                "relationship_count": len(relationships),
                "insight_count": len(insights)
            }),
            completed_at=datetime.utcnow()
        )
        db.add(research_task)

        return {
            "success": True,
            "tree_structure": tree_structure,
            "category_id": saved_category_id,
            "metadata": tree_structure["metadata"]
        }

    async def _create_taxonomy_categories(
        self,
        db: AsyncSession,
        project_id: int,
        parent_id: int,
        taxonomy: Dict[str, Any],
        depth: int = 0
    ):
        """Recursively create category structure from taxonomy"""
        if depth > 3:  # Limit depth to 4 levels
            return

        from models.category import Category

        for name, content in taxonomy.items():
            if isinstance(content, dict):
                # This is a category node
                category = Category(
                    project_id=project_id,
                    parent_id=parent_id,
                    name=name[:100],
                    description=content.get("description", "")[:500],
                    color="#4A90E2"
                )
                db.add(category)
                await db.flush()

                # Recursively create children
                await self._create_taxonomy_categories(
                    db, project_id, category.id, content, depth + 1
                )

    async def synthesize_summary(
        self,
        db: AsyncSession,
        workflow_id: int,
        user_query: str,
        tree_structure: Dict[str, Any]
    ) -> str:
        """
        Generate comprehensive summary of knowledge tree

        Returns:
            Summary text
        """
        await self.log_reasoning(
            db, workflow_id, "synthesize_summary",
            content="Generating knowledge tree summary",
            reasoning="Using Claude to create comprehensive summary"
        )

        system_prompt = """You are a knowledge synthesis expert. Create a comprehensive summary of this knowledge tree.

The summary should include:
1. Executive summary (2-3 sentences)
2. Key findings (bullet points)
3. Main categories discovered
4. Important insights
5. Action items or recommendations

Write in clear, professional language suitable for a knowledge management system."""

        summary_input = f"""
User Query: {user_query}

Tree Structure:
{json.dumps(tree_structure.get("taxonomy", {}), ensure_ascii=False)[:3000]}

Entities: {len(tree_structure.get("entities", []))}
Relationships: {len(tree_structure.get("relationships", []))}
Insights: {len(tree_structure.get("insights", []))}

Top Insights:
{json.dumps(tree_structure.get("insights", [])[:5], ensure_ascii=False)}
"""

        summary = await self.claude.execute_simple(
            user_query=summary_input,
            system_prompt=system_prompt,
            model="claude-3-5-sonnet-20241022"
        )

        await self.log_reasoning(
            db, workflow_id, "synthesize_summary",
            content="Summary generated successfully",
            reasoning="Created comprehensive summary of knowledge tree"
        )

        return summary


# ============================================================================
# Agent Factory
# ============================================================================


class AgentFactory:
    """Factory for creating agent instances"""

    _agents = {
        "research": ResearchAgent,
        "scraper": ScraperAgent,
        "analyzer": AnalyzerAgent,
        "organizer": OrganizerAgent
    }

    @classmethod
    def create_agent(cls, agent_type: str) -> BaseAgent:
        """Create agent instance by type"""
        agent_class = cls._agents.get(agent_type.lower())
        if not agent_class:
            raise ValueError(f"Unknown agent type: {agent_type}")
        return agent_class()

    @classmethod
    def get_available_agents(cls) -> List[str]:
        """Get list of available agent types"""
        return list(cls._agents.keys())


# Global agent instances for reuse
_agent_instances: Dict[str, BaseAgent] = {}


def get_agent(agent_type: str) -> BaseAgent:
    """Get or create agent instance (singleton pattern)"""
    if agent_type not in _agent_instances:
        _agent_instances[agent_type] = AgentFactory.create_agent(agent_type)
    return _agent_instances[agent_type]
