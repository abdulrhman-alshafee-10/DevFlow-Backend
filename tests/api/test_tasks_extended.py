import pytest
from httpx import AsyncClient
import uuid

from .test_projects import _register_and_login, _create_org, _create_project

async def _create_task(client: AsyncClient, headers: dict, project_id: str):
    payload = {"title": "Task 1", "status": "todo", "priority": "medium", "description": "Desc"}
    resp = await client.post(f"/api/v1/projects/{project_id}/tasks", json=payload, headers=headers)
    assert resp.status_code == 201
    return resp.json()

@pytest.mark.asyncio
async def test_update_task(client: AsyncClient):
    alice = await _register_and_login(client)
    org = await _create_org(client, alice["headers"])
    project = await _create_project(client, alice["headers"], org["id"])
    task = await _create_task(client, alice["headers"], project["id"])
    
    resp = await client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={"title": "Updated Task", "status": "in_progress"},
        headers=alice["headers"]
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated Task"

@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient):
    alice = await _register_and_login(client)
    org = await _create_org(client, alice["headers"])
    project = await _create_project(client, alice["headers"], org["id"])
    task = await _create_task(client, alice["headers"], project["id"])
    
    resp = await client.delete(f"/api/v1/tasks/{task['id']}", headers=alice["headers"])
    assert resp.status_code == 204

