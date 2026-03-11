"""
API Logger and Monitoring System

Comprehensive API request/response logging with performance monitoring,
security tracking, and analytics collection.
"""

import asyncio
import time
import traceback
import uuid
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from shared.logging_config import LogContext, get_logger, sanitize_for_log

logger = get_logger("sorce.api_logger")


def _mask_ip_for_log(ip: str) -> str:
    """Mask IP for PII-safe logging. Uses backend masking when available."""
    try:
        from packages.backend.domain.masking import mask_ip

        return mask_ip(ip)
    except ImportError:
        return ip[:8] + "***" if len(ip) > 8 else "***"


class LogLevel(Enum):
    """Log levels for different types of events."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class EventType(Enum):
    """Types of API events."""

    REQUEST_START = "request_start"
    REQUEST_END = "request_end"
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    VALIDATION_ERROR = "validation_error"
    RATE_LIMITED = "rate_limited"
    SECURITY_ALERT = "security_alert"
    PERFORMANCE_ISSUE = "performance_issue"
    ERROR_OCCURRED = "error_occurred"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"


@dataclass
class APIRequest:
    """API request metadata."""

    request_id: str
    method: str
    url: str
    path: str
    query_params: Dict[str, Any]
    headers: Dict[str, str]
    user_agent: str
    ip_address: str
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    session_id: Optional[str] = None
    api_key: Optional[str] = None
    content_type: Optional[str] = None
    content_length: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class APIResponse:
    """API response metadata."""

    request_id: str
    status_code: int
    content_type: Optional[str] = None
    content_length: Optional[int] = None
    response_time_ms: float = 0.0
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SecurityEvent:
    """Security-related event metadata."""

    event_id: str
    request_id: str
    event_type: str
    severity: str
    description: str
    ip_address: str
    user_agent: str
    user_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PerformanceMetrics:
    """Performance metrics for a request."""

    request_id: str
    endpoint: str
    method: str
    response_time_ms: float
    db_query_time_ms: float = 0.0
    cache_lookup_time_ms: float = 0.0
    auth_time_ms: float = 0.0
    validation_time_ms: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


class MetricsCollector:
    """Collects and aggregates API metrics."""

    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.request_metrics: deque = deque(maxlen=10000)
        self.error_counts: defaultdict = defaultdict(int)
        self.endpoint_stats: defaultdict = defaultdict(
            lambda: {
                "count": 0,
                "total_response_time": 0.0,
                "avg_response_time": 0.0,
                "error_count": 0,
                "last_seen": None,
            }
        )
        self.security_events: deque = deque(maxlen=1000)
        self.active_requests: Dict[str, datetime] = {}
        self._cleanup_task: Optional[asyncio.Task] = None

    def start_cleanup_task(self) -> None:
        """Start background cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_old_data())

    async def _cleanup_old_data(self) -> None:
        """Clean up old metrics data."""
        while True:
            try:
                cutoff_time = datetime.utcnow() - timedelta(hours=self.retention_hours)

                # Clean request metrics
                while (
                    self.request_metrics
                    and self.request_metrics[0].timestamp < cutoff_time
                ):
                    self.request_metrics.popleft()

                # Clean security events
                while (
                    self.security_events
                    and self.security_events[0].timestamp < cutoff_time
                ):
                    self.security_events.popleft()

                # Clean active requests (stale ones)
                stale_requests = [
                    req_id
                    for req_id, start_time in self.active_requests.items()
                    if start_time < cutoff_time
                ]
                for req_id in stale_requests:
                    del self.active_requests[req_id]

                await asyncio.sleep(3600)  # Clean every hour

            except Exception as e:
                logger.error(f"Metrics cleanup error: {e}")
                await asyncio.sleep(300)  # Retry sooner on error

    def record_request_start(self, request: APIRequest) -> None:
        """Record the start of a request."""
        self.active_requests[request.request_id] = request.timestamp

    def record_request_end(self, response: APIResponse) -> None:
        """Record the end of a request."""
        if response.request_id in self.active_requests:
            del self.active_requests[response.request_id]

        self.request_metrics.append(response)

        # Update endpoint stats
        endpoint_key = f"{response.request_id.split(':')[0]}:{response.status_code}"
        stats = self.endpoint_stats[endpoint_key]
        stats["count"] += 1
        stats["total_response_time"] += response.response_time_ms
        stats["avg_response_time"] = stats["total_response_time"] / stats["count"]
        stats["last_seen"] = response.timestamp

        if response.status_code >= 400:
            stats["error_count"] += 1
            self.error_counts[f"{response.status_code}"] += 1

    def record_security_event(self, event: SecurityEvent) -> None:
        """Record a security event."""
        self.security_events.append(event)
        logger.warning(
            f"Security event: {event.event_type}",
            extra={
                "event_id": event.event_id,
                "request_id": event.request_id,
                "severity": event.severity,
                "ip_address": event.ip_address,
                "user_id": event.user_id,
                "details": sanitize_for_log(event.details),
            },
        )

    def record_performance_metrics(self, metrics: PerformanceMetrics) -> None:
        """Record detailed performance metrics."""
        self.request_metrics.append(metrics)

    def get_endpoint_stats(self, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for endpoints."""
        if endpoint:
            return {endpoint: self.endpoint_stats.get(endpoint, {})}
        return dict(self.endpoint_stats)

    def get_error_summary(self) -> Dict[str, int]:
        """Get error count summary."""
        return dict(self.error_counts)

    def get_security_events(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent security events."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [
            asdict(event)
            for event in self.security_events
            if event.timestamp >= cutoff_time
        ]

    def get_active_requests_count(self) -> int:
        """Get count of currently active requests."""
        return len(self.active_requests)

    def get_performance_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get performance summary for recent requests."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_metrics = [
            metric for metric in self.request_metrics if metric.timestamp >= cutoff_time
        ]

        if not recent_metrics:
            return {}

        response_times = [
            m.response_time_ms for m in recent_metrics if hasattr(m, "response_time_ms")
        ]

        return {
            "total_requests": len(recent_metrics),
            "avg_response_time": sum(response_times) / len(response_times)
            if response_times
            else 0,
            "min_response_time": min(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "requests_per_hour": len(recent_metrics) / hours,
            "error_rate": sum(
                1
                for m in recent_metrics
                if hasattr(m, "status_code") and m.status_code >= 400
            )
            / len(recent_metrics),
        }


class APILogger:
    """Main API logging and monitoring system."""

    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.security_rules: List[Callable] = []
        self.performance_thresholds: Dict[str, float] = {
            "response_time_warning": 1000.0,  # 1 second
            "response_time_critical": 5000.0,  # 5 seconds
            "error_rate_warning": 0.05,  # 5%
            "error_rate_critical": 0.10,  # 10%
        }
        self.sensitive_fields: set = {
            "password",
            "token",
            "api_key",
            "secret",
            "key",
            "authorization",
            "cookie",
            "session",
            "csrf",
            "email",
        }

    def start_monitoring(self) -> None:
        """Start the monitoring system."""
        self.metrics_collector.start_cleanup_task()
        logger.info("API monitoring started")

    def add_security_rule(
        self, rule: Callable[[APIRequest], Optional[SecurityEvent]]
    ) -> None:
        """Add a security rule for request monitoring."""
        self.security_rules.append(rule)

    def log_request_start(self, request: APIRequest) -> str:
        """Log the start of a request."""
        # Set log context
        LogContext.set(
            user_id=request.user_id,
            tenant_id=request.tenant_id,
            application_id=request.request_id,
        )

        # Record metrics
        self.metrics_collector.record_request_start(request)

        # Apply security rules
        for rule in self.security_rules:
            try:
                event = rule(request)
                if event:
                    self.metrics_collector.record_security_event(event)
            except Exception as e:
                logger.error(f"Security rule error: {e}")

        # Log request start
        logger.info(
            f"API request started: {request.method} {request.path}",
            extra={
                "event_type": EventType.REQUEST_START.value,
                "request_id": request.request_id,
                "method": request.method,
                "path": request.path,
                "query_params": self._sanitize_params(request.query_params),
                "user_agent": request.user_agent,
                "ip_address": request.ip_address,
                "user_id": request.user_id,
                "tenant_id": request.tenant_id,
            },
        )

        return request.request_id

    def log_request_end(self, response: APIResponse) -> None:
        """Log the end of a request."""
        # Record metrics
        self.metrics_collector.record_request_end(response)

        # Check performance thresholds
        self._check_performance_thresholds(response)

        # Determine log level based on status code
        log_level = LogLevel.INFO
        if response.status_code >= 500:
            log_level = LogLevel.ERROR
        elif response.status_code >= 400:
            log_level = LogLevel.WARNING

        # Log request end
        log_method = getattr(logger, log_level.value, logger.info)
        log_method(
            f"API request completed: {response.status_code} in {response.response_time_ms:.2f}ms",
            extra={
                "event_type": EventType.REQUEST_END.value,
                "request_id": response.request_id,
                "status_code": response.status_code,
                "response_time_ms": response.response_time_ms,
                "content_length": response.content_length,
                "error_message": response.error_message,
            },
        )

        # Clear log context
        LogContext.clear()

    def log_auth_event(
        self,
        request_id: str,
        success: bool,
        method: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log authentication events."""
        event_type = EventType.AUTH_SUCCESS if success else EventType.AUTH_FAILURE
        log_level = LogLevel.INFO if success else LogLevel.WARNING

        log_method = getattr(logger, log_level.value, logger.info)
        log_method(
            f"Auth {method}: {'success' if success else 'failure'}",
            extra={
                "event_type": event_type.value,
                "request_id": request_id,
                "auth_method": method,
                "user_id": user_id,
                "details": sanitize_for_log(details or {}),
            },
        )

    def log_validation_error(
        self, request_id: str, errors: List[str], field_name: Optional[str] = None
    ) -> None:
        """Log validation errors."""
        logger.warning(
            f"Validation failed: {len(errors)} errors",
            extra={
                "event_type": EventType.VALIDATION_ERROR.value,
                "request_id": request_id,
                "field_name": field_name,
                "errors": errors,
            },
        )

    def log_security_event(self, event: SecurityEvent) -> None:
        """Log security events."""
        self.metrics_collector.record_security_event(event)

    def log_performance_metrics(self, metrics: PerformanceMetrics) -> None:
        """Log detailed performance metrics."""
        self.metrics_collector.record_performance_metrics(metrics)

        # Check for performance issues
        if (
            metrics.response_time_ms
            > self.performance_thresholds["response_time_critical"]
        ):
            logger.error(
                f"Critical performance issue: {metrics.response_time_ms:.2f}ms",
                extra={
                    "event_type": EventType.PERFORMANCE_ISSUE.value,
                    "request_id": metrics.request_id,
                    "endpoint": metrics.endpoint,
                    "response_time_ms": metrics.response_time_ms,
                },
            )
        elif (
            metrics.response_time_ms
            > self.performance_thresholds["response_time_warning"]
        ):
            logger.warning(
                f"Performance warning: {metrics.response_time_ms:.2f}ms",
                extra={
                    "event_type": EventType.PERFORMANCE_ISSUE.value,
                    "request_id": metrics.request_id,
                    "endpoint": metrics.endpoint,
                    "response_time_ms": metrics.response_time_ms,
                },
            )

    def log_cache_event(
        self, request_id: str, cache_key: str, hit: bool, lookup_time_ms: float = 0.0
    ) -> None:
        """Log cache events."""
        event_type = EventType.CACHE_HIT if hit else EventType.CACHE_MISS
        logger.debug(
            f"Cache {'hit' if hit else 'miss'}: {cache_key}",
            extra={
                "event_type": event_type.value,
                "request_id": request_id,
                "cache_key": cache_key,
                "lookup_time_ms": lookup_time_ms,
            },
        )

    def _sanitize_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize query parameters for logging."""
        sanitized = {}
        for key, value in params.items():
            if any(sensitive in key.lower() for sensitive in self.sensitive_fields):
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value
        return sanitized

    def _check_performance_thresholds(self, response: APIResponse) -> None:
        """Check if response exceeds performance thresholds."""
        if (
            response.response_time_ms
            > self.performance_thresholds["response_time_critical"]
        ):
            logger.error(
                f"Critical response time: {response.response_time_ms:.2f}ms",
                extra={
                    "event_type": EventType.PERFORMANCE_ISSUE.value,
                    "request_id": response.request_id,
                    "severity": "critical",
                    "response_time_ms": response.response_time_ms,
                },
            )
        elif (
            response.response_time_ms
            > self.performance_thresholds["response_time_warning"]
        ):
            logger.warning(
                f"Slow response time: {response.response_time_ms:.2f}ms",
                extra={
                    "event_type": EventType.PERFORMANCE_ISSUE.value,
                    "request_id": response.request_id,
                    "severity": "warning",
                    "response_time_ms": response.response_time_ms,
                },
            )

    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        return {
            "performance": self.metrics_collector.get_performance_summary(),
            "endpoints": self.metrics_collector.get_endpoint_stats(),
            "errors": self.metrics_collector.get_error_summary(),
            "security": self.metrics_collector.get_security_events(),
            "active_requests": self.metrics_collector.get_active_requests_count(),
        }


class APILoggingMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for automatic API logging."""

    def __init__(self, app, api_logger: APILogger):
        super().__init__(app)
        self.api_logger = api_logger

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through logging middleware."""
        # Generate request ID
        request_id = str(uuid.uuid4())

        # Extract request information
        start_time = time.time()

        # Get client IP (masked for PII-safe logging)
        client_ip = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        ip_masked = _mask_ip_for_log(client_ip)

        # Create request object
        api_request = APIRequest(
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            path=request.url.path,
            query_params=dict(request.query_params),
            headers=dict(request.headers),
            user_agent=request.headers.get("user-agent", ""),
            ip_address=ip_masked,
            content_type=request.headers.get("content-type"),
            content_length=request.headers.get("content-length"),
        )

        # Extract user info from headers (if available)
        if "x-user-id" in request.headers:
            api_request.user_id = request.headers["x-user-id"]
        if "x-tenant-id" in request.headers:
            api_request.tenant_id = request.headers["x-tenant-id"]
        if "x-session-id" in request.headers:
            api_request.session_id = request.headers["x-session-id"]

        # Log request start
        self.api_logger.log_request_start(api_request)

        try:
            # Process request
            response = await call_next(request)

            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000

            # Create response object
            api_response = APIResponse(
                request_id=request_id,
                status_code=response.status_code,
                content_type=response.headers.get("content-type"),
                content_length=response.headers.get("content-length"),
                response_time_ms=response_time_ms,
            )

            # Log request end
            self.api_logger.log_request_end(api_response)

            return response

        except Exception as e:
            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000

            # Create error response
            api_response = APIResponse(
                request_id=request_id,
                status_code=500,
                response_time_ms=response_time_ms,
                error_message=str(e),
                error_traceback=traceback.format_exc(),
            )

            # Log request end with error
            self.api_logger.log_request_end(api_response)

            # Re-raise the exception
            raise


# Built-in security rules
def detect_suspicious_user_agent(request: APIRequest) -> Optional[SecurityEvent]:
    """Detect suspicious user agents."""
    suspicious_patterns = [
        "bot",
        "crawler",
        "spider",
        "scraper",
        "curl",
        "wget",
        "python",
        "java",
        "node",
        "ruby",
        "php",
    ]

    user_agent_lower = request.user_agent.lower()

    # Check for missing user agent
    if not user_agent_lower or user_agent_lower == "":
        return SecurityEvent(
            event_id=str(uuid.uuid4()),
            request_id=request.request_id,
            event_type="missing_user_agent",
            severity="medium",
            description="Request missing user agent",
            ip_address=request.ip_address,
            user_agent=request.user_agent,
            details={"pattern": "empty_user_agent"},
        )

    # Check for suspicious patterns
    for pattern in suspicious_patterns:
        if pattern in user_agent_lower:
            return SecurityEvent(
                event_id=str(uuid.uuid4()),
                request_id=request.request_id,
                event_type="suspicious_user_agent",
                severity="low",
                description=f"Suspicious user agent detected: {pattern}",
                ip_address=request.ip_address,
                user_agent=request.user_agent,
                details={"pattern": pattern, "user_agent": request.user_agent},
            )

    return None


def detect_rapid_requests(request: APIRequest) -> Optional[SecurityEvent]:
    """Detect rapid successive requests from same IP."""
    # This would need to be implemented with a request tracker
    # For now, just a placeholder
    return None


def detect_unusual_endpoints(request: APIRequest) -> Optional[SecurityEvent]:
    """Detect requests to unusual or sensitive endpoints."""
    sensitive_patterns = [
        "/admin",
        "/debug",
        "/config",
        "/system",
        "/internal",
        "/health",
        "/metrics",
        "/logs",
        "/dump",
    ]

    for pattern in sensitive_patterns:
        if pattern in request.path.lower():
            return SecurityEvent(
                event_id=str(uuid.uuid4()),
                request_id=request.request_id,
                event_type="sensitive_endpoint_access",
                severity="medium",
                description=f"Access to sensitive endpoint: {pattern}",
                ip_address=request.ip_address,
                user_agent=request.user_agent,
                details={"endpoint": request.path, "pattern": pattern},
            )

    return None


# Global instance
api_logger = APILogger()

# Add built-in security rules
api_logger.add_security_rule(detect_suspicious_user_agent)
api_logger.add_security_rule(detect_rapid_requests)
api_logger.add_security_rule(detect_unusual_endpoints)
