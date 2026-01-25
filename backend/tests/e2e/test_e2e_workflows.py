"""
End-to-End Integration Tests for KnowledgeTree

Tests complete user workflows from start to finish:
1. Complete RAG Workflow: Register → Upload → Process → Search → Chat
2. Category Management Workflow: Upload → Generate Categories → Assign → Search
3. AI Insights Workflow: Upload Multiple → Generate Insights
4. Multi-User Access Control: User isolation and permissions
"""

import pytest
import io
from unittest.mock import patch, MagicMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import numpy as np

from models.user import User
from models.project import Project
from models.document import Document, ProcessingStatus
from models.chunk import Chunk
from models.category import Category
from models.conversation import Conversation
from models.message import Message
from services.toc_extractor import TocEntry, TocExtractionResult, ExtractionMethod


@pytest.fixture
def mock_pdf_file():
    """Create a mock PDF file for E2E tests"""
    pdf_content = b"%PDF-1.4\n%Test PDF content for E2E testing\n%%EOF"
    return ("e2e_test.pdf", io.BytesIO(pdf_content), "application/pdf")


@pytest.fixture
def mock_pdf_with_toc():
    """Create a mock PDF file with table of contents"""
    pdf_content = b"%PDF-1.4\n%PDF with TOC\n%%EOF"
    return ("toc_test.pdf", io.BytesIO(pdf_content), "application/pdf")


