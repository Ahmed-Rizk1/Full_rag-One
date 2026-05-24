import asyncio
import logging
import os
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import SessionLocal
from app.models.document import Document
from app.repositories.document_repo import (
    document_chunk_repository,
    document_repository,
)
from app.rag.chunking import RecursiveChunker
from app.rag.embeddings import EmbeddingService
from app.rag.ingestion import parse_docx, parse_pdf, parse_txt
from app.rag.vector_store import VectorStore
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.ingestion_tasks.ingest_document_task")
def ingest_document_task(document_id: str) -> str:
    """Synchronous Celery task wrapper that runs the asynchronous ingestion pipeline."""
    doc_uuid = uuid.UUID(document_id)
    return asyncio.run(async_ingest_document(doc_uuid))


async def async_ingest_document(doc_id: uuid.UUID) -> str:
    """Asynchronous ingestion pipeline."""
    async with SessionLocal() as db:
        # 1. Fetch document metadata
        doc = await document_repository.get(db, id=doc_id)
        if not doc:
            error_msg = f"Document with ID {doc_id} not found."
            logger.error(error_msg)
            raise ValueError(error_msg)

        # 2. Update status to processing
        doc.status = "processing"
        await db.commit()

        try:
            # 3. Read raw bytes from local disk
            if not doc.storage_path or not os.path.exists(doc.storage_path):
                raise FileNotFoundError(f"Storage path {doc.storage_path} does not exist.")

            with open(doc.storage_path, "rb") as f:
                file_bytes = f.read()

            # 4. Parse content based on file extension
            filename_lower = doc.filename.lower()
            if filename_lower.endswith(".pdf"):
                text = parse_pdf(file_bytes)
            elif filename_lower.endswith((".docx", ".doc")):
                text = parse_docx(file_bytes)
            else:
                text = parse_txt(file_bytes)

            # 5. Segment parsed text into chunks
            chunker = RecursiveChunker()
            chunks = chunker.chunk_text(
                text=text,
                doc_metadata={
                    "document_id": str(doc.id),
                    "user_id": str(doc.user_id),
                    "filename": doc.filename,
                },
            )

            if not chunks:
                doc.status = "ready"
                doc.chunk_count = 0
                await db.commit()
                return "Processed empty file successfully."

            # 6. Generate embedding vectors locally
            embedding_service = EmbeddingService()
            texts = [c.content for c in chunks]
            embeddings = embedding_service.embed_documents(texts)

            # 7. Add vectors and text to ChromaDB store
            vector_store = VectorStore()
            vector_ids = [str(uuid.uuid4()) for _ in chunks]
            metadatas = [c.metadata for c in chunks]

            vector_store.add(
                collection_name="document_chunks",
                ids=vector_ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )

            # 8. Save chunks in PostgreSQL
            for idx, c in enumerate(chunks):
                chunk_data = {
                    "document_id": doc.id,
                    "chunk_index": c.index,
                    "content": c.content,
                    "embedding_id": vector_ids[idx],
                    "metadata_json": c.metadata,
                }
                await document_chunk_repository.create(db, obj_in=chunk_data)

            # 9. Update document metadata to ready
            doc.status = "ready"
            doc.chunk_count = len(chunks)
            await db.commit()

            return f"Ingested {len(chunks)} chunks successfully."

        except Exception as e:
            # Update status to failed
            doc.status = "failed"
            await db.commit()
            logger.exception(f"Ingestion failed for document {doc_id}")
            raise e
