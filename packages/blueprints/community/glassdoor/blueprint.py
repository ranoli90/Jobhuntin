"""Glassdoor Job Application Blueprint — automates Glassdoor job applications.

Handles Glassdoor's company review integration, salary insights, and
application flow including their unique form structure and validation.
"""

from __future__ import annotations

from typing import Any


class GlassdoorBlueprint:
    """Community blueprint: Glassdoor Job Applications."""

    key = "glassdoor"
    display_name = "Glassdoor Applications"
    completion_status = "SUBMITTED"

    def build_profile_parse_prompt(self, raw_text: str) -> str:
        return f"""Extract job applicant information from the following resume text.
Return JSON with keys: full_name, email, phone, location, city, state, zip_code, country,
summary, experience (list of {{title, company, start_date, end_date, description, location, salary}}),
education (list of {{school, degree, field, start_date, end_date, gpa}}),
skills (list of strings), certifications (list of {{name, issuer, date}}),
languages (list of {{language, proficiency}}), portfolio_url, github_url,
salary_expectations (min, max, currency), work_preferences (remote, hybrid, on-site),
industry_experience (list of industries), company_size_preference (startup, small, medium, large),
management_experience (years_direct_reports, team_size), career_goals.

Include salary information and company size preferences as Glassdoor focuses on compensation data.
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
        """Normalize profile for Glassdoor's compensation-focused approach."""
        # Set default salary expectations if not provided
        if not profile.get("salary_expectations"):
            profile["salary_expectations"] = {
                "min": "50000",
                "max": "80000",
                "currency": "USD",
            }

        # Set default work preferences
        if not profile.get("work_preferences"):
            profile["work_preferences"] = "hybrid"

        # Ensure location is properly formatted
        if profile.get("city") and profile.get("state"):
            profile["location"] = f"{profile['city']}, {profile['state']}"

        return profile

    def build_dom_mapping_prompt(
        self, profile: dict[str, Any], fields: list[dict]
    ) -> str:
        import json

        return f"""Map the job applicant profile to Glassdoor's application form fields.

Applicant Profile:
{json.dumps(profile, indent=2)}

Form Fields:
{json.dumps(fields, indent=2)}

Return JSON array of {{field_id, value}} pairs.

Special handling for Glassdoor:
- For salary expectations: provide realistic range based on experience
- For company size: indicate preference (startup, small, medium, large)
- For industry: specify relevant industries from experience
- For management experience: include team size if applicable
- For work preferences: remote/hybrid/on-site preference
- For resume: attach if Glassdoor allows file upload
- For cover letter: mention knowledge of company from Glassdoor reviews
- For availability: "Immediately" or specific notice period
- For relocation: indicate willingness if applicable
- For benefits: prioritize if mentioned in job description

Glassdoor values compensation transparency and company culture insights."""

    def parse_dom_mapping_response(self, llm_output: str) -> list[dict[str, Any]]:
        import json

        try:
            return json.loads(llm_output)
        except json.JSONDecodeError:
            return []

    def submit_button_selectors(self) -> list[str]:
        """Return CSS selectors for Glassdoor submit buttons."""
        return [
            "button[type='submit']",
            "input[type='submit']",
            "button:has-text('Apply')",
            "button:has-text('Apply Now')",
            "button:has-text('Submit Application')",
            "button:has-text('Continue')",
            ".gd-apply-button",
            ".apply-btn",
            "[data-testid='apply-button']",
            "[data-gd-track*='apply']",
            "[aria-label*='Apply']",
            ".applyNow",
        ]

    async def on_task_completed(self, task_id: str, result: dict[str, Any]) -> None:
        """Handle Glassdoor-specific task completion."""
        # Glassdoor might prompt for company reviews after application
        if result.get("status") == "success":
            # Could suggest reviewing the company
            pass

    def get_pre_application_checks(self) -> list[str]:
        """Return pre-application validation checks for Glassdoor."""
        return [
            "verify_salary_expectations",
            "check_company_reviews_read",
            "validate_industry_experience",
            "confirm_work_location_preference",
            "ensure_resume_uploaded",
        ]

    def get_post_application_actions(self) -> list[str]:
        """Return post-application actions for Glassdoor."""
        return [
            "review_company_ratings",
            "check_salary_data",
            "read_interview_experiences",
            "set_job_alert",
            "research_company_culture",
        ]
