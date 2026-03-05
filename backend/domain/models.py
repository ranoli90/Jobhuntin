"""Single source of truth for all domain models.

Both api/main.py and worker/agent.py import from here.
Pydantic models for API serialization; plain dicts/enums for DB interop.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ApplicationStatus(enum.StrEnum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    REQUIRES_INPUT = "REQUIRES_INPUT"
    APPLIED = "APPLIED"  # Sorce job-app terminal status
    SUBMITTED = "SUBMITTED"  # Grant/vendor terminal status
    COMPLETED = "COMPLETED"  # Generic terminal status
    FAILED = "FAILED"


class TenantPlan(enum.StrEnum):
    FREE = "FREE"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"


class TenantRole(enum.StrEnum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"
    SUPPORT_AGENT = "SUPPORT_AGENT"


class ApplicationEventType(enum.StrEnum):
    CREATED = "CREATED"
    CLAIMED = "CLAIMED"
    STARTED_PROCESSING = "STARTED_PROCESSING"
    REQUIRES_INPUT_RAISED = "REQUIRES_INPUT_RAISED"
    USER_ANSWERED = "USER_ANSWERED"
    RESUMED = "RESUMED"
    SUBMITTED = "SUBMITTED"
    FAILED = "FAILED"
    RETRY_SCHEDULED = "RETRY_SCHEDULED"


# ---------------------------------------------------------------------------
# Canonical Profile (the "Digital Twin" schema for LLM prompts)
# ---------------------------------------------------------------------------


class CanonicalContact(BaseModel):
    # PII fields: these contain personally identifiable information
    # and must be redacted before logging or support views.
    full_name: str = Field(default="", json_schema_extra={"pii": True})
    first_name: str = Field(default="", json_schema_extra={"pii": True})
    last_name: str = Field(default="", json_schema_extra={"pii": True})
    email: str = Field(default="", json_schema_extra={"pii": True})
    phone: str = Field(default="", json_schema_extra={"pii": True})
    location: str = Field(default="", json_schema_extra={"pii": True})
    linkedin_url: str = Field(default="", json_schema_extra={"pii": True})
    portfolio_url: str = Field(default="", json_schema_extra={"pii": True})


class CanonicalEducation(BaseModel):
    """Educational history entry."""

    institution: str = ""
    degree: str = ""
    field_of_study: str = ""
    start_date: str = ""
    end_date: str = ""
    gpa: str = ""


class CanonicalExperience(BaseModel):
    """Professional experience entry."""

    company: str = ""
    title: str = ""
    start_date: str = ""
    end_date: str = ""
    location: str = ""
    responsibilities: list[str] = Field(default_factory=list)


class CanonicalSkills(BaseModel):
    """Categorized skills."""

    technical: list[str] = Field(default_factory=list)
    soft: list[str] = Field(default_factory=list)


class CanonicalProfile(BaseModel):
    """Full normalized user profile.
    Acts as the source of truth for filling job applications.
    """

    contact: CanonicalContact = Field(default_factory=CanonicalContact)
    education: list[CanonicalEducation] = Field(default_factory=list)
    experience: list[CanonicalExperience] = Field(default_factory=list)
    skills: CanonicalSkills = Field(default_factory=CanonicalSkills)
    certifications: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    summary: str = ""
    current_title: str = ""
    current_company: str = ""
    years_experience: int | None = None


def _extract_name_parts(full_name: str) -> tuple[str, str]:
    """Extract first and last name from full name."""
    parts = full_name.split(maxsplit=1) if full_name else []
    first = parts[0] if parts else ""
    last = parts[1] if len(parts) > 1 else ""
    return first, last


def _parse_contact(contact_raw: dict) -> CanonicalContact:
    """Parse contact information from raw data."""
    full_name = contact_raw.get("full_name", "")
    first, last = _extract_name_parts(full_name)

    return CanonicalContact(
        full_name=full_name,
        first_name=contact_raw.get("first_name", "") or first,
        last_name=contact_raw.get("last_name", "") or last,
        email=contact_raw.get("email", ""),
        phone=contact_raw.get("phone", ""),
        location=contact_raw.get("location", ""),
        linkedin_url=contact_raw.get("linkedin_url", ""),
        portfolio_url=contact_raw.get("portfolio_url", ""),
    )


def _parse_education(education_raw: list) -> list[CanonicalEducation]:
    """Parse education entries from raw data."""
    return [
        CanonicalEducation(
            **{k: e.get(k, "") for k in CanonicalEducation.model_fields}
        )  # pylint: disable=not-an-iterable
        for e in education_raw
    ]


def _parse_experience(experience_raw: list) -> list[CanonicalExperience]:
    """Parse experience entries from raw data."""
    return [
        CanonicalExperience(
            company=x.get("company", ""),
            title=x.get("title", ""),
            start_date=x.get("start_date", ""),
            end_date=x.get("end_date", ""),
            location=x.get("location", ""),
            responsibilities=x.get("responsibilities", []),
        )
        for x in experience_raw
    ]


def _extract_skill_names(skills_list: list) -> list[str]:
    """Extract skill names from V2 (dict) or V1 (string) format."""
    names = []
    for item in skills_list:
        if isinstance(item, dict):
            names.append(item.get("skill", ""))
        elif isinstance(item, str):
            names.append(item)
    return [s for s in names if s]


def _parse_skills(skills_raw: dict) -> CanonicalSkills:
    """Parse skills from raw data, handling both V1 and V2 formats."""
    technical = _extract_skill_names(skills_raw.get("technical", []))
    soft = _extract_skill_names(skills_raw.get("soft", []))
    return CanonicalSkills(technical=technical, soft=soft)


def _get_current_info(experience: list[CanonicalExperience]) -> tuple[str, str]:
    """Get current title and company from most recent experience."""
    if experience:
        return experience[0].title, experience[0].company
    return "", ""


def normalize_profile(raw: dict) -> CanonicalProfile:
    """Transform a raw profile_data blob into the canonical shape."""
    contact = _parse_contact(raw.get("contact", {}))
    education = _parse_education(raw.get("education", []))
    experience = _parse_experience(raw.get("experience", []))
    skills = _parse_skills(raw.get("skills", {}))
    current_title, current_company = _get_current_info(experience)

    return CanonicalProfile(
        contact=contact,
        education=education,
        experience=experience,
        skills=skills,
        certifications=raw.get("certifications", []),
        languages=raw.get("languages", []),
        summary=raw.get("summary", ""),
        current_title=current_title,
        current_company=current_company,
        years_experience=raw.get("years_experience"),
    )


# ---------------------------------------------------------------------------
# DB row models (for typed returns from repositories)
# ---------------------------------------------------------------------------


class Tenant(BaseModel):
    """Tenant (Organization/Team) entity.
    Represents a billing unit and isolation scope.
    """

    id: str
    name: str
    slug: str
    plan: TenantPlan = TenantPlan.FREE
    plan_metadata: dict[str, Any] = Field(default_factory=dict)
    blueprint_key: str = "job-app"
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class TenantMember(BaseModel):
    id: str
    tenant_id: str
    user_id: str
    role: TenantRole = TenantRole.MEMBER
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class Job(BaseModel):
    id: str
    external_id: str
    title: str
    company: str
    description: str | None = None
    location: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    category: str | None = None
    application_url: str
    source: str = ""
    tenant_id: str | None = None  # NULL = global/shared catalog
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class Application(BaseModel):
    id: str
    user_id: str
    job_id: str
    tenant_id: str | None = None
    blueprint_key: str = "job-app"
    status: ApplicationStatus
    error_message: str | None = None
    last_error: str | None = None
    attempt_count: int = 0
    locked_at: datetime | None = None
    submitted_at: datetime | None = None
    last_processed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class ApplicationInput(BaseModel):
    """Interactive form field requiring user input.
    Used when the Agent hits a question it cannot answer automatically.
    """

    id: str
    application_id: str
    tenant_id: str | None = None
    selector: str
    question: str
    field_type: str
    answer: str | None = None
    resolved: bool = False
    meta: dict[str, Any] | None = None
    created_at: datetime | None = None
    answered_at: datetime | None = None

    model_config = {"from_attributes": True}


class ApplicationEvent(BaseModel):
    id: str
    application_id: str
    tenant_id: str | None = None
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Aggregated views
# ---------------------------------------------------------------------------


class ApplicationDetail(BaseModel):
    """Typed container for application detail queries."""

    application: Application
    inputs: list[ApplicationInput] = Field(default_factory=list)
    events: list[ApplicationEvent] = Field(default_factory=list)

    def to_serializable(self) -> dict[str, Any]:
        """Return JSON-ready dict (iso datetimes, string UUIDs)."""
        return {
            "application": self.application.model_dump(mode="json"),
            "inputs": [inp.model_dump(mode="json") for inp in self.inputs],
            "events": [evt.model_dump(mode="json") for evt in self.events],
        }


# ---------------------------------------------------------------------------
# Form / LLM data structures (used by worker)
# ---------------------------------------------------------------------------


class FormFieldOption(BaseModel):
    value: str
    text: str


class FormField(BaseModel):
    """DOM element representation extracted from the target page."""

    selector: str
    label: str
    type: str
    required: bool
    step_index: int
    options: list[FormFieldOption] | None = None


class UnresolvedField(BaseModel):
    """Field that the LLM could not map confidently."""

    selector: str
    question: str


class LLMMapping(BaseModel):
    """Response schema for the DOM → profile field mapping LLM call."""

    field_values: dict[str, str] = Field(default_factory=dict)
    unresolved_required_fields: list[UnresolvedField] = Field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> LLMMapping:
        return cls(
            field_values=d.get("field_values", {}),
            unresolved_required_fields=[
                UnresolvedField(**u) for u in d.get("unresolved_required_fields", [])
            ],
        )


# ---------------------------------------------------------------------------
# Standard API error envelope
# ---------------------------------------------------------------------------


class ErrorResponse(BaseModel):
    """Stable error shape returned by all API error responses."""

    error: ErrorDetail


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None
