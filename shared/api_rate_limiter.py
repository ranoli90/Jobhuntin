"""Advanced API rate limiting system with Redis backend.

Provides:
- Token bucket algorithm
- Sliding window algorithm
- Distributed rate limiting
- Multiple rate limit strategies
- Per-endpoint and global limits
- Redis-based storage

Usage:
    from shared.api_rate_limiter import RateLimiter

    limiter = RateLimiter(redis_client)
    await limiter.check_rate_limit("api_calls", "user_123")
"""

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import redis.asyncio as redis

from shared.alerting import get_alert_manager
from shared.logging_config import get_logger

logger = get_logger("sorce.api_rate_limiter")


class RateLimitStrategy(Enum):
    """Rate limiting strategies."""

    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    LEAKY_BUCKET = "leaky_bucket"


class RateLimitScope(Enum):
    """Rate limiting scope levels."""

    GLOBAL = "global"
    PER_USER = "per_user"
    PER_IP = "per_ip"
    PER_ENDPOINT = "per_endpoint"
    PER_TENANT = "per_tenant"


@dataclass
class RateLimitRule:
    """Rate limiting rule configuration."""

    name: str
    scope: RateLimitScope
    strategy: RateLimitStrategy
    limit: int
    window_seconds: int
    burst: int = 0
    key_func: Optional[str] = None
    enabled: bool = True
    priority: int = 1


@dataclass
class RateLimitResult:
    """Rate limiting check result."""

    allowed: bool
    remaining: int
    reset_time: Optional[float] = None
    retry_after: Optional[float] = None
    rule_name: str
    scope: str
    limit: int
    window_seconds: int


@dataclass
class RateLimitMetrics:
    """Rate limiting performance metrics."""

    rule_name: str
    scope: str
    total_requests: int
    blocked_requests: int
    allowed_requests: int
    avg_response_time_ms: float
    max_response_time_ms: float
    current_usage: float
    peak_usage: float
    last_reset: Optional[float] = None
    created_at: float = field(default_factory=time.time)


