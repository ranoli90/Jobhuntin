"""
Staffing Agency Blueprint — bulk candidate submission to client ATS portals.

Handles Greenhouse, Lever, Workday, iCIMS, BambooHR, and generic career pages.
Designed for staffing agencies submitting multiple candidates per role.
"""

from __future__ import annotations

from typing import Any


class StaffingAgencyBlueprint:
    """Enterprise blueprint: Staffing Agency — bulk candidate ATS submission."""

    key = "staffing-agency"
    display_name = "Staffing Agency"
    completion_status = "SUBMITTED"

    def build_profile_parse_prompt(self, raw_text: str) -> str:
        return f"""Extract candidate information from the following staffing submission data.
Return JSON with keys: full_name, email, phone, linkedin_url,
title, years_experience, skills (list), location,
salary_expectation, availability, work_authorization,
education (list of {{school, degree, year}}),
certifications (list),
previous_roles (list of {{company, title, duration}}),
summary (2-3 sentence professional summary).

Text:
{raw_text}"""

    def parse_profile_response(self, llm_output: str) -> dict[str, Any]:
        """Parse LLM JSON response into candidate profile dict."""
        import json
        try:
            return json.loads(llm_output)
        except json.JSONDecodeError:
            return {"raw": llm_output}

    def normalize_profile(self, profile: dict[str, Any]) -> dict[str, Any]:
        return profile

    def build_dom_mapping_prompt(self, profile: dict[str, Any], fields: list[dict]) -> str:
        """Construct prompt to map candidate profile to ATS form fields."""
        import json
        return f"""Map the candidate profile data to the ATS application form fields.

Candidate Profile:
{json.dumps(profile, indent=2)}

Form Fields:
{json.dumps(fields, indent=2)}

Return JSON array of {{field_id, value}} pairs.
IMPORTANT RULES FOR ATS FORMS:
- For name fields, use full_name or split into first/last as needed.
- For resume/file upload fields, return the resume_url.
- For "How did you hear about us?" use "Staffing Agency Referral".
- For salary fields, use salary_expectation.
- For availability/start date, use availability.
- For work authorization dropdowns, select the matching option.
- For LinkedIn fields, use linkedin_url.
- For skills/textarea fields, join skills list with commas.
Leave fields empty if no matching data."""

    def parse_dom_mapping_response(self, llm_output: str) -> list[dict[str, Any]]:
        import json
        try:
            return json.loads(llm_output)
        except json.JSONDecodeError:
            return []

    def submit_button_selectors(self) -> list[str]:
        return [
            "button[type='submit']",
            "input[type='submit']",
            "button:has-text('Submit Application')",
            "button:has-text('Submit')",
            "button:has-text('Apply')",
            "button:has-text('Apply Now')",
            "button:has-text('Submit Candidate')",
            "button:has-text('Send Application')",
            # Greenhouse
            "#submit_app",
            "button[data-hook='submit']",
            # Lever
            ".posting-btn-submit",
            # Workday
            "button[data-automation-id='bottom-navigation-next-button']",
            # iCIMS
            ".iCIMS_ActionButton",
            # BambooHR
            ".fab-Button--submit",
        ]

    async def on_task_completed(self, task_id: str, result: dict[str, Any]) -> None:
        """Handle task completion (no-op)."""
        pass
