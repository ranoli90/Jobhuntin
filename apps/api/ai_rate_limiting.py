"""AI Rate Limiting Module.

This module provides comprehensive rate limiting for AI endpoints to prevent abuse,
ensure fair usage, and protect against DDoS attacks.
"""

from __future__ import annotations

import time
from typing import Any

from shared.logging_config import get_logger
from shared.redis_client import get_redis

from shared.metrics import incr

logger = get_logger("sorce.api.ai_rate_limiting")


class RateLimitExceededError(Exception):
    """Raised when rate limit is exceeded."""

    pass


class RateLimiter:
    """Rate limiter for AI endpoints using Redis."""

    def __init__(self, redis_client=None):
        self.redis = redis_client or get_redis()
        self.limits = {
            'ai_suggestions': {
                'requests_per_minute': 10,
                'requests_per_hour': 100,
                'requests_per_day': 500,
            },
            'ai_job_matching': {
                'requests_per_minute': 20,
                'requests_per_hour': 200,
                'requests_per_day': 1000,
            },
            'ai_onboarding': {
                'requests_per_minute': 5,
                'requests_per_hour': 50,
                'requests_per_day': 250,
            },
            'ai_general': {
                'requests_per_minute': 30,
                'requests_per_hour': 300,
                'requests_per_day': 1500,
            },
        }

    async def check_rate_limit(
        self,
        identifier: str,
        endpoint_type: str,
        ip_address: str | None = None,
        user_id: str | None = None,
    ) -> bool:
        """Check if the request is within rate limits.

        Args:
            identifier: Unique identifier for the request
            endpoint_type: Type of endpoint for rate limiting rules
            ip_address: Client IP address for IP-based limiting
            user_id: User ID for user-based limiting

        Returns:
            True if within limits, False otherwise

        Raises:
            RateLimitExceededError: If rate limit is exceeded

        """
        limits = self.limits.get(endpoint_type, self.limits['ai_general'])

        # Check multiple rate limit tiers
        await self._check_minute_limit(identifier, endpoint_type, limits['requests_per_minute'])
        await self._check_hour_limit(identifier, endpoint_type, limits['requests_per_hour'])
        await self._check_day_limit(identifier, endpoint_type, limits['requests_per_day'])

        # Check IP-based limits
        if ip_address:
            await self._check_ip_limit(ip_address, endpoint_type)

        # Check user-based limits
        if user_id:
            await self._check_user_limit(user_id, endpoint_type)

        return True

    async def _check_minute_limit(self, identifier: str, endpoint_type: str, limit: int) -> None:
        """Check per-minute rate limit."""
        key = f"rate_limit:minute:{endpoint_type}:{identifier}"
        current_time = int(time.time())
        minute_key = f"{key}:{current_time // 60}"

        # Get current count
        current_count = await self.redis.get(minute_key)
        current_count = int(current_count) if current_count else 0

        if current_count >= limit:
            incr(f"rate_limit.exceeded:{endpoint_type}")
            raise RateLimitExceededError(f"Rate limit exceeded for {endpoint_type} (per-minute)")

        # Increment counter with expiration
        await self.redis.setex(minute_key, 60, str(current_count + 1))

    async def _check_hour_limit(self, identifier: str, endpoint_type: str, limit: int) -> None:
        """Check per-hour rate limit."""
        key = f"rate_limit:hour:{endpoint_type}:{identifier}"
        current_time = int(time.time())
        hour_key = f"{key}:{current_time // 3600}"

        # Get current count
        current_count = await self.redis.get(hour_key)
        current_count = int(current_count) if current_count else 0

        if current_count >= limit:
            incr(f"rate_limit.exceeded:{endpoint_type}")
            raise RateLimitExceededError(f"Rate limit exceeded for {endpoint_type} (per-hour)")

        # Increment counter with expiration
        await self.redis.setex(hour_key, 3600, str(current_count + 1))

    async def _check_day_limit(self, identifier: str, endpoint_type: str, limit: int) -> None:
        """Check per-day rate limit."""
        key = f"rate_limit:day:{endpoint_type}:{identifier}"
        current_time = int(time.time())
        day_key = f"{key}:{current_time // 86400}"

        # Get current count
        current_count = await self.redis.get(day_key)
        current_count = int(current_count) if current_count else 0

        if current_count >= limit:
            incr(f"rate_limit.exceeded:{endpoint_type}")
            raise RateLimitExceededError(f"Rate limit exceeded for {endpoint_type} (per-day)")

        # Increment counter with expiration
        await self.redis.setex(day_key, 86400, str(current_count + 1))

    async def _check_ip_limit(self, ip_address: str, endpoint_type: str) -> None:
        """Check IP-based rate limits."""
        ip_limits = {
            'requests_per_minute': 50,
            'requests_per_hour': 500,
            'requests_per_day': 2000,
        }

        key = f"rate_limit:ip:{endpoint_type}:{ip_address}"
        await self._check_minute_limit(key, f"ip_{endpoint_type}", ip_limits['requests_per_minute'])
        await self._check_hour_limit(key, f"ip_{endpoint_type}", ip_limits['requests_per_hour'])
        await self._check_day_limit(key, f"ip_{endpoint_type}", ip_limits['requests_per_day'])

    async def _check_user_limit(self, user_id: str, endpoint_type: str) -> None:
        """Check user-based rate limits."""
        user_limits = {
            'requests_per_minute': 20,
            'requests_per_hour': 200,
            'requests_per_day': 1000,
        }

        key = f"rate_limit:user:{endpoint_type}:{user_id}"
        await self._check_minute_limit(key, f"user_{endpoint_type}", user_limits['requests_per_minute'])
        await self._check_hour_limit(key, f"user_{endpoint_type}", user_limits['requests_per_hour'])
        await self._check_day_limit(key, f"user_{endpoint_type}", user_limits['requests_per_day'])

    async def get_rate_limit_status(
        self,
        identifier: str,
        endpoint_type: str,
        ip_address: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """Get current rate limit status.

        Args:
            identifier: Unique identifier for the request
            endpoint_type: Type of endpoint
            ip_address: Client IP address
            user_id: User ID

        Returns:
            Dictionary containing rate limit status

        """
        limits = self.limits.get(endpoint_type, self.limits['ai_general'])

        current_time = int(time.time())

        status = {
            'identifier': identifier,
            'endpoint_type': endpoint_type,
            'limits': limits,
            'current': {
                'minute': await self._get_window_count(f"rate_limit:minute:{endpoint_type}:{identifier}", current_time // 60),
                'hour': await self._get_window_count(f"rate_limit:hour:{endpoint_type}:{identifier}", current_time // 3600),
                'day': await self._get_window_count(f"rate_limit:day:{endpoint_type}:{identifier}", current_time // 86400),
            },
            'remaining': {
                'minute': max(0, limits['requests_per_minute'] - await self._get_window_count(f"rate_limit:minute:{endpoint_type}:{identifier}", current_time // 60)),
                'hour': max(0, limits['requests_per_hour'] - await self._get_window_count(f"rate_limit:hour:{endpoint_type}:{identifier}", current_time // 3600)),
                'day': max(0, limits['requests_per_day'] - await self._get_window_count(f"rate_limit:day:{endpoint_type}:{identifier}", current_time // 86400)),
            },
        }

        # Add IP-based status if available
        if ip_address:
            ip_key = f"rate_limit:ip:{endpoint_type}:{ip_address}"
            status['ip'] = {
                'current': {
                    'minute': await self._get_window_count(f"{ip_key}:minute", current_time // 60),
                    'hour': await self._get_window_count(f"{ip_key}:hour", current_time // 3600),
                    'day': await self._get_window_count(f"{ip_key}:day", current_time // 86400),
                }
            }

        # Add user-based status if available
        if user_id:
            user_key = f"rate_limit:user:{endpoint_type}:{user_id}"
            status['user'] = {
                'current': {
                    'minute': await self._get_window_count(f"{user_key}:minute", current_time // 60),
                    'hour': await self._get_window_count(f"{user_key}:hour", current_time // 3600),
                    'day': await self._get_window_count(f"{user_key}:day", current_time // 86400),
                }
            }

        return status

    async def _get_window_count(self, key_prefix: str, window: int) -> int:
        """Get count for a specific time window."""
        key = f"{key_prefix}:{window}"
        count = await self.redis.get(key)
        return int(count) if count else 0

    async def reset_rate_limit(
        self,
        identifier: str,
        endpoint_type: str,
        window: str = 'all',
    ) -> None:
        """Reset rate limit for a specific identifier.

        Args:
            identifier: Unique identifier for the request
            endpoint_type: Type of endpoint
            window: Time window to reset ('minute', 'hour', 'day', 'all')

        """
        current_time = int(time.time())

        if window == 'all':
            # Reset all windows
            await self.redis.delete(f"rate_limit:minute:{endpoint_type}:{identifier}")
            await self.redis.delete(f"rate_limit:hour:{endpoint_type}:{identifier}")
            await self.redis.delete(f"rate_limit:day:{endpoint_type}:{identifier}")
        elif window == 'minute':
            await self.redis.delete(f"rate_limit:minute:{endpoint_type}:{identifier}:{current_time // 60}")
        elif window == 'hour':
            await self.redis.delete(f"rate_limit:hour:{endpoint_type}:{identifier}:{current_time // 3600}")
        elif window == 'day':
            await self.redis.delete(f"rate_limit:day:{endpoint_type}:{identifier}:{current_time // 86400}")

        logger.info(f"Rate limit reset for {identifier} on {endpoint_type} ({window} window)")


class AdaptiveRateLimiter(RateLimiter):
    """Adaptive rate limiter that adjusts limits based on system load."""

    def __init__(self, redis_client=None):
        super().__init__(redis_client)
        self.load_factor = 1.0
        self.last_load_check = 0

    async def check_rate_limit(
        self,
        identifier: str,
        endpoint_type: str,
        ip_address: str | None = None,
        user_id: str | None = None,
    ) -> bool:
        """Check rate limit with adaptive adjustments."""
        # Update load factor every 60 seconds
        current_time = time.time()
        if current_time - self.last_load_check > 60:
            await self._update_load_factor()
            self.last_load_check = current_time

        # Adjust limits based on load factor
        adjusted_limits = self._adjust_limits(endpoint_type)

        # Check with adjusted limits
        await self._check_minute_limit_adaptive(identifier, endpoint_type, adjusted_limits['requests_per_minute'])
        await self._check_hour_limit_adaptive(identifier, endpoint_type, adjusted_limits['requests_per_hour'])
        await self._check_day_limit_adaptive(identifier, endpoint_type, adjusted_limits['requests_per_day'])

        return True

    async def _update_load_factor(self) -> None:
        """Update load factor based on system metrics."""
        try:
            # Check Redis memory usage
            info = await self.redis.info()
            used_memory = int(info.get('used_memory', 0))
            max_memory = int(info.get('max_memory', 0))

            if max_memory > 0:
                memory_usage = used_memory / max_memory

                # Adjust load factor based on memory usage
                if memory_usage > 0.8:
                    self.load_factor = 0.5  # Reduce limits by 50%
                elif memory_usage > 0.6:
                    self.load_factor = 0.7  # Reduce limits by 30%
                elif memory_usage > 0.4:
                    self.load_factor = 0.85  # Reduce limits by 15%
                else:
                    self.load_factor = 1.0  # Full limits

            logger.info(f"Updated load factor to {self.load_factor} based on memory usage: {memory_usage:.2%}")

        except Exception as e:
            logger.error(f"Error updating load factor: {e}")
            self.load_factor = 1.0

    def _adjust_limits(self, endpoint_type: str) -> dict[str, int]:
        """Adjust limits based on load factor."""
        base_limits = self.limits.get(endpoint_type, self.limits['ai_general'])

        return {
            'requests_per_minute': int(base_limits['requests_per_minute'] * self.load_factor),
            'requests_per_hour': int(base_limits['requests_per_hour'] * self.load_factor),
            'requests_per_day': int(base_limits['requests_per_day'] * self.load_factor),
        }

    async def _check_minute_limit_adaptive(self, identifier: str, endpoint_type: str, limit: int) -> None:
        """Check per-minute rate limit with adjusted limits."""
        key = f"rate_limit:minute:{endpoint_type}:{identifier}"
        current_time = int(time.time())
        minute_key = f"{key}:{current_time // 60}"

        current_count = await self.redis.get(minute_key)
        current_count = int(current_count) if current_count else 0

        if current_count >= limit:
            incr(f"rate_limit.exceeded:{endpoint_type}")
            raise RateLimitExceededError(f"Rate limit exceeded for {endpoint_type} (per-minute, adjusted for load)")

        await self.redis.setex(minute_key, 60, str(current_count + 1))

    async def _check_hour_limit_adaptive(self, identifier: str, endpoint_type: str, limit: int) -> None:
        """Check per-hour rate limit with adjusted limits."""
        key = f"rate_limit:hour:{endpoint_type}:{identifier}"
        current_time = int(time.time())
        hour_key = f"{key}:{current_time // 3600}"

        current_count = await self.redis.get(hour_key)
        current_count = int(current_count) if current_count else 0

        if current_count >= limit:
            incr(f"rate_limit.exceeded:{endpoint_type}")
            raise RateLimitExceededError(f"Rate limit exceeded for {endpoint_type} (per-hour, adjusted for load)")

        await self.redis.setex(hour_key, 3600, str(current_count + 1))

    async def _check_day_limit_adaptive(self, identifier: str, endpoint_type: str, limit: int) -> None:
        """Check per-day rate limit with adjusted limits."""
        key = f"rate_limit:day:{endpoint_type}:{identifier}"
        current_time = int(time.time())
        day_key = f"{key}:{current_time // 86400}"

        current_count = await self.redis.get(day_key)
        current_count = int(current_count) if current_count else 0

        if current_count >= limit:
            incr(f"rate_limit.exceeded:{endpoint_type}")
            raise RateLimitExceededError(f"Rate limit exceeded for {endpoint_type} (per-day, adjusted for load)")

        await self.redis.setex(day_key, 86400, str(current_count + 1))


# ---------------------------------------------------------------------------
# Global Rate Limiter Instance
# ---------------------------------------------------------------------------

rate_limiter = RateLimiter()
adaptive_rate_limiter = AdaptiveRateLimiter()


# ---------------------------------------------------------------------------
# Decorator for Rate Limiting
# ---------------------------------------------------------------------------

def rate_limit(endpoint_type: str, adaptive: bool = False):
    """Decorator for rate limiting AI endpoints.

    Args:
        endpoint_type: Type of endpoint for rate limiting rules
        adaptive: Whether to use adaptive rate limiting

    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract request context
            request = kwargs.get('request')
            if not request:
                return await func(*args, **kwargs)

            # Get identifiers
            identifier = request.headers.get('x-request-id', 'unknown')
            ip_address = request.client.host if request.client else 'unknown'
            user_id = getattr(request.state, 'user_id', None)

            # Check rate limit
            limiter = adaptive_rate_limiter if adaptive else rate_limiter
            await limiter.check_rate_limit(identifier, endpoint_type, ip_address, user_id)

            # Add rate limit headers
            kwargs['rate_limit_status'] = await limiter.get_rate_limit_status(
                identifier, endpoint_type, ip_address, user_id
            )

            return await func(*args, **kwargs)

        return wrapper
    return decorator
