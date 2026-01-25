"""
KnowledgeTree Backend - Chat Routes
RAG-powered chat endpoints with Claude API
"""

import logging
import json
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from core.database import get_db
from models.user import User
from models.project import Project
from models.conversation import Conversation
from models.message import Message
from models.category import Category
from schemas.conversation import (
    ChatRequest,
    ChatResponse,
    MessageResponse,
    RetrievedChunk,
    ConversationResponse,
    ConversationWithMessages,
    ConversationListResponse,
    ConversationUpdateRequest,
    MessageRole,
)
from api.dependencies import get_current_active_user, check_messages_limit
from services.rag_service import RAGService
from services.command_parser import command_parser
from services.artifact_generator import artifact_generator
from services.usage_service import usage_service
from services.crawler_orchestrator import CrawlerOrchestrator, ScrapeResult
from models.artifact import Artifact, ArtifactType
from anthropic import Anthropic

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = logging.getLogger(__name__)

# Initialize RAG service
rag_service = RAGService()

# Initialize services for agent mode
crawler_orchestrator = CrawlerOrchestrator()
anthropic_client = Anthropic()


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _messages_limit: None = Depends(check_messages_limit())
):
    """
    Send a message and get an AI response using RAG

    This endpoint:
    1. Checks subscription message limits before processing
    2. Retrieves relevant document chunks using vector search (if use_rag=True)
    3. Builds context from retrieved chunks and conversation history
    4. Generates response using Claude API
    5. Saves both user message and assistant response to database
    6. Tracks message usage for billing and limits

    **Request Body:**
    - `message`: User message (1-5000 chars)
    - `conversation_id`: Existing conversation ID (null for new conversation)
    - `project_id`: Project for RAG context
    - `use_rag`: Enable RAG retrieval (default: true)
    - `max_context_chunks`: Max chunks to retrieve (1-20, default: 5)
    - `min_similarity`: Min similarity threshold (0-1, default: 0.5)
    - `temperature`: Claude temperature (0-1, default: 0.7)

    **Returns:**
    - Assistant's response with metadata
    - Retrieved chunks used for context
    - Token usage and processing time
    """
    # Verify project access
    result = await db.execute(
        select(Project).where(
            Project.id == request.project_id,
            Project.owner_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )

    try:
        # Get or create conversation
        conversation = None
        if request.conversation_id:
            # Verify conversation belongs to user's project
            conv_result = await db.execute(
                select(Conversation)
                .join(Project)
                .where(
                    and_(
                        Conversation.id == request.conversation_id,
                        Conversation.project_id == request.project_id,
                        Project.owner_id == current_user.id
                    )
                )
            )
            conversation = conv_result.scalar_one_or_none()

            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found or access denied"
                )
        else:
            # Create new conversation
            conversation = Conversation(
                project_id=request.project_id,
                user_id=current_user.id,
                title=request.message[:100]  # Use first 100 chars as title
            )
            db.add(conversation)
            await db.flush()  # Get conversation ID

        # Get conversation history
        history_result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.asc())
        )
        history = history_result.scalars().all()

        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in history
        ]

        # Save user message
        user_message = Message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=request.message
        )
        db.add(user_message)

        # Check if message is an artifact generation command
        artifact_id = None
        if command_parser.is_command(request.message):
            logger.info("Detected artifact generation command")

            # Parse command
            command_data = command_parser.parse_command(request.message)

            if command_data:
                # Resolve category ID from identifier
                category_id = await command_parser.resolve_category_id(
                    db=db,
                    project_id=request.project_id,
                    category_identifier=command_data.get("category_identifier")
                )

                # Generate artifact
                try:
                    content, retrieved_chunks, generation_metadata = await artifact_generator.generate_artifact(
                        db=db,
                        artifact_type=command_data["artifact_type"],
                        title=command_data["title"],
                        project_id=request.project_id,
                        query=command_data["query"],
                        category_id=category_id,
                        instructions=command_data.get("instructions"),
                        temperature=request.temperature
                    )

                    # Create artifact in database
                    artifact = Artifact(
                        type=command_data["artifact_type"],
                        title=command_data["title"],
                        content=content,
                        version=1,
                        artifact_metadata=json.dumps(generation_metadata),
                        project_id=request.project_id,
                        user_id=current_user.id,
                        conversation_id=conversation.id,
                        category_id=category_id,
                    )
                    db.add(artifact)
                    await db.flush()  # Get artifact ID
                    artifact_id = artifact.id

                    # Create assistant response about artifact creation
                    response_text = (
                        f"I've created a **{command_data['artifact_type'].value}** for you: "
                        f"**{command_data['title']}**\n\n"
                        f"The artifact was generated using {generation_metadata.get('chunks_retrieved', 0)} "
                        f"relevant document chunks"
                    )

                    if category_id:
                        response_text += " from the specified chapter/section"

                    response_text += (
                        f". You can view, edit, and download it in the Artifacts panel.\n\n"
                        f"**Generation details:**\n"
                        f"- Tokens used: {generation_metadata.get('tokens_used', 0):,}\n"
                        f"- Processing time: {generation_metadata.get('processing_time_ms', 0):.0f}ms\n"
                        f"- Model: {generation_metadata.get('model', 'unknown')}"
                    )

                    tokens_used = generation_metadata.get('tokens_used', 0)
                    processing_time = generation_metadata.get('processing_time_ms', 0)

                    logger.info(f"Created artifact {artifact_id} from chat command")

                except Exception as e:
                    logger.error(f"Artifact generation failed: {str(e)}")
                    # Fallback to normal RAG if artifact generation fails
                    response_text = (
                        f"I tried to generate an artifact for you, but encountered an error: {str(e)}\n\n"
                        f"Let me answer your question using regular search instead..."
                    )

                    # Continue with normal RAG flow
                    response_text_rag, retrieved_chunks, tokens_used, processing_time = await rag_service.generate_response(
                        db=db,
                        query=request.message,
                        project_id=request.project_id,
                        conversation_history=conversation_history,
                        use_rag=request.use_rag,
                        max_context_chunks=request.max_context_chunks,
                        min_similarity=request.min_similarity,
                        temperature=request.temperature
                    )
                    response_text = response_text + "\n\n" + response_text_rag
            else:
                # Command parsing failed, use normal RAG
                response_text, retrieved_chunks, tokens_used, processing_time = await rag_service.generate_response(
                    db=db,
                    query=request.message,
                    project_id=request.project_id,
                    conversation_history=conversation_history,
                    use_rag=request.use_rag,
                    max_context_chunks=request.max_context_chunks,
                    min_similarity=request.min_similarity,
                    temperature=request.temperature
                )
        else:
            # Not a command, generate response using RAG
            response_text, retrieved_chunks, tokens_used, processing_time = await rag_service.generate_response(
                db=db,
                query=request.message,
                project_id=request.project_id,
                conversation_history=conversation_history,
                use_rag=request.use_rag,
                max_context_chunks=request.max_context_chunks,
                min_similarity=request.min_similarity,
                temperature=request.temperature
            )

        # Save assistant message
        assistant_message = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=response_text,
            tokens_used=tokens_used
        )
        db.add(assistant_message)

        # Update conversation metadata
        conversation.message_count = len(history) + 2  # +2 for current messages
        conversation.total_tokens_used = (conversation.total_tokens_used or 0) + tokens_used

        await db.commit()
        await db.refresh(assistant_message)

        # Track usage
        await usage_service.increment_usage(
            db=db,
            user_id=current_user.id,
            metric="messages_sent",
            period="monthly",
            amount=1
        )

        # Format retrieved chunks
        retrieved_chunks_response = [
            RetrievedChunk(
                chunk_id=chunk["chunk_id"],
                document_id=chunk["document_id"],
                document_title=chunk.get("document_title"),
                document_filename=chunk["document_filename"],
                chunk_text=chunk["chunk_text"],
                similarity_score=chunk["similarity_score"]
            )
            for chunk in retrieved_chunks
        ]

        logger.info(
            f"Chat completed for user {current_user.id}: "
            f"conversation={conversation.id}, tokens={tokens_used}, time={processing_time:.2f}ms"
        )

        return ChatResponse(
            conversation_id=conversation.id,
            message=MessageResponse.model_validate(assistant_message),
            retrieved_chunks=retrieved_chunks_response,
            tokens_used=tokens_used,
            model=rag_service.model,
            processing_time_ms=round(processing_time, 2),
            artifact_id=artifact_id
        )

    except Exception as e:
        logger.error(f"Chat failed: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}"
        )


