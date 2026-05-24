from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

from sqlalchemy.pool import NullPool

# Create async database engine
# Using echo=True/False depending on environment if needed, but defaults to False
engine = create_async_engine(
    settings.POSTGRES_ASYNC_URI,
    future=True,
    poolclass=NullPool,
)

# Async session factory
SessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for obtaining an asynchronous database session.

    Ensures that sessions are rolled back on error and always closed.
    """
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
