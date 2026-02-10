"""
Shared metrics and rate limiting utilities.
"""

import asyncio
import time
from collections import defaultdict
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, max_calls: int, window_seconds: float):
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self.calls: list[float] = []

    def allow(self) -> bool:
        """Check if a call is allowed."""
        now = time.time()

        # Remove old calls outside the window
        self.calls = [call for call in self.calls if now - call < self.window_seconds]

        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True

        return False

    def reset(self) -> None:
        """Reset the rate limiter."""
        self.calls.clear()


# Global rate limiters cache
_rate_limiters: Dict[str, RateLimiter] = defaultdict(lambda: RateLimiter(max_calls=100, window_seconds=60))


def get_rate_limiter(key: str, max_calls: int = 100, window_seconds: float = 60) -> RateLimiter:
    """Get or create a rate limiter for the given key."""
    limiter = _rate_limiters.get(key)
    if limiter is None or limiter.max_calls != max_calls or limiter.window_seconds != window_seconds:
        limiter = RateLimiter(max_calls, window_seconds)
        _rate_limiters[key] = limiter
    return limiter


def incr(metric: str, value: int = 1, tags: Optional[Dict[str, Any]] = None) -> None:
    """Increment a metric counter."""
    # Simple logging-based metrics for now
    # In production, this would send to a metrics service
    tag_str = ""
    if tags:
        tag_str = " " + " ".join(f"{k}={v}" for k, v in tags.items())

    logger.info(f"METRIC: {metric}={value}{tag_str}")


# Circuit breaker for external service calls
_circuit_breakers: Dict[str, Dict[str, Any]] = {}


def get_circuit_breaker_status(service_name: str) -> Dict[str, Any]:
    """Get circuit breaker status for a service."""
    return _circuit_breakers.get(service_name, {
        "state": "closed",
        "failures": 0,
        "last_failure": None,
        "successes": 0,
    })


def record_circuit_breaker_failure(service_name: str) -> None:
    """Record a failure for circuit breaker."""
    if service_name not in _circuit_breakers:
        _circuit_breakers[service_name] = {
            "state": "closed",
            "failures": 0,
            "last_failure": None,
            "successes": 0,
        }

    cb = _circuit_breakers[service_name]
    cb["failures"] += 1
    cb["last_failure"] = time.time()

    # Simple circuit breaker logic
    if cb["failures"] >= 5:  # Open after 5 failures
        cb["state"] = "open"
        logger.warning(f"Circuit breaker opened for {service_name}")


def record_circuit_breaker_success(service_name: str) -> None:
    """Record a success for circuit breaker."""
    if service_name not in _circuit_breakers:
        return

    cb = _circuit_breakers[service_name]
    cb["successes"] += 1

    # Reset failures on success
    if cb["state"] == "open" and cb["successes"] >= 2:  # Close after 2 successes
        cb["state"] = "closed"
        cb["failures"] = 0
        logger.info(f"Circuit breaker closed for {service_name}")


def get_all_circuit_breaker_statuses() -> Dict[str, Dict[str, Any]]:
    """Get all circuit breaker statuses."""
    return _circuit_breakers.copy()
