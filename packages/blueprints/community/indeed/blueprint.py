"""Indeed Job Application Blueprint — automates Indeed job applications.

Handles Indeed's specific form structure, resume upload, and application flow
including their custom fields and validation requirements.
"""

from __future__ import annotations

from typing import Any


class IndeedBlueprint:
    """Community blueprint: Indeed Job Applications."""

    key = "indeed"
    display_name = "Indeed Applications"
    completion_status = "SUBMITTED"

    def build_profile_parse_prompt(self, raw_text: str) -> str:
        return f"""Extract job applicant information from the following resume text.
Return JSON with keys: full_name, email, phone, location, city, state, zip_code, country,
summary, experience (list of {{title, company, start_date, end_date, description, location}}),
education (list of {{school, degree, field, start_date, end_date, gpa}}),
skills (list of strings), certifications (list of {{name, issuer, date}}),
languages (list of {{language, proficiency}}), linkedin_url, portfolio_url.

Focus on professional experience and skills relevant to job applications.
Format dates consistently (YYYY-MM or YYYY).

Text:
{raw_text}"""

    def parse_profile_response(self, llm_output: str) -> dict[str, Any]:
        import json

        try:
            return json.loads(llm_output)
        except json.JSONDecodeError:
            return {"raw": llm_output}

    def normalize_profile(self, profile: dict[str, Any]) -> dict[str, Any]:
        """Normalize profile for Indeed's specific field requirements."""
        # Ensure location is in "City, State" format
        if profile.get("city") and profile.get("state"):
            profile["location"] = f"{profile['city']}, {profile['state']}"
        elif profile.get("location"):
            # Extract city and state from location if available
            location_parts = profile["location"].split(",")
            if len(location_parts) >= 2:
                profile["city"] = location_parts[0].strip()
                profile["state"] = location_parts[1].strip()
        
        return profile

    def build_dom_mapping_prompt(
        self, profile: dict[str, Any], fields: list[dict]
    ) -> str:
        import json

        return f"""Map the job applicant profile to Indeed's form fields.

Applicant Profile:
{json.dumps(profile, indent=2)}

Form Fields:
{json.dumps(fields, indent=2)}

Return JSON array of {{field_id, value}} pairs.

Special handling for Indeed:
- For resume upload: use resume_url if available
- For location: use "City, State" format
- For experience: provide most recent/relevant role
- For education: provide highest degree
- For skills: provide top 5-7 relevant skills
- For availability: "Immediately" or specific date if known
- For salary: use "Negotiable" if not specified
- For authorization: "Yes" if legally authorized to work
- For sponsorship: "No" if no sponsorship required

Leave fields empty if no matching data."""

    def parse_dom_mapping_response(self, llm_output: str) -> list[dict[str, Any]]:
        import json

        try:
            return json.loads(llm_output)
        except json.JSONDecodeError:
            return []

    def submit_button_selectors(self) -> list[str]:
        """Return CSS selectors for Indeed submit buttons."""
        return [
            "button[type='submit']",
            "input[type='submit']",
            "button:has-text('Apply')",
            "button:has-text('Submit Application')",
            "button:has-text('Continue')",
            "button:has-text('Next')",
            ".indeed-apply-button",
            "#apply-now-button",
            "[data-testid='apply-button']",
            "[aria-label*='Apply']",
            "[aria-label*='Submit']",
        ]

    async def on_task_completed(self, task_id: str, result: dict[str, Any]) -> None:
        """Handle Indeed-specific task completion."""
        # Indeed might require additional confirmation steps
        if result.get("status") == "success":
            # Log successful application for tracking
            pass

    def get_pre_application_checks(self) -> list[str]:
        """Return pre-application validation checks for Indeed."""
        return [
            "verify_resume_uploaded",
            "check_profile_completeness", 
            "validate_contact_information",
            "confirm_job_requirements_match",
        ]
