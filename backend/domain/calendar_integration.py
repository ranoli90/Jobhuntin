"""Calendar integration service for interview scheduling.

Provides:
- Google Calendar integration
- Outlook/Microsoft Calendar integration
- iCal export
- Interview scheduling and reminders
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum

logger = logging.getLogger(__name__)


class CalendarProvider(StrEnum):
    """Supported calendar providers."""

    GOOGLE = "google"
    OUTLOOK = "outlook"
    APPLE = "apple"
    ICAL = "ical"


@dataclass
class InterviewEvent:
    """An interview event to be added to calendar."""

    title: str
    start_time: datetime
    end_time: datetime
    location: str
    description: str
    attendees: list[str] = field(default_factory=list)
    timezone: str = "UTC"
    conference_url: str | None = None
    reminder_minutes: list[int] = field(default_factory=lambda: [15, 60])

    def to_ical(self) -> str:
        """Generate iCal format string."""
        dt_start = self.start_time.strftime("%Y%m%dT%H%M%SZ")
        dt_end = self.end_time.strftime("%Y%m%dT%H%M%SZ")
        dt_stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        uid = str(uuid.uuid4())

        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Sorce//Interview Scheduler//EN",
            "BEGIN:VEVENT",
            f"UID:{uid}@sorce.ai",
            f"DTSTAMP:{dt_stamp}",
            f"DTSTART:{dt_start}",
            f"DTEND:{dt_end}",
            f"SUMMARY:{self.title}",
            f"LOCATION:{self.location}",
            f"DESCRIPTION:{self.description}",
        ]

        if self.conference_url:
            lines.append(f"URL:{self.conference_url}")

        for reminder in self.reminder_minutes:
            lines.extend(
                [
                    "BEGIN:VALARM",
                    "ACTION:DISPLAY",
                    f"DESCRIPTION:Reminder: {self.title}",
                    f"TRIGGER:-PT{reminder}M",
                    "END:VALARM",
                ]
            )

        lines.extend(
            [
                "END:VEVENT",
                "END:VCALENDAR",
            ]
        )

        return "\r\n".join(lines)


@dataclass
class CalendarAuth:
    """Calendar authentication credentials."""

    provider: CalendarProvider
    access_token: str | None = None
    refresh_token: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    tenant_id: str | None = None  # For Microsoft


class CalendarService:
    """Calendar integration service.

    Supports:
    - Google Calendar API
    - Microsoft Graph API (Outlook)
    - iCal export
    """

    def __init__(self, auth: CalendarAuth | None = None):
        self.auth = auth

    async def create_event(
        self,
        event: InterviewEvent,
        provider: CalendarProvider | None = None,
    ) -> str:
        """Create a calendar event.

        Args:
            event: Interview event details
            provider: Calendar provider (uses auth provider if not specified)

        Returns:
            Event ID or iCal content

        """
        provider = provider or (
            self.auth.provider if self.auth else CalendarProvider.ICAL
        )

        if provider == CalendarProvider.GOOGLE:
            return await self._create_google_event(event)
        elif provider == CalendarProvider.OUTLOOK:
            return await self._create_outlook_event(event)
        else:
            return event.to_ical()

    async def _create_google_event(self, event: InterviewEvent) -> str:
        """Create event in Google Calendar."""
        if not self.auth or not self.auth.access_token:
            raise ValueError("Google Calendar requires authentication")

        import httpx

        event_body = {
            "summary": event.title,
            "location": event.location,
            "description": event.description,
            "start": {
                "dateTime": event.start_time.isoformat(),
                "timeZone": event.timezone,
            },
            "end": {
                "dateTime": event.end_time.isoformat(),
                "timeZone": event.timezone,
            },
            "attendees": [{"email": email} for email in event.attendees],
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": minutes}
                    for minutes in event.reminder_minutes
                ],
            },
        }

        if event.conference_url:
            event_body["conferenceData"] = {
                "createRequest": {
                    "requestId": str(uuid.uuid4()),
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                },
            }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                json=event_body,
                headers={
                    "Authorization": f"Bearer {self.auth.access_token}",
                    "Content-Type": "application/json",
                },
                params={"conferenceDataVersion": "1"} if event.conference_url else {},
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("id", "")
            else:
                logger.error(f"Google Calendar API error: {response.text}")
                raise Exception(
                    f"Failed to create Google Calendar event: {response.status_code}"
                )

    async def _create_outlook_event(self, event: InterviewEvent) -> str:
        """Create event in Microsoft Outlook."""
        if not self.auth or not self.auth.access_token:
            raise ValueError("Outlook requires authentication")

        import httpx

        event_body = {
            "subject": event.title,
            "body": {
                "contentType": "HTML",
                "content": event.description,
            },
            "start": {
                "dateTime": event.start_time.isoformat(),
                "timeZone": event.timezone,
            },
            "end": {
                "dateTime": event.end_time.isoformat(),
                "timeZone": event.timezone,
            },
            "location": {
                "displayName": event.location,
            },
            "attendees": [
                {
                    "emailAddress": {"address": email},
                    "type": "required",
                }
                for email in event.attendees
            ],
            "isOnlineMeeting": bool(event.conference_url),
        }

        headers = {
            "Authorization": f"Bearer {self.auth.access_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://graph.microsoft.com/v1.0/me/events",
                json=event_body,
                headers=headers,
            )

            if response.status_code == 201:
                data = response.json()
                return data.get("id", "")
            else:
                logger.error(f"Microsoft Graph API error: {response.text}")
                raise Exception(
                    f"Failed to create Outlook event: {response.status_code}"
                )

    async def get_free_busy(
        self,
        start_time: datetime,
        end_time: datetime,
        provider: CalendarProvider | None = None,
    ) -> list[dict]:
        """Get free/busy times from calendar.

        Returns list of busy periods with start and end times.
        """
        provider = provider or (self.auth.provider if self.auth else None)

        if provider == CalendarProvider.GOOGLE:
            return await self._get_google_free_busy(start_time, end_time)
        elif provider == CalendarProvider.OUTLOOK:
            return await self._get_outlook_free_busy(start_time, end_time)

        return []

    async def _get_google_free_busy(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> list[dict]:
        """Get free/busy from Google Calendar."""
        if not self.auth or not self.auth.access_token:
            return []

        import httpx

        body = {
            "timeMin": start_time.isoformat() + "Z",
            "timeMax": end_time.isoformat() + "Z",
            "items": [{"id": "primary"}],
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://www.googleapis.com/calendar/v3/freeBusy",
                json=body,
                headers={
                    "Authorization": f"Bearer {self.auth.access_token}",
                    "Content-Type": "application/json",
                },
            )

            if response.status_code == 200:
                data = response.json()
                busy = []
                for calendar in data.get("calendars", {}).values():
                    for period in calendar.get("busy", []):
                        busy.append(
                            {
                                "start": datetime.fromisoformat(
                                    period["start"].replace("Z", "+00:00")
                                ),
                                "end": datetime.fromisoformat(
                                    period["end"].replace("Z", "+00:00")
                                ),
                            }
                        )
                return busy

        return []

    async def _get_outlook_free_busy(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> list[dict]:
        """Get free/busy from Outlook."""
        if not self.auth or not self.auth.access_token:
            return []

        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://graph.microsoft.com/v1.0/me/calendar/getSchedule",
                json={
                    "schedules": ["/me"],
                    "startTime": {
                        "dateTime": start_time.isoformat(),
                        "timeZone": "UTC",
                    },
                    "endTime": {
                        "dateTime": end_time.isoformat(),
                        "timeZone": "UTC",
                    },
                    "availabilityViewInterval": 30,
                },
                headers={
                    "Authorization": f"Bearer {self.auth.access_token}",
                    "Content-Type": "application/json",
                    "Prefer": 'outlook.timezone="UTC"',
                },
            )

            if response.status_code == 200:
                data = response.json()
                busy = []
                for schedule in data.get("value", []):
                    for item in schedule.get("scheduleItems", []):
                        busy.append(
                            {
                                "start": datetime.fromisoformat(
                                    item["start"]["dateTime"].replace("Z", "+00:00")
                                ),
                                "end": datetime.fromisoformat(
                                    item["end"]["dateTime"].replace("Z", "+00:00")
                                ),
                            }
                        )
                return busy

        return []

    def generate_ical_download(self, event: InterviewEvent) -> tuple[str, str]:
        """Generate iCal content for download.

        Returns:
            Tuple of (content, filename)

        """
        content = event.to_ical()
        filename = f"interview_{event.start_time.strftime('%Y%m%d')}.ics"
        return content, filename


async def create_interview_event(
    title: str,
    start_time: datetime,
    duration_minutes: int = 60,
    location: str = "",
    description: str = "",
    conference_url: str | None = None,
    attendees: list[str] | None = None,
    provider: CalendarProvider = CalendarProvider.ICAL,
    auth: CalendarAuth | None = None,
) -> str:
    """Convenience function to create an interview event.

    Args:
        title: Interview title
        start_time: Interview start time
        duration_minutes: Interview duration
        location: Interview location
        description: Interview description
        conference_url: Video conference URL
        attendees: List of attendee emails
        provider: Calendar provider
        auth: Calendar authentication

    Returns:
        Event ID or iCal content

    """
    event = InterviewEvent(
        title=title,
        start_time=start_time,
        end_time=start_time + timedelta(minutes=duration_minutes),
        location=location,
        description=description,
        conference_url=conference_url,
        attendees=attendees or [],
    )

    service = CalendarService(auth)
    return await service.create_event(event, provider)


def get_google_oauth_url(
    client_id: str,
    redirect_uri: str,
    state: str = "",
) -> str:
    """Generate Google OAuth URL for calendar access."""
    scopes = [
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/calendar.events",
    ]

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes),
        "access_type": "offline",
        "prompt": "consent",
    }

    if state:
        params["state"] = state

    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"


def get_microsoft_oauth_url(
    client_id: str,
    redirect_uri: str,
    tenant_id: str = "common",
    state: str = "",
) -> str:
    """Generate Microsoft OAuth URL for calendar access."""
    scopes = [
        "offline_access",
        "Calendars.ReadWrite",
        "Calendars.Read",
    ]

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes),
        "response_mode": "query",
    }

    if state:
        params["state"] = state

    query = "&".join(f"{k}={v}" for k, v in params.items())
    return (
        f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize?{query}"
    )


async def refresh_google_token(
    refresh_token: str,
    client_id: str,
    client_secret: str,
) -> dict:
    """Refresh Google OAuth access token.

    Args:
        refresh_token: Google refresh token
        client_id: Google OAuth client ID
        client_secret: Google OAuth client secret

    Returns:
        Dict with new access_token and optionally refresh_token

    Raises:
        Exception: If token refresh fails

    """
    import httpx

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "access_token": data.get("access_token"),
                "expires_in": data.get("expires_in", 3600),
                "token_type": data.get("token_type", "Bearer"),
                # Google rarely returns new refresh_token, keep the old one
            }
        else:
            logger.error(f"Google token refresh failed: {response.text}")
            raise Exception(f"Failed to refresh Google token: {response.status_code}")


async def refresh_microsoft_token(
    refresh_token: str,
    client_id: str,
    client_secret: str,
    tenant_id: str = "common",
) -> dict:
    """Refresh Microsoft OAuth access token.

    Args:
        refresh_token: Microsoft refresh token
        client_id: Microsoft OAuth client ID
        client_secret: Microsoft OAuth client secret
        tenant_id: Microsoft tenant ID

    Returns:
        Dict with new access_token and optionally refresh_token

    Raises:
        Exception: If token refresh fails

    """
    import httpx

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
                "scope": "offline_access Calendars.ReadWrite Calendars.Read",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "access_token": data.get("access_token"),
                "refresh_token": data.get("refresh_token", refresh_token),
                "expires_in": data.get("expires_in", 3600),
                "token_type": data.get("token_type", "Bearer"),
            }
        else:
            logger.error(f"Microsoft token refresh failed: {response.text}")
            raise Exception(
                f"Failed to refresh Microsoft token: {response.status_code}"
            )


async def ensure_valid_token(
    auth: CalendarAuth,
    token_expires_at: datetime | None = None,
) -> CalendarAuth:
    """Ensure the calendar auth has a valid access token, refreshing if necessary.

    Args:
        auth: Current calendar authentication
        token_expires_at: When the current token expires (if known)

    Returns:
        Updated CalendarAuth with valid access_token

    Raises:
        ValueError: If refresh is not possible (missing refresh_token or credentials)

    """
    # If no expiration info, assume token is valid for 1 hour from now
    if token_expires_at is None:
        token_expires_at = datetime.utcnow() + timedelta(hours=1)

    # If token is still valid for at least 5 minutes, return as-is
    if datetime.utcnow() < token_expires_at - timedelta(minutes=5):
        return auth

    # Need to refresh
    if not auth.refresh_token:
        raise ValueError("Token expired and no refresh_token available")

    if auth.provider == CalendarProvider.GOOGLE:
        if not auth.client_id:
            raise ValueError("Google refresh requires client_id")
        # Note: client_secret should be fetched from secure storage in production
        tokens = await refresh_google_token(
            refresh_token=auth.refresh_token,
            client_id=auth.client_id,
            client_secret=auth.client_secret or "",
        )
        return CalendarAuth(
            provider=auth.provider,
            access_token=tokens["access_token"],
            refresh_token=tokens.get("refresh_token", auth.refresh_token),
            client_id=auth.client_id,
            client_secret=auth.client_secret,
            tenant_id=auth.tenant_id,
        )

    elif auth.provider == CalendarProvider.OUTLOOK:
        if not auth.client_id:
            raise ValueError("Microsoft refresh requires client_id")
        tokens = await refresh_microsoft_token(
            refresh_token=auth.refresh_token,
            client_id=auth.client_id,
            client_secret=auth.client_secret or "",
            tenant_id=auth.tenant_id or "common",
        )
        return CalendarAuth(
            provider=auth.provider,
            access_token=tokens["access_token"],
            refresh_token=tokens.get("refresh_token", auth.refresh_token),
            client_id=auth.client_id,
            client_secret=auth.client_secret,
            tenant_id=auth.tenant_id,
        )

    raise ValueError(f"Token refresh not supported for provider: {auth.provider}")
