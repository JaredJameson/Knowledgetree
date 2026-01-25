"""
Integration tests for Documents API endpoints

Tests document upload, processing, and management:
- POST /documents/upload - Upload PDF file
- POST /documents/{id}/process - Process document (extract + vectorize)
- GET /documents/ - List documents
- GET /documents/{id} - Get single document
- PATCH /documents/{id} - Update document metadata
- DELETE /documents/{id} - Delete document
- POST /documents/{id}/generate-categories - Generate categories from TOC
"""

import pytest
import io
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.user import User
from models.project import Project
from models.document import Document, ProcessingStatus, DocumentType
from models.chunk import Chunk
from models.category import Category


# Test fixtures for mock PDF data
@pytest.fixture
def mock_pdf_file():
    """Create a mock PDF file for upload tests"""
    # Simple PDF header + minimal content
    pdf_content = b"%PDF-1.4\n%Mock PDF content for testing\n%%EOF"
    return ("test_document.pdf", io.BytesIO(pdf_content), "application/pdf")


@pytest.fixture
def large_pdf_file():
    """Create a mock PDF file exceeding size limit"""
    # Create 101MB of mock PDF data (exceeds 100MB limit)
    large_content = b"%PDF-1.4\n" + b"X" * (101 * 1024 * 1024) + b"\n%%EOF"
    return ("large_document.pdf", io.BytesIO(large_content), "application/pdf")


@pytest.fixture
async def test_document(db_session: AsyncSession, test_project: Project) -> Document:
    """Create a test document"""
    document = Document(
        filename="test.pdf",
        title="Test Document",
        source_type=DocumentType.PDF,
        file_size=1024,
        file_path="/tmp/test.pdf",
        processing_status=ProcessingStatus.PENDING,
        project_id=test_project.id,
    )
    db_session.add(document)
    await db_session.flush()
    await db_session.refresh(document)
    return document


@pytest.fixture
async def processed_document(db_session: AsyncSession, test_project: Project) -> Document:
    """Create a processed document with chunks"""
    document = Document(
        filename="processed.pdf",
        title="Processed Document",
        source_type=DocumentType.PDF,
        file_size=2048,
        file_path="/tmp/processed.pdf",
        processing_status=ProcessingStatus.COMPLETED,
        project_id=test_project.id,
        page_count=10,
        word_count=1000,
    )
    db_session.add(document)
    await db_session.flush()
    await db_session.refresh(document)

    # Add some chunks with mock embeddings
    import numpy as np
    for i in range(5):
        chunk = Chunk(
            document_id=document.id,
            project_id=test_project.id,
            content=f"This is chunk {i} of the processed document.",
            chunk_index=i,
            start_char=i * 100,
            end_char=(i + 1) * 100,
            embedding=np.random.rand(1024).tolist(),  # BGE-M3 1024 dims
        )
        db_session.add(chunk)

    await db_session.flush()
    return document


