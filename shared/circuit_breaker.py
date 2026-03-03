"""Circuit breaker implementation for external service calls."""

import logging
import time

logger = logging.getLogger(__name__)


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open."""

    def __init__(self, message: str, retry_after: float):
        super().__init__(message)
        self.retry_after = retry_after


class CircuitBreaker:
    """Simple circuit breaker implementation."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60, expected_exception: type = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def __enter__(self):
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                if self.last_failure_time:
                    retry_after = self.recovery_timeout - (time.time() - self.last_failure_time)
                    raise CircuitBreakerOpen("Circuit breaker is OPEN", retry_after)
                else:
                    raise CircuitBreakerOpen("Circuit breaker is OPEN", self.recovery_timeout)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type and issubclass(exc_type, self.expected_exception):
            self._on_failure()
        else:
            self._on_success()

    def call(self, func, *args, **kwargs):
        """Call a function through the circuit breaker."""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                retry_after = self.recovery_timeout - (time.time() - self.last_failure_time)
                raise CircuitBreakerOpen("Circuit breaker is OPEN", retry_after)

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit breaker."""
        if self.last_failure_time is None:
            return False
        return time.time() - self.last_failure_time >= self.recovery_timeout

    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        self.state = "CLOSED"

    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


# Global circuit breakers cache
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(service_name: str, **kwargs) -> CircuitBreaker:
    """Get or create a circuit breaker for the given service."""
    if service_name not in _circuit_breakers:
        _circuit_breakers[service_name] = CircuitBreaker(**kwargs)
    return _circuit_breakers[service_name]
