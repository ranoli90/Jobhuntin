"""Domain-agnostic core models for the Autonomous Form Agent engine.

These models define the generic vocabulary that any vertical (job applications,
grant applications, vendor onboarding, etc.) maps onto. Sorce's concrete models
in models.py are backward-compatible specializations of these.

Vocabulary mapping:
  - Actor       → a user/profile (Sorce: user + profile)
  - TargetForm  → the form to be filled (Sorce: a job listing)
  - Task        → a queued work item (Sorce: an application row)
  - TaskInput   → a hold question (Sorce: application_input)
  - TaskEvent   → an audit event (Sorce: application_event)
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Generic Task Status (state machine)
# ---------------------------------------------------------------------------

class TaskStatus(enum.StrEnum):
    """Generic status enum for all agent tasks.

    State machine:
      QUEUED ──→ PROCESSING ──→ COMPLETED
        │            │               │
        │            ├──→ REQUIRES_INPUT ──→ (back to QUEUED when answered)
        │            │
        │            └──→ FAILED
        └──→ FAILED (if quota exceeded before processing)

    Blueprint-specific completion statuses (e.g., APPLIED for Sorce)
    are stored in the DB as-is; the generic layer treats them as COMPLETED.
    """

    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    REQUIRES_INPUT = "REQUIRES_INPUT"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# Mapping from blueprint-specific terminal statuses to the generic COMPLETED
COMPLETION_STATUS_ALIASES: dict[str, TaskStatus] = {
    "APPLIED": TaskStatus.COMPLETED,     # Sorce (job applications)
    "SUBMITTED": TaskStatus.COMPLETED,   # Grants, vendor onboarding
    "COMPLETED": TaskStatus.COMPLETED,
}


def is_terminal(status: str) -> bool:
    """Check if a status string represents a terminal state."""
    return status in ("COMPLETED", "FAILED", "APPLIED", "SUBMITTED")


def to_generic_status(status: str) -> TaskStatus:
    """Map a blueprint-specific status to its generic TaskStatus."""
    if status in COMPLETION_STATUS_ALIASES:
        return COMPLETION_STATUS_ALIASES[status]
    try:
        return TaskStatus(status)
    except ValueError:
        return TaskStatus.PROCESSING  # fallback for unknown statuses


# ---------------------------------------------------------------------------
# Generic Task Event Types
# ---------------------------------------------------------------------------

class TaskEventType(enum.StrEnum):
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
# ActorProfile — domain-neutral profile base
# ---------------------------------------------------------------------------

class ActorIdentity(BaseModel):
    """Core identity fields common to all verticals."""

    full_name: str = Field(default="", json_schema_extra={"pii": True})

    first_name: str = Field(default="", json_schema_extra={"pii": True})
    last_name: str = Field(default="", json_schema_extra={"pii": True})
    email: str = Field(default="", json_schema_extra={"pii": True})
    phone: str = Field(default="", json_schema_extra={"pii": True})
    location: str = Field(default="", json_schema_extra={"pii": True})


class ActorQualification(BaseModel):
    """A single qualification entry (education, certification, etc.)."""

    institution: str = ""
    title: str = ""        # degree, cert name, etc.
    field: str = ""        # field of study, specialization
    start_date: str = ""
    end_date: str = ""
    details: str = ""      # GPA, honors, etc.


class ActorHistoryEntry(BaseModel):
    """A single history entry (employment, project, engagement, etc.)."""

    organization: str = ""
    role: str = ""
    start_date: str = ""
    end_date: str = ""
    location: str = ""
    description: list[str] = Field(default_factory=list)


class ActorProfile(BaseModel):
    """Domain-neutral profile schema. Every blueprint extends this with
    vertical-specific fields via the `metadata` dict or by subclassing.

    Sections:
      identity       — PII / contact info
      qualifications — education, certs, languages
      history        — work/project/engagement history
      skills         — categorized skill lists
      metadata       — open-ended extension point (jsonb)
    """

    identity: ActorIdentity = Field(default_factory=ActorIdentity)
    qualifications: list[ActorQualification] = Field(default_factory=list)
    history: list[ActorHistoryEntry] = Field(default_factory=list)
    skills: dict[str, list[str]] = Field(default_factory=dict)
    certifications: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    summary: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Generic DB row models
# ---------------------------------------------------------------------------

class TargetForm(BaseModel):
    """A form that the agent will fill out. Sorce: a job listing."""

    id: str
    tenant_id: str | None = None
    form_url: str = ""
    blueprint_key: str = "job-app"
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class Task(BaseModel):
    """A queued work item. Sorce: an application row."""

    id: str
    user_id: str
    target_form_id: str
    tenant_id: str | None = None
    blueprint_key: str = "job-app"
    status: str = "QUEUED"
    error_message: str | None = None
    last_error: str | None = None
    attempt_count: int = 0
    locked_at: datetime | None = None
    submitted_at: datetime | None = None
    last_processed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}

    @property
    def generic_status(self) -> TaskStatus:
        return to_generic_status(self.status)

    @property
    def is_terminal(self) -> bool:
        return is_terminal(self.status)


class TaskInput(BaseModel):
    """A hold question. Sorce: application_input."""

    id: str
    task_id: str
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


class TaskEvent(BaseModel):
    """An audit event. Sorce: application_event."""

    id: str
    task_id: str
    tenant_id: str | None = None
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Form / LLM data structures (already generic, re-exported here)
# ---------------------------------------------------------------------------

class FormFieldOption(BaseModel):
    value: str
    text: str


class FormField(BaseModel):
    selector: str
    label: str
    type: str
    required: bool
    step_index: int
    options: list[FormFieldOption] | None = None


class UnresolvedField(BaseModel):
    selector: str
    question: str


class DomMappingResult(BaseModel):
    """Response schema for the DOM → profile field mapping LLM call."""

    field_values: dict[str, str] = Field(default_factory=dict)
    unresolved_required_fields: list[UnresolvedField] = Field(default_factory=list)
