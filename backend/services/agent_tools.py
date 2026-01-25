"""
KnowledgeTree - Agent Tools
Base tools that Claude can call during workflow execution
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
import ipaddress

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import AsyncSessionLocal
from core.config import settings
from models.document import Document
from models.category import Category
from services.search_service import SearchService
from services.crawler_orchestrator import CrawlerOrchestrator, CrawlEngine
from services.category_tree_generator import CategoryTreeGenerator
from services.youtube_transcriber import YouTubeTranscriber


# ============================================================================
# Tool 1: search_web - URL Discovery
# ============================================================================

async def search_web(
    query: str,
    num_results: int = 20,
    date_range: str = "any",
    language: str = "en",
    _context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Search the web for URLs related to a query
    
    Args:
        query: Search query
        num_results: Number of results (1-50)
        date_range: Date range filter (day, week, month, year, any)
        language: Search language code
        _context: Workflow context (auto-injected)
    
    Returns:
        Dict with discovered URLs
    """
    # TODO: Implement Google Custom Search API integration
    # For now, return mock results
    
    mock_urls = [
        {
            "url": f"https://example.com/page{i}",
            "title": f"Example Page {i} - {query}",
            "snippet": f"This page contains information about {query}",
            "relevance_score": 0.8 - (i * 0.02),
            "date": "2024-01-01"
        }
        for i in range(min(num_results, 10))
    ]
    
    return {
        "urls": mock_urls,
        "total": len(mock_urls),
        "query": query,
        "source": "google_search_api",
        "date_range": date_range
    }


# ============================================================================
# Tool 2: scrape_urls - Web Scraping
# ============================================================================

