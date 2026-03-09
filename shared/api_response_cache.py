"""Advanced API response caching system with multiple cache layers.

Provides:
- Multi-tier caching (memory, Redis, disk)
- Intelligent cache invalidation
- Cache warming strategies
- Performance optimization
- Analytics and monitoring

Usage:
    from shared.api_response_cache import ResponseCache

    cache = ResponseCache()
    await cache.get_or_set("api:users:123", user_data)
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

import redis.asyncio as redis

from shared.logging_config import get_logger
from shared.alerting import get_alert_manager

logger = get_logger("sorce.api_cache")


class CacheLevel(Enum):
    """Cache storage levels."""

    MEMORY = "memory"
    REDIS = "redis"
    DISK = "disk"


class CacheStrategy(Enum):
    """Cache invalidation strategies."""

    TTL = "ttl"
    LRU = "lru"
    LFU = "lfu"
    MANUAL = "manual"
    WRITE_THROUGH = "write_through"
    WRITE_BEHIND = "write_behind"


@dataclass
class CacheEntry:
    """Cache entry data."""

    key: str
    value: Any
    content_type: str
    content_encoding: str
    size_bytes: int
    created_at: float
    last_accessed: float
    access_count: int
    ttl_seconds: Optional[float] = None
    expires_at: Optional[float] = None
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
    avg_ttl_seconds: float
    peak_usage: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class CacheConfig:
    """Cache configuration."""

    default_ttl_seconds: float = 300.0  # 5 minutes
    max_memory_entries: int = 10000
    max_memory_size_mb: float = 512.0  # 512MB
    max_redis_size_mb: float = 1024.0  # 1GB
    max_disk_size_mb: float = 10240.0  # 10GB
    enable_redis: bool = True
    enable_disk: bool = False
    enable_compression: bool = True
    compression_threshold_bytes: int = 1024
    cleanup_interval_seconds: float = 300.0
    warming_enabled: bool = True
    warming_batch_size: int = 100

    # Cache strategy
    memory_strategy: CacheStrategy = CacheStrategy.LRU
    redis_strategy: CacheStrategy = CacheStrategy.LRU
    disk_strategy = CacheStrategy.LRU

    # Performance thresholds
    high_memory_usage_pct: float = 80.0
    high_redis_usage_pct: float = 80.0
    high_disk_usage_pct: float = 80.0
    slow_access_time_ms: float = 100.0


class ResponseCache:
    """Advanced API response caching system."""

    def __init__(
        self,
        redis_client: Optional[redis.asyncio.Redis] = None,
        config: Optional[CacheConfig] = None,
        alert_manager: Optional[Any] = None,
    ):
        self.redis_client = redis_client
        self.config = config or CacheConfig()
        self.alert_manager = alert_manager or get_alert_manager()

        # Cache storage
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.redis_cache: Dict[str, CacheEntry] = {}
        self.disk_cache: Dict[str, CacheEntry] = {}

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
                avg_ttl_seconds=0.0,
                peak_usage=0.0,
            ),
            CacheLevel.REDIS: CacheMetrics(
                cache_level=CacheLevel.REDIS,
                total_entries=0,
                total_size_mb=0.0,
                hit_count=0,
                miss_count=0,
                hit_rate_pct=0.0,
                avg_access_time_ms=0.0,
                eviction_count=0,
                invalidation_count=0,
                avg_ttl_seconds=0.0,
                peak_usage=0.0,
            ),
            CacheLevel.DISK: CacheMetrics(
                cache_level=CacheLevel.DISK,
                total_entries=0,
                total_size_mb=0.0,
                hit_count=0,
                miss_count=0,
                hit_rate_pct=0.0,
                avg_access_time_ms=0.0,
                eviction_count=0,
                invalidation_count=0,
                avg_ttl_seconds=0.0,
                peak_usage=0.0,
            ),
        }

        # Access tracking
        self.access_order: deque[str] = deque(maxlen=self.config.max_memory_entries)
        self.frequency_counter: defaultdict(int)
        self.last_access: Dict[str, float] = {}

        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._warming_task: Optional[asyncio.Task] = None

        self._lock = asyncio.Lock()

    async def get(
        self,
        key: str,
        default: Any = None,
        ttl_seconds: Optional[float] = None,
        cache_level: Optional[CacheLevel] = None,
        force_refresh: bool = False,
    ) -> Any:
        """Get value from cache or set default."""
        # Determine cache level
        if cache_level is None:
            cache_level = self._select_cache_level(key)

        # Check cache at specified level
        if cache_level == CacheLevel.MEMORY:
            return await self._get_from_memory_cache(key, default, force_refresh)
        elif cache_level == CacheLevel.REDIS:
            return await self._get_from_redis_cache(key, default, force_refresh)
        elif cache_level == CacheLevel.DISK:
            return await self._get_from_disk_cache(key, default, force_refresh)
        else:
            return default

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[float] = None,
        cache_level: Optional[CacheLevel] = None,
        content_type: str = "application/json",
        content_encoding: str = "utf-8",
    ) -> None:
        """Set value in cache."""
        # Determine cache level
        if cache_level is None:
            cache_level = self._select_cache_level(key)

        # Serialize value
        if value is None:
            return

        try:
            serialized_value = json.dumps(value, default=str)
        except (TypeError, ValueError):
            serialized_value = str(value)

        # Calculate size
        size_bytes = len(serialized_value.encode(content_encoding))

        # Apply compression if enabled
        if (
            self.config.enable_compression
            and size_bytes > self.config.compression_threshold_bytes
            and cache_level != CacheLevel.MEMORY
        ):
            try:
                import gzip

                compressed_value = gzip.compress(serialized_value)
                serialized_value = compressed_value
                content_encoding = "gzip"
                size_bytes = len(compressed_value)
            except Exception as e:
                logger.warning(f"Compression failed for {key}: {e}")

        # Create cache entry
        entry = CacheEntry(
            key=key,
            value=value,
            content_type=content_type,
            content_encoding=content_encoding,
            size_bytes=size_bytes,
            created_at=time.time(),
            last_accessed=time.time(),
            access_count=1,
            ttl_seconds=ttl_seconds or self.config.default_ttl_seconds,
            expires_at=None if ttl_seconds is None else time.time() + ttl_seconds,
            cache_level=cache_level,
        )

        # Store in appropriate cache level
        if cache_level == CacheLevel.MEMORY:
            await self._store_in_memory_cache(entry)
        elif cache_level == CacheLevel.REDIS:
            await self._store_in_redis_cache(entry)
        elif cache_level == CacheLevel.DISK:
            await self._store_in_disk_cache(entry)

        logger.debug(f"Cached value in {cache_level.value}: {key}")

    async def delete(self, key: str, cache_level: Optional[CacheLevel] = None) -> bool:
        """Delete entry from cache."""
        # Determine cache level
        if cache_level is None:
            # Try all levels in order: memory -> redis -> disk
            for level in [CacheLevel.MEMORY, CacheLevel.REDIS, CacheLevel.DISK]:
                if await self._delete_from_cache_level(key, level):
                    logger.debug(f"Deleted {key} from {level.value} cache")
                    return True
            return False
        else:
            return await self._delete_from_cache_level(key, cache_level)

    async def invalidate(
        self, pattern: str, cache_level: Optional[CacheLevel] = None
    ) -> int:
        """Invalidate entries matching pattern."""
        invalidated_count = 0

        if cache_level is None:
            # Invalidate from all levels
            levels = [CacheLevel.MEMORY, CacheLevel.REDIS, CacheLevel.DISK]
        else:
            levels = [cache_level]

        for level in levels:
            try:
                if level == CacheLevel.MEMORY:
                    keys_to_remove = [
                        key for key in self.memory_cache.keys() if pattern in key
                    ]
                elif level == CacheLevel.REDIS:
                    keys_to_remove = [
                        key for key in self.redis_cache.keys() if pattern in key
                    ]
                elif level == CacheLevel.DISK:
                    keys_to_remove = [
                        key for key in self.disk_cache.keys() if pattern in key
                    ]

                for key in keys_to_remove:
                    await self._delete_from_cache_level(key, level)
                    invalidated_count += 1

            except Exception as e:
                logger.error(f"Failed to invalidate from {level.value} cache: {e}")

        return invalidated_count

    async def _select_cache_level(self, key: str) -> CacheLevel:
        """Select appropriate cache level based on key."""
        # Check if key suggests specific level
        if key.startswith("session:"):
            return CacheLevel.MEMORY
        elif key.startswith("api:"):
            return CacheLevel.REDIS if self.config.enable_redis else CacheLevel.MEMORY
        elif key.startswith("static:"):
            return CacheLevel.DISK if self.config.enable_disk else CacheLevel.MEMORY
        else:
            return CacheLevel.MEMORY

    async def _get_from_memory_cache(
        self, key: str, default: Any, force_refresh: bool = False
    ) -> Any:
        """Get value from memory cache."""
        entry = self.memory_cache.get(key)

        if entry is None:
            return default

        # Check TTL
        if entry.expires_at and time.time() > entry.expires_at:
            await self._delete_from_cache_level(key, CacheLevel.MEMORY)
            return default

        # Update access statistics
        entry.last_accessed = time.time()
        entry.access_count += 1
        self.access_order.remove(key)
        self.access_order.append(key)
        self.frequency_counter[key] += 1
        self.last_access[key] = time.time()

        # Update metrics
        metrics = self.metrics[CacheLevel.MEMORY]
        metrics.hit_count += 1
        metrics.total_entries = len(self.memory_cache)
        metrics.total_size_mb = (
            sum(e.size_bytes for e in self.memory_cache.values()) / 1024 / 1024
        )
        metrics.hit_rate_pct = (
            metrics.hit_count / max(metrics.total_requests, 1)
        ) * 100

        return entry.value

    async def _store_in_memory_cache(self, entry: CacheEntry) -> None:
        """Store entry in memory cache."""
        # Enforce memory limits
        await self._enforce_memory_limits()

        # Store entry
        self.memory_cache[entry.key] = entry

        # Update metrics
        metrics = self.metrics[CacheLevel.MEMORY]
        metrics.total_entries = len(self.memory_cache)
        metrics.total_size_mb = (
            sum(e.size_bytes for e in self.memory_cache.values()) / 1024 / 1024
        )

        logger.debug(f"Stored in memory cache: {entry.key}")

    async def _get_from_redis_cache(
        self, key: str, default: Any, force_refresh: bool = False
    ) -> Any:
        """Get value from Redis cache."""
        if not self.redis_client:
            return default

        try:
            cached_data = await self.redis_client.get(key)

            if cached_data is None:
                return default

            # Deserialize based on content encoding
            if cached_data:
                if cached_data.startswith(b"g:"):
                    import gzip

                    decompressed = gzip.decompress(cached_data)
                    value = json.loads(decompressed.decode("utf-8"))
                elif cached_data.startswith(b'{"'):
                    value = json.loads(cached_data.decode("utf-8"))
                else:
                    value = cached_data.decode("utf-8")

                # Create cache entry
                entry = CacheEntry(
                    key=key,
                    value=value,
                    content_type="application/json",
                    content_encoding="utf-8",
                    size_bytes=len(cached_data),
                    created_at=time.time(),
                    last_accessed=time.time(),
                    access_count=1,
                    ttl_seconds=self.config.default_ttl_seconds,
                    expires_at=None,
                    cache_level=CacheLevel.REDIS,
                )

                # Update metrics
                metrics = self.metrics[CacheLevel.REDIS]
                metrics.hit_count += 1
                metrics.total_entries = len(self.redis_cache)
                metrics.total_size_mb = (
                    sum(e.size_bytes for e in self.redis_cache.values()) / 1024 / 1024
                )
                metrics.hit_rate_pct = (
                    metrics.hit_count / max(metrics.total_requests, 1)
                ) * 100

                return entry.value
            else:
                return default

        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return default

    async def _store_in_redis_cache(self, entry: CacheEntry) -> None:
        """Store entry in Redis cache."""
        if not self.redis_client:
            return

        try:
            # Serialize based on content encoding
            if entry.content_encoding == "gzip":
                import gzip

                serialized_value = gzip.compress(
                    json.dumps(entry.value, default=str).encode("utf-8")
                )
            else:
                serialized_value = json.dumps(entry.value, default=str).encode("utf-8")

            # Set with TTL
            if entry.ttl_seconds:
                await self.redis_client.setex(
                    entry.key, serialized_value, ex=int(entry.ttl_seconds)
                )
            else:
                await self.redis_client.set(entry.key, serialized_value)

            # Update metrics
            metrics = self.metrics[CacheLevel.REDIS]
            metrics.total_entries = len(self.redis_cache)
            metrics.total_size_mb = (
                sum(e.size_bytes for e in self.redis_cache.values()) / 1024 / 1024
            )

            logger.debug(f"Stored in Redis cache: {entry.key}")

        except Exception as e:
            logger.error(f"Redis store error: {e}")

    async def _get_from_disk_cache(
        self, key: str, default: Any, force_refresh: bool = False
    ) -> Any:
        """Get value from disk cache."""
        if not self.config.enable_disk:
            return default

        try:
            cache_file = f"/tmp/api_cache/{hashlib.md5(key.encode() if isinstance(key, str) else key, usedforsecurity=False).hexdigest()}.cache"

            import os

            if os.path.exists(cache_file):
                with open(cache_file, "rb") as f:
                    data = f.read()

                # Check if file is compressed
                if data.startswith(b"\x1f\x8b"):
                    import gzip

                    data = gzip.decompress(data)
                    value = json.loads(data.decode("utf-8"))
                else:
                    value = data.decode("utf-8")

                # Check if cache entry is expired
                metadata_file = f"{cache_file}.meta"
                if os.path.exists(metadata_file):
                    with open(metadata_file, "r") as f:
                        metadata = json.load(f)

                    if (
                        metadata.get("expires_at")
                        and time.time() > metadata["expires_at"]
                    ):
                        os.remove(cache_file)
                        os.remove(metadata_file)
                        return default

                # Update access statistics
                entry = CacheEntry(
                    key=key,
                    value=value,
                    content_type="application/json",
                    content_encoding="utf-8",
                    size_bytes=len(data),
                    created_at=metadata.get("created_at", time.time()),
                    last_accessed=time.time(),
                    access_count=metadata.get("access_count", 0) + 1,
                    ttl_seconds=metadata.get(
                        "ttl_seconds", self.config.default_ttl_seconds
                    ),
                    expires_at=metadata.get("expires_at"),
                    cache_level=CacheLevel.DISK,
                )

                # Update metrics
                metrics = self.metrics[CacheLevel.DISK]
                metrics.hit_count += 1
                metrics.total_entries = len(self.disk_cache)
                metrics.total_size_mb = (
                    sum(e.size_bytes for e in self.disk_cache.values()) / 1024 / 1024
                )
                metrics.hit_rate_pct = (
                    metrics.hit_count / max(metrics.total_requests, 1)
                ) * 100

                return entry.value
            else:
                return default

        except Exception as e:
            logger.error(f"Disk cache error: {e}")
            return default

    async def _store_in_disk_cache(self, entry: CacheEntry) -> None:
        """Store entry in disk cache."""
        if not self.config.enable_disk:
            return

        try:
            cache_file = f"/tmp/api_cache/{hashlib.md5(entry.key.encode() if isinstance(entry.key, str) else entry.key, usedforsecurity=False).hexdigest()}.cache"
            metadata_file = f"{cache_file}.meta"

            import os

            # Create directory if needed
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)

            # Store metadata
            metadata = {
                "created_at": entry.created_at,
                "ttl_seconds": entry.ttl_seconds,
                "expires_at": entry.expires_at,
                "access_count": entry.access_count,
                "size_bytes": entry.size_bytes,
            }

            # Store metadata
            with open(metadata_file, "w") as f:
                json.dump(metadata, f)

            # Store data
            if entry.content_encoding == "gzip":
                import gzip

                data = gzip.compress(
                    json.dumps(entry.value, default=str).encode("utf-8")
                )
            else:
                data = json.dumps(entry.value, default=str).encode("utf-8")

            with open(cache_file, "wb") as f:
                f.write(data)

            # Update metrics
            metrics = self.metrics[CacheLevel.DISK]
            metrics.total_entries = len(self.disk_cache)
            metrics.total_size_mb = (
                sum(e.size_bytes for e in self.disk_cache.values()) / 1024 / 1024
            )

            logger.debug(f"Stored in disk cache: {entry.key}")

        except Exception as e:
            logger.error(f"Disk cache error: {e}")

    async def _delete_from_cache_level(self, key: str, cache_level: CacheLevel) -> bool:
        """Delete entry from specific cache level."""
        deleted = False

        if cache_level == CacheLevel.MEMORY:
            if key in self.memory_cache:
                del self.memory_cache[key]
                deleted = True
        elif cache_level == CacheLevel.REDIS:
            if self.redis_client and key in self.redis_cache:
                await self.redis_client.delete(key)
                del self.redis_cache[key]
                deleted = True
        elif cache_level == CacheLevel.DISK:
            if key in self.disk_cache:
                cache_file = f"/tmp/api_cache/{hashlib.md5(key.encode() if isinstance(key, str) else key, usedforsecurity=False).hexdigest()}.cache"
                metadata_file = f"{cache_file}.meta"

                try:
                    if os.path.exists(cache_file):
                        os.remove(cache_file)
                        if os.path.exists(metadata_file):
                            os.remove(metadata_file)
                        deleted = True
                except Exception:
                    pass

                del self.disk_cache[key]
                deleted = True

        if deleted:
            # Update metrics
            metrics = self.metrics[cache_level]
            metrics.total_entries = len(
                len(self.memory_cache) + len(self.redis_cache) + len(self.disk_cache)
            )

            # Update metrics
            if metrics.total_entries > 0:
                metrics.total_size_mb = (
                    (
                        sum(e.size_bytes for e in self.memory_cache.values())
                        + sum(e.size_bytes for e in self.redis_cache.values())
                        + sum(e.size_bytes for e in self.disk_cache.values())
                    )
                    / 1024
                    / 1024
                )

            logger.debug(f"Deleted {key} from {cache_level.value} cache")

        return deleted

    async def _enforce_memory_limits(self) -> None:
        """Enforce memory cache size limits."""
        current_size_mb = (
            sum(e.size_bytes for e in self.memory_cache.values()) / 1024 / 1024
        )

        if current_size_mb > self.config.max_memory_size_mb:
            # Remove least recently used entries
            entries_to_remove = len(self.access_order) - (
                self.config.max_memory_entries - 100
            )

            for key in entries_to_remove:
                if key in self.memory_cache:
                    del self.memory_cache[key]
                    self.access_order.remove(key)

            logger.warning(
                f"Enforced memory cache size limit: removed {len(entries_to_remove)} entries"
            )

    async def _cleanup_old_entries(self) -> int:
        """Clean up expired entries from all cache levels."""
        current_time = time.time()
        cleaned_count = 0

        # Clean memory cache
        memory_to_remove = []
        for key, entry in self.memory_cache.items():
            if entry.expires_at and current_time > entry.expires_at:
                memory_to_remove.append(key)

        for key in memory_to_remove:
            del self.memory_cache[key]
            cleaned_count += 1

        # Clean Redis cache
        if self.redis_client:
            # Clean expired keys
            for rule in self.rules:
                if rule.strategy == RateLimitStrategy.SLIDING_WINDOW:
                    cache_key = f"rate_limit:{rule.scope.value}:{rule.name}"
                    await self.redis_client.zremrangebyscore(
                        cache_key,
                        0,
                        current_time,
                        current_time - rule.window_seconds * 2,
                    )

        # Clean disk cache
        if self.config.enable_disk:
            cache_dir = "/tmp/api_cache"
            if os.path.exists(cache_dir):
                current_time = time.time()

                for filename in os.listdir(cache_dir):
                    if filename.endswith(".meta"):
                        metadata_file = os.path.join(cache_dir, filename)
                        if os.path.exists(metadata_file):
                            with open(metadata_file, "r") as f:
                                metadata = json.load(f)

                            if (
                                metadata.get("expires_at")
                                and current_time > metadata["expires_at"]
                            ):
                                os.remove(metadata_file)
                                os.remove(metadata_file.replace(".meta", ".cache"))
                                cleaned_count += 1

                # Remove expired cache files
                for filename in os.listdir(cache_dir):
                    if filename.endswith(".cache"):
                        cache_file = os.path.join(cache_dir, filename)
                        if os.path.exists(cache_file):
                            metadata_file = f"{cache_file}.meta"
                            if os.path.exists(metadata_file):
                                with open(metadata_file, "r") as f:
                                    metadata = json.load(f)

                                if (
                                    metadata.get("expires_at")
                                    and current_time > metadata["expires_at"]
                                ):
                                    os.remove(cache_file)
                                    os.remove(metadata_file.replace(".meta", ".cache"))
                                    cleaned_count += 1

        return cleaned_count

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        stats = {
            "total_entries": sum(
                len(self.memory_cache) + len(self.redis_cache) + len(self.disk_cache)
            ),
            "memory_entries": len(self.memory_cache),
            "redis_entries": len(self.redis_cache),
            "disk_entries": len(self.disk_cache),
            "total_size_mb": sum(
                sum(e.size_bytes for e in self.memory_cache.values()) / 1024 / 1024
                + sum(e.size_bytes for e in self.redis_cache.values()) / 1024 / 1024
                + sum(e.size_bytes for e in self.disk_cache.values()) / 1024 / 1024
            ),
            "hit_rate_pct": 0.0,
            "avg_response_time_ms": 0.0,
            "cache_levels": {},
        }

        # Calculate hit rates
        total_requests = sum(m.total_requests for m in self.metrics.values())
        if total_requests > 0:
            stats["hit_rate_pct"] = (
                sum(m.hit_count for m in self.metrics.values()) / total_requests
            ) * 100

        # Calculate average response time
        all_response_times = []
        for m in self.metrics.values():
            if m.avg_response_time_ms > 0:
                all_response_times.append(m.avg_response_time_ms)

        if all_response_times:
            stats["avg_response_time_ms"] = sum(all_response_times) / len(
                all_response_times
            )

        # Add level-specific stats
        for level in CacheLevel:
            metrics = self.metrics[level]
            stats["cache_levels"][level.value] = {
                "total_entries": metrics.total_entries,
                "total_size_mb": metrics.total_size_mb,
                "hit_count": metrics.hit_count,
                "miss_count": metrics.total_requests - metrics.hit_count,
                "hit_rate_pct": metrics.hit_rate_pct,
                "avg_response_time_ms": metrics.avg_response_time_ms,
                "eviction_count": metrics.eviction_count,
                "invalidation_count": metrics.invalidation_count,
                "avg_ttl_seconds": metrics.avg_ttl_seconds,
                "peak_usage": metrics.peak_usage,
            }

        return stats

    async def warm_cache(
        self, warmup_queries: List[Dict[str, Any]], batch_size: int = 100
    ) -> Dict[str, Any]:
        """Warm cache with predefined queries."""
        warmed_count = 0
        errors = []

        # Process in batches
        for i in range(0, len(warm_up_queries), batch_size):
            batch = warm_up_queries[i : i + batch_size]

            for query in batch:
                try:
                    # Execute query and cache result
                    if "query" in query and "params" in query:
                        result = await query["query"](*query["params"])
                    else:
                        result = await query["query"]()

                    # Cache the result
                    await self.set(
                        query["key"],
                        result,
                        ttl_seconds=query.get("ttl", self.config.default_ttl_seconds),
                    )
                    warmed_count += 1

                except Exception as e:
                    errors.append(
                        f"Query failed: {query.get('query', 'unknown')}: {str(e)}"
                    )
                    logger.error(
                        f"Cache warmup failed for query: {query.get('query', 'unknown')}"
                    )

        return {
            "warmed_queries": warmed_count,
            "total_queries": len(warm_up_queries),
            "errors": errors,
            "success_rate": (
                warmed_count / len(warm_up_queries) * 100 if warm_up_queries else 0
            ),
        }

    def get_cache_keys(
        self, pattern: Optional[str] = None, limit: int = 100
    ) -> List[str]:
        """Get cache keys matching pattern."""
        keys = []

        # Get keys from all cache levels
        all_keys = (
            list(self.memory_cache.keys())
            + list(self.redis_cache.keys())
            + list(self.disk_cache.keys())
        )

        if pattern:
            import re

            keys = [key for key in all_keys if re.search(pattern, key)]

        # Sort keys and return limited number
        keys.sort()
        return keys[:limit]

    def get_cache_info(self, key: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a cache entry."""
        for level in CacheLevel:
            if level == CacheLevel.MEMORY and key in self.memory_cache:
                entry = self.memory_cache[key]
                return {
                    "cache_level": "memory",
                    "key": entry.key,
                    "content_type": entry.content_type,
                    "content_encoding": entry.content_encoding,
                    "size_bytes": entry.size_bytes,
                    "created_at": entry.created_at,
                    "last_accessed": entry.last_accessed,
                    "access_count": entry.access_count,
                    "ttl_seconds": entry.ttl_seconds,
                    "expires_at": entry.expires_at,
                    "age_seconds": time.time() - entry.created_at,
                }
            elif level == CacheLevel.REDIS and key in self.redis_cache:
                entry = self.redis_cache[key]
                return {
                    "cache_level": "redis",
                    "key": entry.key,
                    "content_type": entry.content_type,
                    "content_encoding": entry.content_encoding,
                    "size_bytes": entry.size_bytes,
                    "created_at": entry.created_at,
                    "last_accessed": entry.last_accessed,
                    "access_count": entry.access_count,
                    "ttl_seconds": entry.ttl_seconds,
                    "expires_at": entry.expires_at,
                    "age_seconds": time.time() - entry.created_at,
                }
            elif level == CacheLevel.DISK and key in self.disk_cache:
                entry = self.disk_cache[key]
                return {
                    "cache_level": "disk",
                    "key": entry.key,
                    "content_type": entry.content_type,
                    "content_encoding": entry.content_encoding,
                    "size_bytes": entry.size_bytes,
                    "created_at": entry.created_at,
                    "last_accessed": entry.last_accessed,
                    "access_count": entry.access_count,
                    "ttl_seconds": entry.ttl_seconds,
                    "expires_at": entry.expires_at,
                    "age_seconds": time.time() - entry.created_at,
                }

        return None

    def get_cache_health(self) -> Dict[str, Any]:
        """Get cache health status."""
        stats = self.get_cache_stats()

        health_status = "healthy"
        issues = []

        # Check memory cache health
        if stats["memory_entries"] > self.config.max_memory_entries * 0.9:
            health_status = "degraded"
            issues.append(
                f"Memory cache at {stats['memory_entries']} entries ({stats['total_entries']} max: {self.config.max_memory_entries})"
            )

        # Check Redis health
        if self.config.enable_redis:
            if stats["redis_entries"] > 1000:
                health_status = "degraded"
                issues.append(f"Redis cache at {stats['redis_entries']} entries")

        # Check disk cache health
        if self.config.enable_disk:
            if stats["disk_entries"] > 5000:
                health_status = "degraded"
                issues.append(f"Disk cache at {stats['disk_entries']} entries")

        # Check error rates
        if stats["error_rate_pct"] > 10:
            health_status = "degraded"
            issues.append(f"High error rate: {stats['error_rate']:.1f}%")

        return {"status": health_status, "issues": issues, "stats": stats}

    async def export_metrics(self) -> Dict[str, Any]:
        """Export all metrics for analysis."""
        return {
            "timestamp": time.time(),
            "config": {
                "default_ttl_seconds": self.config.default_ttl_seconds,
                "max_memory_entries": self.config.max_memory_entries,
                "max_memory_size_mb": self.config.max_memory_size_mb,
                "enable_redis": self.config.enable_redis,
                "enable_disk": self.config.enable_disk,
                "enable_compression": self.config.enable_compression,
                "compression_threshold_bytes": self.config.compression_threshold_bytes,
                "cleanup_interval_seconds": self.config.cleanup_interval_seconds,
                "enable_warming": self.config.warming_enabled,
                "strategies": {
                    "memory": self.config.memory_strategy.value,
                    "redis": self.config.redis_strategy.value,
                    "disk": self.config.disk_strategy.value,
                },
            },
            "metrics": {
                level: {
                    level.value: {
                        "total_entries": m.total_entries,
                        "total_size_mb": m.total_size_mb,
                        "hit_count": m.hit_count,
                        "miss_count": m.total_requests - m.hit_count,
                        "hit_rate_pct": m.hit_rate_pct,
                        "avg_response_time_ms": m.avg_response_time_ms,
                        "eviction_count": m.eviction_count,
                        "invalidation_count": m.invalidation_count,
                        "avg_ttl_seconds": m.avg_ttl_seconds,
                        "peak_usage": m.peak_usage,
                    }
                    for level, m in self.metrics.items()
                },
                "summary": {
                    "total_entries": stats["total_entries"],
                    "total_size_mb": stats["total_size_mb"],
                    "hit_rate_pct": stats["hit_rate_pct"],
                    "avg_response_time_ms": stats["avg_response_time_ms"],
                    "error_rate_pct": stats["error_rate_pct"],
                    "global_hit_rate_pct": stats["global_hit_rate_pct"],
                    "cache_levels": {
                        level.value: {
                            "total_entries": m.total_entries,
                            "total_size_mb": m.total_size_mb,
                            "hit_count": m.hit_count,
                            "miss_count": m.total_requests - m.hit_count,
                            "hit_rate_pct": m.hit_rate_pct,
                            "avg_response_time_ms": m.avg_response_time_ms,
                            "eviction_count": m.eviction_count,
                            "invalidation_count": m.invalidation_count,
                            "avg_ttl_seconds": m.avg_ttl_seconds,
                            "peak_usage": m.peak_usage,
                        }
                        for level, m in self.metrics.items()
                    },
                },
            },
        }

    async def reset_cache(self, cache_level: Optional[CacheLevel] = None) -> int:
        """Reset specific cache level or all caches."""
        if cache_level:
            if cache_level == CacheLevel.MEMORY:
                count = len(self.memory_cache)
                self.memory_cache.clear()
                self.metrics[CacheLevel.MEMORY] = CacheMetrics(
                    cache_level=CacheLevel.MEMORY,
                    total_entries=0,
                    total_size_mb=0.0,
                    hit_count=0,
                    miss_count=0,
                    hit_rate_pct=0.0,
                    avg_response_time_ms=0.0,
                    eviction_count=0,
                    invalidation_count=0,
                    avg_ttl_seconds=0.0,
                    peak_usage=0.0,
                )
            elif cache_level == CacheLevel.REDIS:
                count = len(self.redis_cache)
                self.redis_cache.clear()
                self.metrics[CacheLevel.REDIS] = CacheMetrics(
                    cache_level=cache_level,
                    total_entries=0,
                    total_size_mb=0.0,
                    hit_count=0,
                    miss_count=0,
                    hit_rate_pct=0.0,
                    avg_response_time_ms=0.0,
                    eviction_count=0,
                    invalidation_count=0,
                    avg_ttl_seconds=0.0,
                    peak_usage=0.0,
                )
            elif cache_level == CacheLevel.DISK:
                count = len(self.disk_cache)
                self.disk_cache.clear()
                self.metrics[CacheLevel.DISK] = CacheMetrics(
                    cache_level=cache_level,
                    total_entries=0,
                    total_size_mb=0.0,
                    hit_count=0,
                    miss_count=0,
                    hit_rate_pct=0.0,
                    avg_response_time_ms=0.0,
                    eviction_count=0,
                    invalidation_count=0,
                    avg_ttl_seconds=0.0,
                    peak_usage=0.0,
                )
        else:
            # Reset all caches
            self.memory_cache.clear()
            self.redis_cache.clear()
            self.disk_cache.clear()

            for level in CacheLevel:
                self.metrics[level] = CacheMetrics(
                    cache_level=level,
                    total_entries=0,
                    total_size_mb=0.0,
                    hit_count=0,
                    miss_count=0,
                    hit_rate_pct=0.0,
                    avg_response_time_ms=0.0,
                    eviction_count=0,
                    invalidation_count=0,
                    avg_ttl_seconds=0.0,
                    peak_usage=0.0,
                )

        return count

    def set_cache_strategy(self, level: CacheLevel, strategy: CacheStrategy) -> None:
        """Set caching strategy for a level."""
        if level == CacheLevel.MEMORY:
            self.config.memory_strategy = strategy
        elif level == CacheLevel.REDIS:
            self.config.redis_strategy = strategy
        elif level == CacheLevel.DISK:
            self.config.disk_strategy = strategy

        logger.info(f"Set {level.value} cache strategy to {strategy.value}")

    def get_cache_strategy(self, level: CacheLevel) -> CacheStrategy:
        """Get current caching strategy for a level."""
        if level == CacheLevel.MEMORY:
            return self.config.memory_strategy
        elif level == CacheLevel.REDIS:
            return self.config.redis_strategy
        elif level == CacheLevel.DISK:
            return self.config.disk_strategy
        else:
            return CacheStrategy.LRU

    def update_config(self, **kwargs) -> None:
        """Update cache configuration."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                old_value = getattr(self.config, key)
                setattr(self.config, key, value)
                logger.info(f"Updated cache config {key}: {old_value} -> {value}")

    def get_config(self) -> Dict[str, Any]:
        """Get current cache configuration."""
        return {
            "default_ttl_seconds": self.config.default_ttl_seconds,
            "max_memory_entries": self.config.max_memory_entries,
            "max_memory_size_mb": self.config.max_memory_size_mb,
            "max_redis_size_mb": self.config.max_redis_size_mb,
            "max_disk_size_mb": self.config.max_disk_size_mb,
            "enable_redis": self.config.enable_redis,
            "enable_disk": self.config.enable_disk,
            "enable_compression": self.config.enable_compression,
            "compression_threshold_bytes": self.config.compression_threshold_bytes,
            "cleanup_interval_seconds": self.config.cleanup_interval_seconds,
            "warming_enabled": self.config.warming_enabled,
            "warming_batch_size": self.config.warming_batch_size,
            "strategies": {
                "memory": self.config.memory_strategy.value,
                "redis": self.config.redis_strategy.value,
                "disk": self.config.disk_strategy.value,
            },
        }


# Global response cache instance
_response_cache: ResponseCache | None = None


def get_response_cache() -> ResponseCache:
    """Get global response cache instance."""
    global _response_cache
    if _response_cache is None:
        raise RuntimeError(
            "Response cache not initialized. Call init_response_cache() first."
        )
    return _response_cache


async def init_response_cache(
    redis_client: Optional[redis.asyncio.Redis] = None,
    config: Optional[CacheConfig] = None,
    alert_manager: Optional[Any] = None,
    default_ttl_seconds: float = 300.0,
    default_burst: int = 10,
) -> ResponseCache:
    """Initialize global response cache."""
    global _response_cache
    _response_cache = ResponseCache(
        redis_client, config, alert_manager, default_ttl_seconds, default_burst
    )
    return _response_cache


# Decorator for easy cache integration
def cached(
    ttl_seconds: float = 300.0,
    cache_level: CacheLevel = CacheLevel.MEMORY,
    key_func: Optional[str] = None,
):
    """Decorator for caching function results."""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = _generate_cache_key(func.__name__, key_func)

            # Execute function
            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time

            # Cache the result
            await _response_cache.set(
                cache_key, result, ttl_seconds=ttl_seconds, cache_level=cache_level
            )

            return result

        return wrapper

    return decorator


def _generate_cache_key(func_name: str, key_func: Optional[str] = None) -> str:
    """Generate cache key for function."""
    if key_func:
        return f"{func_name}:{key_func}:{hashlib.md5(func_name.encode(), usedforsecurity=False).hexdigest()}"
    else:
        return f"{func_name}:{hashlib.md5(func_name.encode(), usedforsecurity=False).hexdigest()}"
