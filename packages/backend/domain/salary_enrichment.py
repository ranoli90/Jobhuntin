"""
Salary Enrichment — enrich job listings with salary data.

Provides:
- Salary estimation from job description
- Market rate lookup by role/location
- Salary range normalization
- Currency conversion
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from shared.config import get_settings
from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.salary_enrichment")


@dataclass
class SalaryRange:
    min_amount: float | None = None
    max_amount: float | None = None
    currency: str = "USD"
    period: str = "year"
    confidence: float = 0.0
    source: str = "unknown"


SALARY_PATTERNS = [
    (
        r"\$(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*[-–to]+\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(k|K)?",
        "range",
    ),
    (r"\$(\d{1,3}(?:,\d{3})*)\s*(?:per|/)?\s*(year|yr|annum|annual)", "annual"),
    (r"\$(\d{1,3}(?:,\d{3})*)\s*(?:per|/)?\s*(hour|hr)", "hourly"),
    (r"(\d{1,3}(?:,\d{3})*)\s*[-–]\s*(\d{1,3}(?:,\d{3})*)\s*(?:USD|dollars?)", "range"),
    (r"salary[:\s]+\$?(\d{1,3}(?:,\d{3})*)", "single"),
]

ROLE_SALARY_RANGES: dict[str, dict[str, Any]] = {
    "software engineer": {"min": 80000, "max": 200000, "median": 130000},
    "senior software engineer": {"min": 120000, "max": 250000, "median": 170000},
    "staff software engineer": {"min": 180000, "max": 350000, "median": 250000},
    "principal engineer": {"min": 200000, "max": 400000, "median": 300000},
    "frontend developer": {"min": 70000, "max": 150000, "median": 100000},
    "backend developer": {"min": 80000, "max": 180000, "median": 120000},
    "full stack developer": {"min": 80000, "max": 180000, "median": 120000},
    "devops engineer": {"min": 100000, "max": 200000, "median": 140000},
    "data scientist": {"min": 100000, "max": 200000, "median": 140000},
    "data engineer": {"min": 90000, "max": 180000, "median": 130000},
    "machine learning engineer": {"min": 120000, "max": 250000, "median": 170000},
    "product manager": {"min": 100000, "max": 200000, "median": 140000},
    "senior product manager": {"min": 140000, "max": 250000, "median": 180000},
    "ux designer": {"min": 70000, "max": 140000, "median": 100000},
    "ui designer": {"min": 65000, "max": 130000, "median": 95000},
    "qa engineer": {"min": 60000, "max": 120000, "median": 85000},
    "engineering manager": {"min": 150000, "max": 280000, "median": 200000},
    "cto": {"min": 200000, "max": 400000, "median": 280000},
    "marketing manager": {"min": 70000, "max": 140000, "median": 100000},
    "sales representative": {"min": 50000, "max": 120000, "median": 75000},
}

LOCATION_MULTIPLIERS: dict[str, float] = {
    "san francisco": 1.35,
    "new york": 1.25,
    "seattle": 1.20,
    "los angeles": 1.10,
    "boston": 1.15,
    "austin": 1.00,
    "denver": 0.95,
    "chicago": 0.95,
    "remote": 1.00,
    "dallas": 0.90,
    "miami": 0.95,
    "atlanta": 0.90,
}

HOURLY_TO_ANNUAL_HOURS = 2080


def parse_salary_from_text(text: str) -> SalaryRange | None:
    if not text:
        return None

    text_lower = text.lower()

    for pattern, pattern_type in SALARY_PATTERNS:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            groups = match.groups()

            if pattern_type == "range":
                min_val = float(groups[0].replace(",", ""))
                max_val = float(groups[1].replace(",", ""))

                if len(groups) > 2 and groups[2] and groups[2].lower() == "k":
                    min_val *= 1000
                    max_val *= 1000

                return SalaryRange(
                    min_amount=min_val,
                    max_amount=max_val,
                    confidence=0.9,
                    source="text_extraction",
                )

            elif pattern_type == "annual":
                amount = float(groups[0].replace(",", ""))
                return SalaryRange(
                    min_amount=amount * 0.9,
                    max_amount=amount * 1.1,
                    confidence=0.85,
                    source="text_extraction",
                )

            elif pattern_type == "hourly":
                hourly = float(groups[0].replace(",", ""))
                annual = hourly * HOURLY_TO_ANNUAL_HOURS
                return SalaryRange(
                    min_amount=annual * 0.9,
                    max_amount=annual * 1.1,
                    period="hour",
                    confidence=0.8,
                    source="text_extraction",
                )

            elif pattern_type == "single":
                amount = float(groups[0].replace(",", ""))
                return SalaryRange(
                    min_amount=amount * 0.85,
                    max_amount=amount * 1.15,
                    confidence=0.7,
                    source="text_extraction",
                )

    return None


def estimate_salary_from_role(
    title: str,
    location: str | None = None,
) -> SalaryRange | None:
    title_lower = title.lower()

    role_key = None
    for key in ROLE_SALARY_RANGES:
        if key in title_lower:
            role_key = key
            break

    if not role_key:
        for key in ROLE_SALARY_RANGES:
            words = key.split()
            if any(w in title_lower for w in words):
                role_key = key
                break

    if not role_key:
        return None

    salary_data = ROLE_SALARY_RANGES[role_key]
    min_sal = float(salary_data["min"])
    max_sal = float(salary_data["max"])

    location_multiplier = 1.0
    if location:
        location_lower = location.lower()
        for loc_key, mult in LOCATION_MULTIPLIERS.items():
            if loc_key in location_lower:
                location_multiplier = mult
                break

    return SalaryRange(
        min_amount=min_sal * location_multiplier,
        max_amount=max_sal * location_multiplier,
        confidence=0.6,
        source="role_estimation",
    )


def enrich_job_salary(
    job: dict[str, Any],
) -> dict[str, Any]:
    title = job.get("title", "")
    description = job.get("description", "")
    location = job.get("location", "")
    existing_min = job.get("salary_min")
    existing_max = job.get("salary_max")

    if existing_min and existing_max:
        return job

    text_salary = parse_salary_from_text(description or "")

    if text_salary:
        job["salary_min"] = (
            int(text_salary.min_amount) if text_salary.min_amount else None
        )
        job["salary_max"] = (
            int(text_salary.max_amount) if text_salary.max_amount else None
        )
        job["salary_confidence"] = text_salary.confidence
        job["salary_source"] = text_salary.source
        incr("salary_enrichment.text_extracted")
        return job

    estimated_salary = estimate_salary_from_role(title, location)

    if estimated_salary:
        job["salary_min"] = (
            int(estimated_salary.min_amount) if estimated_salary.min_amount else None
        )
        job["salary_max"] = (
            int(estimated_salary.max_amount) if estimated_salary.max_amount else None
        )
        job["salary_confidence"] = estimated_salary.confidence
        job["salary_source"] = estimated_salary.source
        incr("salary_enrichment.role_estimated")

    return job


def enrich_jobs_batch(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched = []
    for job in jobs:
        enriched.append(enrich_job_salary(job))
    return enriched


def normalize_salary_range(
    min_salary: float | None,
    max_salary: float | None,
    period: str = "year",
) -> dict[str, Any]:
    if not min_salary and not max_salary:
        return {"min": None, "max": None, "midpoint": None, "range": None}

    min_val = min_salary or max_salary or 0
    max_val = max_salary or min_salary or 0

    if period == "hour":
        min_val *= HOURLY_TO_ANNUAL_HOURS
        max_val *= HOURLY_TO_ANNUAL_HOURS
    elif period == "month":
        min_val *= 12
        max_val *= 12

    midpoint = (min_val + max_val) / 2
    range_val = max_val - min_val if max_val > min_val else 0

    return {
        "min": int(min_val),
        "max": int(max_val),
        "midpoint": int(midpoint),
        "range": int(range_val),
        "formatted": f"${int(min_val):,} - ${int(max_val):,}",
    }
