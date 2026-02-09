"""
PII masking utilities for admin views and logging.

Provides helpers to partially redact sensitive fields so support engineers
can identify records without seeing full PII.
"""

from __future__ import annotations

import re
from typing import Any


def mask_email(email: str) -> str:
    """Mask email: 'alice@example.com' → 'a****@example.com'."""
    if not email or "@" not in email:
        return email
    local, domain = email.rsplit("@", 1)
    if len(local) <= 1:
        return f"*@{domain}"
    return f"{local[0]}{'*' * (len(local) - 1)}@{domain}"


def mask_phone(phone: str) -> str:
    """Mask phone: '+15551234567' → '+1555***4567'."""
    digits = re.sub(r"[^\d]", "", phone)
    if len(digits) <= 4:
        return phone
    return phone[:len(phone) - 4].replace(
        digits[:-4], "*" * len(digits[:-4])
    )[-len(phone):] if len(digits) > 4 else "****" + digits[-4:]


def mask_name(name: str) -> str:
    """Mask name: 'Alice Smith' → 'A**** S****'."""
    if not name:
        return name
    parts = name.split()
    return " ".join(
        f"{p[0]}{'*' * (len(p) - 1)}" if len(p) > 1 else p
        for p in parts
    )


def redact_profile_for_support(profile_data: dict[str, Any]) -> dict[str, Any]:
    """
    Return a copy of profile_data with PII fields masked.
    Safe for support engineer viewing.
    """
    result = _deep_copy_dict(profile_data)

    contact = result.get("contact", {})
    if isinstance(contact, dict):
        if "full_name" in contact:
            contact["full_name"] = mask_name(contact["full_name"])
        if "first_name" in contact:
            contact["first_name"] = mask_name(contact["first_name"])
        if "last_name" in contact:
            contact["last_name"] = mask_name(contact["last_name"])
        if "email" in contact:
            contact["email"] = mask_email(contact["email"])
        if "phone" in contact:
            contact["phone"] = mask_phone(contact["phone"])
        if "location" in contact:
            contact["location"] = "***"
        if "linkedin_url" in contact:
            contact["linkedin_url"] = "***"
        if "portfolio_url" in contact and contact["portfolio_url"]:
            contact["portfolio_url"] = "***"

    return result


def redact_profile_for_logging(profile_data: dict[str, Any]) -> dict[str, Any]:
    """
    Aggressively redact profile data for log output.
    Strips all PII; keeps only structural info.
    """
    result = _deep_copy_dict(profile_data)

    contact = result.get("contact", {})
    if isinstance(contact, dict):
        for key in ("full_name", "first_name", "last_name", "email", "phone",
                     "location", "linkedin_url", "portfolio_url"):
            if key in contact:
                contact[key] = "[REDACTED]"

    return result


def redact_event_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Remove PII-bearing keys from event payloads for anonymization."""
    sensitive_keys = {"email", "phone", "full_name", "first_name", "last_name",
                      "location", "linkedin_url", "portfolio_url", "answer"}
    result = {}
    for k, v in payload.items():
        if k in sensitive_keys:
            result[k] = "[REDACTED]"
        elif isinstance(v, dict):
            result[k] = redact_event_payload(v)
        else:
            result[k] = v
    return result


def _deep_copy_dict(d: dict[str, Any]) -> dict[str, Any]:
    """Simple deep copy for nested dicts/lists (no external dependency)."""
    result: dict[str, Any] = {}
    for k, v in d.items():
        if isinstance(v, dict):
            result[k] = _deep_copy_dict(v)
        elif isinstance(v, list):
            result[k] = [_deep_copy_dict(i) if isinstance(i, dict) else i for i in v]
        else:
            result[k] = v
    return result
