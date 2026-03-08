"""
Cache Manager for Phase 15.1 Database & Performance
"""

from __future__ import annotations

import uuid
import json
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from collections import defaultdict
import pickle
import redis.asyncio as redis

from shared.logging_config import get_logger

logger = get_logger("sorce.cache_manager")


class CacheType(Enum):
    """Types of cache."""

    MEMORY = "memory"
    REDIS = "redis"
    DISTRIBUTED = "distributed"
    HYBRID = "hybrid"


class CacheStrategy(Enum):
    """Cache eviction strategies."""

    LRU = "lru"
    LFU = "lfu"
    FIFO = "fifo"
    TTL = "ttl"
    MANUAL = "manual"


class CacheLevel(Enum):
    """Cache levels."""

    L1_MEMORY = "l1_memory"
    L2_REDIS = "l2_redis"
    L3_DATABASE = "l3_database"


@dataclass
class CacheEntry:
    """Cache entry."""

    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime]
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    size_bytes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheStats:
    """Cache statistics."""

    cache_type: str
    total_entries: int
    total_size_bytes: int
    hit_count: int
    miss_count: int
    eviction_count: int
    hit_rate: float
    avg_access_time_ms: float
    memory_usage_percent: float
    last_updated: datetime = datetime.now(timezone.utc)


@dataclass
class CacheConfiguration:
    """Cache configuration."""

    cache_type: CacheType
    max_size: int
    ttl_seconds: int
    strategy: CacheStrategy
    compression_enabled: bool = False
    serialization_method: str = "json"
    eviction_threshold: float = 0.8
    cleanup_interval_seconds: int = 300
    metrics_enabled: bool = True


