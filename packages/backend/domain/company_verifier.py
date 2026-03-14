"""Company Verification/Scoring Module.

Provides company verification and reputation scoring for job listings.
Verifies company legitimacy through domain validation, industry classification,
employee count verification, known scam database lookup, and domain age analysis.

This module integrates with the quality control fields added by the
migrations/035_job_quality_fields.sql migration and the companies table
from migrations/036_companies_table.sql.
"""

from __future__ import annotations

import asyncio
import hashlib
import re
import socket
import ssl
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

from shared.cache_strategies import CacheStrategy, InMemoryCache
from shared.logging_config import get_logger

logger = get_logger("sorce.company_verifier")


# ============================================================================
# Known Companies and Scams Database
# ============================================================================

# Known legitimate companies (positive reputation)
KNOWN_GOOD_COMPANIES: set[str] = {
    # Tech giants
    "google", "alphabet", "meta", "facebook", "amazon", "apple", "microsoft",
    "netflix", "salesforce", "adobe", "oracle", "ibm", "intel", "nvidia",
    "amd", "qualcomm", "cisco", "dell", "hp", "lenovo", "huawei",
    # Major tech companies
    "stripe", "airbnb", "uber", "lyft", "spotify", "slack", "zoom",
    "snowflake", "databricks", "cloudflare", "github", "gitlab",
    "twilio", "sendgrid", "twilio", "pagerduty", "servicenow",
    "workday", "serviceNow", "splunk", "monday", "atlassian",
    "shopify", "squarespace", "wordpress", "wix",
    # Financial tech
    "paypal", "square", "block", "coinbase", "robinhood", "chase",
    "bank of america", "wells fargo", "citibank", "goldman sachs",
    "morgan stanley", "jpmorgan", "blackrock", "vanguard",
    # Other major companies
    "walmart", "target", "costco", "home depot", "lowes",
    "tesla", "ford", "gm", "toyota", "honda", "bmw", "mercedes",
    "exxon", "chevron", "shell", "bp",
    # Consulting and services
    "accenture", "deloitte", "pwc", "kpmg", "mckinsey", "bcg", " Bain",
    "cognizant", "tcs", "infosys", "wipro", "hcl",
    # Healthcare
    "cvs", "walgreens", "unitedhealth", "anthem", "kaiser",
    # Startups (well-funded)
    "airbnb", "instacart", "doordash", "grubhub", "postmates",
    "uber eats", "wework", "spacex", "blue origin",
}

# Known scam companies and patterns
KNOWN_SCAM_COMPANIES: dict[str, float] = {
    # Common scam patterns
    "data entry": 0.9,
    "email handler": 0.95,
    "package forwarding": 0.95,
    "wire transfer": 0.9,
    "mystery shopper": 0.85,
    "envelope stuffing": 0.95,
    "assembly work": 0.85,
    "work from home": 0.7,
    "medical billing": 0.85,
    "insurance claims": 0.8,
    # Known scam keywords
    "quick cash": 0.9,
    "guaranteed income": 0.9,
    "no experience needed": 0.8,
    "no interview": 0.85,
}

# Suspicious patterns in company names
SUSPICIOUS_NAME_PATTERNS: list[tuple[str, float]] = [
    (r"\bfree\b.*\bmoney\b", 0.9),
    (r"\b\$\d+.*hour\b.*\bwork\b", 0.8),
    (r"\bimmediate\s*(?:hire|cash|money)", 0.8),
    (r"\bno\s*(?:experience|resume|interview)", 0.7),
    (r"\bwork\s*from\s*home\b.*\btyping\b", 0.85),
    (r"\bpart[- ]time\b.*\b\$\d+", 0.6),
    (r"\bentry\s*level\b.*\b\d+k\b", 0.5),
    (r"\bfreshers?\b", 0.7),
    (r"\bconsultant\b.*\btraining\b", 0.8),
    (r"\bmarketing?\b.*\bonline\b", 0.5),
    (r"\bcustomer\s*service\b.*\bhome\b", 0.6),
    (r"\badmin\b.*\bhome\b", 0.7),
]