class TestCompleteRAGWorkflow:
    """
    Test complete RAG workflow from registration to chat

    Workflow:
    1. Register new user
    2. Login and get tokens
    3. Create project
    4. Upload PDF document
    5. Process document (extract text + generate embeddings)
    6. Search documents (vector search)
    7. Chat with RAG (retrieve + generate)
    8. Export results
    """

    @pytest.mark.asyncio
    async def test_complete_rag_workflow(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        mock_pdf_file: tuple,
    ):
        """Test complete RAG workflow end-to-end"""

        # ============================================
        # STEP 1: Register new user
        # ============================================
        registration_data = {
            "email": "rag_user@example.com",
            "password": "SecurePassword123!",
            "full_name": "RAG Test User",
        }

        register_response = await client.post(
            "/api/v1/auth/register",
            json=registration_data,
        )
        assert register_response.status_code == 201
        register_data = register_response.json()
        access_token = register_data["access_token"]
        user_id = register_data["user"]["id"]

        headers = {"Authorization": f"Bearer {access_token}"}

        # ============================================
        # STEP 2: Verify user can get their info
        # ============================================
        me_response = await client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200
        assert me_response.json()["email"] == registration_data["email"]

        # ============================================
        # STEP 3: Create project
        # ============================================
        project_data = {
            "name": "RAG Test Project",
            "description": "Testing complete RAG workflow",
            "color": "#3B82F6",
        }

        project_response = await client.post(
            "/api/v1/projects",
            json=project_data,
            headers=headers,
        )
        assert project_response.status_code == 201
        project = project_response.json()
        project_id = project["id"]
        assert project["name"] == project_data["name"]

        # ============================================
        # STEP 4: Upload PDF document
        # ============================================
        filename, file_content, content_type = mock_pdf_file

        with patch('api.routes.documents.pdf_processor.save_uploaded_file') as mock_save:
            mock_save.return_value = f"/tmp/uploads/{filename}"

            upload_response = await client.post(
                "/api/v1/documents/upload",
                headers=headers,
                files={"file": (filename, file_content, content_type)},
                data={"project_id": project_id},
            )

        assert upload_response.status_code == 201
        upload_data = upload_response.json()
        document_id = upload_data["id"]
        assert upload_data["processing_status"] == ProcessingStatus.PENDING

        # ============================================
        # STEP 5: Process document (extract + vectorize)
        # ============================================
        mock_extracted_text = """
        This is a test document about artificial intelligence and machine learning.
        RAG (Retrieval-Augmented Generation) is a powerful technique for building
        knowledge-based AI systems. It combines information retrieval with language
        generation to provide accurate, contextual responses.
        """

        mock_chunks = [
            {
                "text": "This is a test document about artificial intelligence and machine learning.",
                "chunk_index": 0,
                "document_id": 1,  # Will be updated
                "chunk_metadata": {
                    "start_char": 0,
                    "end_char": 76,
                    "length": 76,
                }
            },
            {
                "text": "RAG (Retrieval-Augmented Generation) is a powerful technique for building knowledge-based AI systems.",
                "chunk_index": 1,
                "document_id": 1,
                "chunk_metadata": {
                    "start_char": 77,
                    "end_char": 178,
                    "length": 101,
                }
            },
            {
                "text": "It combines information retrieval with language generation to provide accurate, contextual responses.",
                "chunk_index": 2,
                "document_id": 1,
                "chunk_metadata": {
                    "start_char": 179,
                    "end_char": 280,
                    "length": 101,
                }
            },
        ]

        with patch('api.routes.documents.pdf_processor.process_pdf') as mock_process:
            with patch('api.routes.documents.text_chunker.chunk_text') as mock_chunk:
                with patch('api.routes.documents.embedding_generator.generate_contextual_embedding') as mock_embed:
                    mock_process.return_value = (mock_extracted_text, 1)  # (text, page_count)
                    mock_chunk.return_value = mock_chunks
                    mock_embed.return_value = np.random.rand(1024).tolist()

                    process_response = await client.post(
                        f"/api/v1/documents/{document_id}/process",
                        headers=headers,
                    )

        assert process_response.status_code == 200
        processed_doc = process_response.json()
        assert processed_doc["processing_status"] == ProcessingStatus.COMPLETED
        assert processed_doc["page_count"] == 1

        # Verify chunks were created
        result = await db_session.execute(
            select(Chunk).where(Chunk.document_id == document_id)
        )
        chunks = result.scalars().all()
        assert len(chunks) == 3

        # ============================================
        # STEP 6: Search documents (vector search)
        # ============================================
        # Mock search service
        with patch('api.routes.search.search_service.search') as mock_search:
            mock_search.return_value = (
                [
                    {
                        "chunk_id": chunks[0].id,
                        "document_id": document_id,
                        "document_title": "RAG Test Project",
                        "document_filename": "e2e_test.pdf",
                        "chunk_text": chunks[0].text,
                        "chunk_index": 0,
                        "similarity_score": 0.95,
                        "chunk_metadata": {},
                        "document_created_at": chunks[0].created_at,
                    }
                ],
                0.015  # query time in seconds
            )

            search_response = await client.post(
                "/api/v1/search/",
                json={
                    "query": "What is RAG?",
                    "project_id": project_id,
                    "top_k": 5,
                },
                headers=headers,
            )

        assert search_response.status_code == 200
        search_results = search_response.json()
        assert "results" in search_results
        assert len(search_results["results"]) > 0
        assert search_results["results"][0]["similarity_score"] > 0.9

        # ============================================
        # STEP 7: Chat with RAG
        # ============================================
        # Mock RAG service and Claude API
        mock_rag_context = [
            {
                "content": chunks[0].text,
                "source": "e2e_test.pdf",
                "relevance": 0.95
            },
            {
                "content": chunks[1].text,
                "source": "e2e_test.pdf",
                "relevance": 0.90
            }
        ]
        mock_claude_response = "RAG (Retrieval-Augmented Generation) is a powerful technique that combines information retrieval with language generation to provide accurate, contextual responses based on your knowledge base."

        with patch('api.routes.chat.rag_service.retrieve_context') as mock_retrieve:
            with patch('api.routes.chat.anthropic_client.messages.create') as mock_claude:
                mock_retrieve.return_value = mock_rag_context

                # Mock Claude API response
                mock_message = MagicMock()
                mock_message.content = [MagicMock(text=mock_claude_response)]
                mock_message.id = "msg_test123"
                mock_message.model = "claude-3-5-sonnet-20241022"
                mock_message.usage.input_tokens = 100
                mock_message.usage.output_tokens = 50
                mock_claude.return_value = mock_message

                chat_response = await client.post(
                    "/api/v1/chat/",
                    json={
                        "message": "What is RAG and how does it work?",
                        "project_id": project_id,
                        "use_rag": True,
                    },
                    headers=headers,
                )

        assert chat_response.status_code == 200
        chat_data = chat_response.json()
        assert "message" in chat_data
        assert "content" in chat_data["message"]
        assert "RAG" in chat_data["message"]["content"]
        assert "retrieved_chunks" in chat_data
        assert len(chat_data["retrieved_chunks"]) > 0

        # ============================================
        # STEP 8: Verify conversation was saved
        # ============================================
        conversations_response = await client.get(
            f"/api/v1/chat/conversations?project_id={project_id}",
            headers=headers,
        )
        assert conversations_response.status_code == 200
        conversations_data = conversations_response.json()
        assert "conversations" in conversations_data
        assert len(conversations_data["conversations"]) > 0

        # ============================================
        # STEP 9: Get project statistics
        # ============================================
        project_response = await client.get(
            f"/api/v1/projects/{project_id}",
            headers=headers,
        )
        assert project_response.status_code == 200
        final_project = project_response.json()
        assert final_project["document_count"] == 1
        assert final_project["total_chunks"] == 3

        # ============================================
        # STEP 10: List documents to verify
        # ============================================
        docs_response = await client.get(
            "/api/v1/documents/",
            params={"project_id": project_id},
            headers=headers,
        )
        assert docs_response.status_code == 200
        docs_data = docs_response.json()
        assert docs_data["total"] == 1
        assert docs_data["documents"][0]["processing_status"] == ProcessingStatus.COMPLETED

        print("\n✅ Complete RAG Workflow Test PASSED")
        print(f"   User: {registration_data['email']}")
        print(f"   Project: {project_data['name']}")
        print(f"   Document: {filename}")
        print(f"   Chunks: {len(chunks)}")
        print(f"   Search results: {len(search_results['results'])}")
        print(f"   Chat answer: {chat_data['message']['content'][:100]}...")


