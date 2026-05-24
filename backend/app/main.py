from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.config import settings
from app.core.events import lifespan
from app.core.exceptions import AppError
from app.core.middleware import LoggingMiddleware, RateLimitMiddleware


def create_app() -> FastAPI:
    """App factory that builds and configures the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan,
    )

    # Configure CORS
    # In production, this should list specific allowed origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add custom middlewares (outermost to innermost execution)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=60)
    app.add_middleware(LoggingMiddleware)

    # Include root API router
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # Register global handler for application-specific exceptions
    @app.exception_handler(AppError)
    async def app_error_handler(request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    return app


app = create_app()
