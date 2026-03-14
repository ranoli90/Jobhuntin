"""Part 2: Hardened Agent and DOM Handling.

Production-grade single-worker module that:
  - Polls Supabase Postgres for QUEUED applications (and resumable REQUIRES_INPUT)
  - Claims tasks atomically with SELECT … FOR UPDATE SKIP LOCKED
  - Drives a headless Playwright browser through multi-step forms
  - Uses a canonical profile schema for stable LLM prompts
  - Emits application_events at every state transition
  - Implements hold / resume / retry / failure policies
"""

from __future__ import annotations

import asyncio
import json
import os
import random
import tempfile
import time
from typing import Any, Callable, Optional, TypedDict

import asyncpg
from playwright.async_api import BrowserContext, Page, async_playwright

from packages.backend.blueprints.registry import get_blueprint, load_default_blueprints
from packages.backend.domain.ats_handlers import (
    ATSPlatform,
    detect_ats_platform,
    get_handler,
)
from packages.backend.domain.ats_handlers import (
    detect_captcha as detect_captcha_ats,
)
from packages.backend.domain.http_apply import try_http_apply_first

# Import job board handlers
try:
    from packages.backend.domain.job_board_handlers import (
        JobBoardPlatform,
        detect_job_board_platform,
        get_job_board_handler,
    )
    JOB_BOARD_HANDLERS_AVAILABLE = True
except ImportError:
    JOB_BOARD_HANDLERS_AVAILABLE = False

# CAPTCHA types we cannot solve; escalate to user immediately
UNSUPPORTED_CAPTCHA_TYPES = frozenset(
    {"cloudflare", "turnstile", "arkose", "friendly_captcha"}
)
from packages.backend.domain.email_communications import get_email_communication_manager
from packages.backend.domain.enhanced_notifications import (
    get_enhanced_notification_manager,
)
from packages.backend.domain.evaluations import record_system_evaluation
from packages.backend.domain.experiments import get_variant_for_tenant
from packages.backend.domain.models import CanonicalProfile, normalize_profile
from packages.backend.domain.notifications import (
    notify_application_submitted,
    notify_hold_questions,
)
from packages.backend.domain.repositories import (
    ApplicationRepo,
    CoverLetterRepo,
    EventRepo,
    InputRepo,
    JobRepo,
    ProfileRepo,
    db_transaction,
)
from packages.backend.domain.resume import download_from_supabase_storage
from packages.backend.llm.client import LLMClient
from packages.backend.llm.contracts import (
    CoverLetterResponse_V1,
    DomMappingResponse_V1,
    build_cover_letter_prompt,
    build_dom_mapping_prompt,
)
from packages.backend.llm.prompt_registry import get_prompt
from shared.config import get_settings
from shared.logging_config import LogContext, get_logger, setup_logging
from shared.metrics import RateLimiter, incr, observe
from shared.telemetry import setup_telemetry

from .concurrent_tracker import get_concurrent_tracker
from .oauth_handler import OAuthHandler


class CaptchaRequiredError(RuntimeError):
    """CAPTCHA detected but not solved; escalate to REQUIRES_INPUT for user action."""


# ---------------------------------------------------------------------------
# Configuration (loaded from shared.config)
# ---------------------------------------------------------------------------
_settings = get_settings()

setup_logging(
    env=_settings.env.value,
    log_level=_settings.log_level,
    log_json=_settings.log_json,
)

logger = get_logger("sorce.agent")

_llm_client = LLMClient(_settings)

MAX_ATTEMPTS: int = _settings.max_attempts
MAX_FORM_STEPS: int = _settings.max_form_steps
PAGE_TIMEOUT_MS: int = _settings.page_timeout_ms

# ---------------------------------------------------------------------------
# Rate limiters (in-process guardrails)
# ---------------------------------------------------------------------------
_llm_limiter = RateLimiter(
    max_calls=_settings.llm_rate_limit_per_minute, window_seconds=60.0
)
_processing_limiter = RateLimiter(
    max_calls=_settings.max_applications_per_minute,
    window_seconds=60.0,
)


# CanonicalProfile, FormField, LLMMapping, normalize_profile imported from backend.domain


# ---------------------------------------------------------------------------
# Local TypedDict aliases for Playwright JS interop (kept for JS evaluate)
# ---------------------------------------------------------------------------


class FormFieldOption(TypedDict):
    value: str
    text: str


class FormField(TypedDict):
    selector: str
    label: str
    type: str  # text | email | tel | select | textarea | checkbox | radio | file | …
    required: bool
    step_index: int
    options: list[FormFieldOption] | None


# record_event imported from backend.domain.repositories

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------


async def create_db_pool():
    """Create database connection pool."""
    settings = get_settings()
    import ssl

    from shared.db import resolve_dsn_ipv4
    dsn = resolve_dsn_ipv4(settings.database_url)

    # Use SSL but don't verify certificate for self-signed certs on Render
    # The connection is still encrypted, just not verified against a CA
    ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    return await asyncpg.create_pool(
        dsn,
        min_size=settings.db_pool_min,
        max_size=settings.db_pool_max,
        statement_cache_size=0,
        ssl=ctx,
        timeout=30.0,
        command_timeout=60.0,
    )


async def claim_task(pool: asyncpg.Pool) -> dict | None:
    """Atomically claim the next task, ordered by priority_score DESC (ENTERPRISE > TEAM > PRO > FREE)."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM public.claim_next_prioritized($1)",
            MAX_ATTEMPTS,
        )
        return dict(row) if row else None


async def fetch_job(pool: asyncpg.Pool, job_id: str) -> dict:
    async with pool.acquire() as conn:
        row = await JobRepo.get_by_id(conn, job_id)
        if row is None:
            raise ValueError(f"Job {job_id} not found")
        return row


async def fetch_profile(pool: asyncpg.Pool, user_id: str) -> dict:
    async with pool.acquire() as conn:
        data = await ProfileRepo.get_profile_data(conn, user_id)
        if data is None:
            raise ValueError(f"Profile for user {user_id} not found")
        return data


async def fetch_answered_inputs(pool: asyncpg.Pool, application_id: str) -> list[dict]:
    async with pool.acquire() as conn:
        return await InputRepo.get_answered(conn, application_id)


async def update_application_status(
    conn: asyncpg.Connection,
    application_id: str,
    status: str,
    error_message: str | None = None,
) -> None:
    await ApplicationRepo.update_status(
        conn, application_id, status, error_message=error_message
    )


# ---------------------------------------------------------------------------
# Playwright: multi-step DOM extraction
# ---------------------------------------------------------------------------

EXTRACT_FORM_FIELDS_JS = """
() => {
    const fields = [];
    const form = document.querySelector('form') || document.body;

    function getLabel(el) {
        if (el.id) {
            const lbl = document.querySelector('label[for="' + el.id + '"]');
            if (lbl) return lbl.innerText.trim();
        }
        const parent = el.closest('label');
        if (parent) {
            const clone = parent.cloneNode(true);
            clone.querySelectorAll('input,select,textarea').forEach(c => c.remove());
            return clone.innerText.trim();
        }
        return el.getAttribute('aria-label')
            || el.getAttribute('placeholder')
            || el.getAttribute('name')
            || '';
    }

    function selectorFor(el) {
        // MEDIUM: Prefer stable selectors (id, name) over nth-of-type
        if (el.id) return '#' + el.id;
        if (el.name) return el.tagName.toLowerCase() + '[name="' + el.name + '"]';
        // Try data attributes as fallback
        if (el.getAttribute('data-field-id')) return el.tagName.toLowerCase() + '[data-field-id="' + el.getAttribute('data-field-id') + '"]';
        if (el.getAttribute('data-testid')) return el.tagName.toLowerCase() + '[data-testid="' + el.getAttribute('data-testid') + '"]';
        // Try label association
        if (el.id && document.querySelector('label[for="' + el.id + '"]')) {
            const label = document.querySelector('label[for="' + el.id + '"]');
            if (label && label.textContent) {
                // Use label text as additional context (not in selector but useful for matching)
            }
        }
        // Last resort: nth-of-type (fragile, may break with DOM changes)
        // WARNING: This selector is fragile and may break if form structure changes
        const siblings = Array.from(form.querySelectorAll(el.tagName.toLowerCase()));
        const idx = siblings.indexOf(el);
        return el.tagName.toLowerCase() + ':nth-of-type(' + (idx + 1) + ')';
    }

    form.querySelectorAll('input, select, textarea').forEach(el => {
        const type = el.tagName.toLowerCase() === 'select' ? 'select'
                   : el.tagName.toLowerCase() === 'textarea' ? 'textarea'
                   : (el.getAttribute('type') || 'text');
        if (['hidden', 'submit', 'button', 'image', 'reset'].includes(type)) return;

        const entry = {
            selector: selectorFor(el),
            label: getLabel(el),
            type: type,
            required: el.required || el.getAttribute('aria-required') === 'true',
            options: null
        };

        if (el.tagName.toLowerCase() === 'select') {
            entry.options = Array.from(el.options).map(o => ({
                value: o.value,
                text: o.text.trim()
            })).filter(o => o.value !== '');
        }

        if (type === 'radio') {
            const name = el.getAttribute('name');
            if (name) {
                const radios = form.querySelectorAll('input[type="radio"][name="' + name + '"]');
                entry.options = Array.from(radios).map(r => ({
                    value: r.value,
                    text: (function(rel) {
                        const p = rel.closest('label');
                        if (p) {
                            const c = p.cloneNode(true);
                            c.querySelectorAll('input').forEach(x => x.remove());
                            return c.innerText.trim();
                        }
                        return rel.value;
                    })(r)
                }));
            }
        }

        fields.push(entry);
    });

    return fields;
}
"""


async def extract_form_fields_single_step(
    page: Page, step_index: int
) -> list[FormField]:
    """Extract all visible form fields on the current step."""
    raw: list[dict] = await page.evaluate(EXTRACT_FORM_FIELDS_JS)
    fields: list[FormField] = []
    seen_radio_names: set[str] = set()
    for f in raw:
        # Deduplicate radio groups by name
        if f["type"] == "radio":
            name = f["selector"]
            if name in seen_radio_names:
                continue
            seen_radio_names.add(name)

        fields.append(
            FormField(
                selector=f["selector"],
                label=f["label"],
                type=f["type"],
                required=f["required"],
                step_index=step_index,
                options=f.get("options"),
            )
        )
    return fields


async def detect_next_button(page: Page) -> bool:
    """Check if there's a 'Next' / 'Continue' button (not a Submit)."""
    next_selectors = [
        'button:has-text("Next")',
        'button:has-text("Continue")',
        'button:has-text("Continue to")',
        'button:has-text("Next Step")',
        'button:has-text("Proceed")',
        'button:has-text("Forward")',
        'button:has-text("Advance")',
        'button:has-text("Next Page")',
        'button:has-text("Continue Application")',
        'button:has-text("Next Section")',
        'button:has-text("Step")',
        'input[type="button"][value*="Next" i]',
        'input[type="button"][value*="Continue" i]',
        'input[type="submit"][value*="Next" i]',
        'input[type="submit"][value*="Continue" i]',
        'button[aria-label*="Next" i]',
        'button[aria-label*="Continue" i]',
        'button[class*="next"]',
        'button[class*="continue"]',
        'a[role="button"]:has-text("Next")',
        'a[role="button"]:has-text("Continue")',
        ".next-button",
        ".continue-button",
        ".btn-next",
        ".btn-continue",
    ]
    for sel in next_selectors:
        btn = page.locator(sel).first
        if await btn.count() > 0 and await btn.is_visible():
            return True
    return False


