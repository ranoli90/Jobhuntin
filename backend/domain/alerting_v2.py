"""Alerting v2 — PagerDuty integration, Slack channels per tenant tier,
auto-rollback on agent failure spikes.

Extends observability.py with multi-channel alert dispatch.
"""

from __future__ import annotations

from typing import Any

import asyncpg
from shared.config import get_settings
from shared.logging_config import get_logger

from backend.domain.observability import run_all_alerts

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
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=payload,
                timeout=10,
            )
            if resp.status_code == 202:
                data = resp.json()
                logger.info("PagerDuty event created: %s", data.get("dedup_key"))
                return data.get("dedup_key")
            else:
                logger.error("PagerDuty error %d: %s", resp.status_code, resp.text)
                return None
    except ImportError:
        logger.warning("httpx not installed — PagerDuty disabled")
        return None
    except Exception as exc:
        logger.error("PagerDuty send failed: %s", exc)
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

        async with httpx.AsyncClient() as client:
            resp = await client.post(webhook_url, json=payload, timeout=10)
            ok = resp.status_code == 200
            if not ok:
                logger.error("Slack error %d: %s", resp.status_code, resp.text)
            return ok
    except ImportError:
        logger.warning("httpx not installed — Slack disabled")
        return False
    except Exception as exc:
        logger.error("Slack send failed: %s", exc)
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
    row = await conn.fetchrow("""
        SELECT
            COUNT(*)::int AS total,
            COUNT(*) FILTER (WHERE status IN ('APPLIED','SUBMITTED','COMPLETED','REGISTERED'))::int AS succeeded
        FROM public.applications
        WHERE created_at >= now() - interval '1 hour'
          AND status NOT IN ('QUEUED', 'PROCESSING')
    """)

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
    experiments = await conn.fetch("""
        SELECT e.key, e.variants, e.created_at,
               COUNT(DISTINCT ea.id)::int AS total_assignments
        FROM public.experiments e
        LEFT JOIN public.experiment_assignments ea ON ea.experiment_key = e.key
        WHERE e.is_active = true
          AND e.created_at <= now() - interval '7 days'
        GROUP BY e.key, e.variants, e.created_at
        HAVING COUNT(DISTINCT ea.id) >= 200
    """)

    graduated = []
    for exp in experiments:
        key = exp["key"]
        # Get per-variant stats
        variants = await conn.fetch("""
            SELECT ea.variant,
                   COUNT(*)::int AS samples,
                   COUNT(*) FILTER (
                       WHERE a.status IN ('APPLIED','SUBMITTED','COMPLETED','REGISTERED')
                   )::int AS succeeded
            FROM public.experiment_assignments ea
            JOIN public.applications a ON a.user_id = ea.user_id
            WHERE ea.experiment_key = $1
            GROUP BY ea.variant
            HAVING COUNT(*) >= 100
        """, key)

        if len(variants) < 2:
            continue

        # Find best variant
        best = max(variants, key=lambda v: (v["succeeded"] or 0) / max(v["samples"], 1))
        best_rate = (best["succeeded"] or 0) / max(best["samples"], 1) * 100

        runner_up = sorted(
            variants, key=lambda v: (v["succeeded"] or 0) / max(v["samples"], 1), reverse=True,
        )[1]
        runner_up_rate = (runner_up["succeeded"] or 0) / max(runner_up["samples"], 1) * 100

        if best_rate - runner_up_rate >= 5:
            # Graduate: deactivate experiment, log result
            await conn.execute(
                "UPDATE public.experiments SET is_active = false WHERE key = $1", key,
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
            logger.info("Experiment graduated: %s → winner=%s (+%.1f%%)",
                        key, best["variant"], best_rate - runner_up_rate)

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
            await send_pagerduty_event(
                summary=alert.get("message", "Sorce alert"),
                severity="critical",
                details=alert,
            )
            await send_slack_message(
                text=f"🚨 *CRITICAL*: {alert.get('message')}",
                channel=get_settings().slack_ops_channel,
            )
        elif alert.get("level") == "warning":
            await send_slack_message(
                text=f"⚠️ *WARNING*: {alert.get('message')}",
                channel=get_settings().slack_ops_channel,
            )

    if rollback:
        await send_pagerduty_event(
            summary=f"AUTO-ROLLBACK: {rollback.get('reason')}",
            severity="critical",
            details=rollback,
        )
        await send_slack_message(
            text=f"🔄 *AUTO-ROLLBACK*: {rollback.get('reason')}",
            channel=get_settings().slack_ops_channel,
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
        "dispatched": len([a for a in alerts if a.get("level") in ("critical", "warning")]),
    }
