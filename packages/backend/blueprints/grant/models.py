"""Grant Application profile model.

Extends ActorProfile with grant-specific fields: organization details,
project information, budget narrative, and compliance data.
"""

from __future__ import annotations

from pydantic import Field

from packages.backend.domain.core_models import ActorProfile


class GrantApplicantProfile(ActorProfile):
    """Grant-specific extension of ActorProfile.

    Stores all data needed to auto-fill grant application forms:
    organization identity, project details, budget, and qualifications.
    """

    # Organization identity
    organization_name: str = ""
    organization_ein: str = ""  # EIN / Tax ID
    organization_type: str = ""  # nonprofit, university, govt, tribal, for-profit
    organization_duns: str = ""  # DUNS / UEI number
    organization_address: str = ""
    organization_website: str = ""
    organization_founding_year: int | None = None
    organization_annual_budget: float | None = None
    organization_mission: str = ""

    # Project details
    project_title: str = ""
    project_description: str = ""
    project_start_date: str = ""
    project_end_date: str = ""
    project_location: str = ""
    target_population: str = ""
    expected_outcomes: str = ""

    # Budget
    requested_amount: float | None = None
    budget_narrative: str = ""
    matching_funds: float | None = None
    total_project_cost: float | None = None

    # Classification
    grant_category: str = ""  # education, health, environment, arts, etc.
    cfda_number: str = ""  # CFDA / Assistance Listing number

    # Qualifications / past performance
    qualifications: list[str] = Field(default_factory=list)
    past_grants: list[str] = Field(default_factory=list)
    key_personnel: list[dict[str, str]] = Field(default_factory=list)

    # Canonical field map for DOM autofill
    FIELD_MAP: dict[str, list[str]] = {
        "organization_name": [
            "org name",
            "organization",
            "applicant name",
            "legal name",
            "entity name",
        ],
        "organization_ein": [
            "ein",
            "tax id",
            "tax identification",
            "fein",
            "employer id",
        ],
        "organization_type": [
            "org type",
            "organization type",
            "entity type",
            "applicant type",
        ],
        "organization_duns": ["duns", "uei", "unique entity", "sam.gov"],
        "organization_address": [
            "org address",
            "organization address",
            "mailing address",
        ],
        "project_title": [
            "project title",
            "proposal title",
            "grant title",
            "project name",
        ],
        "project_description": [
            "project description",
            "abstract",
            "summary",
            "narrative",
            "proposal summary",
        ],
        "requested_amount": [
            "amount requested",
            "funding request",
            "grant amount",
            "budget request",
        ],
        "budget_narrative": [
            "budget narrative",
            "budget justification",
            "budget description",
        ],
        "contact_name": [
            "contact name",
            "pi name",
            "principal investigator",
            "authorized representative",
        ],
        "contact_email": ["contact email", "pi email", "email address"],
        "contact_phone": ["contact phone", "phone number", "telephone"],
    }
