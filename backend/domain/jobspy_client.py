"""
JobSpy integration client for multi-source job aggregation.
Wraps the python-jobspy library with async support and error handling.
"""

from __future__ import annotations

import asyncio
import hashlib
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from functools import partial
from typing import Any

from shared.config import get_settings
from shared.logging_config import get_logger

from shared.metrics import incr, observe

logger = get_logger("sorce.jobspy")

_executor: ThreadPoolExecutor | None = None


def _get_executor() -> ThreadPoolExecutor:
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="jobspy-")
    return _executor


@dataclass
class ScrapingResult:
    """Result of a scraping operation for a single source."""

    source: str
    success: bool
    jobs: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    duration_ms: int = 0
    rate_limited: bool = False


class JobSpyError(Exception):
    """Base exception for JobSpy errors."""

    pass


class JobSpyClient:
    """Async wrapper for JobSpy scraping library with circuit breaker support."""

    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self.sources = self._parse_sources()
        self.proxies = self._parse_proxies()
        self._circuit_breaker_state: dict[str, dict] = {}

    def _parse_sources(self) -> list[str]:
        if not getattr(self.settings, "jobspy_enabled", True):
            return []
        sources_str = getattr(
            self.settings, "jobspy_sources", "indeed,linkedin,zip_recruiter,glassdoor"
        )
        return [s.strip().lower() for s in sources_str.split(",") if s.strip()]

    def _parse_proxies(self) -> list[str]:
        proxies_str = getattr(self.settings, "jobspy_proxies", "")
        if not proxies_str:
            return []
        return [p.strip() for p in proxies_str.split(",") if p.strip()]

    def _get_proxy(self) -> str | None:
        if not self.proxies:
            return None
        return self.proxies[0]

    def _is_circuit_open(self, source: str) -> bool:
        if source not in self._circuit_breaker_state:
            return False
        state = self._circuit_breaker_state[source]
        if state["status"] != "open":
            return False
        if time.time() - state["opened_at"] > 300:
            state["status"] = "half-open"
            return False
        return True

    def _record_failure(self, source: str):
        if source not in self._circuit_breaker_state:
            self._circuit_breaker_state[source] = {
                "failures": 0,
                "status": "closed",
                "opened_at": 0,
            }
        self._circuit_breaker_state[source]["failures"] += 1
        if self._circuit_breaker_state[source]["failures"] >= 5:
            self._circuit_breaker_state[source]["status"] = "open"
            self._circuit_breaker_state[source]["opened_at"] = time.time()
            logger.warning(f"Circuit breaker opened for {source}")

    def _record_success(self, source: str):
        if source in self._circuit_breaker_state:
            self._circuit_breaker_state[source]["failures"] = 0
            self._circuit_breaker_state[source]["status"] = "closed"

    async def fetch_jobs(
        self,
        search_term: str,
        location: str | None = None,
        results_wanted: int | None = None,
        hours_old: int | None = None,
        sources: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Fetch jobs from multiple sources asynchronously.
        """
        results_wanted = results_wanted or getattr(
            self.settings, "jobspy_results_per_source", 50
        )
        hours_old = hours_old or getattr(self.settings, "jobspy_hours_old", 168)
        sources = [s for s in (sources or self.sources) if not self._is_circuit_open(s)]

        if not sources:
            logger.warning("All sources have circuit breakers open")
            return []

        loop = asyncio.get_running_loop()
        executor = _get_executor()

        func = partial(
            self._scrape_sync,
            site_name=sources,
            search_term=search_term,
            location=location,
            results_wanted=results_wanted,
            hours_old=hours_old,
            proxies=self._get_proxy(),
            linkedin_fetch_description=getattr(
                self.settings, "jobspy_linkedin_fetch_description", True
            ),
        )

        start_time = time.time()
        try:
            df = await loop.run_in_executor(executor, func)
            jobs = self._normalize_jobs(df)
            duration_ms = int((time.time() - start_time) * 1000)

            incr("jobspy.jobs_fetched", len(jobs))
            observe("jobspy.fetch_duration_ms", duration_ms)

            for source in sources:
                self._record_success(source)

            return jobs

        except Exception as e:
            error_msg = str(e)
            logger.error(f"JobSpy fetch failed: {error_msg}")

            if "429" in error_msg or "rate" in error_msg.lower():
                for source in sources:
                    self._record_failure(source)
                incr("jobspy.rate_limited")

            incr("jobspy.fetch_failed")
            raise JobSpyError(f"Failed to fetch jobs: {error_msg}")

    def _scrape_sync(self, **kwargs) -> Any:
        """Synchronous scrape call (runs in thread pool)."""
        from jobspy import scrape_jobs

        return scrape_jobs(**kwargs)

    def _normalize_jobs(self, df) -> list[dict[str, Any]]:
        """Normalize JobSpy DataFrame to list of dicts."""
        if df is None or df.empty:
            return []

        jobs = []
        for _, row in df.iterrows():
            try:
                job = self._normalize_job(row)
                if job:
                    jobs.append(job)
            except Exception as e:
                logger.warning(f"Failed to normalize job row: {e}")
                continue
        return jobs

    def _normalize_job(self, row) -> dict[str, Any] | None:
        """Normalize a single job row to database schema."""
        import math

        def clean_val(v):
            """Clean a value, handling NaN."""
            if v is None:
                return None
            if isinstance(v, float) and math.isnan(v):
                return None
            if str(v).lower() == "nan":
                return None
            return v

        source = str(clean_val(row.get("site")) or "unknown").lower()
        if source == "zip_recruiter":
            source = "zip_recruiter"

        job_url = str(clean_val(row.get("job_url")) or "")
        if not job_url:
            return None

        external_id = self._generate_external_id(source, job_url, row)
        location = self._build_location(row)
        salary_min, salary_max = self._parse_salary(row)

        max_desc_len = getattr(self.settings, "jobspy_description_max_length", 50000)
        description = str(clean_val(row.get("description")) or "")[:max_desc_len]

        raw_data = {}
        try:
            for k, v in dict(row).items():
                cleaned = clean_val(v)
                if cleaned is not None:
                    if isinstance(cleaned, (datetime,)):
                        raw_data[k] = cleaned.isoformat()
                    elif isinstance(cleaned, (list, dict)):
                        raw_data[k] = cleaned
                    else:
                        raw_data[k] = str(cleaned)
        except Exception:
            pass

        return {
            "external_id": external_id,
            "title": str(clean_val(row.get("title")) or "Untitled")[:500],
            "company": str(clean_val(row.get("company")) or "Unknown Company")[:255],
            "description": description,
            "location": location,
            "is_remote": bool(clean_val(row.get("is_remote")) or False),
            "job_type": self._normalize_job_type(clean_val(row.get("job_type"))),
            "salary_min": salary_min,
            "salary_max": salary_max,
            "application_url": job_url,
            "source": source,
            "date_posted": clean_val(row.get("date_posted")),
            "job_level": str(clean_val(row.get("job_level")) or "")[:50] or None,
            "company_industry": str(clean_val(row.get("company_industry")) or "")[:100]
            or None,
            "company_logo_url": clean_val(row.get("company_logo")),
            "emails": list(clean_val(row.get("emails")) or []),
            "raw_data": raw_data,
        }

    def _generate_external_id(self, source: str, job_url: str, row) -> str:
        """Generate a unique external ID for the job."""
        import re

        if source == "linkedin":
            match = re.search(r"/jobs/view/(\d+)", job_url)
            if match:
                return f"linkedin:{match.group(1)}"
        elif source == "indeed":
            # Indeed uses 'id' column
            job_id = row.get("id")
            if job_id:
                return f"indeed:{job_id}"

        url_hash = hashlib.sha256(job_url.encode()).hexdigest()[:16]
        return f"{source}:{url_hash}"

    def _build_location(self, row) -> str | None:
        """Build location string from row data."""
        # JobSpy returns location as a single string
        location = row.get("location")
        if location:
            return str(location)
        return None

    def _parse_salary(self, row) -> tuple[int | None, int | None]:
        """Parse and normalize salary from row."""
        import math

        def clean_num(v):
            if v is None:
                return None
            if isinstance(v, float) and math.isnan(v):
                return None
            if str(v).lower() == "nan":
                return None
            return v

        salary_min = clean_num(row.get("min_amount"))
        salary_max = clean_num(row.get("max_amount"))
        interval = clean_num(row.get("interval")) or "yearly"

        try:
            salary_min = int(float(salary_min)) if salary_min else None
        except (ValueError, TypeError):
            salary_min = None
        try:
            salary_max = int(float(salary_max)) if salary_max else None
        except (ValueError, TypeError):
            salary_max = None

        if interval == "hourly":
            if salary_min:
                salary_min = int(salary_min * 2080)
            if salary_max:
                salary_max = int(salary_max * 2080)
        elif interval == "weekly":
            if salary_min:
                salary_min = int(salary_min * 52)
            if salary_max:
                salary_max = int(salary_max * 52)
        elif interval == "monthly":
            if salary_min:
                salary_min = int(salary_min * 12)
            if salary_max:
                salary_max = int(salary_max * 12)

        return salary_min, salary_max

    def _normalize_job_type(self, job_type: Any) -> str | None:
        """Normalize job type to standard values."""
        if not job_type:
            return None
        job_type = str(job_type).lower().strip()
        mapping = {
            "fulltime": "fulltime",
            "full-time": "fulltime",
            "full time": "fulltime",
            "parttime": "parttime",
            "part-time": "parttime",
            "part time": "parttime",
            "contract": "contract",
            "contractor": "contract",
            "internship": "internship",
            "intern": "internship",
            "temporary": "contract",
        }
        return mapping.get(job_type, job_type[:50] if job_type else None)
