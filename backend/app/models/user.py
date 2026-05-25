from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    """User ORM model representing the 'users' database table."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    full_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    role: Mapped[str] = mapped_column(
        String(50),
        default="user",
        server_default="user",
        nullable=False,
    )
    is_verified: Mapped[bool] = mapped_column(
        default=False,
        server_default="false",
        nullable=False,
    )
    verification_token: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    openai_api_key: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    groq_api_key: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    preferred_provider: Mapped[str | None] = mapped_column(
        String(50),
        default="groq",
        server_default="groq",
        nullable=True,
    )

