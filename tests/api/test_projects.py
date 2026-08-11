"""
tests/api/test_projects.py
────────────────────────
Integration tests for the Projects endpoints.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import uuid

from app.config import Settings, get_settings
from app.main import create_app
from unittest.mock import AsyncMock
from app.utils.redis import get_redis_client
from app.database import get_db

@pytest.fixture(scope="module")
def project_test_settings() -> Settings:
    return Settings(
        APP_NAME="DevFlow-ProjectTest",
        ENVIRONMENT="development",
        DEBUG=True,
        ALLOWED_ORIGINS_STR="http://testclient",
    )

@pytest.fixture(scope="module")
def project_test_app(project_test_settings: Settings):
    get_settings.cache_clear()
    return create_app(settings=project_test_settings)

def make_fake_redis() -> AsyncMock:
    redis = AsyncMock()
    redis.incr.return_value = 1
    redis.expire.return_value = True
    redis.delete.return_value = 1
    return redis

@pytest_asyncio.fixture
async def client(project_test_app, db_session):
    fake_redis = make_fake_redis()
    
    async def override_get_redis():
        return fake_redis
        
    async def override_get_db():
        yield db_session
        
    project_test_app.dependency_overrides[get_redis_client] = override_get_redis
    project_test_app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=project_test_app),
        base_url="http://testclient",
    ) as ac:
        yield ac
        
    project_test_app.dependency_overrides.clear()


def _unique_user(prefix: str = "user") -> dict:
    uid = uuid.uuid4().hex[:8]
    return {
        "email": f"{prefix}_{uid}@test.com",
        "username": f"{prefix}_{uid}",
        "password": "SecurePass123!",
        "full_name": f"Test {prefix.title()}",
    }


async def _register_and_login(client: AsyncClient, user_data: dict | None = None) -> dict:
    if user_data is None:
        user_data = _unique_user()

    reg = await client.post("/api/v1/auth/register", json=user_data)
    assert reg.status_code == 201, f"Register failed: {reg.text}"

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": user_data["email"], "password": user_data["password"]},
    )
    assert login.status_code == 200, f"Login failed: {login.text}"

    token = login.json()["access_token"]
    return {
        "headers": {"Authorization": f"Bearer {token}"},
        "email": user_data["email"],
        "username": user_data["username"],
        "user_data": user_data,
    }


async def _create_org(client: AsyncClient, headers: dict, name: str | None = None) -> dict:
    uid = uuid.uuid4().hex[:6]
    payload = {"name": name or f"Test Org {uid}"}
    resp = await client.post("/api/v1/organizations", json=payload, headers=headers)
    assert resp.status_code == 201, f"Create org failed: {resp.text}"
    return resp.json()

async def _create_project(client: AsyncClient, headers: dict, org_id: str, name: str | None = None) -> dict:
    uid = uuid.uuid4().hex[:6]
    payload = {"name": name or f"Test Project {uid}"}
    resp = await client.post(f"/api/v1/organizations/{org_id}/projects", json=payload, headers=headers)
    assert resp.status_code == 201, f"Create project failed: {resp.text}"
    return resp.json()


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient):
    alice = await _register_and_login(client)
    org = await _create_org(client, alice["headers"])
    
    project = await _create_project(client, alice["headers"], org["id"])
    
    assert project["name"].startswith("Test Project")
    assert "id" in project


@pytest.mark.asyncio
async def test_list_projects(client: AsyncClient):
    alice = await _register_and_login(client)
    org = await _create_org(client, alice["headers"])
    
    p1 = await _create_project(client, alice["headers"], org["id"])
    p2 = await _create_project(client, alice["headers"], org["id"])
    
    resp = await client.get(f"/api/v1/organizations/{org['id']}/projects", headers=alice["headers"])
    assert resp.status_code == 200
    
    items = resp.json()["items"]
    assert len(items) == 2


@pytest.mark.asyncio
async def test_get_project(client: AsyncClient):
    alice = await _register_and_login(client)
    org = await _create_org(client, alice["headers"])
    project = await _create_project(client, alice["headers"], org["id"])
    
    resp = await client.get(f"/api/v1/projects/{project['id']}", headers=alice["headers"])
    assert resp.status_code == 200
    assert resp.json()["id"] == project["id"]


@pytest.mark.asyncio
async def test_cross_org_project_access_403(client: AsyncClient):
    alice = await _register_and_login(client)
    bob = await _register_and_login(client)
    
    org = await _create_org(client, alice["headers"])
    project = await _create_project(client, alice["headers"], org["id"])
    
    resp = await client.get(f"/api/v1/projects/{project['id']}", headers=bob["headers"])
    assert resp.status_code == 403
