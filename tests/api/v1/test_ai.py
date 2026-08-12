import pytest
from httpx import AsyncClient
from uuid import uuid4
from fastapi import FastAPI
from app.api.v1.ai import get_ai_service
from app.api.deps import get_current_user
from app.models.user import User

# Mock AIService
class MockAIService:
    async def analyze_task(self, user_id, task_id, focus):
        yield "This "
        yield "is "
        yield "mocked."

    async def suggest_subtasks(self, user_id, task_id):
        return ["Subtask 1", "Subtask 2"]

    async def summarize_project(self, user_id, project_id):
        yield "Project "
        yield "summary."

    async def chat(self, user_id, message, project_id):
        yield "Mock "
        yield "chat."

def mock_get_current_user():
    return User(id=uuid4(), email="test@example.com")

@pytest.fixture
def mock_ai_service(test_app: FastAPI):
    mock = MockAIService()
    test_app.dependency_overrides[get_ai_service] = lambda: mock
    test_app.dependency_overrides[get_current_user] = mock_get_current_user
    yield mock
    test_app.dependency_overrides.pop(get_ai_service, None)
    test_app.dependency_overrides.pop(get_current_user, None)

@pytest.mark.asyncio
async def test_analyze_task(client: AsyncClient, mock_ai_service):
    task_id = str(uuid4())
    response = await client.post(
        f"/api/v1/ai/tasks/{task_id}/analyze",
        json={"focus": "risks"}
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert "data: This " in response.text
    assert "data: is " in response.text

@pytest.mark.asyncio
async def test_suggest_subtasks(client: AsyncClient, mock_ai_service):
    task_id = str(uuid4())
    response = await client.post(
        f"/api/v1/ai/tasks/{task_id}/suggest-subtasks",
        json={}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["subtasks"] == ["Subtask 1", "Subtask 2"]

@pytest.mark.asyncio
async def test_summarize_project(client: AsyncClient, mock_ai_service):
    project_id = str(uuid4())
    response = await client.post(
        f"/api/v1/ai/projects/{project_id}/summarize",
        json={}
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

@pytest.mark.asyncio
async def test_chat(client: AsyncClient, mock_ai_service):
    response = await client.post(
        f"/api/v1/ai/chat",
        json={"message": "hello", "project_id": str(uuid4())}
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
