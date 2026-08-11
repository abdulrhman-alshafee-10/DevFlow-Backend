"""
tests/api/test_users.py
───────────────────────
API-level tests for the User endpoints — Phase 4 (Authorization).

Changes from Phase 2:
  - User creation now goes through POST /api/v1/auth/register (Phase 3)
  - All endpoints require a valid JWT (Phase 3)
  - GET /users is superuser-only (Phase 4)
  - GET/PATCH/DELETE /users/{id} require ownership or superuser (Phase 4)

Testing strategy:
  - SQLite in-memory database (zero-setup, CI-friendly)
  - Redis is mocked/faked — we use fakeredis for the auth service
  - Tests cover: authentication, authorization, and CRUD correctness

Architecture note — why we mock Redis:
  The auth service uses Redis for brute-force protection. In tests we use
  fakeredis.aioredis, which is an in-memory Redis-compatible client, so
  tests run without a real Redis server.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from unittest.mock import AsyncMock, MagicMock

from app.database import get_db
from app.models import Base
from app.main import create_app
from app.config import Settings, get_settings
from app.utils.redis import get_redis_client

# ── In-memory SQLite + Redis mock setup ───────────────────────────────────────

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


def make_fake_redis() -> AsyncMock:
    """
    A minimal fake Redis client that satisfies the auth service's needs:
      - incr()   → returns 1 (first attempt, never locked out)
      - expire() → no-op
      - delete() → no-op
    """
    redis = AsyncMock()
    redis.incr.return_value = 1    # Always first attempt → never rate-limited
    redis.expire.return_value = True
    redis.delete.return_value = 1
    return redis


@pytest_asyncio.fixture
async def db_engine():
    """Create a shared in-memory engine for a test session."""
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
    """Provide an async DB session backed by the in-memory SQLite engine."""
    session_factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    """
    Full-stack test client:
    - DB → in-memory SQLite
    - Redis → fake (in-memory mock)
    - App → fully initialized FastAPI instance
    """
    test_settings = Settings(
        APP_NAME="DevFlow-Test",
        ENVIRONMENT="development",
        DEBUG=False,
        ALLOWED_ORIGINS_STR="http://testclient",
        DATABASE_URL=TEST_DB_URL,
    )
    get_settings.cache_clear()
    app = create_app(settings=test_settings)

    async def override_get_db():
        yield db_session

    fake_redis = make_fake_redis()

    async def override_get_redis():
        return fake_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis_client] = override_get_redis

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testclient",
    ) as ac:
        yield ac


# ── Test helpers ──────────────────────────────────────────────────────────────

ALICE = {
    "email": "alice@example.com",
    "username": "alice",
    "password": "password123",
    "full_name": "Alice Example",
}

BOB = {
    "email": "bob@example.com",
    "username": "bob",
    "password": "password123",
    "full_name": "Bob Example",
}


async def register(client: AsyncClient, data: dict) -> dict:
    """Register a user and return the response body."""
    resp = await client.post("/api/v1/auth/register", json=data)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def login(client: AsyncClient, data: dict) -> str:
    """Login and return the Bearer access token."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": data["email"], "password": data["password"]},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


async def auth_headers(client: AsyncClient, data: dict) -> dict:
    """Return authorization headers for a registered + logged-in user."""
    await register(client, data)
    token = await login(client, data)
    return {"Authorization": f"Bearer {token}"}


async def make_superuser(db_session: AsyncSession, user_id: str) -> None:
    """Directly promote a user to superuser in the database (bypass API)."""
    from sqlalchemy import update
    from app.models.user import User
    import uuid
    await db_session.execute(
        update(User)
        .where(User.id == uuid.UUID(user_id))
        .values(is_superuser=True)
    )
    await db_session.commit()


# ── Authentication Required ───────────────────────────────────────────────────

