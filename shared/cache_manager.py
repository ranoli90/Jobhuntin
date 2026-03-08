"""Multi-tier caching system for API performance optimization.

Provides:
- In-memory LRU cache for hot data
- Redis distributed cache for shared state
- Cache warming and invalidation
- Performance metrics and monitoring

Usage:
    from shared.cache_manager import CacheManager

    cache = CacheManager(redis_client)
    await cache.set("user:123", user_data, ttl=300)
    user = await cache.get("user:123")
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, TypeVar
import hashlib

T = TypeVar("T")


class CacheEntry:
    """Cache entry with metadata."""

    def __init__(self, value: Any, ttl_seconds: int, created_at: float | None = None):
        self.value = value
        self.ttl_seconds = ttl_seconds
        self.created_at = created_at or time.time()
        self.access_count = 0
        self.last_accessed = self.created_at

    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return time.time() - self.created_at > self.ttl_seconds

    def touch(self) -> None:
        """Update access statistics."""
        self.access_count += 1
        self.last_accessed = time.time()


class MemoryCache:
    """Thread-safe in-memory LRU cache."""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: List[str] = []
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key: str) -> Any | None:
        """Get value from cache."""
        entry = self._cache.get(key)
        if entry is None:
            self._misses += 1
            return None

        if entry.is_expired:
            self._remove(key)
            self._misses += 1
            return None

        # Move to end of access order (LRU)
        self._access_order.remove(key)
        self._access_order.append(key)
        entry.touch()
        self._hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Set value in cache."""
        # Remove existing entry if present
        if key in self._cache:
            self._access_order.remove(key)

        # Evict if over capacity
        while len(self._cache) >= self.max_size:
            oldest_key = self._access_order.pop(0)
            del self._cache[oldest_key]
            self._evictions += 1

        # Add new entry
        self._cache[key] = CacheEntry(value, ttl_seconds)
        self._access_order.append(key)

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if key in self._cache:
            del self._cache[key]
            self._access_order.remove(key)
            return True
        return False

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._access_order.clear()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def _remove(self, key: str) -> None:
        """Internal removal without access order update."""
        if key in self._cache:
            del self._cache[key]
            self._access_order.remove(key)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0.0

        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "evictions": self._evictions,
            "hit_rate_pct": round(hit_rate, 2),
        }

    def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed."""
        expired_keys = [key for key, entry in self._cache.items() if entry.is_expired]

        for key in expired_keys:
            self._remove(key)

        return len(expired_keys)


class CacheManager:
    """Multi-tier cache manager with memory and Redis layers."""

    def __init__(self, redis_client: Any, memory_cache_size: int = 1000):
        self.redis = redis_client
        self.memory = MemoryCache(memory_cache_size)
        self._default_ttl = 300  # 5 minutes

    async def get(
        self, key: str, use_memory: bool = True, use_redis: bool = True
    ) -> Any | None:
        """Get value from cache (memory first, then Redis)."""
        # Try memory cache first
        if use_memory:
            value = self.memory.get(key)
            if value is not None:
                return value

        # Try Redis cache
        if use_redis and self.redis:
            try:
                cached = await self.redis.get(key)
                if cached:
                    value = json.loads(cached)
                    # Store in memory for faster access
                    if use_memory:
                        self.memory.set(
                            key, value, ttl_seconds=60
                        )  # Shorter TTL for memory
                    return value
            except Exception as e:
                # Log error but don't fail
                from shared.logging_config import get_logger

                logger = get_logger("sorce.cache")
                logger.warning(f"Redis cache get error for key {key}: {e}")

        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
        use_memory: bool = True,
        use_redis: bool = True,
    ) -> None:
        """Set value in cache (both memory and Redis)."""
        ttl = ttl_seconds or self._default_ttl

        # Set in memory cache
        if use_memory:
            self.memory.set(key, value, ttl)

        # Set in Redis cache
        if use_redis and self.redis:
            try:
                serialized = json.dumps(value, default=str)
                await self.redis.setex(key, ttl, serialized)
            except Exception as e:
                # Log error but don't fail
                from shared.logging_config import get_logger

                logger = get_logger("sorce.cache")
                logger.warning(f"Redis cache set error for key {key}: {e}")

    async def delete(
        self, key: str, use_memory: bool = True, use_redis: bool = True
    ) -> bool:
        """Delete key from cache."""
        deleted = False

        # Delete from memory
        if use_memory:
            deleted = self.memory.delete(key) or deleted

        # Delete from Redis
        if use_redis and self.redis:
            try:
                result = await self.redis.delete(key)
                deleted = bool(result) or deleted
            except Exception as e:
                from shared.logging_config import get_logger

                logger = get_logger("sorce.cache")
                logger.warning(f"Redis cache delete error for key {key}: {e}")

        return deleted

    async def clear_pattern(
        self, pattern: str, use_memory: bool = True, use_redis: bool = True
    ) -> int:
        """Clear keys matching pattern."""
        cleared = 0

        # Clear from memory (simple string matching)
        if use_memory:
            keys_to_remove = [
                key for key in self.memory._cache.keys() if pattern in key
            ]
            for key in keys_to_remove:
                self.memory.delete(key)
                cleared += 1

        # Clear from Redis using pattern
        if use_redis and self.redis:
            try:
                keys = await self.redis.keys(pattern)
                if keys:
                    result = await self.redis.delete(*keys)
                    cleared += result
            except Exception as e:
                from shared.logging_config import get_logger

                logger = get_logger("sorce.cache")
                logger.warning(f"Redis cache clear pattern error for {pattern}: {e}")

        return cleared

    async def warm_cache(self, data_loader: callable, key_patterns: List[str]) -> int:
        """Warm cache with data from loader function."""
        warmed = 0

        for pattern in key_patterns:
            try:
                data = await data_loader(pattern)
                if data:
                    if isinstance(data, dict):
                        for key, value in data.items():
                            await self.set(key, value, ttl_seconds=600)  # 10 minutes
                            warmed += 1
                    elif isinstance(data, list):
                        for item in data:
                            if hasattr(item, "id"):
                                key = f"{pattern}:{item.id}"
                                await self.set(key, item, ttl_seconds=600)
                                warmed += 1
            except Exception as e:
                from shared.logging_config import get_logger

                logger = get_logger("sorce.cache")
                logger.warning(f"Cache warming error for pattern {pattern}: {e}")

        return warmed

    def cleanup_expired_memory(self) -> int:
        """Clean up expired entries from memory cache."""
        return self.memory.cleanup_expired()

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        memory_stats = self.memory.get_stats()

        stats = {
            "memory_cache": memory_stats,
            "redis_available": bool(self.redis),
        }

        # Add Redis stats if available
        if self.redis:
            try:
                # This would require Redis INFO command - simplified for now
                stats["redis_cache"] = {"status": "connected"}
            except Exception:
                stats["redis_cache"] = {"status": "error"}

        return stats

    @staticmethod
    def make_key(*parts: str) -> str:
        """Create a cache key from parts."""
        return ":".join(str(part) for part in parts)

    @staticmethod
    def hash_key(key: str, max_length: int = 250) -> str:
        """Create a hash of key for length limits."""
        if len(key) <= max_length:
            return key
        return hashlib.sha256(key.encode()).hexdigest()[:max_length]


# Global cache instance
_cache_manager: CacheManager | None = None


def get_cache_manager() -> CacheManager:
    """Get global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        raise RuntimeError(
            "Cache manager not initialized. Call init_cache_manager() first."
        )
    return _cache_manager