async def click_next_button(
    page: Page, custom_next_selectors: list[str] | None = None
) -> bool:
    """Click the Next/Continue button and wait for the step transition."""
    next_selectors = (custom_next_selectors or []) + [
        'button:has-text("Next")',
        'button:has-text("Continue")',
        'button:has-text("Continue to")',
        'button:has-text("Next Step")',
        'button:has-text("Proceed")',
        'button:has-text("Forward")',
        'button:has-text("Advance")',
        'button:has-text("Next Page")',
        'button:has-text("Continue Application")',
        'button:has-text("Next Section")',
        'button:has-text("Step")',
        'input[type="button"][value*="Next" i]',
        'input[type="button"][value*="Continue" i]',
        'input[type="submit"][value*="Next" i]',
        'input[type="submit"][value*="Continue" i]',
        'button[aria-label*="Next" i]',
        'button[aria-label*="Continue" i]',
        'button[class*="next"]',
        'button[class*="continue"]',
        'a[role="button"]:has-text("Next")',
        'a[role="button"]:has-text("Continue")',
        ".next-button",
        ".continue-button",
        ".btn-next",
        ".btn-continue",
    ]
    for sel in next_selectors:
        btn = page.locator(sel).first
        if await btn.count() > 0 and await btn.is_visible():
            try:
                await btn.click()
                await page.wait_for_timeout(1000)
                return True
            except Exception as e:
                logger.debug("Failed to click next button %s: %s", sel, e)
                continue
    return False


async def extract_all_form_fields(page: Page) -> list[FormField]:
    """Walk through multi-step forms, collecting fields from each step."""
    all_fields: list[FormField] = []

    for step in range(MAX_FORM_STEPS):
        step_fields = await extract_form_fields_single_step(page, step)
        all_fields.extend(step_fields)

        has_next = await detect_next_button(page)
        if not has_next:
            break
        # Only advance if we're collecting; don't click on the last step
        if step < MAX_FORM_STEPS - 1:
            advanced = await click_next_button(page)
            if not advanced:
                break

    return all_fields


# ---------------------------------------------------------------------------
# LLM: DOM-to-Profile mapping
# ---------------------------------------------------------------------------


