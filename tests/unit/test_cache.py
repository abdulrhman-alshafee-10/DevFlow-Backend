import pytest
from unittest.mock import AsyncMock, patch
from pydantic import BaseModel
import json

from app.core.cache import CacheManager
from app.utils.redis import RedisManager


class MockModel(BaseModel):
    id: int
    name: str


@pytest.fixture
def mock_redis():
    with patch.object(RedisManager, '_client', new_callable=AsyncMock) as mock_client:
        yield mock_client


@pytest.mark.asyncio
async def test_cache_hit(mock_redis):
    # Setup
    mock_redis.get.return_value = json.dumps({"id": 1, "name": "Test"}).encode("utf-8")
    
    async def fetch():
        return MockModel(id=2, name="Should not run")

    # Execute
    result = await CacheManager.get_or_set("test_key", fetch, ttl=60, model=MockModel)

    # Assert
    assert result.id == 1
    assert result.name == "Test"
    mock_redis.get.assert_called_once_with("test_key")
    mock_redis.set.assert_not_called()


@pytest.mark.asyncio
async def test_cache_miss(mock_redis):
    # Setup
    mock_redis.get.return_value = None
    
    async def fetch():
        return MockModel(id=1, name="Test")

    # Execute
    result = await CacheManager.get_or_set("test_key", fetch, ttl=60, model=MockModel)

    # Assert
    assert result.id == 1
    assert result.name == "Test"
    mock_redis.get.assert_called_once_with("test_key")
    mock_redis.set.assert_called_once()
    args, kwargs = mock_redis.set.call_args
    assert args[0] == "test_key"
    assert "Test" in args[1]
    assert kwargs["ex"] == 60


@pytest.mark.asyncio
async def test_cache_fail_open(mock_redis):
    # Setup: Redis raises an exception
    mock_redis.get.side_effect = Exception("Redis connection failed")
    
    async def fetch():
        return MockModel(id=1, name="Fallback")

    # Execute
    result = await CacheManager.get_or_set("test_key", fetch, ttl=60, model=MockModel)

    # Assert: Should gracefully fallback to fetch() and return the result
    assert result.id == 1
    assert result.name == "Fallback"
