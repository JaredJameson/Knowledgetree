"""
KnowledgeTree - Agentic Crawl Workflow
Orchestrates prompt-driven AI extraction from URLs and YouTube videos
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from urllib.parse import urlparse
import json
import logging

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
from services.agentic_browser import AgenticBrowser


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
        category_id: Optional[int] = None,
        task: Optional[Any] = None  # Celery task for real-time progress updates
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
            task: Optional Celery task for real-time progress reporting

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
            logger = logging.getLogger(__name__)
            
            # Decision: Use AgenticBrowser for single URL, traditional scraping for multiple URLs
            if len(urls) == 1:
                logger.info(f"🤖 Using AgenticBrowser for autonomous navigation: {urls[0]}")
                
                from core.config import settings
                
                # Initialize AgenticBrowser with Playwright + Claude
                agentic_browser = AgenticBrowser(
                    anthropic_api_key=settings.ANTHROPIC_API_KEY,
                    max_pages=20,
                    max_depth=3,
                    headless=True
                )
                
                # Progress callback for workflow logging AND Celery progress
                async def progress_callback(**kwargs):
                    """Report agentic browsing progress to workflow logs and Celery task"""
                    status = kwargs.get('status', 'browsing')
                    url = kwargs.get('url', '')
                    pages_visited = kwargs.get('pages_visited', 0)
                    pages_total = kwargs.get('pages_total', 20)
                    
                    # Extract additional details from kwargs
                    decision = kwargs.get('decision', '')
                    reasoning = kwargs.get('reasoning', '')
                    content_length = kwargs.get('content_length', 0)
                    
                    # Log to workflow for debugging
                    await self.analyzer_agent.log_reasoning(
                        db, agent_workflow.id, f"agentic_{status}",
                        content=f"AgenticBrowser: {status} - {url}",
                        reasoning=json.dumps(kwargs)
                    )
                    
                    # Update Celery task state for real-time frontend progress
                    if task:
                        # Calculate percentage (10-80% range during browsing)
                        base_progress = 10
                        browsing_range = 70  # 10% to 80%
                        progress_pct = base_progress + int((pages_visited / pages_total) * browsing_range)
                        
                        # Build detailed message based on status
                        if status == 'observing':
                            message = f'Observing page: {url}'
                        elif status == 'thinking':
                            message = f'AI analyzing page ({pages_visited}/{pages_total})'
                            if decision:
                                message += f' - Decision: {decision}'
                        elif status == 'extracted':
                            entities_count = len(kwargs.get('extracted', {}).get('structured_data', {}).get('entities', []))
                            message = f'Content extracted from page {pages_visited} ({content_length} chars'
                            if entities_count > 0:
                                message += f', {entities_count} entities'
                            message += ')'
                        elif status == 'browsing':
                            message = f'Browsing page: {url}'
                        else:
                            message = f'{status}: {url}'
                        
                        task.update_state(
                            state='PROGRESS',
                            meta={
                                'current': 2,
                                'total': 5,
                                'status': 'Agentic browsing in progress',
                                'step': 'browsing',
                                'percentage': progress_pct,
                                'message': message,
                                'pages_visited': pages_visited,
                                'pages_total': pages_total,
                                'current_url': url,
                                'decision': decision,
                                'reasoning': reasoning[:100] if reasoning else ''
                            }
                        )
                
                # Execute autonomous browsing with observe-think-act loop
                extracted_contents = await agentic_browser.browse_with_intent(
                    start_url=urls[0],
                    user_intent=agent_prompt,
                    db=db,
                    workflow_id=agent_workflow.id,
                    progress_callback=progress_callback
                )
                
                if not extracted_contents:
                    raise ValueError("AgenticBrowser extracted no content from URL")
                
                # Convert AgenticBrowser.ExtractedContent → scraped_content format
                # This ensures compatibility with downstream _extract_with_prompt()
                scraped_content = []
                for content in extracted_contents:
                    scraped_content.append({
                        'url': content.url,
                        'title': content.title,
                        'text': content.main_content,
                        'source_type': 'web',
                        'metadata': {
                            'engine': 'agentic_browser',
                            'extraction_method': content.extraction_method,
                            'entities_count': len(content.structured_data.get('entities', [])),
                            'insights_count': len(content.structured_data.get('insights', [])),
                            'timestamp': content.timestamp.isoformat()
                        }
                    })
                
                stats = agentic_browser.get_statistics()
                logger.info(
                    f"✅ AgenticBrowser complete: {stats['pages_visited']} pages visited, "
                    f"{stats['content_extracted']} content items extracted, "
                    f"{stats['total_entities']} entities, {stats['total_insights']} insights"
                )
                
                await self.analyzer_agent.log_reasoning(
                    db, agent_workflow.id, "agentic_complete",
                    content=f"Agentic browsing completed successfully",
                    reasoning=json.dumps(stats)
                )
                
            else:
                # Multiple URLs - use traditional scraping (legacy path)
                logger.info(f"Multiple URLs ({len(urls)}), using traditional scraping...")
                
                # Intelligent engine selection if not specified
                if engine is None:
                    engine = await self.engine_selector.select_engine(
                        urls=urls,
                        agent_prompt=agent_prompt,
                        use_ai_analysis=True
                    )
                    
                    await self.analyzer_agent.log_reasoning(
                        db, agent_workflow.id, "engine_selection",
                        content=f"Auto-selected engine: {engine.value}",
                        reasoning=f"Intelligent selection for: {agent_prompt[:100]}"
                    )
                    
                    config = json.loads(agent_workflow.config)
                    config["engine"] = engine.value
                    config["engine_auto_selected"] = True
                    agent_workflow.config = json.dumps(config)
                    await db.commit()
                
                # Traditional content acquisition
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

    async def _discover_relevant_links(
        self,
        db: AsyncSession,
        workflow_id: int,
        initial_url: str,
        scraped_result: Dict[str, Any],
        agent_prompt: str,
        max_links: int = 15
    ) -> List[str]:
        """
        Use LLM to analyze links and identify which are relevant to user's goal.
        
        This enables intelligent multi-page crawling where the agent:
        1. Analyzes links from the main page
        2. Uses the user's prompt to filter relevant links
        3. Returns URLs that likely contain the desired content
        
        Example:
            User prompt: "wyciągnij wszystkie artykuły i treści z tych artykułów"
            Main page: anthropic.com/engineering (has links to 15 blog articles)
            Result: Returns 15 article URLs to crawl
        
        Args:
            initial_url: The main page URL
            scraped_result: Scrape result with links list
            agent_prompt: User's extraction prompt
            max_links: Maximum links to discover (default 15)
            
        Returns:
            List of relevant URLs to crawl (absolute URLs)
        """
        from urllib.parse import urljoin, urlparse
        import anthropic
        from core.config import settings
        
        # Get links from scrape result (scrape_batch returns dict with "links" key directly)
        raw_links = scraped_result.get("links", [])
        
        if not raw_links or len(raw_links) == 0:
            logger.info(f"No links found on {initial_url}")
            return []
        
        # Normalize URLs (relative → absolute, remove fragments)
        def normalize_url(link: str) -> Optional[str]:
            """Convert relative to absolute URL and clean"""
            try:
                absolute = urljoin(initial_url, link)
                parsed = urlparse(absolute)
                
                # Remove fragment and optionally query
                clean = parsed._replace(fragment='')
                
                # Same-domain check
                base_domain = urlparse(initial_url).netloc
                if parsed.netloc != base_domain:
                    return None  # Skip external links
                
                return clean.geturl()
            except Exception:
                return None
        
        normalized_links = []
        seen = set()
        
        for link in raw_links[:100]:  # Limit to first 100 for LLM processing
            clean_url = normalize_url(link)
            if clean_url and clean_url not in seen and clean_url != initial_url:
                normalized_links.append(clean_url)
                seen.add(clean_url)
        
        if not normalized_links:
            logger.info(f"No valid same-domain links found on {initial_url}")
            return []
        
        logger.info(f"Found {len(normalized_links)} unique links on {initial_url}, analyzing with LLM...")
        
        # Use Claude to filter relevant links
        system_prompt = f"""You are a web crawling assistant helping identify relevant URLs.

