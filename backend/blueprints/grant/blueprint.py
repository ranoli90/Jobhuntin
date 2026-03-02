"""Grant Application Blueprint — stub implementation.

Demonstrates how a second vertical coexists with Sorce's job-app blueprint
without touching the core engine. All methods are functional stubs.
"""

from __future__ import annotations

from datetime import UTC, datetime

import asyncpg

from backend.blueprints.grant.models import GrantApplicantProfile
from backend.blueprints.grant.prompts import (
    GRANT_SUBMIT_SELECTORS,
    build_grant_dom_mapping_prompt,
    build_grant_profile_parse_prompt,
)
from packages.backend.domain.core_models import (
    ActorProfile,
    DomMappingResult,
    FormField,
    UnresolvedField,
)
from packages.backend.domain.repositories import ApplicationRepo, EventRepo


class GrantApplicationBlueprint:
    """Grant application vertical — stub blueprint for demonstration."""

    @property
    def name(self) -> str:
        return "Grant Applications"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def slug(self) -> str:
        return "grant"

    # -- Profile parsing ---------------------------------------------------

    def build_profile_parse_prompt(self, raw_text: str) -> str:
        """Construct prompt to parse raw text into a GrantApplicantProfile."""
        return build_grant_profile_parse_prompt(raw_text)

    def parse_profile_response(self, raw_json: dict) -> ActorProfile:
        """Parse LLM JSON response into a GrantApplicantProfile."""
        return GrantApplicantProfile(**raw_json)

    def normalize_profile(self, raw: dict) -> ActorProfile:
        """Normalize raw profile dictionary into GrantApplicantProfile."""
        return GrantApplicantProfile(**raw)

    # -- DOM mapping -------------------------------------------------------

    def build_dom_mapping_prompt(
        self,
        profile: ActorProfile,
        form_fields: list[FormField],
        answered_inputs: list[dict] | None = None,
    ) -> str:
        """Construct prompt to map profile data to grant application form fields."""
        profile_dict = profile.model_dump()
        fields_dicts = [f.model_dump() if hasattr(f, "model_dump") else f for f in form_fields]
        return build_grant_dom_mapping_prompt(profile_dict, fields_dicts, answered_inputs)

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
        return GRANT_SUBMIT_SELECTORS

    # -- Completion hook ---------------------------------------------------

    async def on_task_completed(
        self,
        conn: asyncpg.Connection,
        task: dict,
        tenant_id: str | None,
    ) -> str:
        """Mark the grant application as SUBMITTED."""
        app_id = str(task["id"])
        await ApplicationRepo.update_status(conn, app_id, "SUBMITTED")
        await EventRepo.emit(conn, app_id, "SUBMITTED", {
            "submitted_at": datetime.now(UTC).isoformat(),
        }, tenant_id=tenant_id)
        return "SUBMITTED"
