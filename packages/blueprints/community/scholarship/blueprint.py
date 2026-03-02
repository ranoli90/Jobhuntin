"""Scholarship Application Blueprint — automates scholarship form submissions.

Handles personal essays, academic records, financial aid forms, and
recommendation request workflows across scholarship portals.
"""

from __future__ import annotations

from typing import Any


class ScholarshipBlueprint:
    """Community blueprint: Scholarship Applications."""

    key = "scholarship"
    display_name = "Scholarship Applications"
    completion_status = "SUBMITTED"

    def build_profile_parse_prompt(self, raw_text: str) -> str:
        return f"""Extract scholarship applicant information from the following text.
Return JSON with keys: full_name, date_of_birth, email, phone,
address, city, state, zip_code, country,
high_school_name, high_school_gpa, graduation_year,
college_name, college_gpa, major, expected_graduation,
sat_score, act_score,
financial_need_level (high/medium/low),
extracurriculars (list of {{activity, role, years}}),
awards (list of strings),
essay_topics (list of strings),
career_goals, personal_statement,
reference_name, reference_email, reference_relationship.

Text:
{raw_text}"""

    def parse_profile_response(self, llm_output: str) -> dict[str, Any]:
        import json
        try:
            return json.loads(llm_output)
        except json.JSONDecodeError:
            return {"raw": llm_output}

    def normalize_profile(self, profile: dict[str, Any]) -> dict[str, Any]:
        """Normalize profile dictionary (pass-through)."""
        return profile

    def build_dom_mapping_prompt(self, profile: dict[str, Any], fields: list[dict]) -> str:
        import json
        return f"""Map the scholarship applicant profile to form fields.

Applicant Profile:
{json.dumps(profile, indent=2)}

Form Fields:
{json.dumps(fields, indent=2)}

Return JSON array of {{field_id, value}} pairs.
For GPA fields, format as X.XX.
For essay/textarea fields, use the personal_statement or career_goals.
For dropdown/select fields, choose the closest matching option.
Leave fields empty if no matching data."""

    def parse_dom_mapping_response(self, llm_output: str) -> list[dict[str, Any]]:
        import json
        try:
            return json.loads(llm_output)
        except json.JSONDecodeError:
            return []

    def submit_button_selectors(self) -> list[str]:
        """Return CSS selectors for scholarship submit buttons."""
        return [
            "button[type='submit']",
            "input[type='submit']",
            "button:has-text('Submit Application')",
            "button:has-text('Apply')",
            "button:has-text('Submit')",
            "button:has-text('Complete')",
            ".submit-application",
            "#submitBtn",
        ]

    async def on_task_completed(self, task_id: str, result: dict[str, Any]) -> None:
        """Handle task completion (no-op)."""
        pass
