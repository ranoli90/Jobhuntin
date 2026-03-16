"""Tests for query caching functionality.

Tests cover:
- Cache key generation with different prefixes
- TTL behavior for different cache types
- Cache invalidation (specific keys and patterns)
- Cache decorator behavior
- QueryCache context manager

These tests focus on the Phase 1-2 caching fixes:
- Cache key generation security (consistent hashing)
- TTL configuration per cache type
- Proper invalidation patterns
"""

import pytest
from datetime import timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from shared.query_cache import (
    _make_cache_key,
    get_cached,
    set_cached,
    delete_cached,
    delete_pattern,
    cached,
    QueryCache,
    DEFAULT_TTL,
    PROFILE_TTL,
    JOB_LISTINGS_TTL,
    TENANT_CONFIG_TTL,
)


class TestCacheKeyGeneration:
    """Tests for cache key generation."""

    def test_make_cache_key_basic(self):
        """Basic cache key generation works."""
        key = _make_cache_key("user", "123")
        assert key.startswith("cache:user:")
        assert len(key) > 15  # prefix + : + 16-char hash

    def test_make_cache_key_with_kwargs(self):
        """Cache keys include kwargs in hash."""
        key1 = _make_cache_key("profile", "123", include_stats=True)
        key2 = _make_cache_key("profile", "123", include_stats=False)
        
        # Different kwargs should produce different keys
        assert key1 != key2

    def test_make_cache_key_consistency(self):
        """Same inputs produce same cache key."""
        key1 = _make_cache_key("job", "456", status="active")
        key2 = _make_cache_key("job", "456", status="active")
        
        assert key1 == key2

    def test_make_cache_key_different_args(self):
        """Different arguments produce different keys."""
        key1 = _make_cache_key("user", "123")
        key2 = _make_cache_key("user", "456")
        
        assert key1 != key2

    def test_make_cache_key_special_characters(self):
        """Special characters are handled in key generation."""
        key = _make_cache_key("search", query="test@example.com")
        
        assert key.startswith("cache:search:")
        # Key is hashed, so we just verify it's generated
        assert len(key) > 15

    def test_make_cache_key_unicode(self):
        """Unicode characters are handled in key generation."""
        key = _make_cache_key("user", name="日本語")
        
        assert key.startswith("cache:user:")

    def test_make_cache_key_sorting(self):
        """Kwargs are sorted for consistent keys."""
        key1 = _make_cache_key("test", a="1", b="2", c="3")
        key2 = _make_cache_key("test", c="3", a="1", b="2")
        
        # Same args, different order - should produce same key
        assert key1 == key2


class TestTTLConstants:
    """Tests for TTL configuration constants."""

    def test_default_ttl_is_5_minutes(self):
        """DEFAULT_TTL should be 5 minutes."""
        assert DEFAULT_TTL == timedelta(minutes=5)

    def test_profile_ttl_is_15_minutes(self):
        """PROFILE_TTL should be 15 minutes (longer cache for profiles)."""
        assert PROFILE_TTL == timedelta(minutes=15)

    def test_job_listings_ttl_is_2_minutes(self):
        """JOB_LISTINGS_TTL should be 2 minutes (short for frequently changing data)."""
        assert JOB_LISTINGS_TTL == timedelta(minutes=2)

    def test_tenant_config_ttl_is_1_hour(self):
        """TENANT_CONFIG_TTL should be 1 hour (longest for rarely changing config)."""
        assert TENANT_CONFIG_TTL == timedelta(hours=1)