class TestUploadDocument:
    """Test POST /documents/upload endpoint"""

    @pytest.mark.asyncio
    async def test_upload_document_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
        mock_pdf_file: tuple,
        db_session: AsyncSession,
    ):
        """Test successful document upload"""
        filename, file_content, content_type = mock_pdf_file

        with patch('api.routes.documents.pdf_processor.save_uploaded_file') as mock_save:
            mock_save.return_value = f"/tmp/uploads/{filename}"

            response = await client.post(
                "/api/v1/documents/upload",
                headers=auth_headers,
                files={"file": (filename, file_content, content_type)},
                data={"project_id": test_project.id},
            )

        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "id" in data
        assert data["filename"] == filename
        assert data["file_size"] > 0
        assert data["processing_status"] == ProcessingStatus.PENDING
        assert "message" in data

        # Verify document was created in database
        result = await db_session.execute(
            select(Document).where(Document.id == data["id"])
        )
        db_document = result.scalar_one_or_none()
        assert db_document is not None
        assert db_document.filename == filename
        assert db_document.project_id == test_project.id
        assert db_document.title == "test_document"  # filename without .pdf

    @pytest.mark.asyncio
    async def test_upload_document_with_category(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
        test_categories: list[Category],
        mock_pdf_file: tuple,
    ):
        """Test upload with category assignment"""
        filename, file_content, content_type = mock_pdf_file
        category = test_categories[0]

        with patch('api.routes.documents.pdf_processor.save_uploaded_file'):
            response = await client.post(
                "/api/v1/documents/upload",
                headers=auth_headers,
                files={"file": (filename, file_content, content_type)},
                data={
                    "project_id": test_project.id,
                    "category_id": category.id,
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None

    @pytest.mark.asyncio
    async def test_upload_non_pdf_file(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
    ):
        """Test upload with non-PDF file"""
        txt_content = b"This is a text file"

        response = await client.post(
            "/api/v1/documents/upload",
            headers=auth_headers,
            files={"file": ("document.txt", io.BytesIO(txt_content), "text/plain")},
            data={"project_id": test_project.id},
        )

        assert response.status_code == 400
        assert "pdf" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_upload_file_too_large(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
        large_pdf_file: tuple,
    ):
        """Test upload with file exceeding size limit"""
        filename, file_content, content_type = large_pdf_file

        response = await client.post(
            "/api/v1/documents/upload",
            headers=auth_headers,
            files={"file": (filename, file_content, content_type)},
            data={"project_id": test_project.id},
        )

        assert response.status_code == 400
        assert "size" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_upload_to_nonexistent_project(
        self,
        client: AsyncClient,
        auth_headers: dict,
        mock_pdf_file: tuple,
    ):
        """Test upload to non-existent project"""
        filename, file_content, content_type = mock_pdf_file

        response = await client.post(
            "/api/v1/documents/upload",
            headers=auth_headers,
            files={"file": (filename, file_content, content_type)},
            data={"project_id": 99999},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_upload_to_another_users_project(
        self,
        client: AsyncClient,
        auth_headers: dict,
        mock_pdf_file: tuple,
        db_session: AsyncSession,
    ):
        """Test upload to project owned by another user"""
        from core.security import get_password_hash

        # Create another user and their project
        other_user = User(
            email="other@example.com",
            password_hash=get_password_hash("testpassword"),
            is_active=True,
        )
        db_session.add(other_user)
        await db_session.flush()

        other_project = Project(
            name="Other User's Project",
            owner_id=other_user.id,
        )
        db_session.add(other_project)
        await db_session.flush()
        await db_session.refresh(other_project)

        filename, file_content, content_type = mock_pdf_file

        response = await client.post(
            "/api/v1/documents/upload",
            headers=auth_headers,
            files={"file": (filename, file_content, content_type)},
            data={"project_id": other_project.id},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_upload_without_authentication(
        self,
        client: AsyncClient,
        test_project: Project,
        mock_pdf_file: tuple,
    ):
        """Test upload without authentication"""
        filename, file_content, content_type = mock_pdf_file

        response = await client.post(
            "/api/v1/documents/upload",
            files={"file": (filename, file_content, content_type)},
            data={"project_id": test_project.id},
        )

        assert response.status_code == 401


class TestProcessDocument:
    """Test POST /documents/{id}/process endpoint"""

    @pytest.mark.asyncio
    async def test_process_document_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_document: Document,
        db_session: AsyncSession,
    ):
        """Test successful document processing"""
        # Mock the PDF processor and embedding generator
        mock_text = "This is extracted text from the PDF document."
        mock_metadata = {
            "page_count": 5,
            "word_count": 100,
            "has_images": True,
            "has_tables": False,
        }

        with patch('api.routes.documents.pdf_processor.process_pdf') as mock_process:
            with patch('api.routes.documents.text_chunker.chunk_text') as mock_chunk:
                with patch('api.routes.documents.embedding_generator.generate_embeddings') as mock_embed:
                    # Setup mocks
                    mock_process.return_value = (mock_text, mock_metadata)
                    mock_chunk.return_value = [
                        {"content": "Chunk 1", "start_char": 0, "end_char": 10},
                        {"content": "Chunk 2", "start_char": 10, "end_char": 20},
                    ]
                    import numpy as np
                    mock_embed.return_value = np.random.rand(1024).tolist()

                    response = await client.post(
                        f"/api/v1/documents/{test_document.id}/process",
                        headers=auth_headers,
                    )

        assert response.status_code == 200
        data = response.json()

        # Verify response
        assert data["id"] == test_document.id
        assert data["processing_status"] == ProcessingStatus.COMPLETED
        assert data["page_count"] == 5
        assert data["word_count"] == 100

        # Verify chunks were created
        result = await db_session.execute(
            select(Chunk).where(Chunk.document_id == test_document.id)
        )
        chunks = result.scalars().all()
        assert len(chunks) == 2

    @pytest.mark.asyncio
    async def test_process_nonexistent_document(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test processing non-existent document"""
        response = await client.post(
            "/api/v1/documents/99999/process",
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_process_another_users_document(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test processing document owned by another user"""
        from core.security import get_password_hash

        # Create another user and their document
        other_user = User(
            email="other2@example.com",
            password_hash=get_password_hash("testpassword"),
            is_active=True,
        )
        db_session.add(other_user)
        await db_session.flush()

        other_project = Project(
            name="Other Project",
            owner_id=other_user.id,
        )
        db_session.add(other_project)
        await db_session.flush()

        other_document = Document(
            filename="other.pdf",
            title="Other Document",
            source_type=DocumentType.PDF,
            file_size=1024,
            processing_status=ProcessingStatus.PENDING,
            project_id=other_project.id,
        )
        db_session.add(other_document)
        await db_session.flush()
        await db_session.refresh(other_document)

        response = await client.post(
            f"/api/v1/documents/{other_document.id}/process",
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestListDocuments:
    """Test GET /documents/ endpoint"""

    @pytest.mark.asyncio
    async def test_list_documents_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
        test_document: Document,
        processed_document: Document,
    ):
        """Test listing documents"""
        response = await client.get(
            "/api/v1/documents/",
            headers=auth_headers,
            params={"project_id": test_project.id},
        )

        assert response.status_code == 200
        data = response.json()

        assert "documents" in data
        assert "total" in data
        assert data["total"] >= 2
        assert len(data["documents"]) >= 2

        # Verify document fields
        for doc in data["documents"]:
            assert "id" in doc
            assert "filename" in doc
            assert "title" in doc
            assert "processing_status" in doc
            assert "created_at" in doc

    @pytest.mark.asyncio
    async def test_list_documents_pagination(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
        db_session: AsyncSession,
    ):
        """Test document list pagination"""
        # Create 5 documents
        for i in range(5):
            document = Document(
                filename=f"doc_{i}.pdf",
                title=f"Document {i}",
                source_type=DocumentType.PDF,
                file_size=1024,
                processing_status=ProcessingStatus.PENDING,
                project_id=test_project.id,
            )
            db_session.add(document)
        await db_session.flush()

        # Get first page (2 items)
        response = await client.get(
            "/api/v1/documents/",
            headers=auth_headers,
            params={"project_id": test_project.id, "page": 1, "page_size": 2},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["page_size"] == 2

    @pytest.mark.asyncio
    async def test_list_documents_filter_by_category(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_project: Project,
        test_categories: list[Category],
        db_session: AsyncSession,
    ):
        """Test filtering documents by category"""
        category = test_categories[0]

        # Create document with category
        document = Document(
            filename="categorized.pdf",
            title="Categorized Document",
            source_type=DocumentType.PDF,
            file_size=1024,
            processing_status=ProcessingStatus.PENDING,
            project_id=test_project.id,
            category_id=category.id,
        )
        db_session.add(document)
        await db_session.flush()

        response = await client.get(
            "/api/v1/documents/",
            headers=auth_headers,
            params={"project_id": test_project.id, "category_id": category.id},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        # All documents should have this category
        for doc in data["documents"]:
            if doc["category_id"] is not None:
                assert doc["category_id"] == category.id

    @pytest.mark.asyncio
    async def test_list_documents_without_project_filter(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test listing documents without project_id filter"""
        response = await client.get(
            "/api/v1/documents/",
            headers=auth_headers,
        )

        # Should work - returns all documents user has access to
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_documents_unauthorized(
        self,
        client: AsyncClient,
        test_project: Project,
    ):
        """Test listing documents without authentication"""
        response = await client.get(
            "/api/v1/documents/",
            params={"project_id": test_project.id},
        )

        assert response.status_code == 401


class TestGetDocument:
    """Test GET /documents/{id} endpoint"""

    @pytest.mark.asyncio
    async def test_get_document_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        processed_document: Document,
    ):
        """Test getting a single document"""
        response = await client.get(
            f"/api/v1/documents/{processed_document.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == processed_document.id
        assert data["filename"] == processed_document.filename
        assert data["title"] == processed_document.title
        assert data["processing_status"] == processed_document.processing_status
        assert data["page_count"] == 10
        assert data["word_count"] == 1000
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_get_document_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting non-existent document"""
        response = await client.get(
            "/api/v1/documents/99999",
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_another_users_document(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test getting document owned by another user"""
        from core.security import get_password_hash

        other_user = User(
            email="other3@example.com",
            password_hash=get_password_hash("testpassword"),
            is_active=True,
        )
        db_session.add(other_user)
        await db_session.flush()

        other_project = Project(
            name="Other Project",
            owner_id=other_user.id,
        )
        db_session.add(other_project)
        await db_session.flush()

        other_document = Document(
            filename="other.pdf",
            title="Other Document",
            source_type=DocumentType.PDF,
            file_size=1024,
            processing_status=ProcessingStatus.PENDING,
            project_id=other_project.id,
        )
        db_session.add(other_document)
        await db_session.flush()
        await db_session.refresh(other_document)

        response = await client.get(
            f"/api/v1/documents/{other_document.id}",
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestUpdateDocument:
    """Test PATCH /documents/{id} endpoint"""

    @pytest.mark.asyncio
    async def test_update_document_title(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_document: Document,
        db_session: AsyncSession,
    ):
        """Test updating document title"""
        update_data = {
            "title": "Updated Title",
        }

        response = await client.patch(
            f"/api/v1/documents/{test_document.id}",
            headers=auth_headers,
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"

        # Verify in database
        await db_session.refresh(test_document)
        assert test_document.title == "Updated Title"

    @pytest.mark.asyncio
    async def test_update_document_category(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_document: Document,
        test_categories: list[Category],
    ):
        """Test updating document category"""
        category = test_categories[0]
        update_data = {
            "category_id": category.id,
        }

        response = await client.patch(
            f"/api/v1/documents/{test_document.id}",
            headers=auth_headers,
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["category_id"] == category.id

    @pytest.mark.asyncio
    async def test_update_document_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test updating non-existent document"""
        response = await client.patch(
            "/api/v1/documents/99999",
            headers=auth_headers,
            json={"title": "New Title"},
        )

        assert response.status_code == 404


class TestDeleteDocument:
    """Test DELETE /documents/{id} endpoint"""

    @pytest.mark.asyncio
    async def test_delete_document_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_document: Document,
        db_session: AsyncSession,
    ):
        """Test successful document deletion"""
        document_id = test_document.id

        response = await client.delete(
            f"/api/v1/documents/{document_id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify deletion in database
        result = await db_session.execute(
            select(Document).where(Document.id == document_id)
        )
        deleted_document = result.scalar_one_or_none()
        assert deleted_document is None

    @pytest.mark.asyncio
    async def test_delete_document_with_chunks(
        self,
        client: AsyncClient,
        auth_headers: dict,
        processed_document: Document,
        db_session: AsyncSession,
    ):
        """Test deleting document with associated chunks"""
        document_id = processed_document.id

        # Verify chunks exist
        result = await db_session.execute(
            select(Chunk).where(Chunk.document_id == document_id)
        )
        chunks_before = result.scalars().all()
        assert len(chunks_before) > 0

        response = await client.delete(
            f"/api/v1/documents/{document_id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify chunks were also deleted (cascade)
        result = await db_session.execute(
            select(Chunk).where(Chunk.document_id == document_id)
        )
        chunks_after = result.scalars().all()
        assert len(chunks_after) == 0

    @pytest.mark.asyncio
    async def test_delete_document_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test deleting non-existent document"""
        response = await client.delete(
            "/api/v1/documents/99999",
            headers=auth_headers,
        )

        assert response.status_code == 404


# Note: Additional tests for generate-categories endpoint would go here
# Skipped for brevity - similar pattern to above
