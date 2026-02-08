"""
Integration with external job boards.
Currently supporting: Adzuna.
"""

from __future__ import annotations

import httpx
from typing import Any
from shared.config import Settings
from shared.logging_config import get_logger
from shared.metrics import RateLimiter

logger = get_logger("sorce.job_boards")

class AdzunaClient:
    def __init__(self, settings: Settings):
        self.app_id = settings.adzuna_app_id
        self.api_key = settings.adzuna_api_key
        self.default_country = settings.adzuna_default_country or "us"
        self.additional_countries = [c.strip() for c in (settings.adzuna_additional_countries or "").split(",") if c.strip()]
        self.results_per_page = settings.adzuna_results_per_page
        self.max_pages = settings.adzuna_max_pages
        self.rate_limiter = RateLimiter(max_calls=settings.adzuna_rate_limit_per_minute, window_seconds=60)

    def _build_base_url(self, country: str) -> str:
        return f"https://api.adzuna.com/v1/api/jobs/{country}/search"

    async def fetch_jobs(
        self,
        keywords: str | None = None,
        location: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch jobs from Adzuna based on keywords and location."""
        if not self.app_id or not self.api_key:
            logger.warning("Adzuna credentials not configured; returning empty results.")
            return []

        results: list[dict[str, Any]] = []
        countries = [self.default_country, *self.additional_countries]

        async with httpx.AsyncClient() as client:
            for country in countries:
                for page in range(1, self.max_pages + 1):
                    if not self.rate_limiter.allow():
                        logger.warning("Adzuna rate limit reached, halting fetch loop")
                        return results

                    params = {
                        "app_id": self.app_id,
                        "app_key": self.api_key,
                        "results_per_page": self.results_per_page,
                        "content-type": "application/json",
                        "page": page,
                    }
                    if keywords:
                        params["what"] = keywords
                    if location:
                        params["where"] = location

                    url = f"{self._build_base_url(country)}/{page}"

                    try:
                        resp = await client.get(url, params=params, timeout=10)
                        resp.raise_for_status()
                        data = resp.json()
                        batch = data.get("results", [])
                        if not batch:
                            break
                        results.extend(batch)
                    except Exception as e:
                        logger.error("Failed to fetch jobs from Adzuna (%s page %s): %s", country, page, e)
                        break

        return results

    def map_to_db(self, adzuna_job: dict[str, Any]) -> dict[str, Any]:
        """Map Adzuna API response to our public.jobs schema."""
        salary_min = adzuna_job.get("salary_min")
        salary_max = adzuna_job.get("salary_max")
        location_info = adzuna_job.get("location") or {}
        location = location_info.get("display_name") or location_info.get("area") or ""
        if isinstance(location, list):
            location = ", ".join(location)

        description = adzuna_job.get("description", "")
        if len(description) > 10_000:
            description = description[:10_000]

        return {
            "external_id": f"adzuna:{adzuna_job.get('id')}",
            "title": adzuna_job.get("title", "Untitled Job"),
            "company": (adzuna_job.get("company") or {}).get("display_name", "Unknown Company"),
            "description": description,
            "location": location,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "category": (adzuna_job.get("category") or {}).get("label"),
            "application_url": adzuna_job.get("redirect_url"),
            "source": "adzuna",
            "raw_data": adzuna_job,
        }
