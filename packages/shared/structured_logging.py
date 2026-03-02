"""Structured Logging for Observability.

Provides comprehensive observability metrics:
- Success rate per endpoint/operation
- Latency percentiles (p50, p95, p99)
- Error rates by category
- Prometheus-compatible export format
- Integration with existing metrics.py
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from shared.logging_config import get_logger

logger = get_logger("sorce.structured_logging")


@dataclass
class LatencyBucket:
    count: int = 0
    total_ms: float = 0.0
    min_ms: float = float("inf")
    max_ms: float = 0.0
    values: list[float] = field(default_factory=list)


@dataclass
class EndpointMetrics:
    requests_total: int = 0
    requests_success: int = 0
    requests_error: int = 0
    latency: LatencyBucket = field(default_factory=LatencyBucket)
    errors_by_code: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    last_request_time: float | None = None


class StructuredMetrics:
    """Thread-safe structured metrics collection for observability.

    Tracks:
    - Request counts (total, success, error) per endpoint
    - Latency distributions with percentile calculation
    - Error categorization and rates
    - Operation-level metrics

    Prometheus-compatible output format.
    """

    def __init__(self, max_latency_samples: int = 1000) -> None:
        self._lock = threading.Lock()
        self._max_latency_samples = max_latency_samples
        self._endpoints: dict[str, EndpointMetrics] = defaultdict(EndpointMetrics)
        self._operations: dict[str, EndpointMetrics] = defaultdict(EndpointMetrics)
        self._start_time = time.time()

    def record_request(
        self,
        endpoint: str,
        status_code: int,
        latency_ms: float,
        error_category: str | None = None,
        tenant_id: str | None = None,
    ) -> None:
        """Record a request to an endpoint.

        Args:
            endpoint: API endpoint path (e.g., "/api/jobs")
            status_code: HTTP status code
            latency_ms: Request latency in milliseconds
            error_category: Optional error category (e.g., "validation", "auth", "db")
            tenant_id: Optional tenant ID for multi-tenant tracking

        """
        with self._lock:
            metrics = self._endpoints[endpoint]
            metrics.requests_total += 1
            metrics.last_request_time = time.time()

            if 200 <= status_code < 400:
                metrics.requests_success += 1
            else:
                metrics.requests_error += 1
                error_key = error_category or f"http_{status_code}"
                metrics.errors_by_code[error_key] += 1

            self._record_latency(metrics, latency_ms)

    def record_operation(
        self,
        operation: str,
        success: bool,
        latency_ms: float,
        error_category: str | None = None,
        tenant_id: str | None = None,
    ) -> None:
        """Record an internal operation (e.g., "db_query", "llm_call").

        Args:
            operation: Operation name
            success: Whether operation succeeded
            latency_ms: Operation latency in milliseconds
            error_category: Optional error category
            tenant_id: Optional tenant ID

        """
        with self._lock:
            metrics = self._operations[operation]
            metrics.requests_total += 1
            metrics.last_request_time = time.time()

            if success:
                metrics.requests_success += 1
            else:
                metrics.requests_error += 1
                error_key = error_category or "unknown"
                metrics.errors_by_code[error_key] += 1

            self._record_latency(metrics, latency_ms)

    def _record_latency(self, metrics: EndpointMetrics, latency_ms: float) -> None:
        metrics.latency.count += 1
        metrics.latency.total_ms += latency_ms
        metrics.latency.min_ms = min(metrics.latency.min_ms, latency_ms)
        metrics.latency.max_ms = max(metrics.latency.max_ms, latency_ms)
        metrics.latency.values.append(latency_ms)

        if len(metrics.latency.values) > self._max_latency_samples:
            metrics.latency.values = metrics.latency.values[
                -self._max_latency_samples // 2 :
            ]

    def get_endpoint_metrics(self, endpoint: str) -> dict[str, Any] | None:
        with self._lock:
            if endpoint not in self._endpoints:
                return None

            metrics = self._endpoints[endpoint]
            return self._format_metrics(metrics)

    def get_operation_metrics(self, operation: str) -> dict[str, Any] | None:
        with self._lock:
            if operation not in self._operations:
                return None

            metrics = self._operations[operation]
            return self._format_metrics(metrics)

    def _format_metrics(self, metrics: EndpointMetrics) -> dict[str, Any]:
        success_rate = (
            metrics.requests_success / metrics.requests_total * 100
            if metrics.requests_total > 0
            else 0.0
        )

        avg_latency = (
            metrics.latency.total_ms / metrics.latency.count
            if metrics.latency.count > 0
            else 0.0
        )

        percentiles = self._calculate_percentiles(metrics.latency.values)

        return {
            "requests_total": metrics.requests_total,
            "requests_success": metrics.requests_success,
            "requests_error": metrics.requests_error,
            "success_rate_pct": round(success_rate, 2),
            "latency_avg_ms": round(avg_latency, 2),
            "latency_min_ms": round(metrics.latency.min_ms, 2)
            if metrics.latency.min_ms != float("inf")
            else 0,
            "latency_max_ms": round(metrics.latency.max_ms, 2),
            "latency_p50_ms": round(percentiles["p50"], 2),
            "latency_p95_ms": round(percentiles["p95"], 2),
            "latency_p99_ms": round(percentiles["p99"], 2),
            "errors_by_category": dict(metrics.errors_by_code),
            "last_request_time": metrics.last_request_time,
        }

    def _calculate_percentiles(self, values: list[float]) -> dict[str, float]:
        if not values:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0}

        sorted_values = sorted(values)
        n = len(sorted_values)

        def percentile(p: float) -> float:
            idx = int(n * p / 100)
            idx = min(idx, n - 1)
            return sorted_values[idx]

        return {
            "p50": percentile(50),
            "p95": percentile(95),
            "p99": percentile(99),
        }

    def get_all_metrics(self) -> dict[str, Any]:
        """Get all collected metrics."""
        with self._lock:
            uptime_seconds = time.time() - self._start_time

            endpoints = {}
            for endpoint, metrics in self._endpoints.items():
                endpoints[endpoint] = self._format_metrics(metrics)

            operations = {}
            for operation, metrics in self._operations.items():
                operations[operation] = self._format_metrics(metrics)

            return {
                "uptime_seconds": round(uptime_seconds, 2),
                "collection_timestamp": datetime.now(UTC).isoformat(),
                "endpoints": endpoints,
                "operations": operations,
                "summary": self._get_summary(),
            }

    def _get_summary(self) -> dict[str, Any]:
        total_requests = sum(m.requests_total for m in self._endpoints.values())
        total_success = sum(m.requests_success for m in self._endpoints.values())
        total_errors = sum(m.requests_error for m in self._endpoints.values())

        all_latencies = []
        for metrics in self._endpoints.values():
            all_latencies.extend(metrics.latency.values)

        percentiles = self._calculate_percentiles(all_latencies)

        error_categories: dict[str, int] = defaultdict(int)
        for metrics in self._endpoints.values():
            for category, count in metrics.errors_by_code.items():
                error_categories[category] += count

        return {
            "total_requests": total_requests,
            "total_success": total_success,
            "total_errors": total_errors,
            "overall_success_rate_pct": round(total_success / total_requests * 100, 2)
            if total_requests > 0
            else 0.0,
            "overall_latency_p50_ms": round(percentiles["p50"], 2),
            "overall_latency_p95_ms": round(percentiles["p95"], 2),
            "overall_latency_p99_ms": round(percentiles["p99"], 2),
            "error_categories": dict(error_categories),
        }

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus text format.

        Returns:
            Prometheus-formatted metrics string

        """
        with self._lock:
            lines = []
            lines.append("# HELP sorce_uptime_seconds Total uptime in seconds")
            lines.append("# TYPE sorce_uptime_seconds gauge")
            lines.append(f"sorce_uptime_seconds {time.time() - self._start_time:.2f}")
            lines.append("")

            for endpoint, metrics in self._endpoints.items():
                (
                    endpoint.replace("/", "_").replace("-", "_").strip("_") or "root"
                )

                lines.append(f"# Endpoint: {endpoint}")

                lines.append(
                    f'sorce_requests_total{{endpoint="{endpoint}"}} {metrics.requests_total}'
                )
                lines.append(
                    f'sorce_requests_success{{endpoint="{endpoint}"}} {metrics.requests_success}'
                )
                lines.append(
                    f'sorce_requests_error{{endpoint="{endpoint}"}} {metrics.requests_error}'
                )

                percentiles = self._calculate_percentiles(metrics.latency.values)
                lines.append(
                    f'sorce_latency_p50_ms{{endpoint="{endpoint}"}} {percentiles["p50"]:.2f}'
                )
                lines.append(
                    f'sorce_latency_p95_ms{{endpoint="{endpoint}"}} {percentiles["p95"]:.2f}'
                )
                lines.append(
                    f'sorce_latency_p99_ms{{endpoint="{endpoint}"}} {percentiles["p99"]:.2f}'
                )

                for error_cat, count in metrics.errors_by_code.items():
                    safe_cat = error_cat.replace('"', '\\"')
                    lines.append(
                        f'sorce_errors{{endpoint="{endpoint}",category="{safe_cat}"}} {count}'
                    )

                lines.append("")

            for operation, metrics in self._operations.items():
                operation.replace("-", "_").replace(" ", "_")

                lines.append(f"# Operation: {operation}")
                lines.append(
                    f'sorce_operation_total{{operation="{operation}"}} {metrics.requests_total}'
                )
                lines.append(
                    f'sorce_operation_success{{operation="{operation}"}} {metrics.requests_success}'
                )
                lines.append(
                    f'sorce_operation_error{{operation="{operation}"}} {metrics.requests_error}'
                )

                percentiles = self._calculate_percentiles(metrics.latency.values)
                lines.append(
                    f'sorce_operation_latency_p50_ms{{operation="{operation}"}} {percentiles["p50"]:.2f}'
                )
                lines.append(
                    f'sorce_operation_latency_p95_ms{{operation="{operation}"}} {percentiles["p95"]:.2f}'
                )
                lines.append(
                    f'sorce_operation_latency_p99_ms{{operation="{operation}"}} {percentiles["p99"]:.2f}'
                )

                lines.append("")

            return "\n".join(lines)


