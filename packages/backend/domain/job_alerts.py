"""Job Alerts System — daily/weekly email notifications for new matching jobs.

Users can configure alerts with:
- Search keywords/titles
- Location preferences
- Salary thresholds
- Company preferences (include/exclude)
- Frequency (daily, weekly)
"""

from __future__ import annotations

import html
import json
from datetime import datetime
from enum import StrEnum
from typing import Any

import asyncpg
from pydantic import BaseModel, Field

from shared.circuit_breaker import CircuitBreakerOpenError, get_circuit_breaker
from shared.config import get_settings
from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.job_alerts")


class AlertFrequency(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    IMMEDIATE = "immediate"


class JobAlert(BaseModel):
    id: str | None = None
    user_id: str
    tenant_id: str | None = None
    name: str = "Job Alert"
    keywords: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    salary_min: int | None = None
    salary_max: int | None = None
    companies_include: list[str] = Field(default_factory=list)
    companies_exclude: list[str] = Field(default_factory=list)
    job_types: list[str] = Field(default_factory=list)
    remote_only: bool = False
    frequency: AlertFrequency = AlertFrequency.DAILY
    is_active: bool = True
    last_sent_at: datetime | None = None
    created_at: datetime | None = None


class JobAlertMatch(BaseModel):
    job_id: str
    title: str
    company: str
    location: str | None
    salary_min: float | None
    salary_max: float | None
    application_url: str
    match_score: float
    matched_keywords: list[str]


class JobAlertResult(BaseModel):
    alert_id: str
    alert_name: str
    matches: list[JobAlertMatch]
    total_new_jobs: int


class JobAlertRepo:
    @staticmethod
    async def create(
        conn: asyncpg.Connection,
        alert: JobAlert,
    ) -> str:
        row = await conn.fetchrow(
            """
            INSERT INTO public.job_alerts
                (user_id, tenant_id, name, keywords, locations, salary_min, salary_max,
                 companies_include, companies_exclude, job_types, remote_only, frequency, is_active)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12::public.alert_frequency, $13)
            RETURNING id
            """,
            alert.user_id,
            alert.tenant_id,
            alert.name,
            json.dumps(alert.keywords),
            json.dumps(alert.locations),
            alert.salary_min,
            alert.salary_max,
            json.dumps(alert.companies_include),
            json.dumps(alert.companies_exclude),
            json.dumps(alert.job_types),
            alert.remote_only,
            alert.frequency.value,
            alert.is_active,
        )
        return str(row["id"])

    @staticmethod
    async def get_by_user(
        conn: asyncpg.Connection,
        user_id: str,
    ) -> list[JobAlert]:
        rows = await conn.fetch(
            """
            SELECT * FROM public.job_alerts
            WHERE user_id = $1 AND is_active = true
            ORDER BY created_at DESC
            """,
            user_id,
        )
        return [JobAlertRepo._row_to_model(r) for r in rows]

    @staticmethod
    async def get_due_alerts(
        conn: asyncpg.Connection,
        frequency: AlertFrequency,
    ) -> list[JobAlert]:
        if frequency == AlertFrequency.DAILY:
            interval = "interval '1 day'"
        elif frequency == AlertFrequency.WEEKLY:
            interval = "interval '7 days'"
        else:
            return []

        rows = await conn.fetch(
            """
            SELECT * FROM public.job_alerts
            WHERE is_active = true
              AND frequency = $1
              AND (last_sent_at IS NULL OR last_sent_at < now() - {interval})
            """,
            frequency.value,
        )
        return [JobAlertRepo._row_to_model(r) for r in rows]

    @staticmethod
    async def update_last_sent(
        conn: asyncpg.Connection,
        alert_id: str,
    ) -> None:
        await conn.execute(
            """
            UPDATE public.job_alerts
            SET last_sent_at = now()
            WHERE id = $1
            """,
            alert_id,
        )

    @staticmethod
    async def delete(
        conn: asyncpg.Connection,
        alert_id: str,
        user_id: str,
    ) -> bool:
        result = await conn.execute(
            """
            UPDATE public.job_alerts
            SET is_active = false
            WHERE id = $1 AND user_id = $2
            """,
            alert_id,
            user_id,
        )
        return "UPDATE 1" in result

    @staticmethod
    def _row_to_model(row: asyncpg.Record) -> JobAlert:
        return JobAlert(
            id=str(row["id"]),
            user_id=str(row["user_id"]),
            tenant_id=str(row["tenant_id"]) if row["tenant_id"] else None,
            name=row["name"],
            keywords=json.loads(row["keywords"]) if row["keywords"] else [],
            locations=json.loads(row["locations"]) if row["locations"] else [],
            salary_min=row["salary_min"],
            salary_max=row["salary_max"],
            companies_include=(
                json.loads(row["companies_include"]) if row["companies_include"] else []
            ),
            companies_exclude=(
                json.loads(row["companies_exclude"]) if row["companies_exclude"] else []
            ),
            job_types=json.loads(row["job_types"]) if row["job_types"] else [],
            remote_only=row["remote_only"],
            frequency=AlertFrequency(row["frequency"]),
            is_active=row["is_active"],
            last_sent_at=row["last_sent_at"],
            created_at=row["created_at"],
        )


class JobAlertMatcher:
    @staticmethod
    async def find_matching_jobs(
        conn: asyncpg.Connection,
        alert: JobAlert,
        since_hours: int = 24,
        limit: int = 50,
    ) -> list[JobAlertMatch]:
        conditions = [f"j.created_at >= now() - interval '{since_hours} hours'"]
        params: list[Any] = []
        param_idx = 1

        if alert.keywords:
            keyword_conditions = []
            for kw in alert.keywords:
                keyword_conditions.append(f"LOWER(j.title) LIKE ${param_idx}")
                params.append(f"%{kw.lower()}%")
                param_idx += 1
            conditions.append(f"({' OR '.join(keyword_conditions)})")

        if alert.locations:
            loc_conditions = []
            for loc in alert.locations:
                loc_conditions.append(f"LOWER(j.location) LIKE ${param_idx}")
                params.append(f"%{loc.lower()}%")
                param_idx += 1
            conditions.append(f"({' OR '.join(loc_conditions)})")

        if alert.salary_min:
            conditions.append(
                f"(j.salary_min >= ${param_idx} OR j.salary_max >= ${param_idx})"
            )
            params.append(alert.salary_min)
            param_idx += 1

        if alert.companies_exclude:
            exclude_conditions = []
            for company in alert.companies_exclude:
                exclude_conditions.append(f"LOWER(j.company) NOT LIKE ${param_idx}")
                params.append(f"%{company.lower()}%")
                param_idx += 1
            conditions.extend(exclude_conditions)

        if alert.companies_include:
            include_conditions = []
            for company in alert.companies_include:
                include_conditions.append(f"LOWER(j.company) LIKE ${param_idx}")
                params.append(f"%{company.lower()}%")
                param_idx += 1
            conditions.append(f"({' OR '.join(include_conditions)})")

        if alert.remote_only:
            conditions.append("LOWER(j.location) LIKE '%remote%'")

        params.append(limit)
        limit_param = param_idx

        query = """
            SELECT j.id, j.title, j.company, j.location, j.salary_min, j.salary_max, j.application_url
            FROM public.jobs j
            WHERE {" AND ".join(conditions)}
            ORDER BY j.created_at DESC
            LIMIT ${limit_param}
        """

        rows = await conn.fetch(query, *params)
        return [
            JobAlertMatch(
                job_id=str(r["id"]),
                title=r["title"],
                company=r["company"],
                location=r["location"],
                salary_min=float(r["salary_min"]) if r["salary_min"] else None,
                salary_max=float(r["salary_max"]) if r["salary_max"] else None,
                application_url=r["application_url"],
                match_score=JobAlertMatcher._calculate_score(alert, r),
                matched_keywords=JobAlertMatcher._get_matched_keywords(alert, r),
            )
            for r in rows
        ]

    @staticmethod
    def _calculate_score(alert: JobAlert, job: asyncpg.Record) -> float:
        score = 0.0
        title_lower = (job["title"] or "").lower()
        company_lower = (job["company"] or "").lower()

        for kw in alert.keywords:
            if kw.lower() in title_lower:
                score += 20.0

        for loc in alert.locations:
            if loc.lower() in (job["location"] or "").lower():
                score += 15.0

        for company in alert.companies_include:
            if company.lower() in company_lower:
                score += 25.0

        if alert.salary_min and job["salary_max"]:
            if job["salary_max"] >= alert.salary_min:
                score += 10.0

        return min(100.0, score)

    @staticmethod
    def _get_matched_keywords(alert: JobAlert, job: asyncpg.Record) -> list[str]:
        matched = []
        title_lower = (job["title"] or "").lower()
        for kw in alert.keywords:
            if kw.lower() in title_lower:
                matched.append(kw)
        return matched


class JobAlertService:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def create_alert(self, alert: JobAlert) -> str:
        async with self.pool.acquire() as conn:
            alert_id = await JobAlertRepo.create(conn, alert)
            incr("job_alerts.created", {"frequency": alert.frequency.value})
            return alert_id

    async def get_user_alerts(self, user_id: str) -> list[JobAlert]:
        async with self.pool.acquire() as conn:
            return await JobAlertRepo.get_by_user(conn, user_id)

    async def delete_alert(self, alert_id: str, user_id: str) -> bool:
        async with self.pool.acquire() as conn:
            return await JobAlertRepo.delete(conn, alert_id, user_id)

    async def process_alerts(self, frequency: AlertFrequency) -> dict[str, int]:
        sent = skipped = failed = 0
        since_hours = 24 if frequency == AlertFrequency.DAILY else 168

        async with self.pool.acquire() as conn:
            alerts = await JobAlertRepo.get_due_alerts(conn, frequency)

            for alert in alerts:
                if not alert.id:
                    continue

                try:
                    matches = await JobAlertMatcher.find_matching_jobs(
                        conn, alert, since_hours=since_hours
                    )

                    if not matches:
                        skipped += 1
                        await JobAlertRepo.update_last_sent(conn, alert.id)
                        continue

                    user = await conn.fetchrow(
                        "SELECT email, raw_user_meta_data->>'full_name' AS name FROM auth.users WHERE id = $1",
                        alert.user_id,
                    )

                    if not user or not user["email"]:
                        skipped += 1
                        continue

                    html = self._render_alert_email(alert, matches)
                    subject = f"{len(matches)} new jobs match your alert: {alert.name}"

                    success = await self._send_email(user["email"], subject, html)

                    if success:
                        await JobAlertRepo.update_last_sent(conn, alert.id)
                        await self._log_alert_sent(conn, alert.id, matches)
                        sent += 1
                        incr("job_alerts.sent", {"frequency": frequency.value})
                    else:
                        failed += 1

                except Exception as e:
                    logger.error("Failed to process alert %s: %s", alert.id, e)
                    failed += 1

        logger.info(
            "Job alerts processed: sent=%d, skipped=%d, failed=%d",
            sent,
            skipped,
            failed,
        )
        return {"sent": sent, "skipped": skipped, "failed": failed}

    async def _send_email(self, to_email: str, subject: str, html: str) -> bool:
        import httpx

        s = get_settings()
        if not s.resend_api_key:
            logger.warning("Resend API key not set, skipping alert email")
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
                            "headers": {
                                "Precedence": "auto",
                                "Auto-Submitted": "auto-generated",
                                "X-Auto-Response-Suppress": "OOF, AutoReply",
                            },
                        },
                    )
                    return resp.status_code in (200, 201)
        except CircuitBreakerOpenError:
            logger.warning("Resend circuit breaker open")
            return False
        except Exception as e:
            logger.error("Failed to send alert email: %s", e)
            return False

    def _render_alert_email(self, alert: JobAlert, matches: list[JobAlertMatch]) -> str:
        def _safe_url(url: str | None) -> str:
            if not url:
                return "#"
            u = (url or "").strip().lower()
            if u.startswith("http://") or u.startswith("https://"):
                return html.escape(url)
            return "#"

        jobs_html = ""
        for m in matches[:10]:
            salary_str = ""
            if m.salary_min or m.salary_max:
                if m.salary_min and m.salary_max:
                    salary_str = f"${int(m.salary_min):,} - ${int(m.salary_max):,}"
                elif m.salary_max:
                    salary_str = f"Up to ${int(m.salary_max):,}"
                else:
                    salary_str = f"From ${int(m.salary_min):,}"

            safe_title = html.escape(str(m.title or ""))
            safe_company = html.escape(str(m.company or ""))
            safe_location = html.escape(str(m.location or "")) if m.location else ""
            safe_url = _safe_url(m.application_url)

            jobs_html += f"""
            <div style="border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px; margin: 12px 0;">
                <h3 style="margin: 0 0 8px; font-size: 16px;">{safe_title}</h3>
                <p style="margin: 0 0 4px; color: #64748B;">{safe_company}</p>
                {f'<p style="margin: 0 0 4px; color: #64748B;">{safe_location}</p>' if safe_location else ""}
                {f'<p style="margin: 0 0 8px; color: #10B981; font-weight: 600;">{salary_str}</p>' if salary_str else ""}
                <a href="{safe_url}" style="color: #3B82F6; text-decoration: none; font-weight: 600;">View Job →</a>
            </div>
            """

        more_count = len(matches) - 10 if len(matches) > 10 else 0
        more_html = (
            f'<p style="color: #64748B; text-align: center;">+ {more_count} more jobs</p>'
            if more_count > 0
            else ""
        )

        safe_alert_name = html.escape(str(alert.name or ""))

        return f"""
        <div style =
    "font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
    sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #1E293B;">
            <div style="text-align: center; margin-bottom: 24px;">
                <h1 style="color: #3B82F6; margin: 0; font-size: 24px;">JobHuntin</h1>
                <p style="color: #64748B; margin: 4px 0 0;">New Jobs Matching Your Alert</p>
            </div>

            <div style="background: #F1F5F9; border-radius: 12px; padding: 16px; margin: 20px 0; text-align: center;">
                <p style="margin: 0; font-size: 18px;"><strong>{safe_alert_name}</strong></p>
                <p style="margin: 4px 0 0; color: #64748B;">{len(matches)} new matching jobs</p>
            </div>

            {jobs_html}
            {more_html}

            <div style="text-align: center; margin: 30px 0;">
                <a href =
    "sorce://alerts/{alert.id}" style="background: #3B82F6; color: white; padding: 12px 24px; border-radius: 8px; text-d
    ecoration: none; font-weight: 600;">Manage Alert</a>
            </div>

            <p style="color: #94A3B8; font-size: 12px; text-align: center; margin-top: 40px;">
                You're receiving this because you created a job alert. <a href =
    "sorce://settings/alerts" style="color: #94A3B8;">Manage your alerts</a>
            </p>
        </div>
        """

    async def _log_alert_sent(
        self, conn: asyncpg.Connection, alert_id: str, matches: list[JobAlertMatch]
    ) -> None:
        await conn.execute(
            """
            INSERT INTO public.job_alert_log
                (alert_id, jobs_count, job_ids, sent_at)
            VALUES ($1, $2, $3::jsonb, now())
            """,
            alert_id,
            len(matches),
            json.dumps([m.model_dump() for m in matches]),
        )
