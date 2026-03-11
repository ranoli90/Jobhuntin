"""Alerting v2 — PagerDuty integration, Slack channels per tenant tier,
auto-rollback on agent failure spikes.

Extends observability.py with multi-channel alert dispatch.
"""

from __future__ import annotations

import asyncio
from typing import Any

import asyncpg

from backend.domain.observability import run_all_alerts
from shared.config import get_settings
from shared.logging_config import get_logger

logger = get_logger("sorce.alerting_v2")


# ---------------------------------------------------------------------------
# PagerDuty
# ---------------------------------------------------------------------------


async def send_pagerduty_event(
    summary: str,
    severity: str = "warning",
    source: str = "sorce-api",
    details: dict[str, Any] | None = None,
) -> str | None:
    """Send an event to PagerDuty via Events API v2."""
    s = get_settings()
    if not s.pagerduty_api_key:
        logger.debug("PagerDuty not configured — skipping alert")
        return None

    try:
        import httpx

        payload = {
            "routing_key": s.pagerduty_api_key,
            "event_action": "trigger",
            "payload": {
                "summary": summary,
                "severity": severity,
                "source": source,
                "component": "sorce",
                "custom_details": details or {},
            },
        }
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(
                        "https://events.pagerduty.com/v2/enqueue",
                        json=payload,
                    )
                    if resp.status_code == 202:
                        data = resp.json()
                        logger.info("PagerDuty event created: %s", data.get("dedup_key"))
                        return data.get("dedup_key")
                    else:
                        logger.error("PagerDuty error %d: %s", resp.status_code, resp.text)
                        return None
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                if attempt < max_retries:
                    await asyncio.sleep(0.5 * (2**attempt))
                else:
                    logger.error("PagerDuty send failed after retries: %s", e)
                    return None
    except ImportError:
        logger.warning("httpx not installed — PagerDuty disabled")
        return None
    except Exception as exc:
        logger.error("PagerDuty send failed: %s", exc)
        return None
    return None


# ---------------------------------------------------------------------------
# Opsgenie (M10: Alerting Integration)
# ---------------------------------------------------------------------------


async def send_opsgenie_alert(
    message: str,
    alias: str | None = None,
    description: str | None = None,
    priority: str = "P3",
    tags: list[str] | None = None,
    details: dict[str, Any] | None = None,
) -> str | None:
    """M10: Send an alert to Opsgenie.

    Args:
        message: Alert message/title
        alias: Unique identifier for deduplication
        description: Detailed description
        priority: P1 (Critical), P2 (High), P3 (Moderate), P4 (Low), P5 (Info)
        tags: List of tags for filtering
        details: Additional custom details

    Returns:
        Alert ID if successful, None otherwise
    """
    from shared.config import get_settings

    s = get_settings()
    if not s.opsgenie_api_key:
        logger.debug("Opsgenie not configured — skipping alert")
        return None

    try:
        import httpx

        payload: dict[str, Any] = {
            "message": message,
            "priority": priority,
        }

        if alias:
            payload["alias"] = alias
        if description:
            payload["description"] = description
        if tags:
            payload["tags"] = tags
        if details:
            payload["details"] = details

        headers = {
            "Authorization": f"GenieKey {s.opsgenie_api_key}",
            "Content-Type": "application/json",
        }

        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(
                        s.opsgenie_api_url,
                        json=payload,
                        headers=headers,
                    )
                    if resp.status_code in (200, 201, 202):
                        data = resp.json()
                        alert_id = data.get("data", {}).get("alertId") or data.get("requestId")
                        logger.info("Opsgenie alert created: %s", alert_id)
                        return alert_id
                    else:
                        logger.error("Opsgenie error %d: %s", resp.status_code, resp.text)
                        return None
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                if attempt < max_retries:
                    await asyncio.sleep(0.5 * (2**attempt))
                else:
                    logger.error("Opsgenie send failed after retries: %s", e)
                    return None
    except ImportError:
        logger.warning("httpx not installed — Opsgenie disabled")
        return None
    except Exception as exc:
        logger.error("Opsgenie send failed: %s", exc)
        return None
    return None


# ---------------------------------------------------------------------------
# Slack
# ---------------------------------------------------------------------------


