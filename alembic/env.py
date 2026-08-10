"""
alembic/env.py
──────────────
Alembic migration environment.

Configured for ASYNC SQLAlchemy (asyncpg driver) with auto-detection of
all models defined in app/models/.

Key decisions:
  1. We import Base from app.models so that Base.metadata has seen ALL model
     definitions — Alembic uses metadata to diff against the live schema.
  2. We load DATABASE_URL from our Settings class (same source as the app).
  3. We use run_async_migrations() which wraps the sync Alembic API in an
     async context — required for asyncpg.

To generate a new migration after changing models:
    alembic revision --autogenerate -m "describe the change"

To apply migrations:
    alembic upgrade head

To rollback one migration:
    alembic downgrade -1
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ── Import all models so Base.metadata is populated ──────────────────────────
# This must happen before we reference target_metadata.
from app.models import Base  # noqa: F401 — side effect: registers all table defs
from app.config import get_settings

# ── Alembic config object ─────────────────────────────────────────────────────
config = context.config

# Set up Python logging from alembic.ini [loggers] section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── Target metadata ───────────────────────────────────────────────────────────
# Alembic compares this against the live DB schema to auto-generate migrations.
target_metadata = Base.metadata

# ── Database URL ──────────────────────────────────────────────────────────────
settings = get_settings()
# Alembic uses asyncpg-compatible URL directly
db_url = settings.DATABASE_URL


# ── Offline migrations (no live DB connection) ────────────────────────────────
def run_migrations_offline() -> None:
    """
    Run migrations without connecting to the DB.

    Useful for generating raw SQL migration scripts that can be reviewed
    before applying (e.g. in CI/CD pipelines or for DBA approval).
    """
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online migrations (real DB connection) ────────────────────────────────────
def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,              # Detect column type changes
        compare_server_default=True,    # Detect server_default changes
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations using an async engine (required for asyncpg)."""
    connectable = async_engine_from_config(
        {"sqlalchemy.url": db_url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,    # Don't pool connections during migrations
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online migrations."""
    asyncio.run(run_async_migrations())


# ── Dispatch ──────────────────────────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