async def generate_categories_from_content(
    content: str,
    url: str,
    project_id: int,
    user_query: str
) -> tuple[list[dict], str]:
    """
    Generate category structure from crawled web content using Claude AI

    Args:
        content: Crawled web page content
        url: Source URL
        project_id: Project ID for categories
        user_query: User's specific query/interest

    Returns:
        Tuple of (categories list, summary text)
    """
    try:
        # Truncate content if too long (Claude has limits)
        max_content_length = 50000  # Leave room for prompt
        if len(content) > max_content_length:
            content = content[:max_content_length] + "\n\n[Content truncated due to length...]"

        prompt = f"""You are a knowledge organization expert. Analyze this web content and create a hierarchical category structure.

Source URL: {url}
User's interest: {user_query}

Content:
{content}

Create a JSON category tree with this structure:
{{
  "categories": [
    {{
      "name": "Main Topic",
      "description": "Brief description",
      "children": [
        {{
          "name": "Subtopic",
          "description": "Brief description",
          "children": []
        }}
      ]
    }}
  ]
}}

Guidelines:
- Create 3-7 main categories based on the content's main topics
- Each category can have 2-5 subcategories if relevant
- Keep descriptions concise (1-2 sentences)
- Focus on topics relevant to the user's interest
- Use clear, descriptive category names
- Return ONLY the JSON, no other text

Generate the category tree JSON:"""

        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            temperature=0.3,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # Parse response
        response_text = response.content[0].text

        # Extract JSON from response (handle potential markdown wrapping)
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            response_text = json_match.group(0)

        import json
        category_data = json.loads(response_text)

        # Flatten the tree into a list with parent relationships
        categories = []
        counter = [0]  # Use list for mutability in nested function

        def process_category(cat_data, parent_id=None, depth=0):
            cat_id = counter[0]
            counter[0] += 1

            category = {
                "id": cat_id,
                "name": cat_data["name"],
                "description": cat_data.get("description", ""),
                "parent_id": parent_id,
                "depth": depth,
                "order": len(categories)
            }
            categories.append(category)

            for child in cat_data.get("children", []):
                process_category(child, cat_id, depth + 1)

        for cat in category_data.get("categories", []):
            process_category(cat)

        # Generate summary
        summary = f"""**📚 Knowledge Tree Generated**

I've analyzed the content from {url} and created a hierarchical category structure with **{len(categories)} categories**.

**Main topics covered:**
{chr(10).join(f"- {cat['name']}" for cat in categories if cat['depth'] == 0)}

The categories have been organized into a tree structure that reflects the main themes and subtopics from the crawled content. You can now explore these categories in the Categories panel to organize your knowledge base."""

        return categories, summary

    except Exception as e:
        logger.error(f"Failed to generate categories: {str(e)}")
        # Return empty categories and error message
        return [], f"I encountered an error while generating categories: {str(e)}\n\nHowever, I've saved the crawled content and you can manually create categories later."


