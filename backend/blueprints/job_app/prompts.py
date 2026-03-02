"""Sorce Job Application Blueprint — LLM prompt templates.

Extracted from backend/llm/contracts.py. These are the Sorce-specific
prompt texts; the generic LLM client and response schemas remain in backend/llm/.
"""

from __future__ import annotations

import json

# ===================================================================
# Contract 1: Resume Parsing → CanonicalProfile (Job Seeker)
# ===================================================================

RESUME_PARSE_PROMPT_V1 = """You are a resume parser. Extract structured information from the following resume text.

## Resume Text
{resume_text}

## Instructions
Return ONLY a JSON object (no markdown fences) with exactly these top-level keys:
{{
    "contact": {{
        "full_name": "",
        "email": "",
        "phone": "",
        "location": "",
        "linkedin_url": "",
        "portfolio_url": ""
    }},
    "education": [
        {{
            "institution": "",
            "degree": "",
            "field_of_study": "",
            "start_date": "",
            "end_date": "",
            "gpa": ""
        }}
    ],
    "experience": [
        {{
            "company": "",
            "title": "",
            "start_date": "",
            "end_date": "",
            "location": "",
            "responsibilities": [""]
        }}
    ],
    "skills": {{
        "technical": [""],
        "soft": [""]
    }},
    "certifications": [""],
    "languages": [""],
    "summary": ""
}}

Fill in every field you can find. Use empty strings or empty arrays for missing data.
"""


def build_resume_parse_prompt(resume_text: str) -> str:
    """Fill the resume parse prompt template."""
    return RESUME_PARSE_PROMPT_V1.format(resume_text=resume_text)


# ===================================================================
# Contract 2: DOM Mapping → field values + unresolved fields (Job App)
# ===================================================================

DOM_MAPPING_PROMPT_V1 = """You are a job-application autofill assistant. Your goal is to fill a web form using the user's profile data.

## Canonical User Profile
{profile_json}

## Previously Answered Questions (authoritative – override profile if conflicting)
{answered_json}

## Form Fields
Each field is JSON with keys: selector, label, type, required, step_index, options.
For selects and radios, "options" is a list of {{value, text}} objects.
{fields_json}

## Rules
1. For every field, if the profile or previously answered questions contain enough data, add
   an entry to "field_values" mapping the field's `selector` to the concrete value.
   - For <select> fields: return the `value` attribute of the best-matching option.
   - For radio buttons: return the `value` attribute of the best-matching option.
   - For checkboxes: return "true" or "false".
   - For text/email/tel/textarea: return the plain string.
2. If a **required** field cannot be answered, add it to "unresolved_required_fields" with:
   - "selector": the CSS selector,
   - "question": a short user-friendly question.
3. Optional fields that cannot be answered: omit from both lists.
4. User-provided answers (Previously Answered Questions) are authoritative and must always
   override any profile data if there is a conflict.

## Respond with ONLY this JSON (no markdown fences, no commentary):
{{
    "field_values": {{"<selector>": "<value>"}},
    "unresolved_required_fields": [{{"selector": "<selector>", "question": "<question>"}}]
}}
"""


def build_dom_mapping_prompt(
    profile_dict: dict,
    form_fields: list[dict],
    answered_inputs: list[dict] | None = None,
) -> str:
    """Fill the DOM mapping prompt template for job applications."""
    return DOM_MAPPING_PROMPT_V1.format(
        profile_json=json.dumps(profile_dict, indent=2),
        answered_json=json.dumps(answered_inputs or [], indent=2),
        fields_json=json.dumps(form_fields, indent=2, default=str),
    )


# ===================================================================
# Submit button selectors (job application forms)
# ===================================================================

JOB_APP_SUBMIT_SELECTORS = [
    'button[type="submit"]',
    'input[type="submit"]',
    'button:has-text("Submit")',
    'button:has-text("Apply")',
    'button:has-text("Send Application")',
    'button:has-text("Send")',
]
