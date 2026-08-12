import pytest
from httpx import AsyncClient
import uuid

from .test_projects import _register_and_login, _create_org

@pytest.mark.asyncio
async def test_update_org(client: AsyncClient):
    alice = await _register_and_login(client)
    org = await _create_org(client, alice["headers"])
    
    resp = await client.patch(
        f"/api/v1/organizations/{org['id']}",
        json={"name": "Updated Org", "description": "Org Desc"},
        headers=alice["headers"]
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Org"

@pytest.mark.asyncio
async def test_delete_org(client: AsyncClient):
    alice = await _register_and_login(client)
    org = await _create_org(client, alice["headers"])
    
    resp = await client.delete(f"/api/v1/organizations/{org['id']}", headers=alice["headers"])
    assert resp.status_code == 204

@pytest.mark.asyncio
async def test_list_org_members(client: AsyncClient):
    alice = await _register_and_login(client)
    org = await _create_org(client, alice["headers"])
    
    resp = await client.get(f"/api/v1/organizations/{org['id']}/members", headers=alice["headers"])
    assert resp.status_code == 200
    assert len(resp.json()["items"]) >= 1

