import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI, Depends, Request, Response
from app.core.rate_limit import RateLimiter
from app.utils.redis import RedisManager

# Create a clean test app to isolate RateLimiter behavior
test_app = FastAPI()
rate_limiter = RateLimiter(limit=5, window=60, tier="test")

from app.exceptions import RateLimitError
from app.api.error_handlers import rate_limit_handler
test_app.add_exception_handler(RateLimitError, rate_limit_handler)

@test_app.get("/test", dependencies=[Depends(rate_limiter)])
async def dummy_endpoint():
    return {"status": "ok"}

@pytest.fixture
def mock_redis():
    with patch.object(RedisManager, '_client', new_callable=AsyncMock) as mock_client:
        mock_pipeline = MagicMock()
        mock_pipeline.execute = AsyncMock(return_value=[1, True])
        mock_client.pipeline = MagicMock(return_value=mock_pipeline)
        mock_client.ttl.return_value = 60
        mock_client.incr.return_value = 1
        yield mock_client

@pytest.mark.asyncio
async def test_rate_limit_headers(mock_redis):
    # Setup mock to simulate first request (count 1)
    mock_redis.get.return_value = None
    mock_pipeline = MagicMock()
    mock_pipeline.execute = AsyncMock(return_value=[1, True])
    mock_redis.pipeline = MagicMock(return_value=mock_pipeline)

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        response = await client.get("/test")

    assert response.status_code == 200
    assert "X-RateLimit-Limit" in response.headers
    assert response.headers["X-RateLimit-Limit"] == "5"
    assert "X-RateLimit-Remaining" in response.headers
    assert response.headers["X-RateLimit-Remaining"] == "4"

@pytest.mark.asyncio
async def test_rate_limit_exceeded(mock_redis):
    # Setup mock to simulate limit exceeded
    mock_redis.get.return_value = "5"
    mock_redis.ttl.return_value = 30

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        response = await client.get("/test")

    assert response.status_code == 429
    assert "Retry-After" in response.headers
    assert response.headers["Retry-After"] == "30"
    assert response.headers["X-RateLimit-Remaining"] == "0"

@pytest.mark.asyncio
async def test_rate_limit_fail_open(mock_redis):
    # Setup mock to simulate Redis failure
    mock_redis.get.side_effect = Exception("Redis connection failed")

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        response = await client.get("/test")

    # Should fall through to the route logic and return 200
    assert response.status_code == 200