class TestCategoryManagementWorkflow:
    """
    Test category management workflow

    Workflow:
    1. Create project
    2. Upload PDF with table of contents
    3. Generate categories from TOC
    4. Manually create additional categories
    5. Assign document to category
    6. Search within category
    7. Get category tree
    """

    @pytest.mark.asyncio
    async def test_category_workflow(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user: User,
        db_session: AsyncSession,
        mock_pdf_with_toc: tuple,
    ):
        """Test complete category management workflow"""

        # ============================================
        # STEP 1: Create project
        # ============================================
        project_response = await client.post(
            "/api/v1/projects",
            json={"name": "Category Test Project"},
            headers=auth_headers,
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]

        # ============================================
        # STEP 2: Upload PDF document
        # ============================================
        filename, file_content, content_type = mock_pdf_with_toc

        with patch('api.routes.documents.pdf_processor.save_uploaded_file') as mock_save:
            # Return a valid file path
            mock_save.return_value = "/tmp/test_toc_doc.pdf"

            upload_response = await client.post(
                "/api/v1/documents/upload",
                headers=auth_headers,
                files={"file": (filename, file_content, content_type)},
                data={"project_id": project_id},
            )

        assert upload_response.status_code == 201
        document_id = upload_response.json()["id"]

        # ============================================
        # STEP 3: Generate categories from TOC
        # ============================================
        mock_toc_entries = [
            TocEntry(title="Introduction", page=1, level=0),
            TocEntry(title="Background", page=2, level=1),
            TocEntry(title="Methods", page=5, level=0),
            TocEntry(title="Results", page=10, level=0),
            TocEntry(title="Discussion", page=15, level=1),
        ]

        mock_toc_result = TocExtractionResult(
            method=ExtractionMethod.PYMUPDF,
            success=True,
            entries=mock_toc_entries,
            total_entries=len(mock_toc_entries),
            max_depth=2,
        )

        with patch('api.routes.documents.pdf_processor.extract_toc') as mock_extract_toc:
            with patch('services.toc_extractor.extract_toc') as mock_toc_extract:
                with patch('pathlib.Path.exists', return_value=True):
                    mock_extract_toc.return_value = mock_toc_result
                    mock_toc_extract.return_value = mock_toc_result

                    generate_response = await client.post(
                        f"/api/v1/documents/{document_id}/generate-tree",
                        headers=auth_headers,
                    )

        if generate_response.status_code != 200:
            print(f"DEBUG: Response status: {generate_response.status_code}")
            print(f"DEBUG: Response body: {generate_response.json()}")

        assert generate_response.status_code == 200
        generated = generate_response.json()
        assert len(generated["categories"]) > 0

        # ============================================
        # STEP 4: Get category tree
        # ============================================
        tree_response = await client.get(
            f"/api/v1/categories/tree/{project_id}",
            headers=auth_headers,
        )
        assert tree_response.status_code == 200
        tree = tree_response.json()
        # Endpoint zwraca listę kategorii bezpośrednio
        assert isinstance(tree, list)
        assert len(tree) > 0  # Mamy utworzone kategorie z TOC

        # ============================================
        # STEP 5: Create manual category
        # ============================================
        manual_category_response = await client.post(
            f"/api/v1/categories/?project_id={project_id}",
            json={
                "name": "Manual Category",
                "description": "Manually created",
                "color": "#FFE4E1",
            },
            headers=auth_headers,
        )
        assert manual_category_response.status_code == 201
        manual_category = manual_category_response.json()

        # ============================================
        # STEP 6: Assign document to category
        # ============================================
        update_response = await client.patch(
            f"/api/v1/documents/{document_id}",
            json={"category_id": manual_category["id"]},
            headers=auth_headers,
        )
        assert update_response.status_code == 200
        assert update_response.json()["category_id"] == manual_category["id"]

        # ============================================
        # STEP 7: List documents by category
        # ============================================
        docs_by_category = await client.get(
            "/api/v1/documents/",
            params={
                "project_id": project_id,
                "category_id": manual_category["id"],
            },
            headers=auth_headers,
        )
        assert docs_by_category.status_code == 200
        docs = docs_by_category.json()
        assert docs["total"] >= 1

        # ============================================
        # STEP 8: Get category details
        # ============================================
        category_response = await client.get(
            f"/api/v1/categories/{manual_category['id']}",
            headers=auth_headers,
        )
        assert category_response.status_code == 200
        category = category_response.json()
        # Verify category exists and has correct data
        assert category["id"] == manual_category["id"]
        assert category["name"] == "Manual Category"

        print("\n✅ Category Management Workflow Test PASSED")
        print(f"   Generated categories: {len(generated['categories'])}")
        print(f"   Manual category: {manual_category['name']}")
        print(f"   Documents in category: {docs['total']}")


