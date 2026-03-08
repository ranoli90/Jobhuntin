"""Advanced rate limiting system for API abuse prevention.

Provides:
- Token bucket algorithm for smooth rate limiting
- Sliding window counters
- IP-based and user-based limiting
- Distributed rate limiting with Redis
- Adaptive rate limiting based on user behavior

Usage:
    from shared.rate_limiter import RateLimiter

    limiter = RateLimiter(redis_client)
    allowed = await limiter.check_rate_limit("api_calls", "user:123", 100, 60)
"""

from __future__ import annotations

import time
import asyncio
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Dict, Optional
import hashlib

from shared.logging_config import get_logger

logger = get_logger("sorce.rate_limit")


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    requests_per_window: int
    window_seconds: int
    burst_size: Optional[int] = None
    penalty_seconds: Optional[int] = None
    adaptive_enabled: bool = False


@dataclass
class RateLimitResult:
    """Result of rate limit check."""

    allowed: bool
    remaining: int
    reset_time: float
    retry_after: Optional[float] = None
    penalty_applied: bool = False
    limit_exceeded: bool = False


class TokenBucket:
    """Token bucket algorithm implementation."""

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = capacity
        self.last_refill = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """Consume tokens if available."""
        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.refill_rate

        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now

    def get_available_tokens(self) -> int:
        """Get current available tokens."""
        self._refill()
        return int(self.tokens)

    def time_until_available(self, tokens: int = 1) -> float:
        """Get time until tokens are available."""
        self._refill()

        if self.tokens >= tokens:
            return 0.0

        needed = tokens - self.tokens
        return needed / self.refill_rate


class SlidingWindowCounter:
    """Sliding window rate limiter."""

    def __init__(self, window_seconds: int, max_requests: int):
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        self.requests: deque[float] = deque()

    def is_allowed(self) -> bool:
        """Check if request is allowed."""
        now = time.time()

        # Remove old requests outside window
        while self.requests and self.requests[0] <= now - self.window_seconds:
            self.requests.popleft()

        # Check if under limit
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True

        return False

    def get_count(self) -> int:
        """Get current request count."""
        now = time.time()

        # Remove old requests outside window
        while self.requests and self.requests[0] <= now - self.window_seconds:
            self.requests.popleft()

        return len(self.requests)

    def reset_time(self) -> float:
        """Get time when window resets."""
        if not self.requests:
            return time.time()

        return self.requests[0] + self.window_seconds