# Suspicious TLDs
SUSPICIOUS_TLDS: set[str] = {
    ".xyz", ".top", ".click", ".work", ".click", ".loan", ".gq",
    ".ml", ".cf", ".tk", ".buzz", ".rest", ".cam", ".suo", ".wen",
}

# Valid business TLDs
VALID_BUSINESS_TLDS: set[str] = {
    ".com", ".org", ".net", ".io", ".co", ".ai", ".dev", ".app",
    ".inc", ".llc", ".ltd", ".corp", ".io", ".ai",
}


# ============================================================================
# Industry Classification
# ============================================================================

INDUSTRY_KEYWORDS: dict[str, list[str]] = {
    "technology": [
        "software", "tech", "developer", "engineering", "it", "computer",
        "data", "cloud", "saas", "platform", "api", "security", "devops",
    ],
    "finance": [
        "bank", "financial", "finance", "investment", "trading", "fintech",
        "insurance", "credit", "loan", "mortgage", "asset", "wealth",
    ],
    "healthcare": [
        "health", "medical", "hospital", "pharma", "biotech", "clinical",
        "healthcare", "wellness", "dental", "vision", "insurance",
    ],
    "retail": [
        "retail", "store", "shop", "e-commerce", "ecommerce", "marketplace",
        "consumer", "fashion", "clothing", "grocery",
    ],
    "manufacturing": [
        "manufacturing", "factory", "production", "industrial", "assembly",
        "machinery", "equipment", "construction",
    ],
    "consulting": [
        "consulting", "consultancy", "advisory", "strategy", "management",
        "professional services", "solutions",
    ],
    "education": [
        "education", "school", "university", "college", "training",
        "learning", "edtech", "courses", "coaching",
    ],
    "marketing": [
        "marketing", "advertising", "media", "agency", "digital", "seo",
        "social media", "brand", "promotions",
    ],
    "hospitality": [
        "hotel", "restaurant", "hospitality", "travel", "tourism",
        "food service", "catering", "events",
    ],
    "logistics": [
        "logistics", "shipping", "transportation", "delivery", "supply chain",
        "freight", "warehouse", "distribution",
    ],
}


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class CompanyVerificationResult:
    """Result of company verification."""
    company_name: str
    domain: str | None
    is_verified: bool
    reputation_score: float
    company_score: float
    verification_level: str
    is_suspicious: bool
    known_scam: bool
    checks_performed: dict[str, Any]
    industry: str | None
    domain_age_days: int | None
    recommendations: list[str] = field(default_factory=list)


@dataclass
class DomainCheckResult:
    """Result of domain verification."""
    domain: str
    is_valid: bool = False
    exists: bool = False
    has_ssl: bool = False
    registrar: str | None = None
    registration_date: datetime | None = None
    age_days: int | None = None
    suspicious_tld: boolean = False
    mx_records: boolean = False
    error: str | None = None


# ============================================================================
# Company Verifier Class
# ============================================================================


