"""
app/repositories/user.py
────────────────────────
User-specific repository extending the generic BaseRepository.

Adds queries that are specific to the User entity:
  - get_by_email     → used during login
  - get_by_username  → used during registration to check uniqueness
  - email_exists     → cheap existence check (no full row fetch)
  - username_exists  → same for username
"""

import uuid

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(User, session)

    # ── Lookup by unique fields ───────────────────────────────────────────────

    async def get_by_email(self, email: str) -> User | None:
        """Case-insensitive email lookup."""
        result = await self.session.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.username == username.lower())
        )
        return result.scalar_one_or_none()

    # ── Existence checks (cheaper than fetching the full row) ─────────────────

    async def email_exists(self, email: str) -> bool:
        result = await self.session.execute(
            select(exists().where(User.email == email.lower()))
        )
        return bool(result.scalar())

    async def username_exists(self, username: str) -> bool:
        result = await self.session.execute(
            select(exists().where(User.username == username.lower()))
        )
        return bool(result.scalar())
