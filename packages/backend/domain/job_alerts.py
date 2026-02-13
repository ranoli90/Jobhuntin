"""
Job alert service for daily/weekly job notification emails.

This addresses recommendation #42: Implement daily/weekly job alert emails.

Features:
- User-configurable alert frequency (daily, weekly)
- Match score threshold filtering
- Location and job type preferences
- Email digest generation via Resend
- Scheduled job for alert processing
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

import asyncpg

from shared.config import Settings, get_settings
from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.job_alerts")


class AlertFrequency(StrEnum):
    """Frequency for job alerts."""
    DAILY = "daily"
    WEEKLY = "weekly"
    NEVER = "never"


@dataclass
class JobAlertPreferences:
    """User preferences for job alerts."""
    user_id: str
    frequency: AlertFrequency = AlertFrequency.DAILY
    min_match_score: float = 0.7
    locations: list[str] = field(default_factory=list)
    job_types: list[str] = field(default_factory=list)  # full-time, part-time, contract
    categories: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    excluded_companies: list[str] = field(default_factory=list)
    min_salary: int | None = None
    remote_only: bool = False
    last_sent_at: datetime | None = None
    is_active: bool = True


@dataclass
class JobAlertItem:
    """A single job to include in an alert."""
    job_id: str
    title: str
    company: str
    location: str
    salary_range: str | None
    match_score: float
    match_reasons: list[str]
    posted_at: datetime
    job_url: str


@dataclass
class JobAlertDigest:
    """Digest of jobs for a user alert."""
    user_id: str
    email: str
    frequency: AlertFrequency
    jobs: list[JobAlertItem]
    total_matches: int
    digest_period_start: datetime
    digest_period_end: datetime
    unsubscribe_url: str


class JobAlertService:
    """
    Service for managing and sending job alerts.
    """

    def __init__(self, db_pool: asyncpg.Pool, settings: Settings | None = None) -> None:
        self._pool = db_pool
        self._settings = settings or get_settings()

    async def get_user_preferences(self, user_id: str) -> JobAlertPreferences | None:
        """Get alert preferences for a user."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    user_id, frequency, min_match_score, locations, job_types,
                    categories, keywords, excluded_companies, min_salary,
                    remote_only, last_sent_at, is_active
                FROM public.job_alert_preferences
                WHERE user_id = $1
                """,
                user_id,
            )
            if not row:
                return None

            return JobAlertPreferences(
                user_id=row["user_id"],
                frequency=AlertFrequency(row["frequency"] or "daily"),
                min_match_score=row["min_match_score"] or 0.7,
                locations=json.loads(row["locations"]) if row["locations"] else [],
                job_types=json.loads(row["job_types"]) if row["job_types"] else [],
                categories=json.loads(row["categories"]) if row["categories"] else [],
                keywords=json.loads(row["keywords"]) if row["keywords"] else [],
                excluded_companies=json.loads(row["excluded_companies"]) if row["excluded_companies"] else [],
                min_salary=row["min_salary"],
                remote_only=row["remote_only"] or False,
                last_sent_at=row["last_sent_at"],
                is_active=row["is_active"],
            )

    async def save_user_preferences(self, prefs: JobAlertPreferences) -> None:
        """Save or update alert preferences for a user."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO public.job_alert_preferences (
                    user_id, frequency, min_match_score, locations, job_types,
                    categories, keywords, excluded_companies, min_salary,
                    remote_only, is_active, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, now())
                ON CONFLICT (user_id) DO UPDATE SET
                    frequency = $2,
                    min_match_score = $3,
                    locations = $4,
                    job_types = $5,
                    categories = $6,
                    keywords = $7,
                    excluded_companies = $8,
                    min_salary = $9,
                    remote_only = $10,
                    is_active = $11,
                    updated_at = now()
                """,
                prefs.user_id,
                prefs.frequency.value,
                prefs.min_match_score,
                json.dumps(prefs.locations),
                json.dumps(prefs.job_types),
                json.dumps(prefs.categories),
                json.dumps(prefs.keywords),
                json.dumps(prefs.excluded_companies),
                prefs.min_salary,
                prefs.remote_only,
                prefs.is_active,
            )

    async def find_matching_jobs(
        self,
        prefs: JobAlertPreferences,
        since: datetime,
        limit: int = 20,
    ) -> list[JobAlertItem]:
        """Find jobs matching user preferences since the given time."""
        async with self._pool.acquire() as conn:
            # Build query with filters
            conditions = ["j.created_at > $1", "j.is_active = true"]
            params: list[Any] = [since]
            param_idx = 2

            # Location filter
            if prefs.locations:
                conditions.append(
                    f"LOWER(j.location) LIKE ANY(${param_idx}::text[])"
                )
                params.append([f"%{loc.lower()}%" for loc in prefs.locations])
                param_idx += 1

            # Remote filter
            if prefs.remote_only:
                conditions.append("LOWER(j.location) LIKE '%remote%'")

            # Job type filter
            if prefs.job_types:
                conditions.append(f"j.job_type = ANY(${param_idx}::text[])")
                params.append(prefs.job_types)
                param_idx += 1

            # Category filter
            if prefs.categories:
                conditions.append(f"j.category = ANY(${param_idx}::text[])")
                params.append(prefs.categories)
                param_idx += 1

            # Salary filter
            if prefs.min_salary:
                conditions.append(
                    f"(j.salary_max >= ${param_idx} OR j.salary_min >= ${param_idx})"
                )
                params.append(prefs.min_salary)
                param_idx += 1

            # Exclude companies
            if prefs.excluded_companies:
                conditions.append(
                    f"LOWER(j.company) NOT LIKE ALL(${param_idx}::text[])"
                )
                params.append([f"%{c.lower()}%" for c in prefs.excluded_companies])
                param_idx += 1

            # Add limit
            params.append(limit)

            query = f"""
                SELECT 
                    j.id, j.title, j.company, j.location,
                    j.salary_min, j.salary_max, j.created_at,
                    COALESCE(m.score, 0.5) as match_score,
                    m.explanation->>'reasoning' as match_reasoning
                FROM public.jobs j
                LEFT JOIN public.job_match_scores m 
                    ON m.job_id = j.id AND m.user_id = ${param_idx}
                WHERE {' AND '.join(conditions)}
                ORDER BY match_score DESC, j.created_at DESC
                LIMIT ${param_idx + 1}
            """

            # Add user_id for match scores
            params.insert(param_idx - 1, prefs.user_id)

            rows = await conn.fetch(query, *params)

            return [
                JobAlertItem(
                    job_id=row["id"],
                    title=row["title"],
                    company=row["company"],
                    location=row["location"],
                    salary_range=self._format_salary(row["salary_min"], row["salary_max"]),
                    match_score=float(row["match_score"] or 0.5),
                    match_reasons=[row["match_reasoning"]] if row["match_reasoning"] else [],
                    posted_at=row["created_at"],
                    job_url=f"{self._settings.app_base_url}/jobs/{row['id']}",
                )
                for row in rows
                if float(row["match_score"] or 0.5) >= prefs.min_match_score
            ]

    async def get_users_due_for_alert(
        self,
        frequency: AlertFrequency,
    ) -> list[dict[str, Any]]:
        """Get users who are due for an alert based on frequency."""
        async with self._pool.acquire() as conn:
            if frequency == AlertFrequency.DAILY:
                interval = timedelta(hours=20)  # Send if last sent > 20 hours ago
            else:
                interval = timedelta(days=6)  # Send if last sent > 6 days ago

            cutoff = datetime.now(UTC) - interval

            rows = await conn.fetch(
                """
                SELECT 
                    jap.user_id, jap.frequency, jap.min_match_score,
                    jap.locations, jap.job_types, jap.categories,
                    jap.keywords, jap.excluded_companies, jap.min_salary,
                    jap.remote_only, jap.last_sent_at,
                    u.email
                FROM public.job_alert_preferences jap
                JOIN public.users u ON u.id = jap.user_id
                WHERE jap.is_active = true
                    AND jap.frequency = $1
                    AND (jap.last_sent_at IS NULL OR jap.last_sent_at < $2)
                """,
                frequency.value,
                cutoff,
            )
            return [dict(r) for r in rows]

    async def send_alert_email(self, digest: JobAlertDigest) -> bool:
        """Send job alert email via Resend."""
        if not self._settings.resend_api_key:
            logger.warning("Resend API key not configured, skipping alert email")
            return False

        import httpx

        # Build email content
        subject = self._build_subject(digest)
        html_content = self._build_html_email(digest)
        text_content = self._build_text_email(digest)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {self._settings.resend_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": self._settings.email_from,
                        "to": digest.email,
                        "subject": subject,
                        "html": html_content,
                        "text": text_content,
                        "tags": [
                            {"name": "type", "value": "job_alert"},
                            {"name": "frequency", "value": digest.frequency.value},
                        ],
                    },
                )
                if resp.status_code not in (200, 201):
                    logger.error(
                        "Failed to send job alert email: %s - %s",
                        resp.status_code,
                        resp.text,
                    )
                    return False

                incr("job_alerts.sent", {"frequency": digest.frequency.value})
                logger.info(
                    "Sent job alert to %s with %d jobs",
                    digest.email,
                    len(digest.jobs),
                )
                return True

        except Exception as exc:
            logger.error("Error sending job alert email: %s", exc)
            return False

    async def mark_alert_sent(self, user_id: str) -> None:
        """Mark that an alert was sent to a user."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE public.job_alert_preferences
                SET last_sent_at = now()
                WHERE user_id = $1
                """,
                user_id,
            )

    async def process_alerts(self, frequency: AlertFrequency) -> dict[str, int]:
        """
        Process all pending alerts for a frequency.
        
        Returns stats about processed alerts.
        """
        users = await self.get_users_due_for_alert(frequency)
        
        sent_count = 0
        skipped_count = 0
        error_count = 0

        for user in users:
            try:
                prefs = JobAlertPreferences(
                    user_id=user["user_id"],
                    frequency=AlertFrequency(user["frequency"] or "daily"),
                    min_match_score=user["min_match_score"] or 0.7,
                    locations=json.loads(user["locations"]) if user["locations"] else [],
                    job_types=json.loads(user["job_types"]) if user["job_types"] else [],
                    categories=json.loads(user["categories"]) if user["categories"] else [],
                    keywords=json.loads(user["keywords"]) if user["keywords"] else [],
                    excluded_companies=json.loads(user["excluded_companies"]) if user["excluded_companies"] else [],
                    min_salary=user["min_salary"],
                    remote_only=user["remote_only"] or False,
                    last_sent_at=user["last_sent_at"],
                )

                # Determine time range
                if prefs.last_sent_at:
                    since = prefs.last_sent_at
                else:
                    since = datetime.now(UTC) - (
                        timedelta(days=1) if frequency == AlertFrequency.DAILY 
                        else timedelta(days=7)
                    )

                # Find matching jobs
                jobs = await self.find_matching_jobs(prefs, since)

                if not jobs:
                    skipped_count += 1
                    continue

                # Create and send digest
                digest = JobAlertDigest(
                    user_id=prefs.user_id,
                    email=user["email"],
                    frequency=prefs.frequency,
                    jobs=jobs,
                    total_matches=len(jobs),
                    digest_period_start=since,
                    digest_period_end=datetime.now(UTC),
                    unsubscribe_url=f"{self._settings.app_base_url}/settings?tab=alerts",
                )

                if await self.send_alert_email(digest):
                    await self.mark_alert_sent(prefs.user_id)
                    sent_count += 1
                else:
                    error_count += 1

            except Exception as exc:
                logger.error("Error processing alert for user %s: %s", user["user_id"], exc)
                error_count += 1

        return {
            "sent": sent_count,
            "skipped": skipped_count,
            "errors": error_count,
            "total_users": len(users),
        }

    def _format_salary(self, salary_min: int | None, salary_max: int | None) -> str | None:
        """Format salary range for display."""
        if not salary_min and not salary_max:
            return None
        if salary_min and salary_max:
            return f"${salary_min:,} - ${salary_max:,}"
        if salary_min:
            return f"${salary_min:,}+"
        return f"Up to ${salary_max:,}"

    def _build_subject(self, digest: JobAlertDigest) -> str:
        """Build email subject line."""
        count = len(digest.jobs)
        if count == 1:
            return "🎯 1 New Job Match Found!"
        return f"🎯 {count} New Job Matches Found!"

    def _build_html_email(self, digest: JobAlertDigest) -> str:
        """Build HTML email content."""
        jobs_html = ""
        for job in digest.jobs[:10]:  # Limit to 10 jobs in email
            jobs_html += f"""
                <div style="margin-bottom: 20px; padding: 15px; border: 1px solid #e0e0e0; border-radius: 8px;">
                    <h3 style="margin: 0 0 5px 0;">
                        <a href="{job.job_url}" style="color: #0066cc; text-decoration: none;">
                            {job.title}
                        </a>
                    </h3>
                    <p style="margin: 0 0 5px 0; color: #666;">
                        {job.company} • {job.location}
                    </p>
                    {f'<p style="margin: 0 0 5px 0; color: #28a745;">{job.salary_range}</p>' if job.salary_range else ''}
                    <p style="margin: 0 0 5px 0;">
                        <span style="background: #e8f5e9; padding: 2px 8px; border-radius: 4px; font-size: 12px;">
                            {job.match_score:.0%} Match
                        </span>
                    </p>
                </div>
            """

        return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #333;">🎯 Your Job Matches</h1>
                <p style="color: #666;">
                    We found {digest.total_matches} new job{'s' if digest.total_matches != 1 else ''} 
                    matching your preferences:
                </p>
                {jobs_html}
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #e0e0e0;">
                <p style="color: #999; font-size: 12px;">
                    You're receiving this because you enabled {digest.frequency.value} job alerts.
                    <br>
                    <a href="{digest.unsubscribe_url}">Manage alert preferences</a>
                </p>
            </body>
            </html>
        """

    def _build_text_email(self, digest: JobAlertDigest) -> str:
        """Build plain text email content."""
        jobs_text = ""
        for job in digest.jobs[:10]:
            jobs_text += f"""
{job.title}
{job.company} • {job.location}
{f'{job.salary_range}' if job.salary_range else ''}
Match Score: {job.match_score:.0%}
Link: {job.job_url}

"""
        return f"""
Your Job Matches

We found {digest.total_matches} new job{'s' if digest.total_matches != 1 else ''} 
matching your preferences:

{jobs_text}

---
You're receiving this because you enabled {digest.frequency.value} job alerts.
Manage preferences: {digest.unsubscribe_url}
"""
