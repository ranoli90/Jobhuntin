"""On-Call Integration — PagerDuty/Opsgenie integration for alerting.

Provides:
- PagerDuty Events API v2 integration
- Opsgenie integration
- Escalation policy routing
- Alert deduplication
- Incident auto-resolution
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

import httpx

from shared.config import get_settings
from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.oncall")


class Severity(StrEnum):
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class AlertAction(StrEnum):
    TRIGGER = "trigger"
    ACKNOWLEDGE = "acknowledge"
    RESOLVE = "resolve"


class PagerDutyClient:
    def __init__(
        self,
        api_key: str,
        service_id: str,
        default_severity: Severity = Severity.ERROR,
    ):
        self.api_key = api_key
        self.service_id = service_id
        self.default_severity = default_severity
        self.base_url = "https://events.pagerduty.com/v2"

    async def send_event(
        self,
        action: AlertAction,
        dedup_key: str,
        summary: str,
        severity: Severity | None = None,
        details: dict[str, Any] | None = None,
        links: list[str] | None = None,
    ) -> dict[str, Any]:
        severity = severity or self.default_severity

        payload = {
            "routing_key": self.service_id,
            "event_action": action.value,
            "dedup_key": dedup_key,
            "payload": {
                "summary": summary,
                "severity": severity.value,
                "source": "sorce-api",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "custom_details": details or {},
            },
        }

        if links:
            payload["links"] = [{"href": link} for link in links]

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.base_url}/enqueue",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Token token={self.api_key}",
                    },
                    json=payload,
                )

                if resp.status_code == 202:
                    incr("oncall.pagerduty.success", {"action": action.value})
                    return {"success": True, "dedup_key": dedup_key}
                else:
                    incr("oncall.pagerduty.failed", {"action": action.value})
                    logger.error(
                        "PagerDuty error: %d %s", resp.status_code, resp.text[:200]
                    )
                    return {"success": False, "error": resp.text[:200]}

        except Exception as e:
            incr("oncall.pagerduty.error")
            logger.error("PagerDuty request failed: %s", e)
            return {"success": False, "error": str(e)}

    async def trigger(
        self,
        dedup_key: str,
        summary: str,
        severity: Severity | None = None,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await self.send_event(
            action=AlertAction.TRIGGER,
            dedup_key=dedup_key,
            summary=summary,
            severity=severity,
            details=details,
        )

    async def acknowledge(
        self,
        dedup_key: str,
        summary: str | None = None,
    ) -> dict[str, Any]:
        return await self.send_event(
            action=AlertAction.ACKNOWLEDGE,
            dedup_key=dedup_key,
            summary=summary or "Incident acknowledged",
        )

    async def resolve(
        self,
        dedup_key: str,
        summary: str | None = None,
    ) -> dict[str, Any]:
        return await self.send_event(
            action=AlertAction.RESOLVE,
            dedup_key=dedup_key,
            summary=summary or "Incident resolved",
        )


class OpsgenieClient:
    def __init__(
        self,
        api_key: str,
        team_id: str | None = None,
        default_priority: str = "P2",
    ):
        self.api_key = api_key
        self.team_id = team_id
        self.default_priority = default_priority
        self.base_url = "https://api.opsgenie.com/v2"

    async def create_alert(
        self,
        alias: str,
        message: str,
        priority: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        priority = priority or self.default_priority

        payload = {
            "alias": alias,
            "message": message,
            "priority": priority,
            "source": "sorce-api",
        }

        if description:
            payload["description"] = description
        if tags:
            payload["tags"] = tags
        if details:
            payload["details"] = details
        if self.team_id:
            payload["responders"] = [{"type": "team", "id": self.team_id}]

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.base_url}/alerts",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"GenieKey {self.api_key}",
                    },
                    json=payload,
                )

                if resp.status_code in (200, 201, 202):
                    incr("oncall.opsgenie.success")
                    return {
                        "success": True,
                        "request_id": resp.headers.get("X-Request-ID"),
                    }
                else:
                    incr("oncall.opsgenie.failed")
                    logger.error(
                        "Opsgenie error: %d %s", resp.status_code, resp.text[:200]
                    )
                    return {"success": False, "error": resp.text[:200]}

        except Exception as e:
            incr("oncall.opsgenie.error")
            logger.error("Opsgenie request failed: %s", e)
            return {"success": False, "error": str(e)}

    async def close_alert(self, alias: str) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.base_url}/alerts/{alias}/close",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"GenieKey {self.api_key}",
                    },
                    json={"source": "sorce-api"},
                )

                if resp.status_code in (200, 202):
                    return {"success": True}
                return {"success": False, "error": resp.text[:200]}

        except Exception as e:
            return {"success": False, "error": str(e)}


def get_oncall_client() -> PagerDutyClient | OpsgenieClient | None:
    s = get_settings()

    if s.pagerduty_api_key and s.pagerduty_service_id:
        return PagerDutyClient(s.pagerduty_api_key, s.pagerduty_service_id)

    if hasattr(s, "opsgenie_api_key") and s.opsgenie_api_key:
        return OpsgenieClient(s.opsgenie_api_key, getattr(s, "opsgenie_team_id", None))

    return None


async def trigger_incident(
    dedup_key: str,
    summary: str,
    severity: Severity = Severity.ERROR,
    details: dict[str, Any] | None = None,
) -> bool:
    client = get_oncall_client()
    if not client:
        logger.warning("No on-call client configured")
        return False

    if isinstance(client, PagerDutyClient):
        result = await client.trigger(dedup_key, summary, severity, details)
    else:
        priority_map = {
            Severity.CRITICAL: "P1",
            Severity.ERROR: "P2",
            Severity.WARNING: "P3",
            Severity.INFO: "P4",
        }
        result = await client.create_alert(
            alias=dedup_key,
            message=summary,
            priority=priority_map.get(severity, "P2"),
            details=details,
        )

    return result.get("success", False)


async def resolve_incident(dedup_key: str) -> bool:
    client = get_oncall_client()
    if not client:
        return False

    if isinstance(client, PagerDutyClient):
        result = await client.resolve(dedup_key)
    else:
        result = await client.close_alert(dedup_key)

    return result.get("success", False)