class CacheManager:
    """Advanced multi-level caching system."""

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url
        self._memory_cache: Dict[str, CacheEntry] = {}
        self._redis_client: Optional[redis.Redis] = None
        self._cache_configs: Dict[str, CacheConfiguration] = {}
        self._cache_stats: Dict[str, CacheStats] = {}
        self._access_times: Dict[str, List[datetime]] = defaultdict(list)

        # Initialize default configurations
        self._initialize_default_configs()

        # Initialize Redis if available
        asyncio.create_task(self._initialize_redis())

        # Start background cleanup
        asyncio.create_task(self._start_cleanup_task())

    async def get(
        self,
        key: str,
        cache_level: Optional[CacheLevel] = None,
        default: Any = None,
    ) -> Any:
        """Get value from cache."""
        try:
            start_time = datetime.now(timezone.utc)

            # Try memory cache first
            if cache_level is None or cache_level == CacheLevel.L1_MEMORY:
                value = await self._get_from_memory(key)
                if value is not None:
                    await self._record_hit("memory", key, start_time)
                    return value

            # Try Redis cache
            if cache_level is None or cache_level == CacheLevel.L2_REDIS:
                if self._redis_client:
                    value = await self._get_from_redis(key)
                    if value is not None:
                        # Store in memory cache for faster access
                        await self._set_in_memory(
                            key, value, ttl_seconds=300
                        )  # 5 minutes
                        await self._record_hit("redis", key, start_time)
                        return value

            # Record miss
            await self._record_miss("cache", key, start_time)
            return default

        except Exception as e:
            logger.error(f"Failed to get from cache: {e}")
            return default

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        cache_levels: Optional[List[CacheLevel]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Set value in cache."""
        try:
            success = True

            # Default to all cache levels
            if cache_levels is None:
                cache_levels = [CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS]

            # Determine TTL
            if ttl_seconds is None:
                ttl_seconds = self._cache_configs.get("default", {}).ttl_seconds

            # Set in memory cache
            if CacheLevel.L1_MEMORY in cache_levels:
                success &= await self._set_in_memory(key, value, ttl_seconds, metadata)

            # Set in Redis cache
            if CacheLevel.L2_REDIS in cache_levels and self._redis_client:
                success &= await self._set_in_redis(key, value, ttl_seconds, metadata)

            return success

        except Exception as e:
            logger.error(f"Failed to set in cache: {e}")
            return False

    async def delete(
        self, key: str, cache_levels: Optional[List[CacheLevel]] = None
    ) -> bool:
        """Delete value from cache."""
        try:
            success = True

            # Default to all cache levels
            if cache_levels is None:
                cache_levels = [CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS]

            # Delete from memory cache
            if CacheLevel.L1_MEMORY in cache_levels:
                success &= await self._delete_from_memory(key)

            # Delete from Redis cache
            if CacheLevel.L2_REDIS in cache_levels and self._redis_client:
                success &= await self._delete_from_redis(key)

            return success

        except Exception as e:
            logger.error(f"Failed to delete from cache: {e}")
            return False

    async def clear(
        self,
        cache_level: Optional[CacheLevel] = None,
        pattern: Optional[str] = None,
    ) -> bool:
        """Clear cache entries."""
        try:
            if cache_level is None:
                # Clear all levels
                success = await self._clear_memory(pattern)
                if self._redis_client:
                    success &= await self._clear_redis(pattern)
                return success
            elif cache_level == CacheLevel.L1_MEMORY:
                return await self._clear_memory(pattern)
            elif cache_level == CacheLevel.L2_REDIS and self._redis_client:
                return await self._clear_redis(pattern)

            return False

        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False

    async def get_stats(
        self, cache_type: Optional[str] = None
    ) -> Dict[str, CacheStats]:
        """Get cache statistics."""
        try:
            if cache_type:
                return {cache_type: self._cache_stats.get(cache_type)}

            return self._cache_stats.copy()

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}

    async def warm_cache(
        self,
        data_loader: callable,
        keys: List[str],
        ttl_seconds: Optional[int] = None,
    ) -> Dict[str, bool]:
        """Warm cache with data."""
        try:
            results = {}

            # Check which keys need loading
            keys_to_load = []
            for key in keys:
                if not await self._get_from_memory(key):
                    keys_to_load.append(key)

            if not keys_to_load:
                return {key: True for key in keys}  # All keys already cached

            # Load data
            try:
                data = await data_loader(keys_to_load)
            except Exception as e:
                logger.error(f"Failed to load data for cache warming: {e}")
                return {key: False for key in keys}

            # Store in cache
            for key in keys_to_load:
                value = data.get(key) if isinstance(data, dict) else None
                if value is not None:
                    success = await self.set(key, value, ttl_seconds)
                    results[key] = success
                else:
                    results[key] = False

            return results

        except Exception as e:
            logger.error(f"Failed to warm cache: {e}")
            return {key: False for key in keys}

    def _initialize_default_configs(self) -> None:
        """Initialize default cache configurations."""
        self._cache_configs = {
            "default": CacheConfiguration(
                cache_type=CacheType.HYBRID,
                max_size=10000,
                ttl_seconds=3600,  # 1 hour
                strategy=CacheStrategy.LRU,
                compression_enabled=False,
                serialization_method="json",
                eviction_threshold=0.8,
                cleanup_interval_seconds=300,
                metrics_enabled=True,
            ),
            "session": CacheConfiguration(
                cache_type=CacheType.MEMORY,
                max_size=1000,
                ttl_seconds=1800,  # 30 minutes
                strategy=CacheStrategy.TTL,
                compression_enabled=False,
                serialization_method="json",
                eviction_threshold=0.9,
                cleanup_interval_seconds=600,
                metrics_enabled=True,
            ),
            "query": CacheConfiguration(
                cache_type=CacheType.REDIS,
                max_size=50000,
                ttl_seconds=7200,  # 2 hours
                strategy=CacheStrategy.LFU,
                compression_enabled=True,
                serialization_method="pickle",
                eviction_threshold=0.7,
                cleanup_interval_seconds=300,
                metrics_enabled=True,
            ),
            "static": CacheConfiguration(
                cache_type=CacheType.REDIS,
                max_size=100000,
                ttl_seconds=86400,  # 24 hours
                strategy=CacheStrategy.LRU,
                compression_enabled=True,
                serialization_method="json",
                eviction_threshold=0.6,
                cleanup_interval_seconds=1800,
                metrics_enabled=True,
            ),
        }

        # Initialize stats
        for config_name in self._cache_configs:
            self._cache_stats[config_name] = CacheStats(
                cache_type=config_name,
                total_entries=0,
                total_size_bytes=0,
                hit_count=0,
                miss_count=0,
                eviction_count=0,
                hit_rate=0.0,
                avg_access_time_ms=0.0,
                memory_usage_percent=0.0,
            )

    async def _initialize_redis(self) -> None:
        """Initialize Redis client."""
        try:
            if self.redis_url:
                self._redis_client = redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=False,
                )

                # Test connection
                await self._redis_client.ping()
                logger.info("Redis client initialized successfully")
            else:
                logger.warning("Redis URL not provided, Redis cache disabled")

        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            self._redis_client = None

    async def _start_cleanup_task(self) -> None:
        """Start background cleanup task."""
        try:
            while True:
                await asyncio.sleep(60)  # Run every minute

                # Clean expired entries
                await self._cleanup_expired_entries()

                # Evict entries if necessary
                await self._evict_if_necessary()

                # Update statistics
                await self._update_statistics()

        except Exception as e:
            logger.error(f"Background cleanup task failed: {e}")

    async def _get_from_memory(self, key: str) -> Any:
        """Get value from memory cache."""
        try:
            entry = self._memory_cache.get(key)
            if entry is None:
                return None

            # Check expiration
            if entry.expires_at and datetime.now(timezone.utc) > entry.expires_at:
                del self._memory_cache[key]
                return None

            # Update access statistics
            entry.access_count += 1
            entry.last_accessed = datetime.now(timezone.utc)
            self._access_times[key].append(datetime.now(timezone.utc))

            return entry.value

        except Exception as e:
            logger.error(f"Failed to get from memory cache: {e}")
            return None

    async def _set_in_memory(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Set value in memory cache."""
        try:
            # Calculate size
            serialized_value = json.dumps(value, default=str)
            size_bytes = len(serialized_value.encode("utf-8"))

            # Check if eviction is needed
            if len(self._memory_cache) >= self._cache_configs["default"].max_size:
                await self._evict_from_memory()

            # Calculate expiration
            expires_at = None
            if ttl_seconds:
                expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

            # Create entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(timezone.utc),
                expires_at=expires_at,
                size_bytes=size_bytes,
                metadata=metadata or {},
            )

            self._memory_cache[key] = entry
            return True

        except Exception as e:
            logger.error(f"Failed to set in memory cache: {e}")
            return False

    async def _delete_from_memory(self, key: str) -> bool:
        """Delete value from memory cache."""
        try:
            if key in self._memory_cache:
                del self._memory_cache[key]
                if key in self._access_times:
                    del self._access_times[key]
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to delete from memory cache: {e}")
            return False

    async def _get_from_redis(self, key: str) -> Any:
        """Get value from Redis cache."""
        try:
            if not self._redis_client:
                return None

            # Get from Redis
            data = await self._redis_client.get(key)
            if data is None:
                return None

            # Deserialize
            try:
                value = pickle.loads(data)
            except (pickle.PickleError, TypeError):
                # Fallback to JSON
                value = json.loads(data.decode("utf-8"))

            return value

        except Exception as e:
            logger.error(f"Failed to get from Redis cache: {e}")
            return None

    async def _set_in_redis(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Set value in Redis cache."""
        try:
            if not self._redis_client:
                return False

            # Serialize
            try:
                data = pickle.dumps(value)
            except (pickle.PickleError, TypeError):
                # Fallback to JSON
                data = json.dumps(value, default=str).encode("utf-8")

            # Set in Redis
            if ttl_seconds:
                await self._redis_client.setex(key, ttl_seconds, data)
            else:
                await self._redis_client.set(key, data)

            return True

        except Exception as e:
            logger.error(f"Failed to set in Redis cache: {e}")
            return False

    async def _delete_from_redis(self, key: str) -> bool:
        """Delete value from Redis cache."""
        try:
            if not self._redis_client:
                return False

            result = await self._redis_client.delete(key)
            return result > 0

        except Exception as e:
            logger.error(f"Failed to delete from Redis cache: {e}")
            return False

    async def _clear_memory(self, pattern: Optional[str] = None) -> bool:
        """Clear memory cache."""
        try:
            if pattern:
                keys_to_delete = [k for k in self._memory_cache.keys() if pattern in k]
                for key in keys_to_delete:
                    del self._memory_cache[key]
                    if key in self._access_times:
                        del self._access_times[key]
            else:
                self._memory_cache.clear()
                self._access_times.clear()

            return True

        except Exception as e:
            logger.error(f"Failed to clear memory cache: {e}")
            return False

    async def _clear_redis(self, pattern: Optional[str] = None) -> bool:
        """Clear Redis cache."""
        try:
            if not self._redis_client:
                return False

            if pattern:
                # Delete keys matching pattern
                keys = await self._redis_client.keys(f"*{pattern}*")
                if keys:
                    await self._redis_client.delete(*keys)
            else:
                # Clear all keys (be careful with this in production)
                await self._redis_client.flushdb()

            return True

        except Exception as e:
            logger.error(f"Failed to clear Redis cache: {e}")
            return False

    async def _cleanup_expired_entries(self) -> None:
        """Clean up expired entries."""
        try:
            now = datetime.now(timezone.utc)
            expired_keys = []

            for key, entry in self._memory_cache.items():
                if entry.expires_at and now > entry.expires_at:
                    expired_keys.append(key)

            for key in expired_keys:
                del self._memory_cache[key]
                if key in self._access_times:
                    del self._access_times[key]

            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

        except Exception as e:
            logger.error(f"Failed to cleanup expired entries: {e}")

    async def _evict_if_necessary(self) -> None:
        """Evict entries if cache is full."""
        try:
            config = self._cache_configs["default"]
            current_size = len(self._memory_cache)
            max_size = config.max_size

            if current_size >= max_size * config.eviction_threshold:
                await self._evict_from_memory()

        except Exception as e:
            logger.error(f"Failed to evict entries: {e}")

    async def _evict_from_memory(self) -> None:
        """Evict entries from memory cache based on strategy."""
        try:
            config = self._cache_configs["default"]
            strategy = config.strategy

            if strategy == CacheStrategy.LRU:
                await self._evict_lru()
            elif strategy == CacheStrategy.LFU:
                await self._evict_lfu()
            elif strategy == CacheStrategy.FIFO:
                await self._evict_fifo()
            elif strategy == CacheStrategy.TTL:
                await self._evict_ttl()
            else:
                await self._evict_lru()  # Default to LRU

        except Exception as e:
            logger.error(f"Failed to evict from memory: {e}")

    async def _evict_lru(self) -> None:
        """Evict least recently used entries."""
        try:
            # Sort by last accessed time
            sorted_entries = sorted(
                self._memory_cache.items(),
                key=lambda item: item[1].last_accessed or item[1].created_at,
            )

            # Evict 10% of entries
            evict_count = max(1, len(sorted_entries) // 10)
            for i in range(evict_count):
                key = sorted_entries[i][0]
                del self._memory_cache[key]
                if key in self._access_times:
                    del self._access_times[key]

            logger.debug(f"Evicted {evict_count} entries using LRU strategy")

        except Exception as e:
            logger.error(f"Failed to evict LRU: {e}")

    async def _evict_lfu(self) -> None:
        """Evict least frequently used entries."""
        try:
            # Sort by access count
            sorted_entries = sorted(
                self._memory_cache.items(), key=lambda item: item[1].access_count
            )

            # Evict 10% of entries
            evict_count = max(1, len(sorted_entries) // 10)
            for i in range(evict_count):
                key = sorted_entries[i][0]
                del self._memory_cache[key]
                if key in self._access_times:
                    del self._access_times[key]

            logger.debug(f"Evicted {evict_count} entries using LFU strategy")

        except Exception as e:
            logger.error(f"Failed to evict LFU: {e}")

    async def _evict_fifo(self) -> None:
        """Evict first-in-first-out entries."""
        try:
            # Sort by creation time
            sorted_entries = sorted(
                self._memory_cache.items(), key=lambda item: item[1].created_at
            )

            # Evict 10% of entries
            evict_count = max(1, len(sorted_entries) // 10)
            for i in range(evict_count):
                key = sorted_entries[i][0]
                del self._memory_cache[key]
                if key in self._access_times:
                    del self._access_times[key]

            logger.debug(f"Evicted {evict_count} entries using FIFO strategy")

        except Exception as e:
            logger.error(f"Failed to evict FIFO: {e}")

    async def _evict_ttl(self) -> None:
        """Evict entries with shortest TTL."""
        try:
            # Sort by expiration time
            entries_with_ttl = [
                (key, entry)
                for key, entry in self._memory_cache.items()
                if entry.expires_at
            ]

            if not entries_with_ttl:
                return

            sorted_entries = sorted(
                entries_with_ttl, key=lambda item: item[1].expires_at
            )

            # Evict 10% of entries
            evict_count = max(1, len(sorted_entries) // 10)
            for i in range(evict_count):
                key = sorted_entries[i][0]
                del self._memory_cache[key]
                if key in self._access_times:
                    del self._access_times[key]

            logger.debug(f"Evicted {evict_count} entries using TTL strategy")

        except Exception as e:
            logger.error(f"Failed to evict TTL: {e}")

    async def _record_hit(
        self,
        cache_type: str,
        key: str,
        start_time: datetime,
    ) -> None:
        """Record cache hit."""
        try:
            # Update stats
            if cache_type not in self._cache_stats:
                self._cache_stats[cache_type] = CacheStats(
                    cache_type=cache_type,
                    total_entries=0,
                    total_size_bytes=0,
                    hit_count=0,
                    miss_count=0,
                    eviction_count=0,
                    hit_rate=0.0,
                    avg_access_time_ms=0.0,
                    memory_usage_percent=0.0,
                )

            stats = self._cache_stats[cache_type]
            stats.hit_count += 1

            # Calculate hit rate
            total_requests = stats.hit_count + stats.miss_count
            if total_requests > 0:
                stats.hit_rate = stats.hit_count / total_requests

            # Update access time
            access_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000
            if stats.avg_access_time_ms == 0:
                stats.avg_access_time_ms = access_time
            else:
                stats.avg_access_time_ms = (
                    stats.avg_access_time_ms * 0.9 + access_time * 0.1
                )

            stats.last_updated = datetime.now(timezone.utc)

        except Exception as e:
            logger.error(f"Failed to record hit: {e}")

    async def _record_miss(
        self,
        cache_type: str,
        key: str,
        start_time: datetime,
    ) -> None:
        """Record cache miss."""
        try:
            # Update stats
            if cache_type not in self._cache_stats:
                self._cache_stats[cache_type] = CacheStats(
                    cache_type=cache_type,
                    total_entries=0,
                    total_size_bytes=0,
                    hit_count=0,
                    miss_count=0,
                    eviction_count=0,
                    hit_rate=0.0,
                    avg_access_time_ms=0.0,
                    memory_usage_percent=0.0,
                )

            stats = self._cache_stats[cache_type]
            stats.miss_count += 1

            # Calculate hit rate
            total_requests = stats.hit_count + stats.miss_count
            if total_requests > 0:
                stats.hit_rate = stats.hit_count / total_requests

            stats.last_updated = datetime.now(timezone.utc)

        except Exception as e:
            logger.error(f"Failed to record miss: {e}")

    async def _update_statistics(self) -> None:
        """Update cache statistics."""
        try:
            # Update memory cache stats
            if "memory" not in self._cache_stats:
                self._cache_stats["memory"] = CacheStats(
                    cache_type="memory",
                    total_entries=0,
                    total_size_bytes=0,
                    hit_count=0,
                    miss_count=0,
                    eviction_count=0,
                    hit_rate=0.0,
                    avg_access_time_ms=0.0,
                    memory_usage_percent=0.0,
                )

            memory_stats = self._cache_stats["memory"]
            memory_stats.total_entries = len(self._memory_cache)
            memory_stats.total_size_bytes = sum(
                entry.size_bytes for entry in self._memory_cache.values()
            )

            # Update Redis stats if available
            if self._redis_client and "redis" not in self._cache_stats:
                self._cache_stats["redis"] = CacheStats(
                    cache_type="redis",
                    total_entries=0,
                    total_size_bytes=0,
                    hit_count=0,
                    miss_count=0,
                    eviction_count=0,
                    hit_rate=0.0,
                    avg_access_time_ms=0.0,
                    memory_usage_percent=0.0,
                )

            if self._redis_client:
                try:
                    info = await self._redis_client.info("memory")
                    redis_stats = self._cache_stats["redis"]
                    redis_stats.memory_usage_percent = (
                        info.get("used_memory", 0) / info.get("maxmemory", 1) * 100
                    )
                except Exception as e:
                    logger.error(f"Failed to get Redis info: {e}")

        except Exception as e:
            logger.error(f"Failed to update statistics: {e}")

    def get_cache_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        try:
            # Create a deterministic key from arguments
            key_parts = []

            # Add positional arguments
            for arg in args:
                if isinstance(arg, (str, int, float, bool)):
                    key_parts.append(str(arg))
                else:
                    key_parts.append(hashlib.md5(str(arg).encode()).hexdigest())

            # Add keyword arguments
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}={v}")

            # Join with separator
            return ":".join(key_parts)

        except Exception as e:
            logger.error(f"Failed to generate cache key: {e}")
            return str(uuid.uuid4())

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern."""
        try:
            count = 0

            # Invalidate from memory cache
            memory_keys = [k for k in self._memory_cache.keys() if pattern in k]
            for key in memory_keys:
                await self._delete_from_memory(key)
                count += 1

            # Invalidate from Redis
            if self._redis_client:
                redis_keys = await self._redis_client.keys(f"*{pattern}*")
                if redis_keys:
                    await self._redis_client.delete(*redis_keys)
                    count += len(redis_keys)

            logger.info(
                f"Invalidated {count} cache entries matching pattern: {pattern}"
            )
            return count

        except Exception as e:
            logger.error(f"Failed to invalidate pattern: {e}")
            return 0

    async def get_cache_health(self) -> Dict[str, Any]:
        """Get cache health information."""
        try:
            health = {
                "memory_cache": {
                    "status": "healthy",
                    "entries": len(self._memory_cache),
                    "size_mb": sum(
                        entry.size_bytes for entry in self._memory_cache.values()
                    )
                    / (1024 * 1024),
                    "hit_rate": self._cache_stats.get(
                        "memory",
                        CacheStats(
                            cache_type="memory",
                            total_entries=0,
                            total_size_bytes=0,
                            hit_count=0,
                            miss_count=0,
                            eviction_count=0,
                            hit_rate=0.0,
                            avg_access_time_ms=0.0,
                            memory_usage_percent=0.0,
                        ),
                    ).hit_rate,
                },
                "redis_cache": {
                    "status": "healthy" if self._redis_client else "disabled",
                    "hit_rate": self._cache_stats.get(
                        "redis",
                        CacheStats(
                            cache_type="redis",
                            total_entries=0,
                            total_size_bytes=0,
                            hit_count=0,
                            miss_count=0,
                            eviction_count=0,
                            hit_rate=0.0,
                            avg_access_time_ms=0.0,
                            memory_usage_percent=0.0,
                        ),
                    ).hit_rate,
                },
                "overall": {
                    "status": "healthy",
                    "total_hit_rate": 0.0,
                    "total_entries": len(self._memory_cache),
                },
            }

            # Calculate overall hit rate
            total_hits = sum(stats.hit_count for stats in self._cache_stats.values())
            total_misses = sum(stats.miss_count for stats in self._cache_stats.values())
            total_requests = total_hits + total_misses

            if total_requests > 0:
                health["overall"]["total_hit_rate"] = total_hits / total_requests

            # Determine overall status
            if health["memory_cache"]["hit_rate"] < 0.5:
                health["memory_cache"]["status"] = "degraded"
                health["overall"]["status"] = "degraded"

            if (
                health["redis_cache"]["status"] == "healthy"
                and health["redis_cache"]["hit_rate"] < 0.5
            ):
                health["redis_cache"]["status"] = "degraded"
                health["overall"]["status"] = "degraded"

            return health

        except Exception as e:
            logger.error(f"Failed to get cache health: {e}")
            return {"status": "error", "error": str(e)}


# Factory function
def create_cache_manager(redis_url: Optional[str] = None) -> CacheManager:
    """Create cache manager instance."""
    return CacheManager(redis_url)
