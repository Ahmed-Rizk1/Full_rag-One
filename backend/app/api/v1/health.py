from fastapi import APIRouter, Depends, status
import httpx
from redis.asyncio import from_url
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", status_code=status.HTTP_200_OK)
async def check_health(db: AsyncSession = Depends(get_db)):
    """Health check endpoint to verify status of external dependencies."""
    postgres_status = False
    redis_status = False
    chroma_status = False

    # 1. Verify PostgreSQL
    try:
        await db.execute(text("SELECT 1"))
        postgres_status = True
    except Exception:
        pass

    # 2. Verify Redis
    try:
        redis_client = from_url(settings.REDIS_URL)
        await redis_client.ping()
        await redis_client.close()
        redis_status = True
    except Exception:
        pass

    # 3. Verify ChromaDB
    try:
        chroma_url = f"http://{settings.CHROMA_HOST}:{settings.CHROMA_PORT}/api/v1/heartbeat"
        async with httpx.AsyncClient() as client:
            response = await client.get(chroma_url, timeout=2.0)
            if response.status_code == 200:
                chroma_status = True
    except Exception:
        pass

    # Overall system health flag
    all_healthy = postgres_status and redis_status and chroma_status
    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "healthy" if all_healthy else "degraded",
        "services": {
            "postgres": postgres_status,
            "redis": redis_status,
            "chromadb": chroma_status,
        },
    }
