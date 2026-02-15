"""
Career Path Analysis — career progression suggestions.

Features:
  - Career trajectory analysis from job history
  - Skill gap identification for target roles
  - Career progression recommendations
  - Industry transition suggestions
  - Learning path recommendations
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.career_path")


class CareerLevel(str, Enum):
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    MANAGEMENT = "management"
    STAFF = "staff"
    PRINCIPAL = "principal"
    DIRECTOR = "director"
    VP = "vp"
    C_LEVEL = "c_level"


class CareerTrack(str, Enum):
    INDIVIDUAL_CONTRIBUTOR = "ic"
    MANAGEMENT = "management"
    HYBRID = "hybrid"
    CONSULTANT = "consultant"
    ENTREPRENEUR = "entrepreneur"


@dataclass
class CareerRole:
    title: str
    level: CareerLevel
    track: CareerTrack
    typical_years_experience: tuple[int, int]
    typical_skills: list[str]
    salary_range_usd: tuple[int, int]
    growth_outlook: str = "stable"


@dataclass
class CareerTransition:
    from_role: str
    to_role: str
    difficulty: str
    skills_to_acquire: list[str]
    skills_transferable: list[str]
    typical_timeline_months: int
    salary_change_pct: float


@dataclass
class SkillGap:
    skill: str
    importance: str
    acquisition_method: str
    estimated_time_weeks: int
    resources: list[str] = field(default_factory=list)


@dataclass
class CareerPathRecommendation:
    current_role: str
    target_role: str
    path_type: str
    steps: list[dict[str, Any]]
    skill_gaps: list[SkillGap]
    estimated_timeline_months: int
    potential_salary_increase_pct: float
    confidence: float


CAREER_ROLES: dict[str, CareerRole] = {
    "software_engineer": CareerRole(
        title="Software Engineer",
        level=CareerLevel.MID,
        track=CareerTrack.INDIVIDUAL_CONTRIBUTOR,
        typical_years_experience=(2, 5),
        typical_skills=[
            "programming",
            "data structures",
            "algorithms",
            "testing",
            "version control",
        ],
        salary_range_usd=(80000, 150000),
        growth_outlook="strong",
    ),
    "senior_software_engineer": CareerRole(
        title="Senior Software Engineer",
        level=CareerLevel.SENIOR,
        track=CareerTrack.INDIVIDUAL_CONTRIBUTOR,
        typical_years_experience=(5, 8),
        typical_skills=[
            "system design",
            "mentoring",
            "code review",
            "architecture",
            "leadership",
        ],
        salary_range_usd=(130000, 220000),
        growth_outlook="strong",
    ),
    "staff_engineer": CareerRole(
        title="Staff Engineer",
        level=CareerLevel.STAFF,
        track=CareerTrack.INDIVIDUAL_CONTRIBUTOR,
        typical_years_experience=(8, 12),
        typical_skills=[
            "technical strategy",
            "cross-team leadership",
            "architecture",
            "mentoring",
        ],
        salary_range_usd=(180000, 300000),
        growth_outlook="strong",
    ),
    "principal_engineer": CareerRole(
        title="Principal Engineer",
        level=CareerLevel.PRINCIPAL,
        track=CareerTrack.INDIVIDUAL_CONTRIBUTOR,
        typical_years_experience=(12, 20),
        typical_skills=[
            "technical vision",
            "organization leadership",
            "industry expertise",
        ],
        salary_range_usd=(250000, 400000),
        growth_outlook="stable",
    ),
    "engineering_manager": CareerRole(
        title="Engineering Manager",
        level=CareerLevel.MANAGEMENT,
        track=CareerTrack.MANAGEMENT,
        typical_years_experience=(5, 10),
        typical_skills=[
            "people management",
            "project management",
            "hiring",
            "performance reviews",
        ],
        salary_range_usd=(150000, 250000),
        growth_outlook="strong",
    ),
    "director_of_engineering": CareerRole(
        title="Director of Engineering",
        level=CareerLevel.DIRECTOR,
        track=CareerTrack.MANAGEMENT,
        typical_years_experience=(10, 15),
        typical_skills=[
            "org design",
            "budget management",
            "strategic planning",
            "executive communication",
        ],
        salary_range_usd=(200000, 350000),
        growth_outlook="stable",
    ),
    "vp_of_engineering": CareerRole(
        title="VP of Engineering",
        level=CareerLevel.VP,
        track=CareerTrack.MANAGEMENT,
        typical_years_experience=(15, 25),
        typical_skills=[
            "executive leadership",
            "company strategy",
            "board communication",
            "culture building",
        ],
        salary_range_usd=(280000, 450000),
        growth_outlook="stable",
    ),
    "cto": CareerRole(
        title="CTO",
        level=CareerLevel.C_LEVEL,
        track=CareerTrack.MANAGEMENT,
        typical_years_experience=(15, 30),
        typical_skills=[
            "technology strategy",
            "business acumen",
            "investor relations",
            "vision",
        ],
        salary_range_usd=(300000, 600000),
        growth_outlook="stable",
    ),
    "product_manager": CareerRole(
        title="Product Manager",
        level=CareerLevel.MID,
        track=CareerTrack.INDIVIDUAL_CONTRIBUTOR,
        typical_years_experience=(3, 6),
        typical_skills=[
            "product strategy",
            "user research",
            "roadmapping",
            "stakeholder management",
        ],
        salary_range_usd=(100000, 180000),
        growth_outlook="strong",
    ),
    "senior_product_manager": CareerRole(
        title="Senior Product Manager",
        level=CareerLevel.SENIOR,
        track=CareerTrack.INDIVIDUAL_CONTRIBUTOR,
        typical_years_experience=(6, 10),
        typical_skills=[
            "product leadership",
            "market analysis",
            "go-to-market",
            "team mentoring",
        ],
        salary_range_usd=(150000, 250000),
        growth_outlook="strong",
    ),
    "data_scientist": CareerRole(
        title="Data Scientist",
        level=CareerLevel.MID,
        track=CareerTrack.INDIVIDUAL_CONTRIBUTOR,
        typical_years_experience=(2, 5),
        typical_skills=[
            "statistics",
            "machine learning",
            "python",
            "data analysis",
            "visualization",
        ],
        salary_range_usd=(100000, 180000),
        growth_outlook="strong",
    ),
    "senior_data_scientist": CareerRole(
        title="Senior Data Scientist",
        level=CareerLevel.SENIOR,
        track=CareerTrack.INDIVIDUAL_CONTRIBUTOR,
        typical_years_experience=(5, 8),
        typical_skills=["ml engineering", "research", "mentoring", "model deployment"],
        salary_range_usd=(150000, 250000),
        growth_outlook="strong",
    ),
    "devops_engineer": CareerRole(
        title="DevOps Engineer",
        level=CareerLevel.MID,
        track=CareerTrack.INDIVIDUAL_CONTRIBUTOR,
        typical_years_experience=(2, 5),
        typical_skills=[
            "ci/cd",
            "cloud platforms",
            "infrastructure as code",
            "monitoring",
            "automation",
        ],
        salary_range_usd=(100000, 180000),
        growth_outlook="strong",
    ),
    "sre": CareerRole(
        title="Site Reliability Engineer",
        level=CareerLevel.MID,
        track=CareerTrack.INDIVIDUAL_CONTRIBUTOR,
        typical_years_experience=(3, 6),
        typical_skills=[
            "reliability engineering",
            "incident response",
            "capacity planning",
            "coding",
        ],
        salary_range_usd=(120000, 200000),
        growth_outlook="strong",
    ),
    "ux_designer": CareerRole(
        title="UX Designer",
        level=CareerLevel.MID,
        track=CareerTrack.INDIVIDUAL_CONTRIBUTOR,
        typical_years_experience=(2, 5),
        typical_skills=[
            "user research",
            "wireframing",
            "prototyping",
            "usability testing",
            "figma",
        ],
        salary_range_usd=(80000, 140000),
        growth_outlook="stable",
    ),
    "senior_ux_designer": CareerRole(
        title="Senior UX Designer",
        level=CareerLevel.SENIOR,
        track=CareerTrack.INDIVIDUAL_CONTRIBUTOR,
        typical_years_experience=(5, 8),
        typical_skills=[
            "design systems",
            "user strategy",
            "mentoring",
            "design leadership",
        ],
        salary_range_usd=(120000, 180000),
        growth_outlook="stable",
    ),
}

CAREER_TRANSITIONS: list[CareerTransition] = [
    CareerTransition(
        from_role="software_engineer",
        to_role="senior_software_engineer",
        difficulty="moderate",
        skills_to_acquire=["system design", "mentoring", "technical leadership"],
        skills_transferable=["programming", "testing", "debugging"],
        typical_timeline_months=24,
        salary_change_pct=0.25,
    ),
    CareerTransition(
        from_role="senior_software_engineer",
        to_role="staff_engineer",
        difficulty="challenging",
        skills_to_acquire=[
            "technical strategy",
            "cross-team influence",
            "architecture at scale",
        ],
        skills_transferable=["system design", "mentoring", "code quality"],
        typical_timeline_months=36,
        salary_change_pct=0.30,
    ),
    CareerTransition(
        from_role="senior_software_engineer",
        to_role="engineering_manager",
        difficulty="challenging",
        skills_to_acquire=[
            "people management",
            "hiring",
            "performance management",
            "conflict resolution",
        ],
        skills_transferable=["technical expertise", "project planning", "mentoring"],
        typical_timeline_months=12,
        salary_change_pct=0.15,
    ),
    CareerTransition(
        from_role="engineering_manager",
        to_role="director_of_engineering",
        difficulty="challenging",
        skills_to_acquire=[
            "org design",
            "budget management",
            "strategic planning",
            "executive presence",
        ],
        skills_transferable=["people management", "project delivery", "hiring"],
        typical_timeline_months=36,
        salary_change_pct=0.30,
    ),
    CareerTransition(
        from_role="software_engineer",
        to_role="product_manager",
        difficulty="moderate",
        skills_to_acquire=[
            "product strategy",
            "user research",
            "roadmapping",
            "stakeholder management",
        ],
        skills_transferable=[
            "technical knowledge",
            "problem solving",
            "analytical skills",
        ],
        typical_timeline_months=12,
        salary_change_pct=0.10,
    ),
    CareerTransition(
        from_role="data_scientist",
        to_role="senior_data_scientist",
        difficulty="moderate",
        skills_to_acquire=["ml engineering", "research methodology", "mentoring"],
        skills_transferable=["statistics", "python", "data analysis"],
        typical_timeline_months=24,
        salary_change_pct=0.25,
    ),
    CareerTransition(
        from_role="devops_engineer",
        to_role="sre",
        difficulty="moderate",
        skills_to_acquire=[
            "reliability principles",
            "incident management",
            "capacity planning",
        ],
        skills_transferable=["ci/cd", "cloud platforms", "automation"],
        typical_timeline_months=12,
        salary_change_pct=0.15,
    ),
    CareerTransition(
        from_role="ux_designer",
        to_role="senior_ux_designer",
        difficulty="moderate",
        skills_to_acquire=["design systems", "research leadership", "design strategy"],
        skills_transferable=["user research", "prototyping", "usability"],
        typical_timeline_months=24,
        salary_change_pct=0.25,
    ),
]


class CareerPathAnalyzer:
    def __init__(self):
        self.roles = CAREER_ROLES
        self.transitions = CAREER_TRANSITIONS

    def analyze_career_trajectory(
        self,
        work_history: list[dict[str, Any]],
        current_skills: list[str],
    ) -> dict[str, Any]:
        if not work_history:
            return {"error": "No work history provided"}

        total_years = sum(job.get("years", 1) for job in work_history)
        titles = [job.get("title", "").lower() for job in work_history]

        current_level = self._infer_level_from_titles(titles)
        current_track = self._infer_track_from_titles(titles)

        possible_next_roles = self._get_possible_transitions(
            current_level, current_track
        )

        return {
            "total_experience_years": total_years,
            "current_level": current_level.value if current_level else "unknown",
            "current_track": current_track.value if current_track else "unknown",
            "possible_next_roles": possible_next_roles,
            "career_progression_score": self._calculate_progression_score(work_history),
        }

    def get_career_path_recommendation(
        self,
        current_role: str,
        target_role: str,
        current_skills: list[str],
        years_experience: int = 0,
    ) -> CareerPathRecommendation | None:
        current_key = self._normalize_role_name(current_role)
        target_key = self._normalize_role_name(target_role)

        transition = self._find_transition(current_key, target_key)

        if not transition:
            transition = self._infer_transition(current_key, target_key)

        if not transition:
            return None

        skill_gaps = self._identify_skill_gaps(
            current_skills,
            transition.skills_to_acquire,
        )

        steps = self._generate_career_steps(transition, current_skills)

        return CareerPathRecommendation(
            current_role=current_role,
            target_role=target_role,
            path_type="direct" if transition else "inferred",
            steps=steps,
            skill_gaps=skill_gaps,
            estimated_timeline_months=transition.typical_timeline_months
            if transition
            else 24,
            potential_salary_increase_pct=transition.salary_change_pct
            if transition
            else 0.20,
            confidence=0.8 if transition else 0.5,
        )

    def suggest_next_career_moves(
        self,
        current_role: str,
        current_skills: list[str],
        preferences: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        current_key = self._normalize_role_name(current_role)

        possible_moves = []
        for transition in self.transitions:
            if transition.from_role == current_key:
                target_role = self.roles.get(transition.to_role)
                if target_role:
                    possible_moves.append(
                        {
                            "role": target_role.title,
                            "difficulty": transition.difficulty,
                            "timeline_months": transition.typical_timeline_months,
                            "salary_increase_pct": transition.salary_change_pct,
                            "skills_needed": transition.skills_to_acquire,
                            "transferable_skills": transition.skills_transferable,
                        }
                    )

        if not possible_moves:
            possible_moves = self._infer_next_moves(current_key, current_skills)

        if preferences:
            possible_moves = self._filter_by_preferences(possible_moves, preferences)

        incr("career_path.suggestions_generated")
        return possible_moves[:5]

    def identify_skill_gaps(
        self,
        current_role: str,
        target_role: str,
        current_skills: list[str],
    ) -> list[SkillGap]:
        target_key = self._normalize_role_name(target_role)
        target_role_data = self.roles.get(target_key)

        if not target_role_data:
            return []

        gaps = []
        current_lower = [s.lower() for s in current_skills]

        for skill in target_role_data.typical_skills:
            if skill.lower() not in current_lower:
                gaps.append(
                    SkillGap(
                        skill=skill,
                        importance="high"
                        if skill in target_role_data.typical_skills[:3]
                        else "medium",
                        acquisition_method=self._suggest_acquisition_method(skill),
                        estimated_time_weeks=self._estimate_skill_time(skill),
                        resources=self._get_skill_resources(skill),
                    )
                )

        incr("career_path.skill_gaps_identified", None, len(gaps))
        return gaps

    def get_learning_path(
        self,
        skill_gaps: list[SkillGap],
    ) -> dict[str, Any]:
        if not skill_gaps:
            return {"weeks": 0, "milestones": []}

        total_weeks = sum(gap.estimated_time_weeks for gap in skill_gaps)

        milestones = []
        current_week = 0
        for gap in sorted(
            skill_gaps, key=lambda g: g.importance == "high", reverse=True
        ):
            milestones.append(
                {
                    "skill": gap.skill,
                    "start_week": current_week,
                    "end_week": current_week + gap.estimated_time_weeks,
                    "resources": gap.resources,
                    "importance": gap.importance,
                }
            )
            current_week += gap.estimated_time_weeks

        return {
            "total_weeks": total_weeks,
            "milestones": milestones,
            "recommended_pace": "part_time" if total_weeks > 24 else "intensive",
        }

    def _normalize_role_name(self, role: str) -> str:
        role_lower = role.lower().replace(" ", "_").replace("-", "_")
        role_lower = role_lower.replace("(", "").replace(")", "")
        for key in self.roles:
            if key in role_lower or role_lower in key:
                return key
        return role_lower

    def _infer_level_from_titles(self, titles: list[str]) -> CareerLevel | None:
        all_titles = " ".join(titles).lower()
        if any(w in all_titles for w in ["cto", "chief"]):
            return CareerLevel.C_LEVEL
        if any(w in all_titles for w in ["vp", "vice president"]):
            return CareerLevel.VP
        if any(w in all_titles for w in ["director"]):
            return CareerLevel.DIRECTOR
        if any(w in all_titles for w in ["principal", "distinguished"]):
            return CareerLevel.PRINCIPAL
        if any(w in all_titles for w in ["staff"]):
            return CareerLevel.STAFF
        if any(w in all_titles for w in ["senior", "lead"]):
            return CareerLevel.SENIOR
        if any(w in all_titles for w in ["junior", "associate", "entry"]):
            return CareerLevel.JUNIOR
        return CareerLevel.MID

    def _infer_track_from_titles(self, titles: list[str]) -> CareerTrack:
        all_titles = " ".join(titles).lower()
        if any(w in all_titles for w in ["manager", "director", "vp", "head"]):
            return CareerTrack.MANAGEMENT
        return CareerTrack.INDIVIDUAL_CONTRIBUTOR

    def _get_possible_transitions(
        self,
        current_level: CareerLevel | None,
        current_track: CareerTrack | None,
    ) -> list[str]:
        possible = []
        level_order = list(CareerLevel)
        if current_level:
            current_idx = level_order.index(current_level)
            next_levels = level_order[current_idx + 1 : current_idx + 3]
            for role in self.roles.values():
                if role.level in next_levels:
                    possible.append(role.title)

        if current_track == CareerTrack.INDIVIDUAL_CONTRIBUTOR:
            possible.extend(["Engineering Manager", "Product Manager"])
        elif current_track == CareerTrack.MANAGEMENT:
            possible.extend(["Staff Engineer", "Principal Engineer"])

        return list(set(possible))[:8]

    def _calculate_progression_score(self, work_history: list[dict[str, Any]]) -> float:
        if not work_history:
            return 0.0

        score = 0.0
        titles = [job.get("title", "").lower() for job in work_history]

        for i, title in enumerate(titles[:-1]):
            next_title = titles[i + 1]
            current_level = self._infer_level_from_titles([title])
            next_level = self._infer_level_from_titles([next_title])

            if current_level and next_level:
                level_order = list(CareerLevel)
                current_idx = level_order.index(current_level)
                next_idx = level_order.index(next_level)
                if next_idx > current_idx:
                    score += 0.2

        return min(score, 1.0)

    def _find_transition(self, from_role: str, to_role: str) -> CareerTransition | None:
        for t in self.transitions:
            if t.from_role == from_role and t.to_role == to_role:
                return t
        return None

    def _infer_transition(self, from_key: str, to_key: str) -> CareerTransition | None:
        from_role = self.roles.get(from_key)
        to_role = self.roles.get(to_key)

        if not from_role or not to_role:
            return None

        return CareerTransition(
            from_role=from_key,
            to_role=to_key,
            difficulty="moderate",
            skills_to_acquire=to_role.typical_skills,
            skills_transferable=list(
                set(from_role.typical_skills) & set(to_role.typical_skills)
            ),
            typical_timeline_months=24,
            salary_change_pct=(
                (to_role.salary_range_usd[0] - from_role.salary_range_usd[0])
                / from_role.salary_range_usd[0]
            ),
        )

    def _identify_skill_gaps(
        self,
        current_skills: list[str],
        required_skills: list[str],
    ) -> list[SkillGap]:
        gaps = []
        current_lower = [s.lower() for s in current_skills]

        for skill in required_skills:
            if skill.lower() not in current_lower:
                gaps.append(
                    SkillGap(
                        skill=skill,
                        importance="high",
                        acquisition_method=self._suggest_acquisition_method(skill),
                        estimated_time_weeks=self._estimate_skill_time(skill),
                        resources=self._get_skill_resources(skill),
                    )
                )

        return gaps

    def _generate_career_steps(
        self,
        transition: CareerTransition,
        current_skills: list[str],
    ) -> list[dict[str, Any]]:
        steps = []

        steps.append(
            {
                "order": 1,
                "type": "skill_development",
                "description": "Build foundational skills for transition",
                "skills": transition.skills_to_acquire[:3],
                "timeline_weeks": 12,
            }
        )

        if len(transition.skills_to_acquire) > 3:
            steps.append(
                {
                    "order": 2,
                    "type": "skill_development",
                    "description": "Acquire advanced skills",
                    "skills": transition.skills_to_acquire[3:],
                    "timeline_weeks": 12,
                }
            )

        steps.append(
            {
                "order": len(steps) + 1,
                "type": "experience",
                "description": "Gain relevant project experience",
                "activities": [
                    "Lead cross-functional projects",
                    "Mentor junior team members",
                    "Present technical decisions to stakeholders",
                ],
                "timeline_weeks": 24,
            }
        )

        steps.append(
            {
                "order": len(steps) + 1,
                "type": "transition",
                "description": f"Transition to {transition.to_role}",
                "actions": [
                    "Update resume and LinkedIn",
                    "Apply for target roles",
                    "Network with professionals in target role",
                ],
                "timeline_weeks": 8,
            }
        )

        return steps

    def _infer_next_moves(
        self,
        current_key: str,
        current_skills: list[str],
    ) -> list[dict[str, Any]]:
        moves = []
        current_role = self.roles.get(current_key)

        if not current_role:
            return moves

        for key, role in self.roles.items():
            if role.level.value > current_role.level.value:
                overlap = len(
                    set(s.lower() for s in current_skills)
                    & set(s.lower() for s in role.typical_skills)
                )
                if overlap >= 2:
                    moves.append(
                        {
                            "role": role.title,
                            "difficulty": "moderate",
                            "timeline_months": 24,
                            "salary_increase_pct": 0.20,
                            "skills_needed": [
                                s
                                for s in role.typical_skills
                                if s.lower()
                                not in [cs.lower() for cs in current_skills]
                            ],
                            "transferable_skills": [
                                s
                                for s in role.typical_skills
                                if s.lower() in [cs.lower() for cs in current_skills]
                            ],
                        }
                    )

        return moves[:5]

    def _filter_by_preferences(
        self,
        moves: list[dict[str, Any]],
        preferences: dict[str, Any],
    ) -> list[dict[str, Any]]:
        filtered = moves

        if preferences.get("prefer_management"):
            management_roles = ["manager", "director", "vp", "head"]
            filtered = [
                m
                for m in filtered
                if any(r in m["role"].lower() for r in management_roles)
            ]

        if preferences.get("prefer_ic"):
            management_roles = ["manager", "director", "vp", "head"]
            filtered = [
                m
                for m in filtered
                if not any(r in m["role"].lower() for r in management_roles)
            ]

        if preferences.get("max_timeline_months"):
            filtered = [
                m
                for m in filtered
                if m["timeline_months"] <= preferences["max_timeline_months"]
            ]

        return filtered

    def _suggest_acquisition_method(self, skill: str) -> str:
        skill_lower = skill.lower()
        if any(
            w in skill_lower for w in ["programming", "python", "javascript", "coding"]
        ):
            return "online_course"
        if any(w in skill_lower for w in ["management", "leadership", "mentoring"]):
            return "on_the_job"
        if any(w in skill_lower for w in ["design", "ux", "ui"]):
            return "bootcamp"
        if any(w in skill_lower for w in ["strategy", "planning"]):
            return "mentorship"
        return "self_study"

    def _estimate_skill_time(self, skill: str) -> int:
        skill_lower = skill.lower()
        if any(w in skill_lower for w in ["programming", "python", "coding"]):
            return 8
        if any(w in skill_lower for w in ["management", "leadership"]):
            return 12
        if any(w in skill_lower for w in ["design", "ux"]):
            return 6
        if any(w in skill_lower for w in ["strategy", "architecture"]):
            return 10
        return 4

    def _get_skill_resources(self, skill: str) -> list[str]:
        resources = {
            "programming": ["Coursera", "Udemy", "freeCodeCamp"],
            "management": [
                "Harvard ManageMentor",
                "LinkedIn Learning",
                "Internal mentorship",
            ],
            "design": ["DesignLab", "Coursera UX Specialization", "Figma Academy"],
            "strategy": ["HBR articles", "Case studies", "Strategy workshops"],
            "default": ["LinkedIn Learning", "Coursera", "Industry blogs"],
        }

        skill_lower = skill.lower()
        for key, vals in resources.items():
            if key in skill_lower:
                return vals
        return resources["default"]
