"""
app/core/cache.py
─────────────────
Cache manager for caching responses and data in Redis.
Implements the cache-aside pattern and provides graceful degradation.
"""
import json
import logging
from typing import Any, Callable, TypeVar, Awaitable

from pydantic import BaseModel
from redis.asyncio.client import Redis

from app.utils.redis import RedisManager

logger = logging.getLogger(__name__)

T = TypeVar("T")

class CacheManager:
    """
    Manages caching operations using Redis.
    Fails open (graceful degradation) if Redis is unavailable.
    """
    @staticmethod
    async def get_or_set(
        key: str,
        fetch_func: Callable[[], Awaitable[T]],
        ttl: int,
        model: type[BaseModel] | None = None
    ) -> T:
        """
        Cache-aside pattern: try to get from cache, if missing/failed, 
        fetch from source and set in cache.
        """
        redis_client = RedisManager._client
        
        # If redis isn't initialized or unavailable, just fetch directly
        if redis_client is None:
            return await fetch_func()

        try:
            cached_data = await redis_client.get(key)
            if cached_data:
                logger.debug(f"Cache hit for {key}")
                data = json.loads(cached_data)
                if model:
                    if isinstance(data, list):
                        return [model.model_validate(item) for item in data]
                    return model.model_validate(data)
                return data
            logger.debug(f"Cache miss for {key}")
        except Exception as e:
            logger.warning(f"Redis get error for {key}: {e}")

        # Fetch from source
        data = await fetch_func()

        if data is not None:
            try:
                # Serialize
                if model:
                    if isinstance(data, list):
                        serialized_data = json.dumps([item.model_dump(mode="json") for item in data])
                    else:
                        serialized_data = data.model_dump_json()
                else:
                    serialized_data = json.dumps(data)
                
                await redis_client.set(key, serialized_data, ex=ttl)
            except Exception as e:
                logger.warning(f"Redis set error for {key}: {e}")

        return data

    @staticmethod
    async def delete(key: str) -> None:
        """Invalidate a specific cache key."""
        redis_client = RedisManager._client
        if redis_client is None:
            return
            
        try:
            await redis_client.delete(key)
        except Exception as e:
            logger.warning(f"Redis delete error for {key}: {e}")

    @staticmethod
    async def delete_pattern(pattern: str) -> None:
        """Invalidate cache keys matching a pattern."""
        redis_client = RedisManager._client
        if redis_client is None:
            return
            
        try:
            cursor = 0
            while True:
                cursor, keys = await redis_client.scan(cursor=cursor, match=pattern)
                if keys:
                    await redis_client.delete(*keys)
                if cursor == 0:
                    break
        except Exception as e:
            logger.warning(f"Redis delete_pattern error for {pattern}: {e}")
