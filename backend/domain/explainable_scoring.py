"""Explainable Match Scoring with Confidence Intervals.

Implements the "Explainable Match Scoring" feature recommended in competitive analysis:
- Generates one-sentence cryptographic logs explaining why the bot applied
- Provides confidence intervals for match scores
- Shows transparent algorithmic reasoning
- Builds user trust through explainability

Based on competitive analysis insight:
"The fundamental flaw in current autonomous systems is a lack of transparency;
users do not know why the bot applied to a specific job."
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from shared.logging_config import get_logger

logger = get_logger("sorce.explainable_scoring")


class ConfidenceLevel(StrEnum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class MatchFactorType(StrEnum):
    SEMANTIC_SIMILARITY = "semantic_similarity"
    SKILL_MATCH = "skill_match"
    EXPERIENCE_ALIGNMENT = "experience_alignment"
    LOCATION_MATCH = "location_match"
    SALARY_MATCH = "salary_match"
    CERTIFICATION_MATCH = "certification_match"
    EDUCATION_MATCH = "education_match"
    INDUSTRY_MATCH = "industry_match"
    COMPANY_SIZE_FIT = "company_size_fit"
    REMOTE_PREFERENCE = "remote_preference"


@dataclass
class MatchFactor:
    factor_type: MatchFactorType
    score: float
    weight: float
    confidence_interval: tuple[float, float]
    reasoning: str
    evidence: list[str] = field(default_factory=list)
    importance: str = "moderate"


@dataclass
class ConfidenceInterval:
    lower: float
    upper: float
    confidence_level: float = 0.95

    @property
    def midpoint(self) -> float:
        return (self.lower + self.upper) / 2

    @property
    def width(self) -> float:
        return self.upper - self.lower

    def contains(self, value: float) -> bool:
        return self.lower <= value <= self.upper


class ExplainableMatchScore(BaseModel):
    job_id: str
    overall_score: float = Field(ge=0.0, le=1.0)
    confidence_interval_lower: float = Field(ge=0.0, le=1.0)
    confidence_interval_upper: float = Field(ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel
    explanation: str
    detailed_factors: dict[str, Any] = Field(default_factory=dict)
    applied_reasoning: str
    passed_dealbreakers: bool = True
    dealbreaker_details: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_audit_log(self) -> str:
        return f"[{self.timestamp.isoformat()}] Job {self.job_id}: Score {self.overall_score:.2%} (CI: {self.confidence_interval_lower:.2%}-{self.confidence_interval_upper:.2%}). {self.applied_reasoning}"


class ExplainableScoringEngine:
    """Engine for generating explainable match scores with confidence intervals.

    Provides transparency into why applications are submitted,
    building user trust through detailed reasoning.
    """

    FACTOR_WEIGHTS = {
        MatchFactorType.SEMANTIC_SIMILARITY: 0.25,
        MatchFactorType.SKILL_MATCH: 0.25,
        MatchFactorType.EXPERIENCE_ALIGNMENT: 0.15,
        MatchFactorType.LOCATION_MATCH: 0.10,
        MatchFactorType.SALARY_MATCH: 0.10,
        MatchFactorType.CERTIFICATION_MATCH: 0.05,
        MatchFactorType.EDUCATION_MATCH: 0.05,
        MatchFactorType.INDUSTRY_MATCH: 0.03,
        MatchFactorType.COMPANY_SIZE_FIT: 0.01,
        MatchFactorType.REMOTE_PREFERENCE: 0.01,
    }

    UNCERTAINTY_FACTORS = {
        "missing_job_data": 0.15,
        "missing_profile_data": 0.10,
        "ambiguous_skills": 0.08,
        "no_salary_info": 0.05,
        "no_location_info": 0.05,
    }

    def __init__(self):
        self._factor_cache: dict[str, list[MatchFactor]] = {}

    async def compute_explainable_score(
        self,
        profile: dict[str, Any],
        job: dict[str, Any],
        semantic_similarity: float = 0.5,
        skill_match_ratio: float = 0.5,
        dealbreakers: dict[str, Any] | None = None,
    ) -> ExplainableMatchScore:
        factors = await self._compute_all_factors(
            profile=profile,
            job=job,
            semantic_similarity=semantic_similarity,
            skill_match_ratio=skill_match_ratio,
        )

        overall_score = self._aggregate_score(factors)

        uncertainty = self._compute_uncertainty(profile, job)
        ci = self._compute_confidence_interval(overall_score, uncertainty)

        confidence_level = self._determine_confidence_level(ci.width)

        explanation = self._generate_explanation(factors, overall_score)

        applied_reasoning = self._generate_applied_reasoning(
            factors, overall_score, profile, job
        )

        dealbreaker_result = self._check_dealbreakers(profile, job, dealbreakers or {})

        detailed_factors = {
            ft.value: {
                "score": f.score,
                "weight": f.weight,
                "confidence_interval": list(f.confidence_interval),
                "reasoning": f.reasoning,
                "evidence": f.evidence,
            }
            for ft, f in factors.items()
        }

        return ExplainableMatchScore(
            job_id=job.get("id", "unknown"),
            overall_score=overall_score,
            confidence_interval_lower=ci.lower,
            confidence_interval_upper=ci.upper,
            confidence_level=confidence_level,
            explanation=explanation,
            detailed_factors=detailed_factors,
            applied_reasoning=applied_reasoning,
            passed_dealbreakers=dealbreaker_result["passed"],
            dealbreaker_details=dealbreaker_result["reasons"],
        )

    async def _compute_all_factors(
        self,
        profile: dict[str, Any],
        job: dict[str, Any],
        semantic_similarity: float,
        skill_match_ratio: float,
    ) -> dict[MatchFactorType, MatchFactor]:
        factors = {}

        factors[MatchFactorType.SEMANTIC_SIMILARITY] = MatchFactor(
            factor_type=MatchFactorType.SEMANTIC_SIMILARITY,
            score=semantic_similarity,
            weight=self.FACTOR_WEIGHTS[MatchFactorType.SEMANTIC_SIMILARITY],
            confidence_interval=(
                semantic_similarity * 0.9,
                min(1.0, semantic_similarity * 1.1),
            ),
            reasoning=f"Semantic similarity between profile and job description: {semantic_similarity:.1%}",
            importance="high",
        )

        profile_skills = self._extract_skills(profile)
        job_skills = self._extract_job_skills(job)

        matched_skills = [
            s
            for s in profile_skills
            if any(s.lower() in js.lower() for js in job_skills)
        ]
        [
            js
            for js in job_skills
            if not any(ps.lower() in js.lower() for ps in profile_skills)
        ]

        factors[MatchFactorType.SKILL_MATCH] = MatchFactor(
            factor_type=MatchFactorType.SKILL_MATCH,
            score=skill_match_ratio,
            weight=self.FACTOR_WEIGHTS[MatchFactorType.SKILL_MATCH],
            confidence_interval=(
                skill_match_ratio * 0.85,
                min(1.0, skill_match_ratio * 1.05),
            ),
            reasoning=f"Matched {len(matched_skills)} of {len(job_skills)} required skills",
            evidence=matched_skills[:10],
            importance="high",
        )

        exp_score = self._compute_experience_alignment(profile, job)
        factors[MatchFactorType.EXPERIENCE_ALIGNMENT] = MatchFactor(
            factor_type=MatchFactorType.EXPERIENCE_ALIGNMENT,
            score=exp_score,
            weight=self.FACTOR_WEIGHTS[MatchFactorType.EXPERIENCE_ALIGNMENT],
            confidence_interval=(max(0, exp_score - 0.1), min(1.0, exp_score + 0.1)),
            reasoning=self._get_experience_reasoning(profile, job),
            importance="moderate",
        )

        location_score, location_reasoning = self._compute_location_match(profile, job)
        factors[MatchFactorType.LOCATION_MATCH] = MatchFactor(
            factor_type=MatchFactorType.LOCATION_MATCH,
            score=location_score,
            weight=self.FACTOR_WEIGHTS[MatchFactorType.LOCATION_MATCH],
            confidence_interval=(
                max(0, location_score - 0.05),
                min(1.0, location_score + 0.05),
            ),
            reasoning=location_reasoning,
            importance="moderate",
        )

        salary_score, salary_reasoning = self._compute_salary_match(profile, job)
        factors[MatchFactorType.SALARY_MATCH] = MatchFactor(
            factor_type=MatchFactorType.SALARY_MATCH,
            score=salary_score,
            weight=self.FACTOR_WEIGHTS[MatchFactorType.SALARY_MATCH],
            confidence_interval=(
                max(0, salary_score - 0.15),
                min(1.0, salary_score + 0.15),
            ),
            reasoning=salary_reasoning,
            importance="moderate",
        )

        cert_score = self._compute_certification_match(profile, job)
        factors[MatchFactorType.CERTIFICATION_MATCH] = MatchFactor(
            factor_type=MatchFactorType.CERTIFICATION_MATCH,
            score=cert_score,
            weight=self.FACTOR_WEIGHTS[MatchFactorType.CERTIFICATION_MATCH],
            confidence_interval=(max(0, cert_score - 0.1), min(1.0, cert_score + 0.1)),
            reasoning="Certification alignment check",
            importance="low",
        )

        edu_score = self._compute_education_match(profile, job)
        factors[MatchFactorType.EDUCATION_MATCH] = MatchFactor(
            factor_type=MatchFactorType.EDUCATION_MATCH,
            score=edu_score,
            weight=self.FACTOR_WEIGHTS[MatchFactorType.EDUCATION_MATCH],
            confidence_interval=(max(0, edu_score - 0.1), min(1.0, edu_score + 0.1)),
            reasoning="Education requirements check",
            importance="low",
        )

        return factors

    def _aggregate_score(self, factors: dict[MatchFactorType, MatchFactor]) -> float:
        total_weight = sum(f.weight for f in factors.values())
        weighted_sum = sum(f.score * f.weight for f in factors.values())
        return weighted_sum / total_weight if total_weight > 0 else 0.5

    def _compute_uncertainty(
        self,
        profile: dict[str, Any],
        job: dict[str, Any],
    ) -> float:
        uncertainty = 0.0

        if not job.get("description"):
            uncertainty += self.UNCERTAINTY_FACTORS["missing_job_data"]
        if not profile.get("skills"):
            uncertainty += self.UNCERTAINTY_FACTORS["missing_profile_data"]
        if not job.get("salary") and not job.get("salary_range"):
            uncertainty += self.UNCERTAINTY_FACTORS["no_salary_info"]
        if not job.get("location"):
            uncertainty += self.UNCERTAINTY_FACTORS["no_location_info"]

        return min(0.5, uncertainty)

    def _compute_confidence_interval(
        self,
        score: float,
        uncertainty: float,
    ) -> ConfidenceInterval:
        lower = max(0.0, score - uncertainty)
        upper = min(1.0, score + uncertainty)
        return ConfidenceInterval(lower=lower, upper=upper)

    def _determine_confidence_level(self, interval_width: float) -> ConfidenceLevel:
        if interval_width < 0.1:
            return ConfidenceLevel.VERY_HIGH
        elif interval_width < 0.2:
            return ConfidenceLevel.HIGH
        elif interval_width < 0.3:
            return ConfidenceLevel.MEDIUM
        elif interval_width < 0.4:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW

    def _generate_explanation(
        self,
        factors: dict[MatchFactorType, MatchFactor],
        overall_score: float,
    ) -> str:
        high_importance = [f for f in factors.values() if f.importance == "high"]

        explanations = []
        for factor in sorted(high_importance, key=lambda x: x.score, reverse=True):
            if factor.score > 0.7:
                explanations.append(
                    f"Strong {factor.factor_type.value.replace('_', ' ')} ({factor.score:.0%})"
                )
            elif factor.score > 0.5:
                explanations.append(
                    f"Good {factor.factor_type.value.replace('_', ' ')} ({factor.score:.0%})"
                )
            else:
                explanations.append(
                    f"Moderate {factor.factor_type.value.replace('_', ' ')} ({factor.score:.0%})"
                )

        if overall_score > 0.8:
            summary = "This is an excellent match for your profile."
        elif overall_score > 0.6:
            summary = "This is a good match worth considering."
        elif overall_score > 0.4:
            summary = "This is a moderate match with some alignment."
        else:
            summary = "This is a weak match with limited alignment."

        return f"{summary} Key factors: {'; '.join(explanations[:3])}."

    def _generate_applied_reasoning(
        self,
        factors: dict[MatchFactorType, MatchFactor],
        overall_score: float,
        profile: dict[str, Any],
        job: dict[str, Any],
    ) -> str:
        skill_factor = factors.get(MatchFactorType.SKILL_MATCH)
        factors.get(MatchFactorType.SEMANTIC_SIMILARITY)

        skills_evidence = skill_factor.evidence[:3] if skill_factor else []

        if overall_score >= 0.8:
            return (
                f"Executed application: Strong match detected. "
                f"Your verified skills ({', '.join(skills_evidence) if skills_evidence else 'relevant experience'}) "
                f"yielded a {overall_score:.0%} match score, exceeding the 80% threshold. "
                f"Semantic analysis confirmed alignment with job requirements."
            )
        elif overall_score >= 0.6:
            return (
                f"Executed application: Good match detected. "
                f"Profile alignment scored {overall_score:.0%} based on "
                f"skill matching and semantic similarity. "
                f"Job requirements align with your background in {', '.join(skills_evidence[:2]) if skills_evidence else 'relevant areas'}."
            )
        else:
            return (
                f"Executed application: Moderate match ({overall_score:.0%}). "
                f"Applied due to partial skill alignment and semantic match. "
                f"Some requirements may not fully match your current profile."
            )

    def _check_dealbreakers(
        self,
        profile: dict[str, Any],
        job: dict[str, Any],
        dealbreakers: dict[str, Any],
    ) -> dict[str, Any]:
        passed = True
        reasons: list[str] = []

        if (
            dealbreakers.get("remote_only")
            and "remote" not in job.get("location", "").lower()
        ):
            passed = False
            reasons.append("Job is not remote")

        min_salary = dealbreakers.get("min_salary")
        if min_salary:
            job_salary = job.get("salary") or 0
            if isinstance(job_salary, str):
                try:
                    job_salary = int(
                        job_salary.replace("$", "").replace(",", "").split("-")[0]
                    )
                except (ValueError, AttributeError):
                    job_salary = 0
            if job_salary and job_salary < min_salary:
                passed = False
                reasons.append(f"Salary below minimum (${job_salary} < ${min_salary})")

        excluded = dealbreakers.get("excluded_companies", [])
        job_company = job.get("company", "").lower()
        if any(exc.lower() in job_company for exc in excluded):
            passed = False
            reasons.append("Company is in exclusion list")

        return {"passed": passed, "reasons": reasons}

    def _extract_skills(self, profile: dict[str, Any]) -> list[str]:
        skills = profile.get("skills", {})
        if isinstance(skills, dict):
            return skills.get("technical", []) + skills.get("soft", [])
        return skills if isinstance(skills, list) else []

    def _extract_job_skills(self, job: dict[str, Any]) -> list[str]:
        description = job.get("description", "")
        common_skills = [
            "python",
            "javascript",
            "java",
            "typescript",
            "react",
            "angular",
            "vue",
            "node",
            "aws",
            "azure",
            "gcp",
            "docker",
            "kubernetes",
            "sql",
            "postgresql",
            "mysql",
            "mongodb",
            "redis",
            "graphql",
            "machine learning",
            "ai",
            "data science",
            "agile",
            "scrum",
            "ci/cd",
            "git",
            "linux",
            "leadership",
            "communication",
        ]
        found = [s for s in common_skills if s.lower() in description.lower()]
        return found

    def _compute_experience_alignment(
        self, profile: dict[str, Any], job: dict[str, Any]
    ) -> float:
        job_title = job.get("title", "").lower()
        profile_title = profile.get("current_title", "").lower()

        if profile_title and any(
            word in job_title for word in profile_title.split() if len(word) > 3
        ):
            return 0.9

        experience = profile.get("experience", [])
        if not experience:
            return 0.5

        for exp in experience:
            exp_title = exp.get("title", "").lower()
            if exp_title and any(
                word in job_title for word in exp_title.split() if len(word) > 3
            ):
                return 0.8

        return 0.5

    def _get_experience_reasoning(
        self, profile: dict[str, Any], job: dict[str, Any]
    ) -> str:
        job_title = job.get("title", "")
        profile_title = profile.get("current_title", "")
        if profile_title and profile_title.lower() in job_title.lower():
            return (
                f"Current role '{profile_title}' directly aligns with target position"
            )
        return "Experience assessed for role relevance"

    def _compute_location_match(
        self,
        profile: dict[str, Any],
        job: dict[str, Any],
    ) -> tuple[float, str]:
        job_location = job.get("location", "").lower()

        if "remote" in job_location:
            return 1.0, "Position is remote"

        preferred_locations = profile.get("preferred_locations", [])
        if not preferred_locations:
            return 0.7, "Location preference not specified"

        if any(loc.lower() in job_location for loc in preferred_locations):
            return 1.0, "Location matches preference"

        return 0.5, "Location may not match preference"

    def _compute_salary_match(
        self,
        profile: dict[str, Any],
        job: dict[str, Any],
    ) -> tuple[float, str]:
        min_salary = profile.get("min_salary") or profile.get("dealbreakers", {}).get(
            "min_salary"
        )
        job_salary = job.get("salary")

        if not job_salary:
            return 0.7, "Salary information not available"

        if isinstance(job_salary, str):
            try:
                job_salary = int(
                    job_salary.replace("$", "").replace(",", "").split("-")[0]
                )
            except (ValueError, AttributeError):
                return 0.7, "Salary could not be parsed"

        if min_salary and job_salary < min_salary:
            return 0.3, f"Salary below minimum (${job_salary} < ${min_salary})"

        return 1.0, f"Salary ${job_salary:,} meets requirements"

    def _compute_certification_match(
        self, profile: dict[str, Any], job: dict[str, Any]
    ) -> float:
        certs = profile.get("certifications", [])
        job_desc = job.get("description", "").lower()

        if not certs:
            return 0.5

        matched = sum(1 for c in certs if c.lower() in job_desc)
        return min(1.0, 0.5 + matched * 0.25)

    def _compute_education_match(
        self, profile: dict[str, Any], job: dict[str, Any]
    ) -> float:
        education = profile.get("education", [])
        job_desc = job.get("description", "").lower()

        if not education:
            return 0.5

        requires_degree = (
            "bachelor" in job_desc or "master" in job_desc or "degree" in job_desc
        )

        if requires_degree:
            for edu in education:
                degree = edu.get("degree", "").lower()
                if "bachelor" in degree or "master" in degree or "phd" in degree:
                    return 1.0
            return 0.4

        return 0.8


_explainable_scorer: ExplainableScoringEngine | None = None


def get_explainable_scorer() -> ExplainableScoringEngine:
    global _explainable_scorer
    if _explainable_scorer is None:
        _explainable_scorer = ExplainableScoringEngine()
    return _explainable_scorer
