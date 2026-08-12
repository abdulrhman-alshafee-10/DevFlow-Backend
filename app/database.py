"""
app/database.py
───────────────
Async SQLAlchemy 2.x engine and session factory.

Key concepts demonstrated here:
  - async_engine          — connection pool to PostgreSQL via asyncpg
  - AsyncSession          — unit-of-work for a single request
  - async_sessionmaker    — factory that creates sessions with consistent config
  - get_db()              — FastAPI dependency (yield pattern) that manages the
                            session lifecycle: open → yield → commit or rollback → close

Session lifecycle per request:
  1. Request arrives → get_db() opens a new AsyncSession
  2. Router calls the endpoint, session is injected via Depends(get_db)
  3. Service/repository uses the session to query/write
  4. If the endpoint succeeds → get_db() commits
  5. If an exception occurs  → get_db() rolls back
  6. Finally: session is always closed (connection returned to pool)

Why NOT autocommit?
  We want explicit control. The commit happens in get_db() after the entire
  handler succeeds — not inside individual repository calls. This keeps
  multiple writes in the same request in a single transaction.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.config import get_settings

settings = get_settings()

# ── Engine ────────────────────────────────────────────────────────────────────
# Created once at module import time. Shared across all requests.
# The pool keeps N connections open, reusing them instead of creating a new TCP
# connection for every request (expensive).
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,          # Log every SQL statement in development
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_pre_ping=True,           # Test connection health before handing it out
)

# ── Session factory ───────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,   # Keep objects accessible after commit (no lazy-load)
    autocommit=False,
    autoflush=False,          # We flush manually before queries that need fresh data
)


# ── FastAPI dependency ────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield an async database session for the duration of a request.

    Usage in a route:
        async def my_endpoint(db: AsyncSession = Depends(get_db)):
            ...

    The `async with` syntax is equivalent to try/finally — it guarantees
    the session is closed even if an exception is raised mid-request.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