async def process_agent_mode(
    agent_url: str,
    user_query: str,
    project_id: int,
    db: AsyncSession,
    conversation_id: int | None,
    current_user: User
) -> dict:
    """
    Process agent mode: crawl URL, generate categories, return results

    Returns:
        dict with response_text and metadata
    """
    # Step 1: Crawl the URL
    logger.info(f"Agent mode: Starting crawl of {agent_url}")
    scrape_result: ScrapeResult = await crawler_orchestrator.crawl(agent_url)

    if scrape_result.error:
        raise Exception(f"Crawling failed: {scrape_result.error}")

    # Step 2: Generate categories from crawled content
    logger.info(f"Agent mode: Generating categories from content (length: {len(scrape_result.text)})")
    categories, summary = await generate_categories_from_content(
        content=scrape_result.text,
        url=agent_url,
        project_id=project_id,
        user_query=user_query
    )

    # Step 3: Save categories to database
    logger.info(f"Agent mode: Saving {len(categories)} categories to database")
    created_categories = []
    category_id_map = {}  # Maps temporary IDs to real database IDs

    for cat_data in categories:
        # Resolve parent_id to actual database ID
        parent_id = None
        if cat_data["parent_id"] is not None:
            parent_id = category_id_map.get(cat_data["parent_id"])

        # Create category
        category = Category(
            project_id=project_id,
            name=cat_data["name"],
            description=cat_data["description"],
            parent_id=parent_id,
            depth=cat_data["depth"],
            order=cat_data["order"],
            color="#E6E6FA",  # Default lavender
            icon="Folder"
        )
        db.add(category)
        await db.flush()

        # Map temporary ID to real ID
        category_id_map[cat_data["id"]] = category.id
        created_categories.append(category)

    await db.commit()
    logger.info(f"Agent mode: Created {len(created_categories)} categories successfully")

    return {
        "response_text": summary,
        "categories_created": len(created_categories),
        "crawled_title": scrape_result.title,
        "crawled_url": scrape_result.url
    }


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message and get streaming AI response using RAG (SSE)

    This endpoint streams the response token-by-token using Server-Sent Events (SSE).
    Each event is a JSON line with a "type" field:
    - "chunk": Retrieved document chunk metadata
    - "token": Individual response text tokens
    - "error": Error message if generation fails
    - "done": Completion event with final metadata

    **Request Body:** Same as /chat/ endpoint

    **Response Format (SSE):**
    ```
    data: {"type":"chunk","chunk_id":123,"similarity":0.85}

    data: {"type":"token","content":"Hello"}

    data: {"type":"token","content":" there"}

    data: {"type":"done","tokens_used":150,"processing_time_ms":1234}
    ```
    """
    # Verify project access
    result = await db.execute(
        select(Project).where(
            Project.id == request.project_id,
            Project.owner_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )

    async def generate():
        """Async generator for SSE events"""
        try:
            # Get or create conversation
            conversation = None
            if request.conversation_id:
                conv_result = await db.execute(
                    select(Conversation)
                    .join(Project)
                    .where(
                        and_(
                            Conversation.id == request.conversation_id,
                            Conversation.project_id == request.project_id,
                            Project.owner_id == current_user.id
                        )
                    )
                )
                conversation = conv_result.scalar_one_or_none()

                if not conversation:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Conversation not found'})}\n\n"
                    return
            else:
                # Create new conversation
                conversation = Conversation(
                    project_id=request.project_id,
                    user_id=current_user.id,
                    title=request.message[:100]
                )
                db.add(conversation)
                await db.flush()

            # Get conversation history
            history_result = await db.execute(
                select(Message)
                .where(Message.conversation_id == conversation.id)
                .order_by(Message.created_at.asc())
            )
            history = history_result.scalars().all()

            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in history
            ]

            # Save user message
            user_message = Message(
                conversation_id=conversation.id,
                role=MessageRole.USER,
                content=request.message
            )
            db.add(user_message)

            # Track response content for saving later
            response_content = []
            retrieved_chunks_list = []
            tokens_used = 0
            processing_time = 0

            # ============================================
            # AGENT MODE: Crawl URL → Generate Categories → Response
            # ============================================
            if request.agent_mode and request.agent_url:
                try:
                    # Send crawling status
                    yield f"data: {json.dumps({'type': 'agent_status', 'status': 'crawling', 'message': f'Crawling {request.agent_url}...'})}\n\n"

                    # Process agent mode workflow
                    result = await process_agent_mode(
                        agent_url=request.agent_url,
                        user_query=request.message,
                        project_id=request.project_id,
                        db=db,
                        conversation_id=conversation.id,
                        current_user=current_user
                    )

                    # Send generating status
                    yield f"data: {json.dumps({'type': 'agent_status', 'status': 'generating', 'message': 'Generating knowledge tree...'})}\n\n"

                    # Stream the response text token by token
                    response_text = result["response_text"]
                    for char in response_text:
                        response_content.append(char)
                        yield f"data: {json.dumps({'type': 'token', 'content': char})}\n\n"

                    # Send done event with metadata
                    cat_count = result.get('categories_created', 0)
                    msg = f'Created {cat_count} categories'
                    yield f"data: {json.dumps({'type': 'agent_status', 'status': 'done', 'message': msg})}\n\n"
                    
                    # Create category tree artifact if categories were created
                    if cat_count > 0:
                        artifact = Artifact(
                            type=ArtifactType.CATEGORY_TREE,
                            title=f"Knowledge Tree from {result.get('crawled_url', request.agent_url)}",
                            content=f"# Knowledge Tree\n\nSource: {result.get('crawled_url', request.agent_url)}\n\nGenerated from {cat_count} categories organized hierarchically.",
                            version=1,
                            artifact_metadata=json.dumps({
                                "source_url": result.get('crawled_url', request.agent_url),
                                "source_type": "web",
                                "categories_created": cat_count,
                                "crawled_title": result.get('crawled_title', ''),
                            }),
                            project_id=request.project_id,
                            user_id=current_user.id,
                            conversation_id=conversation.id,
                        )
                        db.add(artifact)
                        await db.flush()
                        artifact_id = artifact.id
                        
                        # Send artifact_created event
                        yield f"data: {json.dumps({'type': 'artifact_created', 'artifact_id': artifact_id})}\n\n"
                        logger.info(f"Created category tree artifact {artifact_id} in agent mode")
                    
                    yield f"data: {json.dumps({'type': 'done', 'tokens_used': tokens_used, 'processing_time_ms': processing_time})}\n\n"

                    # Save assistant message
                    if response_content:
                        assistant_message = Message(
                            conversation_id=conversation.id,
                            role=MessageRole.ASSISTANT,
                            content="".join(response_content),
                            tokens_used=tokens_used
                        )
                        db.add(assistant_message)

                        # Update conversation metadata
                        conversation.message_count = len(history) + 2
                        conversation.total_tokens_used = (conversation.total_tokens_used or 0) + tokens_used

                        await db.commit()

                        logger.info(
                            f"Agent mode chat completed for user {current_user.id}: "
                            f"conversation={conversation.id}, categories={result['categories_created']}"
                        )

                    return  # Exit agent mode flow

                except Exception as e:
                    logger.error(f"Agent mode failed: {str(e)}")
                    yield f"data: {json.dumps({'type': 'error', 'message': f'Agent mode failed: {str(e)}'})}\n\n"
                    return

            # ============================================
            # NORMAL RAG FLOW
            # ============================================
            # Stream response from RAG service
            async for event in rag_service.stream_response(
                db=db,
                query=request.message,
                project_id=request.project_id,
                conversation_history=conversation_history,
                use_rag=request.use_rag,
                max_context_chunks=request.max_context_chunks,
                min_similarity=request.min_similarity,
                temperature=request.temperature
            ):
                # Send SSE event
                yield f"data: {json.dumps(event)}\n\n"

                # Track data for saving
                if event.get("type") == "token":
                    response_content.append(event.get("content", ""))
                elif event.get("type") == "chunk":
                    retrieved_chunks_list.append(event)
                elif event.get("type") == "done":
                    tokens_used = event.get("tokens_used", 0)
                    processing_time = event.get("processing_time_ms", 0)
                elif event.get("type") == "error":
                    logger.error(f"Streaming error: {event.get('message')}")
                    # Don't return here - let the stream complete naturally

            # Save assistant message
            if response_content:
                assistant_message = Message(
                    conversation_id=conversation.id,
                    role=MessageRole.ASSISTANT,
                    content="".join(response_content),
                    tokens_used=tokens_used
                )
                db.add(assistant_message)

                # Update conversation metadata
                conversation.message_count = len(history) + 2
                conversation.total_tokens_used = (conversation.total_tokens_used or 0) + tokens_used

                await db.commit()

                # Track usage
                await usage_service.increment_usage(
                    db=db,
                    user_id=current_user.id,
                    metric="messages_sent",
                    period="monthly",
                    amount=1
                )

                logger.info(
                    f"Streaming chat completed for user {current_user.id}: "
                    f"conversation={conversation.id}, tokens={tokens_used}"
                )

        except Exception as e:
            logger.error(f"Streaming chat failed: {str(e)}")
            await db.rollback()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable Nginx buffering
        }
    )


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    project_id: int,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List conversations in a project"""
    # Verify project access
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.owner_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )

    # Get total count
    count_result = await db.execute(
        select(func.count(Conversation.id)).where(Conversation.project_id == project_id)
    )
    total = count_result.scalar()

    # Get conversations
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Conversation)
        .where(Conversation.project_id == project_id)
        .order_by(Conversation.updated_at.desc())
        .limit(page_size)
        .offset(offset)
    )
    conversations = result.scalars().all()

    return ConversationListResponse(
        conversations=[ConversationResponse.model_validate(conv) for conv in conversations],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get conversation with full message history"""
    # Verify conversation access
    result = await db.execute(
        select(Conversation)
        .join(Project)
        .where(
            and_(
                Conversation.id == conversation_id,
                Project.owner_id == current_user.id
            )
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied"
        )

    # Get messages
    messages_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    messages = messages_result.scalars().all()

    return ConversationWithMessages(
        id=conversation.id,
        title=conversation.title,
        project_id=conversation.project_id,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[MessageResponse.model_validate(msg) for msg in messages]
    )


@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: int,
    update_data: ConversationUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update conversation metadata (e.g., title)"""
    # Verify conversation access
    result = await db.execute(
        select(Conversation)
        .join(Project)
        .where(
            and_(
                Conversation.id == conversation_id,
                Project.owner_id == current_user.id
            )
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied"
        )

    # Update title
    if update_data.title is not None:
        conversation.title = update_data.title

    await db.commit()
    await db.refresh(conversation)

    return ConversationResponse.model_validate(conversation)


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete conversation and all messages"""
    # Verify conversation access
    result = await db.execute(
        select(Conversation)
        .join(Project)
        .where(
            and_(
                Conversation.id == conversation_id,
                Project.owner_id == current_user.id
            )
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied"
        )

    # Delete conversation (messages will be cascade deleted)
    await db.delete(conversation)
    await db.commit()

    logger.info(f"Deleted conversation: {conversation_id}")
    return None