class TestCacheOperations:
    """Tests for cache get/set/delete operations."""

    @pytest.mark.asyncio
    async def test_get_cached_returns_none_for_missing_key(self):
        """get_cached returns None when key doesn't exist."""
        with patch("shared.query_cache.get_redis") as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis_instance.get.return_value = None
            mock_redis.return_value = mock_redis_instance

            result = await get_cached("nonexistent_key")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_get_cached_returns_cached_data(self):
        """get_cached returns cached data when exists."""
        import json
        
        with patch("shared.query_cache.get_redis") as mock_redis:
            mock_redis_instance = AsyncMock()
            test_data = {"id": "123", "name": "test"}
            mock_redis_instance.get.return_value = json.dumps(test_data).encode()
            mock_redis.return_value = mock_redis_instance

            result = await get_cached("cache:test:abc123")
            
            assert result == test_data

    @pytest.mark.asyncio
    async def test_get_cached_returns_none_on_error(self):
        """get_cached returns None on Redis errors (fail-open)."""
        with patch("shared.query_cache.get_redis") as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis_instance.get.side_effect = Exception("Redis connection error")
            mock_redis.return_value = mock_redis_instance

            result = await get_cached("cache:test:abc123")
            
            # Should fail-open (return None) rather than raise
            assert result is None

    @pytest.mark.asyncio
    async def test_set_cached_returns_true_on_success(self):
        """set_cached returns True on successful cache set."""
        with patch("shared.query_cache.get_redis") as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis.return_value = mock_redis_instance

            result = await set_cached("cache:test:abc", {"data": "value"})
            
            assert result is True
            mock_redis_instance.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_cached_uses_ttl(self):
        """set_cached uses the provided TTL."""
        with patch("shared.query_cache.get_redis") as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis.return_value = mock_redis_instance

            custom_ttl = timedelta(seconds=300)
            await set_cached("cache:test:abc", {"data": "value"}, ttl=custom_ttl)
            
            # Verify setex was called with the custom TTL in seconds
            call_args = mock_redis_instance.setex.call_args
            assert call_args[0][1] == 300  # TTL in seconds

    @pytest.mark.asyncio
    async def test_set_cached_returns_false_on_error(self):
        """set_cached returns False on Redis errors."""
        with patch("shared.query_cache.get_redis") as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis_instance.setex.side_effect = Exception("Redis error")
            mock_redis.return_value = mock_redis_instance

            result = await set_cached("cache:test:abc", {"data": "value"})
            
            assert result is False

    @pytest.mark.asyncio
    async def test_delete_cached_returns_true_on_success(self):
        """delete_cached returns True on successful deletion."""
        with patch("shared.query_cache.get_redis") as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis.return_value = mock_redis_instance

            result = await delete_cached("cache:test:abc")
            
            assert result is True

    @pytest.mark.asyncio
    async def test_delete_pattern_deletes_matching_keys(self):
        """delete_pattern deletes all keys matching the pattern."""
        with patch("shared.query_cache.get_redis") as mock_redis:
            mock_redis_instance = AsyncMock()
            # Simulate scan_iter returning multiple keys - use async generator
            async def async_iter(match=None):
                yield b"cache:user:abc"
                yield b"cache:user:def"
            mock_redis_instance.scan_iter = async_iter
            mock_redis.return_value = mock_redis_instance

            count = await delete_pattern("cache:user:*")
            
            assert count == 2
            mock_redis_instance.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_pattern_returns_zero_on_error(self):
        """delete_pattern returns 0 on error."""
        with patch("shared.query_cache.get_redis") as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis_instance.scan_iter.side_effect = Exception("Redis error")
            mock_redis.return_value = mock_redis_instance

            count = await delete_pattern("cache:test:*")
            
            assert count == 0


