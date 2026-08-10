"""
tests/conftest.py
─────────────────
Shared pytest fixtures available to all tests.

Phase 1 fixtures:
  - app         → configured FastAPI application instance (test settings)
  - client      → async httpx test client

Phase 2+ will add:
  - db_session  → async database session (rolls back after each test)
  - redis_client → test Redis client (flushed before each test)
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.config import Settings, get_settings
from app.main import create_app


# ── Test settings ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """
    Override production settings for the test suite.

    Using a dedicated Settings object (not reading from .env) keeps tests
    hermetically isolated from the developer's local environment.
    """
    return Settings(
        APP_NAME="DevFlow-Test",
        ENVIRONMENT="development",
        DEBUG=True,
        ALLOWED_ORIGINS_STR="http://testclient",
    )


# ── App fixture ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_app(test_settings: Settings):
    """
    Create a FastAPI app instance configured for testing.

    Scope=session means the app is created once for all tests —
    faster than creating it per-test.
    """
    # Clear the lru_cache so get_settings() returns our test settings
    get_settings.cache_clear()
    return create_app(settings=test_settings)


# ── HTTP client fixture ────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client(test_app) -> AsyncClient:
    """
    Async HTTP test client.

    Uses httpx.AsyncClient with ASGI transport — requests go directly to
    the FastAPI app without a network stack.

    Scope=function (default) so each test gets a fresh client.
    """
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://testclient",
    ) as ac:
        yield ac
