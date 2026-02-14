"""
Zapier Integration — connect JobHuntin to 5000+ apps.

Features:
  - Webhook triggers for events
  - Action endpoints for Zapier
  - Zap templates for common workflows
  - Rate limiting per tenant
"""

from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import asyncpg

from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.zapier")


@dataclass
class ZapierHook:
    hook_id: str
    tenant_id: str
    user_id: str
    webhook_url: str
    event_types: list[str]
    is_active: bool = True
    created_at: datetime | None = None
    last_triggered_at: datetime | None = None


@dataclass
class ZapierTrigger:
    trigger_type: str
    display_name: str
    description: str
    sample_data: dict[str, Any]


TRIGGERS: dict[str, ZapierTrigger] = {
    "new_job_match": ZapierTrigger(
        trigger_type="new_job_match",
        display_name="New Job Match",
        description="Triggers when a new job matches your criteria",
        sample_data={
            "job_id": "abc-123",
            "title": "Software Engineer",
            "company": "Acme Corp",
            "location": "San Francisco, CA",
            "salary_min": 120000,
            "salary_max": 180000,
            "match_score": 95,
            "url": "https://jobhuntin.com/jobs/abc-123",
            "posted_at": "2026-02-14T10:00:00Z",
        },
    ),
    "application_submitted": ZapierTrigger(
        trigger_type="application_submitted",
        display_name="Application Submitted",
        description="Triggers when a job application is submitted",
        sample_data={
            "application_id": "app-456",
            "job_title": "Software Engineer",
            "company": "Acme Corp",
            "status": "submitted",
            "submitted_at": "2026-02-14T10:30:00Z",
            "user_id": "user-789",
        },
    ),
    "application_status_changed": ZapierTrigger(
        trigger_type="application_status_changed",
        display_name="Application Status Changed",
        description="Triggers when an application status changes",
        sample_data={
            "application_id": "app-456",
            "job_title": "Software Engineer",
            "company": "Acme Corp",
            "old_status": "submitted",
            "new_status": "interview_scheduled",
            "changed_at": "2026-02-15T14:00:00Z",
        },
    ),
    "interview_scheduled": ZapierTrigger(
        trigger_type="interview_scheduled",
        display_name="Interview Scheduled",
        description="Triggers when an interview is scheduled",
        sample_data={
            "interview_id": "int-123",
            "company": "Acme Corp",
            "job_title": "Software Engineer",
            "scheduled_at": "2026-02-20T10:00:00Z",
            "interview_type": "technical",
            "location": "Video Call",
        },
    ),
    "weekly_summary": ZapierTrigger(
        trigger_type="weekly_summary",
        display_name="Weekly Summary",
        description="Triggers weekly with your job hunt summary",
        sample_data={
            "week_start": "2026-02-08",
            "week_end": "2026-02-14",
            "jobs_matched": 15,
            "applications_submitted": 5,
            "interviews_scheduled": 2,
            "response_rate": 0.4,
        },
    ),
}

ZAP_TEMPLATES = [
    {
        "title": "Save job matches to Google Sheets",
        "description": "Automatically save new job matches to a Google Sheets spreadsheet",
        "trigger": "new_job_match",
        "suggested_action": "google_sheets:create_spreadsheet_row",
    },
    {
        "title": "Create Trello cards for interviews",
        "description": "Create a Trello card when an interview is scheduled",
        "trigger": "interview_scheduled",
        "suggested_action": "trello:create_card",
    },
    {
        "title": "Send Slack notifications for status changes",
        "description": "Get a Slack message when your application status changes",
        "trigger": "application_status_changed",
        "suggested_action": "slack:send_message",
    },
    {
        "title": "Add interviews to Google Calendar",
        "description": "Automatically add scheduled interviews to Google Calendar",
        "trigger": "interview_scheduled",
        "suggested_action": "google_calendar:create_event",
    },
    {
        "title": "Create Notion page for new applications",
        "description": "Create a Notion page to track each new application",
        "trigger": "application_submitted",
        "suggested_action": "notion:create_page",
    },
]


