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
    Simple sliding-window rate limiter.

    Usage:
        limiter = RateLimiter(max_calls=60, window_seconds=60)
        if not limiter.allow():
            # back off
    """

    def __init__(self, max_calls: int, window_seconds: float = 60.0):
        self.max_calls = max_calls
        self.window = window_seconds
        self._timestamps: list[float] = []
        self._lock = threading.Lock()

    def allow(self) -> bool:
        """Return True if the call is within rate limit, False otherwise."""
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
        now = time.monotonic()
        with self._lock:
            cutoff = now - self.window
            self._timestamps = [t for t in self._timestamps if t > cutoff]
            return len(self._timestamps)
