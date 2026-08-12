import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock

from app.config import Settings
from app.main import create_app
from app.utils.redis import get_redis_client
from app.database import get_db
def make_fake_redis() -> AsyncMock:
    redis = AsyncMock()
    redis.incr.return_value = 1
    redis.expire.return_value = True
    redis.delete.return_value = 1
    return redis

@pytest.fixture(scope="module")
def search_test_settings() -> Settings:
    return Settings(
        APP_NAME="DevFlow-SearchTest",
        ENVIRONMENT="development",
        DEBUG=True,
        ALLOWED_ORIGINS_STR="http://testclient",
    )

@pytest.fixture(scope="module")
def search_test_app(search_test_settings: Settings):
    app = create_app(settings=search_test_settings)
    return app

@pytest_asyncio.fixture
async def client(search_test_app, db_session):
    fake_redis = make_fake_redis()
    
    async def override_get_redis():
        return fake_redis
        
    async def override_get_db():
        yield db_session
        
    search_test_app.dependency_overrides[get_redis_client] = override_get_redis
    search_test_app.dependency_overrides[get_db] = override_get_db

    with patch("app.core.realtime.RedisManager.get_client", return_value=fake_redis):
        async with AsyncClient(
            transport=ASGITransport(app=search_test_app),
            base_url="http://testclient",
        ) as ac:
            yield ac
        
    search_test_app.dependency_overrides.clear()

from tests.api.test_tasks import _register_and_login, _create_org, _create_project, _create_task

async def _create_comment(client: AsyncClient, headers: dict, task_id: str, content: str) -> dict:
    resp = await client.post(f"/api/v1/tasks/{task_id}/comments", json={
        "content": content
    }, headers=headers)
    assert resp.status_code == 201
    return resp.json()

async def _create_search_task(client: AsyncClient, headers: dict, project_id: str, title: str, description: str) -> dict:
    resp = await client.post(f"/api/v1/projects/{project_id}/tasks", json={
        "title": title,
        "description": description,
        "status": "todo",
        "priority": "medium"
    }, headers=headers)
    assert resp.status_code == 201
    return resp.json()

@pytest.mark.asyncio
async def test_unified_search(client: AsyncClient):
    alice = await _register_and_login(client, {"email": "alice_search@test.com", "username": "alice_search", "password": "StrongPassword123!", "full_name": "Alice"})
    org = await _create_org(client, alice["headers"], "Alice Search Org")
    project = await _create_project(client, alice["headers"], org["id"], "Project Alpha")
    
    # Create some tasks and comments
    task1 = await _create_search_task(client, alice["headers"], project["id"], "Deploy to Production", "We need to deploy the new features.")
    task2 = await _create_search_task(client, alice["headers"], project["id"], "Fix login bug", "Users cannot login on mobile.")
    
    await _create_comment(client, alice["headers"], task1["id"], "I will handle the deployment today.")
    await _create_comment(client, alice["headers"], task2["id"], "The login issue is related to the deploy we did yesterday.")

    # Search for "deploy"
    resp = await client.get(f"/api/v1/search?q=deploy&org_id={org['id']}", headers=alice["headers"])
    assert resp.status_code == 200
    data = resp.json()
    
    # Both task1 and its comment, and comment in task2 have "deploy" (stemmed to deploy)
    assert data["total"] >= 1
    
    types = [r["type"] for r in data["results"]]
    assert "task" in types or "comment" in types

    # Search for "login bug"
    resp = await client.get(f"/api/v1/search?q=login bug&org_id={org['id']}", headers=alice["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert "login" in data["results"][0]["title"].lower()

@pytest.mark.asyncio
async def test_search_isolation(client: AsyncClient):
    # Bob searches Alice's org, should be 403 or 404 (handled by require_org_member)
    alice = await _register_and_login(client, {"email": "alice_org@test.com", "username": "alice_org", "password": "StrongPassword123!", "full_name": "Alice"})
    bob = await _register_and_login(client, {"email": "bob_org@test.com", "username": "bob_org", "password": "StrongPassword123!", "full_name": "Bob"})
    
    org = await _create_org(client, alice["headers"], "Alice Secret Org")
    
    resp = await client.get(f"/api/v1/search?q=test&org_id={org['id']}", headers=bob["headers"])
    assert resp.status_code in (403, 404)
