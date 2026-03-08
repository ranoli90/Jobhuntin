"""Advanced database query caching and optimization system.

Provides:
- Multi-tier query caching
- Intelligent cache invalidation
- Cache warming strategies
- Performance monitoring
- Automatic cache optimization

Usage:
    from shared.db_query_cache import QueryCache

    cache = QueryCache()
    result = await cache.get_or_execute("SELECT * FROM users WHERE id = $1", [user_id])
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

import asyncpg

from shared.logging_config import get_logger
from shared.alerting import get_alert_manager

logger = get_logger("sorce.db_query_cache")


class CacheLevel(Enum):
    """Cache levels."""

    MEMORY = "memory"
    REDIS = "redis"
    DISK = "disk"


class CacheStrategy(Enum):
    """Cache invalidation strategies."""

    TTL = "ttl"  # Time-based
    LRU = "lru"  # Least recently used
    LFU = "lfu"  # Least frequently used
    WRITE_THROUGH = "write_through"
    WRITE_BEHIND = "write_behind"


@dataclass
class CacheEntry:
    """Cache entry data."""

    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int
    ttl_seconds: Optional[float]
    size_bytes: int
    query_hash: str
    table_dependencies: List[str]
    cache_level: CacheLevel
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheMetrics:
    """Cache performance metrics."""

    cache_level: CacheLevel
    total_entries: int
    total_size_mb: float
    hit_count: int
    miss_count: int
    hit_rate_pct: float
    avg_access_time_ms: float
    eviction_count: int
    invalidation_count: int
    last_cleanup: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class QueryCacheConfig:
    """Query cache configuration."""

    enabled: bool = True
    default_ttl_seconds: float = 300.0  # 5 minutes
    max_memory_size_mb: float = 512.0
    max_entries_per_level: int = 10000
    cleanup_interval_seconds: float = 60.0
    enable_redis: bool = False
    redis_url: Optional[str] = None
    enable_disk_cache: bool = False
    disk_cache_dir: str = "/tmp/db_cache"
    compression_enabled: bool = True
    compression_threshold_bytes: int = 1024
    auto_warm_enabled: bool = True
    warm_up_queries: List[str] = field(default_factory=list)


class QueryCache:
    """Advanced database query caching system."""

    def __init__(
        self,
        db_pool: asyncpg.Pool,
        config: Optional[QueryCacheConfig] = None,
        alert_manager: Optional[Any] = None,
    ):
        self.db_pool = db_pool
        self.config = config or QueryCacheConfig()
        self.alert_manager = alert_manager or get_alert_manager()

        # Cache storage
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.cache_metadata: Dict[str, Dict[str, Any]] = {}

        # Performance tracking
        self.metrics: Dict[CacheLevel, CacheMetrics] = {
            CacheLevel.MEMORY: CacheMetrics(
                cache_level=CacheLevel.MEMORY,
                total_entries=0,
                total_size_mb=0.0,
                hit_count=0,
                miss_count=0,
                hit_rate_pct=0.0,
                avg_access_time_ms=0.0,
                eviction_count=0,
                invalidation_count=0,
                last_cleanup=time.time(),
            )
        }

        # Cache management
        self.access_order: deque[str] = deque(maxlen=self.config.max_entries_per_level)
        self.frequency_counter: defaultdict[str, int] = defaultdict(int)
        self.table_dependencies: defaultdict[str, set] = defaultdict(set)

        # Background tasks
        self.cleanup_task: Optional[asyncio.Task] = None
        self.warm_up_task: Optional[asyncio.Task] = None

        # Statistics
        self.total_queries = 0
        self.cache_hits = 0
        self.cache_misses = 0

        self._lock = asyncio.Lock()

    async def get_or_execute(
        self,
        query: str,
        params: Optional[List[Any]] = None,
        ttl_seconds: Optional[float] = None,
        cache_level: CacheLevel = CacheLevel.MEMORY,
        force_refresh: bool = False,
    ) -> Any:
        """Get cached result or execute query."""
        if not self.config.enabled:
            return await self._execute_query(query, params)

        start_time = time.time()
        cache_key = self._generate_cache_key(query, params)

        try:
            # Check cache first
            if not force_refresh:
                cached_result = await self._get_from_cache(cache_key, cache_level)
                if cached_result is not None:
                    self.cache_hits += 1
                    await self._update_hit_metrics(
                        cache_level, time.time() - start_time
                    )
                    return cached_result

            # Cache miss - execute query
            self.cache_misses += 1
            result = await self._execute_query(query, params)

            # Store in cache
            await self._store_in_cache(
                cache_key, result, query, params, ttl_seconds, cache_level
            )

            await self._update_miss_metrics(cache_level, time.time() - start_time)
            return result

        except Exception as e:
            logger.error(f"Cache operation failed: {e}")
            # Fallback to direct query execution
            return await self._execute_query(query, params)

    async def _execute_query(
        self, query: str, params: Optional[List[Any]] = None
    ) -> Any:
        """Execute database query."""
        async with self.db_pool.acquire() as conn:
            if params:
                return await conn.fetch(query, *params)
            else:
                return await conn.fetch(query)

    def _generate_cache_key(
        self, query: str, params: Optional[List[Any]] = None
    ) -> str:
        """Generate cache key for query."""
        # Normalize query
        normalized_query = query.strip().lower()

        # Create hash
        hash_input = normalized_query
        if params:
            hash_input += json.dumps(params, sort_keys=True, default=str)

        return hashlib.sha256(hash_input.encode()).hexdigest()

    async def _get_from_cache(
        self, cache_key: str, cache_level: CacheLevel
    ) -> Optional[Any]:
        """Get value from specified cache level."""
        async with self._lock:
            if cache_level == CacheLevel.MEMORY:
                return await self._get_from_memory_cache(cache_key)
            elif cache_level == CacheLevel.REDIS and self.config.enable_redis:
                return await self._get_from_redis_cache(cache_key)
            elif cache_level == CacheLevel.DISK and self.config.enable_disk_cache:
                return await self._get_from_disk_cache(cache_key)

        return None

    async def _get_from_memory_cache(self, cache_key: str) -> Optional[Any]:
        """Get value from memory cache."""
        entry = self.memory_cache.get(cache_key)

        if entry is None:
            return None

        # Check TTL
        if entry.ttl_seconds and (time.time() - entry.created_at) > entry.ttl_seconds:
            await self._invalidate_memory_entry(cache_key)
            return None

        # Update access statistics
        entry.last_accessed = time.time()
        entry.access_count += 1
        self.frequency_counter[cache_key] += 1

        # Update access order for LRU
        if cache_key in self.access_order:
            self.access_order.remove(cache_key)
        self.access_order.append(cache_key)

        return entry.value

    async def _get_from_redis_cache(self, cache_key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        try:
            import redis

            redis_client = redis.from_url(self.config.redis_url)
            cached_data = redis_client.get(cache_key)

            if cached_data:
                # Deserialize and return
                return json.loads(cached_data)

        except Exception as e:
            logger.error(f"Redis cache error: {e}")

        return None

    async def _get_from_disk_cache(self, cache_key: str) -> Optional[Any]:
        """Get value from disk cache."""
        try:
            import os

            cache_file = os.path.join(self.config.disk_cache_dir, f"{cache_key}.cache")

            if os.path.exists(cache_file):
                with open(cache_file, "rb") as f:
                    data = f.read()

                # Check TTL (stored in metadata)
                metadata = self.cache_metadata.get(cache_key, {})
                if (
                    metadata.get("ttl_seconds")
                    and (time.time() - metadata.get("created_at", 0))
                    > metadata["ttl_seconds"]
                ):
                    os.remove(cache_file)
                    return None

                # Deserialize
                if (
                    self.config.compression_enabled
                    and len(data) > self.config.compression_threshold_bytes
                ):
                    import gzip

                    data = gzip.decompress(data)

                return json.loads(data.decode())

        except Exception as e:
            logger.error(f"Disk cache error: {e}")

        return None

    async def _store_in_cache(
        self,
        cache_key: str,
        value: Any,
        query: str,
        params: Optional[List[Any]],
        ttl_seconds: Optional[float],
        cache_level: CacheLevel,
    ) -> None:
        """Store value in specified cache level."""
        ttl_seconds = ttl_seconds or self.config.default_ttl_seconds

        # Extract table dependencies
        table_deps = self._extract_table_dependencies(query)

        # Serialize value
        serialized_value = json.dumps(value, default=str)
        size_bytes = len(serialized_value.encode())

        # Create cache entry
        entry = CacheEntry(
            key=cache_key,
            value=value,
            created_at=time.time(),
            last_accessed=time.time(),
            access_count=1,
            ttl_seconds=ttl_seconds,
            size_bytes=size_bytes,
            query_hash=hashlib.sha256(query.encode()).hexdigest(),
            table_dependencies=table_deps,
            cache_level=cache_level,
            metadata={
                "query": query,
                "params": params or [],
                "original_size_bytes": size_bytes,
            },
        )

        # Store in appropriate cache level
        if cache_level == CacheLevel.MEMORY:
            await self._store_in_memory_cache(entry)
        elif cache_level == CacheLevel.REDIS and self.config.enable_redis:
            await self._store_in_redis_cache(entry)
        elif cache_level == CacheLevel.DISK and self.config.enable_disk_cache:
            await self._store_in_disk_cache(entry)

        # Update table dependencies
        for table in table_deps:
            self.table_dependencies[table].add(cache_key)

    async def _store_in_memory_cache(self, entry: CacheEntry) -> None:
        """Store entry in memory cache."""
        # Check memory limits
        await self._enforce_memory_limits()

        # Store entry
        self.memory_cache[entry.key] = entry

        # Update access order
        self.access_order.append(entry.key)
        self.frequency_counter[entry.key] = 1

        # Update metrics
        metrics = self.metrics[CacheLevel.MEMORY]
        metrics.total_entries = len(self.memory_cache)
        metrics.total_size_mb = (
            sum(e.size_bytes for e in self.memory_cache.values()) / 1024 / 1024
        )

    async def _store_in_redis_cache(self, entry: CacheEntry) -> None:
        """Store entry in Redis cache."""
        try:
            import redis

            redis_client = redis.from_url(self.config.redis_url)

            # Serialize with TTL
            serialized_data = json.dumps(entry.value, default=str)

            if entry.ttl_seconds:
                redis_client.setex(entry.key, int(entry.ttl_seconds), serialized_data)
            else:
                redis_client.set(entry.key, serialized_data)

        except Exception as e:
            logger.error(f"Redis store error: {e}")

    async def _store_in_disk_cache(self, entry: CacheEntry) -> None:
        """Store entry in disk cache."""
        try:
            import os
            import gzip

            os.makedirs(self.config.disk_cache_dir, exist_ok=True)
            cache_file = os.path.join(self.config.disk_cache_dir, f"{entry.key}.cache")

            # Serialize
            serialized_data = json.dumps(entry.value, default=str).encode()

            # Compress if needed
            if (
                self.config.compression_enabled
                and len(serialized_data) > self.config.compression_threshold_bytes
            ):
                serialized_data = gzip.compress(serialized_data)

            # Write to disk
            with open(cache_file, "wb") as f:
                f.write(serialized_data)

            # Store metadata
            self.cache_metadata[entry.key] = {
                "created_at": entry.created_at,
                "ttl_seconds": entry.ttl_seconds,
                "size_bytes": len(serialized_data),
                "table_dependencies": entry.table_dependencies,
            }

        except Exception as e:
            logger.error(f"Disk store error: {e}")

    def _extract_table_dependencies(self, query: str) -> List[str]:
        """Extract table names from query."""
        import re

        # Simple regex patterns for table extraction
        patterns = [
            r"FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            r"JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            r"UPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            r"INSERT\s+INTO\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            r"DELETE\s+FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        ]

        tables = set()
        query_lower = query.lower()

        for pattern in patterns:
            matches = re.findall(pattern, query_lower, re.IGNORECASE)
            tables.update(matches)

        # Filter out system tables
        return [
            table
            for table in tables
            if not table.startswith(("pg_", "information_schema"))
        ]

    async def _enforce_memory_limits(self) -> None:
        """Enforce memory cache limits."""
        current_size = (
            sum(e.size_bytes for e in self.memory_cache.values()) / 1024 / 1024
        )
        current_entries = len(self.memory_cache)

        # Check size limit
        if current_size > self.config.max_memory_size_mb:
            await self._evict_by_size(current_size - self.config.max_memory_size_mb)

        # Check entry limit
        if current_entries > self.config.max_entries_per_level:
            await self._evict_by_count(
                current_entries - self.config.max_entries_per_level
            )

    async def _evict_by_size(self, size_to_free_mb: float) -> None:
        """Evict entries to free memory."""
        size_to_free_bytes = int(size_to_free_mb * 1024 * 1024)
        freed_bytes = 0

        # Sort by LRU (least recently used)
        sorted_entries = sorted(
            self.memory_cache.values(), key=lambda e: e.last_accessed
        )

        for entry in sorted_entries:
            if freed_bytes >= size_to_free_bytes:
                break

            await self._invalidate_memory_entry(entry.key)
            freed_bytes += entry.size_bytes

    async def _evict_by_count(self, count_to_remove: int) -> None:
        """Evict entries by count."""
        removed = 0

        # Sort by LRU
        for cache_key in list(self.access_order):
            if removed >= count_to_remove:
                break

            await self._invalidate_memory_entry(cache_key)
            removed += 1

    async def _invalidate_memory_entry(self, cache_key: str) -> None:
        """Invalidate memory cache entry."""
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]

            # Remove from cache
            del self.memory_cache[cache_key]

            # Remove from access order
            if cache_key in self.access_order:
                self.access_order.remove(cache_key)

            # Remove from frequency counter
            self.frequency_counter.pop(cache_key, None)

            # Update metrics
            metrics = self.metrics[CacheLevel.MEMORY]
            metrics.eviction_count += 1
            metrics.total_entries = len(self.memory_cache)
            metrics.total_size_mb = (
                sum(e.size_bytes for e in self.memory_cache.values()) / 1024 / 1024
            )

    async def invalidate_by_table(self, table_name: str) -> int:
        """Invalidate cache entries dependent on a table."""
        invalidated_count = 0

        if table_name in self.table_dependencies:
            cache_keys = self.table_dependencies[table_name].copy()

            for cache_key in cache_keys:
                await self.invalidate(cache_key)
                invalidated_count += 1

            # Clear table dependencies
            self.table_dependencies[table_name].clear()

        return invalidated_count

    async def invalidate(self, cache_key: str) -> bool:
        """Invalidate specific cache entry."""
        invalidated = False

        # Invalidate from all cache levels
        if cache_key in self.memory_cache:
            await self._invalidate_memory_entry(cache_key)
            invalidated = True

        # Redis invalidation
        if self.config.enable_redis:
            try:
                import redis

                redis_client = redis.from_url(self.config.redis_url)
                if redis_client.delete(cache_key):
                    invalidated = True
            except Exception as e:
                logger.error(f"Redis invalidation error: {e}")

        # Disk invalidation
        if self.config.enable_disk_cache:
            try:
                import os

                cache_file = os.path.join(
                    self.config.disk_cache_dir, f"{cache_key}.cache"
                )
                if os.path.exists(cache_file):
                    os.remove(cache_file)
                    invalidated = True

                # Remove metadata
                self.cache_metadata.pop(cache_key, None)
            except Exception as e:
                logger.error(f"Disk invalidation error: {e}")

        if invalidated:
            metrics = self.metrics[CacheLevel.MEMORY]
            metrics.invalidation_count += 1

        return invalidated

    async def invalidate_all(self) -> int:
        """Invalidate all cache entries."""
        invalidated_count = 0

        # Clear memory cache
        memory_count = len(self.memory_cache)
        self.memory_cache.clear()
        self.access_order.clear()
        self.frequency_counter.clear()
        invalidated_count += memory_count

        # Clear Redis cache
        if self.config.enable_redis:
            try:
                import redis

                redis_client = redis.from_url(self.config.redis_url)
                redis_count = redis_client.flushdb()
                invalidated_count += redis_count
            except Exception as e:
                logger.error(f"Redis clear error: {e}")

        # Clear disk cache
        if self.config.enable_disk_cache:
            try:
                import os
                import shutil

                if os.path.exists(self.config.disk_cache_dir):
                    shutil.rmtree(self.config.disk_cache_dir)
                    os.makedirs(self.config.disk_cache_dir, exist_ok=True)

                disk_count = len(self.cache_metadata)
                self.cache_metadata.clear()
                invalidated_count += disk_count
            except Exception as e:
                logger.error(f"Disk clear error: {e}")

        # Clear table dependencies
        self.table_dependencies.clear()

        # Update metrics
        for metrics in self.metrics.values():
            metrics.invalidation_count += 1
            metrics.total_entries = 0
            metrics.total_size_mb = 0.0

        return invalidated_count

    async def warm_up_cache(self) -> Dict[str, Any]:
        """Warm up cache with predefined queries."""
        if not self.config.auto_warm_enabled or not self.config.warm_up_queries:
            return {"warmed_queries": 0, "errors": []}

        warmed_count = 0
        errors = []

        for query_config in self.config.warm_up_queries:
            try:
                if isinstance(query_config, str):
                    query = query_config
                    params = None
                    ttl = None
                else:
                    query = query_config.get("query")
                    params = query_config.get("params")
                    ttl = query_config.get("ttl")

                # Execute and cache
                await self.get_or_execute(query, params, ttl)
                warmed_count += 1

            except Exception as e:
                errors.append(f"Query warm-up failed: {query[:50]}... - {str(e)}")
                logger.error(f"Cache warm-up error: {e}")

        return {
            "warmed_queries": warmed_count,
            "total_queries": len(self.config.warm_up_queries),
            "errors": errors,
        }

    async def _update_hit_metrics(
        self, cache_level: CacheLevel, access_time_ms: float
    ) -> None:
        """Update hit metrics."""
        metrics = self.metrics.get(cache_level)
        if metrics:
            metrics.hit_count += 1

            # Update average access time
            if metrics.avg_access_time_ms == 0:
                metrics.avg_access_time_ms = access_time_ms
            else:
                metrics.avg_access_time_ms = (metrics.avg_access_time_ms * 0.9) + (
                    access_time_ms * 0.1
                )

            # Update hit rate
            total_requests = metrics.hit_count + metrics.miss_count
            if total_requests > 0:
                metrics.hit_rate_pct = (metrics.hit_count / total_requests) * 100

    async def _update_miss_metrics(
        self, cache_level: CacheLevel, access_time_ms: float
    ) -> None:
        """Update miss metrics."""
        metrics = self.metrics.get(cache_level)
        if metrics:
            metrics.miss_count += 1

            # Update hit rate
            total_requests = metrics.hit_count + metrics.miss_count
            if total_requests > 0:
                metrics.hit_rate_pct = (metrics.hit_count / total_requests) * 100

    async def cleanup_expired_entries(self) -> int:
        """Clean up expired cache entries."""
        cleaned_count = 0
        current_time = time.time()

        # Clean memory cache
        expired_keys = []
        for cache_key, entry in self.memory_cache.items():
            if (
                entry.ttl_seconds
                and (current_time - entry.created_at) > entry.ttl_seconds
            ):
                expired_keys.append(cache_key)

        for cache_key in expired_keys:
            await self._invalidate_memory_entry(cache_key)
            cleaned_count += 1

        # Clean disk cache
        if self.config.enable_disk_cache:
            try:
                import os

                for cache_key, metadata in list(self.cache_metadata.items()):
                    if (
                        metadata.get("ttl_seconds")
                        and (current_time - metadata.get("created_at", 0))
                        > metadata["ttl_seconds"]
                    ):
                        cache_file = os.path.join(
                            self.config.disk_cache_dir, f"{cache_key}.cache"
                        )
                        if os.path.exists(cache_file):
                            os.remove(cache_file)

                        del self.cache_metadata[cache_key]
                        cleaned_count += 1

            except Exception as e:
                logger.error(f"Disk cleanup error: {e}")

        # Update metrics
        for metrics in self.metrics.values():
            metrics.last_cleanup = current_time

        return cleaned_count

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        stats = {
            "enabled": self.config.enabled,
            "total_queries": self.total_queries,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "overall_hit_rate_pct": (self.cache_hits / max(self.total_queries, 1))
            * 100,
            "cache_levels": {},
        }

        for cache_level, metrics in self.metrics.items():
            stats["cache_levels"][cache_level.value] = {
                "total_entries": metrics.total_entries,
                "total_size_mb": metrics.total_size_mb,
                "hit_count": metrics.hit_count,
                "miss_count": metrics.miss_count,
                "hit_rate_pct": metrics.hit_rate_pct,
                "avg_access_time_ms": metrics.avg_access_time_ms,
                "eviction_count": metrics.eviction_count,
                "invalidation_count": metrics.invalidation_count,
                "last_cleanup": metrics.last_cleanup,
            }

        return stats

    async def start_background_tasks(self) -> None:
        """Start background cache management tasks."""
        # Cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())

        # Warm-up task
        if self.config.auto_warm_enabled:
            self.warm_up_task = asyncio.create_task(self._warm_up_loop())

    async def stop_background_tasks(self) -> None:
        """Stop background cache management tasks."""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            self.cleanup_task = None

        if self.warm_up_task:
            self.warm_up_task.cancel()
            self.warm_up_task = None

    async def _cleanup_loop(self) -> None:
        """Background cleanup loop."""
        while True:
            try:
                await self.cleanup_expired_entries()
                await asyncio.sleep(self.config.cleanup_interval_seconds)
            except Exception as e:
                logger.error(f"Cache cleanup loop error: {e}")
                await asyncio.sleep(self.config.cleanup_interval_seconds)

    async def _warm_up_loop(self) -> None:
        """Background warm-up loop."""
        # Run warm-up once at startup, then periodically
        await self.warm_up_cache()

        while True:
            try:
                await asyncio.sleep(3600)  # Warm up every hour
                await self.warm_up_cache()
            except Exception as e:
                logger.error(f"Cache warm-up loop error: {e}")
                await asyncio.sleep(3600)


# Global query cache instance
_query_cache: QueryCache | None = None


def get_query_cache() -> QueryCache:
    """Get global query cache instance."""
    global _query_cache
    if _query_cache is None:
        raise RuntimeError(
            "Query cache not initialized. Call init_query_cache() first."
        )
    return _query_cache


async def init_query_cache(
    db_pool: asyncpg.Pool,
    config: Optional[QueryCacheConfig] = None,
    alert_manager: Optional[Any] = None,
) -> QueryCache:
    """Initialize global query cache."""
    global _query_cache
    _query_cache = QueryCache(db_pool, config, alert_manager)
    await _query_cache.start_background_tasks()
    return _query_cache
