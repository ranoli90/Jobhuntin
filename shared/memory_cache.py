"""
Memory Cache Implementation for Phase 15.1 Database & Performance
"""

from __future__ import annotations

import asyncio
import json
import pickle
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from shared.logging_config import get_logger
from shared.metrics_collector import MetricCategory, MetricType, get_metrics_collector

logger = get_logger("sorce.memory_cache")


class CacheStrategy(Enum):
    """Cache eviction strategies."""

    LRU = "lru"
    LFU = "lfu"
    FIFO = "fifo"
    TTL = "ttl"
    MANUAL = "manual"


class CacheStatus(Enum):
    """Cache entry status."""

    ACTIVE = "active"
    EXPIRED = "expired"
    EVICTED = "evicted"
    DELETED = "deleted"


@dataclass
class CacheEntry:
    """Cache entry with metadata."""

    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime]
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    size_bytes: int = 0
    ttl_seconds: Optional[int] = None
    status: CacheStatus = CacheStatus.ACTIVE
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


@dataclass
class CacheStatistics:
    """Cache statistics."""

    total_entries: int = 0
    total_size_bytes: int = 0
    hit_count: int = 0
    miss_count: int = 0
    eviction_count: int = 0
    hit_rate: float = 0.0
    avg_access_time_ms: float = 0.0
    memory_usage_percent: float = 0.0
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class MemoryCache:
    """Memory-based cache implementation with LRU eviction."""

    def __init__(
        self,
        max_size: int = 10000,
        default_ttl_seconds: int = 3600,
        strategy: CacheStrategy = CacheStrategy.LRU,
        cleanup_interval_seconds: int = 300,
        compression_enabled: bool = False,
        max_memory_mb: int = 100,
    ):
        self.max_size = max_size
        self.default_ttl_seconds = default_ttl_seconds
        self.strategy = strategy
        self.cleanup_interval_seconds = cleanup_interval_seconds
        self.compression_enabled = compression_enabled
        self.max_memory_mb = max_memory_mb

        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: List[str] = []
        self._frequency: Dict[str, int] = defaultdict(int)
        self._lock = asyncio.Lock()

        # Statistics
        self._stats = CacheStatistics()
        self._access_times: List[float] = []

        # Metrics collector
        self._metrics_collector = get_metrics_collector()

        # Background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None

        # Initialize metrics
        self._initialize_metrics()

        # Start background cleanup
        self._start_cleanup_task()

    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        try:
            start_time = time.time()

            async with self._lock:
                entry = self._cache.get(key)

                if entry is None:
                    self._stats.miss_count += 1
                    self._update_hit_rate()
                    self._frequency[key] = 0
                    return default

                # Check expiration
                if entry.expires_at and datetime.now(timezone.utc) > entry.expires_at:
                    # Remove expired entry
                    del self._cache[key]
                    if key in self._access_order:
                        self._access_order.remove(key)
                    self._stats.miss_count += 1
                    self._update_hit_rate()
                    return default

                # Update access statistics
                entry.access_count += 1
                entry.last_accessed = datetime.now(timezone.utc)
                self._frequency[key] += 1

                # Update access order based on strategy
                if self.strategy == CacheStrategy.LRU:
                    # Move to end of access order
                    if key in self._access_order:
                        self._access_order.remove(key)
                        self._access_order.append(key)
                elif self.strategy == CacheStrategy.LFU:
                    # LFU doesn't change order, just update frequency
                    pass
                elif self.strategy == CacheStrategy.FIFO:
                    # FIFO doesn't change order, just update frequency
                    pass

                # Update access time
                access_time_ms = (time.time() - start_time) * 1000
                self._access_times.append(access_time_ms)
                self._update_avg_access_time()
                self._stats.hit_count += 1
                self._update_hit_rate()

                return entry.value

        except Exception as e:
            logger.error(f"Failed to get from memory cache: {e}")
            self._stats.miss_count += 1
            self._update_hit_rate()
            return default

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Set value in cache."""
        try:
            time.time()

            async with self._lock:
                # Serialize and possibly compress value
                if self.compression_enabled:
                    try:
                        serialized_value = pickle.dumps(
                            value, protocol=pickle.HIGHEST_PROTOCOL
                        )
                    except Exception:
                        serialized_value = json.dumps(value, default=str).encode(
                            "utf-8"
                        )
                else:
                    serialized_value = pickle.dumps(value)

                # Calculate size
                size_bytes = len(serialized_value)

                # Check if eviction is needed
                if len(self._cache) >= self.max_size:
                    await self._evict_entry()

                # Create entry
                entry = CacheEntry(
                    key=key,
                    value=value,
                    created_at=datetime.now(timezone.utc),
                    expires_at=datetime.now(timezone.utc)
                    + timedelta(seconds=ttl_seconds or self.default_ttl_seconds),
                    size_bytes=size_bytes,
                    ttl_seconds=ttl_seconds,
                    metadata=metadata or {},
                    tags=tags or [],
                )

                self._cache[key] = entry
                self._access_order.append(key)
                self._frequency[key] = 1

                # Update statistics
                self._stats.total_entries = len(self._cache)
                self._stats.total_size_bytes += size_bytes

                return True

        except Exception as e:
            logger.error(f"Failed to set in memory cache: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            async with self._lock:
                if key in self._cache:
                    del self._cache[key]
                    if key in self._access_order:
                        self._access_order.remove(key)
                    if key in self._frequency:
                        del self._frequency[key]

                    self._stats.total_entries = len(self._cache)
                    self._update_memory_usage()

                    return True

                return False

        except Exception as e:
            logger.error(f"Failed to delete from memory cache: {e}")
            return False

    async def clear(self, pattern: Optional[str] = None) -> int:
        """Clear cache entries."""
        try:
            async with self._lock:
                if pattern:
                    # Clear entries matching pattern
                    keys_to_delete = [k for k in self._cache.keys() if pattern in k]

                    for key in keys_to_delete:
                        del self._cache[key]
                        if key in self._access_order:
                            self._access_order.remove(key)
                        if key in self._frequency:
                            del self._frequency[key]

                    cleared_count = len(keys_to_delete)
                else:
                    # Clear all entries
                    cleared_count = len(self._cache)
                    self._cache.clear()
                    self._access_order.clear()
                    self._frequency.clear()

                # Reset statistics
                self._stats.total_entries = 0
                self._stats.total_size_bytes = 0
                self._stats.hit_count = 0
                self._stats.miss_count = 0
                self._stats.eviction_count += cleared_count
                self._update_hit_rate()
                self._update_memory_usage()

                return cleared_count

        except Exception as e:
            logger.error(f"Failed to clear memory cache: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            async with self._lock:
                entry = self._cache.get(key)

                if entry is None:
                    return False

                # Check expiration
                if entry.expires_at and datetime.now(timezone.utc) > entry.expires_at:
                    return False

                return True

        except Exception as e:
            logger.error(f"Failed to check cache existence: {e}")
            return False

    async def expire(self, key: str, ttl_seconds: int) -> bool:
        """Set expiration for a key."""
        try:
            async with self._lock:
                entry = self._cache.get(key)

                if entry:
                    entry.expires_at = datetime.now(timezone.utc) + timedelta(
                        seconds=ttl_seconds
                    )
                    return True

                return False

        except Exception as e:
            logger.error(f"Failed to set cache expiration: {e}")
            return False

    async def ttl(self, key: str) -> int:
        """Get time to live for a key."""
        try:
            async with self._lock:
                entry = self._cache.get(key)

                if entry and entry.expires_at:
                    ttl = (
                        entry.expires_at - datetime.now(timezone.utc)
                    ).total_seconds()
                    return max(0, int(ttl))

                return -1

        except Exception as e:
            logger.error(f"Failed to get cache TTL: {e}")
            return -1

    async def get_stats(self) -> CacheStatistics:
        """Get cache statistics."""
        try:
            self._update_memory_usage()
            return self._stats

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return CacheStatistics()

    def _update_hit_rate(self) -> None:
        """Update cache hit rate."""
        try:
            total_requests = self._stats.hit_count + self._stats.miss_count
            if total_requests > 0:
                self._stats.hit_rate = self._stats.hit_count / total_requests

        except Exception as e:
            logger.error(f"Failed to update hit rate: {e}")

    def _update_avg_access_time(self) -> None:
        """Update average access time."""
        try:
            if self._access_times:
                self._stats.avg_access_time_ms = sum(self._access_times) / len(
                    self._access_times
                )

                # Keep only last 1000 access times
                if len(self._access_times) > 1000:
                    self._access_times = self._access_times[-1000:]

        except Exception as e:
            logger.error(f"Failed to update avg access time: {e}")

    def _update_memory_usage(self) -> None:
        """Update memory usage statistics."""
        try:
            # Calculate total size
            total_size = sum(entry.size_bytes for entry in self._cache.values())
            self._stats.total_size_bytes = total_size

            # Estimate memory usage percentage
            if self.max_memory_mb > 0:
                total_memory_mb = (
                    self.max_memory_mb * 1024 * 1024
                )  # Convert MB to bytes
                if total_memory_mb > 0:
                    self._stats.memory_usage_percent = (
                        total_size / total_memory_mb
                    ) * 100

        except Exception as e:
            logger.error(f"Failed to update memory usage: {e}")
            self._stats.memory_usage_percent = 0.0

    async def _evict_entry(self) -> None:
        """Evict entry based on strategy."""
        try:
            if self.strategy == CacheStrategy.LRU:
                await self._evict_lru()
            elif self.strategy == CacheStrategy.LFU:
                await self._evict_lfu()
            elif self.strategy == CacheStrategy.FIFO:
                await self._evict_fifo()
            elif self.strategy == CacheStrategy.TTL:
                await self._evict_ttl()
            elif self.strategy == CacheStrategy.MANUAL:
                pass  # Manual eviction requires explicit key specification

        except Exception as e:
            logger.error(f"Failed to evict entry: {e}")

    async def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        try:
            if not self._access_order:
                return

            # Get the least recently used key
            lru_key = self._access_order[0]

            # Remove from cache
            if lru_key in self._cache:
                del self._cache[lru_key]
                self._access_order.remove(lru_key)
                if lru_key in self._frequency:
                    del self._frequency[lru_key]
                self._stats.eviction_count += 1
                self._update_memory_usage()

                logger.debug(f"Evicted LRU entry: {lru_key}")

        except Exception as e:
            logger.error(f"Failed to evict LRU entry: {e}")

    async def _evict_lfu(self) -> None:
        """Evict least frequently used entry."""
        try:
            if not self._frequency:
                return

            # Find the least frequently used key
            lfu_key = min(self._frequency.items(), key=lambda item: item[1])[0]

            # Remove from cache
            if lfu_key in self._cache:
                del self._cache[lfu_key]
                if lfu_key in self._access_order:
                    self._access_order.remove(lfu_key)
                del self._frequency[lfu_key]
                self._stats.eviction_count += 1
                self._update_memory_usage()

                logger.debug(f"Evicted LFU entry: {lfu_key}")

        except Exception as e:
            logger.error(f"Failed to evict LFU entry: {e}")

    async def _evict_fifo(self) -> None:
        """Evict oldest entry (FIFO)."""
        try:
            if not self._access_order:
                return

            # Get the oldest entry (first in access order)
            oldest_key = self._access_order[0]

            # Remove from cache
            if oldest_key in self._cache:
                del self._cache[oldest_key]
                self._access_order.remove(oldest_key)
                if oldest_key in self._frequency:
                    del self._frequency[oldest_key]
                self._stats.eviction_count += 1
                self._update_memory_usage()

                logger.debug(f"Evicted FIFO entry: {oldest_key}")

        except Exception as e:
            logger.error(f"Failed to evict FIFO entry: {e}")

    async def _evict_ttl(self) -> None:
        """Evict expired entries."""
        try:
            now = datetime.now(timezone.utc)
            expired_keys = [
                key
                for key, entry in self._cache.items()
                if entry.expires_at and now > entry.expires_at
            ]

            for key in expired_keys:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                if key in self._frequency:
                    del self._frequency[key]

            if expired_keys:
                self._stats.eviction_count += len(expired_keys)
                self._update_memory_usage()
                logger.debug(f"Evicted {len(expired_keys)} expired entries")

        except Exception as e:
            logger.error(f"Failed to evict expired entries: {e}")

    def _initialize_metrics(self) -> None:
        """Initialize metrics collection."""
        try:
            # Define metrics for memory cache
            self._metrics_collector.define_metric(
                name="memory_cache_hit_rate",
                metric_type=MetricType.GAUGE,
                category=MetricCategory.CACHE,
                description="Memory cache hit rate",
                unit="percent",
                labels=["cache_type"],
            )

            self._metrics_collector.define_metric(
                name="memory_cache_size",
                metric_type=MetricType.GAUGE,
                category=MetricCategory.CACHE,
                description="Memory cache size in bytes",
                unit="bytes",
            )

            self._metrics_collector.define_metric(
                name="memory_cache_memory_usage",
                metric_type=MetricType.GAUGE,
                category=MetricCategory.CACHE,
                description="Memory cache memory usage percentage",
                unit="percent",
            )

            self._metrics_collector.define_metric(
                name="memory_cache_operations",
                metric_type=MetricType.COUNTER,
                category=MetricCategory.CACHE,
                description="Memory cache operations count",
                unit="operations",
            )

        except Exception as e:
            logger.error(f"Failed to initialize metrics: {e}")

    def _start_cleanup_task(self) -> None:
        """Start background cleanup task."""
        try:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        except Exception as e:
            logger.error(f"Failed to start cleanup task: {e}")

    async def _cleanup_loop(self) -> None:
        """Background cleanup loop."""
        try:
            while True:
                await asyncio.sleep(self.cleanup_interval_seconds)

                try:
                    # Clean expired entries
                    await self._cleanup_expired_entries()

                    # Evict entries if over memory limit
                    if self._stats.memory_usage_percent > 80:
                        await self._evict_entries(count=5)

                    # Update metrics
                    await self._update_metrics()

                except Exception as e:
                    logger.error(f"Cleanup loop error: {e}")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Cleanup loop failed: {e}")

    async def _cleanup_expired_entries(self) -> None:
        """Clean up expired entries."""
        try:
            now = datetime.now(timezone.utc)
            expired_keys = [
                key
                for key, entry in self._cache.items()
                if entry.expires_at and now > entry.expires_at
            ]

            for key in expired_keys:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                if key in self._frequency:
                    del self._frequency[key]

            if expired_keys:
                self._stats.eviction_count += len(expired_keys)
                self._update_memory_usage()
                logger.debug(f"Cleaned up {len(expired_keys)} expired entries")

        except Exception as e:
            logger.error(f"Failed to cleanup expired entries: {e}")

    async def _evict_entries(self, count: int = 1) -> None:
        """Evict specified number of entries."""
        try:
            evicted_count = 0

            for _ in range(count):
                if len(self._cache) == 0:
                    break

                await self._evict_entry()
                evicted_count += 1

            if evicted_count > 0:
                logger.debug(f"Evicted {evicted_count} entries")

        except Exception as e:
            logger.error(f"Failed to evict entries: {e}")

    async def _update_metrics(self) -> None:
        """Update cache metrics."""
        try:
            # Update hit rate metric
            await self._metrics_collector.set_gauge(
                "memory_cache_hit_rate",
                self._stats.hit_rate,
                labels={"cache_type": "memory"},
            )

            # Update size metric
            await self._metrics_collector.set_gauge(
                "memory_cache_size",
                self._stats.total_size_bytes,
                labels={"cache_type": "memory"},
            )

            # Update memory usage metric
            await self._metrics_collector.set_gauge(
                "memory_cache_memory_usage",
                self._stats.memory_usage_percent,
                labels={"cache_type": "memory"},
            )

            # Update operations metric
            await self._metrics_collector.increment_counter(
                "memory_cache_operations",
                labels={"cache_type": "memory"},
            )

        except Exception as e:
            logger.error(f"Failed to update metrics: {e}")


# Factory function
def create_memory_cache(**kwargs) -> MemoryCache:
    """Create memory cache instance."""
    return MemoryCache(**kwargs)
