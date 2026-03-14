"""Duplicate Job Detection Module.

Provides advanced duplicate detection for job listings.
Identifies duplicate jobs using multiple similarity metrics including
title/company hashing, description similarity, URL normalization,
and location/salary comparison.

This module integrates with the quality control fields added by the
migrations/035_job_quality_fields.sql migration, specifically the
canonical_job_id field for tracking duplicate groups.

Similarity Thresholds:
- Exact duplicate: >95% similarity
- Likely duplicate: >80% similarity
- Possible duplicate: >60% similarity
"""

from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from urllib.parse import urlparse

from shared.logging_config import get_logger

logger = get_logger("sorce.duplicate_job_detector")


# ============================================================================
# Similarity Thresholds
# ============================================================================

EXACT_DUPLICATE_THRESHOLD: float = 0.95
LIKELY_DUPLICATE_THRESHOLD: float = 0.80
POSSIBLE_DUPLICATE_THRESHOLD: float = 0.60


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class DuplicateMatch:
    """Represents a duplicate job match result."""

    job_id: str
    similarity_score: float
    match_type: str  # "exact", "likely", "possible"
    match_reasons: list[str] = field(default_factory=list)
    canonical_job_id: str | None = None


@dataclass
class DuplicateCheckResult:
    """Result of a duplicate check for a job."""

    is_duplicate: bool
    duplicate_type: str | None  # "exact", "likely", "possible", None
    similarity_score: float
    matches: list[DuplicateMatch] = field(default_factory=list)
    canonical_job_id: str | None = None
    job_hash: str = ""


# ============================================================================
# Normalization Functions
# ============================================================================


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

    # Common location normalizations
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
        "inc",
        "inc.",
        "llc",
        "ltd",
        "ltd.",
        "corp",
        "corp.",
        "corporation",
        "company",
        "co",
        "co.",
        "limited",
    ]

    for suffix in suffixes:
        company = re.sub(rf"\b{suffix}\.?\b", "", company)

    company = re.sub(r"\s+", " ", company)
    return company.strip()


def normalize_url(url: str) -> str:
    """Normalize URL for comparison by removing tracking parameters."""
    if not url:
        return ""

    try:
        parsed = urlparse(url.lower().strip())

        # Remove common tracking parameters
        tracking_params = {
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_content",
            "utm_term",
            "ref",
            "source",
            "mc_cid",
            "mc_eid",
        }

        # Parse and rebuild URL without tracking params
        from urllib.parse import parse_qs, urlencode

        query_params = parse_qs(parsed.query)
        clean_params = {k: v for k, v in query_params.items() if k not in tracking_params}

        # Reconstruct path, removing trailing slashes and www
        path = parsed.path.rstrip("/")
        if path.startswith("/www."):
            path = path[4:]

        # Rebuild URL
        clean_query = urlencode(clean_params, doseq=True)
        netloc = parsed.netloc.replace("www.", "")

        return f"{netloc}{path}" + (f"?{clean_query}" if clean_query else "")
    except Exception:
        # Fallback: simple normalization
        url = url.lower().strip()
        url = re.sub(r"https?://(www\.)?", "", url)
        url = re.sub(r"/$", "", url)
        return url


def tokenize_text(text: str) -> set[str]:
    """Tokenize text into words for comparison."""
    normalized = normalize_text(text)
    if not normalized:
        return set()
    return set(normalized.split())


def extract_salary_range(salary_str: str | None) -> tuple[float, float] | None:
    """Extract min and max salary from a salary string."""
    if not salary_str:
        return None

    # Match patterns like "$50,000 - $100,000", "$50k - $100k", "$50 - $100"
    pattern = r"\$?\s*(\d+(?:,\d{3})?(?:k)?)\s*(?:-|to)\s*\$?\s*(\d+(?:,\d{3})?(?:k)?)"
    matches = re.findall(pattern, salary_str.lower())

    if not matches:
        return None

    def parse_amount(amount: str) -> float:
        amount = amount.replace(",", "")
        if "k" in amount:
            return float(amount.replace("k", "")) * 1000
        return float(amount)

    try:
        min_val = parse_amount(matches[0][0])
        max_val = parse_amount(matches[0][1])
        return (min_val, max_val)
    except (ValueError, IndexError):
        return None


