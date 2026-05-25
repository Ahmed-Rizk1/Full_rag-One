import asyncio
import logging
from typing import Any, AsyncGenerator, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.agents.orchestrator import AgentOrchestrator
from app.db.session import SessionLocal
from app.models.conversation import Conversation, Message
from app.repositories.conversation_repo import (
    conversation_repository,
    message_repository,
)

logger = structlog.get_logger()


class ChatService:
    """Service coordinating conversation CRUD operations and multi-agent orchestrator streaming execution."""

    def __init__(self, orchestrator: AgentOrchestrator) -> None:
        self.orchestrator = orchestrator

    async def get_or_create_conversation(
        self,
        db: AsyncSession,
        user_id: Any,
        title: str,
        agent_type: str = "general",
    ) -> Conversation:
        """Create a new chat conversation."""
        doc = {
            "user_id": user_id,
            "title": title,
            "agent_type": agent_type,
        }
        return await conversation_repository.create(db, obj_in=doc)

    async def list_conversations(
        self, db: AsyncSession, user_id: Any, skip: int = 0, limit: int = 100
    ) -> Sequence[Conversation]:
        """List conversations belonging to the user."""
        return await conversation_repository.get_by_user(
            db, user_id=user_id, skip=skip, limit=limit
        )

    async def get_conversation(
        self, db: AsyncSession, conversation_id: Any
    ) -> Conversation | None:
        """Retrieve a specific conversation metadata record."""
        return await conversation_repository.get(db, id=conversation_id)

    async def delete_conversation(
        self, db: AsyncSession, conversation_id: Any
    ) -> Conversation | None:
        """Delete a conversation and all its messages."""
        return await conversation_repository.delete(db, id=conversation_id)

    async def get_messages(
        self, db: AsyncSession, conversation_id: Any
    ) -> Sequence[Message]:
        """Fetch all messages in a conversation chronologically."""
        return await message_repository.get_by_conversation(
            db, conversation_id=conversation_id
        )

    async def execute_chat_stream(
        self,
        db: AsyncSession,
        conversation_id: Any,
        user_id: Any,
        content: str,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Execute the multi-agent graph in a background task, streaming tokens through a queue."""
        # 1. Fetch conversation
        conv = await conversation_repository.get(db, id=conversation_id)
        if not conv or conv.user_id != user_id:
            raise ValueError("Conversation not found.")

        # 1a. Fetch user to retrieve their API keys
        from app.repositories.user_repo import user_repository
        from app.core.exceptions import ValidationError
        from app.config import settings

        user = await user_repository.get(db, id=user_id)
        if not user:
            raise ValidationError(detail="User not found.")

        provider = user.preferred_provider or "groq"
        api_key = user.openai_api_key if provider == "openai" else user.groq_api_key

        # Validate that the key exists (allow bypass for testing environment)
        if not api_key and settings.ENVIRONMENT != "testing":
            raise ValidationError(
                detail=f"Please configure your {provider.upper()} API key in settings before starting a conversation."
            )


        # 2. Persist user message to database
        user_msg_data = {
            "conversation_id": conversation_id,
            "role": "user",
            "content": content,
            "citations": None,
            "tool_calls": None,
        }
        await message_repository.create(db, obj_in=user_msg_data)
        await db.commit()

        # 3. Retrieve conversation history
        history = await message_repository.get_by_conversation(
            db, conversation_id=conversation_id
        )

        messages_state = []
        for msg in history:
            messages_state.append({"role": msg.role, "content": msg.content})

        # 4. Setup asynchronous queue for streaming token events from graph nodes
        queue: asyncio.Queue = asyncio.Queue()

        initial_state = {
            "messages": messages_state,
            "user_id": str(user_id),
            "conversation_id": str(conversation_id),
            "agent_type": conv.agent_type,
            "context": [],
            "citations": [],
            "tool_results": [],
            "db": db,
            "queue": queue,
            "api_key": api_key,
            "provider": provider,
        }


        # 5. Run the LangGraph orchestration in a separate asyncio Task
        async def run_graph():
            try:
                final_state = await self.orchestrator.graph.ainvoke(initial_state)

                # Extract the assistant's final response content
                messages = final_state.get("messages", [])
                assistant_text = ""
                for msg in reversed(messages):
                    if msg.get("role") == "assistant":
                        assistant_text = msg.get("content", "")
                        break

                citations = final_state.get("citations", [])
                await queue.put({"type": "citations", "citations": citations})

                # Persist the complete response to database
                assistant_msg_data = {
                    "conversation_id": conversation_id,
                    "role": "assistant",
                    "content": assistant_text,
                    "citations": citations,
                    "tool_calls": None,
                }
                await message_repository.create(db, obj_in=assistant_msg_data)
                await db.commit()

            except Exception as e:
                logger.exception("Error executing agent orchestrator graph", error=str(e))
                await queue.put({"type": "error", "content": f"Execution error: {str(e)}"})
            finally:
                # Signal the queue reader that the stream is finished
                await queue.put({"type": "done"})

        # Fire and forget graph run in background
        asyncio.create_task(run_graph())

        # 6. Yield tokens and metadata from the queue as they arrive
        while True:
            item = await queue.get()
            if item.get("type") == "done":
                break
            yield item
