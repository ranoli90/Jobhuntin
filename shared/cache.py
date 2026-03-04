import functools
import json
import logging
from collections.abc import Callable

from shared.redis_client import get_redis

logger = logging.getLogger(__name__)

def redis_cache(ttl_seconds: int = 300, key_prefix: str = "cache"):
    """Async decorator to cache function results in Redis.
    Handles basic types that are JSON serializable.
    Falls back to executing the function if Redis is unavailable.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                redis = await get_redis()
                # Construct key from prefix, function name, and stringified args
                # Note: This is a simple implementation. Complex objects in args might need better serialization.
                key_parts = [key_prefix, func.__name__]
                for arg in args:
                    # Skip 'self' or 'cls' if it looks like an instance/class (naive check)
                    if hasattr(arg, "__dict__"):
                        continue
                    key_parts.append(str(arg))

                # Sort kwargs for stability
                for k, v in sorted(kwargs.items()):
                    key_parts.append(f"{k}={v}")

                key = ":".join(key_parts)

                cached = await redis.get(key)
                if cached:
                    try:
                        return json.loads(cached)
                    except json.JSONDecodeError:
                        pass # Valid cache, but invalid JSON? Recompute.

                result = await func(*args, **kwargs)

                # Only cache if not None (and maybe check serializability)
                if result is not None:
                    try:
                        await redis.set(key, json.dumps(result), ex=ttl_seconds)
                    except Exception as e:
                        logger.warning(f"Failed to cache result for {key}: {e}")

                return result
            except Exception as e:
                # Fallback: execute function without caching if Redis fails
                logger.warning(f"Redis cache error for {func.__name__}: {e}")
                return await func(*args, **kwargs)
        return wrapper
    return decorator
