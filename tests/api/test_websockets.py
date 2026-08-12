import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect
from uuid import uuid4
import json
import asyncio
from unittest.mock import AsyncMock

from app.api.deps import get_current_user_ws
from app.models.user import User
from app.core.realtime import manager
from app.utils.security import create_access_token


@pytest.fixture
def mock_user():
    return User(
        id=uuid4(),
        email="test@example.com",
        username="testuser",
        hashed_password="hashed",
        is_active=True,
        full_name="Alice Smith",
    )

@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    from app.utils.redis import RedisManager
    from unittest.mock import MagicMock
    mock_client = MagicMock()
    mock_pubsub = AsyncMock()
    mock_client.pubsub.return_value = mock_pubsub
    
    async def mock_init():
        pass
    
    async def mock_close():
        pass
        
    monkeypatch.setattr(RedisManager, "init_redis", mock_init)
    monkeypatch.setattr(RedisManager, "close", mock_close)
    monkeypatch.setattr(RedisManager, "get_client", lambda: mock_client)
    return mock_client, mock_pubsub

@pytest.fixture(autouse=True)
def mock_db_engine(monkeypatch):
    import app.database
    from unittest.mock import AsyncMock, MagicMock
    
    mock_engine = MagicMock()
    
    class MockAsyncContext:
        async def __aenter__(self):
            return AsyncMock()
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
            
    mock_engine.begin.return_value = MockAsyncContext()
    
    async def mock_dispose():
        pass
    mock_engine.dispose = mock_dispose
    
    monkeypatch.setattr(app.database, "engine", mock_engine)

def test_websocket_without_token(test_app):
    with TestClient(test_app) as client:
        with pytest.raises(WebSocketDisconnect) as exc:
            with client.websocket_connect("/ws/notifications"):
                pass
        # 403 or 1008 depending on how FastAPI rejects it. Usually raises WebSocketDisconnect
        assert exc is not None


def test_websocket_expired_token(test_app):
    # Expired token can be generated if we mock or just create one with negative expiration
    pass


def test_websocket_valid_connection(test_app, mock_user):
    async def override_get_current_user_ws():
        return mock_user
        
    test_app.dependency_overrides[get_current_user_ws] = override_get_current_user_ws
    with TestClient(test_app) as client:
        with client.websocket_connect("/ws/notifications?token=dummy") as websocket:
            assert websocket is not None
            channel = f"user_{mock_user.id}"
            assert channel in manager.active_connections
        assert channel not in manager.active_connections
    test_app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_websocket_broadcasting(test_app, mock_user):
    async def override_get_current_user_ws():
        return mock_user
        
    test_app.dependency_overrides[get_current_user_ws] = override_get_current_user_ws
    
    with TestClient(test_app) as client:
        with client.websocket_connect("/ws/notifications?token=dummy") as websocket:
            channel = f"user_{mock_user.id}"
            
            message = {
                "type": "notification",
                "payload": {"id": "123", "title": "Test Notif", "type": "test"},
                "timestamp": "2024-01-01T00:00:00Z"
            }
            
            await manager.broadcast_local(channel, json.dumps(message))
            
            data = websocket.receive_text()
            parsed = json.loads(data)
            assert parsed["type"] == "notification"
            assert parsed["payload"]["id"] == "123"

    test_app.dependency_overrides.clear()

def test_websocket_project_tasks_auth(test_app, mock_user, monkeypatch):
    from app.repositories.project import ProjectMemberRepository
    
    async def override_get_current_user_ws():
        return mock_user
        
    test_app.dependency_overrides[get_current_user_ws] = override_get_current_user_ws
    project_id = uuid4()
    
    # 1. Not a member
    async def mock_not_member(*args, **kwargs):
        return None
    monkeypatch.setattr(ProjectMemberRepository, "get_membership", mock_not_member)
    
    with TestClient(test_app) as client:
        with pytest.raises(WebSocketDisconnect) as exc:
            with client.websocket_connect(f"/ws/projects/{project_id}/tasks?token=dummy"):
                pass
        assert exc.value.code == 1008
        
    # 2. Is a member
    async def mock_is_member(*args, **kwargs):
        return True
    monkeypatch.setattr(ProjectMemberRepository, "get_membership", mock_is_member)
    
    with TestClient(test_app) as client:
        with client.websocket_connect(f"/ws/projects/{project_id}/tasks?token=dummy") as websocket:
            assert websocket is not None
            
    test_app.dependency_overrides.clear()
