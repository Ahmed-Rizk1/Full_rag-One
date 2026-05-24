import uuid
from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Conversation(Base, UUIDMixin, TimestampMixin):
    """SQLAlchemy model representing a user chat session."""

    __tablename__ = "conversations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    agent_type: Mapped[str] = mapped_column(
        String(50),
        default="general",
        server_default="general",
        nullable=False,
    )

    # ORM Relationships
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Message(Base, UUIDMixin, TimestampMixin):
    """SQLAlchemy model representing an individual message in a conversation."""

    __tablename__ = "messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # "user" | "assistant" | "system" | "tool"
    content: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    citations: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )
    tool_calls: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # ORM Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="messages",
    )
