"""Grant Application Blueprint — LLM prompt templates.

Production prompts tuned for common grant portals (Grants.gov, foundations,
university research offices). Handles org identity, project details, budget,
and compliance fields.
"""

from __future__ import annotations

import json

# ===================================================================
# Contract 1: Document Parsing → GrantApplicantProfile
# ===================================================================

GRANT_PROFILE_PARSE_PROMPT_V1 =
    """You are a grant application document parser specializing in extracting structured information from organization d
    ocuments, grant narratives, and applicant profiles.

## Document Text
{document_text}

## Instructions
Extract ALL available information and return ONLY a JSON object (no markdown fences) with these keys:
{{
    "contact": {{
        "full_name": "",
        "email": "",
        "phone": "",
        "location": ""
    }},
    "organization_name": "",
    "organization_ein": "",
    "organization_type": "",
    "organization_duns": "",
    "organization_address": "",
    "organization_website": "",
    "organization_founding_year": null,
    "organization_annual_budget": null,
    "organization_mission": "",
    "project_title": "",
    "project_description": "",
    "project_start_date": "",
    "project_end_date": "",
    "project_location": "",
    "target_population": "",
    "expected_outcomes": "",
    "requested_amount": null,
    "budget_narrative": "",
    "matching_funds": null,
    "total_project_cost": null,
    "grant_category": "",
    "cfda_number": "",
    "qualifications": [],
    "past_grants": [],
    "key_personnel": [{{"name": "", "title": "", "role": ""}}],
    "summary": ""
}}

Rules:
- organization_type must be one of: nonprofit, university, govt, tribal, for-profit, other
- Dates should be ISO format (YYYY-MM-DD) when possible
- Monetary values should be numbers (no currency symbols)
- qualifications and past_grants are arrays of short descriptions
- Fill in every field you can find. Use empty strings or null for missing data.
"""


def build_grant_profile_parse_prompt(document_text: str) -> str:
    return GRANT_PROFILE_PARSE_PROMPT_V1.format(document_text=document_text)


# ===================================================================
# Contract 2: DOM Mapping for Grant Forms
# ===================================================================

GRANT_DOM_MAPPING_PROMPT_V1 =
    """You are a grant application autofill assistant. You fill web-based grant application forms using the applicant's
    organization and project data.

## Applicant Profile
{profile_json}

## Previously Answered Questions (authoritative — these override profile data)
{answered_json}

## Form Fields (extracted from the page DOM)
{fields_json}

## Grant-Specific Mapping Rules
1. Map organization fields: org name, EIN, DUNS/UEI, address, type, mission.
2. Map project fields: title, description/abstract/narrative, dates, location, target population.
3. Map budget fields: requested amount, total cost, matching funds, budget narrative.
4. Map contact/PI fields: name, email, phone, title.
5. For dropdown/select fields, choose the closest matching option from the available values.
6. For textarea fields containing "narrative" or "description", provide substantive multi-sentence content from the
profile.
7. For checkboxes asking about org type, certifications, or compliance, check them if the profile data supports it.
8. Required fields that CANNOT be answered from the profile go into "unresolved_required_fields" with a clear question
for the user.
9. Optional unanswerable fields: omit entirely (do not include in field_values).
10. Previously answered questions are AUTHORITATIVE — always use those values over profile data.

## Respond with ONLY this JSON (no markdown):
{{
    "field_values": {{"<css_selector>": "<value_to_fill>"}},
    "unresolved_required_fields": [{{"selector": "<css_selector>", "question": "<human_readable_question>"}}]
}}
"""


def build_grant_dom_mapping_prompt(
    profile_dict: dict,
    form_fields: list[dict],
    answered_inputs: list[dict] | None = None,
) -> str:
    return GRANT_DOM_MAPPING_PROMPT_V1.format(
        profile_json=json.dumps(profile_dict, indent=2),
        answered_json=json.dumps(answered_inputs or [], indent=2),
        fields_json=json.dumps(form_fields, indent=2, default=str),
    )


# ===================================================================
# Submit button selectors (grant portals — ordered by specificity)
# ===================================================================

GRANT_SUBMIT_SELECTORS = [
    # Grants.gov specific
    'button:has-text("Submit Application")',
    'button:has-text("Submit Proposal")',
    'a:has-text("Submit Application")',
    # Foundation portals
    'button:has-text("Submit Grant")',
    'button:has-text("Submit Request")',
    'button:has-text("Submit LOI")',
    # Generic
    'button[type="submit"]',
    'input[type="submit"]',
    'button:has-text("Submit")',
    'button:has-text("Send")',
    'button:has-text("Complete")',
    'button:has-text("Finalize")',
]
