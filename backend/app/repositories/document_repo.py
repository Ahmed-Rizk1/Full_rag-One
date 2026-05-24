from typing import Any, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentChunk
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    """Repository handling data access logic for Document model."""

    def __init__(self) -> None:
        super().__init__(Document)

    async def get_by_user(
        self, db: AsyncSession, user_id: Any, skip: int = 0, limit: int = 100
    ) -> Sequence[Document]:
        """Retrieve all documents belonging to a specific user with pagination."""
        stmt = (
            select(Document)
            .where(Document.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(Document.created_at.desc())
        )
        result = await db.execute(stmt)
        return result.scalars().all()


class DocumentChunkRepository(BaseRepository[DocumentChunk]):
    """Repository handling data access logic for DocumentChunk model."""

    def __init__(self) -> None:
        super().__init__(DocumentChunk)

    async def get_by_document(
        self, db: AsyncSession, document_id: Any
    ) -> Sequence[DocumentChunk]:
        """Retrieve all text chunks associated with a specific document ordered by index."""
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc())
        )
        result = await db.execute(stmt)
        return result.scalars().all()


document_repository = DocumentRepository()
document_chunk_repository = DocumentChunkRepository()
