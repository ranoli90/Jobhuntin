"""Job deduplication utilities.

Deduplicates job listings from multiple sources (Adzuna, LinkedIn, Indeed, etc.)
based on title, company, and location similarity.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from typing import Any


@dataclass
class JobListing:
    """Normalized job listing for deduplication."""

    id: str
    title: str
    company: str
    location: str
    salary: str | None
    description: str
    url: str
    source: str
    posted_at: datetime | None = None
    normalized_title: str = ""
    normalized_company: str = ""
    normalized_location: str = ""
    fingerprint: str = ""


def normalize_text(text: str) -> str:
    """Normalize text for comparison: lowercase, remove punctuation, extra spaces."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_location(location: str) -> str:
    """Normalize location strings for comparison."""
    if not location:
        return ""

    location = location.lower().strip()

    # Common abbreviations
    replacements = {
        "remote": "remote",
        "work from home": "remote",
        "wfh": "remote",
        "san francisco": "sf",
        "new york": "nyc",
        "los angeles": "la",
        "united states": "us",
        "usa": "us",
        "united kingdom": "uk",
        "london, uk": "london",
        "london, united kingdom": "london",
    }

    for old, new in replacements.items():
        location = location.replace(old, new)

    # Remove state codes like "CA", "NY" at the end
    location = re.sub(r",?\s*[a-z]{2}\s*$", "", location)

    return normalize_text(location)


def normalize_company(company: str) -> str:
    """Normalize company names for comparison."""
    if not company:
        return ""

    company = company.lower().strip()

    # Remove common suffixes
    suffixes = [
        "inc", "inc.", "llc", "ltd", "ltd.", "corp", "corp.",
        "corporation", "company", "co", "co.", "limited",
    ]

    for suffix in suffixes:
        if company.endswith(f" {suffix}"):
            company = company[: -len(suffix) - 1]

    return normalize_text(company)


def normalize_title(title: str) -> str:
    """Normalize job titles for comparison."""
    if not title:
        return ""

    title = title.lower().strip()

    # Remove level indicators
    level_patterns = [
        r"\b(senior|sr\.?|junior|jr\.?|lead|principal|staff)\b",
        r"\b(i{1,3}|iv|v)\b",  # Roman numerals
    ]

    for pattern in level_patterns:
        title = re.sub(pattern, "", title)

    # Normalize common job types
    replacements = {
        "software engineer": "software engineer",
        "software developer": "software engineer",
        "full stack": "fullstack",
        "full-stack": "fullstack",
        "front end": "frontend",
        "front-end": "frontend",
        "back end": "backend",
        "back-end": "backend",
        "ml engineer": "machine learning engineer",
        "data scientist": "data scientist",
        "product manager": "product manager",
    }

    for old, new in replacements.items():
        title = title.replace(old, new)

    return normalize_text(title)


def generate_fingerprint(job: JobListing) -> str:
    """Generate a fingerprint for the job based on normalized fields."""
    data = f"{job.normalized_title}|{job.normalized_company}|{job.normalized_location}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def similarity_score(a: str, b: str) -> float:
    """Calculate similarity between two strings (0-1)."""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def jobs_are_similar(job1: JobListing, job2: JobListing, threshold: float = 0.85) -> bool:
    """Check if two jobs are similar enough to be considered duplicates."""
    # Exact fingerprint match
    if job1.fingerprint == job2.fingerprint:
        return True

    # Check individual field similarities
    title_sim = similarity_score(job1.normalized_title, job2.normalized_title)
    company_sim = similarity_score(job1.normalized_company, job2.normalized_company)
    location_sim = similarity_score(job1.normalized_location, job2.normalized_location)

    # Weighted combination
    combined = (title_sim * 0.5 + company_sim * 0.35 + location_sim * 0.15)

    return combined >= threshold


def normalize_job(raw_job: dict[str, Any], source: str) -> JobListing:
    """Convert a raw job dict to a normalized JobListing."""
    job = JobListing(
        id=str(raw_job.get("id", "")),
        title=raw_job.get("title", ""),
        company=raw_job.get("company", raw_job.get("company_name", "")),
        location=raw_job.get("location", raw_job.get("city", "")),
        salary=raw_job.get("salary", raw_job.get("salary_range", None)),
        description=raw_job.get("description", raw_job.get("snippet", "")),
        url=raw_job.get("url", raw_job.get("redirect_url", "")),
        source=source,
        posted_at=raw_job.get("posted_at", raw_job.get("created", None)),
    )

    # Normalize fields
    job.normalized_title = normalize_title(job.title)
    job.normalized_company = normalize_company(job.company)
    job.normalized_location = normalize_location(job.location)
    job.fingerprint = generate_fingerprint(job)

    return job


def deduplicate_jobs(
    jobs: list[dict[str, Any]],
    source: str = "unknown",
    existing_jobs: list[JobListing] | None = None,
) -> tuple[list[JobListing], list[JobListing]]:
    """Deduplicate a list of jobs.

    Returns:
        tuple of (unique_jobs, duplicate_jobs)

    """
    normalized = [normalize_job(job, source) for job in jobs]

    if existing_jobs is None:
        existing_jobs = []

    unique: list[JobListing] = []
    duplicates: list[JobListing] = []

    seen_fingerprints: set[str] = {job.fingerprint for job in existing_jobs}

    for job in normalized:
        # Quick fingerprint check
        if job.fingerprint in seen_fingerprints:
            duplicates.append(job)
            continue

        # Slower similarity check against existing unique jobs
        is_duplicate = False
        for existing in existing_jobs + unique:
            if jobs_are_similar(job, existing):
                is_duplicate = True
                break

        if is_duplicate:
            duplicates.append(job)
        else:
            unique.append(job)
            seen_fingerprints.add(job.fingerprint)

    return unique, duplicates


def merge_job_sources(
    sources: list[tuple[list[dict], str]],
) -> tuple[list[JobListing], dict[str, int]]:
    """Merge jobs from multiple sources with deduplication.

    Args:
        sources: List of (jobs_list, source_name) tuples

    Returns:
        tuple of (unique_jobs, stats_dict)

    """
    all_unique: list[JobListing] = []
    stats: dict[str, int] = {}

    for jobs, source in sources:
        unique, duplicates = deduplicate_jobs(jobs, source, all_unique)
        all_unique.extend(unique)
        stats[source] = {"total": len(jobs), "unique": len(unique), "duplicates": len(duplicates)}

    return all_unique, stats
