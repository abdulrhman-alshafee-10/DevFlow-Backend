"""
tests/api/test_notifications.py
───────────────────────────────
Integration tests for Notifications.
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
def notif_test_settings() -> Settings:
    return Settings(
        APP_NAME="DevFlow-NotifTest",
        ENVIRONMENT="development",
        DEBUG=True,
        ALLOWED_ORIGINS_STR="http://testclient",
    )

@pytest.fixture(scope="module")
def notif_test_app(notif_test_settings: Settings):
    get_settings.cache_clear()
    return create_app(settings=notif_test_settings)

def make_fake_redis() -> AsyncMock:
    redis = AsyncMock()
    redis.incr.return_value = 1
    redis.expire.return_value = True
    redis.delete.return_value = 1
    return redis

@pytest_asyncio.fixture
async def client(notif_test_app, db_session):
    fake_redis = make_fake_redis()
    
    async def override_get_redis():
        return fake_redis
        
    async def override_get_db():
        yield db_session
        
    notif_test_app.dependency_overrides[get_redis_client] = override_get_redis
    notif_test_app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=notif_test_app),
        base_url="http://testclient",
    ) as ac:
        yield ac
        
    notif_test_app.dependency_overrides.clear()


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
    user_id = reg.json()["id"]
    return {
        "headers": {"Authorization": f"Bearer {token}"},
        "email": user_data["email"],
        "username": user_data["username"],
        "user_data": user_data,
        "id": user_id,
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
async def test_invitation_creates_notification(client: AsyncClient):
    alice = await _register_and_login(client)
    bob = await _register_and_login(client)
    
    org = await _create_org(client, alice["headers"])
    
    # Alice invites Bob
    resp = await client.post(
        f"/api/v1/organizations/{org['id']}/invitations",
        json={"email": bob["email"], "role": "member"},
        headers=alice["headers"],
    )
    assert resp.status_code == 201
    
    # Bob should have a notification
    notifs_resp = await client.get("/api/v1/notifications", headers=bob["headers"])
    assert notifs_resp.status_code == 200
    items = notifs_resp.json()["items"]
    assert len(items) == 1
    assert items[0]["type"] == "invitation_received"
    
    # Unread count should be 1
    count_resp = await client.get("/api/v1/notifications/unread-count", headers=bob["headers"])
    assert count_resp.status_code == 200
    assert count_resp.json()["count"] == 1


@pytest.mark.asyncio
async def test_mark_notification_as_read(client: AsyncClient):
    alice = await _register_and_login(client)
    bob = await _register_and_login(client)
    
    org = await _create_org(client, alice["headers"])
    
    # Alice invites Bob
    await client.post(
        f"/api/v1/organizations/{org['id']}/invitations",
        json={"email": bob["email"], "role": "member"},
        headers=alice["headers"],
    )
    
    # Get the notification ID
    notifs_resp = await client.get("/api/v1/notifications", headers=bob["headers"])
    notif_id = notifs_resp.json()["items"][0]["id"]
    
    # Mark as read
    read_resp = await client.patch(f"/api/v1/notifications/{notif_id}/read", headers=bob["headers"])
    assert read_resp.status_code == 200
    assert read_resp.json()["is_read"] is True
    
    # Unread count should be 0
    count_resp = await client.get("/api/v1/notifications/unread-count", headers=bob["headers"])
    assert count_resp.json()["count"] == 0


@pytest.mark.asyncio
async def test_mark_all_as_read(client: AsyncClient):
    alice = await _register_and_login(client)
    bob = await _register_and_login(client)
    
    org = await _create_org(client, alice["headers"])
    org2 = await _create_org(client, alice["headers"])
    
    # Alice invites Bob to two orgs
    await client.post(f"/api/v1/organizations/{org['id']}/invitations", json={"email": bob["email"], "role": "member"}, headers=alice["headers"])
    await client.post(f"/api/v1/organizations/{org2['id']}/invitations", json={"email": bob["email"], "role": "member"}, headers=alice["headers"])
    
    count_resp = await client.get("/api/v1/notifications/unread-count", headers=bob["headers"])
    assert count_resp.json()["count"] == 2
    
    read_all = await client.post("/api/v1/notifications/read-all", headers=bob["headers"])
    assert read_all.status_code == 200
    
    count_resp2 = await client.get("/api/v1/notifications/unread-count", headers=bob["headers"])
    assert count_resp2.json()["count"] == 0


@pytest.mark.asyncio
async def test_task_assignment_creates_notification(client: AsyncClient, db_session):
    alice = await _register_and_login(client)
    bob = await _register_and_login(client)
    
    org = await _create_org(client, alice["headers"])
    project = await _create_project(client, alice["headers"], org["id"])
    
    # Add bob to org using db_session
    from app.models.organization import OrganizationMember
    import uuid
    member = OrganizationMember(
        organization_id=uuid.UUID(org['id']),
        user_id=uuid.UUID(bob['id']),
        role="member"
    )
    db_session.add(member)
    await db_session.commit()
    
    # Add bob to project
    await client.post(f"/api/v1/projects/{project['id']}/members", json={"user_id": bob["id"], "role": "member"}, headers=alice["headers"])
    
    # Clear bob's previous notifications
    await client.post("/api/v1/notifications/read-all", headers=bob["headers"])
    
    # Alice creates task and assigns bob
    payload = {"title": "Test Task for Bob", "status": "todo", "priority": "medium", "assignee_id": bob["id"]}
    await client.post(f"/api/v1/projects/{project['id']}/tasks", json=payload, headers=alice["headers"])
    
    # Check bob has notification
    notifs_resp = await client.get("/api/v1/notifications?is_read=false", headers=bob["headers"])
    items = notifs_resp.json()["items"]
    assert len(items) == 1
    assert items[0]["type"] == "task_assigned"
    
    # Bob changes status
    task_id = items[0]["data"]["task_id"]
    await client.patch(f"/api/v1/tasks/{task_id}", json={"status": "in_progress"}, headers=bob["headers"])
    
    # Bob shouldn't notify himself, so unread should still be 1 (the assignment one) or 0 since we queried it
    # Wait, the task_assigned is still unread for Bob.
    notifs_resp = await client.get("/api/v1/notifications?is_read=false", headers=bob["headers"])
    items = notifs_resp.json()["items"]
    assert len(items) == 1
    
    # Alice changes status
    await client.patch(f"/api/v1/tasks/{task_id}", json={"status": "done"}, headers=alice["headers"])
    
    # Bob should get task_status_changed notification
    notifs_resp = await client.get("/api/v1/notifications?is_read=false", headers=bob["headers"])
    items = notifs_resp.json()["items"]
    assert len(items) == 2
    types = [item["type"] for item in items]
    assert "task_status_changed" in types


@pytest.mark.asyncio
async def test_cross_user_notification_access_denied(client: AsyncClient):
    alice = await _register_and_login(client)
    bob = await _register_and_login(client)
    
    org = await _create_org(client, alice["headers"])
    
    # Alice invites Bob
    await client.post(
        f"/api/v1/organizations/{org['id']}/invitations",
        json={"email": bob["email"], "role": "member"},
        headers=alice["headers"],
    )
    
    # Get Bob's notification ID
    notifs_resp = await client.get("/api/v1/notifications", headers=bob["headers"])
    notif_id = notifs_resp.json()["items"][0]["id"]
    
    # Alice tries to read it
    read_resp = await client.patch(f"/api/v1/notifications/{notif_id}/read", headers=alice["headers"])
    assert read_resp.status_code == 403
    
    # Alice tries to delete it
    del_resp = await client.delete(f"/api/v1/notifications/{notif_id}", headers=alice["headers"])
    assert del_resp.status_code == 403