_structured_metrics: StructuredMetrics | None = None
_metrics_lock = threading.Lock()


def get_structured_metrics() -> StructuredMetrics:
    """Get or create the singleton StructuredMetrics instance."""
    global _structured_metrics

    with _metrics_lock:
        if _structured_metrics is None:
            _structured_metrics = StructuredMetrics()
        return _structured_metrics


class RequestTimer:
    """Context manager for timing requests and automatically recording metrics."""

    def __init__(
        self,
        endpoint: str,
        tenant_id: str | None = None,
        is_operation: bool = False,
    ) -> None:
        self.endpoint = endpoint
        self.tenant_id = tenant_id
        self.is_operation = is_operation
        self.start_time: float | None = None
        self.status_code = 200
        self.error_category: str | None = None

    def __enter__(self) -> RequestTimer:
        self.start_time = time.monotonic()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.start_time is None:
            return

        latency_ms = (time.monotonic() - self.start_time) * 1000
        metrics = get_structured_metrics()

        if exc_type is not None:
            self.status_code = 500
            self.error_category = self._categorize_exception(exc_type, exc_val)

        if self.is_operation:
            metrics.record_operation(
                operation=self.endpoint,
                success=self.status_code < 400,
                latency_ms=latency_ms,
                error_category=self.error_category,
                tenant_id=self.tenant_id,
            )
        else:
            metrics.record_request(
                endpoint=self.endpoint,
                status_code=self.status_code,
                latency_ms=latency_ms,
                error_category=self.error_category,
                tenant_id=self.tenant_id,
            )

    def set_status(self, status_code: int) -> None:
        self.status_code = status_code

    def set_error_category(self, category: str) -> None:
        self.error_category = category

    def _categorize_exception(self, exc_type: Any, exc_val: Any) -> str:
        exc_name = exc_type.__name__ if hasattr(exc_type, "__name__") else str(exc_type)

        if "validation" in exc_name.lower():
            return "validation"
        elif "auth" in exc_name.lower() or "unauthorized" in exc_name.lower():
            return "auth"
        elif "notfound" in exc_name.lower():
            return "not_found"
        elif "timeout" in exc_name.lower():
            return "timeout"
        elif "database" in exc_name.lower() or "postgres" in exc_name.lower():
            return "database"
        elif "redis" in exc_name.lower():
            return "cache"
        elif "ratelimit" in exc_name.lower():
            return "rate_limit"
        else:
            return "internal"


def timed_request(endpoint: str, tenant_id: str | None = None) -> RequestTimer:
    """Create a context manager for timing API requests."""
    return RequestTimer(endpoint, tenant_id, is_operation=False)


def timed_operation(operation: str, tenant_id: str | None = None) -> RequestTimer:
    """Create a context manager for timing internal operations."""
    return RequestTimer(operation, tenant_id, is_operation=True)
