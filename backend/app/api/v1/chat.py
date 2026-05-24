import json
import uuid
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.core.exceptions import NotFoundError
from app.core.schemas.chat import (
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
)
from app.models.user import User
from app.rag.embeddings import EmbeddingService
from app.rag.retriever import HybridRetriever
from app.rag.vector_store import VectorStore
from app.services.chat_service import ChatService
from app.agents.orchestrator import AgentOrchestrator
from app.services.llm_client import LLMClient

router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize singletons for Chat execution
llm_client = LLMClient()
embedding_service = EmbeddingService()
vector_store = VectorStore()
retriever = HybridRetriever(embedding_service, vector_store)
orchestrator = AgentOrchestrator(llm_client, retriever)
chat_service = ChatService(orchestrator)


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    conv_in: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new conversation session."""
    return await chat_service.get_or_create_conversation(
        db=db,
        user_id=current_user.id,
        title=conv_in.title,
        agent_type=conv_in.agent_type,
    )


@router.get(
    "/conversations",
    response_model=list[ConversationResponse],
    status_code=status.HTTP_200_OK,
)
async def list_conversations(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all conversation sessions belonging to the authenticated user."""
    return await chat_service.list_conversations(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )


@router.get(
    "/conversations/{id}",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
)
async def get_conversation(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve details of a specific conversation metadata record."""
    conv = await chat_service.get_conversation(db=db, conversation_id=id)
    if not conv or conv.user_id != current_user.id:
        raise NotFoundError("The requested conversation session was not found.")
    return conv


@router.delete(
    "/conversations/{id}",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_conversation(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a conversation session and all its messages."""
    conv = await chat_service.get_conversation(db=db, conversation_id=id)
    if not conv or conv.user_id != current_user.id:
        raise NotFoundError("The requested conversation session was not found.")
    return await chat_service.delete_conversation(db=db, conversation_id=id)


@router.get(
    "/conversations/{id}/messages",
    response_model=list[MessageResponse],
    status_code=status.HTTP_200_OK,
)
async def list_messages(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve chronological messages history of a specific conversation."""
    conv = await chat_service.get_conversation(db=db, conversation_id=id)
    if not conv or conv.user_id != current_user.id:
        raise NotFoundError("The requested conversation session was not found.")
    return await chat_service.get_messages(db=db, conversation_id=id)


@router.post(
    "/conversations/{id}/messages",
    status_code=status.HTTP_200_OK,
)
async def send_message(
    id: uuid.UUID,
    msg_in: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a message to a conversation and return an SSE stream yielding response tokens."""
    conv = await chat_service.get_conversation(db=db, conversation_id=id)
    if not conv or conv.user_id != current_user.id:
        raise NotFoundError("The requested conversation session was not found.")

    async def sse_generator():
        try:
            async for item in chat_service.execute_chat_stream(
                db=db,
                conversation_id=id,
                user_id=current_user.id,
                content=msg_in.content,
            ):
                event_type = item.get("type", "token")
                # Format: event: <event_type>\ndata: <json_data>\n\n
                if event_type == "token":
                    data = {"content": item.get("content", ""), "type": "token"}
                elif event_type == "citations":
                    data = {"citations": item.get("citations", []), "type": "citations"}
                elif event_type == "error":
                    data = {"detail": item.get("content", ""), "type": "error"}
                else:
                    data = item
                yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
            yield f"event: done\ndata: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'detail': str(e), 'type': 'error'})}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")
