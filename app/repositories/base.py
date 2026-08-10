"""
app/repositories/base.py
────────────────────────
Generic async repository with CRUD operations for any SQLAlchemy model.

The Repository Pattern:
  - Abstracts ALL database I/O into one place per entity
  - Services call repository methods, never raw SQLAlchemy
  - Repositories only know about SQLAlchemy — they never import FastAPI or Pydantic
  - Makes testing easy: mock the repository to test service logic without a DB

Generic typing:
  BaseRepository[User] provides type-safe CRUD for User models.
  BaseRepository[Task] provides the same for Task models.
  Entity-specific repositories extend BaseRepository and add custom queries.

Why Generic?
  Without generics you'd write the same get_by_id / create / update / delete
  code for every entity. With BaseRepository[T], you write it once.
"""

import uuid
from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import BaseModel

# T is bound to BaseModel so we can call model.id, model.created_at, etc.
ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """
    Generic async CRUD repository.

    Usage:
        class UserRepository(BaseRepository[User]):
            def __init__(self, session: AsyncSession) -> None:
                super().__init__(User, session)

            async def get_by_email(self, email: str) -> User | None:
                result = await self.session.execute(
                    select(User).where(User.email == email)
                )
                return result.scalar_one_or_none()
    """

    def __init__(self, model: type[ModelType], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    # ── Create ────────────────────────────────────────────────────────────────

    async def create(self, **kwargs: Any) -> ModelType:
        """
        Create a new record and flush it to the session.

        flush() sends the INSERT to the DB (within the current transaction)
        so the returned object has its DB-generated values (like created_at),
        but the transaction is NOT committed yet — that happens in get_db().
        """
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    # ── Read ──────────────────────────────────────────────────────────────────

    async def get_by_id(self, record_id: uuid.UUID) -> ModelType | None:
        """Fetch a single record by primary key. Returns None if not found."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == record_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[ModelType], int]:
        """
        Fetch a page of records and the total count.

        Returns a tuple (items, total) so the caller can build a PaginatedResponse.
        Two queries are issued:
          1. COUNT(*) — gets the total
          2. SELECT … LIMIT … OFFSET — gets the page

        Note: For very large tables (millions of rows), COUNT(*) can be slow.
        Phase 13 (Search) will address this with estimated counts.
        """
        count_result = await self.session.execute(
            select(func.count()).select_from(self.model)
        )
        total = count_result.scalar_one()

        result = await self.session.execute(
            select(self.model)
            .order_by(self.model.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        items = list(result.scalars().all())

        return items, total

    # ── Update ────────────────────────────────────────────────────────────────

    async def update(self, obj: ModelType, **kwargs: Any) -> ModelType:
        """
        Apply a partial update to an existing model instance.

        Only fields explicitly passed are changed. None values are skipped
        so PATCH requests don't accidentally null out existing data.
        """
        for key, value in kwargs.items():
            if value is not None and hasattr(obj, key):
                setattr(obj, key, value)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    # ── Delete ────────────────────────────────────────────────────────────────

    async def delete(self, obj: ModelType) -> None:
        """
        Hard-delete a record.

        For resources that need audit history (tasks, projects), use a
        soft-delete pattern (is_deleted flag) instead. That's introduced
        in Phase 7 for tasks.
        """
        await self.session.delete(obj)
        await self.session.flush()
