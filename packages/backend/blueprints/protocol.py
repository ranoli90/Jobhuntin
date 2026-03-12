"""AgentBlueprint Protocol — the contract every vertical must implement.

The core engine (FormAgent) is parameterized by a blueprint instance.
Each blueprint owns:
  - Profile parsing prompts and normalization
  - DOM mapping prompts
  - Submit-button selectors for Playwright
  - Completion hook (what status to set, what events to emit)
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import asyncpg

from packages.backend.domain.core_models import ActorProfile, DomMappingResult, FormField


@runtime_checkable
class AgentBlueprint(Protocol):
    """Protocol that every vertical blueprint must satisfy."""

    @property
    def name(self) -> str:
        """Human-readable name, e.g. 'Job Applications'."""
        ...

    @property
    def version(self) -> str:
        """Semantic version of this blueprint."""
        ...

    @property
    def slug(self) -> str:
        """Unique key matching tenants.blueprint_key, e.g. 'job-app'."""
        ...

    # -- Profile parsing ---------------------------------------------------

    def build_profile_parse_prompt(self, raw_text: str) -> str:
        """Build the LLM prompt that extracts a structured profile from raw text."""
        ...

    def parse_profile_response(self, raw_json: dict) -> ActorProfile:
        """Validate and normalize the LLM's profile parse response."""
        ...

    def normalize_profile(self, raw: dict) -> ActorProfile:
        """Transform a raw profile_data blob from the DB into an ActorProfile."""
        ...

    # -- DOM mapping -------------------------------------------------------

    def build_dom_mapping_prompt(
        self,
        profile: ActorProfile,
        form_fields: list[FormField],
        answered_inputs: list[dict] | None = None,
    ) -> str:
        """Build the LLM prompt that maps DOM form fields to profile values."""
        ...

    def parse_dom_mapping_response(self, raw_json: dict) -> DomMappingResult:
        """Validate the LLM's DOM mapping response."""
        ...

    # -- Playwright submit -------------------------------------------------

    def submit_button_selectors(self) -> list[str]:
        """Ordered list of CSS selectors to try when clicking the submit button.
        More specific selectors first.
        """
        ...

    # -- Completion hook ---------------------------------------------------

    async def on_task_completed(
        self,
        conn: asyncpg.Connection,
        task: dict,
        tenant_id: str | None,
    ) -> str:
        """Called after successful form submission.

        Responsible for:
          - Setting the final task status (e.g., 'APPLIED' for jobs)
          - Emitting completion events

        Returns the final status string.
        """
        ...
