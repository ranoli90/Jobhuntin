# Query Caching Implementation Guide

This document describes the query caching system implemented in the JobHuntin codebase to reduce database load for frequently-accessed read-only data.

## Overview

The caching system is built on Redis and provides:
- **Decorator-based caching** for async functions
- **Manual cache control** with get/set/delete operations
- **Pattern-based invalidation** for bulk cache clearing
- **Pre-configured cache instances** for common data types

## Cache Infrastructure

### Core Module: `shared/query_cache.py`

The query cache module provides the main caching API:

```python
from shared.query_cache import (
    # TTL constants
    DEFAULT_TTL,         # 5 minutes
    PROFILE_TTL,         # 15 minutes
    JOB_LISTINGS_TTL,    # 2 minutes
    TENANT_CONFIG_TTL,   # 1 hour
    
    # Core functions
    get_cached,
    set_cached,
    delete_cached,
    delete_pattern,
    
    # Convenience functions
    invalidate_cache,
    invalidate_pattern,
    make_cache_key,
    
    # Decorator
    cached,
    
    # Pre-configured cache instances
    profile_cache,
    job_cache,
    tenant_cache,
)
```

### TTL Guidelines

| Data Type | TTL | Rationale |
|-----------|-----|-----------|
| Job listings | 2 minutes | Jobs may be updated frequently |
| User profiles | 15 minutes | Profile data changes moderately |
| Tenant config | 1 hour | Configuration rarely changes |
| Default | 5 minutes | Safe default for most data |

## Usage Patterns

### 1. Decorator-Based Caching

Use the `@cached` decorator for simple functions with serializable arguments:

```python
from shared.query_cache import cached, PROFILE_TTL

@cached(prefix="user_preferences", ttl=PROFILE_TTL)
async def get_user_preferences(user_id: str) -> dict:
    # Function implementation
    return await fetch_preferences(user_id)
```

### 2. Manual Cache Control

For more control over cache keys and invalidation:

```python
from shared.query_cache import (
    get_cached, 
    set_cached, 
    invalidate_cache,
    PROFILE_TTL
)

async def get_profile(user_id: str, use_cache: bool = True) -> dict | None:
    cache_key = f"profile:{user_id}"
    
    if use_cache:
        cached = await get_cached(cache_key)
        if cached is not None:
            return cached
    
    # Fetch from database
    profile = await fetch_profile_from_db(user_id)
    
    if profile and use_cache:
        await set_cached(cache_key, profile, PROFILE_TTL)
    
    return profile

async def update_profile(user_id: str, data: dict) -> None:
    await save_profile_to_db(user_id, data)
    # Invalidate cache after update
    await invalidate_cache(f"profile:{user_id}")
```

### 3. Batch Operations with Caching

For batch operations, check cache for each item before fetching:

```python
async def get_jobs_by_ids(job_ids: list[str], use_cache: bool = True) -> list[dict]:
    results = []
    uncached_ids = []
    cached_results = {}
    
    # Check cache for each job
    if use_cache:
        for job_id in job_ids:
            cached = await get_cached(f"job:{job_id}")
            if cached is not None:
                cached_results[job_id] = cached
            else:
                uncached_ids.append(job_id)
    else:
        uncached_ids = list(job_ids)
    
    # Fetch uncached jobs from database
    if uncached_ids:
        db_results = await fetch_jobs_from_db(uncached_ids)
        for job in db_results:
            job_id = job["id"]
            cached_results[job_id] = job
            if use_cache:
                await set_cached(f"job:{job_id}", job, JOB_LISTINGS_TTL)
    
    # Return in original order
    return [cached_results[job_id] for job_id in job_ids if job_id in cached_results]
```

### 4. Pattern-Based Invalidation

Invalidate multiple related caches at once:

```python
from shared.query_cache import invalidate_pattern

async def clear_user_caches(user_id: str) -> int:
    """Clear all caches related to a user."""
    return await invalidate_pattern(f"*:{user_id}*")
```

## Cache Invalidation Strategy

### When to Invalidate

Always invalidate cache after:
1. **Create operations** - When new data is inserted
2. **Update operations** - When existing data is modified
3. **Delete operations** - When data is removed