class TestAIInsightsWorkflow:
    """
    Test AI Insights workflow

    Workflow:
    1. Create project
    2. Upload multiple PDF documents
    3. Process all documents
    4. Generate document insights
    5. Generate project insights
    6. List recent insights
    """

    @pytest.mark.asyncio
    async def test_ai_insights_workflow(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
        db_session: AsyncSession,
    ):
        """Test complete AI insights workflow"""

        # Ensure test_project is committed to database (needed for project ownership check)
        await db_session.commit()

        # ============================================
        # STEP 1: Upload multiple documents
        # ============================================
        document_ids = []

        for i in range(3):
            pdf_content = b"%PDF-1.4\n%Document " + str(i).encode() + b"\n%%EOF"

            with patch('api.routes.documents.pdf_processor.save_uploaded_file'):
                upload_response = await client.post(
                    "/api/v1/documents/upload",
                    headers=auth_headers,
                    files={"file": (f"doc_{i}.pdf", io.BytesIO(pdf_content), "application/pdf")},
                    data={"project_id": test_project.id},
                )

            assert upload_response.status_code == 201
            document_ids.append(upload_response.json()["id"])

        # ============================================
        # STEP 2: Process all documents
        # ============================================
        for doc_id in document_ids:
            with patch('api.routes.documents.pdf_processor.process_pdf') as mock_process:
                with patch('api.routes.documents.text_chunker.chunk_text') as mock_chunk:
                    with patch('api.routes.documents.embedding_generator.generate_contextual_embedding') as mock_embed:
                        mock_process.return_value = (f"Content for document {doc_id}", 5)  # (text, page_count)
                        mock_chunk.return_value = [
                            {
                                "text": f"Chunk {i} for doc {doc_id}",
                                "chunk_index": i,
                                "document_id": doc_id,
                                "chunk_metadata": {
                                    "start_char": i*100,
                                    "end_char": (i+1)*100,
                                    "length": 100,
                                }
                            }
                            for i in range(3)
                        ]
                        mock_embed.return_value = np.random.rand(1024).tolist()

                        process_response = await client.post(
                            f"/api/v1/documents/{doc_id}/process",
                            headers=auth_headers,
                        )
                        assert process_response.status_code == 200

        # ============================================
        # STEP 3: Check insights availability
        # ============================================
        with patch('api.routes.insights.insights_service.check_availability') as mock_availability:
            mock_availability.return_value = {
                "available": True,
                "model": "claude-3-5-sonnet-20241022",
                "message": "AI Insights service is available"
            }

            availability_response = await client.get(
                "/api/v1/insights/availability",
                headers=auth_headers,
            )

        assert availability_response.status_code == 200
        availability = availability_response.json()
        assert availability["available"] is True

        # ============================================
        # STEP 4: Generate document insights
        # ============================================
        mock_insight_obj = MagicMock()
        mock_insight_obj.document_id = document_ids[0]
        mock_insight_obj.title = "AI and ML Concepts"
        mock_insight_obj.summary = "This document discusses key concepts in AI and ML."
        mock_insight_obj.key_findings = ["Finding 1", "Finding 2", "Finding 3"]
        mock_insight_obj.topics = ["AI", "Machine Learning", "RAG"]
        mock_insight_obj.entities = ["GPT", "Claude", "LangChain"]
        mock_insight_obj.sentiment = "positive"
        mock_insight_obj.action_items = ["Implement RAG", "Test embeddings"]
        mock_insight_obj.importance_score = 0.85

        with patch('api.routes.insights.insights_service.generate_document_insights') as mock_insights:
            mock_insights.return_value = mock_insight_obj

            doc_insights_response = await client.post(
                f"/api/v1/insights/document/{document_ids[0]}",
                json={"document_id": document_ids[0], "force_refresh": False},
                headers=auth_headers,
            )

        assert doc_insights_response.status_code == 200
        doc_insights = doc_insights_response.json()
        assert "summary" in doc_insights
        assert "key_findings" in doc_insights

        # ============================================
        # STEP 5: Generate project insights
        # ============================================
        from datetime import datetime

        mock_project_insight_obj = MagicMock()
        mock_project_insight_obj.project_id = test_project.id
        mock_project_insight_obj.project_name = test_project.name
        mock_project_insight_obj.executive_summary = "This project contains research on AI technologies."
        mock_project_insight_obj.total_documents = 3
        mock_project_insight_obj.key_themes = ["Artificial Intelligence", "Knowledge Management"]
        mock_project_insight_obj.top_categories = [
            {"name": "AI", "document_count": 2},
            {"name": "ML", "document_count": 1}
        ]
        mock_project_insight_obj.document_summaries = []
        mock_project_insight_obj.patterns = ["Increasing focus on RAG", "Emphasis on embeddings"]
        mock_project_insight_obj.recommendations = ["Deploy to production", "Add more documents"]
        mock_project_insight_obj.generated_at = datetime.now()

        with patch('api.routes.insights.insights_service.generate_project_insights') as mock_proj_insights:
            mock_proj_insights.return_value = mock_project_insight_obj

            proj_insights_response = await client.post(
                "/api/v1/insights/project",
                json={
                    "project_id": test_project.id,
                    "max_documents": 10,
                    "include_categories": True,
                },
                headers=auth_headers,
            )

        if proj_insights_response.status_code != 200:
            print(f"\n❌ Project insights request failed:")
            print(f"   Status: {proj_insights_response.status_code}")
            print(f"   Response: {proj_insights_response.json()}")
            print(f"   Project ID: {test_project.id}")
            print(f"   Project owner_id: {test_project.owner_id}")

        assert proj_insights_response.status_code == 200
        proj_insights = proj_insights_response.json()
        assert "executive_summary" in proj_insights
        assert "key_themes" in proj_insights
        assert "recommendations" in proj_insights

        print("\n✅ AI Insights Workflow Test PASSED")
        print(f"   Documents processed: {len(document_ids)}")
        print(f"   Document insights: {doc_insights['summary'][:50]}...")
        print(f"   Project insights: {proj_insights['executive_summary'][:50]}...")


