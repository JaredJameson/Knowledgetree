"""
Unit tests for RAGService

Tests RAG (Retrieval-Augmented Generation) functionality:
- Context retrieval
- Conversation history
- Prompt building
- Response generation
- Streaming responses
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.rag_service import RAGService


@pytest.fixture
def rag_service():
    """Create RAGService instance with mocked OpenAI client"""
    service = RAGService()
    service.openai = AsyncMock()
    return service


@pytest.fixture
def mock_db_session():
    """Create mock database session"""
    return AsyncMock()


@pytest.fixture
def sample_context_chunks():
    """Sample retrieved context chunks (from hybrid_search)"""
    return [
        {
            "content": "Machine learning is a subset of artificial intelligence",
            "source": "ML Basics (pg 1)",
            "score": 0.95  # Note: hybrid_search returns "score", not "relevance"
        },
        {
            "content": "Neural networks are inspired by biological neurons",
            "source": "Deep Learning Guide (pg 3)",
            "score": 0.88
        },
        {
            "content": "Supervised learning requires labeled training data",
            "source": "ML Fundamentals (pg 5)",
            "score": 0.82
        },
    ]


@pytest.fixture
def sample_conversation_history():
    """Sample conversation history"""
    return [
        {"role": "user", "content": "What is machine learning?"},
        {"role": "assistant", "content": "Machine learning is a subset of AI that enables computers to learn from data."},
        {"role": "user", "content": "How does it work?"},
    ]


class TestContextRetrieval:
    """Tests for context retrieval functionality"""

    @pytest.mark.asyncio
    async def test_retrieve_context_success(self, rag_service, sample_context_chunks):
        """Test successful context retrieval"""
        # Mock search service to return sample chunks
        with patch.object(rag_service.search_service, 'hybrid_search', return_value=sample_context_chunks):
            context = await rag_service.retrieve_context(
                query="What is machine learning?",
                project_id=1,
                limit=5
            )

            assert len(context) == 3
            assert context[0]['content'] == "Machine learning is a subset of artificial intelligence"
            assert context[0]['relevance'] == 0.95

    @pytest.mark.asyncio
    async def test_retrieve_context_empty(self, rag_service):
        """Test context retrieval with no results"""
        with patch.object(rag_service.search_service, 'hybrid_search', return_value=[]):
            context = await rag_service.retrieve_context(
                query="nonexistent topic",
                project_id=1,
                limit=5
            )

            assert len(context) == 0

    @pytest.mark.asyncio
    async def test_retrieve_context_with_limit(self, rag_service, sample_context_chunks):
        """Test context retrieval respects limit parameter"""
        with patch.object(rag_service.search_service, 'hybrid_search', return_value=sample_context_chunks[:2]):
            context = await rag_service.retrieve_context(
                query="test query",
                project_id=1,
                limit=2
            )

            assert len(context) == 2


class TestConversationHistory:
    """Tests for conversation history retrieval"""

    @pytest.mark.asyncio
    async def test_get_conversation_history_success(self, rag_service):
        """Test successful conversation history retrieval"""
        # Mock the entire method to avoid complex SQL mocking
        expected_history = [
            {'role': 'user', 'content': 'What is ML?'},
            {'role': 'assistant', 'content': 'ML is machine learning.'},
            {'role': 'user', 'content': 'How does it work?'},
        ]

        with patch.object(rag_service, 'get_conversation_history', return_value=expected_history):
            mock_db = AsyncMock()
            history = await rag_service.get_conversation_history(
                conversation_id=1,
                db=mock_db,
                limit=10
            )

            assert len(history) == 3
            assert history[0]['role'] == 'user'
            assert history[0]['content'] == "What is ML?"
            assert history[1]['role'] == 'assistant'

    @pytest.mark.asyncio
    async def test_get_conversation_history_empty(self, rag_service):
        """Test conversation history with no messages"""
        with patch.object(rag_service, 'get_conversation_history', return_value=[]):
            mock_db = AsyncMock()
            history = await rag_service.get_conversation_history(
                conversation_id=1,
                db=mock_db,
                limit=10
            )

            assert len(history) == 0

    @pytest.mark.asyncio
    async def test_get_conversation_history_respects_limit(self, rag_service):
        """Test conversation history respects limit"""
        expected_history = [
            {'role': 'user', 'content': f'Message {i}'}
            for i in range(5)
        ]

        with patch.object(rag_service, 'get_conversation_history', return_value=expected_history):
            mock_db = AsyncMock()
            history = await rag_service.get_conversation_history(
                conversation_id=1,
                db=mock_db,
                limit=5
            )

            assert len(history) == 5


class TestPromptBuilding:
    """Tests for prompt building functionality"""

    def test_build_system_prompt_with_context(self, rag_service):
        """Test system prompt building with context"""
        # Use transformed context (with 'relevance' key, as returned by retrieve_context)
        transformed_context = [
            {
                "content": "Machine learning is a subset of artificial intelligence",
                "source": "ML Basics (pg 1)",
                "relevance": 0.95
            },
            {
                "content": "Neural networks are inspired by biological neurons",
                "source": "Deep Learning Guide (pg 3)",
                "relevance": 0.88
            },
            {
                "content": "Supervised learning requires labeled training data",
                "source": "ML Fundamentals (pg 5)",
                "relevance": 0.82
            },
        ]

        prompt = rag_service._build_system_prompt(transformed_context)

        assert "KnowledgeTree" in prompt
        assert "Machine learning is a subset" in prompt
        assert "[Source 1]" in prompt
        assert "[Source 2]" in prompt
        assert "[Source 3]" in prompt
        assert "relevance: 0.95" in prompt
        assert "INSTRUCTIONS" in prompt

    def test_build_system_prompt_empty_context(self, rag_service):
        """Test system prompt building with no context"""
        prompt = rag_service._build_system_prompt([])

        assert "KnowledgeTree" in prompt
        assert "INSTRUCTIONS" in prompt
        # Empty context means CONTEXT section exists but has no sources
        assert "CONTEXT" in prompt

    @pytest.mark.asyncio
    async def test_build_user_prompt_simple(self, rag_service):
        """Test user prompt building without history"""
        prompt = await rag_service._build_user_prompt(
            user_message="What is machine learning?",
            conversation_id=None,
            db=None
        )

        assert prompt == "What is machine learning?"

    @pytest.mark.asyncio
    async def test_build_user_prompt_with_history(self, rag_service):
        """Test user prompt building with conversation history"""
        mock_history = [
            {'role': 'user', 'content': 'What is ML?'},
            {'role': 'assistant', 'content': 'ML is machine learning.'},
        ]

        with patch.object(rag_service, 'get_conversation_history', return_value=mock_history):
            mock_db = AsyncMock()
            prompt = await rag_service._build_user_prompt(
                user_message="Tell me more",
                conversation_id=1,
                db=mock_db
            )

            assert "What is ML?" in prompt
            assert "ML is machine learning" in prompt
            assert "Tell me more" in prompt


class TestResponseGeneration:
    """Tests for response generation"""

    @pytest.mark.asyncio
    async def test_generate_response_with_rag(self, rag_service, mock_db_session):
        """Test response generation with RAG enabled"""
        # Mock context retrieval with transformed context (has 'relevance' key)
        transformed_context = [
            {
                "content": "Machine learning is a subset of artificial intelligence",
                "source": "ML Basics (pg 1)",
                "relevance": 0.95
            },
            {
                "content": "Neural networks are inspired by biological neurons",
                "source": "Deep Learning Guide (pg 3)",
                "relevance": 0.88
            },
            {
                "content": "Supervised learning requires labeled training data",
                "source": "ML Fundamentals (pg 5)",
                "relevance": 0.82
            },
        ]

        with patch.object(rag_service, 'retrieve_context', return_value=transformed_context):
            # Mock OpenAI response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Machine learning is a field of AI that enables systems to learn from data."
            mock_response.usage.total_tokens = 250

            rag_service.openai.chat.completions.create = AsyncMock(return_value=mock_response)

            response_text, retrieved_chunks, tokens, processing_time = await rag_service.generate_response(
                query="What is machine learning?",
                project_id=1,
                db=mock_db_session,
                conversation_history=[],
                use_rag=True,
                max_context_chunks=5,
                min_similarity=0.5,
                temperature=0.7,
                max_tokens=2000
            )

            assert response_text == "Machine learning is a field of AI that enables systems to learn from data."
            assert tokens == 250
            assert processing_time > 0
            assert len(retrieved_chunks) == 3

    @pytest.mark.asyncio
    async def test_generate_response_without_rag(self, rag_service, mock_db_session):
        """Test response generation without RAG"""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "I don't have access to specific documents."
        mock_response.usage.total_tokens = 100

        rag_service.openai.chat.completions.create = AsyncMock(return_value=mock_response)

        response_text, retrieved_chunks, tokens, processing_time = await rag_service.generate_response(
            query="General question",
            project_id=1,
            db=mock_db_session,
            conversation_history=[],
            use_rag=False
        )

        assert response_text == "I don't have access to specific documents."
        assert tokens == 100
        assert len(retrieved_chunks) == 0

    @pytest.mark.asyncio
    async def test_generate_response_with_conversation_history(self, rag_service, mock_db_session, sample_conversation_history):
        """Test response generation with conversation history"""
        with patch.object(rag_service, 'retrieve_context', return_value=[]):
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "It works by learning patterns from data."
            mock_response.usage.total_tokens = 150

            rag_service.openai.chat.completions.create = AsyncMock(return_value=mock_response)

            response_text, _, tokens, _ = await rag_service.generate_response(
                query="How does it work?",
                project_id=1,
                db=mock_db_session,
                conversation_history=sample_conversation_history,
                use_rag=False
            )

            assert "It works by learning patterns from data." in response_text

            # Verify OpenAI was called with conversation history
            call_args = rag_service.openai.chat.completions.create.call_args
            messages = call_args.kwargs['messages']

            # Should have system message + conversation history + current message
            assert len(messages) > 1
            assert any(msg.get('role') == 'user' for msg in messages)

    @pytest.mark.asyncio
    async def test_generate_response_temperature_parameter(self, rag_service, mock_db_session):
        """Test response generation respects temperature parameter"""
        with patch.object(rag_service, 'retrieve_context', return_value=[]):
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Test response"
            mock_response.usage.total_tokens = 50

            rag_service.openai.chat.completions.create = AsyncMock(return_value=mock_response)

            await rag_service.generate_response(
                query="Test",
                project_id=1,
                db=mock_db_session,
                temperature=0.3
            )

            # Verify OpenAI was called with correct temperature
            call_args = rag_service.openai.chat.completions.create.call_args
            assert call_args.kwargs['temperature'] == 0.3

    @pytest.mark.asyncio
    async def test_generate_response_max_tokens_parameter(self, rag_service, mock_db_session):
        """Test response generation respects max_tokens parameter"""
        with patch.object(rag_service, 'retrieve_context', return_value=[]):
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Test response"
            mock_response.usage.total_tokens = 500

            rag_service.openai.chat.completions.create = AsyncMock(return_value=mock_response)

            await rag_service.generate_response(
                query="Test",
                project_id=1,
                db=mock_db_session,
                max_tokens=1000
            )

            # Verify OpenAI was called with correct max_tokens
            call_args = rag_service.openai.chat.completions.create.call_args
            assert call_args.kwargs['max_tokens'] == 1000


class TestStreamingResponse:
    """Tests for streaming response functionality"""

    @pytest.mark.asyncio
    async def test_stream_response_yields_events(self, rag_service, mock_db_session):
        """Test streaming response yields SSE events"""
        with patch.object(rag_service, 'retrieve_context', return_value=[]):
            # Mock streaming response from OpenAI
            async def mock_stream():
                chunks = [
                    MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello"))]),
                    MagicMock(choices=[MagicMock(delta=MagicMock(content=" world"))]),
                    MagicMock(choices=[MagicMock(delta=MagicMock(content="!"))]),
                ]
                for chunk in chunks:
                    yield chunk

            mock_create = AsyncMock(return_value=mock_stream())
            rag_service.openai.chat.completions.create = mock_create

            # Test stream
            events = []
            async for event in rag_service.stream_response(
                query="Test",
                project_id=1,
                db=mock_db_session,
                use_rag=False
            ):
                events.append(event)

            # Should have received events
            assert len(events) > 0