### Invalidation Patterns

```python
# Single key invalidation
await invalidate_cache(f"profile:{user_id}")

# Multiple related keys
await invalidate_cache(f"profile_data:{user_id}")
await invalidate_cache(f"deep_profile:{user_id}")

# Pattern-based invalidation (use sparingly)
await invalidate_pattern(f"tenant:{tenant_id}:*")
```

## Implementation Examples

### Profile Assembly (`packages/backend/domain/profile_assembly.py`)

The profile assembly module caches the assembled `DeepProfile` object:

```python
async def assemble_profile(
    conn: asyncpg.Connection,
    user_id: str,
    *,
    use_cache: bool = True,
) -> DeepProfile | None:
    cache_key = f"deep_profile:{user_id}"
    
    if use_cache:
        cached_row = await get_cached(cache_key)
        if cached_row is not None:
            return _process_profile_row(cached_row, user_id)
    
    # Fetch from database
    profile_row = await _fetch_profile_raw(conn, user_id)
    if not profile_row:
        return None
    
    # Cache and return
    if use_cache:
        await set_cached(cache_key, profile_row, PROFILE_TTL)
    
    return _process_profile_row(profile_row, user_id)

async def invalidate_profile_cache(user_id: str) -> bool:
    """Call after any profile update."""
    return await invalidate_cache(f"deep_profile:{user_id}")
```

### Repository Layer (`packages/backend/domain/repositories.py`)

Repository methods support caching with `use_cache` parameter:

```python
class JobRepo:
    @staticmethod
    async def get_by_id(
        conn: asyncpg.Connection, 
        job_id: str,
        *,
        use_cache: bool = True,
    ) -> dict | None:
        cache_key = f"job:{job_id}"
        
        if use_cache:
            cached = await get_cached(cache_key)
            if cached is not None:
                return cached
        
        # Fetch from database
        row = await conn.fetchrow(
            "SELECT * FROM public.jobs WHERE id = $1",
            job_id,
        )
        if not row:
            return None
        
        result = JobRepo._row_to_job_detail(row)
        
        if use_cache:
            await set_cached(cache_key, result, JOB_LISTINGS_TTL)
        
        return result

class ProfileRepo:
    @staticmethod
    async def upsert(
        conn: asyncpg.Connection,
        user_id: str,
        profile_data: dict,
        resume_url: str | None = None,
        tenant_id: str | None = None,
    ) -> dict:
        # ... perform upsert ...
        
        # Invalidate related caches
        await invalidate_cache(f"profile_data:{user_id}")
        await invalidate_cache(f"deep_profile:{user_id}")
        
        return dict(row)
```

## Best Practices

### DO

- ✅ Cache read-only or rarely-changing data
- ✅ Use appropriate TTLs based on data volatility
- ✅ Invalidate cache immediately after write operations
- ✅ Provide `use_cache=False` option for cache bypass
- ✅ Log cache hits/misses for debugging
- ✅ Handle cache failures gracefully (fallback to DB)

### DON'T

- ❌ Cache sensitive data without encryption
- ❌ Cache data that changes frequently (real-time data)
- ❌ Forget to invalidate cache after updates
- ❌ Use very long TTLs for data that can change
- ❌ Rely on cache for critical business logic

## Monitoring

Cache statistics can be monitored through the Redis cache module:

```python
from shared.redis_cache import RedisCache

cache = RedisCache(redis_url)
stats = await cache.get_stats()

print(f"Hit rate: {stats.hit_rate:.2%}")
print(f"Total entries: {stats.total_entries}")
print(f"Memory usage: {stats.memory_usage_percent:.1f}%")
```

## Troubleshooting

### Cache Not Working

1. Check Redis connection: `redis-cli ping`
2. Verify cache keys are being generated correctly
3. Check logs for cache errors

### Stale Data

1. Verify invalidation is called after updates
2. Check TTL is appropriate for data type
3. Consider using `use_cache=False` for critical reads

### Memory Issues

1. Reduce TTLs for large data
2. Use pattern-based invalidation to clear old entries
3. Monitor memory usage with `get_stats()`
