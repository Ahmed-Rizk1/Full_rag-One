from typing import Any, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memory import Memory
from app.repositories.base import BaseRepository


class MemoryRepository(BaseRepository[Memory]):
    async def get_by_user(
        self, db: AsyncSession, *, user_id: Any, skip: int = 0, limit: int = 100
    ) -> Sequence[Memory]:
        result = await db.execute(
            select(Memory)
            .where(Memory.user_id == user_id)
            .order_by(Memory.importance_score.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


memory_repository = MemoryRepository(Memory)