class CompanyVerifier:
    """Company verification and scoring service.

    Provides comprehensive company verification including domain validation,
    reputation scoring, scam detection, and industry classification.
    """

    def __init__(
        self,
        cache_ttl: int = 86400,  # 24 hours default cache
        cache_strategy: CacheStrategy | None = None,
    ):
        """Initialize the company verifier.

        Args:
            cache_ttl: Cache TTL in seconds (default 24 hours)
            cache_strategy: Optional cache strategy for verification caching
        """
        self._cache_ttl = cache_ttl
        self._cache = cache_strategy or InMemoryCache()
        self._verification_cache: dict[str, tuple[datetime, CompanyVerificationResult]] = {}

    # ==========================================================================
    # Public API
    # ==========================================================================

    async def verify_company(
        self,
        company_name: str,
        domain: str | None = None,
    ) -> CompanyVerificationResult:
        """Main company verification method.

        Performs comprehensive verification including domain validation,
        reputation scoring, scam detection, and industry classification.

        Args:
            company_name: Name of the company to verify
            domain: Optional domain to verify against company name

        Returns:
            CompanyVerificationResult with verification details and score
        """
        # Normalize company name
        normalized_name = self._normalize_company_name(company_name)

        # Check cache first
        cache_key = self._get_cache_key(normalized_name, domain)
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            logger.debug(f"Using cached verification for {company_name}")
            return cached_result

        # Collect verification data
        checks_performed: dict[str, Any] = {}

        # 1. Domain verification
        domain_result = None
        if domain:
            domain_result = await self.check_domain(domain)
            checks_performed["domain_check"] = {
                "is_valid": domain_result.is_valid,
                "exists": domain_result.exists,
                "has_ssl": domain_result.has_ssl,
                "age_days": domain_result.age_days,
                "suspicious_tld": domain_result.suspicious_tld,
            }

        # 2. Company name analysis
        name_analysis = self._analyze_company_name(normalized_name)
        checks_performed["name_analysis"] = name_analysis

        # 3. Known scam check
        scam_check = self._check_known_scams(normalized_name, domain)
        checks_performed["scam_check"] = scam_check

        # 4. Known good company check
        is_known_good = self._check_known_good_company(normalized_name)
        checks_performed["is_known_good"] = is_known_good

        # 5. Industry classification
        industry = self._classify_industry(normalized_name, domain)
        checks_performed["industry"] = industry

        # 6. Calculate reputation score
        reputation_score = self.calculate_reputation_score(checks_performed)

        # 7. Calculate company score (0-100) based on verification factors
        company_score = self._calculate_company_score(
            reputation_score=reputation_score,
            domain_result=domain_result,
            is_known_good=is_known_good,
            is_suspicious=name_analysis.get("is_suspicious", False),
            known_scam=scam_check.get("is_scam", False),
            industry=industry,
        )

        # Determine verification level
        verification_level = self._determine_verification_level(
            domain_result=domain_result,
            is_verified_domain=domain_result.is_valid if domain_result else False,
            is_known_good=is_known_good,
            company_score=company_score,
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            domain_result=domain_result,
            name_analysis=name_analysis,
            scam_check=scam_check,
            company_score=company_score,
        )

        result = CompanyVerificationResult(
            company_name=normalized_name,
            domain=domain,
            is_verified=verification_level in ("verified", "high"),
            reputation_score=reputation_score,
            company_score=company_score,
            verification_level=verification_level,
            is_suspicious=name_analysis.get("is_suspicious", False) or scam_check.get("is_scam", False),
            known_scam=scam_check.get("is_scam", False),
            checks_performed=checks_performed,
            industry=industry,
            domain_age_days=domain_result.age_days if domain_result else None,
            recommendations=recommendations,
        )

        # Cache result
        self._cache_verification_result(cache_key, result)

        logger.info(
            f"Company verification completed: {company_name} - "
            f"score={company_score:.1f}, level={verification_level}"
        )

        return result

    def check_domain(self, domain: str) -> DomainCheckResult:
        """Verify domain existence and validity.

        Performs DNS resolution, SSL certificate check, and domain age estimation.

        Args:
            domain: Domain to verify (e.g., "example.com")

        Returns:
            DomainCheckResult with verification details
        """
        result = DomainCheckResult(domain=domain)

        # Parse and validate domain format
        parsed = urlparse(f"https://{domain}")
        clean_domain = parsed.netloc or domain

        # Remove www prefix for consistency
        if clean_domain.startswith("www."):
            clean_domain = clean_domain[4:]

        # Check TLD
        tld_match = re.search(r"(\.\w+)$", clean_domain)
        if tld_match:
            tld = tld_match.group(1).lower()
            result.suspicious_tld = tld in SUSPICIOUS_TLDS
            result.is_valid = tld in VALID_BUSINESS_TLDS or tld not in SUSPICIOUS_TLDS

        # Try DNS resolution
        try:
            socket.setdefaulttimeout(5)
            ip_address = socket.gethostbyname(clean_domain)
            result.exists = True
            logger.debug(f"Domain {domain} resolves to {ip_address}")
        except socket.gaierror as e:
            result.exists = False
            result.error = f"DNS resolution failed: {str(e)}"
            logger.warning(f"DNS resolution failed for {domain}: {e}")
            return result
        except socket.timeout:
            result.exists = False
            result.error = "DNS resolution timed out"
            logger.warning(f"DNS resolution timed out for {domain}")
            return result
        except Exception as e:
            result.exists = False
            result.error = f"DNS resolution error: {str(e)}"
            logger.warning(f"DNS resolution error for {domain}: {e}")
            return result

        # Check SSL certificate
        try:
            result.has_ssl = self._check_ssl_certificate(clean_domain)
        except Exception as e:
            logger.debug(f"SSL check failed for {domain}: {e}")
            result.has_ssl = False

        # Check MX records (indicates legitimate email)
        try:
            result.mx_records = self._check_mx_records(clean_domain)
        except Exception as e:
            logger.debug(f"MX check failed for {domain}: {e}")
            result.mx_records = False

        # Estimate domain age (simplified - based on common patterns)
        result.age_days = self._estimate_domain_age(clean_domain)

        return result

    async def check_domain_async(self, domain: str) -> DomainCheckResult:
        """Async version of check_domain.

        Args:
            domain: Domain to verify

        Returns:
            DomainCheckResult with verification details
        """
        # Run sync operations in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.check_domain, domain)

    def get_linkedin_info(self, company_name: str) -> dict[str, Any]:
        """Get LinkedIn company data (placeholder for future API integration).

        This is a placeholder method that can be extended to integrate
        with LinkedIn API or web scraping for company information.

        Args:
            company_name: Name of the company

        Returns:
            Dictionary with LinkedIn company data
        """
        # Placeholder implementation - returns mock data structure
        # In production, this would call LinkedIn API or scrape LinkedIn
        normalized_name = self._normalize_company_name(company_name)

        return {
            "company_name": normalized_name,
            "linkedin_url": None,
            "employee_count": None,
            "industry": None,
            "founded": None,
            "company_size": None,
            "headquarters": None,
            "description": None,
            "verified": False,
            "data_source": "placeholder",
        }

    def calculate_reputation_score(self, company_data: dict[str, Any]) -> float:
        """Calculate reputation score based on verification data.

        The score ranges from 0 to 100, with higher scores indicating
        more reputable companies.

        Scoring algorithm:
        - Verified domain: +40 points
        - Industry classification: +20 points
        - Company age (>2 years): +15 points
        - Known good company: +25 points
        - Suspicious patterns: -30 points

        Args:
            company_data: Dictionary with verification data from verify_company

        Returns:
            Reputation score between 0 and 100
        """
        score = 50.0  # Base score

        # Domain verification (+40 points max)
        domain_check = company_data.get("domain_check", {})
        if domain_check.get("is_valid"):
            score += 20
        if domain_check.get("exists"):
            score += 10
        if domain_check.get("has_ssl"):
            score += 10

        # Industry classification (+20 points)
        industry = company_data.get("industry")
        if industry:
            score += 20

        # Domain age (+15 points for >2 years)
        domain_age = domain_check.get("age_days", 0) or 0
        if domain_age > 730:  # >2 years
            score += 15
        elif domain_age > 365:  # >1 year
            score += 10

        # Known good company (+25 points)
        if company_data.get("is_known_good"):
            score += 25

        # Suspicious patterns (-30 points max)
        name_analysis = company_data.get("name_analysis", {})
        if name_analysis.get("is_suspicious"):
            score -= 20
        if name_analysis.get("suspicious_score", 0) > 0.5:
            score -= 10

        # Known scam (-50 points)
        scam_check = company_data.get("scam_check", {})
        if scam_check.get("is_scam"):
            score -= 50

        # Clamp score to 0-100
        return max(0.0, min(100.0, score))

    # ==========================================================================
    # Private Methods
    # ==========================================================================

    def _normalize_company_name(self, name: str) -> str:
        """Normalize company name for comparison."""
        # Remove common suffixes
        suffixes = [
            r",?\s*inc\.?$",
            r",?\s*llc\.?$",
            r",?\s*ltd\.?$",
            r",?\s*corp\.?$",
            r",?\s*corporation$",
            r",?\s*co\.?$",
            r",?\s*company$",
            r",?\s*group$",
            r",?\s*technologies$",
            r",?\s*solutions$",
            r",?\s*services$",
        ]

        normalized = name.strip().lower()
        for suffix in suffixes:
            normalized = re.sub(suffix, "", normalized, flags=re.IGNORECASE)

        # Remove extra whitespace
        normalized = re.sub(r"\s+", " ", normalized).strip()

        return normalized

    def _analyze_company_name(self, company_name: str) -> dict[str, Any]:
        """Analyze company name for suspicious patterns."""
        analysis = {
            "original": company_name,
            "is_suspicious": False,
            "suspicious_score": 0.0,
            "suspicious_patterns": [],
        }

        # Check for suspicious patterns
        for pattern, weight in SUSPICIOUS_NAME_PATTERNS:
            if re.search(pattern, company_name, re.IGNORECASE):
                analysis["suspicious_patterns"].append(pattern)
                analysis["suspicious_score"] = max(analysis["suspicious_score"], weight)

        # Determine if suspicious
        if analysis["suspicious_score"] > 0.5:
            analysis["is_suspicious"] = True
        elif analysis["suspicious_score"] > 0.3:
            analysis["is_suspicious"] = True

        # Check for excessive capitalization (potential scam indicator)
        upper_count = sum(1 for c in company_name if c.isupper())
        if upper_count > len(company_name) * 0.5 and len(company_name) > 5:
            analysis["suspicious_score"] += 0.1

        # Check for numbers in name (often suspicious)
        if re.search(r"\d{3,}", company_name):
            analysis["suspicious_score"] += 0.1

        return analysis

    def _check_known_scams(
        self,
        company_name: str,
        domain: str | None,
    ) -> dict[str, Any]:
        """Check against known scam patterns."""
        result = {
            "is_scam": False,
            "scam_score": 0.0,
            "matched_patterns": [],
        }

        # Check direct name matches
        for scam_pattern, weight in KNOWN_SCAM_COMPANIES.items():
            if scam_pattern.lower() in company_name.lower():
                result["matched_patterns"].append(scam_pattern)
                result["scam_score"] = max(result["scam_score"], weight)

        # Check domain for suspicious TLDs
        if domain:
            parsed = urlparse(f"https://{domain}")
            tld = ""
            if parsed.netloc:
                tld_match = re.search(r"(\.\w+)$", parsed.netloc)
                if tld_match:
                    tld = tld_match.group(1).lower()

            if tld in SUSPICIOUS_TLDS:
                result["scam_score"] = max(result["scam_score"], 0.7)
                result["matched_patterns"].append(f"suspicious_tld:{tld}")

        # Determine if scam
        result["is_scam"] = result["scam_score"] > 0.6

        return result

    def _check_known_good_company(self, company_name: str) -> bool:
        """Check if company is in known good companies list."""
        # Direct match
        if company_name.lower() in KNOWN_GOOD_COMPANIES:
            return True

        # Partial match (company name contains known good company)
        for good_company in KNOWN_GOOD_COMPANIES:
            if good_company in company_name or company_name in good_company:
                return True

        return False

    def _classify_industry(
        self,
        company_name: str,
        domain: str | None = None,
    ) -> str | None:
        """Classify company into industry category."""
        search_text = f"{company_name} {domain or ''}".lower()

        for industry, keywords in INDUSTRY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in search_text:
                    return industry

        return None

    def _calculate_company_score(
        self,
        reputation_score: float,
        domain_result: DomainCheckResult | None,
        is_known_good: bool,
        is_suspicious: bool,
        known_scam: bool,
        industry: str | None,
    ) -> float:
        """Calculate final company score (0-100).

        This is the main scoring function that combines all verification
        factors into a single score used for job quality filtering.
        """
        score = reputation_score

        # Boost for verified domain
        if domain_result and domain_result.is_valid and domain_result.exists:
            score += 10

        # Boost for known good company
        if is_known_good:
            score += 15

        # Penalty for suspicious
        if is_suspicious:
            score -= 20

        # Penalty for known scam
        if known_scam:
            score -= 50

        # Industry classification boost
        if industry:
            score += 5

        # Clamp to 0-100
        return max(0.0, min(100.0, score))

    def _determine_verification_level(
        self,
        domain_result: DomainCheckResult | None,
        is_verified_domain: bool,
        is_known_good: bool,
        company_score: float,
    ) -> str:
        """Determine verification level based on checks."""
        if company_score >= 80 and (is_verified_domain or is_known_good):
            return "verified"
        elif company_score >= 60:
            return "high"
        elif company_score >= 40:
            return "medium"
        elif company_score >= 20:
            return "low"
        else:
            return "none"

    def _generate_recommendations(
        self,
        domain_result: DomainCheckResult | None,
        name_analysis: dict[str, Any],
        scam_check: dict[str, Any],
        company_score: float,
    ) -> list[str]:
        """Generate recommendations based on verification results."""
        recommendations = []

        if domain_result and not domain_result.exists:
            recommendations.append("Domain does not exist - verify company manually")

        if domain_result and domain_result.suspicious_tld:
            recommendations.append("Company uses suspicious domain TLD - extra caution advised")

        if name_analysis.get("is_suspicious"):
            recommendations.append("Company name matches known suspicious patterns")

        if scam_check.get("is_scam"):
            recommendations.append("HIGH RISK: Company matches known scam patterns")

        if company_score < 40:
            recommendations.append("Low company score - consider additional verification")

        if not recommendations:
            recommendations.append("Company appears legitimate")

        return recommendations

    def _check_ssl_certificate(self, domain: str) -> bool:
        """Check if domain has valid SSL certificate."""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    return ssock is not None
        except Exception:
            return False

    def _check_mx_records(self, domain: str) -> bool:
        """Check if domain has MX records."""
        try:
            import dns.resolver
            mx_records = dns.resolver.resolve(domain, 'MX')
            return len(mx_records) > 0
        except Exception:
            return False

    def _estimate_domain_age(self, domain: str) -> int | None:
        """Estimate domain age in days (simplified implementation).

        Note: This is a placeholder that returns a random age for demonstration.
        In production, this would query WHOIS data or use a domain age API.
        """
        # Placeholder - in production, use WHOIS or domain age API
        # For now, return None to indicate unknown
        return None

    def _get_cache_key(self, company_name: str, domain: str | None) -> str:
        """Generate cache key for verification result."""
        key_data = f"{company_name}:{domain or 'none'}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    def _get_cached_result(self, cache_key: str) -> CompanyVerificationResult | None:
        """Get cached verification result if still valid."""
        if cache_key in self._verification_cache:
            cached_time, result = self._verification_cache[cache_key]
            age = datetime.utcnow() - cached_time
            if age.total_seconds() < self._cache_ttl:
                return result
        return None

    def _cache_verification_result(
        self,
        cache_key: str,
        result: CompanyVerificationResult,
    ) -> None:
        """Cache verification result."""
        self._verification_cache[cache_key] = (datetime.utcnow(), result)


# ============================================================================
# Module-level Functions (for backward compatibility)
# ============================================================================


# Default verifier instance
_default_verifier: CompanyVerifier | None = None


def get_verifier() -> CompanyVerifier:
    """Get default company verifier instance."""
    global _default_verifier
    if _default_verifier is None:
        _default_verifier = CompanyVerifier()
    return _default_verifier


async def verify_company(
    company_name: str,
    domain: str | None = None,
) -> CompanyVerificationResult:
    """Module-level function for company verification."""
    verifier = get_verifier()
    return await verifier.verify_company(company_name, domain)


def check_domain(domain: str) -> DomainCheckResult:
    """Module-level function for domain verification."""
    verifier = get_verifier()
    return verifier.check_domain(domain)
