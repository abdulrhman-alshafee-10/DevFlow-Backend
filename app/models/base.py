"""
app/models/base.py
──────────────────
Base SQLAlchemy model that every other model inherits from.

Provides:
  - UUID primary key (generated client-side with uuid4 — avoids a DB roundtrip)
  - created_at / updated_at timestamps with timezone awareness
  - __repr__ for readable debug output

Design decisions:
  - UUIDs over auto-increment integers:
      • No enumeration attacks (user/1, user/2, user/3 …)
      • Safe to generate before inserting
      • Works across distributed systems and event stores
  - TIMESTAMP WITH TIME ZONE:
      • Always store UTC, display in user's timezone on the frontend
      • Avoids DST bugs
  - server_default vs default:
      • server_default → the DB sets the value (faster, consistent with direct SQL inserts)
      • onupdate → SQLAlchemy updates the field on every UPDATE statement
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Declarative base for all SQLAlchemy models.

    All models inherit from this class. Alembic's env.py imports `Base`
    so it can auto-detect table changes for migration generation.
    """
    pass


class TimestampMixin:
    """
    Adds created_at and updated_at to any model.

    Separate mixin so it can be used independently if needed.
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),  # PostgreSQL sets this on INSERT
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),        # SQLAlchemy updates this on UPDATE
        nullable=False,
    )


class BaseModel(TimestampMixin, Base):
    """
    Abstract base model with UUID PK + timestamps.

    Concrete models inherit from this and only define their own columns.
    __abstract__ = True means SQLAlchemy won't create a table for BaseModel itself.
    """
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,         # Generated in Python, not the database
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id}>"