The user wants to: "{agent_prompt}"

The main page at {initial_url} contains {len(normalized_links)} links.

Your task:
1. Analyze which links are MOST RELEVANT to the user's goal
2. Filter out navigation, footer, legal, unrelated pages
3. Prioritize content pages that match the user's intent
4. Return ONLY URLs that likely contain the target information

Return a JSON array of relevant URLs (up to {max_links} URLs).

Example:
User goal: "extract all blog articles and their content"
Relevant: ["/blog/2024-01-15-ai-agents", "/blog/2024-01-20-tool-use", ...]
Not relevant: ["/about", "/careers", "/contact", "/privacy", "/terms"]

Return ONLY valid JSON array of strings, no explanation."""

        user_message = f"""Here are the links from {initial_url}:

{chr(10).join(f"{i+1}. {url}" for i, url in enumerate(normalized_links[:50]))}

Return JSON array of the {max_links} most relevant URLs for: "{agent_prompt}"
"""
        
        try:
            # Call Claude API
            client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            
            response = await client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                temperature=0,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )
            
            # Parse response
            content = response.content[0].text
            
            # Extract JSON array (handle markdown code blocks)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            import json
            relevant_urls = json.loads(content)
            
            # Validate and limit
            if not isinstance(relevant_urls, list):
                logger.warning(f"LLM returned non-list: {relevant_urls}")
                return []
            
            validated_urls = []
            for url in relevant_urls[:max_links]:
                if isinstance(url, str) and url.startswith('http'):
                    validated_urls.append(url)
            
            logger.info(
                f"✅ Link Discovery: Found {len(validated_urls)} relevant URLs "
                f"from {len(normalized_links)} total links"
            )
            
            # Log discovery for debugging
            await self.analyzer_agent.log_reasoning(
                db, workflow_id, "link_discovery",
                content=f"Discovered {len(validated_urls)} relevant links: {validated_urls[:3]}...",
                reasoning=f"LLM filtered {len(normalized_links)} links → {len(validated_urls)} relevant for: '{agent_prompt[:50]}...'"
            )
            
            return validated_urls
            
        except Exception as e:
            logger.error(f"Link discovery failed: {e}")
            # Fallback: return first N links if LLM fails
            return normalized_links[:max_links]

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

        # Clean response - remove markdown code fences if present
        import re
        cleaned_response = response.strip()
        if cleaned_response.startswith("```"):
            match = re.search(r'```(?:json)?\s*\n(.*?)\n```', cleaned_response, re.DOTALL)
            if match:
                cleaned_response = match.group(1)

        try:
            result = json.loads(cleaned_response)
            entities = result.get("entities", [])

            await self.analyzer_agent.log_reasoning(
                db, workflow_id, "extract_entities_with_prompt",
                content=f"Extracted {len(entities)} entities for: {url}",
                reasoning=f"Custom prompt-guided extraction: {custom_prompt[:100]}"
            )

            return entities
        except json.JSONDecodeError as e:
            # Log the raw response for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"JSON decode error in extract_entities: {e}")
            logger.error(f"Raw Claude response: {response[:500]}")
            
            await self.analyzer_agent.log_reasoning(
                db, workflow_id, "extract_entities_error",
                content=f"Failed to parse entities JSON for: {url}",
                reasoning=f"JSONDecodeError: {str(e)}, response preview: {response[:200]}"
            )
            
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

        # Clean response - remove markdown code fences if present
        import re
        cleaned_response = response.strip()
        if cleaned_response.startswith("```"):
            match = re.search(r'```(?:json)?\s*\n(.*?)\n```', cleaned_response, re.DOTALL)
            if match:
                cleaned_response = match.group(1)

        try:
            result = json.loads(cleaned_response)
            insights = result.get("insights", [])

            await self.analyzer_agent.log_reasoning(
                db, workflow_id, "extract_insights_with_prompt",
                content=f"Extracted {len(insights)} insights",
                reasoning=f"Custom prompt-guided extraction: {custom_prompt[:100]}"
            )

            return insights
        except json.JSONDecodeError as e:
            # Log the raw response for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"JSON decode error in extract_insights: {e}")
            logger.error(f"Raw Claude response: {response[:500]}")
            
            await self.analyzer_agent.log_reasoning(
                db, workflow_id, "extract_insights_error",
                content=f"Failed to parse insights JSON",
                reasoning=f"JSONDecodeError: {str(e)}, response preview: {response[:200]}"
            )
            
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

        # Create document title from page title and domain
        first_content = scraped_content[0] if scraped_content else {}
        page_title = first_content.get("title", "Untitled")
        first_url = first_content.get("url", "Unknown")

        # Extract domain for cleaner title
        domain = urlparse(first_url).netloc if first_url != "Unknown" else ""
        doc_title = f"{page_title} | {domain}" if domain else page_title

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
