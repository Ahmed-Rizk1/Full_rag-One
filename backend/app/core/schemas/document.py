import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    id: uuid.UUID
    filename: str
    content_type: str | None
    status: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5


class RetrievedChunkResponse(BaseModel):
    content: str
    score: float
    document_id: uuid.UUID
    chunk_index: int
    metadata: dict

    model_config = ConfigDict(from_attributes=True)
