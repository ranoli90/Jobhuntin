"""
Part 3: Observability – Lightweight In-Process Metrics & Rate Limiter

Provides:
  - incr(name, tags): increment a counter
  - observe(name, value, tags): record a measurement (latency, etc.)
  - RateLimiter: sliding-window per-minute rate limiter
  - dump(): return current metrics snapshot (for /healthz or debugging)

No external dependencies – pure in-process counters.
For production, these can be forwarded to an OTLP collector or StatsD.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from typing import Any

# ---------------------------------------------------------------------------
# In-process metric storage
# ---------------------------------------------------------------------------

_lock = threading.Lock()
_counters: dict[str, int] = defaultdict(int)
_observations: dict[str, list[float]] = defaultdict(list)


def incr(metric_name: str, tags: dict[str, str] | None = None, value: int = 1) -> None:
    """Increment a counter metric."""
    key = _metric_key(metric_name, tags)
    with _lock:
        _counters[key] += value


def observe(metric_name: str, value: float, tags: dict[str, str] | None = None) -> None:
    """Record an observation (e.g., latency in seconds)."""
    key = _metric_key(metric_name, tags)
    with _lock:
        obs = _observations[key]
        obs.append(value)
        # Keep bounded: last 1000 observations
        if len(obs) > 1000:
            _observations[key] = obs[-500:]


def dump() -> dict[str, Any]:
    """Return a snapshot of all counters and recent observation stats."""
    with _lock:
        snapshot: dict[str, Any] = {
            "counters": dict(_counters),
            "observations": {},
        }
        for key, vals in _observations.items():
            if vals:
                snapshot["observations"][key] = {
                    "count": len(vals),
                    "min": min(vals),
                    "max": max(vals),
                    "avg": sum(vals) / len(vals),
                    "last": vals[-1],
                }
        return snapshot


def _metric_key(name: str, tags: dict[str, str] | None) -> str:
    if not tags:
        return name
    tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
    return f"{name}{{{tag_str}}}"


# ---------------------------------------------------------------------------
# Sliding-window rate limiter (in-process, approximate)
# ---------------------------------------------------------------------------

class RateLimiter:
    """
    Sliding-window rate limiter with Redis backend support (async) and in-memory fallback.

    Usage:
        limiter = RateLimiter(name="my_limit", max_calls=60, window_seconds=60)
        if not await limiter.allow():
            # back off
    """

    def __init__(self, max_calls: int, window_seconds: float = 60.0, name: str | None = None):
        self.name = name
        self.max_calls = max_calls
        self.window = int(window_seconds)
        # In-memory fallback
        self._timestamps: list[float] = []
        self._lock = threading.Lock()

    async def acquire(self) -> bool:
        """Async check with Redis support (if name provided), else sync fallback."""
        if not self.name:
            return self.allow()
            
        from shared.redis_client import get_redis
        try:
            client = await get_redis()
            now = time.time()
            cutoff = now - self.window
            key = f"rate_limit:{self.name}"
            
            # Use a pipeline for atomicity
            async with client.pipeline(transaction=True) as pipe:
                await pipe.zremrangebyscore(key, 0, cutoff)
                await pipe.zcard(key)
                results = await pipe.execute()
            
            count = results[1]
            if count >= self.max_calls:
                return False
                
            # Add current timestamp
            # We don't need a transaction here strictly, but it's fine
            await client.zadd(key, {str(now): now})
            await client.expire(key, self.window + 10)
            return True

        except Exception:
            # Fallback to in-memory if Redis fails
            return self.allow()

    def allow(self) -> bool:
        """In-memory synchronous check (backward compatible)."""
        return self.allow_sync()

    def allow_sync(self) -> bool:
        """In-memory synchronous check."""
        now = time.monotonic()
        with self._lock:
            # Prune expired timestamps
            cutoff = now - self.window
            self._timestamps = [t for t in self._timestamps if t > cutoff]
            if len(self._timestamps) >= self.max_calls:
                return False
            self._timestamps.append(now)
            return True

    def current_count(self) -> int:
        # Note: accurate only for in-memory or one node. 
        # For Redis, one should query Redis, but we keep this simple.
        now = time.monotonic()
        with self._lock:
            cutoff = now - self.window
            self._timestamps = [t for t in self._timestamps if t > cutoff]
            return len(self._timestamps)

    def next_available_in(self) -> float:
        """Return seconds until the next request slot opens (0 if available)."""
        now = time.monotonic()
        with self._lock:
            cutoff = now - self.window
            # Prune first
            self._timestamps = [t for t in self._timestamps if t > cutoff]
            
            if len(self._timestamps) < self.max_calls:
                return 0.0
            
            # If full, the next slot opens when the oldest timestamp expires
            oldest = self._timestamps[0]
            # Expiration time is oldest + window
            # Remaining time is (oldest + window) - now
            return max(0.0, (oldest + self.window) - now)


# ---------------------------------------------------------------------------
# Rate limiter factory (cached instances)
# ---------------------------------------------------------------------------

_rate_limiters: dict[str, RateLimiter] = {}
_rate_limiter_lock = threading.Lock()


def get_rate_limiter(
    name: str, max_calls: int = 60, window_seconds: float = 60.0
) -> RateLimiter:
    """Return a cached RateLimiter instance for the given name.

    If a limiter with that name already exists, the existing instance is
    returned (max_calls / window_seconds are NOT updated – they are set once).
    This ensures the sliding window is preserved across requests.
    """
    with _rate_limiter_lock:
        limiter = _rate_limiters.get(name)
        if limiter is None:
            limiter = RateLimiter(max_calls=max_calls, window_seconds=window_seconds, name=name)
            _rate_limiters[name] = limiter
        return limiter
