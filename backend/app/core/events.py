from contextlib import asynccontextmanager
from fastapi import FastAPI
import structlog
from sqlalchemy import text

from app.core.middleware import setup_logging
from app.db.session import SessionLocal, engine

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event manager for FastAPI application startup and shutdown."""
    # 1. Startup Logic
    setup_logging()
    logger.info("Starting up AI Workspace OS backend services")

    try:
        # Warm-up / Validate DB connection
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
        logger.info("Database connection validated successfully")
    except Exception as e:
        logger.error(
            "Failed to establish database connection during startup",
            error=str(e),
        )

    yield

    # 2. Shutdown Logic
    logger.info("Shutting down AI Workspace OS backend services")
    try:
        await engine.dispose()
        logger.info("Database connection pool closed successfully")
    except Exception as e:
        logger.error(
            "Error disposing database connection pool during shutdown",
            error=str(e),
        )
