"""
app/services/user.py
────────────────────
User service — all business logic for user management.

The service layer sits between the API (routers) and the data layer
(repositories). It enforces business rules:
  - An email/username must be unique before creating
  - A user must exist before updating or deleting
  - hashed_password is set here (in Phase 2, using a placeholder scheme;
    Phase 3 replaces this with bcrypt)

What the service does NOT do:
  - No HTTP knowledge (no Request, no status codes, no JSONResponse)
  - No direct database queries (delegates to UserRepository)
  - No schema validation (Pydantic handles that before the router calls the service)

This separation means:
  - The service can be tested without a web server
  - The same service can be used from a CLI, a background job, or a WebSocket handler
"""

import hashlib
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import AlreadyExistsError, NotFoundError
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.core.cache import CacheManager


def _placeholder_hash(password: str) -> str:
    """
    Phase 2 placeholder: store a SHA-256 hash so the column is populated.

    ⚠️  THIS IS NOT SECURE — SHA-256 is NOT appropriate for passwords.
    Phase 3 (Authentication) replaces this entirely with bcrypt via passlib.
    It is here only to satisfy the DB NOT NULL constraint during development.
    """
    return "ph2:" + hashlib.sha256(password.encode()).hexdigest()


class UserService:
    """
    Encapsulates all user management business logic.

    Instantiated per-request (created in the router's Depends chain).
    Each instance gets its own AsyncSession via UserRepository.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.repo = UserRepository(session)

    # ── Create ────────────────────────────────────────────────────────────────

    async def create(self, data: UserCreate) -> User:
        """
        Register a new user.

        Business rules enforced:
          1. Email must be unique
          2. Username must be unique
          3. Password is hashed before storage
        """
        if await self.repo.email_exists(data.email):
            raise AlreadyExistsError("Email")

        if await self.repo.username_exists(data.username):
            raise AlreadyExistsError("Username")

        return await self.repo.create(
            email=data.email.lower(),
            username=data.username.lower(),
            hashed_password=_placeholder_hash(data.password),
            full_name=data.full_name,
            avatar_url=data.avatar_url,
        )

    # ── Read ──────────────────────────────────────────────────────────────────

    async def get_by_id(self, user_id: uuid.UUID) -> User:
        """Fetch a user by ID or raise NotFoundError."""
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found.")
        return user

    async def get_profile_cached(self, user_id: uuid.UUID) -> UserResponse:
        """Fetch a user by ID and return a cached Pydantic model."""
        async def fetch():
            user = await self.get_by_id(user_id)
            return UserResponse.model_validate(user)

        return await CacheManager.get_or_set(
            key=f"user_profile:{user_id}",
            fetch_func=fetch,
            ttl=300,
            model=UserResponse
        )

    async def list_users(
        self, page: int = 1, size: int = 20
    ) -> tuple[list[User], int]:
        """Return a page of users and the total count."""
        offset = (page - 1) * size
        return await self.repo.get_all(offset=offset, limit=size)

    # ── Update ────────────────────────────────────────────────────────────────

    async def update(self, user_id: uuid.UUID, data: UserUpdate) -> User:
        """
        Partially update a user's profile fields.

        Only fields that are explicitly provided (not None) are changed.
        """
        user = await self.get_by_id(user_id)
        updated_user = await self.repo.update(
            user,
            full_name=data.full_name,
            avatar_url=data.avatar_url,
        )
        await CacheManager.delete(f"user_profile:{user_id}")
        await CacheManager.delete(f"user_auth:{user_id}")
        return updated_user

    # ── Delete ────────────────────────────────────────────────────────────────

    async def delete(self, user_id: uuid.UUID) -> None:
        """Hard-delete a user."""
        user = await self.get_by_id(user_id)
        await self.repo.delete(user)
        await CacheManager.delete(f"user_profile:{user_id}")
        await CacheManager.delete(f"user_auth:{user_id}")

    # ── Superuser Management ──────────────────────────────────────────────────

    async def promote_to_superuser(self, user_id: uuid.UUID) -> User:
        """
        Grant superuser (system admin) privileges to a user.

        This is an irreversible promotion intended for initial bootstrapping
        and to grant another trusted admin system-level access.
        Can only be called by an existing superuser (enforced at the API layer).
        """
        user = await self.get_by_id(user_id)
        if user.is_superuser:
            # Idempotent — no error if already a superuser
            return user
        updated_user = await self.repo.update(user, is_superuser=True)
        await CacheManager.delete(f"user_profile:{user_id}")
        await CacheManager.delete(f"user_auth:{user_id}")
        return updated_user

    async def demote_from_superuser(self, user_id: uuid.UUID) -> User:
        """
        Revoke superuser privileges from a user.

        Used by existing superusers to manage system-level admin access.
        A superuser cannot demote themselves (enforced at the API layer).
        """
        user = await self.get_by_id(user_id)
        updated_user = await self.repo.update(user, is_superuser=False)
        await CacheManager.delete(f"user_profile:{user_id}")
        await CacheManager.delete(f"user_auth:{user_id}")
        return updated_user
