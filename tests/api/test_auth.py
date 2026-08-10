import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "testauth@example.com",
            "username": "testauth",
            "password": "securepassword123",
            "full_name": "Test Auth"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "testauth@example.com"
    assert "hashed_password" not in data

@pytest.mark.asyncio
async def test_login_user(client: AsyncClient):
    # Register first
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "loginuser@example.com",
            "username": "loginuser",
            "password": "securepassword123"
        }
    )
    
    # Then login
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "loginuser@example.com",
            "password": "securepassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    # Check for refresh token cookie
    assert "refresh_token" in response.cookies
