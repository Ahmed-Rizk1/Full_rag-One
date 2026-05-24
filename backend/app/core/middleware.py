import time
import structlog
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from redis.asyncio import Redis, from_url
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

logger = structlog.get_logger()


def setup_logging() -> None:
    """Initialize structlog with a production-ready JSON renderer config."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.format_exc_info,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request/response logging using structlog."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            method=request.method,
            path=request.url.path,
            ip=request.client.host if request.client else None,
        )

        try:
            response = await call_next(request)
            duration = time.perf_counter() - start_time
            logger.info(
                "Request completed",
                status_code=response.status_code,
                duration_seconds=round(duration, 4),
            )
            return response
        except Exception as e:
            duration = time.perf_counter() - start_time
            logger.error(
                "Request exception occurred",
                error=str(e),
                duration_seconds=round(duration, 4),
            )
            raise e


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis-backed sliding window rate limiter (60 requests/minute default)."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.redis: Redis | None = None

    async def _get_redis(self) -> Redis:
        if self.redis is None:
            self.redis = from_url(settings.REDIS_URL)
        return self.redis

    async def dispatch(self, request: Request, call_next) -> Response:
        # Bypass rate limits for health checks
        if request.url.path.endswith("/health"):
            return await call_next(request)

        # Rate limit based on IP address
        ip = request.client.host if request.client else "unknown"
        key = f"rate:{ip}"

        try:
            redis_client = await self._get_redis()
            current_time = time.time()
            window_start = current_time - 60

            # Transactional pipeline for sliding window counting
            async with redis_client.pipeline(transaction=True) as pipe:
                pipe.zremrangebyscore(key, 0, window_start)
                pipe.zcard(key)
                pipe.zadd(key, {str(current_time): current_time})
                pipe.expire(key, 60)
                _, request_count, _, _ = await pipe.execute()

            if request_count > self.requests_per_minute:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Too many requests. Please try again later."},
                )

        except Exception as e:
            # Gracefully bypass rate limiter if Redis is offline
            logger.warning("Rate limiter connection error, bypassing limit", error=str(e))

        return await call_next(request)
