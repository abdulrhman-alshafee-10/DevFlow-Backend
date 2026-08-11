"""
tests/api/test_comments.py
────────────────────────
Integration tests for Comments.
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
def comment_test_settings() -> Settings:
    return Settings(
        APP_NAME="DevFlow-CommentTest",
        ENVIRONMENT="development",
        DEBUG=True,
        ALLOWED_ORIGINS_STR="http://testclient",
    )

@pytest.fixture(scope="module")
def comment_test_app(comment_test_settings: Settings):
    get_settings.cache_clear()
    return create_app(settings=comment_test_settings)

def make_fake_redis() -> AsyncMock:
    redis = AsyncMock()
    redis.incr.return_value = 1
    redis.expire.return_value = True
    redis.delete.return_value = 1
    return redis

@pytest_asyncio.fixture
async def client(comment_test_app, db_session):
    fake_redis = make_fake_redis()
    
    async def override_get_redis():
        return fake_redis
        
    async def override_get_db():
        yield db_session
        
    comment_test_app.dependency_overrides[get_redis_client] = override_get_redis
    comment_test_app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=comment_test_app),
        base_url="http://testclient",
    ) as ac:
        yield ac
        
    comment_test_app.dependency_overrides.clear()


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

async def _create_org(client: AsyncClient, headers: dict) -> dict:
    uid = uuid.uuid4().hex[:6]
    payload = {"name": f"Test Org {uid}"}
    resp = await client.post("/api/v1/organizations", json=payload, headers=headers)
    return resp.json()

async def _create_project(client: AsyncClient, headers: dict, org_id: str) -> dict:
    uid = uuid.uuid4().hex[:6]
    payload = {"name": f"Test Project {uid}"}
    resp = await client.post(f"/api/v1/organizations/{org_id}/projects", json=payload, headers=headers)
    return resp.json()

async def _create_task(client: AsyncClient, headers: dict, project_id: str) -> dict:
    uid = uuid.uuid4().hex[:6]
    payload = {"title": f"Test Task {uid}", "status": "todo", "priority": "medium"}
    resp = await client.post(f"/api/v1/projects/{project_id}/tasks", json=payload, headers=headers)
    return resp.json()

async def _create_comment(client: AsyncClient, headers: dict, task_id: str) -> dict:
    payload = {"content": "This is a comment"}
    resp = await client.post(f"/api/v1/tasks/{task_id}/comments", json=payload, headers=headers)
    assert resp.status_code == 201, f"Create comment failed: {resp.text}"
    return resp.json()

@pytest.mark.asyncio
async def test_create_comment(client: AsyncClient):
    alice = await _register_and_login(client)
    org = await _create_org(client, alice["headers"])
    project = await _create_project(client, alice["headers"], org["id"])
    task = await _create_task(client, alice["headers"], project["id"])
    
    comment = await _create_comment(client, alice["headers"], task["id"])
    assert comment["content"] == "This is a comment"
    assert "id" in comment

@pytest.mark.asyncio
async def test_list_comments(client: AsyncClient):
    alice = await _register_and_login(client)
    org = await _create_org(client, alice["headers"])
    project = await _create_project(client, alice["headers"], org["id"])
    task = await _create_task(client, alice["headers"], project["id"])
    
    await _create_comment(client, alice["headers"], task["id"])
    await _create_comment(client, alice["headers"], task["id"])
    
    resp = await client.get(f"/api/v1/tasks/{task['id']}/comments", headers=alice["headers"])
    assert resp.status_code == 200
    
    items = resp.json()["items"]
    assert len(items) == 2

@pytest.mark.asyncio
async def test_update_comment(client: AsyncClient):
    alice = await _register_and_login(client)
    org = await _create_org(client, alice["headers"])
    project = await _create_project(client, alice["headers"], org["id"])
    task = await _create_task(client, alice["headers"], project["id"])
    comment = await _create_comment(client, alice["headers"], task["id"])
    
    resp = await client.patch(
        f"/api/v1/comments/{comment['id']}",
        json={"content": "Updated content"},
        headers=alice["headers"],
    )
    assert resp.status_code == 200
    assert resp.json()["content"] == "Updated content"
    
@pytest.mark.asyncio
async def test_delete_comment(client: AsyncClient):
    alice = await _register_and_login(client)
    org = await _create_org(client, alice["headers"])
    project = await _create_project(client, alice["headers"], org["id"])
    task = await _create_task(client, alice["headers"], project["id"])
    comment = await _create_comment(client, alice["headers"], task["id"])
    
    resp = await client.delete(f"/api/v1/comments/{comment['id']}", headers=alice["headers"])
    assert resp.status_code == 204
