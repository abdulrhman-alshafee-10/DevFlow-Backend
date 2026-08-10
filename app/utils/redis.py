"""
app/utils/redis.py
──────────────────
Redis connection manager for caching, rate limiting, and token blacklisting.
"""

from typing import AsyncGenerator

import redis.asyncio as redis
from redis.asyncio.client import Redis

from app.config import get_settings

settings = get_settings()

class RedisManager:
    """Manages the Redis connection pool."""
    _client: Redis | None = None

    @classmethod
    async def init_redis(cls) -> None:
        if cls._client is None:
            cls._client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await cls._client.ping()

    @classmethod
    async def close(cls) -> None:
        if cls._client is not None:
            await cls._client.close()
            cls._client = None

    @classmethod
    def get_client(cls) -> Redis:
        if cls._client is None:
            raise RuntimeError("Redis client is not initialized")
        return cls._client

async def get_redis_client() -> AsyncGenerator[Redis, None]:
    """Dependency for injecting the Redis client."""
    yield RedisManager.get_client()