# ============================================================================
# Similarity Functions
# ============================================================================


def levenshtein_similarity(s1: str, s2: str) -> float:
    """Calculate Levenshtein similarity between two strings."""
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    # Use SequenceMatcher for efficiency
    return SequenceMatcher(None, s1, s2).ratio()


def jaccard_similarity(set1: set[str], set2: set[str]) -> float:
    """Calculate Jaccard similarity between two sets."""
    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0

    intersection = len(set1 & set2)
    union = len(set1 | set2)

    return intersection / union if union > 0 else 0.0


def title_similarity(title_a: str, title_b: str) -> float:
    """Calculate similarity between job titles."""
    norm_a = normalize_text(title_a)
    norm_b = normalize_text(title_b)

    if not norm_a or not norm_b:
        return 0.0

    # Exact match after normalization
    if norm_a == norm_b:
        return 1.0

    # Use sequence matching
    return SequenceMatcher(None, norm_a, norm_b).ratio()


def company_similarity(company_a: str, company_b: str) -> float:
    """Calculate similarity between company names."""
    norm_a = normalize_company(company_a)
    norm_b = normalize_company(company_b)

    if not norm_a or not norm_b:
        return 0.0

    # Exact match after normalization
    if norm_a == norm_b:
        return 1.0

    # Use sequence matching
    return SequenceMatcher(None, norm_a, norm_b).ratio()


def location_similarity(location_a: str | None, location_b: str | None) -> float:
    """Calculate similarity between locations."""
    if not location_a and not location_b:
        return 1.0
    if not location_a or not location_b:
        return 0.0

    norm_a = normalize_location(location_a)
    norm_b = normalize_location(location_b)

    if norm_a == norm_b:
        return 1.0

    # Partial match for remote
    if "remote" in norm_a or "remote" in norm_b:
        if "remote" in norm_a and "remote" in norm_b:
            return 1.0
        if "remote" in norm_a or "remote" in norm_b:
            return 0.5

    return SequenceMatcher(None, norm_a, norm_b).ratio()


def description_similarity(desc_a: str, desc_b: str) -> float:
    """Calculate similarity between job descriptions using token overlap."""
    if not desc_a and not desc_b:
        return 1.0
    if not desc_a or not desc_b:
        return 0.0

    # Tokenize descriptions
    tokens_a = tokenize_text(desc_a)
    tokens_b = tokenize_text(desc_b)

    # Use Jaccard similarity on tokens
    return jaccard_similarity(tokens_a, tokens_b)


def url_similarity(url_a: str | None, url_b: str | None) -> float:
    """Calculate similarity between URLs."""
    if not url_a and not url_b:
        return 1.0
    if not url_a or not url_b:
        return 0.0

    norm_a = normalize_url(url_a)
    norm_b = normalize_url(url_b)

    if norm_a == norm_b:
        return 1.0

    # Extract domains for partial matching
    try:
        domain_a = urlparse(norm_a if norm_a.startswith("http") else f"http://{norm_a}").netloc
        domain_b = urlparse(norm_b if norm_b.startswith("http") else f"http://{norm_b}").netloc

        if domain_a == domain_b:
            return 0.8
    except Exception:
        pass

    return SequenceMatcher(None, norm_a, norm_b).ratio()


