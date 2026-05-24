import os
import shutil
import uuid
from typing import Sequence
from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.core.exceptions import NotFoundError
from app.core.schemas.document import (
    DocumentResponse,
    QueryRequest,
    RetrievedChunkResponse,
)
from app.models.user import User
from app.repositories.document_repo import document_repository
from app.rag.embeddings import EmbeddingService
from app.rag.retriever import HybridRetriever
from app.rag.vector_store import VectorStore
from app.workers.ingestion_tasks import ingest_document_task

router = APIRouter(prefix="/documents", tags=["documents"])

STORAGE_DIR = "storage"
os.makedirs(STORAGE_DIR, exist_ok=True)


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a document file, persist metadata, and trigger asynchronous parsing/embedding ingestion."""
    filename = file.filename or "unnamed_document"
    doc_id = uuid.uuid4()
    ext = os.path.splitext(filename)[1]
    storage_path = os.path.join(STORAGE_DIR, f"{doc_id}{ext}")

    # Save raw file bytes to local disk
    with open(storage_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Persist pending metadata record
    doc_data = {
        "id": doc_id,
        "user_id": current_user.id,
        "filename": filename,
        "content_type": file.content_type,
        "storage_path": storage_path,
        "status": "pending",
        "chunk_count": 0,
    }

    doc = await document_repository.create(db, obj_in=doc_data)
    await db.commit()

    # Dispatch Celery background task for ingestion pipeline execution
    ingest_document_task.delay(str(doc.id))

    return doc


@router.get(
    "",
    response_model=list[DocumentResponse],
    status_code=status.HTTP_200_OK,
)
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all uploaded documents belonging to the authenticated user."""
    return await document_repository.get_by_user(
        db, user_id=current_user.id, skip=skip, limit=limit
    )


@router.get(
    "/{id}",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
)
async def get_document_status(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve details and processing status of a specific document."""
    doc = await document_repository.get(db, id=id)
    if not doc or doc.user_id != current_user.id:
        raise NotFoundError("The requested document was not found.")
    return doc


@router.post(
    "/{id}/query",
    response_model=list[RetrievedChunkResponse],
    status_code=status.HTTP_200_OK,
)
async def query_document(
    id: uuid.UUID,
    query_in: QueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Perform hybrid vector/keyword search over chunks of a specific document."""
    doc = await document_repository.get(db, id=id)
    if not doc or doc.user_id != current_user.id:
        raise NotFoundError("The requested document was not found.")

    if doc.status != "ready":
        return []

    # Initialize RAG Pipeline components
    embedding_service = EmbeddingService()
    vector_store = VectorStore()
    retriever = HybridRetriever(
        embedding_service=embedding_service,
        vector_store=vector_store,
    )

    # Perform retrieval filtered by current user and specific document
    results = await retriever.retrieve(
        db=db,
        query_str=query_in.query,
        user_id=current_user.id,
        top_k=query_in.top_k,
        document_id=doc.id,
    )

    return [r.to_dict() for r in results]
