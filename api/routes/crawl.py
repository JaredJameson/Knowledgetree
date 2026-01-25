"""
KnowledgeTree Backend - Crawl Routes
Web crawling endpoints with multi-engine support
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, HttpUrl, Field

from core.database import get_db
from models.user import User
from models.project import Project
from models.document import Document, DocumentType, ProcessingStatus
from models.crawl_job import CrawlJob, CrawlStatus
from api.dependencies import get_current_active_user
from services.crawler_orchestrator import CrawlerOrchestrator, CrawlEngine

router = APIRouter(prefix="/crawl", tags=["Crawling"])
logger = logging.getLogger(__name__)

# Initialize orchestrator (will be configured from env vars)
orchestrator = CrawlerOrchestrator(
    firecrawl_api_key=None  # Set from settings.FIRECRAWL_API_KEY
)


# ============================================================================
# Request/Response Schemas
# ============================================================================

class CrawlURLRequest(BaseModel):
    """Request to crawl a single URL"""
    url: HttpUrl
    project_id: int
    category_id: Optional[int] = None
    engine: Optional[CrawlEngine] = None
    force_engine: bool = False
    save_to_db: bool = True
    extract_links: bool = False
    wait_for_selector: Optional[str] = None  # Playwright only


class BatchCrawlRequest(BaseModel):
    """Request to crawl multiple URLs"""
    urls: List[HttpUrl] = Field(min_items=1, max_items=50)
    project_id: int
    category_id: Optional[int] = None
    engine: Optional[CrawlEngine] = None
    force_engine: bool = False
    save_to_db: bool = True


class CrawlResponse(BaseModel):
    """Response from URL crawling"""
    url: str
    title: str
    content: str
    text: str
    engine_used: str
    word_count: int
    links: Optional[List[str]] = None
    document_id: Optional[int] = None


class CrawlJobResponse(BaseModel):
    """Crawl job status response"""
    job_id: int
    url: str
    status: str
    urls_crawled: int
    urls_failed: int
    error_message: Optional[str] = None


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/single", response_model=CrawlResponse, status_code=status.HTTP_200_OK)
async def crawl_single_url(
    request: CrawlURLRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Crawl a single URL with auto-selected engine.
    
    Auto-selection logic:
    - Static HTML → HTTP scraper (fast, free)
    - JavaScript/SPA → Playwright (free, slower)
    - Anti-bot/captcha → Firecrawl (paid API)
    
    You can force a specific engine with engine + force_engine=True.
    """
    try:
        # Verify project ownership
        from sqlalchemy import select
        project_result = await db.execute(
            select(Project).where(
                Project.id == request.project_id,
                Project.owner_id == current_user.id
            )
        )
        project = project_result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Crawl URL
        result = await orchestrator.crawl(
            str(request.url),
            engine=request.engine,
            force_engine=request.force_engine,
            extract_links=request.extract_links,
            wait_for_selector=request.wait_for_selector
        )
        
        # Extract engine used
        engine_used = result.get("metadata", {}).get("engine", "unknown")
        
        # Save to database if requested
        document_id = None
        if request.save_to_db:
            document = Document(
                project_id=request.project_id,
                category_id=request.category_id,
                filename=f"{result['title'][:50]}.html",
                original_url=str(request.url),
                document_type=DocumentType.WEB,
                processing_status=ProcessingStatus.COMPLETED,
                title=result['title'],
                content_summary=result['text'][:500],
                page_count=1,
                word_count=len(result['text'].split())
            )
            
            db.add(document)
            await db.commit()
            await db.refresh(document)
            document_id = document.id
            
            logger.info(f"Saved crawled content to document {document.id}")
        
        return CrawlResponse(
            url=result['url'],
            title=result['title'],
            content=result['content'],
            text=result['text'],
            engine_used=engine_used,
            word_count=len(result['text'].split()),
            links=result.get('links'),
            document_id=document_id
        )
        
    except Exception as e:
        logger.error(f"Error crawling URL {request.url}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Crawling failed: {str(e)}"
        )