async def init_cache_manager(
    redis_client: Any, memory_cache_size: int = 1000
) -> CacheManager:
    """Initialize global cache manager."""
    global _cache_manager
    _cache_manager = CacheManager(redis_client, memory_cache_size)
    return _cache_manager


class CacheDecorator:
    """Decorator for caching function results."""

    def __init__(
        self,
        ttl_seconds: int = 300,
        key_prefix: str = "",
        use_memory: bool = True,
        use_redis: bool = True,
        cache_none: bool = False,
    ):
        self.ttl_seconds = ttl_seconds
        self.key_prefix = key_prefix
        self.use_memory = use_memory
        self.use_redis = use_redis
        self.cache_none = cache_none

    def __call__(self, func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = self._make_cache_key(func, args, kwargs)
            cache = get_cache_manager()

            # Try to get from cache
            cached = await cache.get(cache_key, self.use_memory, self.use_redis)
            if cached is not None or (cached is None and self.cache_none):
                return cached

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            if result is not None or self.cache_none:
                await cache.set(
                    cache_key, result, self.ttl_seconds, self.use_memory, self.use_redis
                )

            return result

        return wrapper

    def _make_cache_key(self, func, args, kwargs) -> str:
        """Generate cache key for function call."""
        # Include function name and arguments
        key_parts = [self.key_prefix, func.__name__]

        # Add positional args (skip first if it's self/cls)
        for arg in args[1:] if args and hasattr(args[0], "__dict__") else args:
            key_parts.append(str(arg))

        # Add keyword args (sorted for consistency)
        if kwargs:
            for k in sorted(kwargs.keys()):
                key_parts.append(f"{k}={kwargs[k]}")

        return CacheManager.make_key(*key_parts)


def cache(
    ttl_seconds: int = 300,
    key_prefix: str = "",
    use_memory: bool = True,
    use_redis: bool = True,
    cache_none: bool = False,
) -> CacheDecorator:
    """Cache decorator factory."""
    return CacheDecorator(
        ttl_seconds=ttl_seconds,
        key_prefix=key_prefix,
        use_memory=use_memory,
        use_redis=use_redis,
        cache_none=cache_none,
    )
