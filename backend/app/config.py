from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "AI Workspace OS"
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "temporary_secret_key_for_development_change_in_production"
    POSTGRES_ASYNC_URI: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_workspace_os"
    REDIS_URL: str = "redis://localhost:6379/0"
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000
    GROQ_API_KEY: str = ""


settings = Settings()
