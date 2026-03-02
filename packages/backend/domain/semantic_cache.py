"""Semantic Cache for LLM Responses.

Caches LLM responses for semantically similar queries, reducing API calls and costs.
Uses embeddings to find similar cached queries rather than exact matches.

Features:
- Similarity-based cache hits (not exact match)
- Configurable similarity threshold
- Redis-backed for distributed caching
- TTL-based expiration
"""

from __future__ import annotations

import hashlib
import threading
import time
from collections import OrderedDict
from typing import Any

from pydantic import BaseModel
from shared.logging_config import get_logger

logger = get_logger("sorce.semantic_cache")


class CacheEntry(BaseModel):
    """A cached LLM response entry."""

    query: str
    query_embedding: list[float]
    response: dict[str, Any]
    model: str
    created_at: float
    hits: int = 0


class SemanticCache:
    """Semantic cache for LLM responses using embedding similarity.

    Unlike exact-match caches, this finds semantically similar queries
    and returns cached responses, reducing LLM API calls significantly.
    """

    def __init__(
        self,
        max_size: int = 500,
        ttl_seconds: int = 3600,  # 1 hour default
        similarity_threshold: float = 0.95,
    ):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.similarity_threshold = similarity_threshold
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.Lock()

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(a) != len(b):
            return 0.0

        dot_product = sum(x * y for x, y in zip(a, b, strict=False))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def _generate_key(self, query: str, model: str) -> str:
        """Generate a cache key from query and model."""
        query_hash = hashlib.sha256(f"{model}:{query}".encode()).hexdigest()[:16]
        return f"sem:{model}:{query_hash}"

    async def get(
        self,
        query: str,
        query_embedding: list[float],
        model: str,
    ) -> dict[str, Any] | None:
        """Get cached response for a semantically similar query.

        Searches through cached entries to find one with similar embedding.
        Returns None if no similar query found or if expired.
        """
        key_prefix = f"sem:{model}:"
        current_time = time.time()

        with self._lock:
            # First check for exact key match (fast path)
            exact_key = self._generate_key(query, model)
            if exact_key in self._cache:
                entry = self._cache[exact_key]
                if current_time - entry.created_at <= self.ttl_seconds:
                    entry.hits += 1
                    self._cache.move_to_end(exact_key)
                    logger.debug("Semantic cache exact hit for query")
                    return entry.response

            # Search for similar queries
            best_match: CacheEntry | None = None
            best_similarity = 0.0
            best_key: str | None = None

            for cache_key, entry in self._cache.items():
                if not cache_key.startswith(key_prefix):
                    continue

                # Check TTL
                if current_time - entry.created_at > self.ttl_seconds:
                    continue

                # Compute similarity
                similarity = self._cosine_similarity(
                    query_embedding, entry.query_embedding
                )

                if (
                    similarity >= self.similarity_threshold
                    and similarity > best_similarity
                ):
                    best_match = entry
                    best_similarity = similarity
                    best_key = cache_key

            if best_match:
                best_match.hits += 1
                self._cache.move_to_end(best_key)
                logger.debug(
                    f"Semantic cache hit with similarity {best_similarity:.3f}",
                    extra={"query_preview": query[:50]},
                )
                return best_match.response

        return None

    def set(
        self,
        query: str,
        query_embedding: list[float],
        response: dict[str, Any],
        model: str,
    ) -> None:
        """Cache a response for a query."""
        key = self._generate_key(query, model)

        with self._lock:
            # Remove oldest if at capacity
            while len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)

            self._cache[key] = CacheEntry(
                query=query,
                query_embedding=query_embedding,
                response=response,
                model=model,
                created_at=time.time(),
                hits=0,
            )

    def invalidate(self, query: str, model: str) -> None:
        """Remove cached response for query."""
        key = self._generate_key(query, model)

        with self._lock:
            if key in self._cache:
                del self._cache[key]

    def clear(self) -> None:
        """Clear all cached responses."""
        with self._lock:
            self._cache.clear()

    def stats(self) -> dict[str, Any]:
        """Return cache statistics."""
        with self._lock:
            total_hits = sum(e.hits for e in self._cache.values())
            entries = len(self._cache)
            return {
                "entries": entries,
                "max_size": self.max_size,
                "total_hits": total_hits,
                "similarity_threshold": self.similarity_threshold,
            }


class RedisSemanticCache(SemanticCache):
    """Redis-backed semantic cache for distributed environments.

    Stores embeddings and responses in Redis for cross-process sharing.
    """

    def __init__(
        self,
        max_size: int = 500,
        ttl_seconds: int = 3600,
        similarity_threshold: float = 0.95,
        redis_key_prefix: str = "sem_cache:",
    ):
        super().__init__(max_size, ttl_seconds, similarity_threshold)
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
            logger.warning("Redis unavailable, using in-memory semantic cache")
            return None

    async def get(
        self,
        query: str,
        query_embedding: list[float],
        model: str,
    ) -> dict[str, Any] | None:
        """Get cached response with Redis support."""
        # Try in-memory first (fast path)
        result = await super().get(query, query_embedding, model)
        if result:
            return result

        # Try Redis
        client = await self._get_redis()
        if not client:
            return None

        try:
            # Get all keys for this model
            pattern = f"{self.redis_key_prefix}{model}:*"
            keys = []
            async for key in client.scan_iter(match=pattern, count=100):
                keys.append(key)

            # Check each for similarity
            for redis_key in keys[:50]:  # Limit search
                data = await client.get(redis_key)
                if not data:
                    continue

                cached = CacheEntry.model_validate_json(data)

                # Check TTL (Redis handles this but double-check)
                if time.time() - cached.created_at > self.ttl_seconds:
                    continue

                # Check similarity
                similarity = self._cosine_similarity(
                    query_embedding, cached.query_embedding
                )
                if similarity >= self.similarity_threshold:
                    logger.debug(
                        f"Redis semantic cache hit with similarity {similarity:.3f}"
                    )

                    # Store in local cache too
                    self.set(query, query_embedding, cached.response, model)

                    return cached.response

        except Exception as e:
            logger.debug(f"Redis semantic cache get failed: {e}")

        return None

    async def set(
        self,
        query: str,
        query_embedding: list[float],
        response: dict[str, Any],
        model: str,
    ) -> None:
        """Cache response with Redis support."""
        # Store in-memory
        super().set(query, query_embedding, response, model)

        # Store in Redis
        client = await self._get_redis()
        if not client:
            return

        try:
            key = f"{self.redis_key_prefix}{model}:{hashlib.sha256(query.encode()).hexdigest()[:16]}"
            entry = CacheEntry(
                query=query,
                query_embedding=query_embedding,
                response=response,
                model=model,
                created_at=time.time(),
            )
            await client.setex(key, self.ttl_seconds, entry.model_dump_json())
        except Exception as e:
            logger.debug(f"Redis semantic cache set failed: {e}")


# Singleton instance
_semantic_cache: SemanticCache | None = None
_cache_lock = threading.Lock()


def get_semantic_cache() -> SemanticCache:
    """Get the global semantic cache instance."""
    global _semantic_cache

    with _cache_lock:
        if _semantic_cache is None:
            from shared.config import get_settings

            s = get_settings()

            if s.redis_url:
                _semantic_cache = RedisSemanticCache(
                    max_size=500,
                    ttl_seconds=3600,
                    similarity_threshold=0.95,
                )
            else:
                _semantic_cache = SemanticCache(
                    max_size=200,
                    ttl_seconds=3600,
                    similarity_threshold=0.95,
                )

        return _semantic_cache
