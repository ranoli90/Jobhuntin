"""HTTP-first apply for Greenhouse and Lever (Section 3.3 High).

Try form-based HTTP submission before spinning up Playwright.
Falls back to browser when form is JS-rendered or submission fails.
"""

from __future__ import annotations

import re
from io import IOBase
from typing import Any
from urllib.parse import urljoin

import httpx

from packages.backend.domain.ats_handlers import ATSPlatform, detect_ats_platform
from shared.logging_config import get_logger

logger = get_logger("sorce.http_apply")

# Realistic User-Agent for HTTP requests (avoid bot detection)
HTTP_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _get_profile_fields(profile: Any) -> dict[str, str]:
    """Extract first_name, last_name, email, phone from profile."""
    contact = getattr(profile, "contact", None) if hasattr(profile, "contact") else None
    if contact is None and isinstance(profile, dict):
        contact = profile.get("contact", {})
    if contact is None:
        contact = {}

    first = ""
    last = ""
    email = ""
    phone = ""
    if hasattr(contact, "first_name"):
        first = contact.first_name or ""
    elif isinstance(contact, dict):
        first = contact.get("first_name", "") or ""
    if hasattr(contact, "last_name"):
        last = contact.last_name or ""
    elif isinstance(contact, dict):
        last = contact.get("last_name", "") or ""
    if hasattr(contact, "email"):
        email = contact.email or ""
    elif isinstance(contact, dict):
        email = contact.get("email", "") or ""
    if hasattr(contact, "phone"):
        phone = contact.phone or ""
    elif isinstance(contact, dict):
        phone = contact.get("phone", "") or ""

    # Fallback: full_name split
    if not first and not last:
        full = getattr(contact, "full_name", None) or (
            contact.get("full_name", "") if isinstance(contact, dict) else ""
        )
        if full:
            parts = str(full).strip().split(None, 1)
            first = parts[0] if parts else ""
            last = parts[1] if len(parts) > 1 else ""

    return {
        "first_name": first,
        "last_name": last,
        "email": email,
        "phone": phone,
    }


def _parse_form(html: str, base_url: str) -> dict[str, Any] | None:
    """Extract form action, method, and hidden fields from HTML. Returns None if no usable form."""
    # Look for form with grnhse (Greenhouse) or lever
    form_match = re.search(
        r'<form[^>]*(?:id=["\']grnhse_app["\']|class=["\'][^"\']*lever[^"\']*["\'])[^>]*>',
        html,
        re.I | re.DOTALL,
    )
    if not form_match:
        form_match = re.search(
            r'<form[^>]*action=["\'][^"\']*greenhouse[^"\']*["\'][^>]*>', html, re.I
        )
    if not form_match:
        form_match = re.search(
            r'<form[^>]*action=["\'][^"\']*lever[^"\']*["\'][^>]*>', html, re.I
        )
    if not form_match:
        return None

    form_start = form_match.start()
    form_end = html.find("</form>", form_start)
    if form_end == -1:
        return None
    form_html = html[form_start:form_end]

    action_match = re.search(r'action=["\']([^"\']*)["\']', form_html, re.I)
    action = action_match.group(1).strip() if action_match else base_url
    if action and not action.startswith("http"):
        action = urljoin(base_url, action)

    method_match = re.search(r'method=["\']([^"\']*)["\']', form_html, re.I)
    method = (method_match.group(1) or "post").lower()

    hidden: dict[str, str] = {}
    for inp in re.finditer(
        r'<input[^>]*type=["\']hidden["\'][^>]*>',
        form_html,
        re.I,
    ):
        name_m = re.search(r'name=["\']([^"\']+)["\']', inp.group(0), re.I)
        val_m = re.search(r'value=["\']([^"\']*)["\']', inp.group(0), re.I)
        if name_m:
            hidden[name_m.group(1)] = val_m.group(1) if val_m else ""

    return {"action": action, "method": method, "hidden": hidden}


def _check_submission_success(html: str, status_code: int) -> bool:
    """Check for specific confirmation elements in the response HTML."""
    if status_code in (200, 302):
        html_lower = html.lower()
        confirmation_indicators = [
            "application submitted",
            "thank you for applying",
            "thanks for applying",
            "application received",
            "successfully submitted",
            "we've received your application",
            "your application has been",
        ]
        for indicator in confirmation_indicators:
            if indicator in html_lower:
                return True
        error_indicators = [
            "error",
            "failed",
            "invalid",
            "required field",
            "please correct",
        ]
        for indicator in error_indicators:
            if indicator in html_lower:
                return False
    return False