MAP_PROMPT_TEMPLATE = """You are a job-application autofill assistant. Your goal is to fill a web form using the user's profile data.

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


def build_mapping_prompt(
    profile: CanonicalProfile,
    form_fields: list[FormField],
    answered_inputs: list[dict] | None = None,
    prompt_version: str | None = None,
) -> str:
    profile_dict = profile.model_dump() if hasattr(profile, "model_dump") else profile
    # NOTE: Do NOT strip PII here. The agent's job is to fill forms with the
    # user's contact info (email, phone, address). The LLM needs the full
    # profile to produce correct field→value mappings. PII stripping is only
    # appropriate for advisory AI endpoints (suggestions, matching, cover letters)
    # where the output doesn't require contact details.
    # If a specific prompt version is requested, use the prompt registry
    if prompt_version:
        template = get_prompt("dom_mapping", prompt_version)
        import json as _json

        return template.format(
            profile_json=_json.dumps(profile_dict, indent=2),
            answered_json=_json.dumps(answered_inputs or [], indent=2),
            fields_json=_json.dumps(form_fields, indent=2, default=str),
        )
    return build_dom_mapping_prompt(profile_dict, form_fields, answered_inputs)


async def _llm_call_with_retry(call_fn, max_retries: int = 3):
    """Retry LLM call with exponential backoff for transient failures."""
    last_exc = None
    for attempt in range(max_retries):
        try:
            return await call_fn()
        except Exception as e:
            last_exc = e
            if attempt < max_retries - 1:
                delay = 2**attempt + random.uniform(0, 1)
                logger.warning(
                    "LLM call failed (attempt %d/%d), retrying in %.1fs: %s",
                    attempt + 1,
                    max_retries,
                    delay,
                    e,
                )
                await asyncio.sleep(delay)
    raise last_exc


async def map_fields_via_llm(
    profile: CanonicalProfile,
    form_fields: list[FormField],
    answered_inputs: list[dict] | None = None,
    prompt_version: str | None = None,
) -> dict:
    """Use the LLM client with the versioned DOM mapping contract."""
    prompt = build_mapping_prompt(profile, form_fields, answered_inputs, prompt_version)

    async def _call():
        return await _llm_client.call(
            prompt=prompt,
            response_format=DomMappingResponse_V1,
        )

    result = await _llm_call_with_retry(_call)
    return {
        "field_values": result.field_values,
        "unresolved_required_fields": [
            {"selector": u.selector, "question": u.question}
            for u in result.unresolved_required_fields
        ],
    }


# ---------------------------------------------------------------------------
# Playwright: form filling (handles all input types)
# ---------------------------------------------------------------------------


async def fill_form_from_mapping(
    page: Page,
    field_values: dict[str, str],
    form_fields: list[FormField],
    resume_path: str | None = None,
    ctx: dict | None = None,
    get_portfolio_path: Callable[[dict], Any] | None = None,
    get_document_path: Callable[[dict, str], Any] | None = None,
    behavior_simulator: Any | None = None,
) -> None:
    """Fill each field using selector → value from the LLM mapping.
    When behavior_simulator (HumanBehaviorSimulator) is provided, uses human-like
    typing for text/textarea/email/tel to reduce bot detection."""
    field_lookup: dict[str, FormField] = {f["selector"]: f for f in form_fields}

    for selector, value in field_values.items():
        ff = field_lookup.get(selector)
        field_type = ff["type"] if ff else "text"

        try:
            # MEDIUM: Wait for field availability and check visibility
            try:
                # Wait for selector to be available
                await page.wait_for_selector(selector, state="attached", timeout=10000)
                el = page.locator(selector).first
                # Wait for field to be visible
                await el.wait_for(state="visible", timeout=5000)

                # Check if field is enabled
                if not await el.is_enabled():
                    logger.warning("Field %s is disabled, skipping", selector)
                    incr(
                        "agent.field_visibility.disabled",
                        tags={"selector": selector[:50]},
                    )
                    continue
            except Exception as wait_error:
                logger.warning(
                    "Field %s not found or not visible, skipping: %s",
                    selector,
                    wait_error,
                )
                incr("agent.field_visibility.timeout", tags={"selector": selector[:50]})
                continue

            step_idx = ff["step_index"] if ff else "?"

            if field_type == "select":
                await _fill_select(el, value)
            elif field_type == "radio":
                await _fill_radio(page, selector, el, value)
            elif field_type == "checkbox":
                await _fill_checkbox(el, value)
            elif field_type == "textarea":
                if behavior_simulator:
                    result = await behavior_simulator.type_humanlike(
                        page, selector, value or ""
                    )
                    if not result.success:
                        logger.warning(
                            "Humanlike textarea fill failed for %s: %s",
                            selector,
                            result.error,
                        )
                else:
                    await el.fill(value)
            elif field_type == "file":
                # LOW: Handle different file types (resume, portfolio, documents)
                file_path = None
                value_lower = (value or "").lower()

                if "resume" in value_lower or value_lower.endswith(".pdf"):
                    file_path = resume_path
                elif "portfolio" in value_lower and ctx and get_portfolio_path:
                    file_path = await get_portfolio_path(ctx)
                elif ctx and get_document_path:
                    doc_type_hint = (
                        value_lower.split()[0] if value_lower else "document"
                    )
                    file_path = await get_document_path(ctx, doc_type_hint)
                else:
                    file_path = None

                if file_path and os.path.exists(file_path):
                    await el.set_input_files(file_path)
                    logger.info("Uploaded file: %s for field %s", file_path, selector)
                else:
                    logger.warning(
                        "File upload skipped: no file path available for %s (value: %s)",
                        selector,
                        value,
                    )
            else:
                if behavior_simulator and field_type in (
                    "text",
                    "email",
                    "tel",
                    "password",
                ):
                    result = await behavior_simulator.type_humanlike(
                        page, selector, value or ""
                    )
                    if not result.success:
                        logger.warning(
                            "Humanlike fill failed for %s: %s",
                            selector,
                            result.error,
                        )
                        await el.fill(value)
                else:
                    await el.fill(value)

            logger.info("Filled [step:%s] %s = %s", step_idx, selector, value[:60])

            # HIGH: Validate field was actually filled after attempting
            try:
                # Wait a brief moment for value to be set
                await page.wait_for_timeout(100)

                # Verify the field has the expected value
                actual_value = await el.input_value() if field_type != "file" else None
                if actual_value is not None:
                    # For text fields, check if value matches (allowing for formatting differences)
                    if field_type in ["text", "textarea", "email", "tel"]:
                        if (
                            value.lower().strip() not in actual_value.lower().strip()
                            and actual_value.lower().strip()
                            not in value.lower().strip()
                        ):
                            logger.warning(
                                "Field value mismatch: expected '%s', got '%s' for selector %s",
                                value[:50],
                                actual_value[:50],
                                selector,
                            )
                            incr(
                                "agent.field_validation.mismatch",
                                tags={"field_type": field_type},
                            )
                    # For select fields, verify option was selected
                    elif field_type == "select":
                        selected_text = await el.evaluate(
                            "el => el.options[el.selectedIndex]?.text || ''"
                        )
                        if (
                            value.lower() not in selected_text.lower()
                            and selected_text.lower() not in value.lower()
                        ):
                            logger.warning(
                                "Select value mismatch: expected '%s', got '%s' for selector %s",
                                value,
                                selected_text,
                                selector,
                            )
                            incr(
                                "agent.field_validation.mismatch",
                                tags={"field_type": "select"},
                            )
            except Exception as validation_error:
                logger.debug(
                    "Field validation check failed (non-critical): %s", validation_error
                )
                # Don't fail the entire fill operation if validation check fails

        except Exception as exc:
            logger.warning("Could not fill %s: %s", selector, exc)
            incr(
                "agent.field_fill.failed",
                tags={"field_type": field_type, "error": type(exc).__name__},
            )


async def _fill_select(el: Any, value: str) -> None:
    # Try by value first, fall back to label
    try:
        await el.select_option(value=value)
    except Exception as e:
        logger.debug("Select by value failed, trying by label: %s", e)
        await el.select_option(label=value)


async def _fill_radio(page: Page, selector: str, el: Any, value: str) -> None:
    """Click radio with matching value, handling quoted values properly."""
    try:
        # Try exact match first (handles quoted values)
        radio = page.locator(f'{selector}[value="{value}"]').first
        if await radio.count() > 0:
            await radio.check()
            return
    except Exception as e:
        # Fallback: try with escaped quotes for complex values
        logger.debug("Radio exact match failed, trying escaped quotes: %s", e)
        escaped_value = value.replace('"', '\\"')
        radio = page.locator(f'{selector}[value="{escaped_value}"]').first
        if await radio.count() > 0:
            await radio.check()
            return

    # Final fallback: click the element directly
    await el.check()


async def _fill_checkbox(el: Any, value: str) -> None:
    should_check = value.lower() in ("true", "yes", "1", "on")
    if should_check:
        await el.check()
    else:
        await el.uncheck()


SUCCESS_INDICATORS = (
    "thank you",
    "application received",
    "submitted",
    "success",
    "confirmation",
    "application complete",
    "we've received",
    "thank you for applying",
    "your application has been",
)
ERROR_INDICATORS = (
    "please correct",
    "invalid",
    "required field",
    "error submitting",
    "submission failed",
)


async def _verify_submit_success(page: Page, strict: bool = False) -> bool:
    """Check page content for success/error indicators after submit.

    strict: when True (no navigation occurred), require success indicators.
    When False (navigation completed), require no error indicators.
    """
    try:
        content = (await page.content()).lower()
        import re

        validation_patterns = [
            r'<div[^>]*class="[^"]*error[^"]*"[^>]*>(.*?)</div>',
            r'<span[^>]*class="[^"]*error[^"]*"[^>]*>(.*?)</span>',
            r'<p[^>]*class="[^"]*error[^"]*"[^>]*>(.*?)</p>',
            r'<div[^>]*class="[^"]*validation[^"]*"[^>]*>(.*?)</div>',
            r'<form[^>]*class="[^"]*error[^"]*"[^>]*>(.*?)</form>',
        ]
        validation_content = ""
        for pattern in validation_patterns:
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            validation_content += " ".join(matches)

        for ind in ERROR_INDICATORS:
            if ind in validation_content:
                logger.warning("Error indicator in validation wrapper: %r", ind)
                return False
        for ind in SUCCESS_INDICATORS:
            if ind in content:
                return True
        if strict:
            logger.warning(
                "Submit click completed but no success indicator found; treating as uncertain"
            )
            return False
        return True
    except Exception as e:
        logger.debug("Could not verify submit success: %s", e)
        return not strict


async def submit_form(page: Page, selectors: list[str] | None = None) -> bool:
    """Click the submit button and wait for navigation or network idle.

    HIGH: Implements retry logic for transient submission failures.
    Verifies success indicators on post-submit page.
    """
    submit_selectors = selectors or [
        'button[type="submit"]',
        'input[type="submit"]',
        'button:has-text("Submit")',
        'button:has-text("Apply")',
        'button:has-text("Send Application")',
        'button:has-text("Send")',
    ]

    max_retries = 2
    base_delay = 1.0
    last_error = None

    for attempt in range(max_retries):
        for sel in submit_selectors:
            btn = page.locator(sel).first
            if await btn.count() > 0:
                try:
                    async with page.expect_navigation(
                        wait_until="networkidle", timeout=30_000
                    ):
                        await btn.click()
                    return await _verify_submit_success(page)
                except Exception as e:
                    last_error = e
                    # Check if error is retryable
                    is_retryable = (
                        isinstance(e, (TimeoutError, ConnectionError))
                        or "timeout" in str(e).lower()
                        or "network" in str(e).lower()
                    )

                    if is_retryable and attempt < max_retries - 1:
                        # HIGH: Exponential backoff for retryable errors
                        delay = base_delay * (2**attempt) + (random.random() * 0.3)
                        logger.warning(
                            "Form submission failed (attempt %d/%d), retrying in %.2fs: %s",
                            attempt + 1,
                            max_retries,
                            delay,
                            e,
                        )
                        await asyncio.sleep(delay)
                        break  # Retry with same selector
                    else:
                        # F16: Don't assume success when navigation times out - check for success indicators
                        logger.debug(
                            "Form submission didn't trigger navigation, falling back to click: %s",
                            e,
                        )
                        try:
                            await btn.click()
                            await page.wait_for_timeout(3000)
                            return await _verify_submit_success(page, strict=True)
                            logger.warning(
                                "Submit click completed but no success indicator found; treating as uncertain"
                            )
                            return False
                        except Exception as fallback_error:
                            logger.debug(
                                "Fallback click also failed: %s", fallback_error
                            )
                            continue  # Try next selector
        # If all selectors failed and we have retries left, wait and retry
        if attempt < max_retries - 1 and last_error:
            delay = base_delay * (2**attempt)
            logger.warning("All submit selectors failed, retrying in %.2fs", delay)
            await asyncio.sleep(delay)

    return False


# ---------------------------------------------------------------------------
# FormAgent – blueprint-parameterized core engine
# ---------------------------------------------------------------------------


class FormAgent:
    """Generic form-filling agent engine.

    The core loop (claim → navigate → extract → map → fill → submit) is
    domain-agnostic. Vertical-specific behavior (prompts, submit selectors,
    completion status) is delegated to an AgentBlueprint instance resolved
    from the task's blueprint_key.
    """

    def __init__(
        self,
        db_pool: asyncpg.Pool,
        playwright_context_factory,
    ):
        self.pool = db_pool
        self._context_factory = playwright_context_factory
        self.poll_interval = get_settings().poll_interval_seconds
        self.wake_event = asyncio.Event()
        self.oauth_handler: Optional[OAuthHandler] = None

    # -- public entry points -----------------------------------------------

    async def run_forever(self) -> None:
        """Infinite polling loop with event-driven wake-up."""
        logger.info(
            "Agent started – event-driven + polling every %ds", self.poll_interval
        )

        # Start the listener task in background
        asyncio.create_task(self._listen_loop())

        while True:
            # Clear event before running to ensure we don't miss notifications
            # that happen *during* processing (though handling that safely is tricky,
            # clearing here implies we demand a new notification for the next run
            # unless we find more work immediately).
            # Actually, standard pattern: check work. If work found, repeat.
            # If no work, wait for event.

            processed = await self.run_once()

            if processed:
                # If we processed something, there might be more. Check immediately.
                # But yield to other tasks slightly to avoid starvation if massive backlog.
                await asyncio.sleep(0.01)
                continue

            # No work found. Wait for notification or timeout.
            self.wake_event.clear()
            try:
                await asyncio.wait_for(
                    self.wake_event.wait(), timeout=self.poll_interval
                )
                # logger.debug("Woke up by event")
            except TimeoutError:
                # logger.debug("Woke up by timeout")
                pass

    async def _listen_loop(self) -> None:
        """Dedicated connection for LISTEN/NOTIFY with exponential backoff.

        Uses asyncpg.connect() (not pool.acquire()) so we do not hold a pool
        connection indefinitely. Pool connections must be short-lived.
        """
        import ssl

        settings = get_settings()
        retry_count = 0
        max_retry_delay = 60.0
        # Use proper SSL verification - Render uses DigiCert signed certificates
        # Only disable in local development if needed
        ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
        # ctx.check_hostname = False  # REMOVED - security risk
        # ctx.verify_mode = ssl.CERT_NONE  # REMOVED - security risk

        while True:
            conn = None
            try:
                from shared.db import resolve_dsn_ipv4
                dsn = resolve_dsn_ipv4(settings.database_url)
                conn = await asyncpg.connect(
                    dsn,
                    ssl=ctx,
                    command_timeout=0,  # No timeout for LISTEN (long-lived)
                )
                await conn.add_listener(
                    "job_queue", lambda *args: self.wake_event.set()
                )
                logger.info("Listening for 'job_queue' notifications...")
                retry_count = 0

                while True:
                    await asyncio.sleep(60)
                    try:
                        await conn.execute("SELECT 1")
                    except Exception:
                        break
            except Exception as e:
                retry_count += 1
                delay = min(2 ** (retry_count - 1), max_retry_delay)
                jitter = delay * 0.1 * random.random()
                delay += jitter

                logger.error(
                    f"Listener connection failed (attempt {retry_count}): {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)
            finally:
                if conn is not None:
                    try:
                        await conn.close()
                    except Exception:
                        pass

    async def run_once(self) -> bool:
        """Claim and process a single task. Returns True if work was done."""
        # Guardrail: emergency stop
        if not _settings.agent_enabled:
            logger.warning("Agent is disabled (AGENT_ENABLED=false), skipping")
            incr("agent.disabled_skip")
            return False

        # Guardrail: processing rate limit
        if not await _processing_limiter.acquire():
            logger.warning(
                "Processing rate limit reached (%d/min), backing off",
                _settings.max_applications_per_minute,
            )
            incr("agent.rate_limited", {"limiter": "processing"})
            return False

        # Claim the task first
        task = await claim_task(self.pool)
        if task is None:
            return False

        # Check concurrent usage limits AFTER claiming but before processing
        # This ensures we don't lose the task to another worker during the check
        task_tenant_id = str(task["tenant_id"]) if task.get("tenant_id") else None
        concurrent_tracker = get_concurrent_tracker()
        can_start = await concurrent_tracker.can_start_task(tenant_id=task_tenant_id)
        if not can_start:
            logger.warning(
                "Concurrent usage limit reached after claim, releasing task %s for tenant %s",
                task["id"],
                task_tenant_id or "none",
            )
            incr(
                "agent.concurrent_limited",
                {"tenant_id": task_tenant_id or "none"},
            )
            async with self.pool.acquire() as conn:
                await conn.execute(
                    "UPDATE public.applications SET status = 'QUEUED' WHERE id = $1",
                    task["id"],
                )
            return False

        app_id = str(task["id"])
        tenant_id = str(task["tenant_id"]) if task.get("tenant_id") else None
        blueprint_key = task.get("blueprint_key", _settings.default_blueprint_key)

        # Mark task as started in concurrent tracker (double-check limits here too)
        concurrent_tracker = get_concurrent_tracker()
        started = await concurrent_tracker.start_task(app_id, tenant_id)
        if not started:
            # Limits changed between peek and claim - release the task back to QUEUED
            logger.warning(
                "Concurrent limit reached after claim, releasing task %s", app_id
            )
            async with self.pool.acquire() as conn:
                await conn.execute(
                    "UPDATE public.applications SET status = 'QUEUED' WHERE id = $1",
                    app_id,
                )
            incr(
                "agent.concurrent_limited_after_claim",
                {"tenant_id": tenant_id or "none"},
            )
            return False

        LogContext.set(
            application_id=app_id,
            user_id=str(task["user_id"]),
            job_id=str(task["job_id"]),
            tenant_id=tenant_id,
        )
        incr(
            "agent.tasks_claimed",
            tags={"tenant_id": tenant_id or "none", "blueprint": blueprint_key},
        )
        logger.info(
            "Claimed task %s (attempt %d, blueprint=%s)",
            app_id,
            task["attempt_count"],
            blueprint_key,
        )

        # HTTP-first: try form submission for Greenhouse/Lever before Playwright (Section 3.3 High)
        ctx = await self._build_context(task)
        if _settings.apply_strategy == "auto":
            if await try_http_apply_first(ctx):
                await self._emit_started(ctx)
                await self._handle_success(task, ctx, None)
                await concurrent_tracker.end_task(app_id)
                LogContext.clear()
                return True

        context: BrowserContext = await self._context_factory()
        self.oauth_handler = OAuthHandler(context)
        page = await context.new_page()

        # Wire AntiDetection: reduce bot fingerprinting before any navigation
        try:
            from packages.backend.domain.execution_engine import AntiDetection

            await AntiDetection.inject_stealth(page)
        except Exception as e:
            logger.warning("AntiDetection.inject_stealth failed (non-blocking): %s", e)

        try:
            await self._process_task(page, task)
        except CaptchaRequiredError:
            ctx = await self._build_context(task)
            await self._enter_hold(
                ctx["app_id"],
                [
                    {
                        "selector": "captcha",
                        "question": "Human verification (CAPTCHA) required. Please complete the CAPTCHA on the application page and retry.",
                    }
                ],
                [],
                tenant_id=ctx.get("tenant_id"),
            )
        except Exception as exc:
            await self._handle_failure(task, exc, page)
        finally:
            await concurrent_tracker.end_task(app_id)
            await context.close()
            LogContext.clear()

        return True

    # -- core processing ---------------------------------------------------

    async def _process_task(self, page: Page, task: dict) -> None:
        ctx = await self._build_context(task)
        ctx.setdefault("_temp_paths", [])  # Track temp files for cleanup
        try:
            await self._emit_started(ctx)

            # Navigate & Extract
            await self._navigate_to_app(page, ctx)
            # ATS detection: run pre_fill_hook (e.g. Lever "Apply" click) before extract
            await self._detect_and_prepare_ats(page, ctx)
            form_fields = await self._extract_fields(page)

            # LLM Mapping
            mapping = await self._map_fields(form_fields, ctx)

            # Hold Logic
            if mapping["unresolved_required_fields"]:
                await self._enter_hold(
                    ctx["app_id"],
                    mapping["unresolved_required_fields"],
                    form_fields,
                    tenant_id=ctx["tenant_id"],
                )
                return

            # Fill & Submit
            await self._fill_form(page, mapping, form_fields, ctx)
            await self._submit_application(page, ctx)

            # Success
            await self._handle_success(task, ctx, page)
        finally:
            # Clean up temporary files to prevent resource leaks
            import os

            resume_path = ctx.get("resume_path")
            if resume_path and os.path.exists(resume_path):
                try:
                    os.unlink(resume_path)
                    logger.debug("Cleaned up resume temp file: %s", resume_path)
                except OSError:
                    pass

            for path in ctx.get("_temp_paths", []):
                if (
                    path
                    and os.path.exists(path)
                    and path.startswith(tempfile.gettempdir())
                ):
                    try:
                        os.unlink(path)
                        logger.debug("Cleaned up temp file: %s", path)
                    except OSError:
                        pass

    async def _build_context(self, task: dict) -> dict:
        """Construct the execution context from task payload and DB."""
        app_id = str(task["id"])
        user_id = str(task["user_id"])
        job_id = str(task["job_id"])
        tenant_id = str(task["tenant_id"]) if task.get("tenant_id") else None
        blueprint_key = task.get("blueprint_key", _settings.default_blueprint_key)
        attempt = task["attempt_count"]

        blueprint = get_blueprint(blueprint_key)
        job = await fetch_job(self.pool, job_id)
        raw_profile = await fetch_profile(self.pool, user_id)
        profile = normalize_profile(raw_profile)

        # Download resume for file upload fields
        resume_path = None
        resume_url = raw_profile.get("resume_url")
        if resume_url:
            try:
                resume_path = await download_from_supabase_storage(resume_url)
                logger.info("Resume downloaded for user %s: %s", user_id, resume_path)
            except Exception as exc:
                logger.warning(
                    "Failed to download resume for user %s: %s", user_id, exc
                )

        return {
            "app_id": app_id,
            "user_id": user_id,
            "job_id": job_id,
            "tenant_id": tenant_id,
            "blueprint_key": blueprint_key,
            "attempt": attempt,
            "blueprint": blueprint,
            "job": job,
            "profile": profile,
            "profile_data": raw_profile,  # Raw profile_data for portfolio_url, documents
            "application_url": job["application_url"],
            "resume_path": resume_path,
        }

    async def _emit_started(self, ctx: dict) -> None:
        async with self.pool.acquire() as conn:
            await EventRepo.emit(
                conn,
                ctx["app_id"],
                "STARTED_PROCESSING",
                {
                    "application_url": ctx["application_url"],
                    "attempt": ctx["attempt"],
                    "blueprint": ctx["blueprint_key"],
                },
                tenant_id=ctx["tenant_id"],
            )

    async def _navigate_to_app(self, page: Page, ctx: dict) -> None:
        """Navigate to the application URL.

        HIGH: Implements retry logic with exponential backoff for network failures.
        """
        max_retries = 3
        base_delay = 2.0

        for attempt in range(max_retries):
            try:
                await page.goto(
                    ctx["application_url"],
                    wait_until="networkidle",
                    timeout=PAGE_TIMEOUT_MS,
                )

                # Check for OAuth/SSO flow
                if await self.oauth_handler.detect_oauth_flow(page):
                    logger.info("OAuth/SSO flow detected, attempting authentication")
                    user_credentials = ctx.get("profile", {}).get("oauth_credentials")
                    if not user_credentials:
                        logger.warning(
                            "OAuth/SSO detected but no oauth_credentials in profile. "
                            "User should connect account in settings. Continuing with standard flow."
                        )
                    else:
                        oauth_success = await self.oauth_handler.handle_oauth_flow(
                            page, user_credentials
                        )
                        if not oauth_success:
                            logger.warning(
                                "OAuth authentication failed, continuing with standard flow"
                            )
                        else:
                            logger.info("OAuth authentication successful")

                # Success - return
                return

            except Exception as exc:
                # Check if error is retryable (network/timeout errors)
                is_retryable = (
                    isinstance(exc, (TimeoutError, ConnectionError))
                    or "timeout" in str(exc).lower()
                    or "network" in str(exc).lower()
                    or "connection" in str(exc).lower()
                )

                if is_retryable and attempt < max_retries - 1:
                    # HIGH: Exponential backoff with jitter
                    delay = base_delay * (2**attempt) + (random.random() * 0.5)
                    logger.warning(
                        "Page navigation failed (attempt %d/%d), retrying in %.2fs: %s",
                        attempt + 1,
                        max_retries,
                        delay,
                        exc,
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    # Non-retryable or retries exhausted
                    raise RuntimeError(
                        f"Page load failed for {ctx['application_url']} after {max_retries} attempts: {exc}"
                    ) from exc

    async def _detect_and_prepare_ats(self, page: Page, ctx: dict) -> None:
        """Detect ATS platform or job board, run pre_fill_hook, and store handler in ctx."""
        url = ctx.get("application_url", "")
        page_content: str | None = None
        try:
            page_content = await page.content()
        except Exception as e:
            logger.debug("Could not get page content for ATS detection: %s", e)
        
        # First try ATS detection
        result = detect_ats_platform(url, page_content)
        if result.platform != ATSPlatform.UNKNOWN and result.confidence >= 0.5:
            handler = get_handler(result.platform)
            if handler:
                ctx["ats_handler"] = handler
                ctx["job_board_handler"] = None
                logger.info(
                    "ATS detected: %s (confidence=%.2f), using %s",
                    result.platform.value,
                    result.confidence,
                    type(handler).__name__,
                )
                try:
                    await handler.pre_fill_hook(page, ctx)
                except Exception as e:
                    logger.warning("ATS pre_fill_hook failed: %s", e)
                return
        
        # If no ATS detected, try job board detection
        if JOB_BOARD_HANDLERS_AVAILABLE:
            job_board_result = detect_job_board_platform(url, page_content)
            if job_board_result.platform != JobBoardPlatform.UNKNOWN and job_board_result.confidence >= 0.5:
                handler = get_job_board_handler(job_board_result.platform)
                if handler:
                    ctx["job_board_handler"] = handler
                    ctx["ats_handler"] = None
                    logger.info(
                        "Job board detected: %s (confidence=%.2f), using %s",
                        job_board_result.platform.value,
                        job_board_result.confidence,
                        type(handler).__name__,
                    )
                    
                    # Handle login if required
                    if job_board_result.requires_login:
                        login_status = await handler.check_login_status(page)
                        if not login_status:
                            logger.info(f"{job_board_result.platform.value} requires login")
                            # Get user credentials from profile
                            user_credentials = ctx.get("profile", {}).get("job_board_credentials", {})
                            if user_credentials:
                                login_success = await handler.handle_login(page, user_credentials)
                                if not login_success:
                                    logger.warning(f"{job_board_result.platform.value} login failed")
                                    ctx["login_required"] = True
                                    return
                            else:
                                logger.warning(f"{job_board_result.platform.value} credentials not found")
                                ctx["login_required"] = True
                                return
                    
                    try:
                        await handler.pre_apply_hook(page, ctx)
                    except Exception as e:
                        logger.warning("Job board pre_apply_hook failed: %s", e)
                    return
        
        # No platform detected
        ctx["ats_handler"] = None
        ctx["job_board_handler"] = None

    async def _extract_fields(self, page: Page) -> list[FormField]:
        form_fields = await extract_all_form_fields(page)
        if not form_fields:
            raise RuntimeError("No form fields detected on the page")
        logger.info(
            "Extracted %d fields across %d step(s)",
            len(form_fields),
            max((f["step_index"] for f in form_fields), default=0) + 1,
        )
        return form_fields

    async def _map_fields(self, form_fields: list[FormField], ctx: dict) -> dict:
        # Fetch previously answered inputs
        answered_inputs = await fetch_answered_inputs(self.pool, ctx["app_id"])

        # Resolve prompt version
        prompt_version = None
        if _settings.prompt_version_override:
            prompt_version = _settings.prompt_version_override
            logger.info("Using prompt version override: %s", prompt_version)
        elif ctx["tenant_id"]:
            async with self.pool.acquire() as conn:
                variant = await get_variant_for_tenant(
                    conn, "dom_mapping_prompt", ctx["tenant_id"]
                )
            if variant:
                prompt_version = variant
                logger.info("Experiment assigned prompt version: %s", prompt_version)

        # LLM mapping
        if not await _llm_limiter.acquire():
            raise RuntimeError("LLM rate limit exceeded; will retry on next poll")

        t0 = time.monotonic()
        mapping = await map_fields_via_llm(
            ctx["profile"], form_fields, answered_inputs, prompt_version
        )
        llm_duration = time.monotonic() - t0
        observe("agent.llm_latency_seconds", llm_duration)
        logger.info(
            "LLM mapping completed in %.2fs (prompt=%s)",
            llm_duration,
            prompt_version or "default",
        )
        return mapping

    async def _fill_form(
        self, page: Page, mapping: dict, form_fields: list[FormField], ctx: dict
    ) -> None:
        # Re-navigate if needed (for multi-step consistency)
        await page.goto(
            ctx["application_url"], wait_until="networkidle", timeout=PAGE_TIMEOUT_MS
        )

        # CAPTCHA: detect unsupported types and escalate before form fill
        try:
            captcha_det = await detect_captcha_ats(page)
            if captcha_det.detected and captcha_det.captcha_type:
                ct = (captcha_det.captcha_type or "").lower()
                if ct in UNSUPPORTED_CAPTCHA_TYPES:
                    raise CaptchaRequiredError(
                        f"Unsupported CAPTCHA ({ct}) detected; human verification required"
                    )
        except CaptchaRequiredError:
            raise
        except Exception as e:
            logger.debug("CAPTCHA pre-check before fill: %s", e)

        max_step = max((f["step_index"] for f in form_fields), default=0)
        ats_handler = ctx.get("ats_handler")
        job_board_handler = ctx.get("job_board_handler")
        
        for step in range(max_step + 1):
            step_values = {
                sel: val
                for sel, val in mapping["field_values"].items()
                if any(
                    f["selector"] == sel and f["step_index"] == step
                    for f in form_fields
                )
            }
            step_fields = [f for f in form_fields if f["step_index"] == step]

            if step_values:
                from packages.backend.domain.execution_engine import (
                    HumanBehaviorConfig,
                    HumanBehaviorSimulator,
                )

                # Get skip selectors from handler (ATS or job board)
                skip_selectors = None
                if ats_handler:
                    skip_selectors = ats_handler.get_skip_selectors()
                elif job_board_handler:
                    skip_selectors = job_board_handler.get_skip_selectors()
                
                behavior_sim = HumanBehaviorSimulator(HumanBehaviorConfig())
                await fill_form_from_mapping(
                    page,
                    step_values,
                    step_fields,
                    resume_path=ctx.get("resume_path"),
                    ctx=ctx,
                    get_portfolio_path=self._get_portfolio_path,
                    get_document_path=self._get_document_path,
                    behavior_simulator=behavior_sim,
                    skip_selectors=skip_selectors,
                )

            if step < max_step:
                custom_next = None
                if ats_handler:
                    custom_next = ats_handler.get_custom_selectors().get("next")
                elif job_board_handler:
                    custom_next = job_board_handler.get_application_selectors().get("continue_button")
                    
                advanced = await click_next_button(page, custom_next)
                if not advanced:
                    logger.warning(
                        "Could not advance from step %d to %d", step, step + 1
                    )
                    break

    async def _handle_file_upload(
        self, el: Any, value: str, field_info: FormField, ctx: dict
    ) -> None:
        """Handle file upload with support for multiple document types."""
        try:
            # Get resume path from context
            resume_path = ctx.get("resume_path")

            # Determine file type based on field attributes and label
            file_type = self._determine_file_type(field_info, value)

            if file_type == "resume" and resume_path:
                await el.set_input_files(resume_path)
                logger.info("Uploaded resume to file input %s", field_info["selector"])
            elif file_type == "cover_letter":
                cover_letter_path = await self._get_cover_letter_path(ctx)
                if cover_letter_path:
                    await el.set_input_files(cover_letter_path)
                    logger.info(
                        "Uploaded cover letter to file input %s", field_info["selector"]
                    )
                else:
                    logger.warning(
                        "No cover letter available for upload %s",
                        field_info["selector"],
                    )
            elif file_type == "portfolio":
                portfolio_path = await self._get_portfolio_path(ctx)
                if portfolio_path:
                    await el.set_input_files(portfolio_path)
                    logger.info(
                        "Uploaded portfolio to file input %s", field_info["selector"]
                    )
                else:
                    logger.warning(
                        "No portfolio available for upload %s", field_info["selector"]
                    )
            elif file_type == "other":
                # Handle other document types
                doc_path = await self._get_document_path(ctx, value)
                if doc_path:
                    await el.set_input_files(doc_path)
                    logger.info(
                        "Uploaded document %s to file input %s",
                        file_type,
                        field_info["selector"],
                    )
                else:
                    logger.warning(
                        "No document available for %s upload %s",
                        file_type,
                        field_info["selector"],
                    )
            else:
                logger.warning(
                    "Unknown file type %s for upload %s",
                    file_type,
                    field_info["selector"],
                )

        except Exception as e:
            logger.error("File upload failed for %s: %s", field_info["selector"], e)

    def _determine_file_type(self, field_info: FormField, value: str) -> str:
        """Determine the type of file to upload based on field information."""
        label = field_info.get("label", "").lower()
        selector = field_info.get("selector", "").lower()

        # Check for resume indicators
        if any(
            keyword in label or keyword in selector
            for keyword in ["resume", "cv", "curriculum", "vitae"]
        ):
            return "resume"

        # Check for cover letter indicators
        if any(
            keyword in label or keyword in selector
            for keyword in ["cover letter", "cover", "letter", "motivation"]
        ):
            return "cover_letter"

        # Check for portfolio indicators
        if any(
            keyword in label or keyword in selector
            for keyword in ["portfolio", "work samples", "samples", "projects"]
        ):
            return "portfolio"

        # Check for other document types
        if any(
            keyword in label or keyword in selector
            for keyword in [
                "transcript",
                "certificate",
                "diploma",
                "degree",
                "reference",
                "recommendation",
                "writing sample",
            ]
        ):
            return "other"

        # Default to resume if no specific type detected
        return "resume"

    async def _get_cover_letter_path(self, ctx: dict) -> Optional[str]:
        """Get cover letter file path from context or generate one.
        Checks DB for existing cover letter; if none, generates via LLM, saves to DB, writes to temp file.
        """
        import tempfile

        from packages.backend.domain.masking import strip_pii_for_llm

        user_id = ctx.get("user_id")
        job_id = ctx.get("job_id")
        job = ctx.get("job", {})
        profile = ctx.get("profile", {})
        if not user_id or not job_id:
            return None

        content: Optional[str] = None
        async with self.pool.acquire() as conn:
            existing = await CoverLetterRepo.get_by_job_user(conn, user_id, job_id)
            if existing:
                content = existing.get("content")

        if not content:
            try:
                sanitized_profile = strip_pii_for_llm(profile) if profile else {}
                job_for_prompt = {
                    "title": job.get("title", ""),
                    "company": job.get("company") or job.get("company_name", ""),
                    "description": job.get("description", ""),
                }
                prompt = build_cover_letter_prompt(
                    sanitized_profile, job_for_prompt, tone="professional"
                )

                async def _cover_letter_call():
                    return await _llm_client.call(
                        prompt=prompt,
                        response_format=CoverLetterResponse_V1,
                    )

                result = await _llm_call_with_retry(_cover_letter_call)
                content = result.content if hasattr(result, "content") else str(result)
                async with self.pool.acquire() as conn:
                    await CoverLetterRepo.create(
                        conn, user_id, job_id, content, tone="professional"
                    )
            except Exception as e:
                logger.warning(
                    "Cover letter generation failed for job %s: %s", job_id, e
                )
                return None

        if not content:
            return None

        try:
            fd, path = tempfile.mkstemp(suffix=".txt", prefix="cover_letter_")
            try:
                with open(fd, "w", encoding="utf-8") as f:
                    f.write(content)
                # Track for cleanup
                ctx.setdefault("_temp_paths", []).append(path)
                return path
            except Exception:
                # MEDIUM: Clean up file handle on error
                try:
                    os.close(fd)
                    if os.path.exists(path):
                        os.unlink(path)
                except OSError:
                    pass
                raise
        except OSError as e:
            logger.warning("Failed to write cover letter temp file: %s", e)
            return None

    async def _get_portfolio_path(self, ctx: dict) -> Optional[str]:
        """Get portfolio file path from context.

        LOW: Retrieves portfolio from user profile or storage.
        """
        try:
            user_id = ctx.get("user_id")
            if not user_id:
                return None

            # Try to get portfolio from profile (profile is normalized CanonicalProfile)
            profile_obj = ctx.get("profile") or ctx.get("profile_data")
            portfolio_url = None
            if profile_obj:
                contact = getattr(profile_obj, "contact", None) or (
                    profile_obj.get("contact")
                    if isinstance(profile_obj, dict)
                    else None
                )
                if contact:
                    portfolio_url = getattr(contact, "portfolio_url", None) or (
                        contact.get("portfolio_url")
                        if isinstance(contact, dict)
                        else None
                    )
                if not portfolio_url and isinstance(profile_obj, dict):
                    portfolio_url = profile_obj.get("portfolio_url") or profile_obj.get(
                        "portfolio"
                    )

            if portfolio_url:
                # Download portfolio file if it's a URL
                if portfolio_url.startswith("http://") or portfolio_url.startswith(
                    "https://"
                ):
                    import tempfile

                    import httpx

                    async with httpx.AsyncClient(timeout=35.0) as client:
                        resp = await client.get(portfolio_url)
                        resp.raise_for_status()

                        fd, path = tempfile.mkstemp(suffix=".pdf", prefix="portfolio_")
                        try:
                            with open(fd, "wb") as f:
                                f.write(resp.content)
                            ctx.setdefault("_temp_paths", []).append(path)
                            return path
                        except Exception:
                            try:
                                os.close(fd)
                                if os.path.exists(path):
                                    os.unlink(path)
                            except OSError:
                                pass
                            raise
                elif os.path.exists(portfolio_url):
                    return portfolio_url

            return None
        except Exception as e:
            logger.warning("Failed to get portfolio path: %s", e)
            return None

    async def _get_document_path(self, ctx: dict, doc_type: str) -> Optional[str]:
        """Get document file path for other document types.

        LOW: Retrieves documents (cover letters, certificates, etc.) from user profile or storage.

        Args:
            ctx: Application context
            doc_type: Document type (cover_letter, certificate, transcript, etc.)
        """
        try:
            user_id = ctx.get("user_id")
            if not user_id:
                return None

            # Try to get document from raw profile_data (documents not in CanonicalProfile)
            profile_data = ctx.get("profile_data") or (
                ctx.get("profile") if isinstance(ctx.get("profile"), dict) else None
            )
            documents = (
                (profile_data or {}).get("documents", [])
                if isinstance(profile_data, dict)
                else []
            )

            # Find document by type
            for doc in documents:
                if isinstance(doc, dict):
                    doc_type_match = doc.get("type", "").lower()
                    doc_url = doc.get("url") or doc.get("file_url")

                    if doc_type_match == doc_type.lower() and doc_url:
                        # Download document if it's a URL
                        if doc_url.startswith("http://") or doc_url.startswith(
                            "https://"
                        ):
                            import tempfile

                            import httpx

                            async with httpx.AsyncClient(timeout=35.0) as client:
                                resp = await client.get(doc_url)
                                resp.raise_for_status()

                                # Determine file extension from content-type or URL
                                ext = ".pdf"  # Default
                                content_type = resp.headers.get("content-type", "")
                                if "pdf" in content_type:
                                    ext = ".pdf"
                                elif "docx" in content_type or doc_url.endswith(
                                    ".docx"
                                ):
                                    ext = ".docx"
                                elif "doc" in content_type or doc_url.endswith(".doc"):
                                    ext = ".doc"

                                fd, path = tempfile.mkstemp(
                                    suffix=ext, prefix=f"{doc_type}_"
                                )
                                try:
                                    with open(fd, "wb") as f:
                                        f.write(resp.content)
                                    ctx.setdefault("_temp_paths", []).append(path)
                                    return path
                                except Exception:
                                    try:
                                        os.close(fd)
                                        if os.path.exists(path):
                                            os.unlink(path)
                                    except OSError:
                                        pass
                                    raise
                        elif os.path.exists(doc_url):
                            return doc_url

            return None
        except Exception as e:
            logger.warning("Failed to get document path for type %s: %s", doc_type, e)
            return None

    async def capture_screenshot(
        self, page: Page, ctx: dict, stage: str = "unknown", success: bool = True
    ) -> Optional[str]:
        """Capture screenshot for application success/failure proof."""
        try:
            app_id = ctx.get("app_id", "unknown")
            timestamp = int(time.time())
            filename = f"screenshot_{app_id}_{stage}_{timestamp}.png"

            # Capture full page screenshot
            screenshot_bytes = await page.screenshot(
                full_page=True, type="png", animations="disabled"
            )

            # MEDIUM: Implement screenshot storage using Supabase storage
            screenshot_url = f"/screenshots/{filename}"  # Fallback
            try:
                from packages.backend.domain.resume import upload_to_supabase_storage
                from shared.storage import get_storage_service

                # Try Supabase storage first
                storage_path = f"{app_id}/{filename}"
                try:
                    uploaded_path = await upload_to_supabase_storage(
                        bucket="screenshots",
                        path=storage_path,
                        data=screenshot_bytes,
                        content_type="image/png",
                    )
                    screenshot_url = f"/storage/{uploaded_path}"
                    logger.info("Screenshot stored successfully: %s", uploaded_path)
                except Exception as supabase_error:
                    # Fallback to generic storage service
                    logger.warning(
                        "Supabase storage failed, trying generic storage: %s",
                        supabase_error,
                    )
                    storage_service = get_storage_service()
                    if storage_service:
                        # Use storage service if available
                        screenshot_url = await storage_service.upload(
                            bucket="screenshots",
                            path=storage_path,
                            data=screenshot_bytes,
                            content_type="image/png",
                        )
                        logger.info(
                            "Screenshot stored via storage service: %s", screenshot_url
                        )
                    else:
                        raise Exception("No storage service available")
            except ImportError as import_error:
                logger.warning("Screenshot storage not available: %s", import_error)
            except Exception as storage_error:
                logger.error("Failed to store screenshot: %s", storage_error)
                # Continue with fallback URL - screenshot metadata still recorded

            # Record screenshot metadata
            await self._record_screenshot_metadata(
                app_id=app_id,
                filename=filename,
                stage=stage,
                success=success,
                screenshot_url=screenshot_url,
                file_size=len(screenshot_bytes),
            )

            logger.info(
                "Captured screenshot for application %s at stage %s: %s (%d bytes)",
                app_id,
                stage,
                filename,
                len(screenshot_bytes),
            )

            return screenshot_url

        except Exception as e:
            logger.error(
                "Failed to capture screenshot for %s at stage %s: %s",
                ctx.get("app_id", "unknown"),
                stage,
                e,
            )
            return None

    async def _record_screenshot_metadata(
        self,
        app_id: str,
        filename: str,
        stage: str,
        success: bool,
        screenshot_url: str,
        file_size: int,
    ) -> None:
        """Record screenshot metadata in database."""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO public.application_screenshots
                    (application_id, filename, stage, success, screenshot_url, file_size, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, now())
                    """,
                    app_id,
                    filename,
                    stage,
                    success,
                    screenshot_url,
                    file_size,
                )
        except Exception as e:
            logger.error("Failed to record screenshot metadata: %s", e)

    async def _send_status_change_email(
        self,
        ctx: dict,
        old_status: str,
        new_status: str,
        reason: str,
    ) -> None:
        """Send status change email notification."""
        try:
            email_manager = get_email_communication_manager(self.pool)

            # Get user_id from context if not present
            user_id = ctx.get("user_id")
            if not user_id:
                # Acquire connection to fetch user_id (caller may not have valid conn)
                async with self.pool.acquire() as conn:
                    user_id = await conn.fetchval(
                        "SELECT user_id FROM public.applications WHERE id = $1",
                        ctx["app_id"],
                    )

            if user_id:
                await email_manager.send_status_change_email(
                    user_id=user_id,
                    application_id=ctx["app_id"],
                    old_status=old_status,
                    new_status=new_status,
                    reason=reason,
                    tenant_id=ctx.get("tenant_id"),
                )

        except Exception as e:
            logger.error("Failed to send status change email: %s", e)

    async def _submit_application(self, page: Page, ctx: dict) -> None:
        """Click the submit button.

        HIGH: Integrates CAPTCHA detection and solving before submission.
        """
        # Check for unsupported CAPTCHA types first (escalate immediately)
        try:
            captcha_det = await detect_captcha_ats(page)
            if captcha_det.detected and captcha_det.captcha_type:
                ct = (captcha_det.captcha_type or "").lower()
                if ct in UNSUPPORTED_CAPTCHA_TYPES:
                    raise CaptchaRequiredError(
                        f"Unsupported CAPTCHA ({ct}) detected; human verification required"
                    )
        except CaptchaRequiredError:
            raise
        except Exception as e:
            logger.debug("CAPTCHA pre-check before submit: %s", e)

        # HIGH: Detect and solve CAPTCHA before form submission
        try:
            from packages.backend.domain.captcha_handler import CaptchaHandler

            handler = CaptchaHandler()
            page_url = page.url

            # Handle CAPTCHA (detects and solves)
            captcha_result = await handler.handle_captcha(page, page_url)

            if captcha_result.get("detected"):
                captcha_type = captcha_result.get("captcha_type", "unknown")
                logger.warning(
                    "CAPTCHA detected: type=%s on %s",
                    captcha_type,
                    page_url,
                )
                incr("agent.captcha.detected", tags={"type": captcha_type})

                if captcha_result.get("solved"):
                    solution = captcha_result.get("solution")
                    if solution:
                        # Inject solution into page
                        injected = await handler.inject_solution(
                            page, captcha_type, solution
                        )
                        if injected:
                            logger.info("CAPTCHA solved and injected successfully")
                            incr("agent.captcha.solved", tags={"type": captcha_type})
                        else:
                            logger.warning("CAPTCHA solved but injection failed")
                            incr(
                                "agent.captcha.injection_failed",
                                tags={"type": captcha_type},
                            )
                    else:
                        logger.error("CAPTCHA solved but no solution returned")
                        incr("agent.captcha.no_solution", tags={"type": captcha_type})
                else:
                    error = captcha_result.get("error", "Unknown error")
                    logger.error("Failed to solve CAPTCHA: %s", error)
                    incr(
                        "agent.captcha.failed",
                        tags={"type": captcha_type, "error": error},
                    )
                    raise CaptchaRequiredError(
                        f"CAPTCHA ({captcha_type}) detected but not solved: {error}"
                    )
        except CaptchaRequiredError:
            raise
        except Exception as e:
            logger.warning("CAPTCHA detection/solving failed: %s", e)
            incr("agent.captcha.error", tags={"error": type(e).__name__})
            # Continue with submission - don't block on CAPTCHA detection errors

        # Capture screenshot before submission
        await self.capture_screenshot(page, ctx, "pre_submit", success=True)

        base_selectors = ctx["blueprint"].submit_button_selectors()
        ats_handler = ctx.get("ats_handler")
        job_board_handler = ctx.get("job_board_handler")
        
        # Get submit selectors from handler (ATS or job board)
        submit_selectors = base_selectors
        if ats_handler:
            ats_submit = ats_handler.get_custom_selectors().get("submit", [])
            submit_selectors = ats_submit + base_selectors
        elif job_board_handler:
            job_board_submit = job_board_handler.get_application_selectors().get("submit_button")
            if job_board_submit:
                submit_selectors = job_board_submit
            else:
                # For job boards, also try apply button selectors
                apply_selectors = job_board_handler.get_application_selectors().get("apply_button")
                if apply_selectors:
                    submit_selectors = apply_selectors + base_selectors
                    
        submitted = await submit_form(page, submit_selectors)
        if not submitted:
            raise RuntimeError("Could not locate a submit button on the form")

        # Capture screenshot after submission
        await self.capture_screenshot(page, ctx, "post_submit", success=True)
        
        # Run post-apply hooks for job board handlers
        if job_board_handler:
            try:
                await job_board_handler.post_apply_hook(page, ctx)
            except Exception as e:
                logger.warning("Job board post_apply_hook failed: %s", e)

    async def _handle_success(self, task: dict, ctx: dict, page: Page | None) -> None:
        # Capture success screenshot (skip when page is None, e.g. HTTP-first apply)
        if page is not None:
            try:
                await self.capture_screenshot(page, ctx, "success", success=True)
            except Exception as e:
                logger.warning("Failed to capture success screenshot: %s", e)

        async with self.pool.acquire() as conn:
            final_status = await ctx["blueprint"].on_task_completed(
                conn, task, ctx["tenant_id"]
            )

            # Record evaluation
            answered = await InputRepo.get_answered(conn, ctx["app_id"])
            had_hold = bool(answered)

            await record_system_evaluation(
                conn,
                application_id=ctx["app_id"],
                status=final_status,
                attempt_count=ctx["attempt"],
                tenant_id=ctx["tenant_id"],
                user_id=ctx["user_id"],
                had_hold=had_hold,
            )

            # Send status change email
            await self._send_status_change_email(
                ctx,
                "PROCESSING",
                final_status,
                "Application successfully submitted",
            )

            # Process application success alert
            notification_manager = get_enhanced_notification_manager(self.pool)
            await notification_manager.process_alert(
                alert_type="application_success",
                user_id=ctx["user_id"],
                alert_data={
                    "application_id": ctx["app_id"],
                    "company": ctx["job"].get("company", "Unknown"),
                    "job_title": ctx["job"].get("title", "Unknown"),
                    "status": final_status,
                    "attempt_count": ctx["attempt"],
                },
                tenant_id=ctx["tenant_id"],
            )

        # C4: Analytics Tracking - Track application submitted
        if final_status in ("APPLIED", "SUBMITTED", "COMPLETED"):
            incr(
                "application_submitted",
                tags={
                    "tenant_id": ctx["tenant_id"] or "none",
                    "blueprint": ctx["blueprint_key"],
                    "status": final_status,
                    "attempt_count": str(ctx["attempt"]),
                },
            )
            logger.info(
                "[ANALYTICS] Application submitted: app_id=%s, company=%s, status=%s",
                ctx["app_id"],
                ctx["job"].get("company", "Unknown"),
                final_status,
            )

        incr(
            "agent.tasks_completed",
            tags={
                "tenant_id": ctx["tenant_id"] or "none",
                "blueprint": ctx["blueprint_key"],
            },
        )
        logger.info("Task %s completed with status %s", ctx["app_id"], final_status)

        try:
            async with self.pool.acquire() as notify_conn:
                await notify_application_submitted(
                    notify_conn,
                    user_id=ctx["user_id"],
                    company=ctx["job"].get("company", "a company"),
                    job_title=ctx["job"].get("title", "a position"),
                    application_id=ctx["app_id"],
                    tenant_id=ctx["tenant_id"],
                )
        except Exception as push_exc:
            logger.warning(
                "Push notification failed for %s: %s", ctx["app_id"], push_exc
            )

    # -- hold logic --------------------------------------------------------

    async def _enter_hold(
        self,
        app_id: str,
        unresolved: list[dict[str, str]],
        form_fields: list[FormField],
        tenant_id: str | None = None,
    ) -> None:
        logger.info(
            "Application %s → REQUIRES_INPUT (%d unresolved)", app_id, len(unresolved)
        )
        async with db_transaction(self.pool) as conn:
            await InputRepo.insert_unresolved(
                conn, app_id, unresolved, form_fields, tenant_id=tenant_id
            )
            await update_application_status(conn, app_id, "REQUIRES_INPUT")
            await EventRepo.emit(
                conn,
                app_id,
                "REQUIRES_INPUT_RAISED",
                {
                    "unresolved_fields": [u["selector"] for u in unresolved],
                    "count": len(unresolved),
                },
                tenant_id=tenant_id,
            )
        incr(
            "agent.applications_requires_input", tags={"tenant_id": tenant_id or "none"}
        )

        # Send status change email (use pool - conn is released after transaction)
        await self._send_status_change_email(
            {"app_id": app_id, "tenant_id": tenant_id},
            "PROCESSING",
            "REQUIRES_INPUT",
            f"Application requires {len(unresolved)} answers to proceed",
        )

        # Process hold questions alert
        notification_manager = get_enhanced_notification_manager(self.pool)
        await notification_manager.process_alert(
            alert_type="hold_questions_ready",
            user_id=None,  # Will be set in _send_status_change_email
            alert_data={
                "application_id": app_id,
                "question_count": len(unresolved),
                "tenant_id": tenant_id,
            },
            tenant_id=tenant_id,
        )

        # Push notification: hold questions need answers
        try:
            # Fetch user_id from the application
            async with self.pool.acquire() as notify_conn:
                app_row = await notify_conn.fetchrow(
                    "SELECT user_id, job_id FROM public.applications WHERE id = $1",
                    app_id,
                )
                if app_row:
                    job_row = await notify_conn.fetchrow(
                        "SELECT company FROM public.jobs WHERE id = $1",
                        str(app_row["job_id"]),
                    )
                    await notify_hold_questions(
                        notify_conn,
                        user_id=str(app_row["user_id"]),
                        company=job_row["company"] if job_row else "a company",
                        question_count=len(unresolved),
                        application_id=app_id,
                        tenant_id=tenant_id,
                    )
        except Exception as push_exc:
            logger.warning("Push notification failed for hold %s: %s", app_id, push_exc)

    # -- failure handling --------------------------------------------------

    async def _handle_failure(
        self, task: dict, exc: Exception, page: Optional[Page] = None
    ) -> None:
        app_id = str(task["id"])
        tenant_id = str(task["tenant_id"]) if task.get("tenant_id") else None
        attempt = task["attempt_count"]
        error_msg = str(exc)[:1000]

        logger.exception("Application %s failed (attempt %d): %s", app_id, attempt, exc)

        user_id = str(task["user_id"]) if task.get("user_id") else None

        # Capture failure screenshot if page is available
        if page:
            try:
                await self.capture_screenshot(
                    page, {"app_id": app_id}, "failure", success=False
                )
            except Exception as screenshot_exc:
                logger.warning(
                    "Failed to capture failure screenshot: %s", screenshot_exc
                )

        async with db_transaction(self.pool) as conn:
            # Check if we reached max attempts
            if attempt >= MAX_ATTEMPTS:
                logger.error(
                    "Application %s reached max attempts. Moving to DLQ.", app_id
                )
                await update_application_status(
                    conn, app_id, "FAILED", error_message=error_msg
                )

                # Send status change email for failure
                await self._send_status_change_email(
                    {"app_id": app_id, "tenant_id": tenant_id, "user_id": user_id},
                    "PROCESSING",
                    "FAILED",
                    f"Application failed after {attempt} attempts: {error_msg}",
                )

                # Process application failure alert
                notification_manager = get_enhanced_notification_manager(self.pool)
                await notification_manager.process_alert(
                    alert_type="application_failed",
                    user_id=user_id,
                    alert_data={
                        "application_id": app_id,
                        "error_message": error_msg,
                        "attempt_count": attempt,
                        "max_attempts": MAX_ATTEMPTS,
                        "tenant_id": tenant_id,
                    },
                    tenant_id=tenant_id,
                )

                # Insert into DLQ
                await conn.execute(
                    """
                    INSERT INTO public.job_dead_letter_queue
                    (application_id, tenant_id, failure_reason, attempt_count, last_error, payload)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """,
                    app_id,
                    tenant_id,
                    "MAX_ATTEMPTS_REACHED",
                    attempt,
                    error_msg,
                    json.dumps(task, default=str),
                )

                incr("agent.dlq_insertion", tags={"tenant_id": tenant_id or "none"})
            else:
                # Exponential backoff: 30s, 60s, 120s, ...
                backoff_seconds = 30 * (2 ** (attempt - 1))
                logger.info(
                    "Scheduling retry for %s in %ds (attempt %d)",
                    app_id,
                    backoff_seconds,
                    attempt,
                )

                await conn.execute(
                    """
                    UPDATE public.applications
                    SET    status       = 'QUEUED',
                    last_error   = $2,
                    available_at = now() + make_interval(secs => $3),
                    updated_at   = now()
                    WHERE  id = $1
                """,
                    app_id,
                    error_msg,
                    float(backoff_seconds),
                )

                await EventRepo.emit(
                    conn,
                    app_id,
                    "RETRY_SCHEDULED",
                    {
                        "error_message": error_msg,
                        "attempt_count": attempt,
                        "backoff_seconds": backoff_seconds,
                        "available_at": f"now+{backoff_seconds}s",
                    },
                    tenant_id=tenant_id,
                )

                # Record system evaluation for retry (using RETRY_SCHEDULED status if supported by enum, else generic)
                # The Enum in models.py has RETRY_SCHEDULED in ApplicationEventType but maybe not in ApplicationStatus.
                # ApplicationStatus only has QUEUED/PROCESSING/REQUIRES_INPUT/APPLIED/SUBMITTED/COMPLETED/FAILED.
                # So we record it as QUEUED effectively, but let's log the event.
                await record_system_evaluation(
                    conn,
                    application_id=app_id,
                    status="QUEUED",  # It is back in queue
                    attempt_count=attempt,
                    error_message=error_msg,
                    tenant_id=tenant_id,
                    user_id=user_id,
                )

                # Exit early, don't emit "FAILED" event below
                return

            await EventRepo.emit(
                conn,
                app_id,
                "FAILED",
                {
                    "error_message": error_msg,
                    "attempt_count": attempt,
                },
                tenant_id=tenant_id,
            )

            # Record system evaluation for failure
            await record_system_evaluation(
                conn,
                application_id=app_id,
                status="FAILED",
                attempt_count=attempt,
                error_message=error_msg,
                tenant_id=tenant_id,
                user_id=user_id,
            )
        incr("agent.applications_failed", tags={"tenant_id": tenant_id or "none"})


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