class TestAuthenticationRequired:
    """All user endpoints must reject unauthenticated requests."""

    @pytest.mark.asyncio
    async def test_list_users_unauthenticated_returns_401(self, client: AsyncClient):
        resp = await client.get("/api/v1/users")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_get_user_unauthenticated_returns_401(self, client: AsyncClient):
        resp = await client.get("/api/v1/users/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_update_user_unauthenticated_returns_401(self, client: AsyncClient):
        resp = await client.patch(
            "/api/v1/users/00000000-0000-0000-0000-000000000000",
            json={"full_name": "X"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_user_unauthenticated_returns_401(self, client: AsyncClient):
        resp = await client.delete("/api/v1/users/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 401


# ── List Users (Superuser Only) ────────────────────────────────────────────────

class TestListUsers:

    @pytest.mark.asyncio
    async def test_regular_user_cannot_list_users_returns_403(
        self, client: AsyncClient
    ):
        """Regular authenticated users should get 403 on the admin list endpoint."""
        headers = await auth_headers(client, ALICE)
        resp = await client.get("/api/v1/users", headers=headers)
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_superuser_can_list_users(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """A promoted superuser can successfully list all users."""
        alice_data = await register(client, ALICE)
        await make_superuser(db_session, alice_data["id"])
        # Re-login to get a fresh token (superuser flag is checked at runtime)
        token = await login(client, ALICE)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.get("/api/v1/users", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body
        assert body["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_users_pagination_structure(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Superuser list response has the correct pagination fields."""
        alice_data = await register(client, ALICE)
        await make_superuser(db_session, alice_data["id"])
        token = await login(client, ALICE)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.get("/api/v1/users?page=1&size=20", headers=headers)
        body = resp.json()
        assert "items" in body
        assert "total" in body
        assert "page" in body
        assert "size" in body
        assert "pages" in body
        assert "has_next" in body
        assert "has_prev" in body


# ── Get User By ID ────────────────────────────────────────────────────────────

class TestGetUser:

    @pytest.mark.asyncio
    async def test_user_can_get_own_profile(self, client: AsyncClient):
        """A user can read their own profile."""
        alice_data = await register(client, ALICE)
        token = await login(client, ALICE)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.get(f"/api/v1/users/{alice_data['id']}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == alice_data["id"]
        assert resp.json()["email"] == ALICE["email"]

    @pytest.mark.asyncio
    async def test_user_cannot_get_other_users_profile_returns_403(
        self, client: AsyncClient
    ):
        """A user cannot read another user's profile (IDOR prevention)."""
        bob_data = await register(client, BOB)
        headers = await auth_headers(client, ALICE)

        resp = await client.get(f"/api/v1/users/{bob_data['id']}", headers=headers)
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_superuser_can_get_any_users_profile(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """A superuser can read any user's profile."""
        alice_data = await register(client, ALICE)
        bob_data = await register(client, BOB)
        await make_superuser(db_session, alice_data["id"])
        token = await login(client, ALICE)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.get(f"/api/v1/users/{bob_data['id']}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == bob_data["id"]

    @pytest.mark.asyncio
    async def test_user_gets_403_for_nonexistent_id_that_is_not_own(
        self, client: AsyncClient
    ):
        """
        A regular user trying to GET another (non-existent) user's profile
        should get 403 (ownership check fires before the 404 DB check).
        This is intentional: we don't leak whether a user ID exists.
        """
        headers = await auth_headers(client, ALICE)
        fake_id = "00000000-0000-0000-0000-000000000001"
        resp = await client.get(f"/api/v1/users/{fake_id}", headers=headers)
        # 403 because the ownership check fires first (Alice's id != fake_id)
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_get_nonexistent_user_as_superuser_returns_404(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        alice_data = await register(client, ALICE)
        await make_superuser(db_session, alice_data["id"])
        token = await login(client, ALICE)
        headers = {"Authorization": f"Bearer {token}"}

        fake_id = "00000000-0000-0000-0000-000000000001"
        resp = await client.get(f"/api/v1/users/{fake_id}", headers=headers)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_response_includes_is_superuser_field(self, client: AsyncClient):
        """Phase 4: is_superuser must be in the UserResponse."""
        alice_data = await register(client, ALICE)
        token = await login(client, ALICE)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.get(f"/api/v1/users/{alice_data['id']}", headers=headers)
        assert "is_superuser" in resp.json()
        assert resp.json()["is_superuser"] is False

    @pytest.mark.asyncio
    async def test_response_never_exposes_password(self, client: AsyncClient):
        alice_data = await register(client, ALICE)
        token = await login(client, ALICE)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.get(f"/api/v1/users/{alice_data['id']}", headers=headers)
        body = resp.json()
        assert "hashed_password" not in body
        assert "password" not in body

    @pytest.mark.asyncio
    async def test_invalid_uuid_returns_422(self, client: AsyncClient):
        headers = await auth_headers(client, ALICE)
        resp = await client.get("/api/v1/users/not-a-uuid", headers=headers)
        assert resp.status_code == 422


# ── Update User ────────────────────────────────────────────────────────────────

class TestUpdateUser:

    @pytest.mark.asyncio
    async def test_user_can_update_own_profile(self, client: AsyncClient):
        alice_data = await register(client, ALICE)
        token = await login(client, ALICE)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.patch(
            f"/api/v1/users/{alice_data['id']}",
            json={"full_name": "Alice Updated"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "Alice Updated"

    @pytest.mark.asyncio
    async def test_user_cannot_update_other_users_profile_returns_403(
        self, client: AsyncClient
    ):
        bob_data = await register(client, BOB)
        headers = await auth_headers(client, ALICE)

        resp = await client.patch(
            f"/api/v1/users/{bob_data['id']}",
            json={"full_name": "Hacked"},
            headers=headers,
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_superuser_can_update_any_profile(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        alice_data = await register(client, ALICE)
        bob_data = await register(client, BOB)
        await make_superuser(db_session, alice_data["id"])
        token = await login(client, ALICE)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.patch(
            f"/api/v1/users/{bob_data['id']}",
            json={"full_name": "Admin Updated Bob"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "Admin Updated Bob"

    @pytest.mark.asyncio
    async def test_partial_update_doesnt_clear_other_fields(
        self, client: AsyncClient
    ):
        alice_data = await register(client, ALICE)
        token = await login(client, ALICE)
        headers = {"Authorization": f"Bearer {token}"}

        await client.patch(
            f"/api/v1/users/{alice_data['id']}",
            json={"full_name": "New Name"},
            headers=headers,
        )
        resp = await client.get(
            f"/api/v1/users/{alice_data['id']}", headers=headers
        )
        assert resp.json()["email"] == ALICE["email"]

    @pytest.mark.asyncio
    async def test_update_nonexistent_user_as_superuser_returns_404(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        alice_data = await register(client, ALICE)
        await make_superuser(db_session, alice_data["id"])
        token = await login(client, ALICE)
        headers = {"Authorization": f"Bearer {token}"}

        fake_id = "00000000-0000-0000-0000-000000000001"
        resp = await client.patch(
            f"/api/v1/users/{fake_id}",
            json={"full_name": "X"},
            headers=headers,
        )
        assert resp.status_code == 404


# ── Delete User ────────────────────────────────────────────────────────────────

class TestDeleteUser:

    @pytest.mark.asyncio
    async def test_user_can_delete_own_account(self, client: AsyncClient):
        alice_data = await register(client, ALICE)
        token = await login(client, ALICE)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.delete(
            f"/api/v1/users/{alice_data['id']}", headers=headers
        )
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_user_cannot_delete_another_user_returns_403(
        self, client: AsyncClient
    ):
        bob_data = await register(client, BOB)
        headers = await auth_headers(client, ALICE)

        resp = await client.delete(f"/api/v1/users/{bob_data['id']}", headers=headers)
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_superuser_can_delete_any_account(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        alice_data = await register(client, ALICE)
        bob_data = await register(client, BOB)
        await make_superuser(db_session, alice_data["id"])
        token = await login(client, ALICE)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.delete(
            f"/api/v1/users/{bob_data['id']}", headers=headers
        )
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_deleted_user_not_found_afterwards(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        alice_data = await register(client, ALICE)
        await make_superuser(db_session, alice_data["id"])
        bob_data = await register(client, BOB)
        token = await login(client, ALICE)
        headers = {"Authorization": f"Bearer {token}"}

        await client.delete(f"/api/v1/users/{bob_data['id']}", headers=headers)
        resp = await client.get(f"/api/v1/users/{bob_data['id']}", headers=headers)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_as_superuser_returns_404(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        alice_data = await register(client, ALICE)
        await make_superuser(db_session, alice_data["id"])
        token = await login(client, ALICE)
        headers = {"Authorization": f"Bearer {token}"}

        fake_id = "00000000-0000-0000-0000-000000000001"
        resp = await client.delete(f"/api/v1/users/{fake_id}", headers=headers)
        assert resp.status_code == 404


# ── Placeholder to avoid unresolved name error in test above ──────────────────
async def make_superuser_by_email(client: AsyncClient, email: str) -> None:
    """Placeholder — used inline in the skipped test above."""
    pass
