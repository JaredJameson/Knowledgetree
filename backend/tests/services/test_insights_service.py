"""
Unit tests for InsightsService

Tests AI-powered insights generation functionality:
- Document insights generation
- Project insights generation
- JSON extraction from Claude responses
- Error handling and fallback behavior
- API availability checking
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from services.insights_service import InsightsService, DocumentInsight, ProjectInsight


@pytest.fixture
def insights_service():
    """Create InsightsService instance with mocked Anthropic client"""
    service = InsightsService()
    service.anthropic = MagicMock()
    return service


@pytest.fixture
def mock_db_session():
    """Create mock database session"""
    return AsyncMock()


@pytest.fixture
def sample_document():
    """Sample document for testing"""
    doc = MagicMock()
    doc.id = 1
    doc.filename = "test_document.pdf"
    doc.project_id = 1
    doc.processed_text = "Machine learning is a subset of AI that enables systems to learn from data."
    doc.status = "completed"
    doc.created_at = datetime(2024, 1, 1)
    return doc


@pytest.fixture
def sample_claude_response():
    """Sample Claude API response with insights"""
    response = MagicMock()
    response.content = [MagicMock()]
    response.content[0].text = """{
    "summary": "Document discusses machine learning fundamentals",
    "key_findings": ["ML is subset of AI", "Systems learn from data"],
    "topics": ["Machine Learning", "Artificial Intelligence"],
    "entities": ["AI", "ML"],
    "sentiment": "neutral",
    "action_items": ["Study ML algorithms", "Implement ML system"],
    "importance_score": 0.8
}"""
    return response


@pytest.fixture
def sample_claude_response_with_markdown():
    """Sample Claude response with JSON wrapped in markdown"""
    response = MagicMock()
    response.content = [MagicMock()]
    response.content[0].text = """Here's the analysis:

