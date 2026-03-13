"""Salary Validation Module.

Provides salary validation and quality analysis for job listings.
Validates salary ranges against market data, detects suspicious patterns,
checks experience level alignment, and identifies unrealistic compensation.

This module integrates with the quality control fields added by the
migrations/035_job_quality_fields.sql migration.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from shared.logging_config import get_logger

logger = get_logger("sorce.salary_validator")


# ============================================================================
# Market Data Definitions
# ============================================================================

# Base salary ranges by role category (annual, USD)
# Includes: min, median, max, and standard deviation for outlier detection
ROLE_SALARY_DATA: dict[str, dict[str, float]] = {
    # Engineering roles
    "software engineer": {"min": 80000, "median": 130000, "max": 200000, "std": 30000},
    "senior software engineer": {"min": 120000, "median": 170000, "max": 250000, "std": 35000},
    "staff engineer": {"min": 180000, "median": 250000, "max": 350000, "std": 45000},
    "principal engineer": {"min": 200000, "median": 300000, "max": 400000, "std": 50000},
    "distinguished engineer": {"min": 250000, "median": 350000, "max": 500000, "std": 60000},
    "frontend developer": {"min": 70000, "median": 100000, "max": 150000, "std": 20000},
    "backend developer": {"min": 80000, "median": 120000, "max": 180000, "std": 25000},
    "full stack developer": {"min": 80000, "median": 120000, "max": 180000, "std": 25000},
    "devops engineer": {"min": 100000, "median": 140000, "max": 200000, "std": 25000},
    "site reliability engineer": {"min": 110000, "median": 150000, "max": 220000, "std": 28000},
    "cloud engineer": {"min": 100000, "median": 140000, "max": 200000, "std": 25000},
    "data engineer": {"min": 90000, "median": 130000, "max": 180000, "std": 23000},
    "data scientist": {"min": 100000, "median": 140000, "max": 200000, "std": 25000},
    "machine learning engineer": {"min": 120000, "median": 170000, "max": 250000, "std": 35000},
    "ml engineer": {"min": 120000, "median": 170000, "max": 250000, "std": 35000},
    "ai engineer": {"min": 130000, "median": 180000, "max": 280000, "std": 40000},
    "security engineer": {"min": 120000, "median": 160000, "max": 240000, "std": 30000},
    "penetration tester": {"min": 100000, "median": 140000, "max": 200000, "std": 25000},
    # Product roles
    "product manager": {"min": 100000, "median": 140000, "max": 200000, "std": 25000},
    "senior product manager": {"min": 140000, "median": 180000, "max": 250000, "std": 30000],
    "principal product manager": {"min": 180000, "median": 230000, "max": 320000, "std": 40000},
    "product owner": {"min": 80000, "median": 120000, "max": 170000, "std": 22000},
    "associate product manager": {"min": 70000, "median": 100000, "max": 140000, "std": 18000},
    # Design roles
    "ux designer": {"min": 70000, "median": 100000, "max": 140000, "std": 18000},
    "ui designer": {"min": 65000, "median": 95000, "max": 130000, "std": 16000},
    "product designer": {"min": 80000, "median": 120000, "max": 170000, "std": 22000},
    "senior designer": {"min": 100000, "median": 140000, "max": 200000, "std": 25000},
    "design lead": {"min": 130000, "median": 170000, "max": 240000, "std": 30000},
    "ux researcher": {"min": 70000, "median": 100000, "max": 150000, "std": 20000},
    # Management roles
    "engineering manager": {"min": 150000, "median": 200000, "max": 280000, "std": 35000},
    "director of engineering": {"min": 200000, "median": 280000, "max": 380000, "std": 50000},
    "vp of engineering": {"min": 280000, "median": 380000, "max": 500000, "std": 70000},
    "cto": {"min": 200000, "median": 300000, "max": 450000, "std": 70000},
    "vp of product": {"min": 250000, "median": 350000, "max": 480000, "std": 65000},
    "director of product": {"min": 180000, "median": 240000, "max": 320000, "std": 40000},
    # Sales & Marketing
    "sales representative": {"min": 50000, "median": 75000, "max": 120000, "std": 20000},
    "account executive": {"min": 60000, "median": 100000, "max": 160000, "std": 25000},
    "sales manager": {"min": 80000, "median": 120000, "max": 180000, "std": 25000},
    "marketing manager": {"min": 70000, "median": 100000, "max": 140000, "std": 18000},
    "growth marketer": {"min": 70000, "median": 100000, "max": 150000, "std": 20000},
    # Operations
    "project manager": {"min": 70000, "median": 100000, "max": 150000, "std": 20000},
    "program manager": {"min": 90000, "median": 130000, "max": 180000, "std": 23000},
    "scrum master": {"min": 80000, "median": 110000, "max": 150000, "std": 18000},
    "business analyst": {"min": 70000, "median": 100000, "max": 140000, "std": 18000},
    # QA & Support
    "qa engineer": {"min": 60000, "median": 85000, "max": 120000, "std": 15000},
    "sdET": {"min": 80000, "median": 110000, "max": 150000, "std": 18000},
    "customer support": {"min": 40000, "median": 55000, "max": 75000, "std": 10000},
    "technical support": {"min": 50000, "median": 70000, "max": 100000, "std": 13000},
}

# Location multipliers for salary adjustment
LOCATION_MULTIPLIERS: dict[str, float] = {
    # Tier 1 - Premium tech hubs (1.35-1.50)
    "san francisco": 1.50,
    "sf": 1.50,
    "palo alto": 1.50,
    "menlo park": 1.45,
    "mountain view": 1.45,
    "cupertino": 1.45,
    "sunnyvale": 1.40,
    "new york": 1.40,
    "nyc": 1.40,
    "manhattan": 1.40,
    # Tier 2 - Major tech hubs (1.20-1.35)
    "seattle": 1.30,
    "boston": 1.25,
    "cambridge": 1.25,
    "los angeles": 1.20,
    "la": 1.20,
    "san diego": 1.20,
    "washington": 1.20,
    "dc": 1.20,
    "washington, dc": 1.20,
    "denver": 1.20,
    "austin": 1.20,
    "chicago": 1.15,
    # Tier 3 - Growing tech (1.00-1.15)
    "atlanta": 1.10,
    "miami": 1.10,
    "dallas": 1.05,
    "phoenix": 1.05,
    "philadelphia": 1.05,
    "portland": 1.10,
    "raleigh": 1.10,
    "minneapolis": 1.05,
    "detroit": 1.00,
    # Standard/Remote (0.90-1.00)
    "remote": 1.00,
    "charlotte": 0.95,
    "tampa": 0.95,
    "orlando": 0.95,
    "las vegas": 0.95,
    "salt lake city": 0.95,
    # Lower cost areas (0.80-0.90)
    "indianapolis": 0.90,
    "columbus": 0.90,
    "kansas city": 0.90,
    "milwaukee": 0.90,
    "oklahoma city": 0.85,
    "omaha": 0.85,
    "albuquerque": 0.85,
}

# Experience level multipliers
EXPERIENCE_LEVELS: dict[str, tuple[float, float]] = {
    "intern": (0.4, 0.6),
    "entry level": (0.5, 0.7),
    "junior": (0.6, 0.8),
    "mid": (0.8, 1.1),
    "mid-level": (0.8, 1.1),
    "senior": (1.1, 1.4),
    "staff": (1.3, 1.6),
    "principal": (1.5, 1.9),
    "lead": (1.2, 1.5),
    "director": (1.5, 2.0),
    "vp": (1.8, 2.5),
    "executive": (2.0, 3.0),
}

# Suspicious salary thresholds
SUSPICIOUS_LOW_ANNUAL = 25000  # Below $25k/year is likely fake
SUSPICIOUS_HIGH_ANNUAL = 500000  # Above $500k/year needs verification
STANDARD_DEVIATIONS_OUTLIER = 3  # Flag salaries beyond 3 std deviations

# Unrealistic salary range ratios
MAX_RANGE_RATIO = 3.0  # Max range should not exceed 3x min


@dataclass
class ValidationResult:
    """Result of salary validation for a job listing."""

    is_valid: bool = True
    salary_validated: bool = False
    salary_validation_notes: list[str] = field(default_factory=list)
    quality_flags: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "is_valid": self.is_valid,
            "salary_validated": self.salary_validated,
            "salary_validation_notes": self.salary_validation_notes,
            "quality_flags": self.quality_flags,
        }


class SalaryValidator:
    """Validates salary data for job listings.

    This class analyzes salary information in job postings for quality control,
    comparing against market rates, detecting suspicious patterns, and checking
    for consistency with role and experience level.
    """

    def __init__(self, outlier_threshold: float = 3.0) -> None:
        """Initialize the salary validator.

        Args:
            outlier_threshold: Number of standard deviations to use for outlier
                             detection. Default is 3.0 (3 sigma).
        """
        self.outlier_threshold = outlier_threshold
        logger.info("SalaryValidator initialized with threshold: %s", outlier_threshold)

    def validate_salary(self, job_data: dict[str, Any]) -> dict[str, Any]:
        """Validate salary information for a job listing.

        Args:
            job_data: Dictionary containing job information with keys like:
                     - title: Job title
                     - salary_min: Minimum salary (optional)
                     - salary_max: Maximum salary (optional)
                     - location: Job location (optional)
                     - description: Job description text (optional)
                     - experience_level: Expected experience level (optional)

        Returns:
            Dictionary with validation result containing:
             - is_valid: Boolean indicating if salary is valid
             - salary_validated: Boolean indicating if validation was performed
             - salary_validation_notes: List of validation notes/warnings
             - quality_flags: Dictionary with detailed validation flags
        """
        logger.debug("Validating salary for job: %s", job_data.get("title", "unknown"))

        notes: list[str] = []
        quality_flags: dict[str, Any] = {}

        salary_min = job_data.get("salary_min")
        salary_max = job_data.get("salary_max")
        title = job_data.get("title", "")
        location = job_data.get("location", "")
        description = job_data.get("description", "")
        experience_level = job_data.get("experience_level", "")

        # If no salary data at all, mark as not validated but not invalid
        if salary_min is None and salary_max is None:
            # Check if competitors typically list salary
            has_competitor_salary = self._check_competitor_salary_mentioned(description)
            if has_competitor_salary:
                notes.append("Missing salary while competitors list compensation")
                quality_flags["missing_salary_with_competitors"] = True
                quality_flags["salary_validated"] = False
                return {
                    "is_valid": True,
                    "salary_validated": False,
                    "salary_validation_notes": notes,
                    "quality_flags": quality_flags,
                }

            # No salary data and no competitor mentions - just note it
            quality_flags["salary_validated"] = False
            quality_flags["no_salary_data"] = True
            return {
                "is_valid": True,
                "salary_validated": False,
                "salary_validation_notes": notes,
                "quality_flags": quality_flags,
            }

        # Have salary data - perform validation
        salary_validated = True
        quality_flags["salary_validated"] = True
        is_valid = True

        # Step 1: Check salary consistency
        if salary_min is not None and salary_max is not None:
            consistency_result = self.check_salary_consistency(salary_min, salary_max)
            notes.extend(consistency_result["notes"])
            quality_flags["consistency"] = consistency_result["flags"]
            if not consistency_result["is_valid"]:
                is_valid = False

        # Step 2: Get market rate
        market_rate = self.get_market_rate(title, location)
        quality_flags["market_rate"] = market_rate

        # Step 3: Compare to market
        if salary_min is not None and salary_max is not None:
            comparison = self.compare_to_market(salary_min, salary_max, title, location)
            notes.extend(comparison["notes"])
            quality_flags["market_comparison"] = comparison["flags"]
            if comparison["is_outlier"]:
                is_valid = False

        # Step 4: Check experience level alignment
        if experience_level and (salary_min is not None or salary_max is not None):
            exp_result = self._check_experience_alignment(
                salary_min, salary_max, experience_level, market_rate
            )
            notes.extend(exp_result["notes"])
            quality_flags["experience_alignment"] = exp_result["flags"]

        logger.debug(
            "Salary validation complete (valid: %s): %s",
            is_valid,
            job_data.get("title", "unknown"),
        )

        return {
            "is_valid": is_valid,
            "salary_validated": salary_validated,
            "salary_validation_notes": notes,
            "quality_flags": quality_flags,
        }

    def get_market_rate(self, role: str, location: str) -> dict[str, Any]:
        """Get market salary data for a role and location.

        Args:
            role: Job title or role description
            location: Job location

        Returns:
            Dictionary containing market rate data:
             - median: Expected median salary
             - min: Expected minimum salary
             - max: Expected maximum salary
             - std: Standard deviation
             - location_multiplier: Applied location multiplier
             - role_matched: Whether role was matched to known roles
        """
        role_lower = role.lower()
        location_lower = location.lower() if location else ""

        # Find matching role
        role_data = None
        matched_role = None

        for key, data in ROLE_SALARY_DATA.items():
            if key in role_lower:
                role_data = data
                matched_role = key
                break

        # If no direct match, try word-based matching
        if not role_data:
            for key, data in ROLE_SALARY_DATA.items():
                words = key.split()
                if any(w in role_lower for w in words):
                    role_data = data
                    matched_role = key
                    break

        if not role_data:
            # Return default engineering salary range
            return {
                "median": 130000,
                "min": 90000,
                "max": 180000,
                "std": 25000,
                "location_multiplier": self._get_location_multiplier(location_lower),
                "role_matched": False,
                "matched_role": None,
            }

        # Get location multiplier
        location_multiplier = self._get_location_multiplier(location_lower)

        # Calculate adjusted salaries
        min_salary = role_data["min"] * location_multiplier
        median_salary = role_data["median"] * location_multiplier
        max_salary = role_data["max"] * location_multiplier
        std_salary = role_data["std"] * location_multiplier

        return {
            "median": int(median_salary),
            "min": int(min_salary),
            "max": int(max_salary),
            "std": int(std_salary),
            "location_multiplier": location_multiplier,
            "role_matched": True,
            "matched_role": matched_role,
        }

    def compare_to_market(
        self,
        salary_min: int,
        salary_max: int,
        role: str,
        location: str,
    ) -> dict[str, Any]:
        """Compare salary range against market rates.

        Args:
            salary_min: Minimum salary
            salary_max: Maximum salary
            role: Job title or role description
            location: Job location

        Returns:
            Dictionary containing comparison results:
             - is_outlier: Boolean indicating if salary is an outlier
             - notes: List of validation notes
             - flags: Dictionary with comparison details
        """
        market = self.get_market_rate(role, location)
        median = market["median"]
        std = market["std"]

        notes: list[str] = []
        flags: dict[str, Any] = {}

        # Calculate the midpoint of the offered salary
        if salary_min and salary_max:
            midpoint = (salary_min + salary_max) / 2
        elif salary_max:
            midpoint = salary_max
        elif salary_min:
            midpoint = salary_min
        else:
            return {
                "is_outlier": False,
                "notes": notes,
                "flags": {"error": "No salary values provided"},
            }

        # Calculate deviation from median
        deviation = abs(midpoint - median)
        std_deviations = deviation / std if std > 0 else 0

        flags["midpoint"] = midpoint
        flags["market_median"] = median
        flags["deviation_from_median"] = deviation
        flags["std_deviations"] = std_deviations
        flags["is_suspiciously_low"] = midpoint < median * 0.5
        flags["is_suspiciously_high"] = midpoint > median * 2.0

        # Check for outlier (beyond threshold standard deviations)
        is_outlier = std_deviations > self.outlier_threshold

        if is_outlier:
            if midpoint < median:
                notes.append(
                    f"Salary significantly below market (${midpoint:,.0f} vs ${median:,.0f} median)"
                )
                flags["outlier_type"] = "below_market"
            else:
                notes.append(
                    f"Salary significantly above market (${midpoint:,.0f} vs ${median:,.0f} median)"
                )
                flags["outlier_type"] = "above_market"
        else:
            # Add contextual notes even for non-outliers
            if flags["is_suspiciously_low"]:
                notes.append("Salary appears unusually low for this role")
            elif flags["is_suspiciously_high"]:
                notes.append("Salary appears unusually high for this role")

        # Add percentile information
        if midpoint < median:
            percentile = self._calculate_percentile(midpoint, median, std, "below")
        else:
            percentile = self._calculate_percentile(midpoint, median, std, "above")

        flags["percentile"] = percentile

        return {
            "is_outlier": is_outlier,
            "notes": notes,
            "flags": flags,
        }

    def check_salary_consistency(self, salary_min: int, salary_max: int) -> dict[str, Any]:
        """Check if salary range makes sense internally.

        Args:
            salary_min: Minimum salary
            salary_max: Maximum salary

        Returns:
            Dictionary containing consistency check results:
             - is_valid: Boolean indicating if range is consistent
             - notes: List of validation notes
             - flags: Dictionary with consistency details
        """
        notes: list[str] = []
        flags: dict[str, Any] = {}
        is_valid = True

        # Handle None values
        if salary_min is None and salary_max is None:
            return {
                "is_valid": True,
                "notes": notes,
                "flags": {"no_salary_data": True},
            }

        # Use available values
        min_val = salary_min if salary_min is not None else 0
        max_val = salary_max if salary_max is not None else 0

        # Ensure min <= max
        if min_val > 0 and max_val > 0 and min_val > max_val:
            notes.append("Minimum salary exceeds maximum salary")
            flags["min_exceeds_max"] = True
            is_valid = False

        # Check for negative values
        if min_val < 0 or max_val < 0:
            notes.append("Salary cannot be negative")
            flags["negative_salary"] = True
            is_valid = False

        # Check for zero
        if min_val == 0 and max_val == 0:
            notes.append("Salary cannot be zero")
            flags["zero_salary"] = True
            is_valid = False

        # Check for unrealistic ranges (e.g., $30k-$500k)
        if min_val > 0 and max_val > 0:
            range_ratio = max_val / min_val if min_val > 0 else float("inf")

            flags["range_ratio"] = range_ratio

            # Extremely wide ranges are suspicious
            if range_ratio > MAX_RANGE_RATIO * 2:  # More than 6x
                notes.append(
                    f"Unrealistic salary range: ${min_val:,.0f} to ${max_val:,.0f} ({range_ratio:.1f}x range)"
                )
                flags["unrealistic_range"] = True
                flags["unrealistic_range_severity"] = "high"
                is_valid = False
            elif range_ratio > MAX_RANGE_RATIO:
                notes.append(
                    f"Very wide salary range: ${min_val:,.0f} to ${max_val:,.0f} ({range_ratio:.1f}x range)"
                )
                flags["wide_range"] = True
                flags["unrealistic_range_severity"] = "medium"

            # Check for specific suspicious patterns
            # e.g., $30k-$500k
            if min_val < 40000 and max_val > 400000:
                notes.append("Suspicious range: very low minimum with very high maximum")
                flags["suspicious_pattern"] = True
                is_valid = False

            # Check for suspiciously round numbers that might be fake
            if max_val > 0:
                # Common fake salary patterns
                if max_val in [100000, 150000, 200000, 250000, 300000, 500000]:
                    # Only flag if exact match (might be auto-filled)
                    if max_val % 1000 == 0:
                        flags["round_number_max"] = True

        # Check for suspiciously low annual salaries
        annual_min = min_val * 52 if min_val > 0 else 0  # Assuming hourly
        if annual_min > 0 and annual_min < SUSPICIOUS_LOW_ANNUAL:
            notes.append(f"Annual salary appears unrealistically low: ${annual_min:,.0f}")
            flags["suspiciously_low"] = True
            is_valid = False

        # Check for suspiciously high annual salaries
        annual_max = max_val * 52 if max_val > 0 else 0
        if annual_max > SUSPICIOUS_HIGH_ANNUAL:
            notes.append(f"Annual salary exceeds typical bounds: ${annual_max:,.0f}")
            flags["suspiciously_high"] = True
            flags["high_salary_severity"] = "warning" if annual_max < 750000 else "critical"

        return {
            "is_valid": is_valid,
            "notes": notes,
            "flags": flags,
        }

    def _get_location_multiplier(self, location: str) -> float:
        """Get location multiplier from location string.

        Args:
            location: Location string to look up

        Returns:
            Location multiplier (default 1.0)
        """
        if not location:
            return 1.0

        location_lower = location.lower()

        for loc_key, mult in LOCATION_MULTIPLIERS.items():
            if loc_key in location_lower:
                return mult

        return 1.0

    def _calculate_percentile(
        self,
        value: float,
        median: float,
        std: float,
        direction: str,
    ) -> str:
        """Calculate approximate percentile for a value.

        Args:
            value: The value to calculate percentile for
            median: The median value
            std: Standard deviation
            direction: 'above' or 'below' median

        Returns:
            String describing approximate percentile
        """
        if std == 0:
            return "unknown"

        z_score = abs(value - median) / std

        # Approximate percentile from z-score
        if z_score < 0.5:
            return "50th" if direction == "below" else "50th"
        elif z_score < 1.0:
            return "25th" if direction == "below" else "75th"
        elif z_score < 1.5:
            return "10th" if direction == "below" else "90th"
        elif z_score < 2.0:
            return "5th" if direction == "below" else "95th"
        elif z_score < 2.5:
            return "2nd" if direction == "below" else "98th"
        else:
            return "1st" if direction == "below" else "99th"

    def _check_competitor_salary_mentioned(self, description: str) -> bool:
        """Check if competitors typically list salary in job descriptions.

        Args:
            description: Job description text

        Returns:
            Boolean indicating if salary is typically mentioned
        """
        if not description:
            return False

        # Look for competitor/salary-related keywords
        competitor_patterns = [
            "competitive salary",
            "market rate",
            "salary range",
            "compensation package",
            "benefits include",
            "salary:",
            "salary up to",
            "earn up to",
            "pay range",
        ]

        description_lower = description.lower()
        return any(pattern in description_lower for pattern in competitor_patterns)

    def _check_experience_alignment(
        self,
        salary_min: int | None,
        salary_max: int | None,
        experience_level: str,
        market_rate: dict[str, Any],
    ) -> dict[str, Any]:
        """Check if salary aligns with experience level.

        Args:
            salary_min: Minimum salary
            salary_max: Maximum salary
            experience_level: Experience level string
            market_rate: Market rate data

        Returns:
            Dictionary with alignment check results
        """
        notes: list[str] = []
        flags: dict[str, Any] = {}
        is_aligned = True

        exp_lower = experience_level.lower()

        # Find matching experience level
        exp_multipliers = None
        for level, multipliers in EXPERIENCE_LEVELS.items():
            if level in exp_lower:
                exp_multipliers = multipliers
                flags["matched_level"] = level
                break

        if not exp_multipliers:
            return {
                "notes": notes,
                "flags": {"unrecognized_level": True},
            }

        min_mult, max_mult = exp_multipliers
        median = market_rate.get("median", 130000)

        # Calculate expected salary range based on experience
        expected_min = median * min_mult
        expected_max = median * max_mult

        flags["expected_min"] = expected_min
        flags["expected_max"] = expected_max
        flags["experience_multiplier_range"] = f"{min_mult}x-{max_mult}x"

        # Check actual salary against expected range
        midpoint = 0
        if salary_min and salary_max:
            midpoint = (salary_min + salary_max) / 2
        elif salary_max:
            midpoint = salary_max
        elif salary_min:
            midpoint = salary_min

        if midpoint > 0:
            if midpoint < expected_min * 0.7:
                notes.append(
                    f"Salary below expected range for {experience_level} level"
                )
                flags["below_expected"] = True
                is_aligned = False
            elif midpoint > expected_max * 1.3:
                notes.append(
                    f"Salary above expected range for {experience_level} level"
                )
                flags["above_expected"] = True
                is_aligned = False

        return {
            "notes": notes,
            "flags": flags,
            "is_aligned": is_aligned,
        }
