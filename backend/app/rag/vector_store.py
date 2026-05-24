from typing import Any
import chromadb
from chromadb.api import ClientAPI
import structlog

from app.config import settings

logger = structlog.get_logger()


class VectorStore:
    """Adapter class wrapping the ChromaDB client to manage document embeddings.

    Gracefully falls back to EphemeralClient if HTTP server is unreachable.
    """

    def __init__(self, client: ClientAPI | None = None) -> None:
        if client is not None:
            self.client = client
        else:
            try:
                self.client = chromadb.HttpClient(
                    host=settings.CHROMA_HOST,
                    port=str(settings.CHROMA_PORT),
                )
                # Test connectivity
                self.client.heartbeat()
            except Exception as e:
                logger.warning(
                    "Could not connect to ChromaDB HTTP Server. Falling back to EphemeralClient.",
                    error=str(e),
                )
                self.client = chromadb.EphemeralClient()

    def _get_collection(self, collection_name: str):
        """Retrieve or create a ChromaDB collection by name."""
        return self.client.get_or_create_collection(name=collection_name)

    def add(
        self,
        collection_name: str,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Add text chunks and corresponding embedding vectors to a collection."""
        collection = self._get_collection(collection_name)
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,  # type: ignore
        )

    def query(
        self,
        collection_name: str,
        query_embeddings: list[list[float]],
        n_results: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Query vector database for similar chunks."""
        collection = self._get_collection(collection_name)
        results = collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=where,  # type: ignore
        )

        parsed_results = []
        if not results or "ids" not in results or not results["ids"]:
            return parsed_results

        # ChromaDB queries return nested lists for multiple query vectors
        ids = results["ids"][0]
        distances = results.get("distances", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        documents = results.get("documents", [[]])[0]

        for idx in range(len(ids)):
            parsed_results.append(
                {
                    "id": ids[idx],
                    "distance": distances[idx] if idx < len(distances) else 0.0,
                    "metadata": metadatas[idx] if idx < len(metadatas) else {},
                    "document": documents[idx] if idx < len(documents) else "",
                }
            )

        return parsed_results

    def delete(
        self,
        collection_name: str,
        ids: list[str] | None = None,
        where: dict[str, Any] | None = None,
    ) -> None:
        """Delete entries from a collection by IDs or metadata filter."""
        collection = self._get_collection(collection_name)
        collection.delete(ids=ids, where=where)  # type: ignore