class RateLimiter:
    """Advanced API rate limiting system."""

    def __init__(
        self,
        redis_client: Optional[redis.asyncio.Redis] = None,
        alert_manager: Optional[Any] = None,
        default_window_seconds: int = 60,
        default_burst: int = 10,
    ):
        self.redis_client = redis_client
        self.alert_manager = alert_manager or get_alert_manager()

        self.default_window_seconds = default_window_seconds
        self.default_burst = default_burst

        # Rate limiting rules
        self.rules: List[RateLimitRule] = []
        self.rule_index: Dict[str, int] = {}

        # Metrics tracking
        self.metrics: Dict[str, RateLimitMetrics] = defaultdict(RateLimitMetrics)

        # Redis key patterns
        self.key_patterns = {
            RateLimitScope.GLOBAL: "rate_limit:global:",
            RateLimitScope.PER_USER: "rate_limit:user:",
            RateLimitScope.PER_IP: "rate_limit:ip:",
            RateLimitScope.PER_ENDPOINT: "rate_limit:endpoint:",
            RateLimitScope.PER_TENANT: "rate_limit:tenant:",
        }

        # Token bucket parameters
        self.token_bucket_capacity = 1000
        self.token_bucket_refill_rate = 1.0  # tokens per second

        # Sliding window parameters
        self.sliding_window_size = 100
        self.sliding_window_granularity = 1  # seconds

        # Fixed window parameters
        self.fixed_window_size = 100
        self.fixed_window_granularity = 10  # seconds

        # Leaky bucket parameters
        self.leaky_bucket_capacity = 1000
        self.leaky_bucket_leak_rate = 1.0  # tokens per second

        self._lock = asyncio.Lock()

    def add_rule(
        self,
        name: str,
        scope: RateLimitScope = RateLimitScope.GLOBAL,
        strategy: RateLimitStrategy = RateLimitStrategy.TOKEN_BUCKET,
        limit: int = 100,
        window_seconds: Optional[int] = None,
        burst: Optional[int] = None,
        key_func: Optional[str] = None,
        enabled: bool = True,
        priority: int = 1,
    ) -> None:
        """Add a rate limiting rule."""
        rule = RateLimitRule(
            name=name,
            scope=scope,
            strategy=strategy,
            limit=limit,
            window_seconds=window_seconds or self.default_window_seconds,
            burst=burst or self.default_burst,
            key_func=key_func,
            enabled=enabled,
            priority=priority,
        )

        self.rules.append(rule)
        self.rule_index[name] = len(self.rules) - 1

        logger.info(
            f"Added rate limit rule: {name} - {scope.value} - {limit}/{window_seconds}s"
        )

    def remove_rule(self, name: str) -> bool:
        """Remove a rate limiting rule."""
        for i, rule in enumerate(self.rules):
            if rule.name == name:
                del self.rules[i]
                del self.rule_index[name]
                logger.info(f"Removed rate limit rule: {name}")
                return True
        return False

    async def check_rate_limit(
        self,
        key: str,
        identifier: Optional[str] = None,
        rule_name: Optional[str] = None,
        **kwargs,
    ) -> RateLimitResult:
        """Check if request is allowed under rate limits."""
        # Find applicable rule
        rule = self._find_applicable_rule(key, rule_name, **kwargs)

        if not rule or not rule.enabled:
            # No applicable rule or rule disabled
            return RateLimitResult(
                allowed=True,
                remaining=float("inf"),
                reset_time=None,
                retry_after=None,
                rule_name="none",
                scope="none",
                limit=0,
                window_seconds=0,
            )

        # Generate cache key
        cache_key = self._generate_cache_key(rule, key, identifier)

        try:
            if rule.strategy == RateLimitStrategy.TOKEN_BUCKET:
                return await self._check_token_bucket(cache_key, rule)
            elif rule.strategy == RateLimitStrategy.SLIDING_WINDOW:
                return await self._check_sliding_window(cache_key, rule)
            elif rule.strategy == RateLimitStrategy.FIXED_WINDOW:
                return await self._check_fixed_window(cache_key, rule)
            elif rule.strategy == RateLimitStrategy.LEAKY_BUCKET:
                return await self._check_leaky_bucket(cache_key, rule)
            else:
                # Default to token bucket
                return await self._check_token_bucket(cache_key, rule)

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")

            # Fail open on error
            return RateLimitResult(
                allowed=True,
                remaining=0,
                reset_time=None,
                retry_after=None,
                rule_name=rule.name,
                scope=rule.scope.value,
                limit=rule.limit,
                window_seconds=rule.window_seconds,
            )

    def _find_applicable_rule(
        self, key: str, rule_name: Optional[str], **kwargs
    ) -> Optional[RateLimitRule]:
        """Find the most applicable rule for a request."""
        if rule_name:
            # Specific rule requested
            if rule_name in self.rule_index:
                return self.rules[self.rule_index[rule_name]]
            return None

        # Find rule by priority (highest priority wins)
        applicable_rules = []

        for rule in self.rules:
            if not rule.enabled:
                continue

            # Check if rule applies based on scope and key function
            if self._rule_applies(rule, key, **kwargs):
                applicable_rules.append(rule)

        if not applicable_rules:
            return None

        # Sort by priority (higher number = higher priority)
        applicable_rules.sort(key=lambda r: r.priority, reverse=True)
        return applicable_rules[0]

    def _rule_applies(self, rule: RateLimitRule, key: str, **kwargs) -> bool:
        """Check if rule applies to the request."""
        # Check scope-specific filtering
        if rule.scope == RateLimitScope.PER_USER and "user_id" not in kwargs:
            return False
        elif rule.scope == RateLimitScope.PER_IP and "ip_address" not in kwargs:
            return False
        elif rule.scope == RateLimitScope.PER_ENDPOINT and "endpoint" not in kwargs:
            return False
        elif rule.scope == RateLimitScope.PER_TENANT and "tenant_id" not in kwargs:
            return False

        # Check key function
        if rule.key_func:
            try:
                # Evaluate key function
                # For simplicity, support basic string matching
                if rule.key_func.startswith("regex:"):
                    import re

                    pattern = rule.key_func[6:]  # Remove "regex:" prefix
                    return bool(re.search(pattern, key))
                elif rule.key_func.startswith("contains:"):
                    substring = rule.key_func[9:]  # Remove "contains:" prefix
                    return substring in key
                elif rule.key_func.startswith("equals:"):
                    exact_match = rule.key_func[7:]  # Remove "equals:" prefix
                    return key == exact_match
                else:
                    return key == rule.key_func
            except Exception as e:
                logger.warning(f"Key function evaluation failed: {e}")
                return False

        return True

    def _generate_cache_key(
        self, rule: RateLimitRule, key: str, identifier: Optional[str]
    ) -> str:
        """Generate cache key for rate limiting."""
        key_parts = [self.key_patterns[rule.scope]]

        # Add rule name
        key_parts.append(rule.name)

        # Add identifier if provided
        if identifier:
            key_parts.append(identifier)
        elif rule.scope in [RateLimitScope.PER_USER, RateLimitScope.PER_IP] and key:
            # Extract identifier from key (simplified)
            key_parts.append(key.split(":")[0])

        return ":".join(key_parts)

    async def _check_token_bucket(
        self, cache_key: str, rule: RateLimitRule
    ) -> RateLimitResult:
        """Check rate limit using token bucket algorithm."""
        if not self.redis_client:
            # No Redis - fail open
            logger.warning("Redis not available for rate limiting, allowing request")
            return RateLimitResult(
                allowed=True,
                remaining=rule.limit,
                reset_time=None,
                retry_after=None,
                rule_name=rule.name,
                scope=rule.scope.value,
                limit=rule.limit,
                window_seconds=rule.window_seconds,
            )

        try:
            # Get current token count
            current_tokens = await self.redis_client.get(cache_key)
            current_tokens = int(current_tokens or 0)

            # Calculate tokens to add (refill rate)
            time_since_last_refill = time.time() - (
                self.metrics[rule.name].last_reset_time or 0
            )
            tokens_to_add = int(time_since_last_refill * self.token_bucket_refill_rate)

            # Add tokens (up to capacity)
            new_tokens = min(current_tokens + tokens_to_add, self.token_bucket_capacity)

            # Update Redis
            await self.redis_client.set(cache_key, new_tokens, ex=rule.window_seconds)

            # Check if request is allowed
            if new_tokens > 0:
                # Consume one token
                remaining = new_tokens - 1
                await self.redis_client.decr(cache_key)

                # Update metrics
                await self._update_metrics(rule.name, allowed=True, remaining=remaining)

                return RateLimitResult(
                    allowed=True,
                    remaining=remaining,
                    reset_time=None,
                    retry_after=None,
                    rule_name=rule.name,
                    scope=rule.scope.value,
                    limit=rule.limit,
                    window_seconds=rule.window_seconds,
                )
            else:
                # No tokens available
                # Calculate reset time
                time_to_reset = rule.window_seconds

                # Update metrics
                await self._update_metrics(rule.name, allowed=False, remaining=0)

                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_time=time.time() + time_to_reset,
                    retry_after=time_to_reset,
                    rule_name=rule.name,
                    scope=rule.scope.value,
                    limit=rule.limit,
                    window_seconds=rule.window_seconds,
                )

        except Exception as e:
            logger.error(f"Token bucket error: {e}")
            # Fail open on error
            return RateLimitResult(
                allowed=True,
                remaining=rule.limit,
                reset_time=None,
                retry_after=None,
                rule_name=rule.name,
                scope=rule.scope.value,
                limit=rule.limit,
                window_seconds=rule.window_seconds,
            )

    async def _check_sliding_window(
        self, cache_key: str, rule: RateLimitRule
    ) -> RateLimitResult:
        """Check rate limit using sliding window algorithm."""
        if not self.redis_client:
            # No Redis - fail open
            return RateLimitResult(
                allowed=True,
                remaining=rule.limit,
                reset_time=None,
                retry_after=None,
                rule_name=rule.name,
                scope=rule.scope.value,
                limit=rule.limit,
                window_seconds=rule.window_seconds,
            )

        try:
            current_time = time.time()
            window_start = current_time - rule.window_seconds

            # Remove old entries
            await self.redis_client.zremrangebyscore(
                cache_key, 0, current_time, window_start
            )

            # Get current count
            current_count = await self.redis_count_sliding_window(
                cache_key, rule.window_seconds
            )

            # Check if request is allowed
            if current_count < rule.limit:
                # Add current request to window
                await self.redis_client.zadd(cache_key, current_time, current_time)

                # Update metrics
                await self._update_metrics(
                    rule.name, allowed=True, remaining=rule.limit - current_count
                )

                return RateLimitResult(
                    allowed=True,
                    remaining=rule.limit - current_count,
                    reset_time=None,
                    retry_after=None,
                    rule_name=rule.name,
                    scope=rule.scope.value,
                    limit=rule.limit,
                    window_seconds=rule.window_seconds,
                )
            else:
                # Rate limit exceeded
                # Calculate when oldest entry expires
                oldest_entries = await self.redis_client.zrange(
                    cache_key, 0, 1, withscores=True
                )
                oldest_entry_time = (
                    float(oldest_entries[0][1]) if oldest_entries else current_time
                )
                retry_after = max(
                    0, oldest_entry_time + rule.window_seconds - current_time
                )

                # Update metrics
                await self._update_metrics(rule.name, allowed=False, remaining=0)

                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_time=None,
                    retry_after=retry_after,
                    rule_name=rule.name,
                    scope=rule.scope.value,
                    limit=rule.limit,
                    window_seconds=rule.window_seconds,
                )

        except Exception as e:
            logger.error(f"Sliding window error: {e}")
            return RateLimitResult(
                allowed=True,
                remaining=rule.limit,
                reset_time=None,
                retry_after=None,
                rule_name=rule.name,
                scope=rule.scope.value,
                limit=rule.limit,
                window_seconds=rule.window_seconds,
            )

    async def _check_fixed_window(
        self, cache_key: str, rule: RateLimitRule
    ) -> RateLimitResult:
        """Check rate limit using fixed window algorithm."""
        if not self.redis_client:
            return RateLimitResult(
                allowed=True,
                remaining=rule.limit,
                reset_time=None,
                retry_after=None,
                rule_name=rule.name,
                scope=rule.scope.value,
                limit=rule.limit,
                window_seconds=rule.window_seconds,
            )

        try:
            current_time = int(time.time())
            window_start = current_time - rule.window_seconds

            # Remove all entries in the window
            await self.redis_client.delete(cache_key)

            # Add current request
            await self.redis_client.setex(cache_key, "1", rule.window_seconds)

            # Check if request is allowed
            current_count = 1
            if current_count <= rule.limit:
                # Update metrics
                await self._update_metrics(
                    rule.name, allowed=True, remaining=rule.limit - current_count
                )

                return RateLimitResult(
                    allowed=True,
                    remaining=rule.limit - current_count,
                    reset_time=window_start + rule.window_seconds,
                    retry_after=None,
                    rule_name=rule.name,
                    scope=rule.scope.value,
                    limit=rule.limit,
                    window_seconds=rule.window_seconds,
                )
            else:
                # Rate limit exceeded
                # Update metrics
                await self._update_metrics(rule.name, allowed=False, remaining=0)

                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_time=window_start + rule.window_seconds,
                    retry_after=None,
                    rule_name=rule.name,
                    scope=rule.scope.value,
                    limit=rule.limit,
                    window_seconds=rule.window_seconds,
                )

        except Exception as e:
            logger.error(f"Fixed window error: {e}")
            return RateLimitResult(
                allowed=True,
                remaining=rule.limit,
                reset_time=None,
                retry_after=None,
                rule_name=rule.name,
                scope=rule.name,
                limit=rule.limit,
                window_seconds=rule.window_seconds,
            )

    async def _check_leaky_bucket(
        self, cache_key: str, rule: RateLimitRule
    ) -> RateLimitResult:
        """Check rate limit using leaky bucket algorithm."""
        if not self.redis_client:
            return RateLimitResult(
                allowed=True,
                remaining=rule.limit,
                reset_time=None,
                retry_after=None,
                rule_name=rule.name,
                scope=rule.scope.value,
                limit=rule.limit,
                window_seconds=rule.window_seconds,
            )

        try:
            # Get current token count
            current_tokens = await self.redis_client.get(cache_key)
            current_tokens = int(current_tokens or 0)

            # Calculate leak (tokens lost since last update)
            time_since_update = time.time() - (
                self.metrics[rule.name].last_reset_time or 0
            )
            leaked_tokens = int(time_since_update * self.leaky_bucket_leak_rate)

            # Remove leaked tokens
            new_tokens = max(0, current_tokens - leaked_tokens)

            # Refill tokens (up to capacity)
            time_since_update = time.time() - (
                self.metrics[rule.name].last_reset_time or 0
            )
            int(time_since_update * self.leaky_bucket_refill_rate)
            new_tokens = min(new_tokens + leaked_tokens, self.leaky_bucket_capacity)

            # Update Redis
            await self.redis_client.set(cache_key, new_tokens)

            # Check if request is allowed
            if new_tokens > 0:
                # Consume one token
                remaining = new_tokens - 1
                await self.redis_client.decr(cache_key)

                # Update metrics
                await self._update_metrics(rule.name, allowed=True, remaining=remaining)

                return RateLimitResult(
                    allowed=True,
                    remaining=remaining,
                    reset_time=None,
                    retry_after=None,
                    rule_name=rule.name,
                    scope=rule.scope.value,
                    limit=rule.limit,
                    window_seconds=rule.window_seconds,
                )
            else:
                # No tokens available
                # Calculate when bucket will be refilled
                time_to_refill = (
                    self.leaky_bucket_capacity / self.leaky_bucket_refill_rate
                )

                # Update metrics
                await self._update_metrics(rule.name, allowed=False, remaining=0)

                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_time=None,
                    retry_after=time_to_refill,
                    rule_name=rule.name,
                    scope=rule.scope.value,
                    limit=rule.limit,
                    window_seconds=rule.window_seconds,
                )

        except Exception as e:
            logger.error(f"Leaky bucket error: {e}")
            return RateLimitResult(
                allowed=True,
                remaining=rule.limit,
                reset_time=None,
                retry_after=None,
                rule_name=rule.name,
                scope=rule.name,
                limit=rule.limit,
                window_seconds=rule.window_seconds,
            )

    async def redis_count_sliding_window(
        self, cache_key: str, window_seconds: int
    ) -> int:
        """Count entries in sliding window."""
        try:
            return await self.redis_client.zcount(
                cache_key, "-inf", "+inf", "ZCOUNT", cache_key
            )
        except Exception as e:
            logger.error(f"Failed to count sliding window: {e}")
            return 0

    async def _update_metrics(
        self, rule_name: str, allowed: bool, remaining: int
    ) -> None:
        """Update metrics for a rule."""
        metrics = self.metrics[rule_name]

        if allowed:
            metrics.allowed_requests += 1
        else:
            metrics.blocked_requests += 1

        metrics.remaining = remaining
        metrics.total_requests += 1

        # Update averages
        if metrics.total_requests > 0:
            metrics.allowed_requests_pct = (
                metrics.allowed_requests / metrics.total_requests
            ) * 100
            metrics.blocked_requests_pct = (
                metrics.blocked_requests / metrics.total_requests
            ) * 100

        # Update timestamps
        current_time = time.time()
        metrics.last_reset = current_time
        metrics.updated_at = current_time

    def get_metrics_summary(self, rule_name: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics summary."""
        if rule_name:
            if rule_name in self.metrics:
                metrics = self.metrics[rule_name]
                return {
                    "rule_name": rule_name,
                    "total_requests": metrics.total_requests,
                    "allowed_requests": metrics.allowed_requests,
                    "blocked_requests": metrics.blocked_requests,
                    "allowed_requests_pct": metrics.allowed_requests_pct,
                    "blocked_requests_pct": metrics.blocked_requests_pct,
                    "avg_response_time_ms": metrics.avg_response_time_ms,
                    "max_response_time_ms": metrics.max_response_time_ms,
                    "current_usage": metrics.current_usage,
                    "peak_usage": metrics.peak_usage,
                    "last_reset": metrics.last_reset,
                    "created_at": metrics.created_at,
                    "updated_at": metrics.updated_at,
                }

        # Return all metrics
        return {
            "total_rules": len(self.rules),
            "active_rules": len([r for r in self.rules if r.enabled]),
            "total_requests": sum(m.total_requests for m in self.metrics.values()),
            "total_allowed": sum(m.allowed_requests for m in self.metrics.values()),
            "total_blocked": sum(m.blocked_requests for m in self.metrics.values()),
            "global_avg_allowed_rate": 0.0,
            "global_avg_blocked_rate": 0.0,
        }

    def get_rule_metrics(self, rule_name: str) -> Optional[RateLimitMetrics]:
        """Get metrics for a specific rule."""
        return self.metrics.get(rule_name)

    def get_all_metrics(self) -> Dict[str, RateLimitMetrics]:
        """Get all metrics."""
        return dict(self.metrics)

    def get_active_rules(self) -> List[RateLimitRule]:
        """Get all active rate limiting rules."""
        return [rule for rule in self.rules if rule.enabled]

    def update_config(self, **kwargs) -> None:
        """Update rate limiter configuration."""
        if "default_window_seconds" in kwargs:
            self.default_window_seconds = kwargs["default_window_seconds"]
        if "default_burst" in kwargs:
            self.default_burst = kwargs["default_burst"]

        # Update Redis parameters
        if "token_bucket_capacity" in kwargs:
            self.token_bucket_capacity = kwargs["token_bucket_capacity"]
        if "token_bucket_refill_rate" in kwargs:
            self.token_bucket_refill_rate = kwargs["token_bucket_refill_rate"]
        if "sliding_window_size" in kwargs:
            self.sliding_window_size = kwargs["sliding_window_size"]
        if "sliding_window_granularity" in kwargs:
            self.sliding_window_granularity = kwargs["sliding_window_granularity"]
        if "leaky_bucket_capacity" in kwargs:
            self.leaky_bucket_capacity = kwargs["leaky_bucket_capacity"]
        if "leaky_bucket_leak_rate" in kwargs:
            self.leaky_bucket_leak_rate = kwargs["leaky_bucket_leak_rate"]

        logger.info("Updated rate limiter configuration")

    async def clear_metrics(self, rule_name: Optional[str] = None) -> int:
        """Clear metrics for a specific rule or all rules."""
        cleared_count = 0

        if rule_name:
            if rule_name in self.metrics:
                del self.metrics[rule_name]
                cleared_count = 1
        else:
            self.metrics.clear()
            cleared_count = len(self.metrics)

        return cleared_count

    async def cleanup_expired_keys(self) -> int:
        """Clean up expired Redis keys."""
        if not self.redis_client:
            return 0

        try:
            # Clean up old sliding window entries
            for rule in self.rules:
                if rule.strategy == RateLimitStrategy.SLIDING_WINDOW:
                    cache_key = f"rate_limit:{rule.scope.value}:{rule.name}"
                    await self.redis_client.zremrangebyscore(
                        cache_key, 0, time.time(), time.time() - rule.window_seconds * 2
                    )
                elif rule.strategy == RateLimitStrategy.FIXED_WINDOW:
                    cache_key = f"rate_limit:{rule.scope.value}:{rule.name}"
                    # Fixed window keys automatically expire

        except Exception as e:
            logger.error(f"Failed to cleanup expired keys: {e}")

        return 0


# Global rate limiter instance
_rate_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        raise RuntimeError(
            "Rate limiter not initialized. Call init_rate_limiter() first."
        )
    return _rate_limiter


async def init_rate_limiter(
    redis_client: Optional[redis.asyncio.Redis] = None,
    alert_manager: Optional[Any] = None,
    default_window_seconds: int = 60,
    default_burst: int = 10,
) -> RateLimiter:
    """Initialize global rate limiter."""
    global _rate_limiter
    _rate_limiter = RateLimiter(
        redis_client, alert_manager, default_window_seconds, default_burst
    )
    return _rate_limiter
