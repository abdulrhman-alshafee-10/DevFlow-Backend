"""
app/core/rate_limit.py
──────────────────────
Rate limiting dependency for FastAPI using Redis.
Provides X-RateLimit-* headers and fails open (allows traffic) if Redis is down.
"""
import time
import logging
from typing import Callable

from fastapi import Request, Response

from app.exceptions import RateLimitError

from app.utils.redis import RedisManager
from app.utils.security import decode_access_token

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    FastAPI dependency for rate limiting.
    Fails open by default if Redis is unavailable.
    """
    def __init__(self, limit: int, window: int = 60, tier: str = "default"):
        self.limit = limit
        self.window = window
        self.tier = tier

    async def __call__(self, request: Request, response: Response):
        redis_client = RedisManager._client
        
        # Fail open if Redis is not connected
        if redis_client is None:
            return

        # Determine identifier: IP address or user ID if authenticated
        identifier = request.client.host if request.client else "unknown_ip"
        
        # Try to extract user ID if authenticated (Bearer token)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload = decode_access_token(token)
                sub = payload.get("sub")
                if sub:
                    identifier = f"user:{sub}"
            except Exception:
                pass # Fall back to IP if token is invalid

        key = f"rate_limit:{self.tier}:{identifier}"
        
        try:
            # Fixed window approach
            current = await redis_client.get(key)
            if current and int(current) >= self.limit:
                # Rate limit exceeded
                ttl = await redis_client.ttl(key)
                
                response.headers["X-RateLimit-Limit"] = str(self.limit)
                response.headers["X-RateLimit-Remaining"] = "0"
                response.headers["X-RateLimit-Reset"] = str(int(time.time()) + ttl)
                
                raise RateLimitError(
                    retry_after=ttl,
                    limit=self.limit,
                    remaining=0,
                    reset=int(time.time()) + ttl
                )
            
            # Increment and set expiry if new
            pipeline = redis_client.pipeline()
            pipeline.incr(key)
            if not current:
                pipeline.expire(key, self.window)
            
            results = await pipeline.execute()
            new_count = results[0]
            
            if not current:
                ttl = self.window
            else:
                ttl = await redis_client.ttl(key)

            # Add headers
            response.headers["X-RateLimit-Limit"] = str(self.limit)
            response.headers["X-RateLimit-Remaining"] = str(max(0, self.limit - new_count))
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + ttl)

        except RateLimitError:
            raise
        except Exception as e:
            # Fail open on Redis error
            logger.warning(f"Rate limiting error (failing open): {e}")
            pass
