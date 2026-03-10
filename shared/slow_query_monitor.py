"""Slow query monitoring for database performance.

Tracks queries that exceed a threshold and logs them for analysis.
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import Any

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
                }
            )
            incr("db.query.slow", {"threshold": str(threshold)})
        
        # Record query count
        incr("db.query.count")


def set_slow_query_threshold(seconds: float) -> None:
    """Set the slow query threshold globally."""
    global SLOW_QUERY_THRESHOLD_SECONDS
    SLOW_QUERY_THRESHOLD_SECONDS = seconds
