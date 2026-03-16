"""Slow query monitoring for database performance.

Tracks queries that exceed a threshold and logs them for analysis.

Usage:
    # As context manager:
    async with monitor_query("SELECT * FROM users WHERE id = $1") as query_info:
        result = await conn.fetch(query, user_id)

    # As decorator:
    @monitor_query_decorator("SELECT * FROM users")
    async def get_user(conn, user_id):
        return await conn.fetchrow(query, user_id)
"""

from __future__ import annotations

import functools
import time
from contextlib import asynccontextmanager
from typing import Any, Callable, Optional

from shared.logging_config import get_logger
from shared.metrics import incr, observe

logger = get_logger("sorce.slow_queries")

# Default threshold: 1 second
SLOW_QUERY_THRESHOLD_SECONDS = 1.0


@asynccontextmanager
async def monitor_query(query: str, threshold: float = SLOW_QUERY_THRESHOLD_SECONDS):
    """Context manager to monitor query execution time.

    Usage:
        async with monitor_query("SELECT * FROM users WHERE id = $1") as query_info:
            result = await conn.fetch(query, user_id)
            query_info["params"] = [user_id]  # Optional: log parameters
    """
    start_time = time.time()
    query_info: dict[str, Any] = {
        "query": query[:200],  # Truncate long queries
        "params": None,
    }

    try:
        yield query_info
    finally:
        elapsed = time.time() - start_time
        query_info["duration"] = elapsed

        # Record metric
        observe("db.query.duration", elapsed)

        # Log slow queries
        if elapsed > threshold:
            logger.warning(
                "Slow query detected",
                extra={
                    "query": query_info["query"],
                    "duration": elapsed,
                    "threshold": threshold,
                    "params": query_info.get("params"),
                },
            )
            incr("db.query.slow", {"threshold": str(threshold)})

        # Record query count
        incr("db.query.count")


def set_slow_query_threshold(seconds: float) -> None:
    """Set the slow query threshold globally."""
    global SLOW_QUERY_THRESHOLD_SECONDS
    SLOW_QUERY_THRESHOLD_SECONDS = seconds


def monitor_query_decorator(
    query: str,
    threshold: float = SLOW_QUERY_THRESHOLD_SECONDS,
    operation_name: Optional[str] = None,
) -> Callable:
    """Decorator to monitor query execution time.

    Usage:
        @monitor_query_decorator("SELECT * FROM users WHERE id = $1", operation_name="get_user")
        async def get_user(conn, user_id):
            return await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)

    Args:
        query: The SQL query to monitor
        threshold: Slow query threshold in seconds (default: 1.0)
        operation_name: Optional name for the operation (defaults to function name)
    """
    def decorator(func: Callable) -> Callable:
        op_name = operation_name or func.__name__

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            query_info = {
                "query": query[:200],
                "operation": op_name,
                "params": None,
            }

            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                elapsed = time.time() - start_time
                query_info["duration"] = elapsed

                # Record metric
                observe("db.query.duration", elapsed)
                observe(f"db.operation.{op_name}.duration", elapsed)

                # Log slow queries
                if elapsed > threshold:
                    logger.warning(
                        "Slow query detected",
                        extra={
                            "operation": op_name,
                            "query": query_info["query"],
                            "duration": elapsed,
                            "threshold": threshold,
                            "params": query_info.get("params"),
                        },
                    )
                    incr("db.query.slow", {"operation": op_name, "threshold": str(threshold)})

                # Record query count
                incr("db.query.count", {"operation": op_name})

                # Log debug for all queries
                logger.debug(
                    f"Query executed: {op_name}",
                    extra={
                        "operation": op_name,
                        "duration": elapsed,
                        "slow": elapsed > threshold,
                    },
                )

        return wrapper
    return decorator


# Convenience function to wrap a connection fetch operation
async def monitored_fetch(
    conn: Any,
    query: str,
    *args,
    operation_name: Optional[str] = None,
    threshold: float = SLOW_QUERY_THRESHOLD_SECONDS,
    **kwargs,
):
    """Execute a query with monitoring.

    Usage:
        result = await monitored_fetch(
            conn,
            "SELECT * FROM users WHERE id = $1",
            user_id,
            operation_name="get_user"
        )

    Args:
        conn: Database connection
        query: SQL query
        *args: Query parameters
        operation_name: Name for the operation (for metrics)
        threshold: Slow query threshold in seconds
        **kwargs: Additional query options

    Returns:
        Query result
    """
    op_name = operation_name or "unknown"
    start_time = time.time()

    try:
        result = await conn.fetch(query, *args, **kwargs)
        return result
    finally:
        elapsed = time.time() - start_time

        # Record metrics
        observe("db.query.duration", elapsed)
        observe(f"db.operation.{op_name}.duration", elapsed)
        incr("db.query.count", {"operation": op_name})

        # Log slow queries
        if elapsed > threshold:
            logger.warning(
                "Slow query detected",
                extra={
                    "operation": op_name,
                    "query": query[:200],
                    "duration": elapsed,
                    "threshold": threshold,
                },
            )
            incr("db.query.slow", {"operation": op_name, "threshold": str(threshold)})
