"""
KnowledgeTree - Web Crawler API Routes
REST API for web crawling functionality
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
from enum import Enum

from core.database import get_db
from models.document import Document
from models.crawl_job import CrawlJob, CrawlStatus
from api.dependencies import get_current_user
from models.user import User
from services.crawler_orchestrator import CrawlerOrchestrator, CrawlEngine, ScrapeResult


router = APIRouter(prefix='/crawl', tags=['Crawling'])


# ============================================================================
# Request/Response Schemas
# ============================================================================


class CrawlEngineRequest(str, Enum):
    """Available scraping engines"""
    HTTP = "http"
    PLAYWRIGHT = "playwright"
    FIRECRAWL = "firecrawl"


class SingleCrawlRequest(BaseModel):
    """Request to crawl a single URL"""
    url: HttpUrl = Field(..., description="URL to crawl")
    engine: Optional[CrawlEngineRequest] = Field(None, description="Force specific engine")
    force_engine: bool = Field(False, description="Force engine selection")
    extract_links: bool = Field(True, description="Extract links from page")
    extract_images: bool = Field(False, description="Extract images from page")
    save_to_db: bool = Field(True, description="Save crawled content as document")
    category_id: Optional[int] = Field(None, description="Category ID for saved document")


class BatchCrawlRequest(BaseModel):
    """Request to crawl multiple URLs"""
    urls: List[HttpUrl] = Field(..., description="URLs to crawl", min_items=1, max_items=50)
    engine: Optional[CrawlEngineRequest] = Field(None, description="Force specific engine")
    force_engine: bool = Field(False, description="Force engine selection")
    extract_links: bool = Field(True, description="Extract links from page")
    extract_images: bool = Field(False, description="Extract images from page")
    category_id: Optional[int] = Field(None, description="Category ID for saved documents")
    concurrency: int = Field(5, description="Maximum concurrent crawls", ge=1, le=10)


class AgenticCrawlRequest(BaseModel):
    """Request for agentic crawl with custom AI extraction prompt"""
    urls: List[HttpUrl] = Field(..., description="URLs to process (web or YouTube)", min_items=1, max_items=20)
    agent_prompt: str = Field(..., description="Custom natural language prompt for extraction", min_length=10, max_length=1000)
    engine: Optional[CrawlEngineRequest] = Field(None, description="Force specific engine")
    category_id: Optional[int] = Field(None, description="Parent category for organization")

    class Config:
        schema_extra = {
            "example": {
                "urls": ["https://example.com/company-list"],
                "agent_prompt": "wyciągnij wszystkie firmy z nazwą, adresem, danymi kontaktowymi i stroną internetową",
                "engine": "http",
                "category_id": None
            }
        }


class TestCrawlRequest(BaseModel):
    """Request for quick test crawl (no DB save)"""
    url: HttpUrl = Field(..., description="URL to test")
    engine: Optional[CrawlEngineRequest] = Field(None, description="Force specific engine")


class CrawlResponse(BaseModel):
    """Response from crawl operation"""
    success: bool
    url: str
    title: str
    engine: str
    text_length: int
    links_count: int
    images_count: int
    status_code: int
    error: Optional[str] = None
    preview: Optional[str] = None  # First 500 chars of text


class JobStatusResponse(BaseModel):
    """Response for job status"""
    job_id: int
    project_id: int
    status: str
    total_urls: int
    completed_urls: int
    failed_urls: int
    created_at: datetime
    updated_at: datetime
    error: Optional[str] = None


# ============================================================================
# Orchestrator Instance
# ============================================================================

from core.config import settings


def get_orchestrator() -> CrawlerOrchestrator:
    """Get crawler orchestrator instance with Firecrawl API key from config"""
    return CrawlerOrchestrator(
        firecrawl_api_key=settings.FIRECRAWL_API_KEY or None
    )


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("/single", response_model=CrawlResponse)
async def crawl_single_url(
    request: SingleCrawlRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    orchestrator: CrawlerOrchestrator = Depends(get_orchestrator)
):
    """
    Crawl a single URL with auto-engine selection
    
    **Engine Selection:**
    - HTTP (default): Fast scraper for static HTML (80% of sites)
    - Playwright: Browser automation for JS-heavy sites (15% of sites)
    - Firecrawl: Managed API for difficult sites with anti-bot (5% of sites)
    
    **Example:**
    ```json
    {
        "url": "https://example.com",
        "engine": "http",
        "save_to_db": true,
        "category_id": 1
    }
    ```
    """
    url = str(request.url)
    engine = CrawlEngine[request.engine.value] if request.engine else None
    
    result: ScrapeResult = await orchestrator.crawl(
        url=url,
        engine=engine,
        force_engine=request.force_engine,
        extract_links=request.extract_links,
        extract_images=request.extract_images
    )
    
    # Save to database if requested
    if request.save_to_db and result.error is None:
        try:
            document = Document(
                project_id=current_user.id,  # Use user's default project
                category_id=request.category_id,
                filename=result.title or url.split('/')[-1] or "crawled_content",
                original_url=url,
                status="completed",
                content_type="text/html",
                file_size=len(result.text),
                page_count=1,
                processed_text=result.text,
                metadata={"engine": result.engine.value, "links": result.links}
            )
            db.add(document)
            await db.commit()
        except Exception as e:
            await db.rollback()
            # Non-fatal error, log but continue
            pass
    
    return CrawlResponse(
        success=result.error is None,
        url=result.url,
        title=result.title,
        engine=result.engine.value,
        text_length=len(result.text),
        links_count=len(result.links),
        images_count=len(result.images),
        status_code=result.status_code,
        error=result.error,
        preview=result.text[:500] if result.text else None
    )


@router.post("/batch")
async def crawl_batch_urls(
    request: BatchCrawlRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crawl multiple URLs in background with Document + Category tree creation
    
    Creates separate crawl job for each URL and processes them in Celery workers.
    Each URL becomes a separate Document with its own Category tree.
    
    **Example:**
    ```json
    {
        "urls": ["https://example.com", "https://example.org"],
        "engine": "http",
        "category_id": 1,
        "concurrency": 5
    }
    ```
    """
    from services.document_tasks import process_web_crawl_task
    from models.crawl_job import ScheduleFrequency
    
    # Parse URLs
    urls = [str(url) for url in request.urls]
    
    if len(urls) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 URLs per batch")
    
    # Create CrawlJob for each URL
    job_ids = []
    created_jobs = []
    
    for url in urls:
        crawl_job = CrawlJob(
            url=url,
            status=CrawlStatus.PENDING,
            schedule_frequency=ScheduleFrequency.ONCE,
            max_depth=1,  # Single page crawl for now
            extraction_method=request.engine.value if request.engine else "auto",
            content_filters={
                "extract_links": request.extract_links,
                "extract_images": request.extract_images
            },
            project_id=current_user.id
        )
        db.add(crawl_job)
        created_jobs.append(crawl_job)
    
    await db.flush()
    
    # Launch Celery tasks for each job
    for crawl_job in created_jobs:
        # Launch async task with priority based on subscription
        task = process_web_crawl_task.apply_async(
            args=[crawl_job.id],
            kwargs={"max_pages": 1},  # Single page for now
            queue="workflows",
            priority=5  # TODO: Map from user subscription tier
        )
        job_ids.append(crawl_job.id)
        
        # Update job with Celery task ID
        crawl_job.status = CrawlStatus.IN_PROGRESS
    
    await db.commit()
    
    return {
        "success": True,
        "message": f"Created {len(job_ids)} crawl jobs",
        "job_ids": job_ids,
        "total_urls": len(urls),
        "note": "Each URL will be processed as a separate Document with Category tree"
    }