class MemoryRateLimiter:
    """In-memory rate limiter for development/testing."""

    def __init__(self):
        self.token_buckets: Dict[str, TokenBucket] = {}
        self.sliding_windows: Dict[str, SlidingWindowCounter] = {}
        self.penalties: Dict[str, float] = {}
        self.adaptive_scores: Dict[str, float] = defaultdict(float)
        self._lock = asyncio.Lock()

    async def check_rate_limit(
        self, key: str, config: RateLimitConfig, algorithm: str = "token_bucket"
    ) -> RateLimitResult:
        """Check if request is allowed."""
        async with self._lock:
            # Check for penalty
            penalty_end = self.penalties.get(key, 0)
            if time.time() < penalty_end:
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_time=penalty_end,
                    retry_after=penalty_end - time.time(),
                    penalty_applied=True,
                    limit_exceeded=True,
                )

            # Apply adaptive rate limiting if enabled
            if config.adaptive_enabled:
                score = self.adaptive_scores.get(key, 1.0)
                if score < 0.5:  # Reduce rate for low-score users
                    adjusted_requests = int(config.requests_per_window * score)
                    config = RateLimitConfig(
                        requests_per_window=adjusted_requests,
                        window_seconds=config.window_seconds,
                        burst_size=config.burst_size,
                        penalty_seconds=config.penalty_seconds,
                        adaptive_enabled=True,
                    )

            if algorithm == "token_bucket":
                return self._check_token_bucket(key, config)
            else:
                return self._check_sliding_window(key, config)

    def _check_token_bucket(self, key: str, config: RateLimitConfig) -> RateLimitResult:
        """Check token bucket rate limit."""
        burst_size = config.burst_size or config.requests_per_window
        refill_rate = config.requests_per_window / config.window_seconds

        if key not in self.token_buckets:
            self.token_buckets[key] = TokenBucket(burst_size, refill_rate)

        bucket = self.token_buckets[key]
        allowed = bucket.consume()

        if allowed:
            return RateLimitResult(
                allowed=True,
                remaining=bucket.get_available_tokens(),
                reset_time=time.time() + config.window_seconds,
            )
        else:
            retry_after = bucket.time_until_available()

            # Apply penalty if configured
            if config.penalty_seconds and retry_after > config.window_seconds * 0.8:
                self.penalties[key] = time.time() + config.penalty_seconds

            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_time=time.time() + retry_after,
                retry_after=retry_after,
                limit_exceeded=True,
            )

    def _check_sliding_window(
        self, key: str, config: RateLimitConfig
    ) -> RateLimitResult:
        """Check sliding window rate limit."""
        if key not in self.sliding_windows:
            self.sliding_windows[key] = SlidingWindowCounter(
                config.window_seconds, config.requests_per_window
            )

        window = self.sliding_windows[key]
        allowed = window.is_allowed()

        if allowed:
            return RateLimitResult(
                allowed=True,
                remaining=config.requests_per_window - window.get_count(),
                reset_time=window.reset_time(),
            )
        else:
            retry_after = window.reset_time() - time.time()

            # Apply penalty if configured
            if config.penalty_seconds:
                self.penalties[key] = time.time() + config.penalty_seconds

            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_time=window.reset_time(),
                retry_after=retry_after,
                limit_exceeded=True,
            )

    def update_adaptive_score(self, key: str, score: float) -> None:
        """Update adaptive score for rate limiting."""
        self.adaptive_scores[key] = max(
            0.1, min(2.0, score)
        )  # Clamp between 0.1 and 2.0

    def clear_key(self, key: str) -> None:
        """Clear rate limiting for a specific key."""
        self.token_buckets.pop(key, None)
        self.sliding_windows.pop(key, None)
        self.penalties.pop(key, None)
        self.adaptive_scores.pop(key, None)

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics."""
        return {
            "active_token_buckets": len(self.token_buckets),
            "active_sliding_windows": len(self.sliding_windows),
            "active_penalties": len(self.penalties),
            "adaptive_scores": dict(self.adaptive_scores),
        }


class RedisRateLimiter:
    """Distributed rate limiter using Redis."""

    def __init__(self, redis_client: Any):
        self.redis = redis_client

    async def check_rate_limit(
        self, key: str, config: RateLimitConfig
    ) -> RateLimitResult:
        """Check rate limit using Redis."""
        now = time.time()
        window_start = now - config.window_seconds

        # Use Redis sorted set for sliding window
        redis_key = f"rate_limit:{key}"

        try:
            # Remove old entries
            await self.redis.zremrangebyscore(redis_key, 0, window_start)

            # Get current count
            current_count = await self.redis.zcard(redis_key)

            if current_count < config.requests_per_window:
                # Add current request
                await self.redis.zadd(redis_key, {str(now): now})
                await self.redis.expire(redis_key, config.window_seconds)

                return RateLimitResult(
                    allowed=True,
                    remaining=config.requests_per_window - current_count - 1,
                    reset_time=now + config.window_seconds,
                )
            else:
                # Get oldest request time for retry_after
                oldest = await self.redis.zrange(redis_key, 0, 0, withscores=True)
                retry_after = 0.0

                if oldest:
                    oldest_time = float(oldest[0][1])
                    retry_after = (oldest_time + config.window_seconds) - now

                # Apply penalty if configured
                if config.penalty_seconds:
                    penalty_key = f"rate_penalty:{key}"
                    await self.redis.setex(penalty_key, config.penalty_seconds, "1")

                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_time=now + config.window_seconds,
                    retry_after=max(0, retry_after),
                    limit_exceeded=True,
                )

        except Exception as e:
            logger.error(f"Redis rate limit error: {e}")
            # Fail open - allow request if Redis is down
            return RateLimitResult(
                allowed=True,
                remaining=config.requests_per_window,
                reset_time=now + config.window_seconds,
            )

    async def clear_key(self, key: str) -> None:
        """Clear rate limiting for a specific key."""
        try:
            redis_key = f"rate_limit:{key}"
            await self.redis.delete(redis_key)

            penalty_key = f"rate_penalty:{key}"
            await self.redis.delete(penalty_key)
        except Exception as e:
            logger.error(f"Redis clear key error: {e}")


class RateLimiter:
    """Main rate limiter with multiple algorithms and backends."""

    def __init__(
        self, redis_client: Any | None = None, use_memory_fallback: bool = True
    ):
        self.redis_limiter = RedisRateLimiter(redis_client) if redis_client else None
        self.memory_limiter = MemoryRateLimiter() if use_memory_fallback else None
        self.configs: Dict[str, RateLimitConfig] = {}

        # Default configurations
        self._setup_default_configs()

    def _setup_default_configs(self) -> None:
        """Setup default rate limit configurations."""
        self.configs.update(
            {
                "api_general": RateLimitConfig(100, 60),  # 100 requests per minute
                "api_auth": RateLimitConfig(10, 60),  # 10 auth requests per minute
                "api_upload": RateLimitConfig(5, 60),  # 5 uploads per minute
                "api_search": RateLimitConfig(30, 60),  # 30 searches per minute
                "webhook": RateLimitConfig(1000, 60),  # 1000 webhooks per minute
                "magic_link": RateLimitConfig(3, 300),  # 3 magic links per 5 minutes
                "password_reset": RateLimitConfig(
                    3, 900
                ),  # 3 password resets per 15 minutes
            }
        )

    def add_config(self, name: str, config: RateLimitConfig) -> None:
        """Add or update a rate limit configuration."""
        self.configs[name] = config

    async def check_rate_limit(
        self,
        config_name: str,
        key: str,
        custom_config: Optional[RateLimitConfig] = None,
    ) -> RateLimitResult:
        """Check rate limit for given config and key."""
        config = custom_config or self.configs.get(config_name)
        if not config:
            raise ValueError(f"Unknown rate limit config: {config_name}")

        # Try Redis first
        if self.redis_limiter:
            try:
                return await self.redis_limiter.check_rate_limit(key, config)
            except Exception as e:
                logger.warning(
                    f"Redis rate limiter failed, falling back to memory: {e}"
                )

        # Fallback to memory
        if self.memory_limiter:
            return await self.memory_limiter.check_rate_limit(key, config)

        # No limiter available - allow all
        return RateLimitResult(
            allowed=True,
            remaining=config.requests_per_window,
            reset_time=time.time() + config.window_seconds,
        )

    async def clear_rate_limit(self, key: str) -> None:
        """Clear rate limit for a specific key."""
        if self.redis_limiter:
            await self.redis_limiter.clear_key(key)

        if self.memory_limiter:
            self.memory_limiter.clear_key(key)

    def update_adaptive_score(self, key: str, score: float) -> None:
        """Update adaptive score for rate limiting."""
        if self.memory_limiter:
            self.memory_limiter.update_adaptive_score(key, score)

    def make_key(self, *parts: str) -> str:
        """Create a rate limit key from parts."""
        return ":".join(str(part) for part in parts)

    def hash_key(self, key: str, max_length: int = 250) -> str:
        """Create a hash of key for length limits."""
        if len(key) <= max_length:
            return key
        return hashlib.sha256(key.encode()).hexdigest()[:max_length]


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


async def init_rate_limiter(redis_client: Any | None = None) -> RateLimiter:
    """Initialize global rate limiter."""
    global _rate_limiter
    _rate_limiter = RateLimiter(redis_client)
    return _rate_limiter


class RateLimitDecorator:
    """Decorator for rate limiting API endpoints."""

    def __init__(
        self,
        config_name: str,
        key_func: callable = None,
        on_limit: callable = None,
    ):
        self.config_name = config_name
        self.key_func = key_func or self._default_key_func
        self.on_limit = on_limit

    def __call__(self, func):
        async def wrapper(*args, **kwargs):
            limiter = get_rate_limiter()

            # Generate key from request context
            key = await self.key_func(*args, **kwargs)

            # Check rate limit
            result = await limiter.check_rate_limit(self.config_name, key)

            if not result.allowed:
                if self.on_limit:
                    await self.on_limit(result)

                from fastapi import HTTPException

                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded",
                    headers={
                        "Retry-After": str(int(result.retry_after or 60)),
                        "X-RateLimit-Limit": str(
                            get_rate_limiter()
                            .configs.get(self.config_name, RateLimitConfig(100, 60))
                            .requests_per_window
                        ),
                        "X-RateLimit-Remaining": str(result.remaining),
                        "X-RateLimit-Reset": str(int(result.reset_time)),
                    },
                )

            # Add rate limit headers
            response = await func(*args, **kwargs)

            if hasattr(response, "headers"):
                response.headers.update(
                    {
                        "X-RateLimit-Limit": str(
                            get_rate_limiter()
                            .configs.get(self.config_name, RateLimitConfig(100, 60))
                            .requests_per_window
                        ),
                        "X-RateLimit-Remaining": str(result.remaining),
                        "X-RateLimit-Reset": str(int(result.reset_time)),
                    }
                )

            return response

        return wrapper

    @staticmethod
    async def _default_key_func(*args, **kwargs) -> str:
        """Default key function using IP address."""
        # Try to get IP from request
        for arg in args:
            if hasattr(arg, "client") and hasattr(arg.client, "host"):
                return f"ip:{arg.client.host}"

        # Fallback to generic key
        return "anonymous"


def rate_limit(
    config_name: str,
    key_func: callable = None,
    on_limit: callable = None,
) -> RateLimitDecorator:
    """Rate limit decorator factory."""
    return RateLimitDecorator(
        config_name=config_name,
        key_func=key_func,
        on_limit=on_limit,
    )
