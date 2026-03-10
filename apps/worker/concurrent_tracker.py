"""Concurrent usage tracking for the FormAgent.

This module provides tracking of concurrent agent usage to prevent
overloading of resources and maintain system stability.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Dict, Optional, Set

from shared.logging_config import get_logger

logger = get_logger("sorce.concurrent_tracker")


@dataclass
class ConcurrentUsageStats:
    """Statistics for concurrent usage tracking."""

    total_active: int = 0
    active_by_tenant: Dict[str, int] = None
    peak_usage: int = 0
    peak_timestamp: float = 0.0

    def __post_init__(self):
        if self.active_by_tenant is None:
            self.active_by_tenant = {}


class ConcurrentUsageTracker:
    """Tracks concurrent usage of the FormAgent."""

    def __init__(self, max_concurrent: int = 10, max_per_tenant: int = 3):
        self.max_concurrent = max_concurrent
        self.max_per_tenant = max_per_tenant
        self._active_tasks: Set[str] = set()
        self._tenant_usage: Dict[str, int] = {}
        self._task_tenant_map: Dict[str, str] = {}
        self._stats = ConcurrentUsageStats()
        self._lock = asyncio.Lock()

    async def can_start_task(
        self, task_id: Optional[str] = None, tenant_id: Optional[str] = None
    ) -> bool:
        """Check if a task can start based on concurrent usage limits.
        
        Args:
            task_id: Optional task ID (for logging)
            tenant_id: Tenant ID to check limits for
            
        Returns:
            True if task can start, False if limits reached
        """
        async with self._lock:
            # Check global limit
            if len(self._active_tasks) >= self.max_concurrent:
                logger.warning(
                    "Global concurrent limit reached: %d/%d",
                    len(self._active_tasks),
                    self.max_concurrent,
                )
                return False

            # Check tenant-specific limit
            if tenant_id:
                current_tenant_usage = self._tenant_usage.get(tenant_id, 0)
                if current_tenant_usage >= self.max_per_tenant:
                    logger.warning(
                        "Tenant %s concurrent limit reached: %d/%d",
                        tenant_id,
                        current_tenant_usage,
                        self.max_per_tenant,
                    )
                    return False

            return True

    async def start_task(self, task_id: str, tenant_id: Optional[str] = None) -> bool:
        """Start tracking a task."""
        async with self._lock:
            if not await self.can_start_task(task_id, tenant_id):
                return False

            # Add task to active set
            self._active_tasks.add(task_id)

            # Update tenant usage
            if tenant_id:
                self._tenant_usage[tenant_id] = self._tenant_usage.get(tenant_id, 0) + 1
                self._task_tenant_map[task_id] = tenant_id

            # Update stats
            self._stats.total_active = len(self._active_tasks)
            self._stats.active_by_tenant = self._tenant_usage.copy()

            if self._stats.total_active > self._stats.peak_usage:
                self._stats.peak_usage = self._stats.total_active
                self._stats.peak_timestamp = time.time()

            logger.info(
                "Started task %s for tenant %s. Active: %d/%d (tenant: %d/%d)",
                task_id,
                tenant_id or "none",
                self._stats.total_active,
                self.max_concurrent,
                self._tenant_usage.get(tenant_id or "none", 0),
                self.max_per_tenant,
            )

            return True

    async def end_task(self, task_id: str) -> None:
        """End tracking a task."""
        async with self._lock:
            if task_id not in self._active_tasks:
                logger.warning("Task %s not found in active tasks", task_id)
                return

            # Remove task from active set
            self._active_tasks.remove(task_id)

            # Update tenant usage
            tenant_id = self._task_tenant_map.pop(task_id, None)
            if tenant_id and tenant_id in self._tenant_usage:
                self._tenant_usage[tenant_id] -= 1
                if self._tenant_usage[tenant_id] <= 0:
                    del self._tenant_usage[tenant_id]

            # Update stats
            self._stats.total_active = len(self._active_tasks)
            self._stats.active_by_tenant = self._tenant_usage.copy()

            logger.info(
                "Ended task %s for tenant %s. Active: %d/%d (tenant: %d/%d)",
                task_id,
                tenant_id or "none",
                self._stats.total_active,
                self.max_concurrent,
                self._tenant_usage.get(tenant_id or "none", 0),
                self.max_per_tenant,
            )

    async def get_stats(self) -> ConcurrentUsageStats:
        """Get current usage statistics."""
        async with self._lock:
            return ConcurrentUsageStats(
                total_active=self._stats.total_active,
                active_by_tenant=self._stats.active_by_tenant.copy(),
                peak_usage=self._stats.peak_usage,
                peak_timestamp=self._stats.peak_timestamp,
            )

    async def get_active_tasks(self) -> Set[str]:
        """Get set of currently active task IDs."""
        async with self._lock:
            return self._active_tasks.copy()

    async def get_tenant_usage(self) -> Dict[str, int]:
        """Get current usage by tenant."""
        async with self._lock:
            return self._tenant_usage.copy()

    async def reset_stats(self) -> None:
        """Reset peak usage statistics."""
        async with self._lock:
            self._stats.peak_usage = self._stats.total_active
            self._stats.peak_timestamp = time.time()
            logger.info("Reset concurrent usage peak stats")


# Global instance
_concurrent_tracker: Optional[ConcurrentUsageTracker] = None


def get_concurrent_tracker() -> ConcurrentUsageTracker:
    """Get or create the global concurrent usage tracker."""
    global _concurrent_tracker
    if _concurrent_tracker is None:
        from shared.config import get_settings

        settings = get_settings()
        _concurrent_tracker = ConcurrentUsageTracker(
            max_concurrent=getattr(settings, "max_concurrent_applications", 10),
            max_per_tenant=getattr(settings, "max_concurrent_per_tenant", 3),
        )
    return _concurrent_tracker