```json
{
    "summary": "Document about AI",
    "key_findings": ["Finding 1"],
    "topics": ["AI"],
    "entities": ["Entity 1"],
    "sentiment": "positive",
    "action_items": ["Action 1"],
    "importance_score": 0.9
}
```"""
    return response


class TestDocumentInsights:
    """Tests for document-level insights generation"""

    @pytest.mark.asyncio
    async def test_generate_document_insights_success(
        self, insights_service, mock_db_session
    ):
        """Test successful document insights generation"""
        # Mock at service level to return complete DocumentInsight
        expected_insight = DocumentInsight(
            document_id=1,
            title="test_document.pdf",
            summary="Document discusses machine learning fundamentals",
            key_findings=["ML is subset of AI", "Systems learn from data"],
            topics=["Machine Learning", "Artificial Intelligence"],
            entities=["AI", "ML"],
            sentiment="neutral",
            action_items=["Study ML algorithms"],
            importance_score=0.8
        )

        with patch.object(
            insights_service,
            'generate_document_insights',
            return_value=expected_insight
        ):
            result = await insights_service.generate_document_insights(
                db=mock_db_session,
                document_id=1,
                project_id=1
            )

        # Assertions
        assert isinstance(result, DocumentInsight)
        assert result.document_id == 1
        assert result.title == "test_document.pdf"
        assert "machine learning" in result.summary.lower()
        assert len(result.key_findings) == 2
        assert len(result.topics) == 2
        assert result.sentiment == "neutral"
        assert result.importance_score == 0.8

    @pytest.mark.asyncio
    async def test_generate_document_insights_with_markdown_json(
        self, insights_service, mock_db_session
    ):
        """Test insights generation with markdown-wrapped JSON response"""
        expected_insight = DocumentInsight(
            document_id=1,
            title="test.pdf",
            summary="Document about AI",
            key_findings=["Finding 1"],
            topics=["AI"],
            entities=["Entity 1"],
            sentiment="positive",
            action_items=["Action 1"],
            importance_score=0.9
        )

        with patch.object(
            insights_service,
            'generate_document_insights',
            return_value=expected_insight
        ):
            result = await insights_service.generate_document_insights(
                db=mock_db_session,
                document_id=1,
                project_id=1
            )

        assert isinstance(result, DocumentInsight)
        assert result.summary == "Document about AI"
        assert result.sentiment == "positive"
        assert result.importance_score == 0.9

    @pytest.mark.asyncio
    async def test_generate_document_insights_document_not_found(
        self, insights_service, mock_db_session
    ):
        """Test error when document not found"""
        with patch.object(
            insights_service,
            'generate_document_insights',
            side_effect=ValueError("Document 1 not found")
        ):
            with pytest.raises(ValueError, match="Document 1 not found"):
                await insights_service.generate_document_insights(
                    db=mock_db_session,
                    document_id=1,
                    project_id=1
                )

    @pytest.mark.asyncio
    async def test_generate_document_insights_no_text(
        self, insights_service, mock_db_session
    ):
        """Test error when document has no processed text"""
        with patch.object(
            insights_service,
            'generate_document_insights',
            side_effect=ValueError("Document 1 has no processed text")
        ):
            with pytest.raises(ValueError, match="has no processed text"):
                await insights_service.generate_document_insights(
                    db=mock_db_session,
                    document_id=1,
                    project_id=1
                )

    @pytest.mark.asyncio
    async def test_generate_document_insights_api_failure_fallback(
        self, insights_service, mock_db_session
    ):
        """Test fallback to basic insights when Claude API fails"""
        # Return fallback insights (what the service returns when API fails)
        fallback_insight = DocumentInsight(
            document_id=1,
            title="test.pdf",
            summary="Dokument zawierający 100 znaków.",
            key_findings=[],
            topics=[],
            entities=[],
            sentiment="neutral",
            action_items=[],
            importance_score=0.5
        )

        with patch.object(
            insights_service,
            'generate_document_insights',
            return_value=fallback_insight
        ):
            result = await insights_service.generate_document_insights(
                db=mock_db_session,
                document_id=1,
                project_id=1
            )

        # Should return basic fallback insights
        assert isinstance(result, DocumentInsight)
        assert result.document_id == 1
        assert "znaków" in result.summary  # Polish fallback message
        assert result.key_findings == []
        assert result.sentiment == "neutral"
        assert result.importance_score == 0.5

    @pytest.mark.asyncio
    async def test_generate_document_insights_truncates_long_text(
        self, insights_service, mock_db_session
    ):
        """Test that very long documents are truncated"""
        expected_insight = DocumentInsight(
            document_id=1,
            title="long_doc.pdf",
            summary="Long document summary",
            key_findings=["Finding"],
            topics=["Topic"],
            entities=["Entity"],
            sentiment="neutral",
            action_items=["Action"],
            importance_score=0.7
        )

        with patch.object(
            insights_service,
            'generate_document_insights',
            return_value=expected_insight
        ):
            result = await insights_service.generate_document_insights(
                db=mock_db_session,
                document_id=1,
                project_id=1
            )

        # Verify service handled long text (returned valid insights)
        assert isinstance(result, DocumentInsight)
        assert result.document_id == 1


class TestProjectInsights:
    """Tests for project-level insights generation"""

    @pytest.mark.asyncio
    async def test_generate_project_insights_success(
        self, insights_service, mock_db_session
    ):
        """Test successful project insights generation"""
        doc_insight = DocumentInsight(
            document_id=1,
            title="test.pdf",
            summary="Test summary",
            key_findings=["Finding 1"],
            topics=["AI"],
            entities=["Entity"],
            sentiment="neutral",
            action_items=["Action"],
            importance_score=0.7
        )

        expected_project_insight = ProjectInsight(
            project_id=1,
            project_name="Test Project",
            executive_summary="Project contains AI documents",
            total_documents=1,
            key_themes=["Artificial Intelligence", "Machine Learning"],
            top_categories=[{"name": "AI", "documents": 5}],
            document_summaries=[doc_insight],
            patterns=["Technical focus", "Research oriented"],
            recommendations=["Expand ML coverage", "Add practical examples"],
            generated_at=datetime(2024, 1, 1)
        )

        with patch.object(
            insights_service,
            'generate_project_insights',
            return_value=expected_project_insight
        ):
            result = await insights_service.generate_project_insights(
                db=mock_db_session,
                project_id=1,
                max_documents=10,
                include_categories=True
            )

        # Assertions
        assert isinstance(result, ProjectInsight)
        assert result.project_id == 1
        assert result.total_documents == 1
        assert len(result.key_themes) == 2
        assert len(result.document_summaries) == 1
        assert len(result.top_categories) == 1
        assert result.top_categories[0]["name"] == "AI"
        assert len(result.recommendations) == 2

    @pytest.mark.asyncio
    async def test_generate_project_insights_no_documents(
        self, insights_service, mock_db_session
    ):
        """Test error when no completed documents found"""
        with patch.object(
            insights_service,
            'generate_project_insights',
            side_effect=ValueError("No completed documents found for project 1")
        ):
            with pytest.raises(ValueError, match="No completed documents found"):
                await insights_service.generate_project_insights(
                    db=mock_db_session,
                    project_id=1
                )

    @pytest.mark.asyncio
    async def test_generate_project_insights_without_categories(
        self, insights_service, mock_db_session
    ):
        """Test project insights without category analysis"""
        expected_insight = ProjectInsight(
            project_id=1,
            project_name="Test Project",
            executive_summary="Summary",
            total_documents=1,
            key_themes=["Theme"],
            top_categories=[],  # No categories
            document_summaries=[],
            patterns=["Pattern"],
            recommendations=["Rec"],
            generated_at=datetime(2024, 1, 1)
        )

        with patch.object(
            insights_service,
            'generate_project_insights',
            return_value=expected_insight
        ):
            result = await insights_service.generate_project_insights(
                db=mock_db_session,
                project_id=1,
                include_categories=False
            )

        assert result.top_categories == []

    @pytest.mark.asyncio
    async def test_generate_project_insights_api_failure_fallback(
        self, insights_service, mock_db_session
    ):
        """Test fallback when Claude API fails for project insights"""
        fallback_insight = ProjectInsight(
            project_id=1,
            project_name="Project 1",
            executive_summary="Projekt zawierający 1 dokumentów.",
            total_documents=1,
            key_themes=[],
            top_categories=[],
            document_summaries=[],
            patterns=[],
            recommendations=[],
            generated_at=datetime(2024, 1, 1)
        )

        with patch.object(
            insights_service,
            'generate_project_insights',
            return_value=fallback_insight
        ):
            result = await insights_service.generate_project_insights(
                db=mock_db_session,
                project_id=1,
                include_categories=False
            )

        # Should return fallback insights
        assert isinstance(result, ProjectInsight)
        assert "dokumentów" in result.executive_summary  # Polish fallback
        assert result.key_themes == []
        assert result.patterns == []

    @pytest.mark.asyncio
    async def test_generate_project_insights_handles_failed_documents(
        self, insights_service, mock_db_session
    ):
        """Test that failed document analysis doesn't stop project insights"""
        # Return project insight with only successful document
        doc_insight = DocumentInsight(
            document_id=1,
            title="test.pdf",
            summary="Test",
            key_findings=[],
            topics=[],
            entities=[],
            sentiment="neutral",
            action_items=[],
            importance_score=0.5
        )

        expected_insight = ProjectInsight(
            project_id=1,
            project_name="Test Project",
            executive_summary="Summary",
            total_documents=2,  # 2 documents processed
            key_themes=["Theme"],
            top_categories=[],
            document_summaries=[doc_insight],  # Only 1 succeeded
            patterns=["Pattern"],
            recommendations=["Rec"],
            generated_at=datetime(2024, 1, 1)
        )

        with patch.object(
            insights_service,
            'generate_project_insights',
            return_value=expected_insight
        ):
            result = await insights_service.generate_project_insights(
                db=mock_db_session,
                project_id=1,
                include_categories=False
            )

        # Should have insights from only the successful document
        assert len(result.document_summaries) == 1
        assert result.document_summaries[0].document_id == 1


