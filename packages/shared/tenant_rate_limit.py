"""
Tenant-aware Rate Limiting with Redis

Implements tier-based rate limiting:
- Free: 10 requests/min
- Pro: 60 requests/min
- Team: 100 requests/min
- Enterprise: 500 requests/min

Uses Redis for distributed rate limiting with in-memory fallback.
Integrates with existing RateLimiter class.
"""

from __future__ import annotations

import asyncio
import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from shared.config import get_settings
from shared.logging_config import get_logger

logger = get_logger("sorce.tenant_rate_limit")


class TenantTier(StrEnum):
    FREE = "FREE"
    PRO = "PRO"
    TEAM = "TEAM"
    ENTERPRISE = "ENTERPRISE"


@dataclass(frozen=True)
class TierLimits:
    requests_per_minute: int
    requests_per_hour: int
    concurrent_requests: int


TIER_LIMITS: dict[TenantTier, TierLimits] = {
    TenantTier.FREE: TierLimits(
        requests_per_minute=10,
        requests_per_hour=100,
        concurrent_requests=2,
    ),
    TenantTier.PRO: TierLimits(
        requests_per_minute=60,
        requests_per_hour=1000,
        concurrent_requests=10,
    ),
    TenantTier.TEAM: TierLimits(
        requests_per_minute=100,
        requests_per_hour=5000,
        concurrent_requests=25,
    ),
    TenantTier.ENTERPRISE: TierLimits(
        requests_per_minute=500,
        requests_per_hour=25000,
        concurrent_requests=100,
    ),
}


def get_tier_limits(tier: str | TenantTier) -> TierLimits:
    tier_enum = TenantTier(tier.upper()) if isinstance(tier, str) else tier
    return TIER_LIMITS.get(tier_enum, TIER_LIMITS[TenantTier.FREE])


