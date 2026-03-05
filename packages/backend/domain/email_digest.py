"""Weekly email digest — generates and sends a summary of job search activity.

Designed to be called by a cron job or scheduled task once per week.
Uses Resend API for email delivery.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

import asyncpg

from shared.circuit_breaker import CircuitBreakerOpenError, get_circuit_breaker
from shared.config import get_settings
from shared.logging_config import get_logger

logger = get_logger("sorce.email_digest")


# ---------------------------------------------------------------------------
# Digest data assembly
# ---------------------------------------------------------------------------


async def build_digest_for_user(
    conn: asyncpg.Connection,
    user_id: str,
    period_days: int = 7,
) -> dict[str, Any] | None:
    """Build weekly digest stats for a user.

    Returns None if user had no activity in the period.
    """
    now = datetime.now(timezone.utc)
    period_start = now - timedelta(days=period_days)

    stats = await conn.fetchrow(
        """
        SELECT
            COUNT(*)::int AS total_apps,
            COUNT(*) FILTER (WHERE status IN ('APPLIED','SUBMITTED','COMPLETED'))::int AS succeeded,
            COUNT(*) FILTER (WHERE status = 'FAILED')::int AS failed,
            COUNT(*) FILTER (WHERE status = 'REQUIRES_INPUT')::int AS on_hold,
            COUNT(*) FILTER (WHERE status = 'QUEUED' OR status = 'PROCESSING')::int AS in_progress
        FROM public.applications
        WHERE user_id = $1
          AND created_at >= $2
        """,
        user_id,
        period_start,
    )

    total = stats["total_apps"] if stats else 0
    if total == 0:
        return None

    # Top companies applied to
    companies = await conn.fetch(
        """
        SELECT j.company, COUNT(*)::int AS count
        FROM public.applications a
        JOIN public.jobs j ON j.id = a.job_id
        WHERE a.user_id = $1 AND a.created_at >= $2
        GROUP BY j.company
        ORDER BY count DESC
        LIMIT 5
        """,
        user_id,
        period_start,
    )

    return {
        "period_start": period_start.isoformat(),
        "period_end": now.isoformat(),
        "total_applications": total,
        "succeeded": stats["succeeded"],
        "failed": stats["failed"],
        "on_hold": stats["on_hold"],
        "in_progress": stats["in_progress"],
        "top_companies": [
            {"company": r["company"], "count": r["count"]} for r in companies
        ],
    }


# ---------------------------------------------------------------------------
# Email rendering
# ---------------------------------------------------------------------------


def render_digest_html(user_name: str | None, stats: dict[str, Any]) -> str:
    """Render the weekly digest as HTML email."""
    greeting = f"Hi {user_name}," if user_name else "Hi there,"
    companies_html = ""
    for c in stats.get("top_companies", []):
        companies_html += f"<li>{c['company']} ({c['count']} apps)</li>"

    return f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #1E293B;">
        <div style="text-align: center; margin-bottom: 24px;">
            <h1 style="color: #3B82F6; margin: 0; font-size: 24px;">Sorce</h1>
            <p style="color: #64748B; margin: 4px 0 0;">Your Weekly Job Search Report</p>
        </div>

        <p>{greeting}</p>
        <p>Here's your job search summary for the past week:</p>

        <div style="background: #F1F5F9; border-radius: 12px; padding: 20px; margin: 20px 0;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="text-align: center; padding: 8px;">
                        <div style="font-size: 28px; font-weight: 700; color: #3B82F6;">{stats["total_applications"]}</div>
                        <div style="font-size: 12px; color: #64748B;">Applied</div>
                    </td>
                    <td style="text-align: center; padding: 8px;">
                        <div style="font-size: 28px; font-weight: 700; color: #10B981;">{stats["succeeded"]}</div>
                        <div style="font-size: 12px; color: #64748B;">Submitted</div>
                    </td>
                    <td style="text-align: center; padding: 8px;">
                        <div style="font-size: 28px; font-weight: 700; color: #F59E0B;">{stats["on_hold"]}</div>
                        <div style="font-size: 12px; color: #64748B;">Need Input</div>
                    </td>
                    <td style="text-align: center; padding: 8px;">
                        <div style="font-size: 28px; font-weight: 700; color: #64748B;">{stats["in_progress"]}</div>
                        <div style="font-size: 12px; color: #64748B;">In Progress</div>
                    </td>
                </tr>
            </table>
        </div>

        {"<div style='margin: 20px 0;'><strong>Top companies this week:</strong><ul>" + companies_html + "</ul></div>" if companies_html else ""}

        {_hold_cta(stats["on_hold"]) if stats["on_hold"] > 0 else ""}

        <div style="text-align: center; margin: 30px 0;">
            <a href="sorce://feed" style="background: #3B82F6; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600;">Open Sorce</a>
        </div>

        <p style="color: #94A3B8; font-size: 12px; text-align: center; margin-top: 40px;">
            You're receiving this because you use Sorce. <a href="sorce://settings" style="color: #94A3B8;">Unsubscribe</a>
        </p>
    </div>
    """