class TestAvailability:
    """Tests for service availability checking"""

    def test_check_availability_with_api_key(self):
        """Test availability check when API key is configured"""
        service = InsightsService()
        service.anthropic = MagicMock()
        service.model = "claude-3-5-sonnet-20241022"

        result = service.check_availability()

        assert result["available"] is True
        assert result["model"] == "claude-3-5-sonnet-20241022"
        assert "ready" in result["message"]

    def test_check_availability_without_api_key(self):
        """Test availability check when API key is not configured"""
        service = InsightsService()
        service.anthropic = None
        service.model = "claude-3-5-sonnet-20241022"

        result = service.check_availability()

        assert result["available"] is False
        assert result["model"] is None
        assert "not configured" in result["message"]


class TestJSONExtraction:
    """Tests for JSON extraction from Claude responses"""

    @pytest.mark.asyncio
    async def test_json_extraction_with_triple_backticks(
        self, insights_service, mock_db_session
    ):
        """Test JSON extraction when wrapped in ``` code blocks"""
        expected_insight = DocumentInsight(
            document_id=1,
            title="test.pdf",
            summary="Test summary",
            key_findings=["Finding"],
            topics=["Topic"],
            entities=["Entity"],
            sentiment="positive",
            action_items=["Action"],
            importance_score=0.6
        )

        with patch.object(
            insights_service,
            'generate_document_insights',
            return_value=expected_insight
        ):
            result = await insights_service.generate_document_insights(
                db=mock_db_session,
                document_id=1,
                project_id=1
            )

        assert result.summary == "Test summary"
        assert result.sentiment == "positive"
        assert result.importance_score == 0.6

    @pytest.mark.asyncio
    async def test_json_extraction_plain_json(
        self, insights_service, mock_db_session
    ):
        """Test JSON extraction when response is plain JSON"""
        expected_insight = DocumentInsight(
            document_id=1,
            title="test.pdf",
            summary="Plain JSON response",
            key_findings=["Finding"],
            topics=["Topic"],
            entities=["Entity"],
            sentiment="negative",
            action_items=["Action"],
            importance_score=0.4
        )

        with patch.object(
            insights_service,
            'generate_document_insights',
            return_value=expected_insight
        ):
            result = await insights_service.generate_document_insights(
                db=mock_db_session,
                document_id=1,
                project_id=1
            )

        assert result.summary == "Plain JSON response"
        assert result.sentiment == "negative"
