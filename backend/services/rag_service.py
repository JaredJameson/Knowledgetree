"""
KnowledgeTree Backend - RAG Service
Retrieval-Augmented Generation using OpenAI GPT-4o-mini
"""

import logging
import time
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import asc

from core.config import settings
from services.search_service import SearchService
from models.conversation import Conversation
from models.message import Message

logger = logging.getLogger(__name__)


class RAGService:
    """
    RAG (Retrieval-Augmented Generation) service for generating responses
    with context from uploaded documents.

    Uses OpenAI GPT-4o-mini for efficient and cost-effective responses.
    """

    def __init__(self):
        from openai import AsyncOpenAI
        self.openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.search_service = SearchService()
        self.model = "gpt-4o-mini"

    async def retrieve_context(
        self,
        query: str,
        project_id: int,
        limit: int = 5
    ) -> List[Dict]:
        """
        Retrieve relevant context from vector search.

        Args:
            query: Search query
            project_id: Project ID for filtering
            limit: Maximum number of results

        Returns:
            List of relevant chunks with metadata
        """
        results = await self.search_service.hybrid_search(
            query=query,
            project_id=project_id,
            limit=limit
        )

        # Format results for prompt
        context = []
        for result in results:
            context.append({
                "content": result.get("content", ""),
                "source": result.get("source", ""),
                "relevance": result.get("score", 0.0)
            })

        return context

    async def get_conversation_history(
        self,
        conversation_id: int,
        db: AsyncSession,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get recent conversation history.

        Args:
            conversation_id: Conversation ID
            db: Database session
            limit: Maximum number of previous messages

        Returns:
            List of messages in chronological order
        """
        from sqlalchemy import select
        from models.message import Message

        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(asc(Message.created_at))
            .limit(limit)
        )

        messages = result.scalars().all()

        return [
            {
                "role": "user" if msg.role == "user" else "assistant",
                "content": msg.content
            }
            for msg in messages
        ]

    def _build_system_prompt(self, context: List[Dict]) -> str:
        """
        Build system prompt with RAG context.

        Args:
            context: Retrieved context chunks

        Returns:
            System prompt string
        """
        prompt = """You are a helpful AI assistant for KnowledgeTree, a knowledge management system.
Your task is to answer questions based on the provided context from uploaded documents.

CONTEXT:
"""

        for i, chunk in enumerate(context, 1):
            prompt += f"\n[Source {i}] (relevance: {chunk['relevance']:.2f})\n"
            prompt += f"{chunk['content']}\n"

        prompt += """
INSTRUCTIONS:
- Answer questions using the provided context when relevant
- If the context doesn't contain relevant information, say so clearly
- Cite sources by referring to [Source 1], [Source 2], etc.
- Be accurate and don't make up information
- If you're unsure, say so
"""

        return prompt

    async def _build_user_prompt(
        self,
        user_message: str,
        conversation_id: Optional[int],
        db: Optional[AsyncSession] = None
    ) -> str:
        """
        Build user prompt with conversation history.

        Args:
            user_message: Current user message
            conversation_id: Conversation ID for history
            db: Database session

        Returns:
            User prompt string
        """
        prompt = user_message

        # Add conversation history if available
        if conversation_id and db:
            history = await self.get_conversation_history(conversation_id, db)
            if history:
                prompt = "\n".join([
                    f"{msg['role']}: {msg['content']}"
                    for msg in history
                ]) + f"\nuser: {user_message}"

        return prompt

    async def generate_response(
        self,
        query: str,
        project_id: int,
        db: AsyncSession,
        conversation_history: list = None,
        use_rag: bool = True,
        max_context_chunks: int = 5,
        min_similarity: float = 0.5,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> tuple:
        """
        Generate a response with RAG context.

        Args:
            query: User's query/message
            project_id: Project ID for filtering
            db: Database session
            conversation_history: List of previous messages
            use_rag: Whether to use RAG retrieval
            max_context_chunks: Maximum chunks to retrieve
            min_similarity: Minimum similarity threshold
            temperature: Response randomness (0-1)
            max_tokens: Maximum tokens in response

        Returns:
            Tuple of (response_text, retrieved_chunks, tokens_used, processing_time)
        """
        import time
        start_time = time.time()

        # Get context from vector search if RAG is enabled
        retrieved_chunks = []
        if use_rag:
            context = await self.retrieve_context(
                query=query,
                project_id=project_id,
                limit=max_context_chunks
            )
        else:
            context = []

        # Build system prompt
        system_prompt = self._build_system_prompt(context)

        # Build messages with conversation history
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history if provided
        if conversation_history:
            for msg in conversation_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        # Add current message
        messages.append({
            "role": "user",
            "content": query
        })

        # Generate response using OpenAI
        response = await self.openai.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=messages
        )

        response_text = response.choices[0].message.content
        tokens_used = response.usage.total_tokens

        elapsed = time.time() - start_time
        processing_time = elapsed * 1000  # Convert to ms

        logger.info(
            f"Generated RAG response in {elapsed:.2f}s, "
            f"tokens: {tokens_used}, model: {self.model}"
        )

        # Format retrieved chunks for response
        retrieved_chunks_response = []
        for i, chunk in enumerate(context):
            retrieved_chunks_response.append({
                "chunk_id": i,  # Temporary ID
                "document_id": 0,
                "document_title": chunk.get("source", ""),
                "document_filename": chunk.get("source", ""),
                "chunk_text": chunk["content"],
                "similarity_score": chunk.get("relevance", 0.0)
            })

        return response_text, retrieved_chunks_response, tokens_used, processing_time

    async def stream_response(
        self,
        query: str,
        project_id: int,
        db: AsyncSession,
        conversation_history: list = None,
        use_rag: bool = True,
        max_context_chunks: int = 5,
        min_similarity: float = 0.5,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ):
        """
        Stream a response with RAG context using SSE.

        Args:
            query: User's query/message
            project_id: Project ID for filtering
            db: Database session
            conversation_history: List of previous messages
            use_rag: Whether to use RAG retrieval
            max_context_chunks: Maximum chunks to retrieve
            min_similarity: Minimum similarity threshold
            temperature: Response randomness (0-1)
            max_tokens: Maximum tokens in response

        Yields:
            Event dictionaries for SSE streaming
        """
        import json
        start_time = time.time()

        # Get context from vector search if RAG is enabled
        retrieved_chunks = []
        if use_rag:
            context = await self.retrieve_context(
                query=query,
                project_id=project_id,
                limit=max_context_chunks
            )

            # Send retrieved chunks as events
            for i, chunk in enumerate(context):
                yield {
                    "type": "chunk",
                    "chunk_id": i,
                    "document_title": chunk.get("source", ""),
                    "chunk_text": chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"],
                    "similarity": chunk.get("relevance", 0.0)
                }
                retrieved_chunks.append(chunk)
        else:
            context = []

        # Build system prompt
        system_prompt = self._build_system_prompt(context)

        # Build messages with conversation history
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history if provided
        if conversation_history:
            for msg in conversation_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        # Add current message
        messages.append({
            "role": "user",
            "content": query
        })

        try:
            # Stream response using OpenAI
            stream = await self.openai.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages,
                stream=True
            )

            async for chunk in stream:
                if chunk.choices:
                    delta = chunk.choices[0].delta

                    # Check for content
                    if hasattr(delta, 'content') and delta.content:
                        content = delta.content

                        # Send token event
                        yield {
                            "type": "token",
                            "content": content
                        }

                    # Check for finish reason
                    if hasattr(chunk.choices[0], 'finish_reason') and chunk.choices[0].finish_reason:
                        finish_reason = chunk.choices[0].finish_reason
                        elapsed = time.time() - start_time
                        processing_time_ms = elapsed * 1000

                        # Get final token usage from response if available
                        # Note: OpenAI streaming doesn't provide usage until the end
                        # We estimate based on what we received

                        # Send done event with metadata
                        yield {
                            "type": "done",
                            "tokens_used": getattr(chunk.choices[0], 'usage', {}).get('total_tokens', 0),
                            "processing_time_ms": processing_time_ms,
                            "finish_reason": finish_reason
                        }

                        logger.info(
                            f"Streamed RAG response in {elapsed:.2f}s, "
                            f"model: {self.model}"
                        )
                        break

        except Exception as e:
            logger.error(f"Error streaming response: {e}")
            yield {
                "type": "error",
                "message": str(e)
            }

        except Exception as e:
            logger.error(f"Error streaming response: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    async def generate_answer(
        self,
        question: str,
        context: str,
        max_tokens: int = 1000
    ) -> str:
        """
        Generate a simple answer with provided context.

        Args:
            question: User's question
            context: Context text to use
            max_tokens: Maximum tokens in response

        Returns:
            Generated answer
        """
        response = await self.openai.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=0.5,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Answer questions based on the provided context."
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {question}"
                }
            ]
        )

        return response.choices[0].message.content


# Singleton instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get global RAG service instance"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
