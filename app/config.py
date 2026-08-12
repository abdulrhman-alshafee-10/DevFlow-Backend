"""
app/config.py
─────────────
Application configuration loaded from environment variables.

Uses pydantic-settings so every value is type-validated at startup.
If a required variable is missing, the app fails fast with a clear error
instead of crashing later at runtime.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central settings object.

    Values are read (in priority order) from:
      1. Environment variables
      2. .env file (only in development)
      3. Default values defined here

    Add new settings here — never scatter os.environ calls around the codebase.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # DATABASE_URL and database_url both work
        extra="ignore",        # Ignore unknown env vars instead of crashing
    )

    # ── Application ───────────────────────────────────────────────────────────
    APP_NAME: str = "DevFlow"
    APP_VERSION: str = "0.1.0"
    APP_DESCRIPTION: str = (
        "Team project and AI task management platform — DevFlow API"
    )
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False

    # ── Server ────────────────────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── Database ──────────────────────────────────────────────────────────────
    # Use asyncpg driver: postgresql+asyncpg://user:pass@host:port/dbname
    DATABASE_URL: str = "postgresql+asyncpg://devflow:devflow@localhost:5432/devflow"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30

    @property
    def sync_database_url(self) -> str:
        """
        Synchronous URL for Alembic migrations (uses psycopg2 style, not asyncpg).
        Alembic's env.py uses this when running migrations from the CLI.
        """
        return self.DATABASE_URL.replace(
            "postgresql+asyncpg://", "postgresql+psycopg2://"
        )

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Security & Authentication ─────────────────────────────────────────────
    # Generate a strong key with: openssl rand -hex 32
    JWT_SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Email / SMTP ──────────────────────────────────────────────────────────
    SMTP_TLS: bool = True
    SMTP_PORT: int = 587
    SMTP_HOST: str = "smtp.example.com"
    SMTP_USER: str = "user@example.com"
    SMTP_PASSWORD: str = "password"
    EMAILS_FROM_EMAIL: str = "noreply@example.com"
    EMAILS_FROM_NAME: str = "DevFlow"

    # ── Storage / MinIO ───────────────────────────────────────────────────────
    STORAGE_ENDPOINT: str = "http://localhost:9000"
    STORAGE_ACCESS_KEY: str = "minioadmin"
    STORAGE_SECRET_KEY: str = "minioadmin"
    STORAGE_BUCKET_NAME: str = "devflow-attachments"

    # ── AI & LLM ──────────────────────────────────────────────────────────────
    OLLAMA_BASE_URL: str = "https://api.ollama.com"
    OLLAMA_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    AI_RATE_LIMIT_PER_HOUR: int = 20

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Comma-separated list of allowed origins stored as a plain string so that
    # pydantic-settings can read it from .env without JSON parsing issues.
    # e.g.  ALLOWED_ORIGINS=http://localhost:3000,https://app.devflow.com
    ALLOWED_ORIGINS_STR: str = "http://localhost:3000,http://localhost:5173"

    @property
    def ALLOWED_ORIGINS(self) -> list[str]:  # noqa: N802
        """Return the comma-separated origins as a list."""
        return [o.strip() for o in self.ALLOWED_ORIGINS_STR.split(",") if o.strip()]

    # ── Convenience helpers ───────────────────────────────────────────────────
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def openapi_url(self) -> str | None:
        """Disable OpenAPI schema in production (served separately)."""
        return "/openapi.json" if not self.is_production else None

    @property
    def docs_url(self) -> str | None:
        """Disable Swagger UI in production."""
        return "/docs" if not self.is_production else None

    @property
    def redoc_url(self) -> str | None:
        """Disable ReDoc in production."""
        return "/redoc" if not self.is_production else None


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached Settings instance.

    Using @lru_cache means the .env file is parsed exactly once.
    In tests, call `get_settings.cache_clear()` after overriding env vars.
    """
    return Settings()
