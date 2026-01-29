"""
KnowledgeTree - Agentic Crawl Workflow
Orchestrates prompt-driven AI extraction from URLs and YouTube videos
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import json

from models.crawl_job import CrawlJob, CrawlStatus
from models.document import Document, DocumentType, ProcessingStatus
from models.category import Category
from models.chunk import Chunk
from models.agent_workflow import AgentWorkflow, WorkflowStatus, WorkflowTemplate
from services.agents import get_agent, ScraperAgent, AnalyzerAgent, OrganizerAgent
from services.youtube_transcriber import YouTubeTranscriber
from services.text_chunker import TextChunker
from services.embedding_generator import EmbeddingGenerator
from services.crawler_orchestrator import CrawlEngine
from services.intelligent_crawler_selector import IntelligentCrawlerSelector


class AgenticCrawlWorkflow:
    """
    Orchestrates prompt-driven AI extraction from web content and YouTube videos.

    User's Vision:
    1. Provide URLs (or YouTube videos) + custom natural language prompt
    2. System crawls/transcribes content
    3. AI agents extract structured information according to the prompt
    4. Results organized into knowledge tree and saved to project

    Examples of prompts:
    - "wyciągnij wszystkie firmy z nazwą, adresem, danymi kontaktowymi"
    - "wyciągnij wszystkie informacje odnośnie metodyki konserwacji drewna"
    - "wejdź na film YouTube, wyciągnij transkrypcję i zbuduj artykuł"

    Workflow:
    1. Content Acquisition: Scrape URLs or transcribe YouTube
    2. Prompt-Guided Extraction: Use AnalyzerAgent with custom prompt
    3. Knowledge Organization: Use OrganizerAgent to build tree
    4. Persistence: Save as Document + Category tree
    """

    def __init__(self):
        from core.config import settings

        self.scraper_agent: ScraperAgent = get_agent("scraper")
        self.analyzer_agent: AnalyzerAgent = get_agent("analyzer")
        self.organizer_agent: OrganizerAgent = get_agent("organizer")
        self.youtube_transcriber = YouTubeTranscriber(anthropic_api_key=settings.ANTHROPIC_API_KEY)
        self.text_chunker = TextChunker()
        self.embedding_generator = EmbeddingGenerator()

        # Intelligent engine selector (auto-detect Firecrawl availability)
        firecrawl_available = bool(settings.FIRECRAWL_API_KEY)
        self.engine_selector = IntelligentCrawlerSelector(firecrawl_available=firecrawl_available)

    async def execute(
        self,
        db: AsyncSession,
        crawl_job_id: int,
        urls: List[str],
        agent_prompt: str,
        project_id: int,
        engine: Optional[CrawlEngine] = None,
        category_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute agentic crawl workflow with custom extraction prompt.

        Args:
            db: Database session
            crawl_job_id: CrawlJob ID for tracking
            urls: List of URLs to process (can include YouTube URLs)
            agent_prompt: Custom natural language prompt for extraction
            project_id: Project ID to save results
            engine: Optional crawl engine (HTTP, Playwright, Firecrawl)
            category_id: Optional parent category for organization

        Returns:
            Dict with extraction results and document IDs
        """
        # Create AgentWorkflow record
        agent_workflow = AgentWorkflow(
            name=f"Agentic Extraction: {agent_prompt[:50]}...",
            template=WorkflowTemplate.CUSTOM,  # Using CUSTOM template for agentic extraction
            user_query=agent_prompt,
            status=WorkflowStatus.RUNNING,  # Using RUNNING (legacy alias for PROCESSING)
            project_id=project_id,
            config=json.dumps({
                "urls": urls,
                "agent_prompt": agent_prompt,
                "engine": engine.value if engine else "auto"
            })
        )
        db.add(agent_workflow)
        await db.flush()

        # Update CrawlJob with workflow link
        crawl_job = await db.get(CrawlJob, crawl_job_id)
        if crawl_job:
            crawl_job.agent_workflow_id = agent_workflow.id
            crawl_job.status = CrawlStatus.IN_PROGRESS

        await db.commit()

        try:
            # Step 0: Intelligent Engine Selection (if not specified)
            if engine is None:
                # Automatically select optimal engine based on URLs and task
                engine = await self.engine_selector.select_engine(
                    urls=urls,
                    agent_prompt=agent_prompt,
                    use_ai_analysis=True
                )

                # Log the selection
                await self.analyzer_agent.log_reasoning(
                    db, agent_workflow.id, "engine_selection",
                    content=f"Auto-selected engine: {engine.value}",
                    reasoning=f"Intelligent selection for: {agent_prompt[:100]}"
                )

                # Update workflow config with selected engine
                config = json.loads(agent_workflow.config)
                config["engine"] = engine.value
                config["engine_auto_selected"] = True
                agent_workflow.config = json.dumps(config)
                await db.commit()

            # Step 1: Content Acquisition
            scraped_content = await self._acquire_content(
                db, agent_workflow.id, urls, engine
            )

            if not scraped_content:
                raise ValueError("No content could be acquired from URLs")

            # Step 2: Prompt-Guided Extraction
            extraction_results = await self._extract_with_prompt(
                db, agent_workflow.id, scraped_content, agent_prompt
            )

            # Step 3: Knowledge Organization
            tree_structure = await self._organize_knowledge(
                db, agent_workflow.id, project_id, agent_prompt,
                extraction_results, category_id
            )

            # Step 4: Create Document + Chunks
            document = await self._create_document_with_chunks(
                db, crawl_job_id, project_id, agent_prompt, scraped_content,
                extraction_results, tree_structure
            )

            # Update workflow status
            agent_workflow.status = WorkflowStatus.COMPLETED
            agent_workflow.completed_at = datetime.utcnow()
            agent_workflow.execution_log = json.dumps({
                "urls_processed": len(urls),
                "entities_extracted": len(extraction_results.get("entities", [])),
                "insights_extracted": len(extraction_results.get("insights", [])),
                "categories_created": len(tree_structure.get("taxonomy", {})),
                "document_id": document.id
            })

            # Update CrawlJob
            if crawl_job:
                crawl_job.status = CrawlStatus.COMPLETED
                crawl_job.document_id = document.id
                crawl_job.urls_crawled = len(scraped_content)
                crawl_job.last_crawl_at = datetime.utcnow()

            await db.commit()

            return {
                "success": True,
                "document_id": document.id,
                "workflow_id": agent_workflow.id,
                "urls_processed": len(urls),
                "entities_extracted": len(extraction_results.get("entities", [])),
                "insights_extracted": len(extraction_results.get("insights", [])),
                "categories_created": len(tree_structure.get("taxonomy", {})),
                "chunks_created": len(extraction_results.get("chunks", []))
            }

        except Exception as e:
            # Update workflow and crawl job status to failed
            agent_workflow.status = WorkflowStatus.FAILED
            agent_workflow.error_message = str(e)
            agent_workflow.completed_at = datetime.utcnow()

            if crawl_job:
                crawl_job.status = CrawlStatus.FAILED
                crawl_job.error_message = str(e)

            await db.commit()

            raise

    async def _acquire_content(
        self,
        db: AsyncSession,
        workflow_id: int,
        urls: List[str],
        engine: Optional[CrawlEngine]
    ) -> List[Dict[str, Any]]:
        """
        Acquire content from URLs (web scraping or YouTube transcription).

        Returns:
            List of content dicts with {url, title, text, source_type}
        """
        scraped_content = []

        # Separate YouTube URLs from web URLs
        youtube_urls = [url for url in urls if "youtube.com" in url or "youtu.be" in url]
        web_urls = [url for url in urls if url not in youtube_urls]

        # Process YouTube videos
        for youtube_url in youtube_urls:
            try:
                transcript_result = await self.youtube_transcriber.get_transcript(youtube_url)

                if transcript_result.transcript:
                    scraped_content.append({
                        "url": youtube_url,
                        "title": transcript_result.video_metadata.title,
                        "text": transcript_result.transcript,
                        "source_type": "youtube",
                        "metadata": {
                            "video_id": transcript_result.video_metadata.video_id,
                            "duration_seconds": transcript_result.video_metadata.duration_seconds,
                            "channel": transcript_result.video_metadata.channel,
                            "language": transcript_result.language
                        }
                    })

                await self.analyzer_agent.log_reasoning(
                    db, workflow_id, "acquire_youtube",
                    content=f"Transcribed YouTube: {youtube_url}",
                    reasoning=f"Extracted {len(transcript_result.transcript)} chars"
                )

            except Exception as e:
                await self.analyzer_agent.log_reasoning(
                    db, workflow_id, "acquire_youtube_error",
                    content=f"Failed to transcribe {youtube_url}: {str(e)}",
                    reasoning="YouTube transcription error"
                )

        # Process web URLs
        if web_urls:
            scrape_results = await self.scraper_agent.scrape_batch(
                db, workflow_id, web_urls, engine, concurrency=5
            )

            for result in scrape_results:
                if result.get("success") and result.get("text"):
                    scraped_content.append({
                        "url": result["url"],
                        "title": result.get("title", ""),
                        "text": result["text"],
                        "source_type": "web",
                        "metadata": {
                            "engine": result.get("engine"),
                            "status_code": result.get("status_code"),
                            "links_count": len(result.get("links", [])),
                            "images_count": len(result.get("images", []))
                        }
                    })

        await db.commit()

        return scraped_content

    async def _extract_with_prompt(
        self,
        db: AsyncSession,
        workflow_id: int,
        scraped_content: List[Dict[str, Any]],
        agent_prompt: str
    ) -> Dict[str, Any]:
        """
        Extract structured information using custom agent prompt.

        Modified AnalyzerAgent methods to accept custom extraction guidance.

        Returns:
            Dict with entities, relationships, insights
        """
        all_entities = []
        all_relationships = []
        all_insights = []

        await self.analyzer_agent.log_reasoning(
            db, workflow_id, "extract_with_prompt",
            content=f"Extracting with custom prompt: {agent_prompt}",
            reasoning=f"Processing {len(scraped_content)} content items with AI-guided extraction"
        )

        for content in scraped_content:
            text = content["text"]
            url = content["url"]

            # Extract entities with custom prompt guidance
            entities = await self._extract_entities_with_prompt(
                db, workflow_id, text, url, agent_prompt
            )
            all_entities.extend(entities)

            # Extract relationships
            if entities:
                relationships = await self.analyzer_agent.extract_relationships(
                    db, workflow_id, text, entities
                )
                all_relationships.extend(relationships)

            # Extract insights with custom prompt guidance
            insights = await self._extract_insights_with_prompt(
                db, workflow_id, text, agent_prompt
            )
            all_insights.extend(insights)

        await db.commit()

        return {
            "entities": all_entities,
            "relationships": all_relationships,
            "insights": all_insights
        }

    async def _extract_entities_with_prompt(
        self,
        db: AsyncSession,
        workflow_id: int,
        text: str,
        url: str,
        custom_prompt: str
    ) -> List[Dict[str, Any]]:
        """
        Extract entities guided by custom prompt.

        Enhances AnalyzerAgent.extract_entities() with custom extraction instructions.
        """
        from services.claude_tool_client import AnthropicToolClient

        claude = AnthropicToolClient()

        system_prompt = f"""You are an expert entity extractor working with a specific extraction goal.

USER'S EXTRACTION GOAL:
{custom_prompt}

Your task is to extract entities from the text that are relevant to this goal.
Return JSON with:
{{
    "entities": [
        {{
            "name": "entity name",
            "type": "person|organization|location|product|concept|contact_info|methodology|other",
            "attributes": {{"key": "value"}},
            "confidence": 0.0-1.0,
            "context": "mentioning context",
            "relevance_to_goal": "how this relates to user's extraction goal"
        }}
    ]
}}

Focus on entities that match the user's extraction goal. Include:
- All entities explicitly mentioned in the goal
- Related contextual entities
- Structured data (names, addresses, contacts, dates, etc.)
"""

        response = await claude.execute_simple(
            prompt=text[:8000],
            system_prompt=system_prompt,
            model="claude-sonnet-4-20250514"
        )

        try:
            result = json.loads(response)
            entities = result.get("entities", [])

            await self.analyzer_agent.log_reasoning(
                db, workflow_id, "extract_entities_with_prompt",
                content=f"Extracted {len(entities)} entities for: {url}",
                reasoning=f"Custom prompt-guided extraction: {custom_prompt[:100]}"
            )

            return entities
        except json.JSONDecodeError:
            return []

    async def _extract_insights_with_prompt(
        self,
        db: AsyncSession,
        workflow_id: int,
        text: str,
        custom_prompt: str
    ) -> List[Dict[str, Any]]:
        """
        Extract insights guided by custom prompt.

        Enhances AnalyzerAgent.extract_insights() with custom extraction instructions.
        """
        from services.claude_tool_client import AnthropicToolClient

        claude = AnthropicToolClient()

        system_prompt = f"""You are an insight extraction expert working with a specific extraction goal.

USER'S EXTRACTION GOAL:
{custom_prompt}

Your task is to extract key insights and findings that are relevant to this goal.
Return JSON:
{{
    "insights": [
        {{
            "insight": "key finding or insight",
            "importance": "high|medium|low",
            "category": "finding|trend|methodology|recommendation|contact|other",
            "evidence": ["supporting quotes or data"],
            "actionable": true/false,
            "relevance_to_goal": "how this relates to user's extraction goal"
        }}
    ]
}}

Focus on insights that directly address the user's extraction goal.
"""

        response = await claude.execute_simple(
            prompt=text[:8000],
            system_prompt=system_prompt,
            model="claude-sonnet-4-20250514"
        )

        try:
            result = json.loads(response)
            insights = result.get("insights", [])

            await self.analyzer_agent.log_reasoning(
                db, workflow_id, "extract_insights_with_prompt",
                content=f"Extracted {len(insights)} insights",
                reasoning=f"Custom prompt-guided extraction: {custom_prompt[:100]}"
            )

            return insights
        except json.JSONDecodeError:
            return []

    async def _organize_knowledge(
        self,
        db: AsyncSession,
        workflow_id: int,
        project_id: int,
        user_query: str,
        extraction_results: Dict[str, Any],
        category_id: Optional[int]
    ) -> Dict[str, Any]:
        """
        Organize extracted knowledge into hierarchical tree structure.

        Uses OrganizerAgent.build_knowledge_tree() with extraction results.
        """
        tree_result = await self.organizer_agent.build_knowledge_tree(
            db=db,
            workflow_id=workflow_id,
            project_id=project_id,
            user_query=user_query,
            entities=extraction_results.get("entities", []),
            relationships=extraction_results.get("relationships", []),
            insights=extraction_results.get("insights", []),
            taxonomy=None,  # Auto-design taxonomy
            category_id=category_id
        )

        await db.commit()

        return tree_result.get("tree_structure", {})

    async def _create_document_with_chunks(
        self,
        db: AsyncSession,
        crawl_job_id: int,
        project_id: int,
        agent_prompt: str,
        scraped_content: List[Dict[str, Any]],
        extraction_results: Dict[str, Any],
        tree_structure: Dict[str, Any]
    ) -> Document:
        """
        Create Document with chunks containing extracted knowledge.

        Saves:
        - Document record (WEB or TEXT type)
        - Chunks with embeddings
        - Links to category tree
        """
        # Determine document type based on content sources
        source_types = set(content["source_type"] for content in scraped_content)
        doc_type = DocumentType.WEB if "web" in source_types else DocumentType.TEXT

        # Create document title from first URL and prompt
        first_url = scraped_content[0]["url"] if scraped_content else "Unknown"
        doc_title = f"{agent_prompt[:50]}... | {first_url}"

        # Create document
        document = Document(
            filename=first_url,
            title=doc_title,
            source_type=doc_type,
            source_url=first_url,
            crawl_job_id=crawl_job_id,
            project_id=project_id,
            processing_status=ProcessingStatus.PROCESSING,
            extraction_metadata={
                "agent_prompt": agent_prompt,
                "urls_processed": len(scraped_content),
                "entities_extracted": len(extraction_results.get("entities", [])),
                "insights_extracted": len(extraction_results.get("insights", [])),
                "extraction_type": "agentic_crawl"
            }
        )

        db.add(document)
        await db.flush()

        # Create chunks from extracted insights and entities
        chunks_created = 0

        # Create chunks from insights (most valuable content)
        for insight in extraction_results.get("insights", []):
            chunk_text = f"[INSIGHT] {insight.get('insight', '')}\n\n"
            chunk_text += f"Category: {insight.get('category', 'N/A')}\n"
            chunk_text += f"Importance: {insight.get('importance', 'N/A')}\n"
            chunk_text += f"Evidence: {'; '.join(insight.get('evidence', []))}\n"
            chunk_text += f"Relevance: {insight.get('relevance_to_goal', '')}"

            # Generate embedding
            embedding = self.embedding_generator.generate_embedding(chunk_text)

            chunk = Chunk(
                text=chunk_text,
                embedding=embedding,
                chunk_index=chunks_created,
                chunk_metadata=json.dumps({
                    "type": "insight",
                    "category": insight.get("category"),
                    "importance": insight.get("importance")
                }),
                document_id=document.id,
                has_embedding=1
            )

            db.add(chunk)
            chunks_created += 1

        # Create chunks from entities (structured data)
        for entity in extraction_results.get("entities", [])[:50]:  # Limit to 50 entities
            chunk_text = f"[ENTITY] {entity.get('name', '')}\n\n"
            chunk_text += f"Type: {entity.get('type', 'N/A')}\n"
            chunk_text += f"Attributes: {json.dumps(entity.get('attributes', {}), ensure_ascii=False)}\n"
            chunk_text += f"Context: {entity.get('context', '')}\n"
            chunk_text += f"Relevance: {entity.get('relevance_to_goal', '')}"

            embedding = self.embedding_generator.generate_embedding(chunk_text)

            chunk = Chunk(
                text=chunk_text,
                embedding=embedding,
                chunk_index=chunks_created,
                chunk_metadata=json.dumps({
                    "type": "entity",
                    "entity_type": entity.get("type"),
                    "confidence": entity.get("confidence")
                }),
                document_id=document.id,
                has_embedding=1
            )

            db.add(chunk)
            chunks_created += 1

        # Update document status
        document.processing_status = ProcessingStatus.COMPLETED
        document.processed_at = datetime.utcnow()

        await db.flush()

        return document


# Singleton instance
agentic_crawl_workflow = AgenticCrawlWorkflow()
