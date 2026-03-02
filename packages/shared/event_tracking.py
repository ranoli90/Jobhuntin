"""Event tracking for user analytics.

Supports multiple backends:
- Segment
- Mixpanel
- PostHog (self-hosted option)
"""

from __future__ import annotations

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

    def track(
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
        self._buffer.append(event)

        if len(self._buffer) >= self._flush_size:
            self._flush()

        return event

    def _flush(self) -> None:
        """Send buffered events to analytics backends."""
        if not self._buffer:
            return

        events = self._buffer.copy()
        self._buffer = []

        # Send to Segment
        if self.write_key:
            self._send_to_segment(events)

        # Send to Mixpanel
        if self.mixpanel_token:
            self._send_to_mixpanel(events)

        # Send to PostHog
        if self.posthog_key:
            self._send_to_posthog(events)

    def _send_to_segment(self, events: list[Event]) -> None:
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
            httpx.post(
                "https://api.segment.io/v1/batch",
                auth=(self.write_key, ""),
                json=batch,
                timeout=10.0,
            )
        except Exception:
            # Don't fail on analytics errors
            pass

    def _send_to_mixpanel(self, events: list[Event]) -> None:
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
            httpx.post(
                "https://api.mixpanel.com/track",
                headers={"Content-Type": "application/json"},
                json=batch,
                timeout=10.0,
            )
        except Exception:
            pass

    def _send_to_posthog(self, events: list[Event]) -> None:
        """Send events to PostHog."""
        for event in events:
            try:
                httpx.post(
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
                    timeout=10.0,
                )
            except Exception:
                pass


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


def get_tracker() -> EventTracker:
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


def track_event(
    event_name: str,
    user_id: str,
    tenant_id: str | None = None,
    **properties: Any,
) -> Event:
    """Convenience function to track an event."""
    return get_tracker().track(
        event_name=event_name,
        user_id=user_id,
        tenant_id=tenant_id,
        properties=properties,
    )