class TestCachedDecorator:
    """Tests for the @cached decorator."""

    @pytest.mark.asyncio
    async def test_cached_decorator_caches_result(self):
        """Decorator caches function results."""
        call_count = 0
        
        @cached("test", ttl=timedelta(minutes=5))
        async def get_data(key):
            nonlocal call_count
            call_count += 1
            return {"data": key}
        
        with patch("shared.query_cache.get_redis") as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis_instance.get.return_value = None  # Cache miss
            mock_redis.return_value = mock_redis_instance

            result1 = await get_data("abc")
            
            assert call_count == 1
            assert result1 == {"data": "abc"}

    @pytest.mark.asyncio
    async def test_cached_decorator_returns_cached_on_hit(self):
        """Decorator returns cached result on cache hit."""
        
        @cached("test", ttl=timedelta(minutes=5))
        async def get_data(key):
            return {"fresh": True}
        
        with patch("shared.query_cache.get_redis") as mock_redis:
            mock_redis_instance = AsyncMock()
            # Return cached data
            mock_redis_instance.get.return_value = '{"cached": true}'
            mock_redis.return_value = mock_redis_instance

            result = await get_data("abc")
            
            # Should return cached data, not call the function
            assert result == {"cached": True}

    @pytest.mark.asyncio
    async def test_cached_decorator_skips_cache_for_none(self):
        """Decorator doesn't cache None results."""
        
        @cached("test", ttl=timedelta(minutes=5))
        async def get_data(key):
            return None
        
        with patch("shared.query_cache.get_redis") as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis_instance.get.return_value = None
            mock_redis.return_value = mock_redis_instance

            result = await get_data("abc")
            
            assert result is None
            # set_cached should not be called for None results
            mock_redis_instance.setex.assert_not_called()

    @pytest.mark.asyncio
    async def test_cached_decorator_custom_key_builder(self):
        """Decorator supports custom key builder function."""
        
        def custom_key_builder(*args, **kwargs):
            return f"custom:{args[1]}"
        
        @cached("test", ttl=timedelta(minutes=5), key_builder=custom_key_builder)
        async def get_data(prefix, user_id):
            return {"user": user_id}
        
        with patch("shared.query_cache.get_redis") as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis_instance.get.return_value = None
            mock_redis.return_value = mock_redis_instance

            await get_data("test", "user123")
            
            # Verify custom key was used
            mock_redis_instance.get.assert_called_with("custom:user123")


class TestQueryCacheContextManager:
    """Tests for QueryCache context manager."""

    @pytest.mark.asyncio
    async def test_query_cache_get_or_set_returns_cached(self):
        """QueryCache returns cached value on hit."""
        cache = QueryCache("user", ttl=timedelta(minutes=5))
        
        with patch("shared.query_cache.get_cached") as mock_get:
            mock_get.return_value = {"cached": "data"}
            
            result = await cache.get_or_set("key1", lambda: {"fresh": "data"})
            
            assert result == {"cached": "data"}

    @pytest.mark.asyncio
    async def test_query_cache_get_or_set_caches_fresh(self):
        """QueryCache caches fresh value on miss."""
        cache = QueryCache("user", ttl=timedelta(minutes=5))
        
        with patch("shared.query_cache.get_cached") as mock_get:
            with patch("shared.query_cache.set_cached") as mock_set:
                mock_get.return_value = None
                mock_set.return_value = True
                
                factory = AsyncMock(return_value={"fresh": "data"})
                result = await cache.get_or_set("key1", factory)
                
                assert result == {"fresh": "data"}
                mock_set.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_cache_invalidate_specific_key(self):
        """QueryCache can invalidate a specific key."""
        cache = QueryCache("user", ttl=timedelta(minutes=5))
        
        with patch("shared.query_cache.delete_cached") as mock_delete:
            mock_delete.return_value = True
            
            result = await cache.invalidate("key1")
            
            assert result is True
            mock_delete.assert_called_with("user:key1")

    @pytest.mark.asyncio
    async def test_query_cache_invalidate_all(self):
        """QueryCache can invalidate all keys with prefix."""
        cache = QueryCache("user", ttl=timedelta(minutes=5))
        
        with patch("shared.query_cache.delete_pattern") as mock_delete:
            mock_delete.return_value = 5
            
            result = await cache.invalidate_all()
            
            assert result == 5
            mock_delete.assert_called_with("user:*")