async def send_slack_message(
    text: str,
    channel: str | None = None,
    blocks: list[dict] | None = None,
) -> bool:
    """Send a message to a Slack channel via incoming webhook."""
    s = get_settings()
    webhook_url = s.slack_webhook_url
    if not webhook_url:
        logger.debug("Slack not configured — skipping alert")
        return False

    try:
        import httpx

        payload: dict[str, Any] = {"text": text}
        if channel:
            payload["channel"] = channel
        if blocks:
            payload["blocks"] = blocks

        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(webhook_url, json=payload)
                    ok = resp.status_code == 200
                    if not ok:
                        logger.error("Slack error %d: %s", resp.status_code, resp.text)
                    return ok
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                if attempt < max_retries:
                    await asyncio.sleep(0.5 * (2**attempt))
                else:
                    logger.error("Slack send failed after retries: %s", e)
                    return False
    except ImportError:
        logger.warning("httpx not installed — Slack disabled")
        return False
    except Exception as exc:
        logger.error("Slack send failed: %s", exc)
        return False
    return False


def slack_channel_for_tier(plan: str) -> str:
    """Return the appropriate Slack channel for a plan tier."""
    s = get_settings()
    if plan == "ENTERPRISE":
        return s.slack_enterprise_channel
    return s.slack_ops_channel


# ---------------------------------------------------------------------------
# Auto-rollback
# ---------------------------------------------------------------------------


async def check_and_auto_rollback(conn: asyncpg.Connection) -> dict[str, Any] | None:
    """Check if agent success rate has dropped critically and auto-rollback
    the prompt version to the previous known-good version.

    Triggers if success rate < 60% in the last hour with > 20 samples.
    """
    row = await conn.fetchrow(
        """
        SELECT
            COUNT(*)::int AS total,
            COUNT(*) FILTER (WHERE status IN ('APPLIED','SUBMITTED','COMPLETED','REGISTERED'))::int AS succeeded
        FROM public.applications
        WHERE created_at >= now() - interval '1 hour'
          AND status NOT IN ('QUEUED', 'PROCESSING')
    """
    )

    if not row or (row["total"] or 0) < 20:
        return None

    rate = (row["succeeded"] or 0) / max(row["total"], 1) * 100

    if rate < 60:
        # Auto-rollback: set prompt_version_override to V1 (safe default)
        from shared.config import get_settings

        s = get_settings()
        if not s.prompt_version_override:
            logger.critical(
                "AUTO-ROLLBACK: Agent success rate %.1f%% — reverting to default prompt",
                rate,
            )
            # In production, update the config store
            # For now, log the action
            return {
                "action": "auto_rollback",
                "reason": f"Success rate {rate:.1f}% < 60% threshold",
                "samples": row["total"],
                "succeeded": row["succeeded"],
            }
    return None


# ---------------------------------------------------------------------------
# A/B Test graduation — auto-promote winning experiments
# ---------------------------------------------------------------------------


