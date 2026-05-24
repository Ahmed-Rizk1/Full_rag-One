from typing import Any, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, Message
from app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    """Repository handling data access logic for Conversation model."""

    def __init__(self) -> None:
        super().__init__(Conversation)

    async def get_by_user(
        self, db: AsyncSession, user_id: Any, skip: int = 0, limit: int = 100
    ) -> Sequence[Conversation]:
        """Retrieve all conversations belonging to a specific user with pagination."""
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(Conversation.created_at.desc())
        )
        result = await db.execute(stmt)
        return result.scalars().all()


class MessageRepository(BaseRepository[Message]):
    """Repository handling data access logic for Message model."""

    def __init__(self) -> None:
        super().__init__(Message)

    async def get_by_conversation(
        self, db: AsyncSession, conversation_id: Any
    ) -> Sequence[Message]:
        """Retrieve all messages in a conversation ordered chronologically."""
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        result = await db.execute(stmt)
        return result.scalars().all()


conversation_repository = ConversationRepository()
message_repository = MessageRepository()
