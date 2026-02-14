"""
Calendar Integration API endpoints — interview scheduling and calendar sync.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.domain.calendar import (
    CalendarProvider,
    GoogleCalendarClient,
    OutlookCalendarClient,
    InterviewEvent,
    CalendarEvent,
    detect_conflicts,
    schedule_interview,
)
from shared.logging_config import get_logger

logger = get_logger("sorce.api.calendar")

router = APIRouter(prefix="/calendar", tags=["calendar"])


def _get_pool():
    raise NotImplementedError("Pool dependency not injected")


async def _get_user_id() -> str:
    raise NotImplementedError("User ID dependency not injected")


async def _get_tenant_id() -> str:
    raise NotImplementedError("Tenant ID dependency not injected")


class CreateEventRequest(BaseModel):
    title: str
    description: str | None = None
    start_time: str
    end_time: str
    location: str | None = None
    attendees: list[str] = []
    timezone: str = "America/Los_Angeles"
    reminder_minutes: int = 30
    conference_url: str | None = None
    provider: str = "google"


class CreateEventResponse(BaseModel):
    success: bool
    event_id: str | None = None
    html_link: str | None = None
    conference_url: str | None = None
    error: str | None = None


class ListEventsResponse(BaseModel):
    events: list[dict[str, Any]]


class ConflictCheckRequest(BaseModel):
    start_time: str
    end_time: str
    provider: str = "google"


class ConflictCheckResponse(BaseModel):
    has_conflicts: bool
    conflicts: list[dict[str, Any]]


@router.post("/events", response_model=CreateEventResponse)
async def create_calendar_event(
    body: CreateEventRequest,
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_user_id),
    tenant_id: str = Depends(_get_tenant_id),
) -> CreateEventResponse:
    async with db.acquire() as conn:
        integration = await conn.fetchrow(
            """
            SELECT access_token, provider
            FROM public.calendar_integrations
            WHERE tenant_id = $1 AND user_id = $2 AND is_active = true
            """,
            tenant_id,
            user_id,
        )

    if not integration:
        raise HTTPException(
            status_code=404,
            detail="Calendar not connected. Please connect your calendar first.",
        )

    try:
        start_time = datetime.fromisoformat(body.start_time.replace("Z", "+00:00"))
        end_time = datetime.fromisoformat(body.end_time.replace("Z", "+00:00"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")

    event = InterviewEvent(
        title=body.title,
        description=body.description,
        start_time=start_time,
        end_time=end_time,
        location=body.location,
        attendees=body.attendees,
        timezone=body.timezone,
        reminder_minutes=body.reminder_minutes,
        conference_url=body.conference_url,
    )

    try:
        provider = CalendarProvider(body.provider.lower())
    except ValueError:
        provider = CalendarProvider.GOOGLE

    result = await schedule_interview(
        event=event,
        provider=provider,
        access_token=integration["access_token"],
    )

    return CreateEventResponse(
        success=result.get("success", False),
        event_id=result.get("event_id"),
        html_link=result.get("html_link"),
        conference_url=result.get("conference_url"),
        error=result.get("error"),
    )


@router.get("/events", response_model=ListEventsResponse)
async def list_calendar_events(
    days_ahead: int = 7,
    days_back: int = 0,
    provider: str = "google",
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_user_id),
    tenant_id: str = Depends(_get_tenant_id),
) -> ListEventsResponse:
    async with db.acquire() as conn:
        integration = await conn.fetchrow(
            """
            SELECT access_token
            FROM public.calendar_integrations
            WHERE tenant_id = $1 AND user_id = $2 AND is_active = true
            """,
            tenant_id,
            user_id,
        )

    if not integration:
        raise HTTPException(
            status_code=404,
            detail="Calendar not connected",
        )

    now = datetime.utcnow()
    time_min = now - timedelta(days=days_back)
    time_max = now + timedelta(days=days_ahead)

    try:
        cal_provider = CalendarProvider(provider.lower())
    except ValueError:
        cal_provider = CalendarProvider.GOOGLE

    if cal_provider == CalendarProvider.GOOGLE:
        client = GoogleCalendarClient(integration["access_token"])
        events = await client.list_events(time_min, time_max)
    elif cal_provider == CalendarProvider.OUTLOOK:
        client = OutlookCalendarClient(integration["access_token"])
        events = await client.list_events(time_min, time_max)
    else:
        events = []

    return ListEventsResponse(
        events=[
            {
                "id": e.id,
                "title": e.title,
                "start_time": e.start_time.isoformat(),
                "end_time": e.end_time.isoformat(),
                "location": e.location,
                "description": e.description,
                "attendees": e.attendees,
                "provider": e.provider.value,
            }
            for e in events
        ]
    )


@router.post("/conflicts", response_model=ConflictCheckResponse)
async def check_calendar_conflicts(
    body: ConflictCheckRequest,
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_user_id),
    tenant_id: str = Depends(_get_tenant_id),
) -> ConflictCheckResponse:
    async with db.acquire() as conn:
        integration = await conn.fetchrow(
            """
            SELECT access_token
            FROM public.calendar_integrations
            WHERE tenant_id = $1 AND user_id = $2 AND is_active = true
            """,
            tenant_id,
            user_id,
        )

    if not integration:
        return ConflictCheckResponse(has_conflicts=False, conflicts=[])

    try:
        start_time = datetime.fromisoformat(body.start_time.replace("Z", "+00:00"))
        end_time = datetime.fromisoformat(body.end_time.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    now = datetime.utcnow()
    time_min = now - timedelta(days=1)
    time_max = now + timedelta(days=30)

    try:
        provider = CalendarProvider(body.provider.lower())
    except ValueError:
        provider = CalendarProvider.GOOGLE

    if provider == CalendarProvider.GOOGLE:
        client = GoogleCalendarClient(integration["access_token"])
        existing_events = await client.list_events(time_min, time_max)
    elif provider == CalendarProvider.OUTLOOK:
        client = OutlookCalendarClient(integration["access_token"])
        existing_events = await client.list_events(time_min, time_max)
    else:
        existing_events = []

    new_event = InterviewEvent(
        title="Conflict Check",
        start_time=start_time,
        end_time=end_time,
    )

    conflicts = detect_conflicts(new_event, existing_events)

    return ConflictCheckResponse(
        has_conflicts=len(conflicts) > 0,
        conflicts=[
            {
                "id": c.id,
                "title": c.title,
                "start_time": c.start_time.isoformat(),
                "end_time": c.end_time.isoformat(),
            }
            for c in conflicts
        ],
    )


@router.delete("/events/{event_id}")
async def delete_calendar_event(
    event_id: str,
    provider: str = "google",
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_user_id),
    tenant_id: str = Depends(_get_tenant_id),
) -> dict[str, str]:
    async with db.acquire() as conn:
        integration = await conn.fetchrow(
            """
            SELECT access_token
            FROM public.calendar_integrations
            WHERE tenant_id = $1 AND user_id = $2 AND is_active = true
            """,
            tenant_id,
            user_id,
        )

    if not integration:
        raise HTTPException(status_code=404, detail="Calendar not connected")

    try:
        cal_provider = CalendarProvider(provider.lower())
    except ValueError:
        cal_provider = CalendarProvider.GOOGLE

    if cal_provider == CalendarProvider.GOOGLE:
        client = GoogleCalendarClient(integration["access_token"])
        success = await client.delete_event(event_id)
    else:
        raise HTTPException(
            status_code=400, detail="Provider not supported for deletion"
        )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete event")

    return {"status": "deleted"}


@router.post("/connect")
async def connect_calendar(
    provider: str,
    access_token: str,
    refresh_token: str | None = None,
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_user_id),
    tenant_id: str = Depends(_get_tenant_id),
) -> dict[str, str]:
    async with db.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO public.calendar_integrations
                (tenant_id, user_id, provider, access_token, refresh_token, is_active)
            VALUES ($1, $2, $3, $4, $5, true)
            ON CONFLICT (tenant_id, user_id, provider) DO UPDATE SET
                access_token = $4,
                refresh_token = COALESCE($5, calendar_integrations.refresh_token),
                is_active = true,
                updated_at = now()
            """,
            tenant_id,
            user_id,
            provider,
            access_token,
            refresh_token,
        )

    return {"status": "connected"}


@router.delete("/disconnect")
async def disconnect_calendar(
    provider: str = "google",
    db: asyncpg.Pool = Depends(_get_pool),
    user_id: str = Depends(_get_user_id),
    tenant_id: str = Depends(_get_tenant_id),
) -> dict[str, str]:
    async with db.acquire() as conn:
        await conn.execute(
            """
            UPDATE public.calendar_integrations
            SET is_active = false
            WHERE tenant_id = $1 AND user_id = $2 AND provider = $3
            """,
            tenant_id,
            user_id,
            provider,
        )

    return {"status": "disconnected"}
