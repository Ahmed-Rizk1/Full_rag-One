from typing import Any, Sequence
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentChunk
from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import VectorStore


class RetrievedChunk:
    """Represents a retrieved document chunk with similarity scores and source metadata."""

    def __init__(
        self,
        content: str,
        score: float,
        document_id: str,
        chunk_index: int,
        metadata: dict[str, Any],
    ) -> None:
        self.content = content
        self.score = score
        self.document_id = document_id
        self.chunk_index = chunk_index
        self.metadata = metadata

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "score": self.score,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "metadata": self.metadata,
        }


class HybridRetriever:
    """Combines dense vector search and keyword relational database search using Reciprocal Rank Fusion (RRF)."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        k: int = 60,
    ) -> None:
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.k = k  # Constant factor for RRF calculation (standard = 60)

    async def _keyword_retrieve(
        self,
        db: AsyncSession,
        query_str: str,
        user_id: Any,
        limit: int = 10,
        document_id: Any | None = None,
    ) -> Sequence[DocumentChunk]:
        """Perform database search for matching terms in chunk content."""
        if db.bind is not None and db.bind.dialect.name == "postgresql":
            # PostgreSQL Full-Text Search
            conditions = [
                Document.user_id == user_id,
                func.to_tsvector("english", DocumentChunk.content).op("@@")(
                    func.plainto_tsquery("english", query_str)
                ),
            ]
            if document_id is not None:
                conditions.append(DocumentChunk.document_id == document_id)
            stmt = (
                select(DocumentChunk)
                .join(Document)
                .where(and_(*conditions))
                .limit(limit)
            )
        else:
            # Fallback for SQLite and other backends (ILike search)
            conditions = [
                Document.user_id == user_id,
                DocumentChunk.content.ilike(f"%{query_str}%"),
            ]
            if document_id is not None:
                conditions.append(DocumentChunk.document_id == document_id)
            stmt = (
                select(DocumentChunk)
                .join(Document)
                .where(and_(*conditions))
                .limit(limit)
            )

        result = await db.execute(stmt)
        return result.scalars().all()

    async def retrieve(
        self,
        db: AsyncSession,
        query_str: str,
        user_id: Any,
        top_k: int = 5,
        document_id: Any | None = None,
    ) -> list[RetrievedChunk]:
        """Query both vector database and relational database, fusioning ranks via RRF."""
        # 1. Dense (Vector) Retrieval
        query_emb = self.embedding_service.embed_query(query_str)
        # Filter vector search by user_id to enforce security boundaries
        where_filter: dict[str, Any] = {"user_id": str(user_id)}
        if document_id is not None:
            where_filter["document_id"] = str(document_id)

        dense_results = self.vector_store.query(
            collection_name="document_chunks",
            query_embeddings=[query_emb],
            n_results=top_k * 2,  # Retrieve more than top_k for fusion
            where=where_filter,
        )

        # 2. Keyword Retrieval
        keyword_results = await self._keyword_retrieve(
            db, query_str, user_id, limit=top_k * 2, document_id=document_id
        )

        # 3. Reciprocal Rank Fusion (RRF)
        # Store scores as: dict[key, float] where key is a unique (document_id, chunk_index) tuple
        rrf_scores: dict[tuple[str, int], float] = {}
        # Keep track of item payloads
        chunk_map: dict[tuple[str, int], dict[str, Any]] = {}

        # Parse Dense Rank (1-indexed)
        for rank, item in enumerate(dense_results, start=1):
            metadata = item["metadata"]
            doc_id = str(metadata.get("document_id", ""))
            chunk_idx = int(metadata.get("chunk_index", 0))
            if not doc_id:
                continue

            key = (doc_id, chunk_idx)
            rrf_scores[key] = rrf_scores.get(key, 0.0) + (1.0 / (self.k + rank))
            chunk_map[key] = {
                "content": item["document"],
                "metadata": metadata,
            }

        # Parse Keyword Rank (1-indexed)
        for rank, chunk in enumerate(keyword_results, start=1):
            doc_id = str(chunk.document_id)
            chunk_idx = int(chunk.chunk_index)

            key = (doc_id, chunk_idx)
            rrf_scores[key] = rrf_scores.get(key, 0.0) + (1.0 / (self.k + rank))
            if key not in chunk_map:
                chunk_map[key] = {
                    "content": chunk.content,
                    "metadata": {
                        "document_id": doc_id,
                        "chunk_index": chunk_idx,
                        "filename": getattr(chunk, "filename", ""),
                    },
                }

        # Sort by RRF score descending
        sorted_keys = sorted(rrf_scores.keys(), key=lambda k: rrf_scores[k], reverse=True)

        retrieved_chunks = []
        for key in sorted_keys[:top_k]:
            doc_id, chunk_idx = key
            score = rrf_scores[key]
            item_data = chunk_map[key]
            retrieved_chunks.append(
                RetrievedChunk(
                    content=item_data["content"],
                    score=score,
                    document_id=doc_id,
                    chunk_index=chunk_idx,
                    metadata=item_data["metadata"],
                )
            )

        return retrieved_chunks
