"""LinkedIn Job Application Blueprint — automates LinkedIn job applications.

Handles LinkedIn's specific application flow including their Easy Apply system,
profile integration, and network-based application features.
"""

from __future__ import annotations

from typing import Any


class LinkedInBlueprint:
    """Community blueprint: LinkedIn Job Applications."""

    key = "linkedin"
    display_name = "LinkedIn Applications"
    completion_status = "SUBMITTED"

    def build_profile_parse_prompt(self, raw_text: str) -> str:
        return f"""Extract professional profile information from the following resume text.
Return JSON with keys: full_name, email, phone, location, city, state, country,
headline, summary, experience (
    list of {{title, company, start_date, end_date, description, location, employment_type}}),
education (list of {{school, degree, field, start_date, end_date, gpa, activities}}),
skills (list of strings with proficiency levels), certifications (list of {{name, issuer, date, url}}),
languages (list of {{language, proficiency}}), linkedin_url, portfolio_url, github_url,
projects (list of {{name, description, technologies, url}}), publications (list of {{title, publisher, date, url}}),
honors_awards (
    list of {{name, issuer, date}}), volunteer_experience (list of {{organization, role, start_date, end_date,
    description}}).

Focus on professional networking and career progression.
Include LinkedIn-specific fields like headline and summary.
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
        """Normalize profile for LinkedIn's specific requirements."""
        # Generate headline if not present
        if not profile.get("headline") and profile.get("experience"):
            # Use most recent job title as headline
            latest_job = profile["experience"][0] if profile["experience"] else {}
            profile["headline"] = (
                f"{latest_job.get('title', '')} at {latest_job.get('company', '')}"
            )

        # Ensure location is properly formatted
        if profile.get("city") and profile.get("state"):
            profile["location"] = f"{profile['city']}, {profile['state']}"
        elif profile.get("location"):
            # Clean up location format
            profile["location"] = profile["location"].strip()

        return profile

    def build_dom_mapping_prompt(
        self, profile: dict[str, Any], fields: list[dict]
    ) -> str:
        import json

        return f"""Map the professional profile to LinkedIn's application form fields.

Applicant Profile:
{json.dumps(profile, indent=2)}

Form Fields:
{json.dumps(fields, indent=2)}

Return JSON array of {{field_id, value}} pairs.

Special handling for LinkedIn:
- For headline: use current or most recent job title
- For summary: use professional summary or generate from experience
- For experience: provide most relevant roles with descriptions
- For education: include degree, field, and graduation date
- For skills: include both hard and soft skills, prioritize relevance
- For resume: attach if LinkedIn allows file upload
- For cover letter: generate concise, professional introduction
- For availability: "Open to opportunities" or specific timeline
- For work preferences: "Remote", "Hybrid", or "On-site"
- For salary: use market rate or "Negotiable"
- For relocation: "Willing to relocate" if applicable

LinkedIn values professional presentation and completeness."""

    def parse_dom_mapping_response(self, llm_output: str) -> list[dict[str, Any]]:
        import json

        try:
            return json.loads(llm_output)
        except json.JSONDecodeError:
            return []

    def submit_button_selectors(self) -> list[str]:
        """Return CSS selectors for LinkedIn submit buttons."""
        return [
            "button[type='submit']",
            "input[type='submit']",
            "button:has-text('Apply')",
            "button:has-text('Easy Apply')",
            "button:has-text('Submit Application')",
            "button:has-text('Continue')",
            ".jobs-apply-button",
            ".jobs-easy-apply-button",
            "[data-test-id='apply-button']",
            "[data-test-entity-urn*='apply']",
            "[aria-label*='Apply']",
            "[aria-label*='Easy Apply']",
        ]

    async def on_task_completed(self, task_id: str, result: dict[str, Any]) -> None:
        """Handle LinkedIn-specific task completion."""
        # LinkedIn often shows network connections after application
        if result.get("status") == "success":
            # Could trigger network connection suggestions
            pass

    def get_pre_application_checks(self) -> list[str]:
        """Return pre-application validation checks for LinkedIn."""
        return [
            "verify_linkedin_profile_completeness",
            "check_network_connections",
            "validate_professional_headline",
            "ensure_skills_section_populated",
            "confirm_work_history_accuracy",
        ]

    def get_post_application_actions(self) -> list[str]:
        """Return post-application actions for LinkedIn."""
        return [
            "suggest_network_connections",
            "follow_company_page",
            "save_job_to_collection",
            "enable_job_alerts",
        ]
