"""
Salary enrichment service for job postings.

Provides:
- Salary estimation from job description
- Salary data aggregation from multiple sources
- Market rate analysis
- Currency conversion
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import re
import logging

logger = logging.getLogger(__name__)


class SalarySource(str, Enum):
    """Sources of salary data."""
    LISTED = "listed"  # Listed in job posting
    ESTIMATED = "estimated"  # Estimated from description
    MARKET_DATA = "market_data"  # From market data sources
    USER_REPORTED = "user_reported"  # Reported by users


class Currency(str, Enum):
    """Supported currencies."""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CAD = "CAD"
    AUD = "AUD"
    INR = "INR"


@dataclass
class SalaryRange:
    """A salary range with metadata."""
    min_amount: float
    max_amount: float
    currency: Currency
    period: str  # "hourly", "monthly", "annual"
    source: SalarySource
    confidence: float = 0.5
    median: Optional[float] = None
    
    def __post_init__(self):
        if self.median is None:
            self.median = (self.min_amount + self.max_amount) / 2
    
    def to_annual(self) -> "SalaryRange":
        """Convert to annual salary."""
        if self.period == "annual":
            return self
        
        multiplier = {
            "hourly": 2080,  # 40 hours * 52 weeks
            "monthly": 12,
            "annual": 1,
        }
        
        mult = multiplier.get(self.period, 1)
        
        return SalaryRange(
            min_amount=self.min_amount * mult,
            max_amount=self.max_amount * mult,
            currency=self.currency,
            period="annual",
            source=self.source,
            confidence=self.confidence,
        )
    
    def to_dict(self) -> dict:
        return {
            "min": round(self.min_amount, 2),
            "max": round(self.max_amount, 2),
            "median": round(self.median or 0, 2),
            "currency": self.currency.value,
            "period": self.period,
            "source": self.source.value,
            "confidence": round(self.confidence, 2),
        }


# Salary patterns for extraction
SALARY_PATTERNS = [
    # $100k - $150k
    r'\$(\d+(?:,\d+)?)\s*k?\s*[-–to]+\s*\$(\d+(?:,\d+)?)\s*k?',
    # $100,000 - $150,000
    r'\$(\d{1,3}(?:,\d{3})*)\s*[-–to]+\s*\$(\d{1,3}(?:,\d{3})*)',
    # 100k-150k
    r'(\d+)k\s*[-–to]+\s*(\d+)k',
    # $100k+
    r'\$(\d+)k\+?',
    # $100,000+
    r'\$(\d{1,3}(?:,\d{3})*)\+?',
    # £50k - £70k
    r'£(\d+(?:,\d+)?)\s*k?\s*[-–to]+\s*£(\d+(?:,\d+)?)\s*k?',
    # €50k - €70k
    r'€(\d+(?:,\d+)?)\s*k?\s*[-–to]+\s*€(\d+(?:,\d+)?)\s*k?',
]

# Period indicators
PERIOD_INDICATORS = {
    "hourly": ["/hr", "/hour", "per hour", "hourly", "hr"],
    "monthly": ["/mo", "/month", "per month", "monthly"],
    "annual": ["/yr", "/year", "per year", "annual", "yearly"],
}

# Currency indicators
CURRENCY_INDICATORS = {
    Currency.USD: ["$", "USD", "dollars"],
    Currency.GBP: ["£", "GBP", "pounds"],
    Currency.EUR: ["€", "EUR", "euros"],
    Currency.CAD: ["CAD", "C$", "canadian"],
    Currency.AUD: ["AUD", "A$", "australian"],
    Currency.INR: ["₹", "INR", "rupees", "lakh", "lakhs"],
}

# Default salary ranges by job level (USD annual)
DEFAULT_SALARIES = {
    "intern": (30000, 50000),
    "junior": (50000, 80000),
    "mid": (80000, 120000),
    "senior": (120000, 180000),
    "lead": (150000, 220000),
    "principal": (180000, 280000),
    "director": (200000, 350000),
    "vp": (250000, 450000),
    "c_level": (300000, 600000),
}

# Salary modifiers by location (multiplier)
LOCATION_MODIFIERS = {
    "san francisco": 1.4,
    "new york": 1.35,
    "seattle": 1.25,
    "los angeles": 1.2,
    "boston": 1.2,
    "austin": 1.1,
    "denver": 1.05,
    "chicago": 1.0,
    "remote": 0.95,
    "london": 1.15,
    "berlin": 0.85,
    "toronto": 0.9,
    "sydney": 1.0,
    "bangalore": 0.35,
    "mumbai": 0.3,
}


class SalaryEnrichmentService:
    """
    Service for enriching jobs with salary data.
    
    Features:
    - Extract salary from job description
    - Estimate salary from title/requirements
    - Apply location modifiers
    - Currency conversion
    """
    
    def __init__(
        self,
        db_conn: Optional["asyncpg.Connection"] = None,
        default_currency: Currency = Currency.USD,
    ):
        self.db = db_conn
        self.default_currency = default_currency
    
    def extract_salary(self, text: str) -> Optional[SalaryRange]:
        """
        Extract salary information from text.
        
        Args:
            text: Job description or salary text
            
        Returns:
            SalaryRange if found, None otherwise
        """
        text_lower = text.lower()
        
        # Detect currency
        currency = self._detect_currency(text)
        
        # Detect period
        period = self._detect_period(text)
        
        # Try each pattern
        for pattern in SALARY_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                
                if len(groups) >= 2:
                    min_val = self._parse_salary_number(groups[0])
                    max_val = self._parse_salary_number(groups[1])
                else:
                    min_val = self._parse_salary_number(groups[0])
                    max_val = min_val * 1.2  # Estimate max as 20% higher
                
                # Handle 'k' suffix (thousands)
                if 'k' in text_lower[match.start():match.end()].lower():
                    min_val *= 1000
                    max_val *= 1000
                
                return SalaryRange(
                    min_amount=min_val,
                    max_amount=max_val,
                    currency=currency,
                    period=period,
                    source=SalarySource.LISTED,
                    confidence=0.9,
                )
        
        return None
    
    def estimate_salary(
        self,
        title: str,
        description: str = "",
        location: str = "",
        experience_years: Optional[int] = None,
    ) -> SalaryRange:
        """
        Estimate salary based on job metadata.
        
        Args:
            title: Job title
            description: Job description
            location: Job location
            experience_years: Required experience
            
        Returns:
            Estimated SalaryRange
        """
        # Determine job level
        level = self._determine_job_level(title, description, experience_years)
        
        # Get base salary range
        base_min, base_max = DEFAULT_SALARIES.get(level, (80000, 120000))
        
        # Apply location modifier
        location_modifier = self._get_location_modifier(location)
        base_min *= location_modifier
        base_max *= location_modifier
        
        # Adjust for specific role
        role_modifier = self._get_role_modifier(title)
        base_min *= role_modifier
        base_max *= role_modifier
        
        return SalaryRange(
            min_amount=round(base_min, 0),
            max_amount=round(base_max, 0),
            currency=self.default_currency,
            period="annual",
            source=SalarySource.ESTIMATED,
            confidence=0.5,
        )
    
    def enrich_job(
        self,
        job: dict,
    ) -> dict:
        """
        Enrich a job with salary data.
        
        Args:
            job: Job dictionary with title, description, location
            
        Returns:
            Job dictionary with added salary field
        """
        # Try to extract from description first
        description = job.get("description", "")
        salary = self.extract_salary(description)
        
        if not salary:
            # Try to estimate
            salary = self.estimate_salary(
                title=job.get("title", ""),
                description=description,
                location=job.get("location", ""),
                experience_years=job.get("experience_years"),
            )
        
        # Convert to annual for consistency
        annual_salary = salary.to_annual()
        
        job["salary"] = annual_salary.to_dict()
        job["salary_enriched_at"] = datetime.utcnow().isoformat()
        
        return job
    
    def _detect_currency(self, text: str) -> Currency:
        """Detect currency from text."""
        text_lower = text.lower()
        
        for currency, indicators in CURRENCY_INDICATORS.items():
            for indicator in indicators:
                if indicator.lower() in text_lower:
                    return currency
        
        return self.default_currency
    
    def _detect_period(self, text: str) -> str:
        """Detect salary period from text."""
        text_lower = text.lower()
        
        for period, indicators in PERIOD_INDICATORS.items():
            for indicator in indicators:
                if indicator in text_lower:
                    return period
        
        # Default to annual for yearly amounts > 10000
        return "annual"
    
    def _parse_salary_number(self, value: str) -> float:
        """Parse a salary number from string."""
        # Remove commas and spaces
        cleaned = value.replace(",", "").replace(" ", "").strip()
        
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    
    def _determine_job_level(
        self,
        title: str,
        description: str,
        experience_years: Optional[int],
    ) -> str:
        """Determine job level from title and description."""
        title_lower = title.lower()
        desc_lower = description.lower()
        
        # Check title for level indicators
        if any(w in title_lower for w in ["intern", "internship"]):
            return "intern"
        if any(w in title_lower for w in ["junior", "entry", "associate", "grad"]):
            return "junior"
        if any(w in title_lower for w in ["senior", "sr.", "sr "]):
            return "senior"
        if any(w in title_lower for w in ["lead", "staff", "principal"]):
            if "principal" in title_lower:
                return "principal"
            return "lead"
        if any(w in title_lower for w in ["director", "head of"]):
            return "director"
        if any(w in title_lower for w in ["vp", "vice president"]):
            return "vp"
        if any(w in title_lower for w in ["cto", "cio", "cfo", "ceo", "chief"]):
            return "c_level"
        
        # Use experience years if available
        if experience_years is not None:
            if experience_years < 1:
                return "intern"
            elif experience_years < 3:
                return "junior"
            elif experience_years < 5:
                return "mid"
            elif experience_years < 8:
                return "senior"
            elif experience_years < 12:
                return "lead"
            else:
                return "principal"
        
        # Check description for experience requirements
        exp_match = re.search(
            r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?experience',
            desc_lower
        )
        if exp_match:
            years = int(exp_match.group(1))
            if years < 2:
                return "junior"
            elif years < 5:
                return "mid"
            elif years < 8:
                return "senior"
            else:
                return "lead"
        
        # Default to mid-level
        return "mid"
    
    def _get_location_modifier(self, location: str) -> float:
        """Get salary modifier for location."""
        if not location:
            return 1.0
        
        location_lower = location.lower()
        
        for loc, modifier in LOCATION_MODIFIERS.items():
            if loc in location_lower:
                return modifier
        
        return 1.0
    
    def _get_role_modifier(self, title: str) -> float:
        """Get salary modifier for specific roles."""
        title_lower = title.lower()
        
        # High-demand roles
        if any(w in title_lower for w in ["machine learning", "ml engineer", "ai engineer"]):
            return 1.2
        if any(w in title_lower for w in ["devops", "sre", "platform"]):
            return 1.15
        if any(w in title_lower for w in ["security", "crypto"]):
            return 1.15
        if any(w in title_lower for w in ["data scientist", "data engineer"]):
            return 1.1
        if any(w in title_lower for w in ["full stack", "fullstack"]):
            return 1.05
        
        # Lower-demand roles
        if any(w in title_lower for w in ["qa", "test", "manual"]):
            return 0.9
        if any(w in title_lower for w in ["support", "helpdesk"]):
            return 0.85
        
        return 1.0


def enrich_job_salary(job: dict) -> dict:
    """Convenience function to enrich a job with salary."""
    service = SalaryEnrichmentService()
    return service.enrich_job(job)


def extract_salary_from_text(text: str) -> Optional[SalaryRange]:
    """Convenience function to extract salary from text."""
    service = SalaryEnrichmentService()
    return service.extract_salary(text)