@router.post("/agentic")
async def crawl_with_agent_prompt(
    request: AgenticCrawlRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    **Agentic Crawl with Custom AI Extraction Prompt**

    User provides URLs + custom natural language prompt for extraction guidance.
    AI agents extract structured information according to the prompt.
    Results organized into knowledge tree and saved to project.

    **Workflow:**
    1. Content Acquisition: Scrape URLs or transcribe YouTube
    2. Prompt-Guided Extraction: Use AI with custom instructions
    3. Knowledge Organization: Build hierarchical tree
    4. Persistence: Save as Document + Chunks + Categories

    **Example Prompts:**
    - "wyciągnij wszystkie firmy z nazwą, adresem, danymi kontaktowymi"
    - "wyciągnij wszystkie informacje odnośnie metodyki konserwacji drewna"
    - "wejdź na film YouTube, wyciągnij transkrypcję i zbuduj artykuł"

    **Request Body:**
    ```json
    {
        "urls": ["https://example.com", "https://youtube.com/watch?v=xyz"],
        "agent_prompt": "extract all companies with name, address, contact info, and website",
        "engine": "http",
        "category_id": null
    }
    ```

    **Returns:**
    - job_id: CrawlJob ID for tracking
    - workflow_id: AgentWorkflow ID
    - message: Status message
    """
    from services.document_tasks import process_agentic_crawl_task
    from models.crawl_job import ScheduleFrequency

    # Parse URLs
    urls = [str(url) for url in request.urls]

    if len(urls) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 URLs per agentic crawl")

    # Create CrawlJob with agent_prompt
    crawl_job = CrawlJob(
        url=urls[0],  # Primary URL
        status=CrawlStatus.PENDING,
        schedule_frequency=ScheduleFrequency.ONCE,
        max_depth=1,
        extraction_method=request.engine.value if request.engine else "auto",
        content_filters={
            "urls_count": len(urls),
            "additional_urls": urls[1:] if len(urls) > 1 else []
        },
        agent_prompt=request.agent_prompt,  # Custom extraction prompt
        project_id=current_user.id
    )
    db.add(crawl_job)
    await db.flush()

    # Launch Celery task for agentic workflow
    task = process_agentic_crawl_task.apply_async(
        kwargs={
            "crawl_job_id": crawl_job.id,
            "urls": urls,
            "agent_prompt": request.agent_prompt,
            "project_id": current_user.id,
            "engine": request.engine.value if request.engine else None,
            "category_id": request.category_id
        },
        queue="workflows",
        priority=7  # Higher priority for agentic tasks
    )

    # Update job status
    crawl_job.status = CrawlStatus.IN_PROGRESS
    await db.commit()

    return {
        "success": True,
        "job_id": crawl_job.id,
        "message": f"Agentic extraction started for {len(urls)} URLs with custom prompt",
        "agent_prompt": request.agent_prompt,
        "urls_count": len(urls),
        "note": "AI agents will extract structured information according to your prompt"
    }


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_crawl_job_status(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get status of a crawl job

    Returns current status, progress, and any errors.
    """
    result = await db.execute(
        select(CrawlJob).where(
            CrawlJob.id == job_id,
            CrawlJob.project_id == current_user.id
        )
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Crawl job not found")
    
    return JobStatusResponse(
        job_id=job.id,
        project_id=job.project_id,
        status=job.status,
        total_urls=job.total_urls,
        completed_urls=job.completed_urls,
        failed_urls=job.failed_urls,
        created_at=job.created_at,
        updated_at=job.updated_at,
        error=job.error
    )


@router.get("/jobs", response_model=List[JobStatusResponse])
async def list_crawl_jobs(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all crawl jobs for the current user
    
    Returns paginated list of crawl jobs.
    """
    result = await db.execute(
        select(CrawlJob)
        .where(CrawlJob.project_id == current_user.id)
        .order_by(CrawlJob.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    jobs = result.scalars().all()
    
    return [
        JobStatusResponse(
            job_id=job.id,
            project_id=job.project_id,
            status=job.status,
            total_urls=job.total_urls,
            completed_urls=job.completed_urls,
            failed_urls=job.failed_urls,
            created_at=job.created_at,
            updated_at=job.updated_at,
            error=job.error
        )
        for job in jobs
    ]


@router.post("/test", response_model=CrawlResponse)
async def test_crawl(
    request: TestCrawlRequest,
    orchestrator: CrawlerOrchestrator = Depends(get_orchestrator)
):
    """
    Quick test crawl endpoint (no authentication, no DB save)
    
    Useful for testing crawler functionality without creating documents.
    
    **Example:**
    ```json
    {
        "url": "https://example.com",
        "engine": "http"
    }
    ```
    """
    url = str(request.url)
    engine = CrawlEngine[request.engine.value] if request.engine else None
    
    result: ScrapeResult = await orchestrator.crawl(
        url=url,
        engine=engine,
        force_engine=False
    )
    
    return CrawlResponse(
        success=result.error is None,
        url=result.url,
        title=result.title,
        engine=result.engine.value,
        text_length=len(result.text),
        links_count=len(result.links),
        images_count=len(result.images),
        status_code=result.status_code,
        error=result.error,
        preview=result.text[:500] if result.text else None
    )


# ============================================================================
# Reddit-Specific Endpoints
# ============================================================================


class RedditSubredditRequest(BaseModel):
    """Request to scrape a subreddit"""
    subreddit: str = Field(..., description="Subreddit name (without r/)")
    limit: int = Field(50, description="Number of posts to fetch", ge=1, le=100)
    sort: str = Field("hot", description="Sort order: hot, new, top, rising")
    save_to_db: bool = Field(False, description="Save as document")
    category_id: Optional[int] = Field(None, description="Category ID for saved document")


class RedditPostRequest(BaseModel):
    """Request to scrape a Reddit post"""
    post_id: str = Field(..., description="Reddit post ID")
    save_to_db: bool = Field(False, description="Save as document")
    category_id: Optional[int] = Field(None, description="Category ID for saved document")


class RedditSearchRequest(BaseModel):
    """Request to search Reddit"""
    query: str = Field(..., description="Search query")
    subreddit: Optional[str] = Field(None, description="Limit to subreddit")
    limit: int = Field(50, description="Number of results", ge=1, le=100)
    sort: str = Field("relevance", description="Sort: relevance, hot, top, new, comments")
    save_to_db: bool = Field(False, description="Save as document")
    category_id: Optional[int] = Field(None, description="Category ID for saved document")


class RedditResponse(BaseModel):
    """Response from Reddit scraping"""
    success: bool
    source: str
    url: str
    title: str
    posts_count: int
    content: str
    posts: List[Dict[str, Any]] = []
    subreddit_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/reddit/subreddit/{subreddit}", response_model=RedditResponse)
async def scrape_reddit_subreddit(
    subreddit: str,
    request: RedditSubredditRequest = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Scrape a subreddit using Reddit API
    
    Requires Reddit API credentials (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET).
    Get free credentials at: https://www.reddit.com/prefs/apps
    
    **Example:**
    ```json
    {
        "limit": 50,
        "sort": "hot",
        "save_to_db": false
    }
    ```
    
    **Sort options:**
    - `hot` - Hot posts (default)
    - `new` - New posts
    - `top` - Top posts of all time
    - `rising` - Rising posts
    """
    from services.reddit_scraper import reddit_scraper
    
    if request is None:
        request = RedditSubredditRequest(subreddit=subreddit)
    
    result = await reddit_scraper.scrape_subreddit(
        subreddit_name=subreddit,
        limit=request.limit,
        sort=request.sort
    )
    
    # Save to database if requested
    if request.save_to_db and result.error is None:
        try:
            document = Document(
                project_id=current_user.id,
                category_id=request.category_id,
                filename=f"reddit_{subreddit}",
                original_url=result.url,
                status="completed",
                content_type="text/reddit",
                file_size=len(result.content),
                page_count=1,
                processed_text=result.content,
                metadata={
                    "source": "reddit",
                    "subreddit": subreddit,
                    "posts_count": len(result.posts),
                    "sort": request.sort
                }
            )
            db.add(document)
            await db.commit()
        except:
            await db.rollback()
    
    return RedditResponse(
        success=result.error is None,
        source=result.source,
        url=result.url,
        title=result.title,
        posts_count=len(result.posts),
        content=result.content,
        posts=result.posts[:10],  # Return first 10 posts
        subreddit_info=result.subreddit_info,
        error=result.error
    )


@router.post("/reddit/post", response_model=RedditResponse)
async def scrape_reddit_post(
    request: RedditPostRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Scrape a Reddit post with comments
    
    **Example:**
    ```json
    {
        "post_id": "14g5h6k",
        "save_to_db": false
    }
    ```
    """
    from services.reddit_scraper import reddit_scraper
    
    result = await reddit_scraper.scrape_post(post_id=request.post_id)
    
    # Save to database if requested
    if request.save_to_db and result.error is None:
        try:
            document = Document(
                project_id=current_user.id,
                category_id=request.category_id,
                filename=f"reddit_post_{request.post_id}",
                original_url=result.url,
                status="completed",
                content_type="text/reddit",
                file_size=len(result.content),
                page_count=1,
                processed_text=result.content,
                metadata={"source": "reddit", "post_id": request.post_id}
            )
            db.add(document)
            await db.commit()
        except:
            await db.rollback()
    
    return RedditResponse(
        success=result.error is None,
        source=result.source,
        url=result.url,
        title=result.title,
        posts_count=len(result.posts),
        content=result.content,
        posts=result.posts,
        subreddit_info=result.subreddit_info,
        error=result.error
    )


@router.post("/reddit/search", response_model=RedditResponse)
async def search_reddit(
    request: RedditSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search Reddit
    
    **Example:**
    ```json
    {
        "query": "python programming",
        "subreddit": "learnpython",
        "limit": 50,
        "sort": "relevance"
    }
    ```
    
    **Sort options:**
    - `relevance` - Most relevant (default)
    - `hot` - Hot posts
    - `top` - Top posts
    - `new` - New posts
    - `comments` - Most commented
    """
    from services.reddit_scraper import reddit_scraper
    
    result = await reddit_scraper.search(
        query=request.query,
        subreddit=request.subreddit,
        limit=request.limit,
        sort=request.sort
    )
    
    # Save to database if requested
    if request.save_to_db and result.error is None:
        try:
            document = Document(
                project_id=current_user.id,
                category_id=request.category_id,
                filename=f"reddit_search_{request.query[:20]}",
                original_url=result.url,
                status="completed",
                content_type="text/reddit",
                file_size=len(result.content),
                page_count=1,
                processed_text=result.content,
                metadata={
                    "source": "reddit",
                    "search_query": request.query,
                    "subreddit": request.subreddit,
                    "results_count": len(result.posts)
                }
            )
            db.add(document)
            await db.commit()
        except:
            await db.rollback()
    
    return RedditResponse(
        success=result.error is None,
        source=result.source,
        url=result.url,
        title=result.title,
        posts_count=len(result.posts),
        content=result.content,
        posts=result.posts[:10],
        subreddit_info=result.subreddit_info,
        error=result.error
    )


@router.get("/reddit/test")
async def test_reddit_api():
    """
    Test if Reddit API is configured

    Returns status of Reddit API credentials.
    """
    from services.reddit_scraper import reddit_scraper

    return {
        "available": reddit_scraper.available,
        "message": (
            "Reddit API is configured and ready" if reddit_scraper.available
            else "Reddit API credentials not configured. Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables."
        ),
        "setup_instructions": {
            "step1": "Go to https://www.reddit.com/prefs/apps",
            "step2": "Create a new app (script type)",
            "step3": "Copy client_id and client_secret",
            "step4": "Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables"
        }
    }


# ============================================================================
# Google Search via Serper.dev
# ============================================================================

class GoogleSearchRequest(BaseModel):
    """Request for Google search"""
    query: str = Field(..., description="Search query")
    num_results: int = Field(10, description="Number of results", ge=1, le=100)
    country: str = Field("pl", description="Country code (pl, us, uk)")
    language: str = Field("lang_pl", description="Language code")
    type: str = Field("search", description="Search type: search, images, news")


class GoogleSearchResponse(BaseModel):
    """Response from Google search"""
    query: str
    total_results: int
    results: List[Dict[str, Any]]
    related_searches: List[str]
    error: Optional[str] = None


@router.post("/google-search", response_model=GoogleSearchResponse)
async def google_search(
    request: GoogleSearchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Perform Google search via Serper.dev API

    Useful for finding URLs to crawl or researching topics.

    **Example:**
    ```json
    {
        "query": "machine learning tutorials",
        "num_results": 10,
        "country": "pl",
        "language": "lang_pl"
    }
    ```

    **Search types:**
    - `search` - Web search (default)
    - `images` - Image search
    - `news` - News search
    """
    from services.serper_search import serper_search

    try:
        result = await serper_search.search(
            query=request.query,
            num_results=request.num_results,
            country=request.country,
            language=request.language,
            type=request.type
        )

        return GoogleSearchResponse(
            query=result.query,
            total_results=result.total_results,
            results=[
                {
                    "title": r.title,
                    "link": r.link,
                    "snippet": r.snippet,
                    "position": r.position
                }
                for r in result.results
            ],
            related_searches=result.related_searches
        )
    except Exception as e:
        return GoogleSearchResponse(
            query=request.query,
            total_results=0,
            results=[],
            related_searches=[],
            error=str(e)
        )


@router.get("/google-search/test")
async def test_google_search():
    """
    Test if Serper.dev API is configured

    Returns status of Serper.dev credentials.
    """
    from core.config import settings

    return {
        "available": bool(settings.SERPER_API_KEY),
        "message": (
            "Serper.dev API is configured and ready" if settings.SERPER_API_KEY
            else "Serper.dev API key not configured. Set SERPER_API_KEY environment variable."
        ),
        "setup_instructions": {
            "step1": "Go to https://serper.dev",
            "step2": "Sign up and get your API key",
            "step3": "Set SERPER_API_KEY environment variable"
        }
    }


@router.post("/google-search/urls")
async def google_find_urls(
    query: str,
    num_results: int = 10,
    domain_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Quick search to find URLs (simplified interface)

    Returns only URLs, useful for batch crawling setup.

    **Example:**
    ```
    {
        "query": "site:wikipedia.org python programming",
        "num_results": 5
    }
    ```
    """
    from services.serper_search import serper_search

    try:
        urls = await serper_search.find_urls(
            query=query,
            num_results=num_results,
            domain_filter=domain_filter
        )

        return {
            "success": True,
            "query": query,
            "urls": urls,
            "count": len(urls)
        }
    except Exception as e:
        return {
            "success": False,
            "query": query,
            "urls": [],
            "error": str(e)
        }
