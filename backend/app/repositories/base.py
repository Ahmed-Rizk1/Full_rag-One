from typing import Any, Generic, Sequence, Type, TypeVar
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic repository providing asynchronous CRUD operations for SQLAlchemy models."""

    def __init__(self, model: Type[ModelType]) -> None:
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> ModelType | None:
        """Retrieve a single record by primary key ID."""
        return await db.get(self.model, id)

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> Sequence[ModelType]:
        """Retrieve multiple records with pagination."""
        query = select(self.model).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: dict[str, Any] | Any) -> ModelType:
        """Create a new record."""
        if isinstance(obj_in, dict):
            db_obj = self.model(**obj_in)
        else:
            # Handle Pydantic schema or other object inputs dynamically
            if hasattr(obj_in, "model_dump"):
                obj_in_data = obj_in.model_dump()
            elif hasattr(obj_in, "dict"):
                obj_in_data = obj_in.dict()
            else:
                obj_in_data = {
                    k: v for k, v in obj_in.__dict__.items() if not k.startswith("_")
                }
            db_obj = self.model(**obj_in_data)

        db.add(db_obj)
        await db.flush()
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: ModelType, obj_in: dict[str, Any] | Any
    ) -> ModelType:
        """Update an existing record."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            # Handle Pydantic schema or other object inputs dynamically
            if hasattr(obj_in, "model_dump"):
                update_data = obj_in.model_dump(exclude_unset=True)
            elif hasattr(obj_in, "dict"):
                update_data = obj_in.dict(exclude_unset=True)
            else:
                update_data = {
                    k: v for k, v in obj_in.__dict__.items() if not k.startswith("_")
                }

        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])

        db.add(db_obj)
        await db.flush()
        return db_obj

    async def delete(self, db: AsyncSession, id: Any) -> ModelType | None:
        """Delete a record by ID."""
        db_obj = await db.get(self.model, id)
        if db_obj:
            await db.delete(db_obj)
            await db.flush()
        return db_obj
