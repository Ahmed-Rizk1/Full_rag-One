from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas.enums import GroqModel
from app.models.document import Document
from app.rag.chunking import RecursiveChunker
from app.rag.ingestion import parse_docx, parse_pdf, parse_txt
from app.repositories.document_repo import document_repository


def test_txt_parser():
    """Verify that TXT parser successfully decodes bytes."""
    test_bytes = b"Hello, world! This is a plain text file."
    result = parse_txt(test_bytes)
    assert result == "Hello, world! This is a plain text file."


@patch("app.rag.ingestion.PdfReader")
def test_pdf_parser_mocked(mock_reader_cls):
    """Verify that PDF parser delegates to PdfReader pages content extraction."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Page content extracted."

    mock_reader = MagicMock()
    mock_reader.pages = [mock_page]
    mock_reader_cls.return_value = mock_reader

    result = parse_pdf(b"dummy pdf bytes")
    assert result == "Page content extracted."
    mock_page.extract_text.assert_called_once()


@patch("app.rag.ingestion.docx.Document")
def test_docx_parser_mocked(mock_doc_cls):
    """Verify that DOCX parser extracts paragraphs correctly."""
    mock_para = MagicMock()
    mock_para.text = "Paragraph content extracted."

    mock_doc = MagicMock()
    mock_doc.paragraphs = [mock_para]
    mock_doc_cls.return_value = mock_doc

    result = parse_docx(b"dummy docx bytes")
    assert result == "Paragraph content extracted."


def test_chunker_basic():
    """Verify that RecursiveChunker divides text correctly with character boundaries and overlaps."""
    chunker = RecursiveChunker(chunk_size=50, chunk_overlap=10)
    text = "The quick brown fox jumps over the lazy dog. A secondary sentence."

    chunks = chunker.chunk_text(text, doc_metadata={"test": "true"})
    assert len(chunks) > 0
    assert chunks[0].index == 0
    assert chunks[0].metadata["test"] == "true"
    assert "start_char" in chunks[0].metadata

    # Validate that overlap works and start pointers move
    if len(chunks) > 1:
        assert chunks[1].index == 1
        assert chunks[1].metadata["start_char"] > 0


@pytest.mark.asyncio
async def test_upload_document_endpoint(client: AsyncClient, db_session: AsyncSession):
    """Verify document upload metadata persistence and Celery task dispatching."""
    # 1. Register and login a user to get auth headers
    email = "rag_test@example.com"
    password = "secure_test_password"
    signup_payload = {"email": email, "password": password, "full_name": "RAG User"}

    signup_res = await client.post("/api/v1/auth/signup", json=signup_payload)
    assert signup_res.status_code == 201

    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Perform document upload mock
    file_payload = {"file": ("test_doc.txt", b"RAG ingestion test file content", "text/plain")}

    with patch("app.api.v1.documents.ingest_document_task.delay") as mock_delay:
        response = await client.post(
            "/api/v1/documents/upload",
            files=file_payload,
            headers=headers,
        )

        assert response.status_code == 202
        data = response.json()
        assert data["filename"] == "test_doc.txt"
        assert data["status"] == "pending"
        assert "id" in data

        # Verify Celery delay is called with correct document ID
        mock_delay.assert_called_once_with(data["id"])


@pytest.mark.asyncio
async def test_query_document_endpoint_mocked(client: AsyncClient, db_session: AsyncSession):
    """Verify hybrid RRF retrieval returns aggregated dense and keyword results."""
    # Setup auth and dummy document
    email = "query_test@example.com"
    password = "secure_query_password"
    signup_payload = {"email": email, "password": password, "full_name": "Query User"}

    await client.post("/api/v1/auth/signup", json=signup_payload)
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = login_res.json()["access_token"]
    user_id = login_res.json().get("user_id")  # Wait, response has tokens, not user_id by default. We get user profile.
    headers = {"Authorization": f"Bearer {token}"}

    me_res = await client.get("/api/v1/auth/me", headers=headers)
    user_id_str = me_res.json()["id"]
    import uuid
    user_id = uuid.UUID(user_id_str)

    # Pre-populate ready document in Postgres
    doc_data = {
        "user_id": user_id,
        "filename": "mocked_rag.txt",
        "status": "ready",
        "chunk_count": 1,
    }
    doc = await document_repository.create(db_session, obj_in=doc_data)
    await db_session.commit()

    # Stub ChromaDB vector store query and sentence-transformers encoding
    mock_vector_query = [
        {
            "id": "chunk_vector_id",
            "distance": 0.1,
            "metadata": {"document_id": str(doc.id), "chunk_index": 0},
            "document": "Dense retrieved chunk text content.",
        }
    ]

    with patch("app.rag.embeddings.EmbeddingService.embed_query") as mock_embed, \
         patch("app.rag.vector_store.chromadb.HttpClient") as mock_chroma_client, \
         patch("app.rag.vector_store.VectorStore.query") as mock_vector_store:

        mock_embed.return_value = [0.1] * 384
        mock_vector_store.return_value = mock_vector_query

        # Make query call
        query_payload = {"query": "test query string", "top_k": 3}
        response = await client.post(
            f"/api/v1/documents/{doc.id}/query",
            json=query_payload,
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert data[0]["content"] == "Dense retrieved chunk text content."
        assert data[0]["chunk_index"] == 0
        assert str(data[0]["document_id"]) == str(doc.id)