@router.post("/batch", status_code=status.HTTP_202_ACCEPTED)
async def batch_crawl_urls(
    request: BatchCrawlRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Crawl multiple URLs asynchronously.
    
    Returns immediately with job ID, processes in background.
    """
    # Verify project ownership
    from sqlalchemy import select
    project_result = await db.execute(
        select(Project).where(
            Project.id == request.project_id,
            Project.owner_id == current_user.id
        )
    )
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Create crawl job
    job = CrawlJob(
        url=f"{len(request.urls)} URLs",
        project_id=request.project_id,
        status=CrawlStatus.PENDING
    )
    
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    # Add background task
    background_tasks.add_task(
        _process_batch_crawl,
        job.id,
        [str(url) for url in request.urls],
        request.project_id,
        request.category_id,
        request.engine,
        request.force_engine,
        request.save_to_db,
        db
    )
    
    return {
        "job_id": job.id,
        "status": "pending",
        "urls_count": len(request.urls),
        "message": "Batch crawl job started"
    }


async def _process_batch_crawl(
    job_id: int,
    urls: List[str],
    project_id: int,
    category_id: Optional[int],
    engine: Optional[CrawlEngine],
    force_engine: bool,
    save_to_db: bool,
    db: AsyncSession
):
    """Background task to process batch crawl."""
    from sqlalchemy import update
    
    try:
        # Update job status to in_progress
        await db.execute(
            update(CrawlJob)
            .where(CrawlJob.id == job_id)
            .values(status=CrawlStatus.IN_PROGRESS)
        )
        await db.commit()
        
        # Process URLs
        results = await orchestrator.batch_crawl(
            urls,
            engine=engine,
            force_engine=force_engine
        )
        
        urls_crawled = 0
        urls_failed = 0
        
        for result in results:
            if result.get("failed"):
                urls_failed += 1
                continue
            
            urls_crawled += 1
            
            # Save to database if requested
            if save_to_db:
                document = Document(
                    project_id=project_id,
                    category_id=category_id,
                    filename=f"{result['title'][:50]}.html",
                    original_url=result['url'],
                    document_type=DocumentType.WEB,
                    processing_status=ProcessingStatus.COMPLETED,
                    title=result['title'],
                    content_summary=result['text'][:500],
                    page_count=1,
                    word_count=len(result['text'].split())
                )
                
                db.add(document)
        
        await db.commit()
        
        # Update job as completed
        await db.execute(
            update(CrawlJob)
            .where(CrawlJob.id == job_id)
            .values(
                status=CrawlStatus.COMPLETED,
                urls_crawled=urls_crawled,
                urls_failed=urls_failed
            )
        )
        await db.commit()
        
        logger.info(f"Batch crawl job {job_id} completed: {urls_crawled} crawled, {urls_failed} failed")
        
    except Exception as e:
        logger.error(f"Batch crawl job {job_id} failed: {e}")
        
        # Update job as failed
        await db.execute(
            update(CrawlJob)
            .where(CrawlJob.id == job_id)
            .values(
                status=CrawlStatus.FAILED,
                error_message=str(e)
            )
        )
        await db.commit()


@router.get("/jobs/{job_id}", response_model=CrawlJobResponse)
async def get_crawl_job_status(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get status of a crawl job."""
    from sqlalchemy import select
    
    result = await db.execute(
        select(CrawlJob)
        .join(Project)
        .where(
            CrawlJob.id == job_id,
            Project.owner_id == current_user.id
        )
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crawl job not found"
        )
    
    return CrawlJobResponse(
        job_id=job.id,
        url=job.url,
        status=job.status.value,
        urls_crawled=job.urls_crawled,
        urls_failed=job.urls_failed,
        error_message=job.error_message
    )


@router.get("/jobs")
async def list_crawl_jobs(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List all crawl jobs for a project."""
    from sqlalchemy import select
    
    # Verify project ownership
    project_result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id
        )
    )
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get jobs
    result = await db.execute(
        select(CrawlJob)
        .where(CrawlJob.project_id == project_id)
        .order_by(CrawlJob.created_at.desc())
    )
    jobs = result.scalars().all()
    
    return {
        "project_id": project_id,
        "jobs": [
            {
                "job_id": job.id,
                "url": job.url,
                "status": job.status.value,
                "urls_crawled": job.urls_crawled,
                "urls_failed": job.urls_failed,
                "created_at": job.created_at.isoformat()
            }
            for job in jobs
        ]
    }


@router.post("/test")
async def test_crawler(url: HttpUrl):
    """
    Test endpoint to quickly crawl a URL without saving to database.
    Useful for testing and debugging.
    """
    try:
        result = await orchestrator.crawl(str(url))
        
        return {
            "url": result['url'],
            "title": result['title'],
            "text_length": len(result['text']),
            "engine_used": result.get('metadata', {}).get('engine', 'unknown'),
            "preview": result['text'][:500] + "..." if len(result['text']) > 500 else result['text']
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Crawling failed: {str(e)}"
        )
