"""Embedding Cache for AI Operations.

Provides caching layer for embeddings to reduce API calls and latency.
Uses Redis when available, falls back to in-memory LRU cache.
"""

from __future__ import annotations

import hashlib
import threading
import time
from collections import OrderedDict

from shared.logging_config import get_logger

logger = get_logger("sorce.embedding_cache")


class EmbeddingCache:
    """LRU cache for text embeddings with TTL support.

    Features:
    - In-memory LRU cache with configurable size
    - Redis backend support for distributed caching
    - TTL-based expiration
    - Hash-based key generation for text content
    """

    def __init__(
        self,
        max_size: int = 1000,
        ttl_seconds: int = 86400,  # 24 hours default
    ):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, tuple[list[float], float]] = OrderedDict()
        self._lock = threading.Lock()

    def _generate_key(self, text: str, model: str = "default") -> str:
        """Generate a cache key from text content."""
        text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        return f"emb:{model}:{text_hash}"

    def get(self, text: str, model: str = "default") -> list[float] | None:
        """Get cached embedding for text.

        Returns None if not cached or expired.
        """
        key = self._generate_key(text, model)

        with self._lock:
            if key not in self._cache:
                return None

            embedding, timestamp = self._cache[key]

            # Check TTL
            if time.time() - timestamp > self.ttl_seconds:
                del self._cache[key]
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return embedding

    def set(self, text: str, embedding: list[float], model: str = "default") -> None:
        """Cache an embedding for text."""
        key = self._generate_key(text, model)

        with self._lock:
            # Remove oldest if at capacity
            while len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)

            self._cache[key] = (embedding, time.time())

    def invalidate(self, text: str, model: str = "default") -> None:
        """Remove cached embedding for text."""
        key = self._generate_key(text, model)

        with self._lock:
            if key in self._cache:
                del self._cache[key]

    def clear(self) -> None:
        """Clear all cached embeddings."""
        with self._lock:
            self._cache.clear()

    def size(self) -> int:
        """Return current cache size."""
        with self._lock:
            return len(self._cache)


class RedisEmbeddingCache(EmbeddingCache):
    """Redis-backed embedding cache for distributed environments.

    Falls back to in-memory LRU cache if Redis is unavailable.
    """

    def __init__(
        self,
        max_size: int = 1000,
        ttl_seconds: int = 86400,
        redis_key_prefix: str = "emb_cache:",
    ):
        super().__init__(max_size, ttl_seconds)
        self.redis_key_prefix = redis_key_prefix
        self._redis_available: bool | None = None

    async def _get_redis(self):
        """Get Redis client, caching availability status."""
        if self._redis_available is False:
            return None

        try:
            from shared.redis_client import get_redis

            client = await get_redis()
            await client.ping()
            self._redis_available = True
            return client
        except Exception:
            self._redis_available = False
            logger.warning("Redis unavailable, using in-memory cache")
            return None

    async def get_async(
        self, text: str, model: str = "default"
    ) -> list[float] | None:
        """Get cached embedding (async with Redis support)."""
        import json

        key = self._generate_key(text, model)

        # Try Redis first
        client = await self._get_redis()
        if client:
            try:
                redis_key = f"{self.redis_key_prefix}{key}"
                data = await client.get(redis_key)
                if data:
                    cached = json.loads(data)
                    return cached.get("embedding")
            except Exception as e:
                logger.debug(f"Redis get failed: {e}")

        # Fall back to in-memory
        return self.get(text, model)

    async def set_async(
        self, text: str, embedding: list[float], model: str = "default"
    ) -> None:
        """Cache an embedding (async with Redis support)."""
        import json

        key = self._generate_key(text, model)

        # Try Redis first
        client = await self._get_redis()
        if client:
            try:
                redis_key = f"{self.redis_key_prefix}{key}"
                data = json.dumps({"embedding": embedding, "model": model})
                await client.setex(redis_key, self.ttl_seconds, data)
            except Exception as e:
                logger.debug(f"Redis set failed: {e}")

        # Also store in-memory for fast local access
        self.set(text, embedding, model)


# Singleton instance
_embedding_cache: EmbeddingCache | None = None
_cache_lock = threading.Lock()


def get_embedding_cache() -> EmbeddingCache:
    """Get the global embedding cache instance."""
    global _embedding_cache

    with _cache_lock:
        if _embedding_cache is None:
            from shared.config import get_settings

            s = get_settings()

            if s.redis_url:
                _embedding_cache = RedisEmbeddingCache(
                    max_size=5000,
                    ttl_seconds=86400,  # 24 hours
                )
            else:
                _embedding_cache = EmbeddingCache(
                    max_size=1000,
                    ttl_seconds=86400,
                )

        return _embedding_cache
