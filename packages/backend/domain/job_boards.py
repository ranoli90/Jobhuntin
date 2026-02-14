"""
Integration with external job boards.
Currently supporting: Adzuna, LinkedIn, Indeed, Glassdoor.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import httpx

from shared.config import Settings
from shared.logging_config import get_logger
from shared.metrics import RateLimiter, incr

logger = get_logger("sorce.job_boards")


class JobBoardClient(ABC):
    @abstractmethod
    async def fetch_jobs(
        self,
        keywords: str | None = None,
        location: str | None = None,
    ) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    def map_to_db(self, job: dict[str, Any]) -> dict[str, Any]:
        pass


class AdzunaClient(JobBoardClient):
    def __init__(self, settings: Settings):
        self.app_id = settings.adzuna_app_id
        self.api_key = settings.adzuna_api_key
        self.default_country = settings.adzuna_default_country or "us"
        self.additional_countries = [
            c.strip()
            for c in (settings.adzuna_additional_countries or "").split(",")
            if c.strip()
        ]
        self.results_per_page = settings.adzuna_results_per_page
        self.max_pages = settings.adzuna_max_pages
        self.rate_limiter = RateLimiter(
            max_calls=settings.adzuna_rate_limit_per_minute, window_seconds=60
        )

    def _build_base_url(self, country: str) -> str:
        return f"https://api.adzuna.com/v1/api/jobs/{country}/search"

    async def fetch_jobs(
        self,
        keywords: str | None = None,
        location: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch jobs from Adzuna based on keywords and location."""
        if not self.app_id or not self.api_key:
            logger.warning(
                "Adzuna credentials not configured; returning empty results."
            )
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
                        logger.error(
                            "Failed to fetch jobs from Adzuna (%s page %s): %s",
                            country,
                            page,
                            e,
                        )
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
            "company": (adzuna_job.get("company") or {}).get(
                "display_name", "Unknown Company"
            ),
            "description": description,
            "location": location,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "category": (adzuna_job.get("category") or {}).get("label"),
            "application_url": adzuna_job.get("redirect_url"),
            "source": "adzuna",
            "raw_data": adzuna_job,
        }


