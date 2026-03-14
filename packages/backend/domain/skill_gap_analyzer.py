"""Skill Gap Analyzer - Domain logic for analyzing skill gaps and providing recommendations.

This module provides the core logic for comparing user skills against job requirements,
ranking skills by importance, and generating personalized learning recommendations
with estimated learning times and resources.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from packages.backend.domain.skills_taxonomy import (
    SkillsTaxonomy,
    get_skills_taxonomy,
)
from shared.logging_config import get_logger

logger = get_logger("sorce.skill_gap_analyzer")


class SkillLevel(Enum):
    """Proficiency levels for skills."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class SkillType(Enum):
    """Categories of skills."""

    TECHNICAL = "technical"
    SOFT = "soft"
    INDUSTRY = "industry"
    TOOL = "tool"
    DOMAIN = "domain"


@dataclass
class SkillGapItem:
    """Individual skill gap with metadata."""

    skill_name: str
    category: str
    skill_type: SkillType
    demand_score: float
    priority: str
    missing: bool
    proficiency_gap: int  # How many levels needed to reach target
    estimated_learning_weeks: float
    related_skills: List[str] = field(default_factory=list)
    description: str = ""
    resources: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class SkillGapAnalysis:
    """Complete skill gap analysis result."""

    target_role: str
    current_skills: List[str]
    required_skills: List[str]
    matched_skills: List[str]
    missing_skills: List[str]
    gap_score: float  # 0.0 to 1.0 (1.0 = no gaps)
    skill_gaps: List[SkillGapItem]
    category_breakdown: Dict[str, Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    market_insights: Dict[str, Any]


class JobMarketData:
    """Simulated job market data for skill requirements.

    In a production system, this would query actual job market data.
    For now, we use a predefined mapping of roles to required skills.
    """

    # Role to required skills mapping with proficiency levels
    ROLE_REQUIREMENTS: Dict[str, Dict[str, Any]] = {
        "software_engineer": {
            "required_skills": [
                "Python",
                "JavaScript",
                "Git",
                "SQL",
                "REST APIs",
                "Data Structures",
                "Algorithms",
                "Problem Solving",
                "Agile",
                "Unit Testing",
            ],
            "preferred_skills": [
                "Docker",
                "Kubernetes",
                "AWS",
                "TypeScript",
                "GraphQL",
                "CI/CD",
                "Microservices",
            ],
            "experience_level": "mid",
            "demand_growth": 0.15,
        },
        "data_scientist": {
            "required_skills": [
                "Python",
                "Machine Learning",
                "Statistics",
                "SQL",
                "Data Visualization",
                "Pandas",
                "NumPy",
                "Problem Solving",
            ],
            "preferred_skills": [
                "Deep Learning",
                "TensorFlow",
                "PyTorch",
                "Scala",
                "Spark",
                "Cloud Platforms",
            ],
            "experience_level": "mid",
            "demand_growth": 0.20,
        },
        "frontend_developer": {
            "required_skills": [
                "JavaScript",
                "HTML",
                "CSS",
                "React",
                "TypeScript",
                "Responsive Design",
                "Git",
                "REST APIs",
            ],
            "preferred_skills": [
                "Vue.js",
                "Angular",
                "GraphQL",
                "Next.js",
                "Webpack",
                "Tailwind CSS",
            ],
            "experience_level": "mid",
            "demand_growth": 0.12,
        },
        "backend_developer": {
            "required_skills": [
                "Python",
                "Java",
                "SQL",
                "REST APIs",
                "Git",
                "Unit Testing",
                "Data Structures",
            ],
            "preferred_skills": [
                "Go",
                "Node.js",
                "Docker",
                "Kubernetes",
                "AWS",
                "PostgreSQL",
                "MongoDB",
            ],
            "experience_level": "mid",
            "demand_growth": 0.14,
        },
        "devops_engineer": {
            "required_skills": [
                "Docker",
                "Kubernetes",
                "AWS",
                "CI/CD",
                "Linux",
                "Terraform",
                "Scripting",
                "Git",
            ],
            "preferred_skills": [
                "Azure",
                "Google Cloud",
                "Ansible",
                "Prometheus",
                "Grafana",
                "Helm",
            ],
            "experience_level": "mid",
            "demand_growth": 0.18,
        },
        "product_manager": {
            "required_skills": [
                "Product Strategy",
                "User Research",
                "Agile",
                "Data Analysis",
                "Communication",
                "Roadmapping",
            ],
            "preferred_skills": [
                "SQL",
                "A/B Testing",
                "Figma",
                "Jira",
                "Scrum",
            ],
            "experience_level": "mid",
            "demand_growth": 0.10,
        },
        "ux_designer": {
            "required_skills": [
                "User Research",
                "Wireframing",
                "Prototyping",
                "Figma",
                "Visual Design",
                "Usability Testing",
            ],
            "preferred_skills": [
                "Sketch",
                "Adobe XD",
                "HTML/CSS",
                "Design Systems",
                "Interaction Design",
            ],
            "experience_level": "mid",
            "demand_growth": 0.11,
        },
    }

    # Skill type mapping
    SKILL_TYPES: Dict[str, SkillType] = {
        "Python": SkillType.TECHNICAL,
        "JavaScript": SkillType.TECHNICAL,
        "Java": SkillType.TECHNICAL,
        "TypeScript": SkillType.TECHNICAL,
        "Go": SkillType.TECHNICAL,
        "SQL": SkillType.TECHNICAL,
        "Git": SkillType.TOOL,
        "Docker": SkillType.TOOL,
        "Kubernetes": SkillType.TOOL,
        "AWS": SkillType.TOOL,
        "REST APIs": SkillType.TECHNICAL,
        "Machine Learning": SkillType.TECHNICAL,
        "Data Structures": SkillType.TECHNICAL,
        "Algorithms": SkillType.TECHNICAL,
        "Problem Solving": SkillType.SOFT,
        "Communication": SkillType.SOFT,
        "Agile": SkillType.INDUSTRY,
        "Product Strategy": SkillType.DOMAIN,
        "User Research": SkillType.SOFT,
        "Wireframing": SkillType.TOOL,
    }

    # Learning resources for skills
    LEARNING_RESOURCES: Dict[str, List[Dict[str, str]]] = {
        "Python": [
            {"type": "course", "name": "Python for Everybody", "provider": "Coursera"},
            {"type": "course", "name": "Python Basics", "provider": "Codecademy"},
            {"type": "book", "name": "Automate the Boring Stuff", "provider": "Free"},
        ],
        "JavaScript": [
            {"type": "course", "name": "JavaScript Basics", "provider": "MDN"},
            {"type": "course", "name": "JavaScript Algorithms", "provider": "freeCodeCamp"},
        ],
        "React": [
            {"type": "course", "name": "React - The Complete Guide", "provider": "Udemy"},
            {"type": "docs", "name": "React Documentation", "provider": "react.dev"},
        ],
        "Machine Learning": [
            {"type": "course", "name": "Machine Learning", "provider": "Coursera"},
            {"type": "book", "name": "Hands-On Machine Learning", "provider": "O'Reilly"},
        ],
        "Docker": [
            {"type": "course", "name": "Docker for Beginners", "provider": "Docker"},
            {"type": "course", "name": "Docker & Kubernetes", "provider": "Udemy"},
        ],
        "AWS": [
            {"type": "cert", "name": "AWS Solutions Architect", "provider": "AWS"},
            {"type": "course", "name": "AWS Fundamentals", "provider": "Coursera"},
        ],
    }

    # Estimated learning times (in weeks for intermediate proficiency)
    LEARNING_TIMES: Dict[str, float] = {
        "Python": 8.0,
        "JavaScript": 10.0,
        "Java": 12.0,
        "TypeScript": 6.0,
        "Go": 8.0,
        "SQL": 6.0,
        "Git": 2.0,
        "Docker": 6.0,
        "Kubernetes": 10.0,
        "AWS": 12.0,
        "REST APIs": 4.0,
        "Machine Learning": 16.0,
        "React": 8.0,
        "Data Structures": 8.0,
        "Algorithms": 10.0,
        "Problem Solving": 4.0,
        "Communication": 3.0,
        "Agile": 3.0,
        "Product Strategy": 6.0,
        "User Research": 4.0,
        "Wireframing": 4.0,
    }

    @classmethod
    def get_role_requirements(cls, role: str) -> Optional[Dict[str, Any]]:
        """Get required skills for a role."""
        normalized_role = role.lower().replace(" ", "_").replace("-", "_")
        return cls.ROLE_REQUIREMENTS.get(normalized_role)

    @classmethod
    def get_skill_type(cls, skill: str) -> SkillType:
        """Get the type of a skill."""
        return cls.SKILL_TYPES.get(skill, SkillType.TECHNICAL)

    @classmethod
    def get_learning_resources(cls, skill: str) -> List[Dict[str, str]]:
        """Get learning resources for a skill."""
        return cls.LEARNING_RESOURCES.get(skill, [])

    @classmethod
    def get_learning_time(cls, skill: str) -> float:
        """Get estimated learning time in weeks."""
        return cls.LEARNING_TIMES.get(skill, 6.0)


class SkillGapAnalyzer:
    """Analyzer for comparing user skills against job requirements."""

    def __init__(self, taxonomy: Optional[SkillsTaxonomy] = None):
        """Initialize the analyzer with a skills taxonomy."""
        self.taxonomy = taxonomy or get_skills_taxonomy()
        self.market_data = JobMarketData()

    def analyze(
        self,
        current_skills: List[str],
        target_role: str,
        user_proficiency_levels: Optional[Dict[str, str]] = None,
    ) -> SkillGapAnalysis:
        """Analyze gaps between user skills and target role requirements.

        Args:
            current_skills: List of user's current skills
            target_role: Target job role
            user_proficiency_levels: Optional dict mapping skills to proficiency levels

        Returns:
            Complete skill gap analysis
        """
        logger.info(
            f"[SKILL_GAP] Analyzing gap for role '{target_role}' "
            f"with {len(current_skills)} current skills"
        )

        # Validate and normalize current skills
        valid_skills, _, _ = self.taxonomy.validate_user_skills(current_skills)
        user_skill_set = set(valid_skills)

        # Get role requirements from market data
        role_requirements = self.market_data.get_role_requirements(target_role)
        if not role_requirements:
            logger.warning(f"[SKILL_GAP] Unknown role: {target_role}, using generic analysis")
            role_requirements = self._generate_generic_requirements(target_role)

        required_skills = role_requirements.get("required_skills", [])
        preferred_skills = role_requirements.get("preferred_skills", [])

        # Find matched and missing skills
        matched_skills = []
        missing_skills = []

        for skill in required_skills:
            if skill in user_skill_set:
                matched_skills.append(skill)
            else:
                missing_skills.append(skill)

        # Calculate gap score (0.0 to 1.0)
        total_required = len(required_skills)
        gap_score = (
            len(matched_skills) / total_required if total_required > 0 else 1.0
        )

        # Build detailed skill gap items
        skill_gaps = self._build_skill_gaps(
            missing_skills, required_skills, user_proficiency_levels
        )

        # Get category breakdown
        category_breakdown = self._get_category_breakdown(
            matched_skills, missing_skills, required_skills
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            skill_gaps, role_requirements
        )

        # Get market insights
        market_insights = {
            "role_demand_growth": role_requirements.get("demand_growth", 0.1),
            "experience_level": role_requirements.get("experience_level", "mid"),
            "total_job_postings_estimate": self._estimate_job_postings(target_role),
            "competition_level": self._get_competition_level(gap_score),
        }

        logger.info(
            f"[SKILL_GAP] Analysis complete: {len(matched_skills)}/{total_required} "
            f"skills matched, gap score: {gap_score:.2f}"
        )

        return SkillGapAnalysis(
            target_role=target_role,
            current_skills=valid_skills,
            required_skills=required_skills,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            gap_score=gap_score,
            skill_gaps=skill_gaps,
            category_breakdown=category_breakdown,
            recommendations=recommendations,
            market_insights=market_insights,
        )

    def get_recommendations(
        self,
        current_skills: List[str],
        target_role: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get prioritized skill recommendations.

        Args:
            current_skills: List of user's current skills
            target_role: Target job role
            limit: Maximum number of recommendations

        Returns:
            Prioritized list of skill recommendations with resources
        """
        analysis = self.analyze(current_skills, target_role)

        # Sort recommendations by priority
        sorted_recommendations = sorted(
            analysis.recommendations,
            key=lambda x: (
                x.get("priority_weight", 0),
                -x.get("demand_score", 0),
            ),
            reverse=True,
        )

        return sorted_recommendations[:limit]

    def _generate_generic_requirements(self, role: str) -> Dict[str, Any]:
        """Generate generic requirements for unknown roles."""
        return {
            "required_skills": [
                "Problem Solving",
                "Communication",
                "Teamwork",
                "Time Management",
            ],
            "preferred_skills": [],
            "experience_level": "mid",
            "demand_growth": 0.05,
        }

    def _build_skill_gaps(
        self,
        missing_skills: List[str],
        required_skills: List[str],
        user_proficiency_levels: Optional[Dict[str, str]],
    ) -> List[SkillGapItem]:
        """Build detailed skill gap items."""
        skill_gaps = []

        for skill in missing_skills:
            # Get skill info from taxonomy
            skill_info = self.taxonomy.get_skill_info(skill)

            # Get skill type from market data
            skill_type = self.market_data.get_skill_type(skill)

            # Determine demand score
            demand_score = skill_info.demand_score if skill_info else 0.5

            # Determine priority based on demand score
            priority = "high"
            if demand_score < 0.6:
                priority = "medium"
            if demand_score < 0.4:
                priority = "low"

            # Calculate proficiency gap
            user_level = user_proficiency_levels.get(skill, "beginner") if user_proficiency_levels else "beginner"
            proficiency_gap = self._calculate_proficiency_gap(user_level, "advanced")

            # Get estimated learning time
            learning_time = self.market_data.get_learning_time(skill)

            # Get related skills
            related_skills = self._get_related_skills(skill, required_skills)

            # Get learning resources
            resources = self.market_data.get_learning_resources(skill)

            # Get description
            description = skill_info.description if skill_info else ""

            skill_gaps.append(
                SkillGapItem(
                    skill_name=skill,
                    category=skill_info.category.value if skill_info else "other",
                    skill_type=skill_type,
                    demand_score=demand_score,
                    priority=priority,
                    missing=True,
                    proficiency_gap=proficiency_gap,
                    estimated_learning_weeks=learning_time,
                    related_skills=related_skills,
                    description=description,
                    resources=resources,
                )
            )

        return skill_gaps

    def _calculate_proficiency_gap(self, user_level: str, target_level: str) -> int:
        """Calculate the proficiency gap in levels."""
        levels = ["beginner", "intermediate", "advanced", "expert"]
        user_idx = levels.index(user_level.lower()) if user_level.lower() in levels else 0
        target_idx = levels.index(target_level.lower()) if target_level.lower() in levels else 2
        return max(0, target_idx - user_idx)

    def _get_related_skills(self, skill: str, required_skills: List[str]) -> List[str]:
        """Get skills related to the given skill."""
        # Simple related skills mapping
        related_map = {
            "Python": ["Django", "Flask", "Pandas", "NumPy"],
            "JavaScript": ["React", "Vue.js", "Node.js", "TypeScript"],
            "Docker": ["Kubernetes", "Helm", "Docker Compose"],
            "AWS": ["EC2", "S3", "Lambda", "CloudFormation"],
            "Machine Learning": ["Deep Learning", "TensorFlow", "PyTorch"],
        }
        related = related_map.get(skill, [])
        return [s for s in related if s in required_skills]

    def _get_category_breakdown(
        self,
        matched_skills: List[str],
        missing_skills: List[str],
        required_skills: List[str],
    ) -> Dict[str, Dict[str, Any]]:
        """Get breakdown by skill category."""
        breakdown = {}

        all_skills = set(matched_skills + missing_skills)
        taxonomy = self.taxonomy

        for skill in all_skills:
            skill_info = taxonomy.get_skill_info(skill)
            category = skill_info.category.value if skill_info else "other"

            if category not in breakdown:
                breakdown[category] = {
                    "matched": [],
                    "missing": [],
                    "total": 0,
                    "match_rate": 0.0,
                }

            if skill in matched_skills:
                breakdown[category]["matched"].append(skill)
            if skill in missing_skills:
                breakdown[category]["missing"].append(skill)

        # Calculate match rates
        for category in breakdown:
            total = len(breakdown[category]["matched"]) + len(breakdown[category]["missing"])
            matched = len(breakdown[category]["matched"])
            breakdown[category]["total"] = total
            breakdown[category]["match_rate"] = matched / total if total > 0 else 0.0

        return breakdown

    def _generate_recommendations(
        self,
        skill_gaps: List[SkillGapItem],
        role_requirements: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Generate prioritized learning recommendations."""
        recommendations = []

        # Priority weights for different factors
        priority_weights = {
            "high": 3.0,
            "medium": 2.0,
            "low": 1.0,
        }

        for gap in skill_gaps:
            weight = priority_weights.get(gap.priority, 1.0)

            # Adjust weight by demand score
            weight *= gap.demand_score

            # Adjust by learning time (prefer shorter learning paths)
            if gap.estimated_learning_weeks > 12:
                weight *= 0.8

            recommendation = {
                "skill": gap.skill_name,
                "category": gap.category,
                "skill_type": gap.skill_type.value,
                "priority": gap.priority,
                "priority_weight": weight,
                "demand_score": gap.demand_score,
                "estimated_learning_weeks": gap.estimated_learning_weeks,
                "description": gap.description,
                "related_skills": gap.related_skills,
                "resources": gap.resources,
                "reason": f"High demand skill ({gap.demand_score:.0%} market demand)",
            }

            # Add specific reason based on priority
            if gap.priority == "high":
                recommendation["reason"] = f"Critical skill for target role (demand: {gap.demand_score:.0%})"
            elif gap.priority == "medium":
                recommendation["reason"] = "Valued skill to strengthen your profile"

            recommendations.append(recommendation)

        return recommendations

    def _estimate_job_postings(self, role: str) -> int:
        """Estimate number of job postings (simulated)."""
        estimates = {
            "software_engineer": 150000,
            "data_scientist": 80000,
            "frontend_developer": 70000,
            "backend_developer": 90000,
            "devops_engineer": 50000,
            "product_manager": 60000,
            "ux_designer": 40000,
        }
        normalized_role = role.lower().replace(" ", "_").replace("-", "_")
        return estimates.get(normalized_role, 30000)

    def _get_competition_level(self, gap_score: float) -> str:
        """Determine competition level based on gap score."""
        if gap_score >= 0.8:
            return "high"
        if gap_score >= 0.5:
            return "medium"
        return "low"


# Singleton instance
_skill_gap_analyzer: Optional[SkillGapAnalyzer] = None


def get_skill_gap_analyzer() -> SkillGapAnalyzer:
    """Get or create the skill gap analyzer singleton."""
    global _skill_gap_analyzer
    if _skill_gap_analyzer is None:
        _skill_gap_analyzer = SkillGapAnalyzer()
    return _skill_gap_analyzer
