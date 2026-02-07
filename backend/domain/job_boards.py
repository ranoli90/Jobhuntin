"""
Integration with external job boards.
Currently supporting: Adzuna.
"""

from __future__ import annotations

import httpx
from typing import Any
from shared.config import Settings
from shared.logging_config import get_logger

logger = get_logger("sorce.job_boards")

class AdzunaClient:
    def __init__(self, settings: Settings):
        self.app_id = settings.adzuna_app_id
        self.api_key = settings.adzuna_api_key
        self.base_url = "https://api.adzuna.com/v1/api/jobs/us/search/1"

    async def fetch_jobs(
        self, 
        keywords: str | None = None, 
        location: str | None = None, 
        results_per_page: int = 50
    ) -> list[dict[str, Any]]:
        if not self.app_id or not self.api_key:
            logger.warning("Adzuna credentials not configured; returning empty results.")
            return []

        params = {
            "app_id": self.app_id,
            "app_key": self.api_key,
            "results_per_page": results_per_page,
            "content-type": "application/json",
        }
        if keywords:
            params["what"] = keywords
        if location:
            params["where"] = location

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(self.base_url, params=params, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                return data.get("results", [])
        except Exception as e:
            logger.error("Failed to fetch jobs from Adzuna: %s", e)
            return []

    def map_to_db(self, adzuna_job: dict[str, Any]) -> dict[str, Any]:
        """Map Adzuna API response to our public.jobs schema."""
        salary_min = adzuna_job.get("salary_min")
        salary_max = adzuna_job.get("salary_max")
        
        return {
            "external_id": f"adzuna:{adzuna_job.get('id')}",
            "title": adzuna_job.get("title", "Untitled Job"),
            "company": adzuna_job.get("company", {}).get("display_name", "Unknown Company"),
            "description": adzuna_job.get("description"),
            "location": adzuna_job.get("location", {}).get("display_name"),
            "salary_min": float(salary_min) if salary_min is not None else None,
            "salary_max": float(salary_max) if salary_max is not None else None,
            "category": adzuna_job.get("category", {}).get("label"),
            "application_url": adzuna_job.get("redirect_url"),
            "source": "adzuna",
            "raw_data": adzuna_job,
        }
