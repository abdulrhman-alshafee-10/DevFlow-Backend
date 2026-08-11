"""
tests/api/test_auth.py
──────────────────────
API-level tests for the authentication + admin endpoints.

Covers:
  - POST /auth/register      — user registration
  - POST /auth/login         — login, access token, refresh cookie
  - GET  /auth/me            — current user profile + is_superuser field
  - PATCH /auth/admin/users/{id}/promote — superuser promotion
  - PATCH /auth/admin/users/{id}/demote  — superuser demotion

Testing infrastructure:
  - SQLite in-memory for zero-setup DB isolation
  - fakeredis (AsyncMock) for Redis brute-force protection
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from unittest.mock import AsyncMock
import uuid

from app.database import get_db
from app.models import Base
from app.models.user import User
from app.main import create_app
from app.config import Settings, get_settings
from app.utils.redis import get_redis_client


# ── Fixtures ──────────────────────────────────────────────────────────────────

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


def make_fake_redis() -> AsyncMock:
    redis = AsyncMock()
    redis.incr.return_value = 1
    redis.expire.return_value = True
    redis.delete.return_value = 1
    return redis


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    session_factory = async_sessionmaker(
        bind=db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
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
        transport=ASGITransport(app=app), base_url="http://testclient"
    ) as ac:
        yield ac


# ── Helpers ───────────────────────────────────────────────────────────────────

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
    resp = await client.post("/api/v1/auth/register", json=data)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def login(client: AsyncClient, data: dict) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": data["email"], "password": data["password"]},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


async def auth_headers(client: AsyncClient, data: dict) -> dict:
    await register(client, data)
    token = await login(client, data)
    return {"Authorization": f"Bearer {token}"}


async def make_superuser(db_session: AsyncSession, user_id: str) -> None:
    await db_session.execute(
        update(User)
        .where(User.id == uuid.UUID(user_id))
        .values(is_superuser=True)
    )
    await db_session.commit()


# ── Registration Tests ────────────────────────────────────────────────────────

class TestRegister:

    @pytest.mark.asyncio
    async def test_register_returns_201(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/register", json=ALICE)
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_register_returns_user_data(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/register", json=ALICE)
        data = resp.json()
        assert data["email"] == ALICE["email"]
        assert data["username"] == ALICE["username"]

    @pytest.mark.asyncio
    async def test_register_never_exposes_password(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/register", json=ALICE)
        body = resp.json()
        assert "hashed_password" not in body
        assert "password" not in body

    @pytest.mark.asyncio
    async def test_register_email_verified_defaults_false(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/register", json=ALICE)
        assert resp.json()["is_email_verified"] is False

    @pytest.mark.asyncio
    async def test_register_is_superuser_defaults_false(self, client: AsyncClient):
        """Phase 4: new users should never be superuser by default."""
        resp = await client.post("/api/v1/auth/register", json=ALICE)
        assert resp.json()["is_superuser"] is False

    @pytest.mark.asyncio
    async def test_register_duplicate_email_returns_409(self, client: AsyncClient):
        await register(client, ALICE)
        resp = await client.post("/api/v1/auth/register", json=ALICE)
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_register_duplicate_username_returns_409(self, client: AsyncClient):
        await register(client, ALICE)
        resp = await client.post(
            "/api/v1/auth/register",
            json={**ALICE, "email": "other@example.com"},
        )
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_register_invalid_email_returns_422(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/register", json={**ALICE, "email": "bad-email"}
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_register_short_password_returns_422(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/register", json={**ALICE, "password": "abc"}
        )
        assert resp.status_code == 422


# ── Login Tests ───────────────────────────────────────────────────────────────

class TestLogin:

    @pytest.mark.asyncio
    async def test_login_returns_access_token(self, client: AsyncClient):
        await register(client, ALICE)
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": ALICE["email"], "password": ALICE["password"]},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    @pytest.mark.asyncio
    async def test_login_sets_refresh_token_cookie(self, client: AsyncClient):
        await register(client, ALICE)
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": ALICE["email"], "password": ALICE["password"]},
        )
        assert "refresh_token" in resp.cookies

    @pytest.mark.asyncio
    async def test_login_wrong_password_returns_401(self, client: AsyncClient):
        await register(client, ALICE)
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": ALICE["email"], "password": "wrongpassword1"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user_returns_401(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "password123"},
        )
        assert resp.status_code == 401


# ── /me endpoint ──────────────────────────────────────────────────────────────

class TestGetMe:

    @pytest.mark.asyncio
    async def test_me_returns_current_user(self, client: AsyncClient):
        headers = await auth_headers(client, ALICE)
        resp = await client.get("/api/v1/auth/me", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["email"] == ALICE["email"]

    @pytest.mark.asyncio
    async def test_me_includes_is_superuser_field(self, client: AsyncClient):
        """Phase 4: /me must expose is_superuser."""
        headers = await auth_headers(client, ALICE)
        resp = await client.get("/api/v1/auth/me", headers=headers)
        assert "is_superuser" in resp.json()

    @pytest.mark.asyncio
    async def test_me_includes_is_email_verified_field(self, client: AsyncClient):
        headers = await auth_headers(client, ALICE)
        resp = await client.get("/api/v1/auth/me", headers=headers)
        assert "is_email_verified" in resp.json()

    @pytest.mark.asyncio
    async def test_me_unauthenticated_returns_401(self, client: AsyncClient):
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401


# ── Promote / Demote Superuser ────────────────────────────────────────────────

class TestPromoteDemote:

    @pytest.mark.asyncio
    async def test_regular_user_cannot_promote_returns_403(self, client: AsyncClient):
        """Non-superusers must not be able to promote anyone."""
        bob_data = await register(client, BOB)
        headers = await auth_headers(client, ALICE)

        resp = await client.patch(
            f"/api/v1/auth/admin/users/{bob_data['id']}/promote",
            headers=headers,
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_promote_returns_401(
        self, client: AsyncClient
    ):
        bob_data = await register(client, BOB)
        resp = await client.patch(
            f"/api/v1/auth/admin/users/{bob_data['id']}/promote"
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_superuser_can_promote_another_user(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """A superuser can successfully promote another user."""
        alice_data = await register(client, ALICE)
        bob_data = await register(client, BOB)
        await make_superuser(db_session, alice_data["id"])
        token = await login(client, ALICE)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.patch(
            f"/api/v1/auth/admin/users/{bob_data['id']}/promote",
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["is_superuser"] is True

    @pytest.mark.asyncio
    async def test_promote_is_idempotent(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Promoting an already-superuser should return 200 without error."""
        alice_data = await register(client, ALICE)
        bob_data = await register(client, BOB)
        await make_superuser(db_session, alice_data["id"])
        await make_superuser(db_session, bob_data["id"])
        token = await login(client, ALICE)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.patch(
            f"/api/v1/auth/admin/users/{bob_data['id']}/promote",
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["is_superuser"] is True

    @pytest.mark.asyncio
    async def test_superuser_can_demote_another_user(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """A superuser can revoke another superuser's privileges."""
        alice_data = await register(client, ALICE)
        bob_data = await register(client, BOB)
        await make_superuser(db_session, alice_data["id"])
        await make_superuser(db_session, bob_data["id"])
        token = await login(client, ALICE)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.patch(
            f"/api/v1/auth/admin/users/{bob_data['id']}/demote",
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["is_superuser"] is False

    @pytest.mark.asyncio
    async def test_superuser_cannot_demote_themselves_returns_400(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Self-demotion prevention: avoids full admin lockout."""
        alice_data = await register(client, ALICE)
        await make_superuser(db_session, alice_data["id"])
        token = await login(client, ALICE)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.patch(
            f"/api/v1/auth/admin/users/{alice_data['id']}/demote",
            headers=headers,
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_regular_user_cannot_demote_returns_403(self, client: AsyncClient):
        bob_data = await register(client, BOB)
        headers = await auth_headers(client, ALICE)

        resp = await client.patch(
            f"/api/v1/auth/admin/users/{bob_data['id']}/demote",
            headers=headers,
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_promote_nonexistent_user_returns_404(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        alice_data = await register(client, ALICE)
        await make_superuser(db_session, alice_data["id"])
        token = await login(client, ALICE)
        headers = {"Authorization": f"Bearer {token}"}

        fake_id = "00000000-0000-0000-0000-000000000001"
        resp = await client.patch(
            f"/api/v1/auth/admin/users/{fake_id}/promote",
            headers=headers,
        )
        assert resp.status_code == 404
