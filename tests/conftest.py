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
from app.core.celery_app import celery_app

# Configure celery for testing (run synchronously without broker)
celery_app.conf.update(
    task_always_eager=True,
    task_eager_propagates=True,
)


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

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, REGCONFIG
from sqlalchemy import JSON
from app.database import get_db
from app.models import Base

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

@compiles(TSVECTOR, "sqlite")
def compile_tsvector_sqlite(type_, compiler, **kw):
    return "TEXT"

@compiles(REGCONFIG, "sqlite")
def compile_regconfig_sqlite(type_, compiler, **kw):
    return "TEXT"

# Hack to fix literal value rendering for REGCONFIG in SQLite
from sqlalchemy.dialects.sqlite.base import SQLiteCompiler
def render_literal_value(self, value, type_):
    if isinstance(type_, REGCONFIG):
        return f"'{value}'"
    return super(SQLiteCompiler, self).render_literal_value(value, type_)
SQLiteCompiler.render_literal_value = render_literal_value

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "connect")
def sqlite_engine_connect(dbapi_connection, connection_record):
    if getattr(dbapi_connection, "create_function", None):
        dbapi_connection.create_function("to_tsvector", 2, lambda a, b: "", deterministic=True)

@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(db_engine):
    session_factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session

@pytest.fixture(scope="session")
def test_app(test_settings: Settings):
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
