"""
Monitoring Service

Persistent monitoring service with database integration for API metrics,
security events, and analytics data storage.
"""

import asyncio
import json
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from shared.api_logger import (
    APILogger,
    APIRequest,
    APIResponse,
    MetricsCollector,
    PerformanceMetrics,
    SecurityEvent,
)
from shared.logging_config import get_logger

logger = get_logger("sorce.monitoring_service")


class DatabaseMetricsCollector(MetricsCollector):
    """Extended metrics collector with database persistence."""

    def __init__(self, retention_hours: int = 24, db_pool=None):
        super().__init__(retention_hours)
        self.db_pool = db_pool
        self._batch_size = 100
        self._flush_interval = 60  # seconds
        self._pending_requests: List[Dict[str, Any]] = []
        self._pending_metrics: List[Dict[str, Any]] = []
        self._pending_security_events: List[Dict[str, Any]] = []
        self._flush_task: Optional[asyncio.Task] = None

    def start_database_flushing(self) -> None:
        """Start background database flushing task."""
        if self._flush_task is None:
            self._flush_task = asyncio.create_task(self._periodic_flush())

    async def _periodic_flush(self) -> None:
        """Periodically flush pending data to database."""
        while True:
            try:
                await asyncio.sleep(self._flush_interval)
                await self._flush_to_database()
            except Exception as e:
                logger.error(f"Database flush error: {e}")
                await asyncio.sleep(30)  # Retry sooner on error

    async def _flush_to_database(self) -> None:
        """Flush all pending data to database."""
        if not self.db_pool:
            return

        try:
            async with self.db_pool.acquire() as conn:
                # Flush request logs
                if self._pending_requests:
                    await self._flush_requests(conn)

                # Flush performance metrics
                if self._pending_metrics:
                    await self._flush_metrics(conn)

                # Flush security events
                if self._pending_security_events:
                    await self._flush_security_events(conn)

        except Exception as e:
            logger.error(f"Database flush failed: {e}")

    async def _flush_requests(self, conn) -> None:
        """Flush pending request logs to database."""
        if not self._pending_requests:
            return

        batch = self._pending_requests[: self._batch_size]
        self._pending_requests = self._pending_requests[self._batch_size :]

        query = """
        INSERT INTO api_request_logs (
            request_id, method, url, path, query_params, headers,
            user_agent, ip_address, user_id, tenant_id, session_id,
            content_type, content_length, status_code, response_time_ms,
            error_message, error_traceback, timestamp
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18
        )
        """

        await conn.executemany(
            query,
            [
                (
                    req["request_id"],
                    req["method"],
                    req["url"],
                    req["path"],
                    json.dumps(req["query_params"]) if req["query_params"] else None,
                    json.dumps(req["headers"]) if req["headers"] else None,
                    req["user_agent"],
                    req["ip_address"],
                    req.get("user_id"),
                    req.get("tenant_id"),
                    req.get("session_id"),
                    req.get("content_type"),
                    req.get("content_length"),
                    req.get("status_code"),
                    req.get("response_time_ms"),
                    req.get("error_message"),
                    req.get("error_traceback"),
                    req["timestamp"],
                )
                for req in batch
            ],
        )

        logger.info(f"Flushed {len(batch)} request logs to database")

    async def _flush_metrics(self, conn) -> None:
        """Flush pending performance metrics to database."""
        if not self._pending_metrics:
            return

        batch = self._pending_metrics[: self._batch_size]
        self._pending_metrics = self._pending_metrics[self._batch_size :]

        query = """
        INSERT INTO api_performance_metrics (
            request_id, endpoint, method, response_time_ms, db_query_time_ms,
            cache_lookup_time_ms, auth_time_ms, validation_time_ms,
            memory_usage_mb, cpu_usage_percent, timestamp
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
        )
        """

        await conn.executemany(
            query,
            [
                (
                    metric["request_id"],
                    metric["endpoint"],
                    metric["method"],
                    metric["response_time_ms"],
                    metric.get("db_query_time_ms", 0.0),
                    metric.get("cache_lookup_time_ms", 0.0),
                    metric.get("auth_time_ms", 0.0),
                    metric.get("validation_time_ms", 0.0),
                    metric.get("memory_usage_mb", 0.0),
                    metric.get("cpu_usage_percent", 0.0),
                    metric["timestamp"],
                )
                for metric in batch
            ],
        )

        logger.info(f"Flushed {len(batch)} performance metrics to database")

    async def _flush_security_events(self, conn) -> None:
        """Flush pending security events to database."""
        if not self._pending_security_events:
            return

        batch = self._pending_security_events[: self._batch_size]
        self._pending_security_events = self._pending_security_events[
            self._batch_size :
        ]

        query = """
        INSERT INTO api_security_events (
            event_id, request_id, event_type, severity, description,
            ip_address, user_agent, user_id, details, timestamp
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10
        )
        """

        await conn.executemany(
            query,
            [
                (
                    event["event_id"],
                    event["request_id"],
                    event["event_type"],
                    event["severity"],
                    event["description"],
                    event["ip_address"],
                    event["user_agent"],
                    event.get("user_id"),
                    json.dumps(event["details"]) if event["details"] else None,
                    event["timestamp"],
                )
                for event in batch
            ],
        )

        logger.info(f"Flushed {len(batch)} security events to database")

    def record_request_start(self, request: APIRequest) -> None:
        """Record request start with database queuing."""
        super().record_request_start(request)

        # Queue for database insertion
        self._pending_requests.append(asdict(request))

    def record_request_end(self, response: APIResponse) -> None:
        """Record request end with database queuing."""
        super().record_request_end(response)

        # Queue for database insertion
        self._pending_requests.append(asdict(response))

    def record_security_event(self, event: SecurityEvent) -> None:
        """Record security event with database queuing."""
        super().record_security_event(event)

        # Queue for database insertion
        self._pending_security_events.append(asdict(event))

    def record_performance_metrics(self, metrics: PerformanceMetrics) -> None:
        """Record performance metrics with database queuing."""
        super().record_performance_metrics(metrics)

        # Queue for database insertion
        self._pending_metrics.append(asdict(metrics))

    async def get_database_metrics(
        self,
        hours: int = 24,
        endpoint: Optional[str] = None,
        status_code: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get metrics from database."""
        if not self.db_pool:
            return {}

        try:
            async with self.db_pool.acquire() as conn:
                # Get request statistics
                where_clauses = ["timestamp >= NOW() - INTERVAL '%s hours'" % hours]
                params = []

                if endpoint:
                    where_clauses.append("path = $%s" % (len(params) + 1))
                    params.append(endpoint)

                if status_code:
                    where_clauses.append("status_code = $%s" % (len(params) + 1))
                    params.append(status_code)

                where_clause = " AND ".join(where_clauses)

                # Basic statistics
                stats_query = f"""
                SELECT
                    COUNT(*) as total_requests,
                    COUNT(*) FILTER (WHERE status_code < 400) as successful_requests,
                    COUNT(*) FILTER (WHERE status_code >= 400) as failed_requests,
                    AVG(response_time_ms) as avg_response_time_ms,
                    MIN(response_time_ms) as min_response_time_ms,
                    MAX(response_time_ms) as max_response_time_ms,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(DISTINCT ip_address) as unique_ips
                FROM api_request_logs
                WHERE {where_clause}
                """

                stats = await conn.fetchrow(stats_query, *params)

                # Error distribution
                error_query = f"""
                SELECT status_code, COUNT(*) as count
                FROM api_request_logs
                WHERE {where_clause} AND status_code >= 400
                GROUP BY status_code
                ORDER BY count DESC
                """

                errors = await conn.fetch(error_query, *params)

                # Top endpoints
                if not endpoint:
                    endpoint_query = f"""
                    SELECT path, method, COUNT(*) as request_count,
                           AVG(response_time_ms) as avg_response_time,
                           COUNT(*) FILTER (WHERE status_code >= 400) as error_count
                    FROM api_request_logs
                    WHERE {where_clause}
                    GROUP BY path, method
                    ORDER BY request_count DESC
                    LIMIT 10
                    """

                    top_endpoints = await conn.fetch(endpoint_query, *params)
                else:
                    top_endpoints = []

                return {
                    "total_requests": int(stats["total_requests"]),
                    "successful_requests": int(stats["successful_requests"]),
                    "failed_requests": int(stats["failed_requests"]),
                    "avg_response_time_ms": float(stats["avg_response_time_ms"] or 0),
                    "min_response_time_ms": float(stats["min_response_time_ms"] or 0),
                    "max_response_time_ms": float(stats["max_response_time_ms"] or 0),
                    "unique_users": int(stats["unique_users"]),
                    "unique_ips": int(stats["unique_ips"]),
                    "error_distribution": [
                        {"status_code": row["status_code"], "count": int(row["count"])}
                        for row in errors
                    ],
                    "top_endpoints": [
                        {
                            "path": row["path"],
                            "method": row["method"],
                            "request_count": int(row["request_count"]),
                            "avg_response_time": float(row["avg_response_time"] or 0),
                            "error_count": int(row["error_count"]),
                        }
                        for row in top_endpoints
                    ],
                }

        except Exception as e:
            logger.error(f"Failed to get database metrics: {e}")
            return {}

    async def get_security_events_db(
        self,
        hours: int = 24,
        severity: Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get security events from database."""
        if not self.db_pool:
            return []

        try:
            async with self.db_pool.acquire() as conn:
                where_clauses = ["timestamp >= NOW() - INTERVAL '%s hours'" % hours]
                params = []

                if severity:
                    where_clauses.append("severity = $%s" % (len(params) + 1))
                    params.append(severity)

                if event_type:
                    where_clauses.append("event_type = $%s" % (len(params) + 1))
                    params.append(event_type)

                where_clause = " AND ".join(where_clauses)

                query = f"""
                SELECT
                    event_id, request_id, event_type, severity, description,
                    ip_address, user_agent, user_id, details, timestamp,
                    resolved, resolved_by, resolved_at
                FROM api_security_events
                WHERE {where_clause}
                ORDER BY timestamp DESC
                LIMIT 1000
                """

                rows = await conn.fetch(query, *params)

                return [
                    {
                        "event_id": row["event_id"],
                        "request_id": row["request_id"],
                        "event_type": row["event_type"],
                        "severity": row["severity"],
                        "description": row["description"],
                        "ip_address": str(row["ip_address"]),
                        "user_agent": row["user_agent"],
                        "user_id": str(row["user_id"]) if row["user_id"] else None,
                        "details": json.loads(row["details"])
                        if row["details"]
                        else None,
                        "timestamp": row["timestamp"].isoformat(),
                        "resolved": row["resolved"],
                        "resolved_by": str(row["resolved_by"])
                        if row["resolved_by"]
                        else None,
                        "resolved_at": row["resolved_at"].isoformat()
                        if row["resolved_at"]
                        else None,
                    }
                    for row in rows
                ]

        except Exception as e:
            logger.error(f"Failed to get security events from database: {e}")
            return []

    async def get_daily_metrics_db(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get daily metrics from database."""
        if not self.db_pool:
            return []

        try:
            async with self.db_pool.acquire() as conn:
                query = (
                    """
                SELECT
                    date, total_requests, successful_requests, failed_requests,
                    avg_response_time_ms, min_response_time_ms, max_response_time_ms,
                    unique_users, unique_ips, top_endpoints, error_distribution,
                    security_events_count
                FROM api_daily_metrics
                WHERE date >= CURRENT_DATE - INTERVAL '%s days'
                ORDER BY date DESC
                """
                    % days
                )

                rows = await conn.fetch(query)

                return [
                    {
                        "date": row["date"].isoformat(),
                        "total_requests": int(row["total_requests"]),
                        "successful_requests": int(row["successful_requests"]),
                        "failed_requests": int(row["failed_requests"]),
                        "avg_response_time_ms": float(row["avg_response_time_ms"] or 0),
                        "min_response_time_ms": float(row["min_response_time_ms"] or 0),
                        "max_response_time_ms": float(row["max_response_time_ms"] or 0),
                        "unique_users": int(row["unique_users"]),
                        "unique_ips": int(row["unique_ips"]),
                        "top_endpoints": json.loads(row["top_endpoints"])
                        if row["top_endpoints"]
                        else {},
                        "error_distribution": json.loads(row["error_distribution"])
                        if row["error_distribution"]
                        else {},
                        "security_events_count": int(row["security_events_count"]),
                    }
                    for row in rows
                ]

        except Exception as e:
            logger.error(f"Failed to get daily metrics from database: {e}")
            return []


class MonitoringService:
    """High-level monitoring service with database integration."""

    def __init__(self, db_pool=None):
        self.metrics_collector = DatabaseMetricsCollector(db_pool=db_pool)
        self.api_logger = APILogger()
        self.api_logger.metrics_collector = self.metrics_collector
        self.db_pool = db_pool
        self._alert_thresholds = {
            "error_rate_warning": 0.05,
            "error_rate_critical": 0.10,
            "response_time_warning": 1000.0,
            "response_time_critical": 5000.0,
            "security_events_warning": 50,
            "security_events_critical": 100,
        }

    async def start(self) -> None:
        """Start the monitoring service."""
        self.metrics_collector.start_database_flushing()
        self.api_logger.start_monitoring()
        logger.info("Monitoring service started")

    async def stop(self) -> None:
        """Stop the monitoring service."""
        if self.metrics_collector._flush_task:
            self.metrics_collector._flush_task.cancel()

        # Flush any remaining data
        await self.metrics_collector._flush_to_database()

        logger.info("Monitoring service stopped")

    async def get_comprehensive_metrics(
        self, hours: int = 24, include_database: bool = True
    ) -> Dict[str, Any]:
        """Get comprehensive metrics from memory and database."""
        # Get in-memory metrics
        memory_metrics = self.api_logger.get_metrics()

        if include_database and self.db_pool:
            # Get database metrics
            db_metrics = await self.metrics_collector.get_database_metrics(hours)

            # Merge metrics
            return {
                "performance": db_metrics,
                "endpoints": memory_metrics["endpoints"],
                "errors": memory_metrics["errors"],
                "security": memory_metrics["security"],
                "active_requests": memory_metrics["active_requests"],
                "period_hours": hours,
                "timestamp": datetime.utcnow().isoformat(),
            }

        return memory_metrics

    async def get_security_dashboard(self, hours: int = 24) -> Dict[str, Any]:
        """Get security-focused dashboard data."""
        # Get security events from database
        security_events = await self.metrics_collector.get_security_events_db(hours)

        # Analyze security patterns
        event_counts = {}
        severity_counts = {}
        ip_counts = {}

        for event in security_events:
            event_type = event["event_type"]
            severity = event["severity"]
            ip_address = event["ip_address"]

            event_counts[event_type] = event_counts.get(event_type, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            ip_counts[ip_address] = ip_counts.get(ip_address, 0) + 1

        # Get top suspicious IPs
        top_suspicious_ips = sorted(
            ip_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]

        # Calculate security score
        security_score = 100
        total_events = len(security_events)

        if total_events > self._alert_thresholds["security_events_critical"]:
            security_score -= 40
        elif total_events > self._alert_thresholds["security_events_warning"]:
            security_score -= 20

        if severity_counts.get("critical", 0) > 0:
            security_score -= 30
        elif severity_counts.get("high", 0) > 5:
            security_score -= 15

        security_score = max(0, security_score)

        return {
            "security_score": security_score,
            "total_events": total_events,
            "event_counts": event_counts,
            "severity_counts": severity_counts,
            "top_suspicious_ips": top_suspicious_ips,
            "recent_events": security_events[:50],  # Last 50 events
            "period_hours": hours,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def check_alert_conditions(self) -> List[Dict[str, Any]]:
        """Check for alert conditions and return active alerts."""
        alerts = []

        # Get recent metrics
        metrics = await self.get_comprehensive_metrics(hours=1)
        performance = metrics["performance"]

        # Check error rate
        error_rate = performance.get("error_rate", 0)
        if error_rate > self._alert_thresholds["error_rate_critical"]:
            alerts.append(
                {
                    "type": "error_rate",
                    "severity": "critical",
                    "message": f"Critical error rate: {error_rate:.2%}",
                    "current_value": error_rate,
                    "threshold": self._alert_thresholds["error_rate_critical"],
                }
            )
        elif error_rate > self._alert_thresholds["error_rate_warning"]:
            alerts.append(
                {
                    "type": "error_rate",
                    "severity": "warning",
                    "message": f"High error rate: {error_rate:.2%}",
                    "current_value": error_rate,
                    "threshold": self._alert_thresholds["error_rate_warning"],
                }
            )

        # Check response time
        avg_response_time = performance.get("avg_response_time", 0)
        if avg_response_time > self._alert_thresholds["response_time_critical"]:
            alerts.append(
                {
                    "type": "response_time",
                    "severity": "critical",
                    "message": f"Critical response time: {avg_response_time:.2f}ms",
                    "current_value": avg_response_time,
                    "threshold": self._alert_thresholds["response_time_critical"],
                }
            )
        elif avg_response_time > self._alert_thresholds["response_time_warning"]:
            alerts.append(
                {
                    "type": "response_time",
                    "severity": "warning",
                    "message": f"Slow response time: {avg_response_time:.2f}ms",
                    "current_value": avg_response_time,
                    "threshold": self._alert_thresholds["response_time_warning"],
                }
            )

        # Check security events
        security_events = metrics.get("security", [])
        if len(security_events) > self._alert_thresholds["security_events_critical"]:
            alerts.append(
                {
                    "type": "security_events",
                    "severity": "critical",
                    "message": f"Critical number of security events: {len(security_events)}",
                    "current_value": len(security_events),
                    "threshold": self._alert_thresholds["security_events_critical"],
                }
            )
        elif len(security_events) > self._alert_thresholds["security_events_warning"]:
            alerts.append(
                {
                    "type": "security_events",
                    "severity": "warning",
                    "message": f"High number of security events: {len(security_events)}",
                    "current_value": len(security_events),
                    "threshold": self._alert_thresholds["security_events_warning"],
                }
            )

        return alerts

    async def record_system_health(self, health_data: Dict[str, Any]) -> None:
        """Record system health metrics."""
        if not self.db_pool:
            return

        try:
            async with self.db_pool.acquire() as conn:
                query = """
                INSERT INTO api_system_health (
                    cpu_usage_percent, memory_usage_percent, disk_usage_percent,
                    active_connections, database_connections, cache_hit_rate,
                    error_rate, health_score, alerts
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """

                await conn.execute(
                    query,
                    health_data.get("cpu_usage_percent"),
                    health_data.get("memory_usage_percent"),
                    health_data.get("disk_usage_percent"),
                    health_data.get("active_connections"),
                    health_data.get("database_connections"),
                    health_data.get("cache_hit_rate"),
                    health_data.get("error_rate", 0.0),
                    health_data.get("health_score", 100),
                    json.dumps(health_data.get("alerts", [])),
                )

        except Exception as e:
            logger.error(f"Failed to record system health: {e}")

    async def get_health_trends(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get system health trends."""
        if not self.db_pool:
            return []

        try:
            async with self.db_pool.acquire() as conn:
                query = (
                    """
                SELECT
                    timestamp, cpu_usage_percent, memory_usage_percent,
                    disk_usage_percent, active_connections, database_connections,
                    cache_hit_rate, error_rate, health_score, alerts
                FROM api_system_health
                WHERE timestamp >= NOW() - INTERVAL '%s hours'
                ORDER BY timestamp DESC
                """
                    % hours
                )

                rows = await conn.fetch(query)

                return [
                    {
                        "timestamp": row["timestamp"].isoformat(),
                        "cpu_usage_percent": float(row["cpu_usage_percent"])
                        if row["cpu_usage_percent"]
                        else None,
                        "memory_usage_percent": float(row["memory_usage_percent"])
                        if row["memory_usage_percent"]
                        else None,
                        "disk_usage_percent": float(row["disk_usage_percent"])
                        if row["disk_usage_percent"]
                        else None,
                        "active_connections": int(row["active_connections"])
                        if row["active_connections"]
                        else None,
                        "database_connections": int(row["database_connections"])
                        if row["database_connections"]
                        else None,
                        "cache_hit_rate": float(row["cache_hit_rate"])
                        if row["cache_hit_rate"]
                        else None,
                        "error_rate": float(row["error_rate"]),
                        "health_score": int(row["health_score"]),
                        "alerts": json.loads(row["alerts"]) if row["alerts"] else [],
                    }
                    for row in rows
                ]

        except Exception as e:
            logger.error(f"Failed to get health trends: {e}")
            return []


# Global instance
monitoring_service = MonitoringService()
