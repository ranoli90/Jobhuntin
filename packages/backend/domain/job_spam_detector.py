"""Job Spam Detection Module.

Provides spam detection and quality analysis for job listings.
Identifies suspicious patterns, keyword stuffing, scam phrases,
and other indicators of low-quality or fraudulent job postings.

This module integrates with the quality control fields added by the
migrations/035_job_quality_fields.sql migration.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from shared.logging_config import get_logger

logger = get_logger("sorce.job_spam_detector")


# ============================================================================
# Spam Pattern Definitions
# ============================================================================

# Common scam phrases that indicate potential spam
SCAM_PHRASES: list[tuple[str, float]] = [
    (r"\bno experience necessary\b", 0.8),
    (r"\bno experience needed\b", 0.8),
    (r"\bno resume needed\b", 0.9),
    (r"\bno interview\b", 0.7),
    (r"\bwork from home\b", 0.4),
    (r"\bwork from home today\b", 0.9),
    (r"\bimmediate hire\b", 0.5),
    (r"\bimmediate start\b", 0.4),
    (r"\bapply now\b.*\bno experience\b", 0.9),
    (r"\b\$5000\b.*\bweek\b", 1.0),
    (r"\b\$3000\b.*\bweek\b", 0.9),
    (r"\b\$2000\b.*\bweek\b", 0.8),
    (r"\bguaranteed income\b", 0.9),
    (r"\bguaranteed salary\b", 0.9),
    (r"\bmake \$\d+.*hour\b", 0.7),
    (r"\bearn \$\d+.*hour\b", 0.6),
    (r"\bpassive income\b", 0.8),
    (r"\bextra cash\b", 0.5),
    (r"\bbe your own boss\b", 0.6),
    (r"\bfast cash\b", 0.8),
    (r"\bquick money\b", 0.9),
    (r"\bzero investment\b", 1.0),
    (r"\bno investment\b", 0.9),
    (r"\bfree money\b", 1.0),
    (r"\bwinner\b.*\bselected\b", 0.9),
    (r"\bcongratulations\b.*\bselected\b", 0.8),
    (r"\bclick here\b.*\bapply\b", 0.8),
    (r"\bfirst come first served\b", 0.6),
    (r"\burgent hiring\b", 0.5),
    (r"\bhiring today\b", 0.4),
    (r"\bonline job\b.*\btyping\b", 0.7),
    (r"\bdata entry\b.*\bhome\b", 0.6),
    (r"\bcustomer service\b.*\bhome\b", 0.5),
    (r"\bsecret shopper\b", 0.8),
    (r"\bpackage forwarding\b", 0.9),
    (r"\bcourier\b.*\bpayment\b", 0.9),
    (r"\bwire transfer\b", 0.9),
    (r"\bmoney order\b", 0.8),
    (r"\bwestern union\b", 0.8),
    (r"\bgift card\b.*\bpayment\b", 0.9),
    (r"\bitem sold\b.*\bshipping\b", 0.7),
    (r"\breshipment\b", 0.8),
    (r"\bmlm\b", 0.9),
    (r"\bmulti-level marketing\b", 0.9),
    (r"\bpyramid scheme\b", 1.0),
    (r"\bnetwork marketing\b", 0.7),
    (r"\bpart-time\b.*\b\$\d+k\b", 0.5),
    (r"\bentry level\b.*\$\d{5,}", 0.6),
    (r"\bfreshers\b.*\bsalary\b.*\bhigh\b", 0.7),
]

# Suspicious URL patterns
SUSPICIOUS_URL_PATTERNS: list[tuple[re.Pattern[str], float]] = [
    (re.compile(r"free\.ya(?:hoo|hoo)\.com", re.IGNORECASE), 0.9),
    (re.compile(r"bit\.ly/", re.IGNORECASE), 0.4),
    (re.compile(r"tinyurl\.com/", re.IGNORECASE), 0.5),
    (re.compile(r"t\.co/", re.IGNORECASE), 0.4),
    (re.compile(r"goo\.gl/", re.IGNORECASE), 0.4),
    (re.compile(r"\.xyz\b", re.IGNORECASE), 0.3),
    (re.compile(r"\.top\b", re.IGNORECASE), 0.4),
    (re.compile(r"\.work\b", re.IGNORECASE), 0.3),
    (re.compile(r"\.click\b", re.IGNORECASE), 0.4),
    (re.compile(r"\.info\b", re.IGNORECASE), 0.3),
    (re.compile(r"\.stream\b", re.IGNORECASE), 0.4),
]

# Suspicious email patterns
SUSPICIOUS_EMAIL_PATTERNS: list[tuple[re.Pattern[str], float]] = [
    (re.compile(r"@gmail\.com.*company", re.IGNORECASE), 0.4),
    (re.compile(r"@yahoo\.com.*recruit", re.IGNORECASE), 0.5),
    (re.compile(r"@hotmail\.com.*hiring", re.IGNORECASE), 0.5),
    (re.compile(r"@\.com$", re.IGNORECASE), 0.3),
]

# Company name suspicious patterns
COMPANY_NAME_PATTERNS: list[tuple[re.Pattern[str], float]] = [
    (re.compile(r"^[a-z]{3,6}$", re.IGNORECASE), 0.7),  # Random 3-6 letter company
    (re.compile(r"^[a-z]{1,2}\d{3,}$", re.IGNORECASE), 0.9),  # Letters followed by numbers
    (re.compile(r"\d{4,}", re.IGNORECASE), 0.6),  # Too many numbers
    (re.compile(r"(home|jobs|work|money|cash|earn|fast|quick|easy|bonus|prize|winners?|gift)", re.IGNORECASE), 0.5),  # Suspicious words
    (re.compile(r"^[A-Z]+\s+INC\b", re.IGNORECASE), 0.3),  # All caps with INC
    (re.compile(r"^\d+\s+COMPANY", re.IGNORECASE), 0.7),  # Starting with numbers
]

# Keyword stuffing patterns - words often repeated excessively in spam
KEYWORD_STUFFING_WORDS: list[tuple[str, float]] = [
    ("hiring", 0.3),
    ("work", 0.2),
    ("job", 0.2),
    ("apply", 0.3),
    ("salary", 0.3),
    ("money", 0.4),
    ("earn", 0.4),
    ("income", 0.4),
    ("bonus", 0.4),
    ("benefits", 0.3),
    ("free", 0.5),
    ("limited", 0.3),
    ("urgent", 0.4),
    ("position", 0.2),
    ("opportunity", 0.3),
]

# Minimum description length thresholds
MIN_DESCRIPTION_LENGTH = 50  # Characters
SUSPICIOUS_SHORT_DESCRIPTION_LENGTH = 100  # Characters


@dataclass
class SpamAnalysisResult:
    """Result of spam analysis for a job listing."""

    is_spam: bool = False
    score: float = 0.0  # 0.0 = definitely not spam, 1.0 = definitely spam
    reasons: list[str] = field(default_factory=list)
    flags: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "is_spam": self.is_spam,
            "score": self.score,
            "reasons": self.reasons,
            "flags": self.flags,
        }


class SpamDetector:
    """Detects spam patterns in job listings.

    This class analyzes job postings for various spam indicators
    including suspicious company names, keyword stuffing, scam phrases,
    unrealistic salaries, and other quality issues.
    """

    def __init__(self, spam_threshold: float = 0.6) -> None:
        """Initialize the spam detector.

        Args:
            spam_threshold: Score threshold above which a job is considered spam.
                          Default is 0.6 (60% spam probability).
        """
        self.spam_threshold = spam_threshold
        # Compile all regex patterns for efficiency
        self._compiled_scam_patterns = [
            (re.compile(pattern, re.IGNORECASE), weight)
            for pattern, weight in SCAM_PHRASES
        ]
        logger.info("SpamDetector initialized with threshold: %s", spam_threshold)

    def detect_spam(self, job_data: dict[str, Any]) -> dict[str, Any]:
        """Analyze a job posting for spam indicators.

        Args:
            job_data: Dictionary containing job information with keys like:
                     - title: Job title
                     - company: Company name
                     - description: Job description text
                     - salary_min: Minimum salary (optional)
                     - salary_max: Maximum salary (optional)
                     - url: Job posting URL (optional)
                     - contact_email: Contact email (optional)

        Returns:
            Dictionary with spam analysis result containing:
            - is_spam: Boolean indicating if job is likely spam
            - score: Float between 0.0 and 1.0 indicating spam probability
            - reasons: List of reasons for spam detection
            - flags: Dictionary of specific flags for each check
        """
        logger.debug("Analyzing job for spam: %s", job_data.get("title", "unknown"))

        reasons: list[str] = []
        flags: dict[str, Any] = {}
        total_score: float = 0.0

        # Check company name
        company = job_data.get("company", "")
        if company:
            company_score = self.check_company_name(company)
            flags["company_score"] = company_score
            if company_score > 0.3:
                reasons.append(f"Suspicious company name: {company}")
                total_score += company_score * 0.25

        # Check job title
        title = job_data.get("title", "")
        if title:
            title_score = self.check_title(title)
            flags["title_score"] = title_score
            if title_score > 0.3:
                reasons.append(f" Suspicious job title: {title}")
                total_score += title_score * 0.25

        # Check description
        description = job_data.get("description", "")
        if description:
            desc_score = self.check_description(description)
            flags["description_score"] = desc_score
            if desc_score > 0.4:
                reasons.append("Job description contains spam indicators")
                total_score += desc_score * 0.25

        # Check salary
        salary_min = job_data.get("salary_min")
        salary_max = job_data.get("salary_max")
        if salary_min is not None and salary_max is not None:
            salary_score = self.check_salary(salary_min, salary_max)
            flags["salary_score"] = salary_score
            if salary_score > 0.5:
                reasons.append("Unrealistic salary range")
                total_score += salary_score * 0.15

        # Check URL for suspicious patterns
        if job_data.get("url"):
            url_score = self.check_url(job_data["url"])
            flags["url_score"] = url_score
            if url_score > 0.3:
                reasons.append("Suspicious URL detected")
                total_score += url_score * 0.1

        # Check contact email for suspicious patterns
        if job_data.get("contact_email"):
            email_score = self.check_email(job_data["contact_email"])
            flags["email_score"] = email_score
            if email_score > 0.3:
                reasons.append("Suspicious contact information")
                total_score += email_score * 0.1

        # Normalize score to 0-1 range
        final_score = min(total_score, 1.0)

        is_spam = final_score >= self.spam_threshold

        if is_spam:
            logger.info(
                "Job detected as spam (score: %.2f, threshold: %.2f): %s",
                final_score,
                self.spam_threshold,
                job_data.get("title", "unknown"),
            )
        else:
            logger.debug(
                "Job passed spam check (score: %.2f): %s",
                final_score,
                job_data.get("title", "unknown"),
            )

        return {
            "is_spam": is_spam,
            "score": round(final_score, 3),
            "reasons": reasons,
            "flags": flags,
        }

    def check_company_name(self, company: str) -> float:
        """Score a company name for suspicious patterns.

        Args:
            company: Company name to check.

        Returns:
            Float between 0.0 and 1.0 indicating suspiciousness.
            Higher scores indicate more suspicious company names.
        """
        if not company or len(company.strip()) < 2:
            return 0.0

        score: float = 0.0
        company_lower = company.lower()
        company_clean = re.sub(r"[^\w\s]", "", company)

        # Check against patterns
        for pattern, weight in COMPANY_NAME_PATTERNS:
            if pattern.search(company):
                score = max(score, weight)

        # Check for random letter combinations (like "abcxyz")
        if len(company_clean) >= 6:
            # Check for repeated characters or random sequences
            if re.match(r"^[a-z]{6,}$", company_clean):
                # Check for consonant clusters that look random
                consonants = re.findall(r"[bcdfghjklmnpqrstvwxz]+", company_clean)
                if any(len(c) >= 5 for c in consonants):
                    score = max(score, 0.7)

        # Check for company name that's just keywords
        keyword_count = sum(
            1 for word in ["jobs", "work", "home", "money", "cash", "earn", "fast"]
            if word in company_lower
        )
        if keyword_count >= 2:
            score = max(score, 0.6)

        # Check for suspiciously short company names (less than 3 chars)
        if len(company_clean) < 3 and len(company_clean) > 0:
            score = max(score, 0.5)

        # All uppercase check
        if company.isupper() and len(company) > 5:
            score = max(score, 0.4)

        return min(score, 1.0)

    def check_title(self, title: str) -> float:
        """Score a job title for spam indicators.

        Args:
            title: Job title to check.

        Returns:
            Float between 0.0 and 1.0 indicating suspiciousness.
        """
        if not title:
            return 0.0

        score: float = 0.0

        # Check for excessive caps
        upper_count = sum(1 for c in title if c.isupper())
        if len(title) > 0 and upper_count / len(title) > 0.5:
            score = max(score, 0.5)

        # Check title length - too short or too long
        if len(title) < 10:
            score = max(score, 0.4)
        if len(title) > 150:
            score = max(score, 0.3)

        # Check for suspicious phrases in title
        suspicious_title_phrases = [
            (r"urgent", 0.5),
            (r"immediate hire", 0.7),
            (r"no experience", 0.6),
            (r"\$", 0.3),  # Dollar sign in title
            (r"bonus", 0.4),
            (r"earn \$\d+", 0.7),
            (r"\d+k\b.*\d+k\b", 0.5),  # Salary range in title
            (r"part.?time", 0.3),
            (r"work from home", 0.4),
            (r"home based", 0.4),
            (r"quick cash", 0.7),
            (r"easy money", 0.7),
        ]

        title_lower = title.lower()
        for pattern, weight in suspicious_title_phrases:
            if re.search(pattern, title_lower):
                score = max(score, weight)

        # Check for all caps title
        if title.isupper() and len(title) > 5:
            score = max(score, 0.5)

        # Check for excessive punctuation
        punct_count = sum(1 for c in title if c in "!@#$%*")
        if punct_count > 2:
            score = max(score, 0.4)

        return min(score, 1.0)

    def check_description(self, description: str) -> float:
        """Score a job description for keyword stuffing and spam indicators.

        Args:
            description: Job description text to check.

        Returns:
            Float between 0.0 and 1.0 indicating suspiciousness.
        """
        if not description:
            return 0.0

        score: float = 0.0

        # Check for minimum length
        if len(description) < MIN_DESCRIPTION_LENGTH:
            score = max(score, 0.8)
            return min(score, 1.0)

        if len(description) < SUSPICIOUS_SHORT_DESCRIPTION_LENGTH:
            score = max(score, 0.4)

        # Check for excessive repetition (keyword stuffing)
        words = re.findall(r"\b\w{4,}\b", description.lower())
        if words:
            word_counts: dict[str, int] = {}
            for word in words:
                word_counts[word] = word_counts.get(word, 0) + 1

            # Find words repeated excessively
            total_words = len(words)
            for word, count in word_counts.items():
                if count > 3:
                    ratio = count / total_words
                    if ratio > 0.1:  # More than 10% of total words
                        score = max(score, 0.5)

        # Check for scam phrases
        description_lower = description.lower()
        for pattern, weight in self._compiled_scam_patterns:
            if pattern.search(description):
                score = max(score, weight * 0.6)

        # Check for excessive numbers (often in spam)
        numbers = re.findall(r"\d+", description)
        if len(numbers) > 20:
            score = max(score, 0.4)

        # Check for suspicious URL patterns in description
        url_patterns = re.findall(
            r"https?://[^\s]+", description, re.IGNORECASE
        )
        if len(url_patterns) > 5:
            score = max(score, 0.4)

        # Check for email patterns
        email_patterns = re.findall(
            r"[\w\.-]+@[\w\.-]+\.\w+", description
        )
        if len(email_patterns) > 3:
            score = max(score, 0.4)

        return min(score, 1.0)

    def check_salary(self, salary_min: int, salary_max: int) -> float:
        """Check for unrealistic salary ranges.

        Args:
            salary_min: Minimum salary.
            salary_max: Maximum salary.

        Returns:
            Float between 0.0 and 1.0 indicating suspiciousness.
        """
        if salary_min <= 0 or salary_max <= 0:
            return 0.0

        # Calculate annual salary assuming 40hr work week
        annual_min = salary_min * 52
        annual_max = salary_max * 52

        score: float = 0.0

        # Check for extremely high salaries for entry-level positions
        # Entry level usually below $80k/year
        if annual_min > 150000:
            score = max(score, 0.7)
        elif annual_min > 100000:
            score = max(score, 0.4)

        # Check for unrealistic ranges (too wide)
        if salary_max > 0:
            range_ratio = (salary_max - salary_min) / salary_min if salary_min > 0 else 0
            if range_ratio > 5:  # More than 500% range
                score = max(score, 0.5)
            if range_ratio > 10:  # More than 1000% range
                score = max(score, 0.8)

        # Check for suspiciously low salaries combined with "no experience"
        # These are often too good to be true
        if annual_max < 30000:
            score = max(score, 0.3)

        # Check for unusually high maximum salaries
        if annual_max > 500000:
            score = max(score, 0.9)
        elif annual_max > 300000:
            score = max(score, 0.6)

        return min(score, 1.0)

    def check_url(self, url: str) -> float:
        """Check URL for suspicious patterns.

        Args:
            url: URL to check.

        Returns:
            Float between 0.0 and 1.0 indicating suspiciousness.
        """
        if not url:
            return 0.0

        score: float = 0.0
        url_lower = url.lower()

        for pattern, weight in SUSPICIOUS_URL_PATTERNS:
            if pattern.search(url):
                score = max(score, weight)

        # Check for overly long URLs
        if len(url) > 200:
            score = max(score, 0.4)

        # Check for suspicious domains
        suspicious_domains = ["dating", "casino", "poker", "gambling", "adult"]
        for domain in suspicious_domains:
            if domain in url_lower:
                score = max(score, 0.8)

        return min(score, 1.0)

    def check_email(self, email: str) -> float:
        """Check email address for suspicious patterns.

        Args:
            email: Email address to check.

        Returns:
            Float between 0.0 and 1.0 indicating suspiciousness.
        """
        if not email:
            return 0.0

        score: float = 0.0

        for pattern, weight in SUSPICIOUS_EMAIL_PATTERNS:
            if pattern.search(email.lower()):
                score = max(score, weight)

        # Check for generic email patterns
        email_lower = email.lower()
        if any(x in email_lower for x in ["noreply", "no-reply", "donotreply", "admin"]):
            score = max(score, 0.3)

        # Check for very long email addresses
        if len(email) > 100:
            score = max(score, 0.5)

        return min(score, 1.0)


# ============================================================================
# Integration Functions
# ============================================================================


def analyze_job(job_data: dict[str, Any]) -> dict[str, Any]:
    """Analyze a job listing and return quality flags.

    This is the main entry point for job quality analysis.
    It uses the SpamDetector to analyze the job and returns
    quality flags that can be stored in the database.

    Args:
        job_data: Dictionary containing job information with keys like:
                 - title: Job title
                 - company: Company name
                 - description: Job description text
                 - salary_min: Minimum salary (optional)
                 - salary_max: Maximum salary (optional)
                 - url: Job posting URL (optional)
                 - contact_email: Contact email (optional)

    Returns:
        Dictionary with quality analysis result containing:
        - is_spam: Boolean indicating if job is likely spam
        - spam_score: Float between 0.0 and 1.0
        - spam_reasons: List of reasons for spam detection
        - quality_flags: Dictionary with specific quality indicators
        - needs_review: Boolean indicating if manual review is needed

    Example:
        >>> job_data = {
        ...     "title": "Software Engineer",
        ...     "company": "Tech Corp",
        ...     "description": "Great opportunity for experienced developer...",
        ...     "salary_min": 80000,
        ...     "salary_max": 120000,
        ... }
        >>> result = analyze_job(job_data)
        >>> print(result["is_spam"])
        False
    """
    logger.debug("Analyzing job quality: %s", job_data.get("title", "unknown"))

    # Initialize detector with default threshold
    detector = SpamDetector(spam_threshold=0.6)

    # Perform spam analysis
    spam_result = detector.detect_spam(job_data)

    # Build quality flags based on analysis
    quality_flags: dict[str, Any] = {
        "spam_detected": spam_result["is_spam"],
        "spam_score": spam_result["score"],
        "company_score": spam_result["flags"].get("company_score", 0.0),
        "title_score": spam_result["flags"].get("title_score", 0.0),
        "description_score": spam_result["flags"].get("description_score", 0.0),
        "salary_score": spam_result["flags"].get("salary_score", 0.0),
        "url_score": spam_result["flags"].get("url_score", 0.0),
        "email_score": spam_result["flags"].get("email_score", 0.0),
    }

    # Determine if manual review is needed
    # Review is needed if spam score is above 0.3 but below threshold
    # or if any individual score is very high
    needs_review = (
        spam_result["score"] > 0.3
        and not spam_result["is_spam"]
    ) or any(
        score > 0.7 for score in [
            quality_flags["company_score"],
            quality_flags["title_score"],
            quality_flags["description_score"],
            quality_flags["salary_score"],
            quality_flags["url_score"],
            quality_flags["email_score"],
        ]
    )

    return {
        "is_spam": spam_result["is_spam"],
        "spam_score": spam_result["score"],
        "spam_reasons": spam_result["reasons"],
        "quality_flags": quality_flags,
        "needs_review": needs_review,
    }


# For backwards compatibility, also expose the SpamDetector class
__all__ = ["SpamDetector", "SpamAnalysisResult", "analyze_job"]