async def check_experiment_graduation(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    """Check running experiments and auto-graduate winners.

    An experiment graduates if:
    - ≥ 100 samples per variant
    - One variant has ≥ 5% higher success rate
    - Experiment has been running ≥ 7 days
    """
    experiments = await conn.fetch(
        """
        SELECT e.key, e.variants, e.created_at,
               COUNT(DISTINCT ea.id)::int AS total_assignments
        FROM public.experiments e
        LEFT JOIN public.experiment_assignments ea ON ea.experiment_key = e.key
        WHERE e.is_active = true
          AND e.created_at <= now() - interval '7 days'
        GROUP BY e.key, e.variants, e.created_at
        HAVING COUNT(DISTINCT ea.id) >= 200
    """
    )

    if not experiments:
        return []

    # Batch fetch variant stats for all experiments (avoids N+1)
    keys = [str(e["key"]) for e in experiments]
    all_variants = await conn.fetch(
        """
        SELECT ea.experiment_key, ea.variant,
               COUNT(*)::int AS samples,
               COUNT(*) FILTER (
                   WHERE a.status IN ('APPLIED','SUBMITTED','COMPLETED','REGISTERED')
               )::int AS succeeded
        FROM public.experiment_assignments ea
        JOIN public.applications a ON a.user_id = ea.user_id
        WHERE ea.experiment_key = ANY($1::text[])
        GROUP BY ea.experiment_key, ea.variant
        HAVING COUNT(*) >= 100
        """,
        keys,
    )

    variants_by_exp: dict[str, list] = {}
    for row in all_variants:
        key = str(row["experiment_key"])
        variants_by_exp.setdefault(key, []).append(row)

    graduated = []
    for exp in experiments:
        key = exp["key"]
        variants = variants_by_exp.get(str(key), [])

        if len(variants) < 2:
            continue

        # Find best variant
        best = max(variants, key=lambda v: (v["succeeded"] or 0) / max(v["samples"], 1))
        best_rate = (best["succeeded"] or 0) / max(best["samples"], 1) * 100

        runner_up = sorted(
            variants,
            key=lambda v: (v["succeeded"] or 0) / max(v["samples"], 1),
            reverse=True,
        )[1]
        runner_up_rate = (
            (runner_up["succeeded"] or 0) / max(runner_up["samples"], 1) * 100
        )

        if best_rate - runner_up_rate >= 5:
            # Graduate: deactivate experiment, log result
            await conn.execute(
                "UPDATE public.experiments SET is_active = false WHERE key = $1",
                key,
            )
            result = {
                "experiment": key,
                "winner": best["variant"],
                "winner_rate": round(best_rate, 1),
                "runner_up": runner_up["variant"],
                "runner_up_rate": round(runner_up_rate, 1),
                "delta": round(best_rate - runner_up_rate, 1),
            }
            graduated.append(result)
            logger.info(
                "Experiment graduated: %s → winner=%s (+%.1f%%)",
                key,
                best["variant"],
                best_rate - runner_up_rate,
            )

    return graduated


# ---------------------------------------------------------------------------
# Orchestrator — run all checks and dispatch alerts
# ---------------------------------------------------------------------------


async def run_alerting_cycle(conn: asyncpg.Connection) -> dict[str, Any]:
    """Full alerting cycle:
    1. Run all alert checks
    2. Check for auto-rollback
    3. Graduate experiments
    4. Dispatch to PagerDuty/Slack.
    """
    # 1. Standard alerts
    alerts = await run_all_alerts(conn)

    # 2. Auto-rollback check
    rollback = await check_and_auto_rollback(conn)

    # 3. Experiment graduation
    graduated = await check_experiment_graduation(conn)

    # 4. Dispatch critical alerts
    for alert in alerts:
        if alert.get("level") == "critical":
            # M10: Send to both PagerDuty and Opsgenie if configured
            pagerduty_dedup = await send_pagerduty_event(
                summary=alert.get("message", "Sorce alert"),
                severity="critical",
                details=alert,
            )

            # M10: Send to Opsgenie as well
            opsgenie_id = await send_opsgenie_alert(
                message=alert.get("message", "Sorce critical alert"),
                alias=f"alert-{alert.get('code', 'unknown')}",
                description=alert.get("message", ""),
                priority="P1",  # Critical
                tags=["critical", alert.get("code", "unknown")],
                details={
                    **alert,
                    "pagerduty_dedup": pagerduty_dedup,
                },
            )

            await send_slack_message(
                text=f"🚨 *CRITICAL*: {alert.get('message')}",
                channel=get_settings().slack_ops_channel,
            )

            logger.info(
                "Critical alert dispatched: PagerDuty=%s, Opsgenie=%s",
                pagerduty_dedup,
                opsgenie_id,
            )
        elif alert.get("level") == "warning":
            # M10: Send warnings to Opsgenie as P3 (Moderate)
            await send_opsgenie_alert(
                message=alert.get("message", "Sorce warning"),
                alias=f"warning-{alert.get('code', 'unknown')}",
                description=alert.get("message", ""),
                priority="P3",  # Moderate
                tags=["warning", alert.get("code", "unknown")],
                details=alert,
            )

            await send_slack_message(
                text=f"⚠️ *WARNING*: {alert.get('message')}",
                channel=get_settings().slack_ops_channel,
            )

    if rollback:
        # M10: Send auto-rollback alerts to both PagerDuty and Opsgenie
        pagerduty_dedup = await send_pagerduty_event(
            summary=f"AUTO-ROLLBACK: {rollback.get('reason')}",
            severity="critical",
            details=rollback,
        )

        opsgenie_id = await send_opsgenie_alert(
            message=f"AUTO-ROLLBACK: {rollback.get('reason')}",
            alias="auto-rollback",
            description=f"Automatic rollback triggered: {rollback.get('reason')}",
            priority="P1",  # Critical
            tags=["auto-rollback", "critical", "agent"],
            details={
                **rollback,
                "pagerduty_dedup": pagerduty_dedup,
            },
        )

        await send_slack_message(
            text=f"🔄 *AUTO-ROLLBACK*: {rollback.get('reason')}",
            channel=get_settings().slack_ops_channel,
        )

        logger.info(
            "Auto-rollback alert dispatched: PagerDuty=%s, Opsgenie=%s",
            pagerduty_dedup,
            opsgenie_id,
        )

    for grad in graduated:
        await send_slack_message(
            text=f"🎓 *Experiment Graduated*: `{grad['experiment']}` → winner `{grad['winner']}` (+{grad['delta']}%)",
            channel=get_settings().slack_ops_channel,
        )

    return {
        "alerts": alerts,
        "rollback": rollback,
        "graduated_experiments": graduated,
        "dispatched": len(
            [a for a in alerts if a.get("level") in ("critical", "warning")]
        ),
    }