class TenantRateLimiter:
    """
    Tenant-aware rate limiter with Redis backend support.

    Uses a sliding window algorithm with Redis for distributed systems.
    Falls back to in-memory when Redis is unavailable.
    """

    _LUA_SLIDING_WINDOW = """
    local key = KEYS[1]
    local now = tonumber(ARGV[1])
    local window_seconds = tonumber(ARGV[2])
    local max_requests = tonumber(ARGV[3])
    local cutoff = now - window_seconds
    
    redis.call('ZREMRANGEBYSCORE', key, 0, cutoff)
    local count = redis.call('ZCARD', key)
    
    if count >= max_requests then
        return {0, count}
    end
    
    local member = tostring(now) .. ':' .. tostring(math.random(1000000))
    redis.call('ZADD', key, now, member)
    redis.call('EXPIRE', key, window_seconds + 10)
    return {1, count + 1}
    """

    def __init__(self) -> None:
        self._redis_client: Any = None
        self._lock = threading.Lock()
        self._memory_windows: dict[str, list[float]] = defaultdict(list)
        self._concurrent_counts: dict[str, int] = defaultdict(int)
        self._concurrent_locks: dict[str, asyncio.Lock] = {}

    async def _get_redis(self) -> Any:
        if self._redis_client is None:
            try:
                from shared.redis_client import get_redis

                self._redis_client = await get_redis()
            except Exception as e:
                logger.warning(f"Redis unavailable, using in-memory rate limiting: {e}")
        return self._redis_client

    async def acquire(
        self,
        tenant_id: str,
        tier: str | TenantTier,
        endpoint: str = "default",
    ) -> tuple[bool, dict[str, Any]]:
        """
        Attempt to acquire a rate limit slot for the tenant.

        Returns:
            (allowed: bool, metadata: dict) - whether allowed and metadata about limits
        """
        limits = get_tier_limits(tier)
        key = f"rate_limit:tenant:{tenant_id}:{endpoint}"

        redis = await self._get_redis()

        if redis:
            return await self._acquire_redis(redis, key, limits)
        else:
            return self._acquire_memory(key, limits)

    async def _acquire_redis(
        self,
        redis: Any,
        key: str,
        limits: TierLimits,
    ) -> tuple[bool, dict[str, Any]]:
        try:
            now = time.time()
            result = await redis.eval(
                self._LUA_SLIDING_WINDOW,
                1,
                key,
                str(now),
                str(60),
                str(limits.requests_per_minute),
            )
            allowed = int(result[0]) == 1
            current_count = int(result[1])

            return allowed, {
                "limit": limits.requests_per_minute,
                "remaining": max(0, limits.requests_per_minute - current_count),
                "reset_in": 60,
                "backend": "redis",
            }
        except Exception as e:
            logger.warning(f"Redis rate limit failed, falling back to memory: {e}")
            return self._acquire_memory(key, limits)

    def _acquire_memory(
        self,
        key: str,
        limits: TierLimits,
    ) -> tuple[bool, dict[str, Any]]:
        now = time.monotonic()
        window_seconds = 60

        with self._lock:
            timestamps = self._memory_windows[key]
            cutoff = now - window_seconds
            timestamps[:] = [t for t in timestamps if t > cutoff]

            if len(timestamps) >= limits.requests_per_minute:
                oldest = timestamps[0] if timestamps else now
                reset_in = int((oldest + window_seconds) - now)
                return False, {
                    "limit": limits.requests_per_minute,
                    "remaining": 0,
                    "reset_in": max(1, reset_in),
                    "backend": "memory",
                }

            timestamps.append(now)
            return True, {
                "limit": limits.requests_per_minute,
                "remaining": limits.requests_per_minute - len(timestamps),
                "reset_in": window_seconds,
                "backend": "memory",
            }

    async def acquire_concurrent(
        self,
        tenant_id: str,
        tier: str | TenantTier,
        operation: str = "default",
    ) -> tuple[bool, dict[str, Any]]:
        """
        Acquire a concurrent request slot for the tenant.

        Used for long-running operations like AI requests.
        Must be paired with release_concurrent().
        """
        limits = get_tier_limits(tier)
        key = f"{tenant_id}:{operation}"

        if key not in self._concurrent_locks:
            self._concurrent_locks[key] = asyncio.Lock()

        async with self._concurrent_locks[key]:
            current = self._concurrent_counts.get(key, 0)

            if current >= limits.concurrent_requests:
                return False, {
                    "limit": limits.concurrent_requests,
                    "current": current,
                    "operation": operation,
                }

            self._concurrent_counts[key] = current + 1
            return True, {
                "limit": limits.concurrent_requests,
                "current": current + 1,
                "operation": operation,
            }

    async def release_concurrent(
        self,
        tenant_id: str,
        operation: str = "default",
    ) -> None:
        """Release a concurrent request slot."""
        key = f"{tenant_id}:{operation}"

        if key in self._concurrent_locks:
            async with self._concurrent_locks[key]:
                current = self._concurrent_counts.get(key, 0)
                if current > 0:
                    self._concurrent_counts[key] = current - 1

    def get_tier_from_request(
        self,
        tenant_context: Any = None,
        plan: str | None = None,
    ) -> TenantTier:
        """
        Determine tenant tier from request context or explicit plan.

        Priority:
        1. Explicit plan parameter
        2. tenant_context.tenant_plan
        3. Default to FREE
        """
        if plan:
            try:
                return TenantTier(plan.upper())
            except ValueError:
                pass

        if tenant_context and hasattr(tenant_context, "tenant_plan"):
            try:
                return TenantTier(tenant_context.tenant_plan.upper())
            except (ValueError, AttributeError):
                pass

        return TenantTier.FREE


_tenant_rate_limiter: TenantRateLimiter | None = None
_rate_limiter_lock = threading.Lock()


def get_tenant_rate_limiter() -> TenantRateLimiter:
    """Get or create the singleton TenantRateLimiter instance."""
    global _tenant_rate_limiter

    with _rate_limiter_lock:
        if _tenant_rate_limiter is None:
            _tenant_rate_limiter = TenantRateLimiter()
        return _tenant_rate_limiter


