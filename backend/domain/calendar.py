"""Calendar Integration — interview scheduling and calendar sync.

Provides:
- Google Calendar integration
- Outlook/Microsoft Calendar integration
- Interview scheduling with invites
- Calendar conflict detection
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

import httpx
from pydantic import BaseModel

from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.calendar")


class CalendarProvider(StrEnum):
    GOOGLE = "google"
    OUTLOOK = "outlook"
    APPLE = "apple"
    CALDAV = "caldav"


class InterviewEvent(BaseModel):
    title: str
    description: str | None = None
    start_time: datetime
    end_time: datetime
    location: str | None = None
    attendees: list[str] = []
    timezone: str = "America/Los_Angeles"
    reminder_minutes: int = 30
    conference_url: str | None = None


class CalendarEvent(BaseModel):
    id: str
    title: str
    start_time: datetime
    end_time: datetime
    location: str | None = None
    description: str | None = None
    attendees: list[str] = []
    provider: CalendarProvider


class GoogleCalendarClient:
    def __init__(self, access_token: str, refresh_token: str | None = None):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.base_url = "https://www.googleapis.com/calendar/v3"

    async def list_events(
        self,
        time_min: datetime,
        time_max: datetime,
        calendar_id: str = "primary",
    ) -> list[CalendarEvent]:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{self.base_url}/calendars/{calendar_id}/events",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    params={
                        "timeMin": time_min.isoformat(),
                        "timeMax": time_max.isoformat(),
                        "singleEvents": "true",
                        "orderBy": "startTime",
                    },
                )

                if resp.status_code == 200:
                    data = resp.json()
                    events = []
                    for item in data.get("items", []):
                        start = item.get("start", {}).get("dateTime")
                        end = item.get("end", {}).get("dateTime")
                        if start and end:
                            events.append(
                                CalendarEvent(
                                    id=item["id"],
                                    title=item.get("summary", "Untitled"),
                                    start_time=datetime.fromisoformat(
                                        start.replace("Z", "+00:00")
                                    ),
                                    end_time=datetime.fromisoformat(
                                        end.replace("Z", "+00:00")
                                    ),
                                    location=item.get("location"),
                                    description=item.get("description"),
                                    attendees=[
                                        a.get("email")
                                        for a in item.get("attendees", [])
                                    ],
                                    provider=CalendarProvider.GOOGLE,
                                )
                            )
                    incr("calendar.google.events_fetched", value=len(events))
                    return events
                return []
        except Exception as e:
            logger.error("Failed to list Google Calendar events: %s", e)
            return []

    async def create_event(
        self,
        event: InterviewEvent,
        calendar_id: str = "primary",
    ) -> dict[str, Any]:
        event_body = {
            "summary": event.title,
            "description": event.description or "",
            "start": {
                "dateTime": event.start_time.isoformat(),
                "timeZone": event.timezone,
            },
            "end": {
                "dateTime": event.end_time.isoformat(),
                "timeZone": event.timezone,
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": event.reminder_minutes},
                    {"method": "popup", "minutes": 10},
                ],
            },
        }

        if event.location:
            event_body["location"] = event.location

        if event.attendees:
            event_body["attendees"] = [{"email": email} for email in event.attendees]

        if event.conference_url:
            event_body["conferenceData"] = {
                "createRequest": {
                    "requestId": f"sorce-{datetime.now(timezone.utc).timestamp()}",
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"{self.base_url}/calendars/{calendar_id}/events",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json",
                    },
                    params=(
                        {"conferenceDataVersion": "1"} if event.conference_url else {}
                    ),
                    json=event_body,
                )

                if resp.status_code in (200, 201):
                    data = resp.json()
                    incr("calendar.google.event_created")
                    return {
                        "success": True,
                        "event_id": data["id"],
                        "html_link": data.get("htmlLink"),
                        "conference_url": data.get("conferenceData", {})
                        .get("entryPoints", [{}])[0]
                        .get("uri"),
                    }
                return {"success": False, "error": resp.text[:200]}
        except Exception as e:
            logger.error("Failed to create Google Calendar event: %s", e)
            return {"success": False, "error": str(e)}

    async def delete_event(
        self,
        event_id: str,
        calendar_id: str = "primary",
    ) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.delete(
                    f"{self.base_url}/calendars/{calendar_id}/events/{event_id}",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                )
                if resp.status_code in (200, 204):
                    incr("calendar.google.event_deleted")
                    return True
                return False
        except Exception as e:
            logger.error("Failed to delete Google Calendar event: %s", e)
            return False


class OutlookCalendarClient:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://graph.microsoft.com/v1.0"

    async def list_events(
        self,
        time_min: datetime,
        time_max: datetime,
    ) -> list[CalendarEvent]:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{self.base_url}/me/calendarView",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    params={
                        "startDateTime": time_min.isoformat(),
                        "endDateTime": time_max.isoformat(),
                        "$orderby": "start/dateTime",
                    },
                )

                if resp.status_code == 200:
                    data = resp.json()
                    events = []
                    for item in data.get("value", []):
                        start = item.get("start", {}).get("dateTime")
                        end = item.get("end", {}).get("dateTime")
                        if start and end:
                            events.append(
                                CalendarEvent(
                                    id=item["id"],
                                    title=item.get("subject", "Untitled"),
                                    start_time=datetime.fromisoformat(
                                        start.replace("Z", "+00:00")
                                    ),
                                    end_time=datetime.fromisoformat(
                                        end.replace("Z", "+00:00")
                                    ),
                                    location=item.get("location", {}).get(
                                        "displayName"
                                    ),
                                    description=item.get("bodyPreview"),
                                    attendees=[
                                        a.get("emailAddress", {}).get("address")
                                        for a in item.get("attendees", [])
                                    ],
                                    provider=CalendarProvider.OUTLOOK,
                                )
                            )
                    incr("calendar.outlook.events_fetched", value=len(events))
                    return events
                return []
        except Exception as e:
            logger.error("Failed to list Outlook events: %s", e)
            return []

    async def create_event(
        self,
        event: InterviewEvent,
    ) -> dict[str, Any]:
        event_body = {
            "subject": event.title,
            "body": {
                "contentType": "HTML",
                "content": event.description or "",
            },
            "start": {
                "dateTime": event.start_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "timeZone": event.timezone,
            },
            "end": {
                "dateTime": event.end_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "timeZone": event.timezone,
            },
            "isOnlineMeeting": bool(event.conference_url),
        }

        if event.location:
            event_body["location"] = {"displayName": event.location}

        if event.attendees:
            event_body["attendees"] = [
                {"emailAddress": {"address": email}, "type": "required"}
                for email in event.attendees
            ]

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"{self.base_url}/me/events",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json",
                    },
                    json=event_body,
                )

                if resp.status_code in (200, 201):
                    data = resp.json()
                    incr("calendar.outlook.event_created")
                    return {
                        "success": True,
                        "event_id": data["id"],
                        "online_meeting_url": data.get("onlineMeeting", {}).get(
                            "joinUrl"
                        ),
                    }
                return {"success": False, "error": resp.text[:200]}
        except Exception as e:
            logger.error("Failed to create Outlook event: %s", e)
            return {"success": False, "error": str(e)}


def detect_conflicts(
    new_event: InterviewEvent,
    existing_events: list[CalendarEvent],
) -> list[CalendarEvent]:
    conflicts = []
    for existing in existing_events:
        if (
            new_event.start_time < existing.end_time
            and new_event.end_time > existing.start_time
        ):
            conflicts.append(existing)
    return conflicts


async def schedule_interview(
    event: InterviewEvent,
    provider: CalendarProvider,
    access_token: str,
) -> dict[str, Any]:
    if provider == CalendarProvider.GOOGLE:
        client = GoogleCalendarClient(access_token)
        return await client.create_event(event)
    elif provider == CalendarProvider.OUTLOOK:
        client = OutlookCalendarClient(access_token)
        return await client.create_event(event)
    else:
        return {"success": False, "error": f"Unsupported provider: {provider}"}
