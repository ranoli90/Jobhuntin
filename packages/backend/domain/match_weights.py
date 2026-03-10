"""Match Weights Configuration System - Per-tenant job matching customization.

This module provides a comprehensive system for managing match weights and scoring
configurations on a per-tenant basis, allowing customization of job matching algorithms.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

import asyncpg

from shared.logging_config import get_logger

logger = get_logger("sorce.match_weights")


class WeightCategory(Enum):
    """Categories of match weights for different aspects of job matching."""

    SKILLS_MATCH = "skills_match"
    EXPERIENCE_MATCH = "experience_match"
    LOCATION_MATCH = "location_match"
    SALARY_MATCH = "salary_match"
    EDUCATION_MATCH = "education_match"
    COMPANY_SIZE_MATCH = "company_size_match"
    REMOTE_WORK_MATCH = "remote_work_match"
    INDUSTRY_MATCH = "industry_match"
    JOB_TYPE_MATCH = "job_type_match"
    SENIORITY_MATCH = "seniority_match"


@dataclass
class WeightConfig:
    """Individual weight configuration for a specific category."""

    category: WeightCategory
    weight: float = 1.0  # Weight multiplier (0.0 to 2.0)
    enabled: bool = True
    priority: int = 1  # Priority level (1=highest, 5=lowest)
    custom_rules: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    last_updated: Optional[datetime] = None
    updated_by: Optional[str] = None


@dataclass
class TenantMatchConfig:
    """Complete match configuration for a tenant."""

    tenant_id: str
    weights: Dict[WeightCategory, WeightConfig] = field(default_factory=dict)
    global_multiplier: float = 1.0
    min_match_score: float = 0.3
    max_results: int = 100
    enable_ml_scoring: bool = True
    custom_scoring_rules: Dict[str, Any] = field(default_factory=dict)
    version: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None
    updated_by: Optional[str] = None


class MatchWeightsManager:
    """Manager for tenant-specific match weights configurations."""

    def __init__(self):
        """Initialize the match weights manager."""
        self._default_weights = self._create_default_weights()

    def _create_default_weights(self) -> Dict[WeightCategory, WeightConfig]:
        """Create default weight configurations."""
        return {
            WeightCategory.SKILLS_MATCH: WeightConfig(
                category=WeightCategory.SKILLS_MATCH,
                weight=1.5,
                enabled=True,
                priority=1,
                description="Weight for skills matching between user profile and job requirements",
                custom_rules={
                    "exact_match_bonus": 0.5,
                    "partial_match_penalty": 0.2,
                    "demand_score_weight": 0.3,
                    "category_boost": {
                        "programming": 0.2,
                        "data_science": 0.15,
                        "cloud_devops": 0.1,
                    },
                },
            ),
            WeightCategory.EXPERIENCE_MATCH: WeightConfig(
                category=WeightCategory.EXPERIENCE_MATCH,
                weight=1.2,
                enabled=True,
                priority=2,
                description="Weight for experience level matching",
                custom_rules={
                    "exact_years_bonus": 0.3,
                    "under_experience_penalty": 0.4,
                    "over_experience_penalty": 0.1,
                    "seniority_boost": {
                        "entry": 0.1,
                        "mid": 0.2,
                        "senior": 0.3,
                        "lead": 0.4,
                    },
                },
            ),
            WeightCategory.LOCATION_MATCH: WeightConfig(
                category=WeightCategory.LOCATION_MATCH,
                weight=1.0,
                enabled=True,
                priority=3,
                description="Weight for location and remote work preferences",
                custom_rules={
                    "exact_location_bonus": 0.4,
                    "same_region_bonus": 0.2,
                    "remote_work_bonus": 0.3,
                    "distance_penalty_per_mile": 0.001,
                    "max_distance_miles": 100,
                },
            ),
            WeightCategory.SALARY_MATCH: WeightConfig(
                category=WeightCategory.SALARY_MATCH,
                weight=0.8,
                enabled=True,
                priority=4,
                description="Weight for salary range matching",
                custom_rules={
                    "exact_match_bonus": 0.3,
                    "within_range_bonus": 0.2,
                    "below_expected_penalty": 0.3,
                    "above_expected_penalty": 0.1,
                    "salary_range_tolerance": 0.2,
                },
            ),
            WeightCategory.EDUCATION_MATCH: WeightConfig(
                category=WeightCategory.EDUCATION_MATCH,
                weight=0.6,
                enabled=True,
                priority=5,
                description="Weight for education level matching",
                custom_rules={
                    "degree_level_bonus": {
                        "high_school": 0.1,
                        "bachelor": 0.3,
                        "master": 0.4,
                        "phd": 0.5,
                    },
                    "field_relevance_bonus": 0.2,
                    "prestige_boost": 0.1,
                },
            ),
            WeightCategory.COMPANY_SIZE_MATCH: WeightConfig(
                category=WeightCategory.COMPANY_SIZE_MATCH,
                weight=0.4,
                enabled=True,
                priority=6,
                description="Weight for company size preferences",
                custom_rules={
                    "size_preference_bonus": {
                        "startup": 0.2,
                        "small": 0.1,
                        "medium": 0.3,
                        "large": 0.2,
                        "enterprise": 0.1,
                    }
                },
            ),
            WeightCategory.REMOTE_WORK_MATCH: WeightConfig(
                category=WeightCategory.REMOTE_WORK_MATCH,
                weight=0.7,
                enabled=True,
                priority=3,
                description="Weight for remote work compatibility",
                custom_rules={
                    "fully_remote_bonus": 0.4,
                    "hybrid_bonus": 0.2,
                    "onsite_penalty": 0.3,
                    "remote_experience_bonus": 0.2,
                },
            ),
            WeightCategory.INDUSTRY_MATCH: WeightConfig(
                category=WeightCategory.INDUSTRY_MATCH,
                weight=0.5,
                enabled=True,
                priority=7,
                description="Weight for industry experience matching",
                custom_rules={
                    "exact_industry_bonus": 0.3,
                    "related_industry_bonus": 0.15,
                    "industry_transfer_penalty": 0.2,
                },
            ),
            WeightCategory.JOB_TYPE_MATCH: WeightConfig(
                category=WeightCategory.JOB_TYPE_MATCH,
                weight=0.6,
                enabled=True,
                priority=8,
                description="Weight for job type (full-time, contract, etc.) matching",
                custom_rules={
                    "preferred_type_bonus": 0.3,
                    "acceptable_type_bonus": 0.15,
                    "unacceptable_type_penalty": 0.5,
                },
            ),
            WeightCategory.SENIORITY_MATCH: WeightConfig(
                category=WeightCategory.SENIORITY_MATCH,
                weight=0.9,
                enabled=True,
                priority=2,
                description="Weight for seniority level matching",
                custom_rules={
                    "exact_level_bonus": 0.4,
                    "one_level_difference_penalty": 0.2,
                    "two_level_difference_penalty": 0.4,
                    "promotion_readiness_bonus": 0.2,
                },
            ),
        }

    async def get_tenant_config(
        self, db_pool: asyncpg.Pool, tenant_id: str
    ) -> TenantMatchConfig:
        """Get match configuration for a specific tenant.

        Args:
            db_pool: Database connection pool
            tenant_id: Tenant identifier

        Returns:
            TenantMatchConfig with tenant-specific or default settings
        """
        try:
            async with db_pool.acquire() as conn:
                # Try to get tenant-specific configuration
                row = await conn.fetchrow(
                    """
                    SELECT config_data, version, created_at, updated_at, created_by, updated_by
                    FROM tenant_match_configs
                    WHERE tenant_id = $1
                    ORDER BY version DESC
                    LIMIT 1
                """,
                    tenant_id,
                )

                if row:
                    # Parse stored configuration
                    config_data = json.loads(row["config_data"])

                    # Reconstruct weight configurations
                    weights = {}
                    for cat_str, weight_data in config_data.get("weights", {}).items():
                        category = WeightCategory(cat_str)
                        weights[category] = WeightConfig(
                            category=category,
                            weight=weight_data.get("weight", 1.0),
                            enabled=weight_data.get("enabled", True),
                            priority=weight_data.get("priority", 1),
                            custom_rules=weight_data.get("custom_rules", {}),
                            description=weight_data.get("description", ""),
                            last_updated=datetime.fromisoformat(
                                weight_data["last_updated"]
                            )
                            if weight_data.get("last_updated")
                            else None,
                            updated_by=weight_data.get("updated_by"),
                        )

                    return TenantMatchConfig(
                        tenant_id=tenant_id,
                        weights=weights,
                        global_multiplier=config_data.get("global_multiplier", 1.0),
                        min_match_score=config_data.get("min_match_score", 0.3),
                        max_results=config_data.get("max_results", 100),
                        enable_ml_scoring=config_data.get("enable_ml_scoring", True),
                        custom_scoring_rules=config_data.get(
                            "custom_scoring_rules", {}
                        ),
                        version=row["version"],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                        created_by=row["created_by"],
                        updated_by=row["updated_by"],
                    )
                else:
                    # Return default configuration for new tenant
                    logger.info(f"Using default match config for tenant {tenant_id}")
                    return TenantMatchConfig(
                        tenant_id=tenant_id,
                        weights=self._default_weights.copy(),
                        global_multiplier=1.0,
                        min_match_score=0.3,
                        max_results=100,
                        enable_ml_scoring=True,
                        version=1,
                    )

        except Exception as e:
            logger.error(f"Failed to get tenant config for {tenant_id}: {e}")
            # Return default configuration on error
            return TenantMatchConfig(
                tenant_id=tenant_id,
                weights=self._default_weights.copy(),
                global_multiplier=1.0,
                min_match_score=0.3,
                max_results=100,
                enable_ml_scoring=True,
                version=1,
            )

    async def save_tenant_config(
        self,
        db_pool: asyncpg.Pool,
        config: TenantMatchConfig,
        updated_by: Optional[str] = None,
    ) -> bool:
        """Save match configuration for a tenant.

        Args:
            db_pool: Database connection pool
            config: TenantMatchConfig to save
            updated_by: User who made the update

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Prepare configuration data for storage
            weights_data = {}
            for category, weight_config in config.weights.items():
                weights_data[category.value] = {
                    "weight": weight_config.weight,
                    "enabled": weight_config.enabled,
                    "priority": weight_config.priority,
                    "custom_rules": weight_config.custom_rules,
                    "description": weight_config.description,
                    "last_updated": weight_config.last_updated.isoformat()
                    if weight_config.last_updated
                    else None,
                    "updated_by": weight_config.updated_by,
                }

            config_data = {
                "weights": weights_data,
                "global_multiplier": config.global_multiplier,
                "min_match_score": config.min_match_score,
                "max_results": config.max_results,
                "enable_ml_scoring": config.enable_ml_scoring,
                "custom_scoring_rules": config.custom_scoring_rules,
            }

            async with db_pool.acquire() as conn:
                # Increment version
                new_version = config.version + 1

                # Insert new configuration
                await conn.execute(
                    """
                    INSERT INTO tenant_match_configs (
                        tenant_id, config_data, version, created_at, updated_at, created_by, updated_by
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                    config.tenant_id,
                    json.dumps(config_data),
                    new_version,
                    config.created_at,
                    datetime.now(timezone.utc),
                    config.created_by,
                    updated_by,
                )

                logger.info(
                    f"Saved match config v{new_version} for tenant {config.tenant_id}"
                )
                return True

        except Exception as e:
            logger.error(f"Failed to save tenant config for {config.tenant_id}: {e}")
            return False

    async def update_weight(
        self,
        db_pool: asyncpg.Pool,
        tenant_id: str,
        category: WeightCategory,
        weight: float,
        enabled: bool = True,
        priority: int = 1,
        custom_rules: Optional[Dict[str, Any]] = None,
        updated_by: Optional[str] = None,
    ) -> bool:
        """Update a specific weight for a tenant.

        Args:
            db_pool: Database connection pool
            tenant_id: Tenant identifier
            category: Weight category to update
            weight: New weight value
            enabled: Whether the weight is enabled
            priority: Priority level
            custom_rules: Custom rules for the weight
            updated_by: User making the update

        Returns:
            True if updated successfully, False otherwise
        """
        try:
            # Get current configuration
            config = await self.get_tenant_config(db_pool, tenant_id)

            # Update the specific weight
            if category not in config.weights:
                config.weights[category] = self._default_weights[category]

            config.weights[category].weight = weight
            config.weights[category].enabled = enabled
            config.weights[category].priority = priority
            config.weights[category].last_updated = datetime.now(timezone.utc)
            config.weights[category].updated_by = updated_by

            if custom_rules:
                config.weights[category].custom_rules.update(custom_rules)

            # Save updated configuration
            return await self.save_tenant_config(db_pool, config, updated_by)

        except Exception as e:
            logger.error(f"Failed to update weight for tenant {tenant_id}: {e}")
            return False

    def calculate_match_score(
        self, config: TenantMatchConfig, match_data: Dict[str, Any]
    ) -> float:
        """Calculate match score using tenant-specific configuration.

        Args:
            config: Tenant match configuration
            match_data: Data about the match (skills, experience, etc.)

        Returns:
            Calculated match score (0.0 to 1.0)
        """
        total_score = 0.0
        total_weight = 0.0

        # HIGH: Normalize weights to ensure scores are consistent
        # First, calculate total enabled weight
        total_enabled_weight = sum(
            wc.weight for wc in config.weights.values() if wc.enabled
        )

        # Calculate scores for each enabled category
        for category, weight_config in config.weights.items():
            if not weight_config.enabled:
                continue

            category_score = self._calculate_category_score(
                category, match_data, weight_config
            )

            if category_score > 0:
                # HIGH: Normalize weight by total enabled weight to prevent score inflation
                normalized_weight = (
                    weight_config.weight / total_enabled_weight
                    if total_enabled_weight > 0
                    else 0.0
                )
                total_score += category_score * normalized_weight
                total_weight += normalized_weight

        # Apply global multiplier
        if total_weight > 0:
            base_score = (total_score / total_weight) * config.global_multiplier
        else:
            base_score = 0.0

        # Apply ML scoring if enabled
        if config.enable_ml_scoring and "ml_score" in match_data:
            ml_weight = 0.3  # ML score gets 30% weight
            base_score = (base_score * (1 - ml_weight)) + (
                match_data["ml_score"] * ml_weight
            )

        # Apply custom scoring rules
        base_score = self._apply_custom_scoring_rules(
            base_score, match_data, config.custom_scoring_rules
        )

        # Ensure score is within bounds
        final_score = max(0.0, min(1.0, base_score))

        # Apply minimum score threshold
        if final_score < config.min_match_score:
            final_score = 0.0

        return final_score

    def _calculate_category_score(
        self,
        category: WeightCategory,
        match_data: Dict[str, Any],
        weight_config: WeightConfig,
    ) -> float:
        """Calculate score for a specific category."""
        if category == WeightCategory.SKILLS_MATCH:
            return self._calculate_skills_score(match_data, weight_config)
        elif category == WeightCategory.EXPERIENCE_MATCH:
            return self._calculate_experience_score(match_data, weight_config)
        elif category == WeightCategory.LOCATION_MATCH:
            return self._calculate_location_score(match_data, weight_config)
        elif category == WeightCategory.SALARY_MATCH:
            return self._calculate_salary_score(match_data, weight_config)
        elif category == WeightCategory.EDUCATION_MATCH:
            return self._calculate_education_score(match_data, weight_config)
        elif category == WeightCategory.REMOTE_WORK_MATCH:
            return self._calculate_remote_work_score(match_data, weight_config)
        elif category == WeightCategory.SENIORITY_MATCH:
            return self._calculate_seniority_score(match_data, weight_config)
        else:
            # Default scoring for other categories
            return float(match_data.get(f"{category.value}_score", 0.0))

    def _calculate_skills_score(
        self, match_data: Dict[str, Any], weight_config: WeightConfig
    ) -> float:
        """Calculate skills matching score.

        HIGH: Enhanced to use rich skills metadata (confidence, years) for better matching.
        """
        user_skills = match_data.get("user_skills", [])
        job_skills = match_data.get("job_skills", [])

        if not user_skills or not job_skills:
            return 0.0

        # HIGH: Handle rich skills (dicts with confidence, years) or simple strings
        # Build skill map with confidence scores
        user_skill_map: dict[str, float] = {}  # skill_name -> confidence
        user_skill_years: dict[str, float] = {}  # skill_name -> years

        for skill in user_skills:
            if isinstance(skill, dict):
                skill_name = (
                    (skill.get("skill") or skill.get("name") or "").lower().strip()
                )
                confidence = float(skill.get("confidence", 0.5))
                years = (
                    float(skill.get("years_actual", 0))
                    if skill.get("years_actual")
                    else 0.0
                )
                if skill_name:
                    # Use highest confidence if skill appears multiple times
                    if (
                        skill_name not in user_skill_map
                        or confidence > user_skill_map[skill_name]
                    ):
                        user_skill_map[skill_name] = confidence
                        user_skill_years[skill_name] = years
            elif isinstance(skill, str):
                skill_name = skill.lower().strip()
                if skill_name:
                    user_skill_map[skill_name] = 0.5  # Default confidence
                    user_skill_years[skill_name] = 0.0

        # Calculate skill overlap with confidence weighting
        job_skill_set = {s.lower().strip() for s in job_skills if s}
        user_skill_set = set(user_skill_map.keys())
        matched_skills = user_skill_set.intersection(job_skill_set)
        exact_matches = len(matched_skills)

        total_job_skills = len(job_skill_set)
        if total_job_skills == 0:
            return 0.0

        # HIGH: Weight matches by confidence
        weighted_matches = sum(user_skill_map[skill] for skill in matched_skills)
        # Normalize by total possible confidence (if all skills matched with confidence 1.0)
        base_score = (
            weighted_matches / total_job_skills if total_job_skills > 0 else 0.0
        )

        # HIGH: Bonus for skills with years of experience
        years_bonus = sum(
            min(user_skill_years.get(skill, 0) / 10.0, 0.2)  # Max 0.2 bonus per skill
            for skill in matched_skills
        )
        base_score = min(1.0, base_score + years_bonus)

        # Apply custom rules
        rules = weight_config.custom_rules
        if rules:
            # Exact match bonus
            if exact_matches == total_job_skills and "exact_match_bonus" in rules:
                base_score += rules["exact_match_bonus"]

            # Partial match penalty
            if (
                exact_matches < total_job_skills * 0.5
                and "partial_match_penalty" in rules
            ):
                base_score *= 1 - rules["partial_match_penalty"]

            # Category boosts
            if "category_boost" in rules:
                category_boost = 0.0
                matched_skills = user_skill_set.intersection(job_skill_set)
                for skill in matched_skills:
                    for category, boost in rules["category_boost"].items():
                        # This would need actual skill categorization
                        pass
                base_score += category_boost

        return min(1.0, base_score)

    def _calculate_experience_score(
        self, match_data: Dict[str, Any], weight_config: WeightConfig
    ) -> float:
        """Calculate experience matching score."""
        user_years = match_data.get("user_experience_years", 0)
        required_years = match_data.get("required_experience_years", 0)

        if required_years == 0:
            return 1.0  # No experience requirement

        difference = abs(user_years - required_years)

        # Base score based on how close the experience matches
        if difference == 0:
            base_score = 1.0
        elif difference <= 2:
            base_score = 0.8
        elif difference <= 5:
            base_score = 0.6
        else:
            base_score = 0.3

        # Apply custom rules
        rules = weight_config.custom_rules
        if rules:
            if user_years >= required_years and "exact_years_bonus" in rules:
                base_score += rules["exact_years_bonus"]
            elif user_years < required_years and "under_experience_penalty" in rules:
                base_score *= 1 - rules["under_experience_penalty"]
            elif user_years > required_years and "over_experience_penalty" in rules:
                base_score *= 1 - rules["over_experience_penalty"]

        return min(1.0, base_score)

    def _calculate_location_score(
        self, match_data: Dict[str, Any], weight_config: WeightConfig
    ) -> float:
        """Calculate location matching score."""
        user_location = match_data.get("user_location", "")
        job_location = match_data.get("job_location", "")
        is_remote = match_data.get("is_remote", False)
        user_prefers_remote = match_data.get("user_prefers_remote", False)

        base_score = 0.0

        if is_remote and user_prefers_remote:
            base_score = 1.0
        elif not is_remote and user_location and job_location:
            # Simple location matching (would need more sophisticated geolocation)
            if user_location.lower() == job_location.lower():
                base_score = 1.0
            else:
                base_score = 0.5  # Partial match for same region
        elif is_remote and not user_prefers_remote:
            base_score = 0.3  # Remote job but user prefers onsite

        # Apply custom rules
        rules = weight_config.custom_rules
        if rules:
            if base_score == 1.0 and "exact_location_bonus" in rules:
                base_score += rules["exact_location_bonus"]
            elif is_remote and "remote_work_bonus" in rules:
                base_score += rules["remote_work_bonus"]

        return min(1.0, base_score)

    def _calculate_salary_score(
        self, match_data: Dict[str, Any], weight_config: WeightConfig
    ) -> float:
        """Calculate salary matching score."""
        user_min_salary = match_data.get("user_min_salary", 0)
        job_min_salary = match_data.get("job_min_salary", 0)
        job_max_salary = match_data.get("job_max_salary", 0)

        if user_min_salary == 0:
            return 1.0  # No salary preference

        base_score = 0.0

        if job_min_salary >= user_min_salary:
            # Job meets or exceeds user's minimum
            if job_max_salary > 0:
                # Check if user's salary is within job range
                if user_min_salary <= job_max_salary:
                    base_score = 1.0
                else:
                    base_score = 0.7  # Above job range but close
            else:
                base_score = 0.8  # No max salary specified
        else:
            # Job below user's minimum
            ratio = job_min_salary / user_min_salary
            base_score = max(0.0, ratio - 0.8)  # Penalize low salaries heavily

        # Apply custom rules
        rules = weight_config.custom_rules
        if rules:
            if base_score == 1.0 and "exact_match_bonus" in rules:
                base_score += rules["exact_match_bonus"]
            elif base_score < 0.5 and "below_expected_penalty" in rules:
                base_score *= 1 - rules["below_expected_penalty"]

        return min(1.0, base_score)

    def _calculate_education_score(
        self, match_data: Dict[str, Any], weight_config: WeightConfig
    ) -> float:
        """Calculate education matching score."""
        user_education = match_data.get("user_education_level", "")
        required_education = match_data.get("required_education_level", "")

        if not required_education:
            return 1.0  # No education requirement

        # Simple education level matching
        education_levels = ["high_school", "bachelor", "master", "phd"]

        try:
            user_level = education_levels.index(user_education.lower())
            required_level = education_levels.index(required_education.lower())
        except (ValueError, IndexError):
            return 0.5  # Unknown education levels

        if user_level >= required_level:
            base_score = 1.0
        elif user_level == required_level - 1:
            base_score = 0.7
        else:
            base_score = 0.3

        # Apply custom rules
        rules = weight_config.custom_rules
        if rules and "degree_level_bonus" in rules:
            bonus_map = rules["degree_level_bonus"]
            if user_education.lower() in bonus_map:
                base_score += bonus_map[user_education.lower()]

        return min(1.0, base_score)

    def _calculate_remote_work_score(
        self, match_data: Dict[str, Any], weight_config: WeightConfig
    ) -> float:
        """Calculate remote work compatibility score."""
        user_remote_preference = match_data.get(
            "user_remote_preference", ""
        )  # "remote", "hybrid", "onsite"
        job_remote_option = match_data.get(
            "job_remote_option", ""
        )  # "remote", "hybrid", "onsite"

        if not user_remote_preference or not job_remote_option:
            return 1.0  # No preference specified

        # Compatibility matrix
        compatibility = {
            ("remote", "remote"): 1.0,
            ("remote", "hybrid"): 0.8,
            ("remote", "onsite"): 0.3,
            ("hybrid", "remote"): 0.9,
            ("hybrid", "hybrid"): 1.0,
            ("hybrid", "onsite"): 0.7,
            ("onsite", "remote"): 0.2,
            ("onsite", "hybrid"): 0.8,
            ("onsite", "onsite"): 1.0,
        }

        base_score = compatibility.get((user_remote_preference, job_remote_option), 0.5)

        # Apply custom rules
        rules = weight_config.custom_rules
        if rules:
            if job_remote_option == "remote" and "fully_remote_bonus" in rules:
                base_score += rules["fully_remote_bonus"]
            elif job_remote_option == "hybrid" and "hybrid_bonus" in rules:
                base_score += rules["hybrid_bonus"]
            elif job_remote_option == "onsite" and "onsite_penalty" in rules:
                base_score *= 1 - rules["onsite_penalty"]

        return min(1.0, base_score)

    def _calculate_seniority_score(
        self, match_data: Dict[str, Any], weight_config: WeightConfig
    ) -> float:
        """Calculate seniority level matching score."""
        user_seniority = match_data.get("user_seniority_level", "")
        job_seniority = match_data.get("job_seniority_level", "")

        if not user_seniority or not job_seniority:
            return 1.0  # No seniority specified

        # Seniority levels
        seniority_levels = ["entry", "junior", "mid", "senior", "lead", "principal"]

        try:
            user_level = seniority_levels.index(user_seniority.lower())
            job_level = seniority_levels.index(job_seniority.lower())
        except (ValueError, IndexError):
            return 0.5  # Unknown seniority levels

        difference = abs(user_level - job_level)

        if difference == 0:
            base_score = 1.0
        elif difference == 1:
            base_score = 0.8
        elif difference == 2:
            base_score = 0.5
        else:
            base_score = 0.2

        # Apply custom rules
        rules = weight_config.custom_rules
        if rules:
            if difference == 0 and "exact_level_bonus" in rules:
                base_score += rules["exact_level_bonus"]
            elif difference == 1 and "one_level_difference_penalty" in rules:
                base_score *= 1 - rules["one_level_difference_penalty"]
            elif difference >= 2 and "two_level_difference_penalty" in rules:
                base_score *= 1 - rules["two_level_difference_penalty"]

        return min(1.0, base_score)

    def _apply_custom_scoring_rules(
        self,
        base_score: float,
        match_data: Dict[str, Any],
        custom_rules: Dict[str, Any],
    ) -> float:
        """Apply custom scoring rules to the base score."""
        if not custom_rules:
            return base_score

        # Apply global multipliers
        if "global_multiplier" in custom_rules:
            base_score *= custom_rules["global_multiplier"]

        # Apply score adjustments based on specific conditions
        if "score_adjustments" in custom_rules:
            adjustments = custom_rules["score_adjustments"]
            for condition, adjustment in adjustments.items():
                if self._evaluate_condition(condition, match_data):
                    base_score += adjustment

        # Apply score caps
        if "max_score" in custom_rules:
            base_score = min(base_score, custom_rules["max_score"])

        if "min_score" in custom_rules:
            base_score = max(base_score, custom_rules["min_score"])

        return base_score

    def _evaluate_condition(self, condition: str, match_data: Dict[str, Any]) -> bool:
        """Evaluate a scoring condition."""
        # Simple condition evaluation (could be expanded)
        try:
            # Handle simple conditions like "user_experience_years > 5"
            if ">" in condition:
                field, value = condition.split(">", 1)
                field = field.strip()
                threshold = float(value.strip())
                field_value = float(match_data.get(field, 0))
                return field_value > threshold
            elif "<" in condition:
                field, value = condition.split("<", 1)
                field = field.strip()
                threshold = float(value.strip())
                field_value = float(match_data.get(field, 0))
                return field_value < threshold
            elif "=" in condition:
                field, value = condition.split("=", 1)
                field = field.strip()
                value = value.strip().strip("\"'")
                return str(match_data.get(field, "")).lower() == value.lower()
        except (ValueError, AttributeError):
            pass

        return False


# Global instance
_match_weights_manager = None


def get_match_weights_manager() -> MatchWeightsManager:
    """Get the global match weights manager instance."""
    global _match_weights_manager
    if _match_weights_manager is None:
        _match_weights_manager = MatchWeightsManager()
    return _match_weights_manager