async def check_tenant_rate_limit(
    tenant_id: str,
    tier: str | TenantTier,
    endpoint: str = "default",
) -> tuple[bool, dict[str, Any]]:
    """
    Convenience function to check tenant rate limit.

    Usage:
        allowed, metadata = await check_tenant_rate_limit(
            tenant_id=ctx.tenant_id,
            tier=ctx.tenant_plan,
            endpoint="ai_suggestions",
        )
        if not allowed:
            raise HTTPException(429, detail="Rate limit exceeded")
    """
    limiter = get_tenant_rate_limiter()
    return await limiter.acquire(tenant_id, tier, endpoint)


class AIEndpointRateLimiter:
    """
    Specialized rate limiter for AI endpoints with stricter limits.

    AI endpoints have additional constraints:
    - Lower per-minute limits due to LLM costs
    - Concurrent request limits for long-running calls
    - Separate tracking per AI operation type
    """

    AI_TIER_LIMITS: dict[TenantTier, TierLimits] = {
        TenantTier.FREE: TierLimits(
            requests_per_minute=5,
            requests_per_hour=20,
            concurrent_requests=1,
        ),
        TenantTier.PRO: TierLimits(
            requests_per_minute=20,
            requests_per_hour=200,
            concurrent_requests=3,
        ),
        TenantTier.TEAM: TierLimits(
            requests_per_minute=50,
            requests_per_hour=500,
            concurrent_requests=10,
        ),
        TenantTier.ENTERPRISE: TierLimits(
            requests_per_minute=200,
            requests_per_hour=2000,
            concurrent_requests=50,
        ),
    }

    def __init__(self) -> None:
        self._base_limiter = TenantRateLimiter()
        self._ai_windows: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    async def acquire(
        self,
        tenant_id: str,
        tier: str | TenantTier,
        operation: str = "ai_default",
    ) -> tuple[bool, dict[str, Any]]:
        """Check AI-specific rate limits."""
        tier_enum = TenantTier(tier.upper()) if isinstance(tier, str) else tier
        limits = self.AI_TIER_LIMITS.get(
            tier_enum, self.AI_TIER_LIMITS[TenantTier.FREE]
        )

        key = f"ai:{tenant_id}:{operation}"

        (
            concurrent_allowed,
            concurrent_meta,
        ) = await self._base_limiter.acquire_concurrent(
            tenant_id, tier, f"ai_{operation}"
        )

        if not concurrent_allowed:
            return False, {
                **concurrent_meta,
                "reason": "concurrent_limit",
                "message": f"Too many concurrent AI requests. Limit: {limits.concurrent_requests}",
            }

        allowed, metadata = await self._check_ai_rate_limit(key, limits)

        if not allowed:
            await self._base_limiter.release_concurrent(tenant_id, f"ai_{operation}")

        metadata["operation"] = operation
        metadata["concurrent_acquired"] = True
        return allowed, metadata

    async def release(self, tenant_id: str, operation: str = "ai_default") -> None:
        """Release concurrent slot after AI operation completes."""
        await self._base_limiter.release_concurrent(tenant_id, f"ai_{operation}")

    async def _check_ai_rate_limit(
        self,
        key: str,
        limits: TierLimits,
    ) -> tuple[bool, dict[str, Any]]:
        now = time.monotonic()
        window_seconds = 60

        with self._lock:
            timestamps = self._ai_windows[key]
            cutoff = now - window_seconds
            timestamps[:] = [t for t in timestamps if t > cutoff]

            if len(timestamps) >= limits.requests_per_minute:
                oldest = timestamps[0] if timestamps else now
                reset_in = int((oldest + window_seconds) - now)
                return False, {
                    "limit": limits.requests_per_minute,
                    "remaining": 0,
                    "reset_in": max(1, reset_in),
                    "reason": "rate_limit",
                }

            timestamps.append(now)
            return True, {
                "limit": limits.requests_per_minute,
                "remaining": limits.requests_per_minute - len(timestamps),
                "reset_in": window_seconds,
            }


_ai_rate_limiter: AIEndpointRateLimiter | None = None


def get_ai_rate_limiter() -> AIEndpointRateLimiter:
    """Get or create the singleton AIEndpointRateLimiter instance."""
    global _ai_rate_limiter

    with _rate_limiter_lock:
        if _ai_rate_limiter is None:
            _ai_rate_limiter = AIEndpointRateLimiter()
        return _ai_rate_limiter