def _hold_cta(count: int) -> str:
    return f"""
    <div style="background: #FEF3C7; border-radius: 8px; padding: 14px; margin: 16px 0; border-left: 4px solid #F59E0B;">
        <strong>{count} application(s) need your input.</strong> Answer the questions so Sorce can finish submitting.
        <a href="sorce://applications" style="color: #D97706; font-weight: 600;"> Review now →</a>
    </div>
    """


# ---------------------------------------------------------------------------
# Send via Resend
# ---------------------------------------------------------------------------


async def send_digest_email(
    to_email: str,
    subject: str,
    html: str,
) -> bool:
    """Send an email via Resend API. Returns True on success."""
    import httpx

    s = get_settings()
    if not s.resend_api_key:
        logger.warning("Resend API key not set, skipping email send")
        return False

    cb = get_circuit_breaker("resend")

    try:
        async with cb:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {s.resend_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": s.email_from,
                        "to": [to_email],
                        "subject": subject,
                        "html": html,
                    },
                )
                if resp.status_code in (200, 201):
                    return True
                logger.error("Resend error: %d %s", resp.status_code, resp.text[:200])
                return False
    except CircuitBreakerOpenError as exc:
        logger.warning("Resend circuit breaker open: %s", exc)
        return False
    except Exception as exc:
        logger.error("Email send failed: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Batch digest runner (called by cron)
# ---------------------------------------------------------------------------


async def run_weekly_digest(pool: asyncpg.Pool) -> dict[str, int]:
    """Generate and send weekly digests for all active users.

    Returns {"sent": N, "skipped": M, "failed": F}.
    """
    sent = skipped = failed = 0

    async with pool.acquire() as conn:
        # Get all users with activity in last 7 days
        users = await conn.fetch(
            """
            SELECT DISTINCT u.id, u.email, u.full_name AS name
            FROM public.users u
            JOIN public.applications a ON a.user_id = u.id
            WHERE a.created_at >= now() - interval '7 days'
            """
        )

        for user in users:
            user_id = str(user["id"])
            email = user.get("email")
            name = user.get("name")

            if not email:
                skipped += 1
                continue

            # Check if we already sent a digest this week
            already = await conn.fetchval(
                """
                SELECT COUNT(*) FROM public.email_digest_log
                WHERE user_id = $1 AND sent_at >= now() - interval '6 days'
                """,
                user_id,
            )
            if already and already > 0:
                skipped += 1
                continue

            stats = await build_digest_for_user(conn, user_id)
            if not stats:
                skipped += 1
                continue

            html = render_digest_html(name, stats)
            subject = f"Your week: {stats['total_applications']} applications submitted"
            success = await send_digest_email(email, subject, html)

            if success:
                # Log the digest
                await conn.execute(
                    """
                    INSERT INTO public.email_digest_log
                        (user_id, tenant_id, period_start, period_end, stats)
                    VALUES ($1, NULL, $2::timestamptz, $3::timestamptz, $4::jsonb)
                    """,
                    user_id,
                    stats["period_start"],
                    stats["period_end"],
                    json.dumps(stats),
                )
                sent += 1
            else:
                failed += 1

    logger.info(
        "Weekly digest complete: sent=%d, skipped=%d, failed=%d", sent, skipped, failed
    )
    return {"sent": sent, "skipped": skipped, "failed": failed}
