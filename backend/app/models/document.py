import uuid
from sqlalchemy import JSON, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Document(Base, UUIDMixin, TimestampMixin):
    """SQLAlchemy model representing an uploaded user document."""

    __tablename__ = "documents"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    content_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    storage_path: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        server_default="pending",
        nullable=False,
    )
    chunk_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )
    metadata_json: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # ORM Relationships
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class DocumentChunk(Base, UUIDMixin, TimestampMixin):
    """SQLAlchemy model representing a single split text chunk of a document."""

    __tablename__ = "document_chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    embedding_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    metadata_json: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # ORM Relationships
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="chunks",
    )
