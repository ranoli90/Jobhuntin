"""
Adaptive Onboarding and Profiling System.

Implements intelligent onboarding as recommended in competitive analysis:
- Dynamic questionnaire based on user responses
- Machine learning feedback loop for profile refinement
- Dealbreaker configuration (salary, location, remote preferences)
- Behavioral question training from user edits

Based on JobCopilot's adaptive ML ingestion approach.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any, Callable

from pydantic import BaseModel, Field

from shared.logging_config import get_logger

logger = get_logger("sorce.onboarding")


class QuestionCategory(str, Enum):
    BASIC_INFO = "basic_info"
    EXPERIENCE = "experience"
    SKILLS = "skills"
    PREFERENCES = "preferences"
    DEALBREAKERS = "dealbreakers"
    WORK_STYLE = "work_style"
    CAREER_GOALS = "career_goals"


class QuestionType(str, Enum):
    TEXT = "text"
    TEXTAREA = "textarea"
    SELECT = "select"
    MULTISELECT = "multiselect"
    RANGE = "range"
    BOOLEAN = "boolean"
    DATE = "date"
    CURRENCY = "currency"


class OnboardingQuestion(BaseModel):
    id: str
    category: QuestionCategory
    question: str
    question_type: QuestionType
    placeholder: str | None = None
    required: bool = True
    options: list[str] | None = None
    min_value: float | None = None
    max_value: float | None = None
    depends_on: str | None = None
    depends_value: Any = None
    priority: int = 0
    field_mapping: str | None = None


class OnboardingAnswer(BaseModel):
    question_id: str
    answer: Any
    edited: bool = False
    confidence: float = 1.0


class DealbreakerConfig(BaseModel):
    min_salary: int | None = None
    max_salary: int | None = None
    required_locations: list[str] = Field(default_factory=list)
    excluded_locations: list[str] = Field(default_factory=list)
    remote_only: bool = False
    hybrid_acceptable: bool = True
    onsite_acceptable: bool = True
    visa_sponsorship_required: bool = False
    required_benefits: list[str] = Field(default_factory=list)
    excluded_companies: list[str] = Field(default_factory=list)
    min_company_size: int | None = None
    max_company_size: int | None = None
    industries_preference: list[str] = Field(default_factory=list)
    industries_excluded: list[str] = Field(default_factory=list)


class AdaptiveProfile(BaseModel):
    user_id: str
    basic_info: dict[str, Any] = Field(default_factory=dict)
    experience_summary: dict[str, Any] = Field(default_factory=dict)
    skills: dict[str, list[str]] = Field(default_factory=dict)
    preferences: dict[str, Any] = Field(default_factory=dict)
    dealbreakers: DealbreakerConfig = Field(default_factory=DealbreakerConfig)
    work_style: dict[str, Any] = Field(default_factory=dict)
    career_goals: dict[str, Any] = Field(default_factory=dict)
    learned_preferences: dict[str, Any] = Field(default_factory=dict)
    profile_completeness: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


QUESTIONS: list[OnboardingQuestion] = [
    OnboardingQuestion(
        id="current_title",
        category=QuestionCategory.BASIC_INFO,
        question="What is your current or most recent job title?",
        question_type=QuestionType.TEXT,
        placeholder="e.g., Senior Software Engineer",
        field_mapping="current_title",
        priority=10,
    ),
    OnboardingQuestion(
        id="years_experience",
        category=QuestionCategory.EXPERIENCE,
        question="How many years of professional experience do you have?",
        question_type=QuestionType.SELECT,
        options=["0-1 years", "1-3 years", "3-5 years", "5-10 years", "10+ years"],
        field_mapping="years_experience",
        priority=9,
    ),
    OnboardingQuestion(
        id="current_company",
        category=QuestionCategory.BASIC_INFO,
        question="What company do you currently work for? (or most recent)",
        question_type=QuestionType.TEXT,
        placeholder="e.g., Google, Startup, Self-employed",
        required=False,
        field_mapping="current_company",
        priority=8,
    ),
    OnboardingQuestion(
        id="target_roles",
        category=QuestionCategory.CAREER_GOALS,
        question="What job titles are you looking for?",
        question_type=QuestionType.TEXT,
        placeholder="e.g., Software Engineer, Product Manager, Data Scientist",
        field_mapping="target_roles",
        priority=10,
    ),
    OnboardingQuestion(
        id="technical_skills",
        category=QuestionCategory.SKILLS,
        question="What are your top technical skills?",
        question_type=QuestionType.TEXT,
        placeholder="e.g., Python, JavaScript, AWS, Machine Learning",
        field_mapping="skills.technical",
        priority=9,
    ),
    OnboardingQuestion(
        id="soft_skills",
        category=QuestionCategory.SKILLS,
        question="What are your key soft skills?",
        question_type=QuestionType.TEXT,
        placeholder="e.g., Leadership, Communication, Problem-solving",
        required=False,
        field_mapping="skills.soft",
        priority=7,
    ),
    OnboardingQuestion(
        id="min_salary",
        category=QuestionCategory.DEALBREAKERS,
        question="What is your minimum acceptable salary? (annual, USD)",
        question_type=QuestionType.CURRENCY,
        placeholder="e.g., 100000",
        required=False,
        field_mapping="dealbreakers.min_salary",
        priority=8,
    ),
    OnboardingQuestion(
        id="location_preference",
        category=QuestionCategory.PREFERENCES,
        question="What is your preferred work location?",
        question_type=QuestionType.SELECT,
        options=["Remote only", "Hybrid", "On-site", "Open to all"],
        field_mapping="preferences.location_type",
        priority=8,
    ),
    OnboardingQuestion(
        id="preferred_locations",
        category=QuestionCategory.PREFERENCES,
        question="Which cities/regions are you open to working in?",
        question_type=QuestionType.TEXT,
        placeholder="e.g., San Francisco, New York, Remote",
        required=False,
        field_mapping="dealbreakers.required_locations",
        priority=7,
    ),
    OnboardingQuestion(
        id="excluded_locations",
        category=QuestionCategory.DEALBREAKERS,
        question="Are there any locations you want to exclude?",
        question_type=QuestionType.TEXT,
        placeholder="e.g., Non-US, High cost of living areas",
        required=False,
        field_mapping="dealbreakers.excluded_locations",
        priority=5,
    ),
    OnboardingQuestion(
        id="visa_sponsorship",
        category=QuestionCategory.DEALBREAKERS,
        question="Do you require visa sponsorship?",
        question_type=QuestionType.BOOLEAN,
        field_mapping="dealbreakers.visa_sponsorship_required",
        priority=8,
    ),
    OnboardingQuestion(
        id="company_size_preference",
        category=QuestionCategory.PREFERENCES,
        question="What company size do you prefer?",
        question_type=QuestionType.SELECT,
        options=[
            "Startup (<50)",
            "Small (50-200)",
            "Mid-size (200-1000)",
            "Large (1000+)",
            "Any size",
        ],
        required=False,
        field_mapping="preferences.company_size",
        priority=6,
    ),
    OnboardingQuestion(
        id="industry_preference",
        category=QuestionCategory.PREFERENCES,
        question="Do you have industry preferences?",
        question_type=QuestionType.TEXT,
        placeholder="e.g., FinTech, Healthcare, E-commerce",
        required=False,
        field_mapping="dealbreakers.industries_preference",
        priority=5,
    ),
    OnboardingQuestion(
        id="notice_period",
        category=QuestionCategory.WORK_STYLE,
        question="What is your notice period?",
        question_type=QuestionType.SELECT,
        options=["Immediately", "2 weeks", "1 month", "2+ months"],
        required=False,
        field_mapping="work_style.notice_period",
        priority=4,
    ),
    OnboardingQuestion(
        id="work_auth",
        category=QuestionCategory.BASIC_INFO,
        question="What is your work authorization status?",
        question_type=QuestionType.SELECT,
        options=[
            "Citizen/Permanent Resident",
            "H1B Visa",
            "F1-OPT",
            "Other Visa",
            "Need Sponsorship",
        ],
        required=False,
        field_mapping="basic_info.work_authorization",
        priority=7,
    ),
    OnboardingQuestion(
        id="linkedin_url",
        category=QuestionCategory.BASIC_INFO,
        question="What is your LinkedIn profile URL?",
        question_type=QuestionType.TEXT,
        placeholder="https://linkedin.com/in/yourprofile",
        required=False,
        field_mapping="basic_info.linkedin_url",
        priority=3,
    ),
    OnboardingQuestion(
        id="portfolio_url",
        category=QuestionCategory.BASIC_INFO,
        question="Do you have a portfolio or personal website?",
        question_type=QuestionType.TEXT,
        placeholder="https://yourportfolio.com",
        required=False,
        field_mapping="basic_info.portfolio_url",
        priority=2,
    ),
    OnboardingQuestion(
        id="career_goal",
        category=QuestionCategory.CAREER_GOALS,
        question="What is your primary career goal?",
        question_type=QuestionType.SELECT,
        options=[
            "Senior IC role",
            "Management/Leadership",
            "Career change",
            "Higher compensation",
            "Better work-life balance",
            "Startup experience",
        ],
        required=False,
        field_mapping="career_goals.primary_goal",
        priority=6,
    ),
    OnboardingQuestion(
        id="why_leaving",
        category=QuestionCategory.CAREER_GOALS,
        question="Why are you looking to leave your current role?",
        question_type=QuestionType.SELECT,
        options=[
            "Career growth",
            "Compensation",
            "Company culture",
            "Layoff/Restructuring",
            "Relocation",
            "Contract ending",
            "N/A - Not currently employed",
        ],
        required=False,
        field_mapping="career_goals.leaving_reason",
        priority=5,
    ),
    OnboardingQuestion(
        id="job_search_urgency",
        category=QuestionCategory.CAREER_GOALS,
        question="How urgently are you looking for a new role?",
        question_type=QuestionType.SELECT,
        options=["Actively interviewing", "Open to opportunities", "Just browsing"],
        required=False,
        field_mapping="career_goals.urgency",
        priority=5,
    ),
]


class OnboardingService:
    """
    Adaptive onboarding service that creates personalized questionnaires
    and learns from user responses.
    """

    def __init__(self):
        self._questions = {q.id: q for q in QUESTIONS}
        self._edit_history: dict[str, list[dict[str, Any]]] = {}

    def get_initial_questions(self, count: int = 10) -> list[OnboardingQuestion]:
        sorted_questions = sorted(QUESTIONS, key=lambda q: q.priority, reverse=True)
        return sorted_questions[:count]

    def get_next_questions(
        self,
        answered: dict[str, Any],
        count: int = 5,
    ) -> list[OnboardingQuestion]:
        answered_ids = set(answered.keys())

        available = [
            q
            for q in QUESTIONS
            if q.id not in answered_ids and self._check_dependency(q, answered)
        ]

        available.sort(key=lambda q: q.priority, reverse=True)

        return available[:count]

    def _check_dependency(
        self, question: OnboardingQuestion, answered: dict[str, Any]
    ) -> bool:
        if not question.depends_on:
            return True

        if question.depends_on not in answered:
            return False

        return answered[question.depends_on] == question.depends_value

    def build_profile(
        self,
        user_id: str,
        answers: dict[str, Any],
    ) -> AdaptiveProfile:
        profile = AdaptiveProfile(user_id=user_id)

        for question_id, answer in answers.items():
            question = self._questions.get(question_id)
            if not question:
                continue

            self._apply_answer_to_profile(profile, question, answer)

        profile.profile_completeness = self._calculate_completeness(profile)
        profile.updated_at = datetime.now(UTC)

        return profile

    def _apply_answer_to_profile(
        self,
        profile: AdaptiveProfile,
        question: OnboardingQuestion,
        answer: Any,
    ) -> None:
        if not question.field_mapping:
            return

        mapping = question.field_mapping
        parts = mapping.split(".")

        if len(parts) == 1:
            setattr(profile, parts[0], answer)
        elif len(parts) == 2:
            parent, child = parts
            parent_obj = getattr(profile, parent, None)
            if parent_obj is not None:
                if isinstance(parent_obj, dict):
                    parent_obj[child] = answer
                else:
                    setattr(parent_obj, child, answer)

        if mapping.startswith("skills."):
            skill_type = parts[1]
            if isinstance(answer, str):
                skills_list = [s.strip() for s in answer.split(",") if s.strip()]
            else:
                skills_list = answer if isinstance(answer, list) else [answer]
            profile.skills[skill_type] = skills_list

        elif mapping.startswith("dealbreakers."):
            field = parts[1]
            if field in [
                "required_locations",
                "excluded_locations",
                "industries_preference",
            ]:
                if isinstance(answer, str):
                    value = [a.strip() for a in answer.split(",") if a.strip()]
                else:
                    value = answer if isinstance(answer, list) else [answer]
                setattr(profile.dealbreakers, field, value)
            elif field == "min_salary":
                try:
                    profile.dealbreakers.min_salary = int(answer)
                except (ValueError, TypeError):
                    pass
            else:
                setattr(profile.dealbreakers, field, answer)

        elif mapping.startswith("preferences."):
            field = parts[1]
            profile.preferences[field] = answer
            if field == "location_type":
                if answer == "Remote only":
                    profile.dealbreakers.remote_only = True
                    profile.dealbreakers.hybrid_acceptable = False
                    profile.dealbreakers.onsite_acceptable = False
                elif answer == "Hybrid":
                    profile.dealbreakers.remote_only = False
                    profile.dealbreakers.hybrid_acceptable = True
                    profile.dealbreakers.onsite_acceptable = False

        elif mapping.startswith("work_style."):
            field = parts[1]
            profile.work_style[field] = answer

        elif mapping.startswith("career_goals."):
            field = parts[1]
            profile.career_goals[field] = answer

        elif mapping.startswith("basic_info."):
            field = parts[1]
            profile.basic_info[field] = answer

    def _calculate_completeness(self, profile: AdaptiveProfile) -> float:
        total_fields = 0
        filled_fields = 0

        if profile.current_title:
            filled_fields += 1
        total_fields += 1

        if profile.skills.get("technical"):
            filled_fields += 1
        total_fields += 1

        if profile.dealbreakers.min_salary:
            filled_fields += 1
        total_fields += 1

        if profile.preferences.get("location_type"):
            filled_fields += 1
        total_fields += 1

        if profile.career_goals.get("primary_goal"):
            filled_fields += 1
        total_fields += 1

        for field in ["target_roles", "years_experience", "visa_sponsorship"]:
            total_fields += 1
            if profile.basic_info.get(field) or profile.career_goals.get(field):
                filled_fields += 1

        return filled_fields / total_fields if total_fields > 0 else 0.0

    def record_edit(
        self,
        user_id: str,
        field: str,
        original_value: Any,
        new_value: Any,
        context: str = "application",
    ) -> None:
        if user_id not in self._edit_history:
            self._edit_history[user_id] = []

        self._edit_history[user_id].append(
            {
                "field": field,
                "original": original_value,
                "new": new_value,
                "context": context,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )

        logger.info(
            "Recorded profile edit for user %s: %s changed in %s context",
            user_id,
            field,
            context,
        )

    def get_learned_preferences(self, user_id: str) -> dict[str, Any]:
        if user_id not in self._edit_history:
            return {}

        edits = self._edit_history[user_id]
        learned: dict[str, Any] = {}

        field_edits: dict[str, list] = {}
        for edit in edits:
            field = edit["field"]
            if field not in field_edits:
                field_edits[field] = []
            field_edits[field].append(edit)

        for field, field_edit_list in field_edits.items():
            if len(field_edit_list) >= 2:
                new_values = [e["new"] for e in field_edit_list]
                if len(set(str(v) for v in new_values)) == 1:
                    learned[field] = new_values[-1]

        return learned

    def apply_learned_preferences(
        self,
        profile: AdaptiveProfile,
    ) -> AdaptiveProfile:
        learned = self.get_learned_preferences(profile.user_id)

        for field, value in learned.items():
            if field.startswith("skills."):
                skill_type = field.split(".")[1]
                if isinstance(value, list):
                    current = profile.skills.get(skill_type, [])
                    profile.skills[skill_type] = list(set(current + value))

            profile.learned_preferences[field] = value

        return profile


_onboarding_service: OnboardingService | None = None


def get_onboarding_service() -> OnboardingService:
    global _onboarding_service
    if _onboarding_service is None:
        _onboarding_service = OnboardingService()
    return _onboarding_service
