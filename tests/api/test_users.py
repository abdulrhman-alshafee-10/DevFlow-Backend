"""
tests/api/test_users.py
───────────────────────
API-level tests for Phase 2 user CRUD endpoints.

Testing strategy:
  - We override the `get_db` dependency with an in-memory SQLite database
    via aiosqlite, so tests run WITHOUT a running PostgreSQL instance.
  - Each test gets a fresh database (tables created fresh, dropped after).
  - This tests the FULL stack: router → service → repository → DB.

Why SQLite instead of PostgreSQL for tests?
  SQLite + aiosqlite is zero-setup and runs in CI without Docker.
  PostgreSQL-specific features (UUID type, timezone handling) are compatible
  thanks to SQLAlchemy's dialect abstraction.

  In Phase 16 (Testing phase), a dedicated PostgreSQL test container
  is added for full production parity.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import get_db
from app.models import Base
from app.main import create_app
from app.config import Settings, get_settings

# ── In-memory SQLite setup ────────────────────────────────────────────────────

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_session():
    """
    Create a fresh in-memory SQLite database for each test.

    Tables are created at the start and dropped at the end.
    Each test is fully isolated.
    """
    engine = create_async_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    """
    HTTP test client with the real DB dependency overridden to use
    the in-memory SQLite session.
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

    # Override get_db to yield our test session
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testclient",
    ) as ac:
        yield ac


# ── Helpers ───────────────────────────────────────────────────────────────────

VALID_USER = {
    "email": "alice@example.com",
    "username": "alice",
    "password": "password123",
    "full_name": "Alice Example",
}


async def create_user(client: AsyncClient, data: dict | None = None) -> dict:
    """Helper: POST /users and return the response body."""
    payload = data or VALID_USER
    resp = await client.post("/api/v1/users", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


# ── CREATE ────────────────────────────────────────────────────────────────────

class TestCreateUser:

    async def test_creates_user_returns_201(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/users", json=VALID_USER)
        assert resp.status_code == 201

    async def test_response_has_expected_fields(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/users", json=VALID_USER)
        body = resp.json()
        assert "id" in body
        assert body["email"] == VALID_USER["email"]
        assert body["username"] == VALID_USER["username"]
        assert body["full_name"] == VALID_USER["full_name"]

    async def test_hashed_password_not_in_response(self, client: AsyncClient) -> None:
        """CRITICAL: password hash must never be exposed in responses."""
        resp = await client.post("/api/v1/users", json=VALID_USER)
        body = resp.json()
        assert "hashed_password" not in body
        assert "password" not in body

    async def test_is_email_verified_defaults_to_false(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/users", json=VALID_USER)
        assert resp.json()["is_email_verified"] is False

    async def test_is_active_defaults_to_true(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/users", json=VALID_USER)
        assert resp.json()["is_active"] is True

    async def test_duplicate_email_returns_409(self, client: AsyncClient) -> None:
        await create_user(client)
        resp = await client.post("/api/v1/users", json=VALID_USER)
        assert resp.status_code == 409

    async def test_duplicate_username_returns_409(self, client: AsyncClient) -> None:
        await create_user(client)
        different_email = {**VALID_USER, "email": "other@example.com"}
        resp = await client.post("/api/v1/users", json=different_email)
        assert resp.status_code == 409

    async def test_missing_email_returns_422(self, client: AsyncClient) -> None:
        payload = {k: v for k, v in VALID_USER.items() if k != "email"}
        resp = await client.post("/api/v1/users", json=payload)
        assert resp.status_code == 422

    async def test_missing_password_returns_422(self, client: AsyncClient) -> None:
        payload = {k: v for k, v in VALID_USER.items() if k != "password"}
        resp = await client.post("/api/v1/users", json=payload)
        assert resp.status_code == 422

    async def test_short_password_returns_422(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/users", json={**VALID_USER, "password": "abc"})
        assert resp.status_code == 422

    async def test_invalid_email_returns_422(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/users", json={**VALID_USER, "email": "not-an-email"})
        assert resp.status_code == 422

    async def test_username_lowercase_stored(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/users", json={**VALID_USER, "username": "ALICE"})
        assert resp.json()["username"] == "alice"


# ── GET BY ID ─────────────────────────────────────────────────────────────────

class TestGetUser:

    async def test_get_existing_user(self, client: AsyncClient) -> None:
        created = await create_user(client)
        resp = await client.get(f"/api/v1/users/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    async def test_get_nonexistent_user_returns_404(self, client: AsyncClient) -> None:
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.get(f"/api/v1/users/{fake_id}")
        assert resp.status_code == 404

    async def test_invalid_uuid_returns_422(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/users/not-a-uuid")
        assert resp.status_code == 422


# ── LIST ──────────────────────────────────────────────────────────────────────

class TestListUsers:

    async def test_empty_list(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/users")
        assert resp.status_code == 200
        body = resp.json()
        assert body["items"] == []
        assert body["total"] == 0

    async def test_lists_created_users(self, client: AsyncClient) -> None:
        await create_user(client)
        resp = await client.get("/api/v1/users")
        assert resp.json()["total"] == 1
        assert len(resp.json()["items"]) == 1

    async def test_pagination_structure(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/users?page=1&size=20")
        body = resp.json()
        assert "items" in body
        assert "total" in body
        assert "page" in body
        assert "size" in body
        assert "pages" in body
        assert "has_next" in body
        assert "has_prev" in body

    async def test_page_size_respected(self, client: AsyncClient) -> None:
        # Create 3 users
        for i in range(3):
            await create_user(client, {
                "email": f"user{i}@example.com",
                "username": f"user{i}",
                "password": "password123",
            })
        resp = await client.get("/api/v1/users?page=1&size=2")
        body = resp.json()
        assert body["total"] == 3
        assert len(body["items"]) == 2
        assert body["has_next"] is True
        assert body["has_prev"] is False

    async def test_page_size_max_100(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/users?size=999")
        assert resp.status_code == 422


# ── UPDATE ────────────────────────────────────────────────────────────────────

class TestUpdateUser:

    async def test_update_full_name(self, client: AsyncClient) -> None:
        created = await create_user(client)
        resp = await client.patch(
            f"/api/v1/users/{created['id']}",
            json={"full_name": "Alice Updated"},
        )
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "Alice Updated"

    async def test_update_nonexistent_user_returns_404(self, client: AsyncClient) -> None:
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.patch(f"/api/v1/users/{fake_id}", json={"full_name": "X"})
        assert resp.status_code == 404

    async def test_partial_update_doesnt_clear_other_fields(self, client: AsyncClient) -> None:
        created = await create_user(client)
        # Update only full_name
        await client.patch(f"/api/v1/users/{created['id']}", json={"full_name": "New Name"})
        # Email should still be there
        resp = await client.get(f"/api/v1/users/{created['id']}")
        assert resp.json()["email"] == VALID_USER["email"]


# ── DELETE ────────────────────────────────────────────────────────────────────

class TestDeleteUser:

    async def test_delete_returns_204(self, client: AsyncClient) -> None:
        created = await create_user(client)
        resp = await client.delete(f"/api/v1/users/{created['id']}")
        assert resp.status_code == 204

    async def test_deleted_user_not_found(self, client: AsyncClient) -> None:
        created = await create_user(client)
        await client.delete(f"/api/v1/users/{created['id']}")
        resp = await client.get(f"/api/v1/users/{created['id']}")
        assert resp.status_code == 404

    async def test_delete_nonexistent_returns_404(self, client: AsyncClient) -> None:
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.delete(f"/api/v1/users/{fake_id}")
        assert resp.status_code == 404
