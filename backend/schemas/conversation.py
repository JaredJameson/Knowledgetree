"""
KnowledgeTree Backend - Conversation Schemas
Pydantic models for RAG chat conversations
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """Message role in conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatRequest(BaseModel):
    """Chat request with message and context"""
    message: str = Field(..., min_length=1, max_length=5000, description="User message")
    conversation_id: Optional[int] = Field(None, description="Existing conversation ID (null for new)")
    project_id: int = Field(..., description="Project context for RAG retrieval")
    use_rag: bool = Field(True, description="Whether to use RAG retrieval")
    max_context_chunks: int = Field(5, ge=1, le=20, description="Maximum chunks to retrieve for context")
    min_similarity: float = Field(0.5, ge=0.0, le=1.0, description="Minimum similarity for retrieved chunks")
    temperature: float = Field(0.7, ge=0.0, le=1.0, description="Claude API temperature")
    # Agent mode fields
    agent_mode: bool = Field(False, description="Enable agent mode for web crawling and knowledge tree generation")
    agent_url: Optional[str] = Field(None, description="URL to crawl in agent mode")


class RetrievedChunk(BaseModel):
    """Chunk retrieved for RAG context"""
    chunk_id: int
    document_id: int
    document_title: Optional[str]
    document_filename: str
    chunk_text: str
    similarity_score: float


class MessageResponse(BaseModel):
    """Single message in conversation"""
    id: int
    role: MessageRole
    content: str
    created_at: datetime
    tokens_used: Optional[int] = None

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    """Chat response with assistant message and metadata"""
    conversation_id: int = Field(..., description="Conversation ID")
    message: MessageResponse = Field(..., description="Assistant's response")
    retrieved_chunks: List[RetrievedChunk] = Field(..., description="Chunks used for context")
    tokens_used: int = Field(..., description="Total tokens used for this request")
    model: str = Field(..., description="Claude model used")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    artifact_id: Optional[int] = Field(None, description="Created artifact ID (if command generated artifact)")


class ConversationResponse(BaseModel):
    """Conversation with messages"""
    id: int
    title: Optional[str]
    project_id: int
    created_at: datetime
    updated_at: datetime
    message_count: int
    total_tokens_used: int

    class Config:
        from_attributes = True


class ConversationWithMessages(BaseModel):
    """Conversation with full message history"""
    id: int
    title: Optional[str]
    project_id: int
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse]

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """List of conversations with pagination"""
    conversations: List[ConversationResponse]
    total: int
    page: int
    page_size: int


class ConversationUpdateRequest(BaseModel):
    """Update conversation metadata"""
    title: Optional[str] = Field(None, max_length=200, description="Conversation title")