async def scrape_urls(
    urls: List[str],
    engine: str = "auto",
    concurrency: int = 5,
    extract_links: bool = True,
    _context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Scrape content from multiple URLs
    
    Args:
        urls: List of URLs to scrape
        engine: Scraping engine (auto, http, playwright, firecrawl)
        concurrency: Concurrent scraping operations
        extract_links: Extract links from pages
        _context: Workflow context (auto-injected)
    
    Returns:
        Dict with scraped content
    """
    # Validate URLs
    validated_urls = []
    for url in urls:
        if await _validate_url(url):
            validated_urls.append(url)
    
    if not validated_urls:
        return {
            "scraped": [],
            "failed": urls,
            "total": len(urls),
            "error": "No valid URLs after validation"
        }
    
    # Get workflow context
    workflow_id = _context.get("workflow_id") if _context else None
    
    # Execute scraping
    orchestrator = CrawlerOrchestrator()
    
    # Determine engine
    crawl_engine = None
    if engine != "auto":
        try:
            crawl_engine = CrawlEngine[engine.upper()]
        except KeyError:
            pass
    
    try:
        results = await orchestrator.batch_crawl(
            urls=validated_urls,
            engine=crawl_engine,
            concurrency=min(concurrency, len(validated_urls)),
            extract_links=extract_links
        )
        
        # Process results
        scraped = []
        failed = []
        
        for result in results:
            if result.error:
                failed.append({
                    "url": result.url,
                    "error": result.error,
                    "engine": result.engine.value if result.engine else "unknown"
                })
            else:
                scraped.append({
                    "url": result.url,
                    "title": result.title or "",
                    "text": result.text,
                    "text_length": len(result.text),
                    "links": result.links,
                    "images": result.images,
                    "engine": result.engine.value,
                    "status_code": result.status_code
                })
        
        # Save to database if workflow context available
        if workflow_id and _context:
            await _save_scraped_content(
                workflow_id=workflow_id,
                scraped=scraped,
                context=_context
            )
        
        return {
            "scraped": scraped,
            "failed": failed,
            "total": len(validated_urls),
            "successful": len(scraped)
        }
        
    except Exception as e:
        return {
            "scraped": [],
            "failed": [{"url": url, "error": str(e)} for url in validated_urls],
            "total": len(validated_urls),
            "error": str(e)
        }


async def _validate_url(url: str) -> bool:
    """Validate URL is safe to scrape"""
    try:
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
        
        # Block non-http/https schemes
        if parsed.scheme not in ['http', 'https']:
            return False
        
        return True
    except Exception:
        return False


async def _save_scraped_content(
    workflow_id: int,
    scraped: List[Dict[str, Any]],
    context: Dict[str, Any]
):
    """Save scraped content to database"""
    async with AsyncSessionLocal() as db:
        project_id = context.get("project_id")
        category_id = context.get("category_id")
        
        for item in scraped:
            document = Document(
                project_id=project_id,
                category_id=category_id,
                filename=item["title"][:200] or "scraped_content",
                original_url=item["url"],
                status="completed",
                content_type="text/html",
                file_size=item["text_length"],
                page_count=1,
                processed_text=item["text"],
                metadata={
                    "engine": item["engine"],
                    "workflow_id": workflow_id,
                    "links_count": len(item.get("links", [])),
                    "images_count": len(item.get("images", []))
                }
            )
            db.add(document)
        
        await db.commit()


# ============================================================================
# Tool 3: create_knowledge_tree - Category Tree Generation
# ============================================================================

async def create_knowledge_tree(
    knowledge_points: List[Dict[str, Any]],
    project_id: int,
    category_id: Optional[int] = None,
    tree_name: Optional[str] = None,
    _context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate a hierarchical knowledge tree from content
    
    Args:
        knowledge_points: List of knowledge points with text/metadata
        project_id: Project ID for the tree
        category_id: Parent category ID (optional)
        tree_name: Name for the tree (optional)
        _context: Workflow context (auto-injected)
    
    Returns:
        Dict with tree information
    """
    try:
        generator = CategoryTreeGenerator()
        
        # Build tree from knowledge points
        tree = await generator.generate_tree(
            knowledge_points=knowledge_points,
            project_id=project_id,
            parent_category_id=category_id,
            tree_name=tree_name or "Generated Knowledge Tree"
        )
        
        return {
            "tree_id": tree.id,
            "name": tree.name,
            "node_count": getattr(tree, "node_count", len(knowledge_points)),
            "depth": getattr(tree, "depth", 3),
            "status": "success"
        }
        
    except Exception as e:
        return {
            "tree_id": None,
            "error": str(e),
            "status": "failed"
        }


# ============================================================================
# Tool 4: query_knowledge_base - Database Search
# ============================================================================

async def query_knowledge_base(
    query: str,
    project_id: int,
    limit: int = 10,
    search_type: str = "hybrid",
    _context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Search the knowledge base using vector search
    
    Args:
        query: Search query
        project_id: Project ID to search
        limit: Number of results
        search_type: Type of search (hybrid, semantic, keyword)
        _context: Workflow context (auto-injected)
    
    Returns:
        Dict with search results
    """
    async with AsyncSessionLocal() as db:
        try:
            service = SearchService()
            
            # Execute search based on type
            if search_type == "hybrid":
                results = await service.hybrid_search(
                    query=query,
                    project_id=project_id,
                    limit=limit
                )
            elif search_type == "semantic":
                results = await service.semantic_search(
                    query=query,
                    project_id=project_id,
                    limit=limit
                )
            else:  # keyword
                results = await service.keyword_search(
                    query=query,
                    project_id=project_id,
                    limit=limit
                )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "id": result.id,
                    "content": result.content[:500] if hasattr(result, "content") else "",
                    "score": getattr(result, "score", 0),
                    "metadata": getattr(result, "metadata", {})
                })
            
            return {
                "results": formatted_results,
                "total": len(formatted_results),
                "query": query,
                "search_type": search_type
            }
            
        except Exception as e:
            return {
                "results": [],
                "total": 0,
                "query": query,
                "error": str(e)
            }


# ============================================================================
# Tool 5: save_to_database - Persistence
# ============================================================================

async def save_to_database(
    entity_type: str,
    data: Dict[str, Any],
    project_id: int,
    workflow_id: Optional[int] = None,
    _context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Save data to the database
    
    Args:
        entity_type: Type of entity (document, category, knowledge_point)
        data: Data to save
        project_id: Project ID
        workflow_id: Workflow ID (for tracking)
        _context: Workflow context (auto-injected)
    
    Returns:
        Dict with save result
    """
    async with AsyncSessionLocal() as db:
        try:
            if entity_type == "document":
                entity = Document(
                    project_id=project_id,
                    **data
                )
            elif entity_type == "category":
                entity = Category(
                    project_id=project_id,
                    **data
                )
            elif entity_type == "knowledge_point":
                # Save as a document with special metadata
                entity = Document(
                    project_id=project_id,
                    filename=data.get("title", "Knowledge Point")[:200],
                    original_url=data.get("source_url"),
                    status="completed",
                    content_type="text/knowledge_point",
                    file_size=len(data.get("text", "")),
                    page_count=1,
                    processed_text=data.get("text", ""),
                    metadata={
                        "type": "knowledge_point",
                        "workflow_id": workflow_id,
                        **data.get("metadata", {})
                    }
                )
            else:
                return {
                    "id": None,
                    "type": entity_type,
                    "status": "error",
                    "error": f"Unknown entity type: {entity_type}"
                }
            
            db.add(entity)
            await db.commit()
            await db.refresh(entity)
            
            return {
                "id": entity.id,
                "type": entity_type,
                "status": "saved",
                "created_at": entity.created_at.isoformat()
            }
            
        except Exception as e:
            await db.rollback()
            return {
                "id": None,
                "type": entity_type,
                "status": "error",
                "error": str(e)
            }


# ============================================================================
# Tool 6: process_youtube_video - YouTube Transcription & Analysis
# ============================================================================

async def process_youtube_video(
    url: str,
    project_id: int,
    language: str = "pl",
    _context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Extract transcript from YouTube video and generate knowledge tree

    Args:
        url: YouTube video URL
        project_id: Project ID for the document
        language: Transcript language preference (pl, en)
        _context: Workflow context (auto-injected)

    Returns:
        Dict with video metadata, categories, and analysis
    """
    async with AsyncSessionLocal() as db:
        try:
            # Initialize transcriber
            transcriber = YouTubeTranscriber(settings.anthropic_api_key)

            # Process video
            document, categories, metadata = await transcriber.process_video(
                url=url,
                project_id=project_id,
                db=db,
                language=language,
                project_context=_context.get("project_context") if _context else None
            )

            await transcriber.close()

            # Format response
            return {
                "status": "success",
                "document": {
                    "id": document.id,
                    "title": document.title,
                    "filename": document.filename,
                    "source_type": document.source_type.value,
                    "source_url": document.source_url
                },
                "categories": [
                    {
                        "id": cat.id,
                        "name": cat.name,
                        "description": cat.description,
                        "depth": cat.depth,
                        "color": cat.color,
                        "icon": cat.icon
                    }
                    for cat in categories
                ],
                "metadata": metadata,
                "total_categories": len(categories)
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "url": url
            }


# ============================================================================
# Tool Schemas for Claude API
# ============================================================================

TOOL_SCHEMAS = {
    "search_web": {
        "name": "search_web",
        "description": "Search the web for URLs related to a query. Returns relevant URLs with metadata.",
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
                    "default": 20,
                    "minimum": 1,
                    "maximum": 50
                },
                "date_range": {
                    "type": "string",
                    "description": "Date range filter",
                    "enum": ["day", "week", "month", "year", "any"],
                    "default": "any"
                },
                "language": {
                    "type": "string",
                    "description": "Language code",
                    "default": "en"
                }
            },
            "required": ["query"]
        }
    },
    
    "scrape_urls": {
        "name": "scrape_urls",
        "description": "Scrape content from multiple URLs using multi-engine scraper with auto-detection.",
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
                    "default": 5,
                    "minimum": 1,
                    "maximum": 20
                },
                "extract_links": {
                    "type": "boolean",
                    "description": "Extract links from pages",
                    "default": True
                }
            },
            "required": ["urls"]
        }
    },
    
    "create_knowledge_tree": {
        "name": "create_knowledge_tree",
        "description": "Generate a hierarchical knowledge tree from knowledge points using AI categorization.",
        "input_schema": {
            "type": "object",
            "properties": {
                "knowledge_points": {
                    "type": "array",
                    "description": "List of knowledge points with text and metadata",
                    "items": {"type": "object"}
                },
                "project_id": {
                    "type": "integer",
                    "description": "Project ID for the tree"
                },
                "category_id": {
                    "type": "integer",
                    "description": "Parent category ID (optional)"
                },
                "tree_name": {
                    "type": "string",
                    "description": "Name for the tree"
                }
            },
            "required": ["knowledge_points", "project_id"]
        }
    },
    
    "query_knowledge_base": {
        "name": "query_knowledge_base",
        "description": "Search the knowledge base using vector search and keyword matching.",
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
                    "default": 10,
                    "minimum": 1,
                    "maximum": 100
                },
                "search_type": {
                    "type": "string",
                    "description": "Type of search",
                    "enum": ["hybrid", "semantic", "keyword"],
                    "default": "hybrid"
                }
            },
            "required": ["query", "project_id"]
        }
    },
    
    "save_to_database": {
        "name": "save_to_database",
        "description": "Save data to the database as documents, categories, or knowledge points.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_type": {
                    "type": "string",
                    "description": "Type of entity",
                    "enum": ["document", "category", "knowledge_point"]
                },
                "data": {
                    "type": "object",
                    "description": "Data to save"
                },
                "project_id": {
                    "type": "integer",
                    "description": "Project ID"
                },
                "workflow_id": {
                    "type": "integer",
                    "description": "Workflow ID for tracking"
                }
            },
            "required": ["entity_type", "data", "project_id"]
        }
    },

    "process_youtube_video": {
        "name": "process_youtube_video",
        "description": "Extract transcript from YouTube video and generate knowledge tree with categories and insights. Use this when user provides a YouTube URL or asks to process a video.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "YouTube video URL (e.g., https://youtube.com/watch?v=xxx or https://youtu.be/xxx)"
                },
                "project_id": {
                    "type": "integer",
                    "description": "Project ID for the document"
                },
                "language": {
                    "type": "string",
                    "description": "Transcript language preference",
                    "enum": ["pl", "en"],
                    "default": "pl"
                }
            },
            "required": ["url", "project_id"]
        }
    }
}


# ============================================================================
# Tool Registration Helper
# ============================================================================

def register_all_tools(client) -> None:
    """
    Register all tools with AnthropicToolClient
    
    Args:
        client: AnthropicToolClient instance
    """
    client.register_tool(
        name="search_web",
        description=TOOL_SCHEMAS["search_web"]["description"],
        input_schema=TOOL_SCHEMAS["search_web"]["input_schema"],
        function=search_web
    )
    
    client.register_tool(
        name="scrape_urls",
        description=TOOL_SCHEMAS["scrape_urls"]["description"],
        input_schema=TOOL_SCHEMAS["scrape_urls"]["input_schema"],
        function=scrape_urls
    )
    
    client.register_tool(
        name="create_knowledge_tree",
        description=TOOL_SCHEMAS["create_knowledge_tree"]["description"],
        input_schema=TOOL_SCHEMAS["create_knowledge_tree"]["input_schema"],
        function=create_knowledge_tree
    )
    
    client.register_tool(
        name="query_knowledge_base",
        description=TOOL_SCHEMAS["query_knowledge_base"]["description"],
        input_schema=TOOL_SCHEMAS["query_knowledge_base"]["input_schema"],
        function=query_knowledge_base
    )
    
    client.register_tool(
        name="save_to_database",
        description=TOOL_SCHEMAS["save_to_database"]["description"],
        input_schema=TOOL_SCHEMAS["save_to_database"]["input_schema"],
        function=save_to_database
    )

    client.register_tool(
        name="process_youtube_video",
        description=TOOL_SCHEMAS["process_youtube_video"]["description"],
        input_schema=TOOL_SCHEMAS["process_youtube_video"]["input_schema"],
        function=process_youtube_video
    )

