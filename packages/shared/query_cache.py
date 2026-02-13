"""
Query result caching with Redis.

Provides caching for frequent database queries to reduce load and latency.
"""

from __future__ import annotations

import json
import hashlib
from typing import Any, TypeVar, Callable
from datetime import timedelta
import functools

from shared.logging_config import get_logger
from shared.redis_client import get_redis

logger = get_logger("sorce.cache")

T = TypeVar("T")

DEFAULT_TTL = timedelta(minutes=5)
PROFILE_TTL = timedelta(minutes=15)
JOB_LISTINGS_TTL = timedelta(minutes=2)
TENANT_CONFIG_TTL = timedelta(hours=1)


def _make_cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate a consistent cache key from function arguments."""
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    key_hash = hashlib.sha256(key_data.encode()).hexdigest()[:16]
    return f"cache:{prefix}:{key_hash}"


async def get_cached(key: str) -> Any | None:
    """Get a value from cache."""
    try:
        redis = await get_redis()
        data = await redis.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.warning(f"Cache get failed for {key}: {e}")
        return None


async def set_cached(key: str, value: Any, ttl: timedelta = DEFAULT_TTL) -> bool:
    """Set a value in cache with TTL."""
    try:
        redis = await get_redis()
        await redis.setex(key, int(ttl.total_seconds()), json.dumps(value, default=str))
        return True
    except Exception as e:
        logger.warning(f"Cache set failed for {key}: {e}")
        return False


async def delete_cached(key: str) -> bool:
    """Delete a value from cache."""
    try:
        redis = await get_redis()
        await redis.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Cache delete failed for {key}: {e}")
        return False


async def delete_pattern(pattern: str) -> int:
    """Delete all keys matching a pattern."""
    try:
        redis = await get_redis()
        keys = []
        async for key in redis.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            await redis.delete(*keys)
        return len(keys)
    except Exception as e:
        logger.warning(f"Cache pattern delete failed for {pattern}: {e}")
        return 0


def cached(
    prefix: str,
    ttl: timedelta = DEFAULT_TTL,
    key_builder: Callable | None = None,
):
    """
    Decorator for caching async function results.
    
    Usage:
        @cached("user_profile", ttl=PROFILE_TTL)
        async def get_user_profile(user_id: str) -> dict:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = _make_cache_key(prefix, *args, **kwargs)
            
            cached_result = await get_cached(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_result
            
            result = await func(*args, **kwargs)
            
            if result is not None:
                await set_cached(cache_key, result, ttl)
                logger.debug(f"Cache set: {cache_key}")
            
            return result
        return wrapper
    return decorator


class QueryCache:
    """Context manager for query caching with automatic invalidation."""
    
    def __init__(self, prefix: str, ttl: timedelta = DEFAULT_TTL):
        self.prefix = prefix
        self.ttl = ttl
    
    async def get_or_set(self, key: str, factory: Callable) -> Any:
        """Get from cache or compute and cache the result."""
        cache_key = f"{self.prefix}:{key}"
        cached = await get_cached(cache_key)
        if cached is not None:
            return cached
        
        result = await factory()
        if result is not None:
            await set_cached(cache_key, result, self.ttl)
        return result
    
    async def invalidate(self, key: str) -> bool:
        """Invalidate a specific cache key."""
        return await delete_cached(f"{self.prefix}:{key}")
    
    async def invalidate_all(self) -> int:
        """Invalidate all keys with this prefix."""
        return await delete_pattern(f"{self.prefix}:*")


# Pre-configured cache instances
profile_cache = QueryCache("profile", PROFILE_TTL)
job_cache = QueryCache("jobs", JOB_LISTINGS_TTL)
tenant_cache = QueryCache("tenant", TENANT_CONFIG_TTL)
