from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for handling database operations for the User model."""

    def __init__(self) -> None:
        super().__init__(User)

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        """Retrieve a user by their email address."""
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        return result.scalar_one_or_none()


user_repository = UserRepository()
