"""
Stripe client wrapper with circuit breaker protection.

Provides a protected Stripe client that automatically handles failures
with circuit breaker pattern.
"""

from __future__ import annotations

from functools import wraps
from typing import TypeVar, Callable, Any

from shared.config import get_settings
from shared.logging_config import get_logger
from shared.circuit_breaker import get_circuit_breaker, CircuitBreakerOpen

logger = get_logger("sorce.stripe")

T = TypeVar("T")

# Cache the stripe module
_stripe_module = None


def get_stripe():
    """Lazy-import and configure stripe SDK."""
    global _stripe_module
    if _stripe_module is None:
        import stripe
        s = get_settings()
        stripe.api_key = s.stripe_secret_key
        _stripe_module = stripe
    return _stripe_module


class StripeCircuitBreaker:
    """
    Wrapper for Stripe API calls with circuit breaker protection.
    
    Usage:
        stripe_cb = StripeCircuitBreaker()
        
        # Protected call
        customer = stripe_cb.call(
            lambda: stripe.Customer.create(email="test@example.com")
        )
    """
    
    def __init__(self):
        self._cb = get_circuit_breaker("stripe")
    
    def call(self, func: Callable[[], T], fallback: T | None = None) -> T | None:
        """
        Execute a Stripe API call with circuit breaker protection.
        
        Args:
            func: A callable that performs the Stripe API call
            fallback: Optional fallback value if circuit is open
            
        Returns:
            Result of the Stripe call, or fallback if circuit is open
            
        Raises:
            Exception: Re-raises Stripe exceptions if circuit is closed
        """
        import asyncio
        
        # Get or create event loop
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        
        if loop is not None:
            # We're in an async context, need to handle synchronously
            # Since Stripe SDK is sync, we just check circuit state manually
            if self._cb.state.value == "open":
                logger.warning("Stripe circuit breaker is open, returning fallback")
                if fallback is not None:
                    return fallback
                raise CircuitBreakerOpen("stripe", self._cb.config.timeout_seconds)
        
        try:
            result = func()
            # Manually record success (sync version)
            self._cb.stats.successes += 1
            self._cb.stats.total_successes += 1
            self._cb.stats.failures = 0  # Reset on success
            return result
        except Exception as e:
            # Manually record failure (sync version)
            self._cb.stats.failures += 1
            self._cb.stats.total_failures += 1
            
            # Check if we should open the circuit
            if self._cb.stats.failures >= self._cb.config.failure_threshold:
                from shared.circuit_breaker import CircuitState
                import time
                self._cb.state = CircuitState.OPEN
                self._cb._opened_at = time.monotonic()
                logger.error(
                    "Stripe circuit breaker opened after %d failures",
                    self._cb.stats.failures
                )
            
            logger.warning("Stripe API call failed: %s", str(e)[:100])
            raise


# Global instance
_stripe_cb = None


def get_protected_stripe() -> StripeCircuitBreaker:
    """Get the global Stripe client with circuit breaker protection."""
    global _stripe_cb
    if _stripe_cb is None:
        _stripe_cb = StripeCircuitBreaker()
    return _stripe_cb


def protected_stripe_call(func: Callable[[], T], fallback: T | None = None) -> T | None:
    """
    Convenience function for making protected Stripe calls.
    
    Example:
        from backend.domain.stripe_client import protected_stripe_call
        
        customer = protected_stripe_call(
            lambda: stripe.Customer.create(email="test@example.com")
        )
    """
    return get_protected_stripe().call(func, fallback)