async def _try_greenhouse(ctx: dict) -> bool:
    """Attempt HTTP form submission for Greenhouse. Returns True on success."""
    url = ctx.get("application_url", "")
    profile = ctx.get("profile") or {}
    resume_path = ctx.get("resume_path")
    fields = _get_profile_fields(profile)
    if not fields.get("email"):
        logger.debug("HTTP apply: no email in profile, skip")
        return False

    client = httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
        headers={"User-Agent": HTTP_UA},
    )
    try:
        resp = await client.get(url)
        resp.raise_for_status()
        html = resp.text

        parsed = _parse_form(html, url)
        if not parsed:
            logger.debug("HTTP apply Greenhouse: no form found (likely JS-rendered)")
            return False

        data: dict[str, str] = {}
        for k, v in parsed["hidden"].items():
            data[str(k)] = str(v) if v is not None else ""
        data["first_name"] = fields["first_name"] or "Applicant"
        data["last_name"] = fields["last_name"] or "User"
        data["email"] = fields["email"]
        if fields["phone"]:
            data["phone"] = fields["phone"]

        files: dict[str, tuple[str, IOBase, str]] = {}
        if resume_path:
            try:
                files["resume"] = (
                    "resume.pdf",
                    open(resume_path, "rb"),
                    "application/pdf",
                )
            except OSError:
                pass

        resp = await client.post(
            parsed["action"],
            data=data,
            files=files if files else None,
        )

        success = _check_submission_success(resp.text, resp.status_code)
        if success:
            logger.info("HTTP apply Greenhouse succeeded for %s", url)
        return success
    except Exception as e:
        logger.debug("HTTP apply Greenhouse failed: %s", e)
        return False
    finally:
        await client.aclose()
        for f in files.values():
            if len(f) > 2 and hasattr(f[1], "close"):
                f[1].close()


async def _try_lever(ctx: dict) -> bool:
    """Attempt HTTP form submission for Lever. Returns True on success."""
    url = ctx.get("application_url", "")
    profile = ctx.get("profile") or {}
    resume_path = ctx.get("resume_path")
    fields = _get_profile_fields(profile)
    if not fields.get("email"):
        return False

    client = httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
        headers={"User-Agent": HTTP_UA},
    )
    try:
        resp = await client.get(url)
        resp.raise_for_status()
        html = resp.text

        parsed = _parse_form(html, url)
        if not parsed:
            return False

        data: dict[str, str] = {}
        for k, v in parsed["hidden"].items():
            data[str(k)] = str(v) if v is not None else ""
        data["name"] = (
            f"{fields['first_name']} {fields['last_name']}".strip() or "Applicant"
        )
        data["email"] = fields["email"]
        if fields["phone"]:
            data["phone"] = fields["phone"]

        files: dict[str, tuple[str, IOBase, str]] = {}
        if resume_path:
            try:
                files["resume"] = (
                    "resume.pdf",
                    open(resume_path, "rb"),
                    "application/pdf",
                )
            except OSError:
                pass

        resp = await client.post(
            parsed["action"],
            data=data,
            files=files if files else None,
        )

        success = _check_submission_success(resp.text, resp.status_code)
        if success:
            logger.info("HTTP apply Lever succeeded for %s", url)
        return success
    except Exception as e:
        logger.debug("HTTP apply Lever failed: %s", e)
        return False
    finally:
        await client.aclose()
        for f in files.values():
            if len(f) > 2 and hasattr(f[1], "close"):
                f[1].close()


async def try_http_apply_first(ctx: dict) -> bool:
    """Try HTTP form submission for Greenhouse/Lever before Playwright.

    Returns True if application was submitted successfully, False to fall back to browser.
    """
    url = ctx.get("application_url", "")
    if not url:
        return False

    result = detect_ats_platform(url)
    if result.platform == ATSPlatform.GREENHOUSE:
        return await _try_greenhouse(ctx)
    if result.platform == ATSPlatform.LEVER:
        return await _try_lever(ctx)
    return False
