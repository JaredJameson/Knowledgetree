"""
KnowledgeTree - Web Content Processor Service
Orchestrates web crawl → Document → Category tree generation
"""

import hashlib
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse, unquote
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.crawl_job import CrawlJob
from models.document import Document, DocumentType, ProcessingStatus
from models.category import Category
from models.chunk import Chunk
from services.text_chunker import TextChunker
from services.embedding_generator import EmbeddingGenerator
from services.crawler_orchestrator import CrawlerOrchestrator, ScrapeResult


class WebContentProcessor:
    """
    Processes web crawl results into Document with hierarchical Category tree

    Workflow:
    1. Accept CrawlJob and list of ScrapeResults
    2. Create Document (source_type=WEB, linked to CrawlJob)
    3. Generate URL-based Category tree hierarchy
    4. Process content: chunk → embed → store
    5. Update CrawlJob with document_id and statistics
    """

    def __init__(self):
        self.crawler = CrawlerOrchestrator()
        self.text_chunker = TextChunker()
        self.embedding_generator = EmbeddingGenerator()

    async def process_crawl_job(
        self,
        crawl_job: CrawlJob,
        db: AsyncSession,
        max_pages: Optional[int] = None
    ) -> Document:
        """
        Process a crawl job: crawl → create document → generate category tree

        Args:
            crawl_job: CrawlJob to process
            db: Database session
            max_pages: Maximum number of pages to crawl (None = unlimited)

        Returns:
            Created Document with Category tree
        """
        # Step 1: Crawl the URL
        crawl_results = await self._crawl_url(
            url=crawl_job.url,
            max_depth=crawl_job.max_depth,
            max_pages=max_pages,
            url_patterns=crawl_job.url_patterns,
            content_filters=crawl_job.content_filters,
            extraction_method=crawl_job.extraction_method
        )

        # Filter results by quality
        filtered_results = self._filter_by_quality(
            results=crawl_results,
            min_quality_score=crawl_job.content_filters.get("min_quality_score", 0.5) if crawl_job.content_filters else 0.5,
            min_text_length=crawl_job.content_filters.get("min_text_length", 200) if crawl_job.content_filters else 200
        )

        # Step 2: Create Document
        document = await self._create_document(
            crawl_job=crawl_job,
            crawl_results=filtered_results,
            db=db
        )

        # Step 3: Generate URL-based Category tree
        root_category = await self._generate_category_tree(
            document=document,
            crawl_results=filtered_results,
            db=db
        )

        # Step 4: Process content (chunk → embed → store)
        await self._process_content(
            document=document,
            crawl_results=filtered_results,
            category_tree=root_category,
            db=db
        )

        # Step 5: Update CrawlJob
        crawl_job.document_id = document.id
        crawl_job.urls_crawled = len(filtered_results)
        crawl_job.urls_failed = len(crawl_results) - len(filtered_results)
        crawl_job.last_crawl_at = datetime.utcnow()

        await db.commit()
        await db.refresh(document)

        return document

    async def _crawl_url(
        self,
        url: str,
        max_depth: int,
        max_pages: Optional[int],
        url_patterns: Optional[Dict],
        content_filters: Optional[Dict],
        extraction_method: str
    ) -> List[ScrapeResult]:
        """
        Crawl URL and return list of ScrapeResults

        Args:
            url: Starting URL
            max_depth: Maximum crawl depth
            max_pages: Maximum pages to crawl
            url_patterns: URL filtering patterns
            content_filters: Content quality filters
            extraction_method: Content extraction method

        Returns:
            List of ScrapeResult from crawled pages
        """
        # For now, just crawl the single URL
        # TODO: Implement recursive crawling with depth tracking
        result = await self.crawler.crawl(url, extract_links=False)

        if result.error:
            return []

        return [result]

    def _filter_by_quality(
        self,
        results: List[ScrapeResult],
        min_quality_score: float,
        min_text_length: int
    ) -> List[ScrapeResult]:
        """
        Filter crawl results by quality metrics

        Args:
            results: List of ScrapeResults
            min_quality_score: Minimum quality score (0.0-1.0)
            min_text_length: Minimum text length in characters

        Returns:
            Filtered list of ScrapeResults
        """
        filtered = []

        for result in results:
            # Filter by quality score
            if result.quality_score < min_quality_score:
                continue

            # Filter by text length
            if len(result.text) < min_text_length:
                continue

            filtered.append(result)

        return filtered

    async def _create_document(
        self,
        crawl_job: CrawlJob,
        crawl_results: List[ScrapeResult],
        db: AsyncSession
    ) -> Document:
        """
        Create Document from crawl results

        Args:
            crawl_job: CrawlJob that initiated the crawl
            crawl_results: List of ScrapeResults
            db: Database session

        Returns:
            Created Document
        """
        # Use first result for document metadata
        first_result = crawl_results[0] if crawl_results else None

        if not first_result:
            raise ValueError("No valid crawl results to create document")

        # Create document
        document = Document(
            filename=crawl_job.url,
            title=first_result.title or crawl_job.url,
            source_type=DocumentType.WEB,
            source_url=crawl_job.url,
            crawl_job_id=crawl_job.id,
            project_id=crawl_job.project_id,
            processing_status=ProcessingStatus.PROCESSING,
            extraction_metadata={
                "extraction_method": first_result.extraction_method,
                "quality_score": first_result.quality_score,
                "engine": first_result.engine.value,
                "pages_crawled": len(crawl_results)
            }
        )

        db.add(document)
        await db.flush()  # Get document.id

        return document

    async def _generate_category_tree(
        self,
        document: Document,
        crawl_results: List[ScrapeResult],
        db: AsyncSession
    ) -> Category:
        """
        Generate URL-based Category tree from crawl results

        Args:
            document: Document to associate categories with
            crawl_results: List of ScrapeResults
            db: Database session

        Returns:
            Root Category of the tree
        """
        # Create root category from base URL
        first_result = crawl_results[0]
        parsed_url = urlparse(first_result.url)

        # Root category: domain name
        root_category = Category(
            name=parsed_url.netloc,
            description=f"Content from {parsed_url.netloc}",
            color="#E6E6FA",
            icon="Globe",
            depth=0,
            order=0,
            source_url=f"{parsed_url.scheme}://{parsed_url.netloc}",
            url_path=parsed_url.path or "/",
            content_hash=self._calculate_content_hash(first_result.text),
            last_crawled_at=datetime.utcnow(),
            project_id=document.project_id
        )

        db.add(root_category)
        await db.flush()

        # Update document with root category
        document.category_id = root_category.id

        # Generate child categories from URL paths
        for i, result in enumerate(crawl_results):
            parsed = urlparse(result.url)
            path_segments = [s for s in parsed.path.split('/') if s]

            if not path_segments:
                continue

            # Create category for this URL
            category_name = unquote(path_segments[-1]) if path_segments else parsed.netloc

            category = Category(
                name=category_name,
                description=result.title or category_name,
                color="#E6E6FA",
                icon="FileText",
                depth=1,
                order=i,
                source_url=result.url,
                url_path=parsed.path,
                content_hash=self._calculate_content_hash(result.text),
                last_crawled_at=datetime.utcnow(),
                parent_id=root_category.id,
                project_id=document.project_id
            )

            db.add(category)

        await db.flush()

        return root_category

    async def _process_content(
        self,
        document: Document,
        crawl_results: List[ScrapeResult],
        category_tree: Category,
        db: AsyncSession
    ) -> None:
        """
        Process content through RAG pipeline: chunk → embed → store

        Args:
            document: Document to associate chunks with
            crawl_results: List of ScrapeResults
            category_tree: Root category of the tree
            db: Database session
        """
        # Get all categories for this document
        result = await db.execute(
            select(Category)
            .where(Category.project_id == document.project_id)
            .where(
                (Category.id == category_tree.id) |
                (Category.parent_id == category_tree.id)
            )
            .order_by(Category.depth, Category.order)
        )
        categories = result.scalars().all()

        # Create category URL mapping
        category_by_url = {cat.source_url: cat for cat in categories if cat.source_url}

        # Process each crawl result
        for result in crawl_results:
            # Find matching category
            category = category_by_url.get(result.url)

            if not category:
                category = category_tree  # Use root as fallback

            # Chunk the text
            chunks_data = self.text_chunker.chunk_text(result.text, document.id)

            # Generate embeddings
            texts = [chunk["text"] for chunk in chunks_data]
            embeddings = self.embedding_generator.generate_embeddings_batch(texts)

            # Store chunks
            for i, (chunk_data, embedding) in enumerate(zip(chunks_data, embeddings)):
                chunk = Chunk(
                    text=chunk_data["text"],
                    embedding=embedding,
                    chunk_index=i,
                    chunk_metadata=str({"source_url": result.url}),  # Store URL in metadata as string
                    document_id=document.id,
                    category_id=category.id,
                    has_embedding=1
                )

                db.add(chunk)

        # Update document status
        document.processing_status = ProcessingStatus.COMPLETED
        document.processed_at = datetime.utcnow()

        await db.flush()

    def _calculate_content_hash(self, text: str) -> str:
        """
        Calculate MD5 hash of content for change detection

        Args:
            text: Text content

        Returns:
            MD5 hash as hex string
        """
        return hashlib.md5(text.encode('utf-8')).hexdigest()


# Singleton instance
web_content_processor = WebContentProcessor()