def salary_similarity(salary_a: str | None, salary_b: str | None) -> float:
    """Calculate similarity between salary ranges."""
    if not salary_a and not salary_b:
        return 1.0
    if not salary_a or not salary_b:
        return 0.0

    range_a = extract_salary_range(salary_a)
    range_b = extract_salary_range(salary_b)

    if not range_a and not range_b:
        return 1.0
    if not range_a or not range_b:
        return 0.5

    # Calculate overlap coefficient
    min_a, max_a = range_a
    min_b, max_b = range_b

    # Check for overlap
    overlap_min = max(min_a, min_b)
    overlap_max = min(max_a, max_b)

    if overlap_min > overlap_max:
        return 0.0  # No overlap

    overlap = overlap_max - overlap_min
    union = max(max_a, max_b) - min(min_a, min_b)

    if union == 0:
        return 1.0 if min_a == min_b and max_a == max_b else 0.5

    return overlap / union


# ============================================================================
# DuplicateDetector Class
# ============================================================================


class DuplicateDetector:
    """Detects duplicate job listings using multiple similarity metrics."""

    def __init__(
        self,
        exact_threshold: float = EXACT_DUPLICATE_THRESHOLD,
        likely_threshold: float = LIKELY_DUPLICATE_THRESHOLD,
        possible_threshold: float = POSSIBLE_DUPLICATE_THRESHOLD,
    ):
        """Initialize the duplicate detector.

        Args:
            exact_threshold: Threshold for exact duplicates (>95%)
            likely_threshold: Threshold for likely duplicates (>80%)
            possible_threshold: Threshold for possible duplicates (>60%)
        """
        self.exact_threshold = exact_threshold
        self.likely_threshold = likely_threshold
        self.possible_threshold = possible_threshold

    def hash_job(self, job_data: dict) -> str:
        """Create a normalized hash for job deduplication.

        Uses title + company hash for exact matching.

        Args:
            job_data: Job data dictionary with 'title' and 'company' keys

        Returns:
            Normalized hash string
        """
        title = normalize_text(job_data.get("title", ""))
        company = normalize_company(job_data.get("company", ""))

        # Create hash from normalized title and company
        hash_input = f"{title}|{company}"
        return hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

    def compute_similarity(self, job_a: dict, job_b: dict) -> float:
        """Compute overall similarity score between two jobs.

        Args:
            job_a: First job data dictionary
            job_b: Second job data dictionary

        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Calculate individual similarity components
        title_sim = title_similarity(
            job_a.get("title", ""),
            job_b.get("title", ""),
        )
        company_sim = company_similarity(
            job_a.get("company", ""),
            job_b.get("company", ""),
        )
        location_sim = location_similarity(
            job_a.get("location"),
            job_b.get("location"),
        )
        desc_sim = description_similarity(
            job_a.get("description", ""),
            job_b.get("description", ""),
        )
        url_sim = url_similarity(
            job_a.get("url"),
            job_b.get("url"),
        )
        salary_sim = salary_similarity(
            job_a.get("salary"),
            job_b.get("salary"),
        )

        # Weight the components
        # Title and company are most important for duplicate detection
        weights = {
            "title": 0.30,
            "company": 0.25,
            "description": 0.20,
            "location": 0.10,
            "url": 0.10,
            "salary": 0.05,
        }

        weighted_sum = (
            title_sim * weights["title"]
            + company_sim * weights["company"]
            + desc_sim * weights["description"]
            + location_sim * weights["location"]
            + url_sim * weights["url"]
            + salary_sim * weights["salary"]
        )

        return min(1.0, max(0.0, weighted_sum))

    def _get_match_type(self, similarity: float) -> str:
        """Determine the match type based on similarity score."""
        if similarity >= self.exact_threshold:
            return "exact"
        if similarity >= self.likely_threshold:
            return "likely"
        if similarity >= self.possible_threshold:
            return "possible"
        return "none"

    def _get_match_reasons(
        self, job_a: dict, job_b: dict, similarity: float
    ) -> list[str]:
        """Determine why jobs are considered duplicates."""
        reasons = []

        # Check individual similarities
        if title_similarity(job_a.get("title", ""), job_b.get("title", "")) >= 0.9:
            reasons.append("similar_title")

        if company_similarity(job_a.get("company", ""), job_b.get("company", "")) >= 0.9:
            reasons.append("similar_company")

        if location_similarity(
            job_a.get("location"), job_b.get("location")
        ) >= 0.8:
            reasons.append("similar_location")

        if description_similarity(
            job_a.get("description", ""), job_b.get("description", "")
        ) >= 0.7:
            reasons.append("similar_description")

        if url_similarity(job_a.get("url"), job_b.get("url")) >= 0.9:
            reasons.append("similar_url")

        if salary_similarity(job_a.get("salary"), job_b.get("salary")) >= 0.8:
            reasons.append("similar_salary")

        # Add overall similarity reason
        if similarity >= self.exact_threshold:
            reasons.append("high_overall_similarity")
        elif similarity >= self.likely_threshold:
            reasons.append("moderate_overall_similarity")

        return reasons

    def find_duplicates(
        self, job_data: dict, existing_jobs: list[dict]
    ) -> list[DuplicateMatch]:
        """Find duplicate jobs from a list of existing jobs.

        Args:
            job_data: Job data to check for duplicates
            existing_jobs: List of existing job dictionaries

        Returns:
            List of DuplicateMatch objects sorted by similarity
        """
        # First, try exact hash match
        job_hash = self.hash_job(job_data)
        exact_matches = []

        for existing_job in existing_jobs:
            existing_hash = self.hash_job(existing_job)
            if job_hash == existing_hash:
                exact_matches.append(
                    DuplicateMatch(
                        job_id=existing_job.get("id", ""),
                        similarity_score=1.0,
                        match_type="exact",
                        match_reasons=["exact_hash_match"],
                        canonical_job_id=existing_job.get("canonical_job_id"),
                    )
                )

        if exact_matches:
            return exact_matches

        # If no exact matches, compute similarity scores
        duplicates = []

        for existing_job in existing_jobs:
            similarity = self.compute_similarity(job_data, existing_job)
            match_type = self._get_match_type(similarity)

            if match_type != "none":
                match_reasons = self._get_match_reasons(job_data, existing_job, similarity)

                duplicates.append(
                    DuplicateMatch(
                        job_id=existing_job.get("id", ""),
                        similarity_score=similarity,
                        match_type=match_type,
                        match_reasons=match_reasons,
                        canonical_job_id=existing_job.get("canonical_job_id"),
                    )
                )

        # Sort by similarity (highest first)
        duplicates.sort(key=lambda x: x.similarity_score, reverse=True)

        return duplicates

    def check_duplicate(
        self, job_data: dict, existing_jobs: list[dict]
    ) -> DuplicateCheckResult:
        """Check if a job is a duplicate of any existing jobs.

        Args:
            job_data: Job data to check
            existing_jobs: List of existing job dictionaries

        Returns:
            DuplicateCheckResult with duplicate information
        """
        job_hash = self.hash_job(job_data)
        duplicates = self.find_duplicates(job_data, existing_jobs)

        if not duplicates:
            return DuplicateCheckResult(
                is_duplicate=False,
                duplicate_type=None,
                similarity_score=0.0,
                matches=[],
                canonical_job_id=None,
                job_hash=job_hash,
            )

        best_match = duplicates[0]
        is_duplicate = best_match.match_type != "none"

        # If we have a canonical_job_id from existing jobs, use it
        canonical_id = best_match.canonical_job_id

        return DuplicateCheckResult(
            is_duplicate=is_duplicate,
            duplicate_type=best_match.match_type if is_duplicate else None,
            similarity_score=best_match.similarity_score,
            matches=duplicates,
            canonical_job_id=canonical_id,
            job_hash=job_hash,
        )

    def get_canonical_job_id(self, job_data: dict) -> uuid.UUID:
        """Get or create a canonical job ID for a job.

        The canonical job ID is used to group duplicate jobs together.
        If the job already has a canonical_job_id, it will be returned.
        Otherwise, a new UUID will be generated.

        Args:
            job_data: Job data dictionary

        Returns:
            UUID for the canonical job
        """
        # If job already has a canonical_job_id, return it
        existing_id = job_data.get("canonical_job_id")
        if existing_id:
            try:
                return uuid.UUID(existing_id)
            except (ValueError, TypeError):
                pass

        # Generate new canonical job ID based on job hash
        job_hash = self.hash_job(job_data)

        # Use the hash to create a deterministic UUID
        return uuid.UUID(hashlib.md5(job_hash.encode()).hexdigest())

    def update_canonical_references(
        self, jobs: list[dict]
    ) -> list[dict]:
        """Update jobs to reference their canonical job IDs.

        Groups duplicate jobs together by assigning them the same
        canonical_job_id based on their similarity.

        Args:
            jobs: List of job dictionaries

        Returns:
            Updated list of jobs with canonical_job_id references
        """
        if not jobs:
            return jobs

        # Sort jobs by some priority (e.g., date posted)
        sorted_jobs = sorted(
            jobs,
            key=lambda j: j.get("posted_at", ""),
            reverse=True,
        )

        # Track canonical job IDs
        canonical_map: dict[str, str] = {}  # job_hash -> canonical_id

        updated_jobs = []

        for job in sorted_jobs:
            job_hash = self.hash_job(job)

            # Check if we've seen this exact job before
            if job_hash in canonical_map:
                # Use existing canonical ID
                canonical_id = canonical_map[job_hash]
            else:
                # Check for similar jobs
                best_similarity = 0.0
                best_canonical_id = None

                for existing_hash, canonical_id in canonical_map.items():
                    similarity = self.compute_similarity(
                        job,
                        {"title": existing_hash, "company": "", "description": ""},
                    )
                    if similarity > best_similarity and similarity >= self.likely_threshold:
                        best_similarity = similarity
                        best_canonical_id = canonical_id

                if best_canonical_id:
                    canonical_id = best_canonical_id
                else:
                    # Create new canonical ID
                    canonical_id = str(self.get_canonical_job_id(job))

                canonical_map[job_hash] = canonical_id

            # Create updated job with canonical reference
            updated_job = job.copy()
            updated_job["canonical_job_id"] = canonical_id
            updated_jobs.append(updated_job)

        return updated_jobs


# ============================================================================
# Utility Functions
# ============================================================================


def create_detector(
    exact_threshold: float = EXACT_DUPLICATE_THRESHOLD,
    likely_threshold: float = LIKELY_DUPLICATE_THRESHOLD,
    possible_threshold: float = POSSIBLE_DUPLICATE_THRESHOLD,
) -> DuplicateDetector:
    """Create a configured DuplicateDetector instance.

    Args:
        exact_threshold: Threshold for exact duplicates
        likely_threshold: Threshold for likely duplicates
        possible_threshold: Threshold for possible duplicates

    Returns:
        Configured DuplicateDetector instance
    """
    return DuplicateDetector(
        exact_threshold=exact_threshold,
        likely_threshold=likely_threshold,
        possible_threshold=possible_threshold,
    )


def find_duplicate_groups(jobs: list[dict]) -> list[list[dict]]:
    """Group jobs into duplicate clusters.

    Args:
        jobs: List of job dictionaries

    Returns:
        List of job groups where each group contains duplicate jobs
    """
    detector = DuplicateDetector()
    processed: set[str] = set()
    groups: list[list[dict]] = []

    for job in jobs:
        job_id = job.get("id")
        if not job_id or job_id in processed:
            continue

        # Find all jobs similar to this one
        group = [job]
        processed.add(job_id)

        for other_job in jobs:
            other_id = other_job.get("id")
            if not other_id or other_id in processed:
                continue

            similarity = detector.compute_similarity(job, other_job)
            if similarity >= LIKELY_DUPLICATE_THRESHOLD:
                group.append(other_job)
                processed.add(other_id)

        if group:
            groups.append(group)

    return groups