class TestMultiUserAccessControl:
    """
    Test multi-user access control

    Workflow:
    1. User A creates project and documents
    2. User B tries to access User A's resources
    3. Verify proper 404 responses (not 403 to avoid info leakage)
    4. User B creates their own resources
    5. Verify both users can only see their own data
    """

    @pytest.mark.asyncio
    async def test_multi_user_isolation(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        """Test that users can only access their own resources"""

        # ============================================
        # STEP 1: Register User A
        # ============================================
        user_a_data = {
            "email": "user_a@example.com",
            "password": "PasswordA123!",
            "full_name": "User A",
        }

        reg_a = await client.post("/api/v1/auth/register", json=user_a_data)
        assert reg_a.status_code == 201
        token_a = reg_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # ============================================
        # STEP 2: User A creates project
        # ============================================
        project_a_response = await client.post(
            "/api/v1/projects",
            json={"name": "User A Project"},
            headers=headers_a,
        )
        assert project_a_response.status_code == 201
        project_a_id = project_a_response.json()["id"]

        # ============================================
        # STEP 3: User A uploads document
        # ============================================
        pdf_content = b"%PDF-1.4\n%User A Doc\n%%EOF"

        with patch('api.routes.documents.pdf_processor.save_uploaded_file'):
            upload_a = await client.post(
                "/api/v1/documents/upload",
                headers=headers_a,
                files={"file": ("user_a_doc.pdf", io.BytesIO(pdf_content), "application/pdf")},
                data={"project_id": project_a_id},
            )

        assert upload_a.status_code == 201
        document_a_id = upload_a.json()["id"]

        # ============================================
        # STEP 4: Register User B
        # ============================================
        user_b_data = {
            "email": "user_b@example.com",
            "password": "PasswordB123!",
            "full_name": "User B",
        }

        reg_b = await client.post("/api/v1/auth/register", json=user_b_data)
        assert reg_b.status_code == 201
        token_b = reg_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # ============================================
        # STEP 5: User B tries to access User A's project
        # ============================================
        b_get_a_project = await client.get(
            f"/api/v1/projects/{project_a_id}",
            headers=headers_b,
        )
        assert b_get_a_project.status_code == 404  # Not 403 - avoid info leakage

        # ============================================
        # STEP 6: User B tries to access User A's document
        # ============================================
        b_get_a_doc = await client.get(
            f"/api/v1/documents/{document_a_id}",
            headers=headers_b,
        )
        assert b_get_a_doc.status_code == 404

        # ============================================
        # STEP 7: User B tries to update User A's project
        # ============================================
        b_update_a_project = await client.patch(
            f"/api/v1/projects/{project_a_id}",
            json={"name": "Hacked Name"},
            headers=headers_b,
        )
        assert b_update_a_project.status_code == 404

        # ============================================
        # STEP 8: User B tries to delete User A's document
        # ============================================
        b_delete_a_doc = await client.delete(
            f"/api/v1/documents/{document_a_id}",
            headers=headers_b,
        )
        assert b_delete_a_doc.status_code == 404

        # ============================================
        # STEP 9: User B creates their own project
        # ============================================
        project_b_response = await client.post(
            "/api/v1/projects",
            json={"name": "User B Project"},
            headers=headers_b,
        )
        assert project_b_response.status_code == 201
        project_b_id = project_b_response.json()["id"]

        # ============================================
        # STEP 10: Verify User A can't see User B's project
        # ============================================
        a_get_b_project = await client.get(
            f"/api/v1/projects/{project_b_id}",
            headers=headers_a,
        )
        assert a_get_b_project.status_code == 404

        # ============================================
        # STEP 11: Verify project lists are isolated
        # ============================================
        a_projects = await client.get("/api/v1/projects", headers=headers_a)
        b_projects = await client.get("/api/v1/projects", headers=headers_b)

        assert a_projects.status_code == 200
        assert b_projects.status_code == 200

        a_project_ids = [p["id"] for p in a_projects.json()["projects"]]
        b_project_ids = [p["id"] for p in b_projects.json()["projects"]]

        assert project_a_id in a_project_ids
        assert project_a_id not in b_project_ids
        assert project_b_id in b_project_ids
        assert project_b_id not in a_project_ids

        # ============================================
        # STEP 12: Verify both users can access their own resources
        # ============================================
        a_own_project = await client.get(f"/api/v1/projects/{project_a_id}", headers=headers_a)
        b_own_project = await client.get(f"/api/v1/projects/{project_b_id}", headers=headers_b)

        assert a_own_project.status_code == 200
        assert b_own_project.status_code == 200

        print("\n✅ Multi-User Access Control Test PASSED")
        print(f"   User A project: {project_a_id}")
        print(f"   User B project: {project_b_id}")
        print(f"   Access isolation: VERIFIED")
        print(f"   Info leakage prevention: VERIFIED (404 not 403)")


class TestErrorRecoveryWorkflow:
    """
    Test error recovery and edge cases

    Workflow:
    1. Upload fails mid-process
    2. Processing fails and retries
    3. Search with no results
    4. Chat with empty context
    """

    @pytest.mark.asyncio
    async def test_upload_failure_recovery(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
    ):
        """Test recovery from upload failures"""

        # Simulate upload failure
        with patch('api.routes.documents.pdf_processor.save_uploaded_file') as mock_save:
            mock_save.side_effect = Exception("Disk full")

            pdf_content = b"%PDF-1.4\n%%EOF"
            response = await client.post(
                "/api/v1/documents/upload",
                headers=auth_headers,
                files={"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")},
                data={"project_id": test_project.id},
            )

        # Should return 500 error
        assert response.status_code == 500
        assert "failed" in response.json()["detail"].lower()

        print("\n✅ Error Recovery Test PASSED")
        print(f"   Upload failure handled correctly")
