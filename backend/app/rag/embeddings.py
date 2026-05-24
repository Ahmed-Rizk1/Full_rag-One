from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """Wrapper over sentence-transformers to generate vector embeddings locally."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self._model = None

    @property
    def model(self) -> SentenceTransformer:
        """Lazy load the model to speed up initialization."""
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_query(self, text: str) -> list[float]:
        """Generate a single embedding vector for a query string."""
        embedding = self.model.encode(text)
        return embedding.tolist()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generate a list of embedding vectors for multiple document strings."""
        embeddings = self.model.encode(texts)
        return embeddings.tolist()
