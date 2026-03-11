"""
Concurrent Usage Tracker for Phase 12.1 Agent Improvements
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from shared.logging_config import get_logger

logger = get_logger("sorce.concurrent_tracker")

_concurrent_tracker_lock = threading.Lock()


@dataclass
class ConcurrentUsageStats:
    """Concurrent usage statistics."""

    total_active: int = 0
    max_concurrent: int = 10
    current_concurrent: int = 0
    peak_concurrent: int = 0
    active_sessions: List[str] = field(default_factory=list)
    tenant_stats: Dict[str, Dict[str, int]] = field(default_factory=dict)


@dataclass
class ConcurrentUsageSession:
    """Concurrent usage session tracking."""

    session_id: str
    user_id: str
    tenant_id: str
    start_time: datetime
    application_id: Optional[str] = None
    end_time: Optional[datetime] = None
    status: str = "active"  # active, completed, failed, cancelled
    steps_completed: int = 0
    total_steps: int = 0
    error_count: int = 0
    screenshots_captured: int = 0
    buttons_detected: int = 0
    forms_processed: int = 0
    duration_seconds: Optional[int] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ConcurrentTracker:
    """Concurrent usage tracking system."""

    def __init__(self):
        self._sessions: Dict[str, ConcurrentUsageSession] = {}
        self._stats = ConcurrentUsageStats()
        self._max_concurrent = 10
        self._tenant_stats: Dict[str, Dict[str, int]] = {}

    async def track_session(
        self,
        session_id: str,
        user_id: str,
        tenant_id: str,
        application_id: Optional[str] = None,
        total_steps: int = 0,
    ) -> ConcurrentUsageSession:
        """Track a concurrent usage session."""
        session = ConcurrentUsageSession(
            session_id=session_id,
            user_id=user_id,
            tenant_id=tenant_id,
            application_id=application_id,
            start_time=datetime.now(timezone.utc),
            total_steps=total_steps,
        )

        self._sessions[session_id] = session

        # Update tenant stats
        tenant_stats = self._tenant_stats.get(tenant_id, {})
        tenant_stats["active"] = tenant_stats.get("active", 0) + 1
        self._tenant_stats[tenant_id] = tenant_stats

        # Update global stats
        self._stats.total_active = len(
            [s for s in self._sessions.values() if s.status == "active"]
        )
        self._stats.current_concurrent = self._stats.total_active

        if self._stats.total_active > self._stats.peak_concurrent:
            self._stats.peak_concurrent = self._stats.total_active

        logger.info(f"Tracked concurrent session: {session_id} for user {user_id}")

        return session

    async def complete_session(
        self,
        session_id: str,
        status: str = "completed",
        error_count: int = 0,
    ) -> bool:
        """Complete a concurrent usage session."""
        if session_id not in self._sessions:
            return False

        session = self._sessions[session_id]
        session.status = status
        session.end_time = datetime.now(timezone.utc)
        session.updated_at = datetime.now(timezone.utc)

        # Update tenant stats
        tenant_stats = self._tenant_stats.get(session.tenant_id, {})
        tenant_stats["active"] = max(0, tenant_stats.get("active", 1) - 1)
        self._tenant_stats[session.tenant_id] = tenant_stats

        # Update global stats
        self._stats.total_active = len(
            [s for s in self._sessions.values() if s.status == "active"]
        )
        self._stats.current_concurrent = self._stats.total_active

        logger.info(f"Completed concurrent session: {session_id}")

        return True

    async def fail_session(
        self,
        session_id: str,
        error_count: int = 1,
    ) -> bool:
        """Mark a session as failed."""
        if session_id not in self._sessions:
            return False

        session = self._sessions[session_id]
        session.status = "failed"
        session.error_count += error_count
        session.updated_at = datetime.now(timezone.utc)

        # Update tenant stats
        tenant_stats = self._tenant_stats.get(session.tenant_id, {})
        tenant_stats["active"] = max(0, tenant_stats.get("active", 1) - 1)
        self._tenant_stats[session.tenant_id] = tenant_stats

        # Update global stats
        self._stats.total_active = len(
            [s for s in self._sessions.values() if s.status == "active"]
        )
        self._stats.current_concurrent = self._stats.total_active

        logger.info(f"Failed concurrent session: {session_id}")

        return True

    def get_session(self, session_id: str) -> Optional[ConcurrentUsageSession]:
        """Get session by ID."""
        return self._sessions.get(session_id)

    def get_active_sessions(self) -> List[ConcurrentUsageSession]:
        """Get all active sessions."""
        return [s for s in self._sessions.values() if s.status == "active"]

    def get_stats(self) -> ConcurrentUsageStats:
        """Get concurrent usage statistics."""
        return self._stats  # type: ignore[no-any-return]

    def get_tenant_stats(self, tenant_id: str) -> Dict[str, int]:
        """Get statistics for a specific tenant."""
        return self._tenant_stats.get(tenant_id, {})

    def get_active_tasks(self) -> List[str]:
        """Get list of currently active task IDs."""
        return [s.session_id for s in self._sessions.values() if s.status == "active"]

    async def reset_stats(self) -> None:
        """Reset peak concurrent usage statistics."""
        self._stats.peak_concurrent = self._stats.total_active
        logger.info("Reset peak concurrent usage statistics")

    async def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up old session data."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        old_sessions = [
            session_id
            for session_id, session in self._sessions.items()
            if session.created_at < cutoff_time
        ]

        for session_id in old_sessions:
            del self._sessions[session_id]

        logger.info(f"Cleaned up {len(old_sessions)} old sessions")
        return len(old_sessions)


# Factory function
def get_concurrent_tracker() -> ConcurrentTracker:
    """Get concurrent tracker instance. Thread-safe singleton."""
    with _concurrent_tracker_lock:
        if not hasattr(get_concurrent_tracker, "_instance"):
            get_concurrent_tracker._instance = ConcurrentTracker()  # type: ignore[attr-defined]
        return get_concurrent_tracker._instance  # type: ignore[no-any-return, attr-defined]
