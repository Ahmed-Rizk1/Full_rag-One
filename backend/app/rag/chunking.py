from typing import Any


class Chunk:
    """Represents a single parsed text chunk from a document."""

    def __init__(self, content: str, index: int, metadata: dict[str, Any]) -> None:
        self.content = content
        self.index = index
        self.metadata = metadata

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "index": self.index,
            "metadata": self.metadata,
        }


class RecursiveChunker:
    """Sliding-window text chunker with word-boundary alignment."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(
        self, text: str, doc_metadata: dict[str, Any] | None = None
    ) -> list[Chunk]:
        """Split clean text into overlapping chunks with character offsets."""
        if not text:
            return []

        doc_meta = doc_metadata or {}
        chunks = []
        text_len = len(text)
        start = 0
        chunk_idx = 0

        while start < text_len:
            end = min(start + self.chunk_size, text_len)

            # Avoid splitting words in the middle: search backward for a separator
            if end < text_len:
                # Look back up to 50 characters for a whitespace or newline
                search_limit = max(start, end - 50)
                separator_index = -1
                for i in range(end - 1, search_limit - 1, -1):
                    if text[i] in (" ", "\n", "\t"):
                        separator_index = i
                        break
                if separator_index != -1:
                    end = separator_index + 1  # Include the space/newline in the current chunk

            chunk_content = text[start:end].strip()
            if chunk_content:
                meta = doc_meta.copy()
                meta.update(
                    {
                        "start_char": start,
                        "end_char": end,
                    }
                )
                chunks.append(
                    Chunk(
                        content=chunk_content,
                        index=chunk_idx,
                        metadata=meta,
                    )
                )
                chunk_idx += 1

            # Move start pointer forward, applying overlap
            next_start = end - self.chunk_overlap
            if next_start <= start:
                start = end
            else:
                start = next_start

        return chunks
