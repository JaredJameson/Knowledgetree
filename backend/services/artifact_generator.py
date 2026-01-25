"""
KnowledgeTree Backend - Artifact Generator Service
Generate AI artifacts (summaries, articles, notes, etc.) using Claude API with RAG
"""

import logging
import time
import json
from typing import List, Dict, Optional
from anthropic import Anthropic
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.artifact import ArtifactType
from services.search_service import SearchService

logger = logging.getLogger(__name__)


class ArtifactGenerator:
    """
    Service for generating AI artifacts using Claude API with RAG

    Features:
    - Retrieves relevant context from documents
    - Generates specialized content based on artifact type
    - Supports chapter-level and category-filtered generation
    - Provides metadata about generation process

    Use Cases:
    - "Summarize chapter 3" → Generate summary artifact
    - "Create study notes for section 2.1" → Generate notes artifact
    - "Write an article about X" → Generate article artifact
    """

    # Artifact type-specific system prompts
    SYSTEM_PROMPTS = {
        ArtifactType.SUMMARY: """You are an expert at creating concise, informative summaries.

Your summaries should:
- Capture the main ideas and key points
- Be clear and well-structured
- Include important details and examples
- Use markdown formatting (headings, lists, bold)
- Be appropriate for study and review""",

        ArtifactType.ARTICLE: """You are a skilled technical writer who creates comprehensive articles.

Your articles should:
- Have a clear introduction, body, and conclusion
- Explain concepts thoroughly with examples
- Use proper markdown formatting
- Include relevant context and background
- Be engaging and informative""",

        ArtifactType.EXTRACT: """You are an expert at extracting key information from documents.

Your extracts should:
- Pull out the most important facts and data
- Organize information logically
- Preserve accuracy and precision
- Use bullet points and tables where appropriate
- Highlight critical takeaways""",

        ArtifactType.NOTES: """You are a student creating study notes from source material.

Your notes should:
- Be well-organized and easy to review
- Use headings, subheadings, and bullet points
- Include key definitions and concepts
- Highlight important formulas or procedures
- Be concise but comprehensive""",

        ArtifactType.OUTLINE: """You are creating a structured outline from content.

Your outlines should:
- Use hierarchical structure (I, A, 1, a, etc.)
- Capture logical flow and relationships
- Be clear and scannable
- Include all major topics and subtopics
- Use markdown list formatting""",

        ArtifactType.COMPARISON: """You are comparing and contrasting different concepts or topics.

Your comparisons should:
- Clearly identify similarities and differences
- Use tables or side-by-side formatting
- Be balanced and objective
- Highlight key distinctions
- Provide clear conclusions""",

        ArtifactType.EXPLANATION: """You are explaining complex concepts in an accessible way.

Your explanations should:
- Break down complex ideas into simple parts
- Use analogies and examples
- Build understanding progressively
- Clarify common misconceptions
- Be clear and pedagogical""",

        ArtifactType.CUSTOM: """You are a versatile AI assistant creating custom content.

Your content should:
- Follow the specific instructions provided
- Be well-formatted and organized
- Be accurate and informative
- Use appropriate markdown formatting
- Meet the user's stated goals""",
    }

    def __init__(self):
        """Initialize the artifact generator"""
        self.anthropic = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.search_service = SearchService()
        self.model = settings.ANTHROPIC_MODEL

    async def retrieve_context(
        self,
        db: AsyncSession,
        query: str,
        project_id: int,
        category_id: Optional[int] = None,
        max_chunks: int = 10,
        min_similarity: float = 0.5
    ) -> tuple[List[Dict], str]:
        """
        Retrieve relevant chunks for artifact generation

        Args:
            db: Database session
            query: Search query (e.g., "chapter 3 content")
            project_id: Project to search in
            category_id: Optional category filter (e.g., specific chapter)
            max_chunks: Maximum chunks to retrieve
            min_similarity: Minimum similarity threshold

        Returns:
            Tuple of (retrieved chunks list, formatted context string)
        """
        # Perform search with optional category filter
        chunks, _ = await self.search_service.search(
            db=db,
            query=query,
            project_id=project_id,
            limit=max_chunks,
            min_similarity=min_similarity,
            category_id=category_id
        )

        if not chunks:
            logger.warning(f"No context found for query: {query[:50]}")
            return [], ""

        # Format context for Claude
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            doc_title = chunk.get("document_title") or chunk.get("document_filename")
            page_number = None

            # Extract page number from metadata
            if chunk.get("chunk_metadata"):
                page_number = chunk["chunk_metadata"].get("page_number")

            # Build source header
            source_header = f"[Source {i}: {doc_title}"
            if page_number:
                source_header += f", Page {page_number}"
            source_header += "]"

            context_parts.append(
                f"{source_header}\n{chunk['chunk_text']}\n"
            )

        formatted_context = "\n---\n\n".join(context_parts)

        logger.info(f"Retrieved {len(chunks)} chunks for artifact generation")
        return chunks, formatted_context

    def build_generation_prompt(
        self,
        artifact_type: ArtifactType,
        title: str,
        context: str,
        instructions: Optional[str] = None
    ) -> str:
        """
        Build generation prompt for Claude

        Args:
            artifact_type: Type of artifact to generate
            title: Artifact title
            context: Retrieved context
            instructions: Optional custom instructions

        Returns:
            Formatted prompt for Claude
        """
        prompt_parts = []

        # Add retrieved context
        if context:
            prompt_parts.append("# Source Material\n")
            prompt_parts.append(context)
            prompt_parts.append("\n---\n")

        # Add generation task
        prompt_parts.append(f"# Task\n")
        prompt_parts.append(f"Create a {artifact_type.value} titled: **{title}**\n")

        # Add custom instructions if provided
        if instructions:
            prompt_parts.append(f"\n## Additional Instructions\n{instructions}\n")

        # Add formatting reminder
        prompt_parts.append(
            "\n## Format\n"
            "- Use markdown formatting (headings, lists, bold, italic, code blocks)\n"
            "- Start with a clear title (# heading)\n"
            "- Structure content logically with appropriate headings\n"
            "- Be comprehensive but concise\n"
        )

        return "\n".join(prompt_parts)

    async def generate_artifact(
        self,
        db: AsyncSession,
        artifact_type: ArtifactType,
        title: str,
        project_id: int,
        query: str,
        category_id: Optional[int] = None,
        instructions: Optional[str] = None,
        max_context_chunks: int = 10,
        min_similarity: float = 0.5,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> tuple[str, List[Dict], Dict]:
        """
        Generate artifact content using Claude API with RAG

        Args:
            db: Database session
            artifact_type: Type of artifact to generate
            title: Artifact title
            project_id: Project context
            query: Search query for context retrieval
            category_id: Optional category filter
            instructions: Optional custom instructions
            max_context_chunks: Maximum chunks to retrieve
            min_similarity: Minimum similarity threshold
            temperature: Claude API temperature
            max_tokens: Maximum tokens in response

        Returns:
            Tuple of (generated content, retrieved chunks, generation metadata)

        Example:
            >>> generator = ArtifactGenerator()
            >>> content, chunks, metadata = await generator.generate_artifact(
            ...     db=db,
            ...     artifact_type=ArtifactType.SUMMARY,
            ...     title="Chapter 3 Summary: Neural Networks",
            ...     project_id=1,
            ...     query="chapter 3 neural networks",
            ...     category_id=15  # Chapter 3 category
            ... )
        """
        start_time = time.time()

        # Step 1: Retrieve context
        logger.info(f"Generating {artifact_type.value} artifact: {title}")
        retrieved_chunks, context = await self.retrieve_context(
            db=db,
            query=query,
            project_id=project_id,
            category_id=category_id,
            max_chunks=max_context_chunks,
            min_similarity=min_similarity
        )

        if not context:
            raise ValueError(
                f"No relevant content found for query: {query}. "
                f"Cannot generate artifact without source material."
            )

        # Step 2: Build prompts
        system_prompt = self.SYSTEM_PROMPTS.get(
            artifact_type,
            self.SYSTEM_PROMPTS[ArtifactType.CUSTOM]
        )

        user_prompt = self.build_generation_prompt(
            artifact_type=artifact_type,
            title=title,
            context=context,
            instructions=instructions
        )

        # Step 3: Call Claude API
        logger.info(f"Calling Claude API with model: {self.model}")

        try:
            response = self.anthropic.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            # Extract response
            content = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            processing_time = (time.time() - start_time) * 1000  # Convert to ms

            # Build metadata
            metadata = {
                "model": self.model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "tokens_used": tokens_used,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "processing_time_ms": round(processing_time, 2),
                "chunks_retrieved": len(retrieved_chunks),
                "source_documents": list(set([
                    chunk.get("document_title") or chunk.get("document_filename")
                    for chunk in retrieved_chunks
                ])),
                "query": query,
            }

            if category_id:
                metadata["category_id"] = category_id

            logger.info(
                f"Generated {artifact_type.value}: {len(content)} chars, "
                f"{tokens_used} tokens, {processing_time:.2f}ms"
            )

            return content, retrieved_chunks, metadata

        except Exception as e:
            logger.error(f"Artifact generation failed: {str(e)}")
            raise Exception(f"Failed to generate {artifact_type.value}: {str(e)}")

    async def regenerate_artifact(
        self,
        db: AsyncSession,
        original_content: str,
        original_metadata: Dict,
        artifact_type: ArtifactType,
        title: str,
        project_id: int,
        new_instructions: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> tuple[str, List[Dict], Dict]:
        """
        Regenerate artifact with modified parameters

        Uses original metadata to maintain consistency but allows override
        of generation parameters for refinement.

        Args:
            db: Database session
            original_content: Content from previous version
            original_metadata: Metadata from previous version
            artifact_type: Type of artifact
            title: Artifact title (may be updated)
            project_id: Project context
            new_instructions: Optional new instructions
            temperature: Optional new temperature (overrides original)
            max_tokens: Optional new max_tokens (overrides original)

        Returns:
            Tuple of (generated content, retrieved chunks, generation metadata)
        """
        # Extract original parameters
        query = original_metadata.get("query", "")
        category_id = original_metadata.get("category_id")
        original_temp = original_metadata.get("temperature", 0.7)
        original_max_tokens = original_metadata.get("max_tokens", 4096)

        # Use new parameters if provided, otherwise use original
        final_temperature = temperature if temperature is not None else original_temp
        final_max_tokens = max_tokens if max_tokens is not None else original_max_tokens

        logger.info(f"Regenerating artifact with updated parameters")

        # Generate with updated parameters
        return await self.generate_artifact(
            db=db,
            artifact_type=artifact_type,
            title=title,
            project_id=project_id,
            query=query,
            category_id=category_id,
            instructions=new_instructions,
            temperature=final_temperature,
            max_tokens=final_max_tokens
        )


# Global instance
artifact_generator = ArtifactGenerator()