class IndeedClient(JobBoardClient):
    def __init__(self, settings: Settings):
        self.publisher_id = getattr(settings, "indeed_publisher_id", "")
        self.rate_limiter = RateLimiter(max_calls=30, window_seconds=60)

    async def fetch_jobs(
        self,
        keywords: str | None = None,
        location: str | None = None,
    ) -> list[dict[str, Any]]:
        if not self.publisher_id:
            logger.warning("Indeed publisher ID not configured")
            return []

        results: list[dict[str, Any]] = []
        base_url = "https://api.indeed.com/ads/apisearch"

        async with httpx.AsyncClient() as client:
            params = {
                "publisher": self.publisher_id,
                "v": "2",
                "format": "json",
                "q": keywords or "",
                "l": location or "",
                "limit": 25,
                "co": "us",
            }

            try:
                resp = await client.get(base_url, params=params, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                results = data.get("results", [])
                incr("job_board.indeed.fetched", value=len(results))
            except Exception as e:
                logger.error("Indeed fetch failed: %s", e)

        return results

    def map_to_db(self, indeed_job: dict[str, Any]) -> dict[str, Any]:
        return {
            "external_id": f"indeed:{indeed_job.get('jobkey', '')}",
            "title": indeed_job.get("jobtitle", "Untitled Job"),
            "company": indeed_job.get("company", "Unknown Company"),
            "description": indeed_job.get("snippet", "")[:10_000],
            "location": indeed_job.get("formattedLocation", ""),
            "salary_min": None,
            "salary_max": None,
            "category": None,
            "application_url": indeed_job.get("url"),
            "source": "indeed",
            "raw_data": indeed_job,
        }


class LinkedInClient(JobBoardClient):
    def __init__(self, settings: Settings):
        self.client_id = getattr(settings, "linkedin_client_id", "")
        self.client_secret = getattr(settings, "linkedin_client_secret", "")
        self.rate_limiter = RateLimiter(max_calls=20, window_seconds=60)

    async def fetch_jobs(
        self,
        keywords: str | None = None,
        location: str | None = None,
    ) -> list[dict[str, Any]]:
        if not self.client_id:
            logger.warning("LinkedIn client ID not configured")
            return []

        results: list[dict[str, Any]] = []
        base_url = "https://api.linkedin.com/v2/jobSearch"

        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {self.client_secret}"}
            params = {
                "keywords": keywords or "",
                "location": location or "",
                "count": 25,
            }

            try:
                resp = await client.get(
                    base_url, headers=headers, params=params, timeout=10
                )
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("elements", [])
                    incr("job_board.linkedin.fetched", value=len(results))
            except Exception as e:
                logger.error("LinkedIn fetch failed: %s", e)

        return results

    def map_to_db(self, linkedin_job: dict[str, Any]) -> dict[str, Any]:
        return {
            "external_id": f"linkedin:{linkedin_job.get('id', '')}",
            "title": linkedin_job.get("title", "Untitled Job"),
            "company": linkedin_job.get("companyName", "Unknown Company"),
            "description": (linkedin_job.get("description") or "")[:10_000],
            "location": linkedin_job.get("formattedLocation", ""),
            "salary_min": None,
            "salary_max": None,
            "category": None,
            "application_url": linkedin_job.get("applyUrl"),
            "source": "linkedin",
            "raw_data": linkedin_job,
        }


class GlassdoorClient(JobBoardClient):
    def __init__(self, settings: Settings):
        self.partner_id = getattr(settings, "glassdoor_partner_id", "")
        self.api_key = getattr(settings, "glassdoor_api_key", "")
        self.rate_limiter = RateLimiter(max_calls=20, window_seconds=60)

    async def fetch_jobs(
        self,
        keywords: str | None = None,
        location: str | None = None,
    ) -> list[dict[str, Any]]:
        if not self.partner_id:
            logger.warning("Glassdoor partner ID not configured")
            return []

        results: list[dict[str, Any]] = []
        base_url = "https://api.glassdoor.com/api/api.htm"

        async with httpx.AsyncClient() as client:
            params = {
                "v": "1",
                "format": "json",
                "t.p": self.partner_id,
                "t.k": self.api_key,
                "userip": "0.0.0.0",
                "useragent": "SorceBot/1.0",
                "action": "jobs",
                "q": keywords or "",
                "l": location or "",
            }

            try:
                resp = await client.get(base_url, params=params, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("response", {}).get("jobListings", [])
                    incr("job_board.glassdoor.fetched", value=len(results))
            except Exception as e:
                logger.error("Glassdoor fetch failed: %s", e)

        return results

    def map_to_db(self, glassdoor_job: dict[str, Any]) -> dict[str, Any]:
        return {
            "external_id": f"glassdoor:{glassdoor_job.get('jobListingId', '')}",
            "title": glassdoor_job.get("jobTitle", "Untitled Job"),
            "company": glassdoor_job.get("employer", {}).get("name", "Unknown Company"),
            "description": glassdoor_job.get("description", "")[:10_000],
            "location": glassdoor_job.get("location", ""),
            "salary_min": None,
            "salary_max": None,
            "category": None,
            "application_url": glassdoor_job.get("jobViewUrl"),
            "source": "glassdoor",
            "raw_data": glassdoor_job,
        }


def get_job_board_clients(settings: Settings) -> list[JobBoardClient]:
    clients: list[JobBoardClient] = []

    if settings.adzuna_app_id and settings.adzuna_api_key:
        clients.append(AdzunaClient(settings))

    indeed = IndeedClient(settings)
    if indeed.publisher_id:
        clients.append(indeed)

    linkedin = LinkedInClient(settings)
    if linkedin.client_id:
        clients.append(linkedin)

    glassdoor = GlassdoorClient(settings)
    if glassdoor.partner_id:
        clients.append(glassdoor)

    return clients


async def fetch_all_jobs(
    settings: Settings,
    keywords: str | None = None,
    location: str | None = None,
) -> list[dict[str, Any]]:
    clients = get_job_board_clients(settings)
    all_jobs: list[dict[str, Any]] = []

    for client in clients:
        try:
            jobs = await client.fetch_jobs(keywords, location)
            for job in jobs:
                mapped = client.map_to_db(job)
                all_jobs.append(mapped)
        except Exception as e:
            logger.error("Failed to fetch from job board: %s", e)

    incr("job_board.total_fetched", value=len(all_jobs))
    return all_jobs
