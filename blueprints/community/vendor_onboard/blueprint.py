"""
Vendor Onboarding Blueprint — automates supplier/vendor registration forms.

Handles W-9, banking info collection, insurance cert uploads, and
compliance questionnaires across common procurement portals.
"""

from __future__ import annotations

from typing import Any

from backend.blueprints.protocol import AgentBlueprint


class VendorOnboardBlueprint:
    """Community blueprint: Vendor / Supplier Onboarding."""

    key = "vendor-onboard"
    display_name = "Vendor Onboarding"
    completion_status = "REGISTERED"

    def build_profile_parse_prompt(self, raw_text: str) -> str:
        return f"""Extract vendor/supplier information from the following text.
Return JSON with keys: company_name, dba_name, tax_id_type (EIN/SSN),
address_line1, address_line2, city, state, zip_code, country,
contact_name, contact_email, contact_phone, website,
business_type (LLC/Corp/Sole Prop/Partnership),
naics_code, duns_number, cage_code,
bank_name, routing_number, account_number,
insurance_provider, insurance_policy_number, insurance_expiry,
diverse_supplier (boolean), diversity_certifications (list).

Text:
{raw_text}"""

    def parse_profile_response(self, llm_output: str) -> dict[str, Any]:
        import json
        try:
            return json.loads(llm_output)
        except json.JSONDecodeError:
            return {"raw": llm_output}

    def normalize_profile(self, profile: dict[str, Any]) -> dict[str, Any]:
        return profile

    def build_dom_mapping_prompt(self, profile: dict[str, Any], fields: list[dict]) -> str:
        import json
        return f"""Map the vendor profile data to the form fields.

Vendor Profile:
{json.dumps(profile, indent=2)}

Form Fields:
{json.dumps(fields, indent=2)}

Return JSON array of {{field_id, value}} pairs. Use exact field IDs.
For tax ID fields, use the tax_id value.
For address fields, map to the appropriate address components.
For bank fields, map routing and account numbers.
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
            "button:has-text('Register')",
            "button:has-text('Submit')",
            "button:has-text('Complete Registration')",
            "button:has-text('Save & Continue')",
            "button:has-text('Next')",
            "#submit-vendor",
            ".vendor-submit-btn",
        ]

    async def on_task_completed(self, task_id: str, result: dict[str, Any]) -> None:
        pass
