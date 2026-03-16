"""Sorce Job Application Blueprint — concrete AgentBlueprint implementation.

This is the first (and reference) blueprint. It wraps all Sorce-specific logic:
  - Resume parsing prompts
  - DOM mapping prompts tuned for job application forms
  - Submit button selectors for common ATS systems
  - Completion hook that sets status to APPLIED
"""

from __future__ import annotations

from datetime import datetime, timezone

import asyncpg

from backend.blueprints.job_app.models import (
    JobSeekerProfile,
    from_canonical_profile,
    to_canonical_dict,
)
from backend.blueprints.job_app.prompts import JOB_APP_SUBMIT_SELECTORS
from backend.blueprints.job_app.prompts import (
    build_dom_mapping_prompt as _build_dom_mapping_prompt,
)
from backend.blueprints.job_app.prompts import (
    build_resume_parse_prompt as _build_resume_parse_prompt,
)
from backend.domain.core_models import (
    ActorProfile,
    DomMappingResult,
    FormField,
    UnresolvedField,
)
from backend.domain.repositories import ApplicationRepo, EventRepo


class JobApplicationBlueprint:
    """Sorce's job-application vertical — the reference AgentBlueprint."""

    @property
    def name(self) -> str:
        return "Job Applications"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def slug(self) -> str:
        return "job-app"

    # -- Profile parsing ---------------------------------------------------

    def build_profile_parse_prompt(self, raw_text: str) -> str:
        """Construct prompt to parse resume text into a JobSeekerProfile."""
        return _build_resume_parse_prompt(raw_text)

    def parse_profile_response(self, raw_json: dict) -> ActorProfile:
        """Parse LLM JSON response into JobSeekerProfile."""
        return from_canonical_profile(raw_json)

    def normalize_profile(self, raw: dict) -> ActorProfile:
        """Normalize raw profile dictionary into JobSeekerProfile."""
        return from_canonical_profile(raw)

    # -- DOM mapping -------------------------------------------------------

    def build_dom_mapping_prompt(
        self,
        profile: ActorProfile,
        form_fields: list[FormField],
        answered_inputs: list[dict] | None = None,
    ) -> str:
        """Construct prompt to map profile data to job application form fields."""
        # Convert ActorProfile back to the canonical dict shape the prompt expects
        if isinstance(profile, JobSeekerProfile):
            profile_dict = to_canonical_dict(profile)
        else:
            profile_dict = profile.model_dump()

        fields_dicts = [
            f.model_dump() if hasattr(f, "model_dump") else f for f in form_fields
        ]
        return _build_dom_mapping_prompt(profile_dict, fields_dicts, answered_inputs)

    def parse_dom_mapping_response(self, raw_json: dict) -> DomMappingResult:
        """Parse LLM JSON response into DomMappingResult."""
        return DomMappingResult(
            field_values=raw_json.get("field_values", {}),
            unresolved_required_fields=[
                UnresolvedField(**u)
                for u in raw_json.get("unresolved_required_fields", [])
            ],
        )

    # -- Playwright submit -------------------------------------------------

    def submit_button_selectors(self) -> list[str]:
        """Return CSS selectors for the submit button."""
        return JOB_APP_SUBMIT_SELECTORS

    # -- Completion hook ---------------------------------------------------

    async def on_task_completed(
        self,
        conn: asyncpg.Connection,
        task: dict,
        tenant_id: str | None,
    ) -> str:
        """Mark the application as APPLIED and emit SUBMITTED event."""
        app_id = str(task["id"])
        await ApplicationRepo.update_status(conn, app_id, "APPLIED")
        await EventRepo.emit(
            conn,
            app_id,
            "SUBMITTED",
            {
                "submitted_at": datetime.now(timezone.utc).isoformat(),
            },
            tenant_id=tenant_id,
        )
        return "APPLIED"
