"""
Redis Cache Implementation for Phase 15.1 Database & Performance
"""

from __future__ import annotations

import asyncio
import json
import pickle
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    import redis.asyncio as redis
except ImportError:
    redis = None

from shared.logging_config import get_logger
from shared.metrics_collector import MetricCategory, MetricType, get_metrics_collector

logger = get_logger("sorce.redis_cache")


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


class RedisCache:
    """Redis-based cache implementation."""

    def __init__(
        self,
        redis_url: str,
        key_prefix: str = "sorce_cache",
        default_ttl_seconds: int = 3600,
        max_connections: int = 10,
        socket_timeout: int = 5,
        socket_connect_timeout: int = 5,
        health_check_interval: int = 30,
        retry_attempts: int = 3,
        retry_delay: float = 1.0,
    ):
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.default_ttl_seconds = default_ttl_seconds
        self.max_connections = max_connections
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout
        self.health_check_interval = health_check_interval
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay

        self._client: Optional[redis.Redis] = None
        self._is_connected = False
        self._connection_error_count = 0
        self._last_health_check = datetime.now(timezone.utc)

        # Statistics
        self._stats = CacheStatistics()
        self._access_times: List[float] = []
        self._lock = asyncio.Lock()

        # Background tasks
        self._health_check_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None

        # Metrics collector
        self._metrics_collector = get_metrics_collector()

        # Initialize metrics
        self._initialize_metrics()

        # Start background tasks
        self._start_background_tasks()

    async def connect(self) -> bool:
        """Connect to Redis."""
        try:
            if not redis:
                logger.warning("Redis not available, RedisCache will be disabled")
                return False

            # Create Redis client
            self._client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False,
                max_connections=self.max_connections,
                socket_timeout=self.socket_timeout,
                socket_connect_timeout=self.socket_connect_timeout,
                retry_on_timeout=True,
                retry_on_error=[redis.ConnectionError, redis.TimeoutError],
            )

            # Test connection
            await self._client.ping()

            self._is_connected = True
            self._connection_error_count = 0
            self._last_health_check = datetime.now(timezone.utc)

            logger.info("Connected to Redis")
            return True

        except Exception as e:
            self._is_connected = False
            self._connection_error_count += 1
            logger.error(f"Failed to connect to Redis: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        try:
            if self._client:
                await self._client.close()
                self._client = None

            self._is_connected = False
            logger.info("Disconnected from Redis")

        except Exception as e:
            logger.error(f"Error disconnecting from Redis: {e}")

    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        try:
            if not self._is_connected:
                return default

            start_time = time.time()

            # Build full key
            full_key = f"{self.key_prefix}:{key}"

            try:
                # Get from Redis
                data = await self._client.get(full_key)

                if data is None:
                    self._stats.miss_count += 1
                    self._update_hit_rate()
                    return default

                # Deserialize
                try:
                    value = pickle.loads(data)
                except (pickle.PickleError, TypeError):
                    # Fallback to JSON
                    value = json.loads(data.decode("utf-8"))

                # Update access statistics
                access_time_ms = (time.time() - start_time) * 1000
                self._access_times.append(access_time_ms)
                self._update_avg_access_time()
                self._stats.hit_count += 1
                self._update_hit_rate()

                return value

            except redis.RedisError as e:
                logger.error(f"Redis get error for key {key}: {e}")
                self._stats.miss_count += 1
                self._update_hit_rate()
                return default

        except Exception as e:
            logger.error(f"Failed to get from cache: {e}")
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
            if not self._is_connected:
                return False

            # Serialize value
            try:
                data = pickle.dumps(value)
            except (pickle.PickleError, TypeError):
                # Fallback to JSON
                data = json.dumps(value, default=str).encode("utf-8")

            # Calculate size
            size_bytes = len(data)

            # Build full key
            full_key = f"{self.key_prefix}:{key}"

            # Set TTL
            ttl = ttl_seconds or self.default_ttl_seconds

            try:
                # Set in Redis
                if ttl > 0:
                    await self._client.setex(full_key, ttl, data)
                else:
                    await self._client.set(full_key, data)

                # Update statistics
                self._stats.total_entries += 1
                self._stats.total_size_bytes += size_bytes
                self._update_memory_usage()

                return True

            except redis.RedisError as e:
                logger.error(f"Redis set error for key {key}: {e}")
                return False

        except Exception as e:
            logger.error(f"Failed to set in cache: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            if not self._is_connected:
                return False

            # Build full key
            full_key = f"{self.key_prefix}:{key}"

            try:
                # Delete from Redis
                result = await self._client.delete(full_key)

                # Update statistics
                if result > 0:
                    self._stats.eviction_count += 1
                    self._update_memory_usage()

                return result > 0

            except redis.RedisError as e:
                logger.error(f"Redis delete error for key {key}: {e}")
                return False

        except Exception as e:
            logger.error(f"Failed to delete from cache: {e}")
            return False

    async def clear(self, pattern: Optional[str] = None) -> int:
        """Clear cache entries."""
        try:
            if not self._is_connected:
                return 0

            try:
                # Clear all keys or specific pattern
                if pattern:
                    full_pattern = f"{self.key_prefix}:{pattern}"
                    keys = await self._client.keys(full_pattern)
                else:
                    keys = await self._keys(f"{self.key_prefix}:*")

                if keys:
                    if pattern:
                        await self._client.delete(*keys)
                    else:
                        await self._client.flushdb()

                    # Update statistics
                    cleared_count = len(keys)
                    self._stats.total_entries = max(
                        0, self._stats.total_entries - cleared_count
                    )
                    self._update_memory_usage()

                    return cleared_count
                else:
                    return 0

            except redis.RedisError as e:
                logger.error(f"Redis clear error: {e}")
                return 0

        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            if not self._is_connected:
                return False

            # Build full key
            full_key = f"{self.key_prefix}:{key}"

            try:
                result = await self._client.exists(full_key)
                return bool(result)

            except redis.RedisError as e:
                logger.error(f"Redis exists error for key {key}: {e}")
                return False

        except Exception as e:
            logger.error(f"Failed to check cache existence: {e}")
            return False

    async def expire(self, key: str, ttl_seconds: int) -> bool:
        """Set expiration for a key."""
        try:
            if not self._is_connected:
                return False

            # Build full key
            full_key = f"{self.key_prefix}:{key}"

            try:
                result = await self.client.expire(full_key, ttl_seconds)
                return result

            except redis.RedisError as e:
                logger.error(f"Redis expire error for key {key}: {e}")
                return False

        except Exception as e:
            logger.error(f"Failed to set cache expiration: {e}")
            return False

    async def ttl(self, key: str) -> int:
        """Get time to live for a key."""
        try:
            if not self._is_connected:
                return -1

            # Build full key
            full_key = f"{self.key_prefix}:{key}"

            try:
                result = await self._client.ttl(full_key)
                return result

            except redis.RedisError as e:
                logger.error(f"Redis TTL error for key {key}: {e}")
                return -1

        except Exception as e:
            logger.error(f"Failed to get cache TTL: {e}")
            return -1

    async def get_stats(self) -> CacheStatistics:
        """Get cache statistics."""
        try:
            # Update memory usage
            self._update_memory_usage()

            return self._stats

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return CacheStatistics()

    async def health_check(self) -> bool:
        """Perform health check on Redis connection."""
        try:
            if not self._is_connected:
                return False

            try:
                await self._client.ping()
                self._last_health_check = datetime.now(timezone.utc)
                return True

            except redis.RedisError as e:
                logger.error(f"Redis health check failed: {e}")
                return False

        except Exception as e:
            logger.error(f"Failed to perform health check: {e}")
            return False

    def _keys(self, pattern: str) -> List[str]:
        """Get keys matching pattern."""
        # This is a placeholder - in practice, you'd use self._client.keys()
        return []

    @property
    def client(self) -> Optional[redis.Redis]:
        """Get Redis client."""
        return self._client

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
            if not self._is_connected:
                self._stats.memory_usage_percent = 0.0
                return

            # Get Redis info
            info = self._client.info("memory")
            used_memory = info.get("used_memory", 0)
            max_memory = info.get("maxmemory", 1)

            if max_memory > 0:
                self._stats.memory_usage_percent = (used_memory / max_memory) * 100

        except Exception as e:
            logger.error(f"Failed to update memory usage: {e}")
            self._stats.memory_usage_percent = 0.0

    def _initialize_metrics(self) -> None:
        """Initialize metrics collection."""
        try:
            # Define metrics for Redis cache
            self._metrics_collector.define_metric(
                name="redis_cache_hit_rate",
                metric_type=MetricType.GAUGE,
                category=MetricCategory.CACHE,
                description="Redis cache hit rate",
                unit="percent",
                labels=["cache_type"],
            )

            self._metrics_collector.define_metric(
                name="redis_cache_size",
                metric_type=MetricType.GAUGE,
                category=MetricCategory.CACHE,
                description="Redis cache size in bytes",
                unit="bytes",
            )

            self._metrics_collector.define_metric(
                name="redis_cache_memory_usage",
                metric_type=MetricType.GAUGE,
                category=MetricCategory.CACHE,
                description="Redis memory usage percentage",
                unit="percent",
            )

            self._metrics_collector.define_metric(
                name="redis_cache_operations",
                metric_type=MetricType.COUNTER,
                category=MetricCategory.CACHE,
                description="Redis cache operations count",
                unit="operations",
            )

        except Exception as e:
            logger.error(f"Failed to initialize metrics: {e}")

    def _start_background_tasks(self) -> None:
        """Start background tasks."""
        try:
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            self._metrics_task = asyncio.create_task(self._metrics_loop())

        except Exception as e:
            logger.error(f"Failed to start background tasks: {e}")

    async def _health_check_loop(self) -> None:
        """Background health check loop."""
        try:
            while True:
                await asyncio.sleep(self.health_check_interval)

                try:
                    is_healthy = await self.health_check()

                    if not is_healthy:
                        self._connection_error_count += 1

                        # Try to reconnect
                        if self._connection_error_count < self.retry_attempts:
                            await asyncio.sleep(self.retry_delay)
                            await self.connect()

                    # Update metrics
                    await self._metrics_collector.set_gauge(
                        "redis_cache_health",
                        1.0 if is_healthy else 0.0,
                        labels={"status": "healthy" if is_healthy else "unhealthy"},
                    )

                except Exception as e:
                    logger.error(f"Health check loop error: {e}")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Health check loop failed: {e}")

    async def _metrics_loop(self) -> None:
        """Background metrics collection loop."""
        try:
            while True:
                await asyncio.sleep(60)  # Update metrics every minute

                try:
                    # Update hit rate metric
                    await self._metrics_collector.set_gauge(
                        "redis_cache_hit_rate",
                        self._stats.hit_rate,
                        labels={"cache_type": "redis"},
                    )

                    # Update size metric
                    await self._metrics_collector.set_gauge(
                        "redis_cache_size",
                        self._stats.total_size_bytes,
                        labels={"cache_type": "redis"},
                    )

                    # Update memory usage metric
                    await self._metrics_collector.set_gauge(
                        "redis_cache_memory_usage",
                        self._stats.memory_usage_percent,
                        labels={"cache_type": "redis"},
                    )

                    # Update operations metric
                    await self._metrics_collector.increment_counter(
                        "redis_cache_operations",
                        labels={"cache_type": "redis"},
                    )

                except Exception as e:
                    logger.error(f"Metrics loop error: {e}")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Metrics loop failed: {e}")


class MemoryCache:
    """Memory-based cache implementation."""

    def __init__(self, max_size: int = 10000, default_ttl_seconds: int = 3600):
        self.max_size = max_size
        self.default_ttl_seconds = default_ttl_seconds
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: List[str] = []
        self._lock = asyncio.Lock()

        # Statistics
        self._stats = CacheStatistics()
        self._access_times: List[float] = []

        # Metrics collector
        self._metrics_collector = get_metrics_collector()

        # Initialize metrics
        self._initialize_metrics()

    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        try:
            start_time = time.time()

            async with self._lock:
                entry = self._cache.get(key)

                if entry is None:
                    self._stats.miss_count += 1
                    self._update_hit_rate()
                    return default

                # Check expiration
                if entry.expires_at and datetime.now(timezone.utc) > entry.expires_at:
                    # Remove expired entry
                    del self._cache[key]
                    self._access_order.remove(key)
                    self._stats.miss_count += 1
                    self._update_hit_rate()
                    return default

                # Update access statistics
                entry.access_count += 1
                entry.last_accessed = datetime.now(timezone.utc)

                # Move to end of access order
                if key in self._access_order:
                    self._access_order.remove(key)
                    self._access_order.append(key)

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
            _start_time = time.time()

            async with self._lock:
                # Calculate size
                size_bytes = len(pickle.dumps(value))

                # Check if eviction is needed
                if len(self._cache) >= self.max_size:
                    await self._evict_lru()

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
                    self._access_order.remove(key)

                    self._stats.total_entries = len(self._cache)
                    self._update_memory_usage()

                    return True

                return False

        except Exception as e:
            logger.error(f"Failed to delete from memory cache: {e}")
            return False

    async def clear(self) -> int:
        """Clear all cache entries."""
        try:
            async with self._lock:
                cleared_count = len(self._cache)

                self._cache.clear()
                self._access_order.clear()

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
            # Calculate approximate memory usage
            total_size = sum(entry.size_bytes for entry in self._cache.values())
            self._stats.total_size_bytes = total_size

            # Estimate memory usage percentage (rough approximation)
            # This is a simplified calculation
            import sys

            if hasattr(sys, "getsizeof"):
                cache_size = sys.getsizeof(self._cache) + sum(
                    sys.getsizeof(entry) for entry in self._cache.values()
                )
                # Assume 1MB = 1,048,576 bytes
                total_memory = 100 * 1024 * 1024  # 100MB estimate
                if total_memory > 0:
                    self._stats.memory_usage_percent = (cache_size / total_memory) * 100

        except Exception as e:
            logger.error(f"Failed to update memory usage: {e}")
            self._stats.memory_usage_percent = 0.0

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
                self._stats.eviction_count += 1
                self._update_memory_usage()

        except Exception as e:
            logger.error(f"Failed to evict LRU entry: {e}")

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


# Factory functions
def create_redis_cache(redis_url: str, **kwargs) -> RedisCache:
    """Create Redis cache instance."""
    return RedisCache(redis_url, **kwargs)


def create_memory_cache(**kwargs) -> MemoryCache:
    """Create memory cache instance."""
    return MemoryCache(**kwargs)
