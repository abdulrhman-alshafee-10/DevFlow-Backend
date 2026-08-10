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
