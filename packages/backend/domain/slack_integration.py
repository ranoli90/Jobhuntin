"""Slack Integration — notifications and bot interactions.

Features:
  - Slack bot for job notifications
  - Application status alerts
  - Interview reminders
  - Team notifications
  - Interactive commands
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

import asyncpg

from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.slack")


class SlackMessageType(StrEnum):
    JOB_MATCH = "job_match"
    APPLICATION_UPDATE = "application_update"
    INTERVIEW_REMINDER = "interview_reminder"
    WEEKLY_DIGEST = "weekly_digest"
    TEAM_INVITE = "team_invite"
    BILLING_ALERT = "billing_alert"


@dataclass
class SlackMessage:
    channel: str
    message_type: SlackMessageType
    text: str
    blocks: list[dict[str, Any]] = field(default_factory=list)
    attachments: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SlackChannel:
    channel_id: str
    channel_name: str
    is_private: bool = False
    webhook_url: str | None = None


@dataclass
class SlackTeamConfig:
    team_id: str
    tenant_id: str
    access_token: str
    bot_user_id: str | None = None
    default_channel: str | None = None
    enabled_notifications: list[str] = field(default_factory=list)
    is_active: bool = True


MESSAGE_TEMPLATES = {
    "job_match": {
        "text": "🎯 New job match found!",
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "🎯 New Job Match"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": "*Title:*\n{title}"},
                    {"type": "mrkdwn", "text": "*Company:*\n{company}"},
                    {"type": "mrkdwn", "text": "*Location:*\n{location}"},
                    {"type": "mrkdwn", "text": "*Match Score:*\n{score}%"},
                ],
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View Job"},
                        "url": "{job_url}",
                        "action_id": "view_job",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Apply"},
                        "url": "{apply_url}",
                        "action_id": "apply_job",
                        "style": "primary",
                    },
                ],
            },
        ],
    },
    "application_update": {
        "text": "📬 Application status updated",
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "📬 Application Update"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": "*Company:*\n{company}"},
                    {"type": "mrkdwn", "text": "*Position:*\n{title}"},
                    {"type": "mrkdwn", "text": "*Status:*\n{status}"},
                    {"type": "mrkdwn", "text": "*Updated:*\n{updated_at}"},
                ],
            },
        ],
    },
    "interview_reminder": {
        "text": "📅 Upcoming interview reminder",
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "📅 Interview Reminder"},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Your interview with *{company}* is coming up!",
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": "*When:*\n{interview_time}"},
                    {"type": "mrkdwn", "text": "*Duration:*\n{duration} minutes"},
                    {"type": "mrkdwn", "text": "*Type:*\n{interview_type}"},
                    {"type": "mrkdwn", "text": "*Location:*\n{location}"},
                ],
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Add to Calendar"},
                        "url": "{calendar_url}",
                        "action_id": "add_calendar",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Prepare"},
                        "url": "{prep_url}",
                        "action_id": "prepare",
                    },
                ],
            },
        ],
    },
    "weekly_digest": {
        "text": "📊 Your weekly job hunt summary",
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "📊 Weekly Digest"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": "*Jobs Matched:*\n{jobs_matched}"},
                    {
                        "type": "mrkdwn",
                        "text": "*Applications Sent:*\n{applications_sent}",
                    },
                    {"type": "mrkdwn", "text": "*Interviews Scheduled:*\n{interviews}"},
                    {"type": "mrkdwn", "text": "*Response Rate:*\n{response_rate}%"},
                ],
            },
        ],
    },
    "team_invite": {
        "text": "👋 You've been invited to join a team",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*{inviter_name}* has invited you to join *{team_name}* on JobHuntin!",
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Accept"},
                        "url": "{accept_url}",
                        "action_id": "accept_invite",
                        "style": "primary",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Decline"},
                        "url": "{decline_url}",
                        "action_id": "decline_invite",
                    },
                ],
            },
        ],
    },
}


class SlackClient:
    API_BASE = "https://slack.com/api"

    def __init__(self, access_token: str):
        self.access_token = access_token

    async def post_message(
        self,
        channel: str,
        text: str,
        blocks: list[dict[str, Any]] | None = None,
        attachments: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        import httpx

        payload = {
            "channel": channel,
            "text": text,
        }
        if blocks:
            payload["blocks"] = blocks
        if attachments:
            payload["attachments"] = attachments

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{self.API_BASE}/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

            data = response.json()
            if not data.get("ok"):
                logger.error("Slack API error: %s", data.get("error"))
                incr("slack.api_error")
                raise Exception(f"Slack API error: {data.get('error')}")

            incr("slack.message_sent")
            return data

    async def post_webhook(
        self,
        webhook_url: str,
        message: SlackMessage,
    ) -> bool:
        import httpx

        payload = {"text": message.text}
        if message.blocks:
            payload["blocks"] = message.blocks
        if message.attachments:
            payload["attachments"] = message.attachments

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(webhook_url, json=payload)
            if response.status_code != 200:
                logger.error("Slack webhook error: %s", response.text)
                incr("slack.webhook_error")
                return False

            incr("slack.webhook_sent")
            return True


class SlackIntegrationManager:
    def __init__(self, db_pool: asyncpg.Pool):
        self._pool = db_pool

    async def register_team(
        self,
        tenant_id: str,
        team_id: str,
        access_token: str,
        bot_user_id: str | None = None,
        default_channel: str | None = None,
    ) -> SlackTeamConfig:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO public.slack_integrations
                    (tenant_id, slack_team_id, access_token, bot_user_id, default_channel, is_active)
                VALUES ($1, $2, $3, $4, $5, true)
                ON CONFLICT (tenant_id) DO UPDATE SET
                    slack_team_id = $2,
                    access_token = $3,
                    bot_user_id = $4,
                    default_channel = $5,
                    is_active = true,
                    updated_at = now()
                """,
                tenant_id,
                team_id,
                access_token,
                bot_user_id,
                default_channel,
            )

        incr("slack.team_registered")
        logger.info("Slack team registered: tenant=%s team=%s", tenant_id, team_id)

        return SlackTeamConfig(
            team_id=team_id,
            tenant_id=tenant_id,
            access_token=access_token,
            bot_user_id=bot_user_id,
            default_channel=default_channel,
        )

    async def get_team_config(self, tenant_id: str) -> SlackTeamConfig | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT slack_team_id, access_token, bot_user_id, default_channel,
                       enabled_notifications, is_active
                FROM public.slack_integrations
                WHERE tenant_id = $1 AND is_active = true
                """,
                tenant_id,
            )

            if not row:
                return None

            return SlackTeamConfig(
                team_id=row["slack_team_id"],
                tenant_id=tenant_id,
                access_token=row["access_token"],
                bot_user_id=row["bot_user_id"],
                default_channel=row["default_channel"],
                enabled_notifications=row["enabled_notifications"] or [],
                is_active=row["is_active"],
            )

    async def send_notification(
        self,
        tenant_id: str,
        message_type: SlackMessageType,
        template_vars: dict[str, Any],
        channel: str | None = None,
    ) -> bool:
        config = await self.get_team_config(tenant_id)
        if not config:
            logger.warning("No Slack integration for tenant: %s", tenant_id)
            return False

        enabled = config.enabled_notifications
        if enabled and message_type.value not in enabled:
            return False

        target_channel = channel or config.default_channel
        if not target_channel:
            logger.warning("No channel configured for tenant: %s", tenant_id)
            return False

        message = self._build_message(message_type, target_channel, template_vars)

        client = SlackClient(config.access_token)
        try:
            await client.post_message(
                message.channel,
                message.text,
                message.blocks,
                message.attachments,
            )
            incr("slack.notification_sent", {"type": message_type.value})
            return True
        except Exception as e:
            error_str = str(e).lower()
            if (
                "invalid_auth" in error_str
                or "account_inactive" in error_str
                or "token_revoked" in error_str
            ):
                logger.warning(
                    "Slack auth failed, disabling integration for tenant: %s", tenant_id
                )
                await self._disable_integration(tenant_id)
            logger.error("Failed to send Slack notification: %s", e)
            return False

    async def send_job_match_notification(
        self,
        tenant_id: str,
        job: dict[str, Any],
        user_email: str,
    ) -> bool:
        template_vars = {
            "title": job.get("title", "Unknown"),
            "company": job.get("company", "Unknown"),
            "location": job.get("location", "Remote"),
            "score": str(job.get("match_score", 0)),
            "job_url": job.get("url", "#"),
            "apply_url": f"https://jobhuntin.com/jobs/{job.get('id', '')}/apply",
        }

        return await self.send_notification(
            tenant_id,
            SlackMessageType.JOB_MATCH,
            template_vars,
        )

    async def send_application_update(
        self,
        tenant_id: str,
        application: dict[str, Any],
    ) -> bool:
        template_vars = {
            "company": application.get("company", "Unknown"),
            "title": application.get("job_title", "Unknown"),
            "status": application.get("status", "Updated"),
            "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        }

        return await self.send_notification(
            tenant_id,
            SlackMessageType.APPLICATION_UPDATE,
            template_vars,
        )

    async def send_interview_reminder(
        self,
        tenant_id: str,
        interview: dict[str, Any],
    ) -> bool:
        template_vars = {
            "company": interview.get("company", "Unknown"),
            "interview_time": interview.get("scheduled_at", "TBD"),
            "duration": str(interview.get("duration_minutes", 30)),
            "interview_type": interview.get("type", "Video Call"),
            "location": interview.get("location", "Video Call"),
            "calendar_url": interview.get("calendar_url", "#"),
            "prep_url": f"https://jobhuntin.com/interviews/{interview.get('id', '')}/prepare",
        }

        return await self.send_notification(
            tenant_id,
            SlackMessageType.INTERVIEW_REMINDER,
            template_vars,
        )

    async def send_weekly_digest(
        self,
        tenant_id: str,
        stats: dict[str, Any],
    ) -> bool:
        template_vars = {
            "jobs_matched": str(stats.get("jobs_matched", 0)),
            "applications_sent": str(stats.get("applications_sent", 0)),
            "interviews": str(stats.get("interviews", 0)),
            "response_rate": str(stats.get("response_rate", 0)),
        }

        return await self.send_notification(
            tenant_id,
            SlackMessageType.WEEKLY_DIGEST,
            template_vars,
        )

    async def set_enabled_notifications(
        self,
        tenant_id: str,
        notification_types: list[str],
    ) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE public.slack_integrations
                SET enabled_notifications = $1, updated_at = now()
                WHERE tenant_id = $2
                """,
                notification_types,
                tenant_id,
            )

    async def disconnect_team(self, tenant_id: str) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE public.slack_integrations
                SET is_active = false, updated_at = now()
                WHERE tenant_id = $1
                """,
                tenant_id,
            )

        incr("slack.team_disconnected")

    async def _disable_integration(self, tenant_id: str) -> None:
        """Disable Slack integration when auth fails."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE public.slack_integrations
                SET is_active = false, updated_at = now()
                WHERE tenant_id = $1
                """,
                tenant_id,
            )
        incr("slack.integration_disabled")

    def _build_message(
        self,
        message_type: SlackMessageType,
        channel: str,
        template_vars: dict[str, Any],
    ) -> SlackMessage:
        template = MESSAGE_TEMPLATES.get(message_type.value, {})

        text = template.get("text", "")
        blocks = template.get("blocks", [])

        formatted_blocks = self._format_blocks(blocks, template_vars)

        return SlackMessage(
            channel=channel,
            message_type=message_type,
            text=text,
            blocks=formatted_blocks,
            metadata=template_vars,
        )

    def _format_blocks(
        self,
        blocks: list[dict[str, Any]],
        template_vars: dict[str, Any],
    ) -> list[dict[str, Any]]:
        import copy

        formatted = []
        for block in blocks:
            block_copy = copy.deepcopy(block)

            if "text" in block_copy:
                if isinstance(block_copy["text"], dict):
                    for key, val in block_copy["text"].items():
                        if isinstance(val, str):
                            block_copy["text"][key] = self._interpolate(
                                val, template_vars
                            )
                else:
                    block_copy["text"] = self._interpolate(
                        block_copy["text"], template_vars
                    )

            if "fields" in block_copy:
                for block_field in block_copy["fields"]:
                    if "text" in block_field:
                        block_field["text"] = self._interpolate(
                            block_field["text"], template_vars
                        )

            if "elements" in block_copy:
                for element in block_copy["elements"]:
                    if "url" in element:
                        element["url"] = self._interpolate(
                            element["url"], template_vars
                        )

            formatted.append(block_copy)

        return formatted

    def _interpolate(self, text: str, variables: dict[str, Any]) -> str:
        for key, value in variables.items():
            text = text.replace(f"{{{key}}}", str(value))
        return text


def verify_slack_signature(
    signing_secret: str,
    body: str,
    timestamp: str,
    signature: str,
) -> bool:
    if abs(int(datetime.now(timezone.utc).timestamp()) - int(timestamp)) > 300:
        return False

    basestring = f"v0:{timestamp}:{body}"
    expected_sig = (
        "v0="
        + hmac.new(
            signing_secret.encode(),
            basestring.encode(),
            hashlib.sha256,
        ).hexdigest()
    )

    return hmac.compare_digest(signature, expected_sig)


async def init_slack_tables(conn: asyncpg.Connection) -> None:
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS public.slack_integrations (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            tenant_id UUID UNIQUE NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
            slack_team_id TEXT NOT NULL,
            access_token TEXT NOT NULL,
            bot_user_id TEXT,
            default_channel TEXT,
            enabled_notifications TEXT[] DEFAULT '{}',
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_slack_tenant_id
            ON public.slack_integrations(tenant_id);
        """
    )
    logger.info("Slack tables initialized")
