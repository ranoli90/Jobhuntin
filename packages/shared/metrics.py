"""
Part 3: Observability – Lightweight In-Process Metrics & Rate Limiter

Provides:
  - incr(name, tags): increment a counter
  - observe(name, value, tags): record a measurement (latency, etc.)
  - RateLimiter: sliding-window per-minute rate limiter
  - dump(): return current metrics snapshot (for /healthz or debugging)
  - setup_otel_metrics(): optional bridge to export metrics via OTLP

In-process counters are always maintained. When setup_otel_metrics() is called
(typically from telemetry.py), counters and observations are also forwarded to
an OpenTelemetry MeterProvider for export to Prometheus, Datadog, etc.
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

# Optional OTLP metric instruments (populated by setup_otel_metrics)
_otel_counters: dict[str, Any] = {}
_otel_histograms: dict[str, Any] = {}
_otel_meter: Any = None


def incr(metric_name: str, tags: dict[str, str] | None = None, value: int = 1) -> None:
    """Increment a counter metric."""
    key = _metric_key(metric_name, tags)
    with _lock:
        _counters[key] += value
    # Forward to OTLP if configured
    if _otel_meter is not None:
        otel_counter = _otel_counters.get(metric_name)
        if otel_counter is None:
            otel_counter = _otel_meter.create_counter(
                name=metric_name.replace(".", "_"),
                description=f"Counter: {metric_name}",
            )
            _otel_counters[metric_name] = otel_counter
        otel_counter.add(value, attributes=tags or {})


def observe(metric_name: str, value: float, tags: dict[str, str] | None = None) -> None:
    """Record an observation (e.g., latency in seconds)."""
    key = _metric_key(metric_name, tags)
    with _lock:
        obs = _observations[key]
        obs.append(value)
        # Keep bounded: last 1000 observations
        if len(obs) > 1000:
            _observations[key] = obs[-500:]
    # Forward to OTLP if configured
    if _otel_meter is not None:
        otel_hist = _otel_histograms.get(metric_name)
        if otel_hist is None:
            otel_hist = _otel_meter.create_histogram(
                name=metric_name.replace(".", "_"),
                description=f"Histogram: {metric_name}",
            )
            _otel_histograms[metric_name] = otel_hist
        otel_hist.record(value, attributes=tags or {})


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

    def __init__(
        self, max_calls: int, window_seconds: float = 60.0, name: str | None = None
    ):
        self.name = name
        self.max_calls = max_calls
        self.window = int(window_seconds)
        # In-memory fallback
        self._timestamps: list[float] = []
        self._lock = threading.Lock()

    # Lua script for atomic sliding-window rate limiting.
    # Removes expired entries, checks count, and adds new entry in one round-trip.
    # Returns 1 if allowed, 0 if rate limited.
    _LUA_SLIDING_WINDOW = """
    local key = KEYS[1]
    local now = tonumber(ARGV[1])
    local cutoff = tonumber(ARGV[2])
    local max_calls = tonumber(ARGV[3])
    local window_ttl = tonumber(ARGV[4])

    redis.call('ZREMRANGEBYSCORE', key, 0, cutoff)
    local count = redis.call('ZCARD', key)
    if count >= max_calls then
        return 0
    end
    redis.call('ZADD', key, now, tostring(now) .. ':' .. tostring(math.random(1000000)))
    redis.call('EXPIRE', key, window_ttl)
    return 1
    """

    async def acquire(self) -> bool:
        """Async check with Redis support (if name provided), else sync fallback.

        Uses an atomic Lua script to eliminate the race window between
        ZCARD and ZADD that existed in the previous pipeline approach.
        Falls back to in-memory if Redis is unavailable.
        """
        if not self.name:
            return self.allow()

        from shared.config import get_settings

        s = get_settings()
        if not s.redis_url:
            return self.allow()

        from shared.redis_client import get_redis

        try:
            client = await get_redis()
            now = time.time()
            cutoff = now - self.window
            key = f"rate_limit:{self.name}"

            result = await client.eval(
                self._LUA_SLIDING_WINDOW,
                1,  # number of KEYS
                key,  # KEYS[1]
                str(now),
                str(cutoff),
                str(self.max_calls),
                str(self.window + 10),
            )
            return int(result) == 1

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
            limiter = RateLimiter(
                max_calls=max_calls, window_seconds=window_seconds, name=name
            )
            _rate_limiters[name] = limiter
        return limiter


def setup_otel_metrics(service_name: str = "sorce") -> None:
    """
    Initialize an OpenTelemetry MeterProvider so that incr() and observe()
    forward data to an OTLP collector (or Prometheus exporter).

    Requires OTEL_EXPORTER_OTLP_ENDPOINT to be set. No-ops silently if
    the OTLP SDK is not installed or the env var is missing.
    """
    import os

    global _otel_meter

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        return

    try:
        from opentelemetry import metrics as otel_metrics
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
            OTLPMetricExporter,
        )
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import SERVICE_NAME, Resource

        resource = Resource.create({SERVICE_NAME: service_name})
        reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(),
            export_interval_millis=30_000,  # flush every 30s
        )
        provider = MeterProvider(resource=resource, metric_readers=[reader])
        otel_metrics.set_meter_provider(provider)
        _otel_meter = provider.get_meter(service_name)
    except Exception:
        pass  # Silently degrade — in-process metrics still work