class ZapierIntegrationManager:
    MAX_HOOKS_PER_TENANT = 10

    def __init__(self, db_pool: asyncpg.Pool):
        self._pool = db_pool

    @staticmethod
    def generate_hook_id() -> str:
        return f"zh_{secrets.token_urlsafe(16)}"

    async def subscribe(
        self,
        tenant_id: str,
        user_id: str,
        webhook_url: str,
        event_types: list[str],
    ) -> ZapierHook:
        async with self._pool.acquire() as conn:
            count = await conn.fetchval(
                """
                SELECT COUNT(*)::int FROM public.zapier_hooks
                WHERE tenant_id = $1 AND is_active = true
                """,
                tenant_id,
            )

            if count >= self.MAX_HOOKS_PER_TENANT:
                raise ValueError(
                    f"Maximum {self.MAX_HOOKS_PER_TENANT} hooks per tenant"
                )

            hook_id = self.generate_hook_id()

            await conn.execute(
                """
                INSERT INTO public.zapier_hooks
                    (hook_id, tenant_id, user_id, webhook_url, event_types, is_active)
                VALUES ($1, $2, $3, $4, $5::text[], true)
                """,
                hook_id,
                tenant_id,
                user_id,
                webhook_url,
                event_types,
            )

        incr("zapier.hook_created")
        logger.info("Zapier hook created: hook=%s tenant=%s", hook_id, tenant_id)

        return ZapierHook(
            hook_id=hook_id,
            tenant_id=tenant_id,
            user_id=user_id,
            webhook_url=webhook_url,
            event_types=event_types,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )

    async def unsubscribe(self, hook_id: str) -> bool:
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE public.zapier_hooks
                SET is_active = false
                WHERE hook_id = $1
                """,
                hook_id,
            )

            success = result != "UPDATE 0"
            if success:
                incr("zapier.hook_deleted")

            return success

    async def get_hooks_for_event(
        self,
        tenant_id: str,
        event_type: str,
    ) -> list[ZapierHook]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT hook_id, tenant_id, user_id, webhook_url, event_types,
                       is_active, created_at, last_triggered_at
                FROM public.zapier_hooks
                WHERE tenant_id = $1 AND is_active = true AND $2 = ANY(event_types)
                """,
                tenant_id,
                event_type,
            )

            return [
                ZapierHook(
                    hook_id=r["hook_id"],
                    tenant_id=str(r["tenant_id"]),
                    user_id=str(r["user_id"]),
                    webhook_url=r["webhook_url"],
                    event_types=list(r["event_types"]) if r["event_types"] else [],
                    is_active=r["is_active"],
                    created_at=r["created_at"],
                    last_triggered_at=r["last_triggered_at"],
                )
                for r in rows
            ]

    async def trigger_event(
        self,
        tenant_id: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> int:
        hooks = await self.get_hooks_for_event(tenant_id, event_type)

        if not hooks:
            return 0

        import httpx

        triggered = 0
        async with httpx.AsyncClient(timeout=10) as client:
            for hook in hooks:
                try:
                    response = await client.post(
                        hook.webhook_url,
                        json={
                            "event_type": event_type,
                            "hook_id": hook.hook_id,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "data": payload,
                        },
                    )

                    if response.status_code in (200, 201, 204):
                        triggered += 1
                        await self._update_last_triggered(hook.hook_id)
                    else:
                        logger.warning(
                            "Zapier webhook failed: hook=%s status=%d",
                            hook.hook_id,
                            response.status_code,
                        )
                        incr("zapier.webhook_failed")

                except Exception as e:
                    logger.error(
                        "Zapier webhook error: hook=%s error=%s", hook.hook_id, e
                    )
                    incr("zapier.webhook_error")

        incr("zapier.events_triggered", None, triggered)
        return triggered

    async def _update_last_triggered(self, hook_id: str) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE public.zapier_hooks
                SET last_triggered_at = now()
                WHERE hook_id = $1
                """,
                hook_id,
            )

    async def list_hooks(self, tenant_id: str) -> list[ZapierHook]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT hook_id, tenant_id, user_id, webhook_url, event_types,
                       is_active, created_at, last_triggered_at
                FROM public.zapier_hooks
                WHERE tenant_id = $1
                ORDER BY created_at DESC
                """,
                tenant_id,
            )

            return [
                ZapierHook(
                    hook_id=r["hook_id"],
                    tenant_id=str(r["tenant_id"]),
                    user_id=str(r["user_id"]),
                    webhook_url=r["webhook_url"],
                    event_types=list(r["event_types"]) if r["event_types"] else [],
                    is_active=r["is_active"],
                    created_at=r["created_at"],
                    last_triggered_at=r["last_triggered_at"],
                )
                for r in rows
            ]

    @staticmethod
    def get_available_triggers() -> list[dict[str, Any]]:
        return [
            {
                "trigger_type": t.trigger_type,
                "display_name": t.display_name,
                "description": t.description,
                "sample_data": t.sample_data,
            }
            for t in TRIGGERS.values()
        ]

    @staticmethod
    def get_zap_templates() -> list[dict[str, Any]]:
        return ZAP_TEMPLATES


async def init_zapier_tables(conn: asyncpg.Connection) -> None:
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS public.zapier_hooks (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            hook_id TEXT UNIQUE NOT NULL,
            tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
            webhook_url TEXT NOT NULL,
            event_types TEXT[] NOT NULL DEFAULT '{}',
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            last_triggered_at TIMESTAMPTZ
        );

        CREATE INDEX IF NOT EXISTS idx_zapier_hooks_tenant_id
            ON public.zapier_hooks(tenant_id);

        CREATE INDEX IF NOT EXISTS idx_zapier_hooks_hook_id
            ON public.zapier_hooks(hook_id);
        """
    )
    logger.info("Zapier tables initialized")
