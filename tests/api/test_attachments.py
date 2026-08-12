import io
import pytest
import pytest_asyncio
import uuid
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport

from app.config import Settings, get_settings
from app.main import create_app
from app.utils.redis import get_redis_client
from app.database import get_db

from tests.api.test_tasks import _register_and_login, _create_org, _create_project, _create_task

@pytest.fixture(scope="module")
def attachment_test_settings() -> Settings:
    return Settings(
        APP_NAME="DevFlow-AttachmentTest",
        ENVIRONMENT="development",
        DEBUG=True,
        ALLOWED_ORIGINS_STR="http://testclient",
    )

@pytest.fixture(scope="module")
def attachment_test_app(attachment_test_settings: Settings):
    get_settings.cache_clear()
    return create_app(settings=attachment_test_settings)

def make_fake_redis() -> AsyncMock:
    redis = AsyncMock()
    redis.incr.return_value = 1
    redis.expire.return_value = True
    redis.delete.return_value = 1
    return redis

@pytest_asyncio.fixture
async def client(attachment_test_app, db_session):
    fake_redis = make_fake_redis()
    
    async def override_get_redis():
        return fake_redis
        
    async def override_get_db():
        yield db_session
        
    attachment_test_app.dependency_overrides[get_redis_client] = override_get_redis
    attachment_test_app.dependency_overrides[get_db] = override_get_db

    with patch("app.core.realtime.RedisManager.get_client", return_value=fake_redis):
        async with AsyncClient(
            transport=ASGITransport(app=attachment_test_app),
            base_url="http://testclient",
        ) as ac:
            yield ac
        
    attachment_test_app.dependency_overrides.clear()

@pytest.fixture
def mock_storage():
    with patch("app.services.attachment_service.storage_client") as mock:
        mock.upload_file = AsyncMock(return_value=True)
        mock.get_presigned_url = AsyncMock(return_value="http://minio/devflow-attachments/test-url?expires=900")
        mock.delete_file = AsyncMock(return_value=True)
        yield mock

@pytest.mark.asyncio
async def test_upload_attachment_success(client: AsyncClient, mock_storage):
    alice = await _register_and_login(client)
    org = await _create_org(client, alice["headers"])
    project = await _create_project(client, alice["headers"], org["id"])
    task = await _create_task(client, alice["headers"], project["id"])

    file_content = b"fake image content"
    with patch("app.services.attachment_service.magic.from_buffer") as mock_magic:
        mock_magic.return_value = "image/png"
        
        response = await client.post(
            f"/api/v1/tasks/{task['id']}/attachments",
            files={"file": ("test.png", io.BytesIO(file_content), "image/png")},
            headers=alice["headers"]
        )
    
    assert response.status_code == 201
    data = response.json()
    assert data["original_filename"] == "test.png"
    assert data["mime_type"] == "image/png"
    assert data["file_size"] == len(file_content)
    assert mock_storage.upload_file.called

@pytest.mark.asyncio
async def test_upload_attachment_too_large(client: AsyncClient, mock_storage):
    alice = await _register_and_login(client)
    org = await _create_org(client, alice["headers"])
    project = await _create_project(client, alice["headers"], org["id"])
    task = await _create_task(client, alice["headers"], project["id"])
            
    with patch("app.services.attachment_service.magic.from_buffer") as mock_magic:
        mock_magic.return_value = "image/png"
        
        response = await client.post(
            f"/api/v1/tasks/{task['id']}/attachments",
            files={"file": ("large.png", b"a" * (11 * 1024 * 1024), "image/png")},
            headers=alice["headers"]
        )
    
    assert response.status_code == 413

@pytest.mark.asyncio
async def test_upload_attachment_invalid_type(client: AsyncClient):
    alice = await _register_and_login(client)
    org = await _create_org(client, alice["headers"])
    project = await _create_project(client, alice["headers"], org["id"])
    task = await _create_task(client, alice["headers"], project["id"])

    with patch("app.services.attachment_service.magic.from_buffer") as mock_magic:
        mock_magic.return_value = "application/x-executable"
        
        response = await client.post(
            f"/api/v1/tasks/{task['id']}/attachments",
            files={"file": ("malware.exe", io.BytesIO(b"fake"), "application/x-executable")},
            headers=alice["headers"]
        )
    
    assert response.status_code == 415

@pytest.mark.asyncio
async def test_get_download_url(client: AsyncClient, mock_storage):
    alice = await _register_and_login(client)
    org = await _create_org(client, alice["headers"])
    project = await _create_project(client, alice["headers"], org["id"])
    task = await _create_task(client, alice["headers"], project["id"])

    with patch("app.services.attachment_service.magic.from_buffer") as mock_magic:
        mock_magic.return_value = "image/png"
        upload_resp = await client.post(
            f"/api/v1/tasks/{task['id']}/attachments",
            files={"file": ("test.png", io.BytesIO(b"fake"), "image/png")},
            headers=alice["headers"]
        )
    
    attachment_id = upload_resp.json()["id"]
    url_resp = await client.get(f"/api/v1/attachments/{attachment_id}/download", headers=alice["headers"])
    assert url_resp.status_code == 200
    assert "url" in url_resp.json()
    assert mock_storage.get_presigned_url.called

@pytest.mark.asyncio
async def test_delete_attachment(client: AsyncClient, mock_storage):
    alice = await _register_and_login(client)
    org = await _create_org(client, alice["headers"])
    project = await _create_project(client, alice["headers"], org["id"])
    task = await _create_task(client, alice["headers"], project["id"])

    with patch("app.services.attachment_service.magic.from_buffer") as mock_magic:
        mock_magic.return_value = "image/png"
        upload_resp = await client.post(
            f"/api/v1/tasks/{task['id']}/attachments",
            files={"file": ("test.png", io.BytesIO(b"fake"), "image/png")},
            headers=alice["headers"]
        )
    
    attachment_id = upload_resp.json()["id"]
    del_resp = await client.delete(f"/api/v1/attachments/{attachment_id}", headers=alice["headers"])
    assert del_resp.status_code == 204
    assert mock_storage.delete_file.called

    url_resp = await client.get(f"/api/v1/attachments/{attachment_id}/download", headers=alice["headers"])
    assert url_resp.status_code == 404
