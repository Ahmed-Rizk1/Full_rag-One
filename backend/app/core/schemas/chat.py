import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ConversationResponse(BaseModel):
    id: uuid.UUID
    title: str
    agent_type: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationCreate(BaseModel):
    title: str
    agent_type: str = "general"


class MessageResponse(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    citations: list[dict] | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageCreate(BaseModel):
    content: str
