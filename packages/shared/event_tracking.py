"""Event tracking for user analytics.

Supports multiple backends:
- Segment
- Mixpanel
- PostHog (self-hosted option)
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx


@dataclass
class Event:
    """Analytics event."""

    name: str
    user_id: str
    tenant_id: str | None
    timestamp: datetime
    properties: dict[str, Any]
    context: dict[str, Any] | None = None


class EventTracker:
    """Track and send events to analytics backends."""

    def __init__(
        self,
        write_key: str | None = None,
        mixpanel_token: str | None = None,
        posthog_key: str | None = None,
        posthog_host: str = "https://app.posthog.com",
    ):
        self.write_key = write_key
        self.mixpanel_token = mixpanel_token
        self.posthog_key = posthog_key
        self.posthog_host = posthog_host
        self._buffer: list[Event] = []
        self._flush_size = 100
        self._lock = asyncio.Lock()
        self._http_client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=10.0)
        return self._http_client

    async def track(
        self,
        event_name: str,
        user_id: str,
        tenant_id: str | None = None,
        properties: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> Event:
        """Create and buffer an event."""
        event = Event(
            name=event_name,
            user_id=user_id,
            tenant_id=tenant_id,
            timestamp=datetime.utcnow(),
            properties=properties or {},
            context=context,
        )

        async with self._lock:
            self._buffer.append(event)
            should_flush = len(self._buffer) >= self._flush_size

        if should_flush:
            await self._flush()

        return event

    async def _flush(self) -> None:
        """Send buffered events to analytics backends."""
        async with self._lock:
            if not self._buffer:
                return

            events = self._buffer.copy()
            self._buffer = []

        # Send to backends concurrently
        tasks = []

        if self.write_key:
            tasks.append(self._send_to_segment(events))

        if self.mixpanel_token:
            tasks.append(self._send_to_mixpanel(events))

        if self.posthog_key:
            tasks.append(self._send_to_posthog(events))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_to_segment(self, events: list[Event]) -> None:
        """Send events to Segment."""
        batch = {
            "batch": [
                {
                    "type": "track",
                    "event": e.name,
                    "userId": e.user_id,
                    "timestamp": e.timestamp.isoformat(),
                    "properties": e.properties,
                    "context": e.context or {},
                }
                for e in events
            ]
        }

        try:
            client = await self._get_client()
            await client.post(
                "https://api.segment.io/v1/batch",
                auth=(self.write_key, ""),
                json=batch,
            )
        except Exception:
            # Don't fail on analytics errors
            pass

    async def _send_to_mixpanel(self, events: list[Event]) -> None:
        """Send events to Mixpanel."""
        batch = [
            {
                "event": e.name,
                "properties": {
                    "distinct_id": e.user_id,
                    "time": int(e.timestamp.timestamp()),
                    "token": self.mixpanel_token,
                    **e.properties,
                },
            }
            for e in events
        ]

        try:
            client = await self._get_client()
            await client.post(
                "https://api.mixpanel.com/track",
                headers={"Content-Type": "application/json"},
                json=batch,
            )
        except Exception:
            pass

    async def _send_to_posthog(self, events: list[Event]) -> None:
        """Send events to PostHog."""
        client = await self._get_client()
        for event in events:
            try:
                await client.post(
                    f"{self.posthog_host}/capture/",
                    json={
                        "api_key": self.posthog_key,
                        "event": event.name,
                        "distinct_id": event.user_id,
                        "timestamp": event.timestamp.isoformat(),
                        "properties": {
                            "tenant_id": event.tenant_id,
                            **event.properties,
                        },
                    },
                )
            except Exception:
                pass

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()


# Common event names
class EventName:
    """Standard event names for consistency."""

    # User events
    USER_SIGNED_UP = "User Signed Up"
    USER_LOGGED_IN = "User Logged In"
    USER_LOGGED_OUT = "User Logged Out"
    USER_UPGRADED = "User Upgraded"
    USER_DOWNGRADED = "User Downgraded"

    # Job events
    JOB_VIEWED = "Job Viewed"
    JOB_MATCHED = "Job Matched"
    JOB_APPLIED = "Job Applied"
    JOB_SAVED = "Job Saved"
    JOB_SHARED = "Job Shared"

    # Search events
    SEARCH_PERFORMED = "Search Performed"
    SEARCH_FILTERED = "Search Filtered"

    # AI events
    AI_MATCH_REQUESTED = "AI Match Requested"
    AI_MATCH_COMPLETED = "AI Match Completed"
    AI_MATCH_FAILED = "AI Match Failed"
    AI_FEEDBACK_GIVEN = "AI Feedback Given"

    # Resume events
    RESUME_UPLOADED = "Resume Uploaded"
    RESUME_PARSED = "Resume Parsed"
    RESUME_TAILORED = "Resume Tailored"

    # Engagement events
    NOTIFICATION_OPENED = "Notification Opened"
    EMAIL_OPENED = "Email Opened"
    EMAIL_CLICKED = "Email Clicked"

    # Error events
    ERROR_OCCURRED = "Error Occurred"
    PAYMENT_FAILED = "Payment Failed"


# Global instance
_tracker: EventTracker | None = None


async def get_tracker() -> EventTracker:
    """Get the global event tracker."""
    global _tracker
    if _tracker is None:
        from shared.config import get_settings

        settings = get_settings()
        _tracker = EventTracker(
            write_key=getattr(settings, "segment_write_key", None),
            mixpanel_token=getattr(settings, "mixpanel_token", None),
            posthog_key=getattr(settings, "posthog_key", None),
        )
    return _tracker


async def track_event(
    event_name: str,
    user_id: str,
    tenant_id: str | None = None,
    **properties: Any,
) -> Event:
    """Convenience function to track an event."""
    tracker = await get_tracker()
    return await tracker.track(
        event_name=event_name,
        user_id=user_id,
        tenant_id=tenant_id,
        properties=properties,
    )
