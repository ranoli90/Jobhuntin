"""Cache stampede protection using probabilistic early expiration.

Prevents cache stampedes when many requests try to refresh the same cache key
simultaneously after expiration.
"""

from __future__ import annotations

import asyncio
import random
import time
from typing import Any, Callable

from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.cache")


async def get_with_stampede_protection(
    cache_key: str,
    fetch_func: Callable[[], Any],
    ttl: int,
    early_refresh_probability: float = 0.1,
    redis_client: Any = None,
) -> Any:
    """Get value from cache with stampede protection.
    
    Args:
        cache_key: Cache key
        fetch_func: Async function to fetch fresh value if cache miss
        ttl: Time to live in seconds
        early_refresh_probability: Probability of early refresh (0.0-1.0)
        redis_client: Redis client (optional, falls back to get_redis)
    
    Returns:
        Cached or freshly fetched value
    """
    if redis_client is None:
        try:
            from shared.redis_client import get_redis
            redis_client = await get_redis()
        except Exception:
            logger.warning("Redis not available, skipping cache")
            return await fetch_func()
    
    try:
        # Try to get from cache
        cached = await redis_client.get(cache_key)
        if cached:
            try:
                import json
                data = json.loads(cached)
                value = data.get("value")
                expires_at = data.get("expires_at", 0)
                
                # Check if expired
                now = time.time()
                if expires_at > now:
                    # Check for early refresh (probabilistic)
                    time_until_expiry = expires_at - now
                    if time_until_expiry < ttl * 0.2:  # Last 20% of TTL
                        if random.random() < early_refresh_probability:
                            # Trigger background refresh
                            logger.debug(f"Early refresh triggered for {cache_key}")
                            asyncio.create_task(_refresh_cache(cache_key, fetch_func, ttl, redis_client))
                            incr("cache.stampede.early_refresh")
                    
                    return value
                else:
                    # Expired, need to refresh
                    logger.debug(f"Cache expired for {cache_key}, refreshing")
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.warning(f"Failed to parse cache value for {cache_key}: {e}")
        
        # Cache miss or expired - fetch fresh value
        # Use lock to prevent stampede
        lock_key = f"{cache_key}:lock"
        lock_acquired = await redis_client.set(lock_key, "1", nx=True, ex=30)
        
        if lock_acquired:
            # We got the lock, fetch fresh value
            try:
                value = await fetch_func()
                # Store in cache
                expires_at = time.time() + ttl
                cache_data = {
                    "value": value,
                    "expires_at": expires_at,
                }
                import json
                await redis_client.setex(
                    cache_key,
                    ttl,
                    json.dumps(cache_data)
                )
                incr("cache.stampede.refresh")
                return value
            finally:
                await redis_client.delete(lock_key)
        else:
            # Another request is refreshing, wait and retry
            await asyncio.sleep(0.1)
            retry_cached = await redis_client.get(cache_key)
            if retry_cached:
                try:
                    import json
                    data = json.loads(retry_cached)
                    return data.get("value")
                except (json.JSONDecodeError, KeyError, TypeError):
                    pass
            
            # If still no cache, fetch directly (fallback)
            logger.warning(f"Cache lock timeout for {cache_key}, fetching directly")
            incr("cache.stampede.fallback")
            return await fetch_func()
            
    except Exception as e:
        logger.warning(f"Cache error for {cache_key}: {e}")
        # Fallback to direct fetch
        return await fetch_func()


async def _refresh_cache(
    cache_key: str,
    fetch_func: Callable[[], Any],
    ttl: int,
    redis_client: Any,
) -> None:
    """Background task to refresh cache."""
    try:
        value = await fetch_func()
        expires_at = time.time() + ttl
        cache_data = {
            "value": value,
            "expires_at": expires_at,
        }
        import json
        await redis_client.setex(
            cache_key,
            ttl,
            json.dumps(cache_data)
        )
        logger.debug(f"Background refresh completed for {cache_key}")
    except Exception as e:
        logger.warning(f"Background refresh failed for {cache_key}: {e}")