async def worker_loop() -> None:
    setup_telemetry("sorce-worker")
    s = get_settings()
    enabled = [slug.strip() for slug in s.enabled_blueprints.split(",") if slug.strip()]
    load_default_blueprints(enabled_slugs=enabled or None)
    pool = await create_db_pool()

    # HIGH: Add signal handlers for graceful shutdown and browser cleanup
    import signal

    browser = None
    playwright_instance = None

    async def cleanup_browser():
        """Cleanup browser and Playwright on shutdown."""
        if browser:
            try:
                await browser.close()
                logger.info("Browser closed gracefully")
            except Exception as e:
                logger.warning("Error closing browser: %s", e)
        if playwright_instance:
            try:
                await playwright_instance.stop()
                logger.info("Playwright stopped gracefully")
            except Exception as e:
                logger.warning("Error stopping Playwright: %s", e)

    def signal_handler(signum, _frame):
        """Handle shutdown signals."""
        logger.info("Received signal %d, initiating graceful shutdown...", signum)
        asyncio.create_task(cleanup_browser())

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    async with async_playwright() as pw:
        playwright_instance = pw
        # Try to launch chromium with fallback handling
        try:
            browser = await pw.chromium.launch(headless=s.playwright_headless)
        except Exception as e:
            logger.warning("Failed to launch chromium with default settings: %s", e)
            try:
                # Try with headless=True if headless=False failed
                if not s.playwright_headless:
                    browser = await pw.chromium.launch(headless=True)
                else:
                    # Try with channel specified as last resort
                    browser = await pw.chromium.launch(
                        headless=s.playwright_headless,
                        channel="chromium"
                    )
            except Exception as e2:
                logger.error("Failed to launch chromium: %s", e2)
                raise

        async def context_factory() -> BrowserContext:
            import random  # nosec B311 - random.choice used for browser fingerprinting, not security purposes

            _ua_pool = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            ]
            _vp_pool = [
                {"width": 1280, "height": 800},
                {"width": 1366, "height": 768},
                {"width": 1440, "height": 900},
                {"width": 1536, "height": 864},
                {"width": 1920, "height": 1080},
            ]
            return await browser.new_context(  # nosec B311
                viewport=random.choice(_vp_pool),  # nosec B311 - browser fingerprinting
                user_agent=random.choice(_ua_pool),  # nosec B311 - browser fingerprinting
                # nosec B311 - browser fingerprinting
                locale=random.choice(["en-US", "en-GB", "en-CA"]),
                timezone_id=random.choice(  # nosec B311 - browser fingerprinting
                    [
                        "America/New_York",
                        "America/Chicago",
                        "America/Los_Angeles",
                        "America/Denver",
                    ]
                ),
            )

        agent = FormAgent(pool, context_factory)
        logger.info(
            "Worker heartbeat: env=%s, poll=%ds, max_attempts=%d",
            s.env.value,
            s.poll_interval_seconds,
            s.max_attempts,
        )
        await agent.run_forever()


# Backward-compatible alias so existing tests/imports still work
ApplicationAgent = FormAgent


def _ensure_playwright_browsers():
    """Ensure Playwright browsers are installed, install if missing."""
    import subprocess
    import sys
    
    try:
        # Run playwright install to ensure browsers are present
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        return result.returncode == 0
    except Exception:
        return False


def main() -> None:
    _ensure_playwright_browsers()
    asyncio.run(worker_loop())


if __name__ == "__main__":
    main()
