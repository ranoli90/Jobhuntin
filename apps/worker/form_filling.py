"""Form filling, submission, and verification logic for the Playwright agent.

Extracted from agent.py as part of PERF-002 to improve modularity. Contains:
  - fill_form_from_mapping()  — fill each field using selector → value mappings
  - submit_form()             — click submit and verify success
  - _fill_select / _fill_radio / _fill_checkbox — field-type helpers
  - _verify_submit_success()  — post-submit success/error detection
  - SUCCESS_INDICATORS / ERROR_INDICATORS constants
"""

from __future__ import annotations

import asyncio
import os
import random
import re
from typing import Any, Callable

from playwright.async_api import Page

from shared.logging_config import get_logger
from shared.metrics import incr

logger = get_logger("sorce.agent.form_filling")

# ---------------------------------------------------------------------------
# Post-submit page content indicators
# ---------------------------------------------------------------------------

SUCCESS_INDICATORS: tuple[str, ...] = (
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

ERROR_INDICATORS: tuple[str, ...] = (
    "please correct",
    "invalid",
    "required field",
    "error submitting",
    "submission failed",
)

# ---------------------------------------------------------------------------
# Form filling
# ---------------------------------------------------------------------------


async def fill_form_from_mapping(
    page: Page,
    field_values: dict[str, str],
    form_fields: list[dict],
    resume_path: str | None = None,
    ctx: dict | None = None,
    get_portfolio_path: Callable[[dict], Any] | None = None,
    get_document_path: Callable[[dict, str], Any] | None = None,
    behavior_simulator: Any | None = None,
) -> None:
    """Fill each field using selector → value from the LLM mapping.

    When *behavior_simulator* (HumanBehaviorSimulator) is provided, uses
    human-like typing for text/textarea/email/tel to reduce bot detection.
    """
    field_lookup: dict[str, dict] = {f["selector"]: f for f in form_fields}

    for selector, value in field_values.items():
        ff = field_lookup.get(selector)
        field_type = ff["type"] if ff else "text"

        try:
            try:
                await page.wait_for_selector(selector, state="attached", timeout=10000)
                el = page.locator(selector).first
                await el.wait_for(state="visible", timeout=5000)

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

            try:
                await page.wait_for_timeout(100)

                actual_value = await el.input_value() if field_type != "file" else None
                if actual_value is not None:
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

        except Exception as exc:
            logger.warning("Could not fill %s: %s", selector, exc)
            incr(
                "agent.field_fill.failed",
                tags={"field_type": field_type, "error": type(exc).__name__},
            )


# ---------------------------------------------------------------------------
# Field-type helpers
# ---------------------------------------------------------------------------


async def _fill_select(el: Any, value: str) -> None:
    """Select an option by value, falling back to label match."""
    try:
        await el.select_option(value=value)
    except Exception as e:
        logger.debug("Select by value failed, trying by label: %s", e)
        await el.select_option(label=value)


async def _fill_radio(page: Page, selector: str, el: Any, value: str) -> None:
    """Click radio with matching value, handling quoted values properly."""
    try:
        radio = page.locator(f'{selector}[value="{value}"]').first
        if await radio.count() > 0:
            await radio.check()
            return
    except Exception as e:
        logger.debug("Radio exact match failed, trying escaped quotes: %s", e)
        escaped_value = value.replace('"', '\\"')
        radio = page.locator(f'{selector}[value="{escaped_value}"]').first
        if await radio.count() > 0:
            await radio.check()
            return

    await el.check()


async def _fill_checkbox(el: Any, value: str) -> None:
    """Check or uncheck a checkbox based on the value string."""
    should_check = value.lower() in ("true", "yes", "1", "on")
    if should_check:
        await el.check()
    else:
        await el.uncheck()


# ---------------------------------------------------------------------------
# Submit & verification
# ---------------------------------------------------------------------------


async def _verify_submit_success(page: Page, strict: bool = False) -> bool:
    """Check page content for success/error indicators after submit.

    *strict*: when True (no navigation occurred), require success indicators.
    When False (navigation completed), require no error indicators.
    """
    try:
        content = (await page.content()).lower()

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

    Implements retry logic with exponential backoff for transient failures.
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
                    is_retryable = (
                        isinstance(e, (TimeoutError, ConnectionError))
                        or "timeout" in str(e).lower()
                        or "network" in str(e).lower()
                    )

                    if is_retryable and attempt < max_retries - 1:
                        delay = base_delay * (2**attempt) + (random.random() * 0.3)
                        logger.warning(
                            "Form submission failed (attempt %d/%d), retrying in %.2fs: %s",
                            attempt + 1,
                            max_retries,
                            delay,
                            e,
                        )
                        await asyncio.sleep(delay)
                        break
                    else:
                        logger.debug(
                            "Form submission didn't trigger navigation, falling back to click: %s",
                            e,
                        )
                        try:
                            await btn.click()
                            await page.wait_for_timeout(3000)
                            success = await _verify_submit_success(page, strict=True)
                            if not success:
                                logger.warning(
                                    "Submit click completed but no success indicator found; treating as uncertain"
                                )
                            return success
                        except Exception as fallback_error:
                            logger.debug(
                                "Fallback click also failed: %s", fallback_error
                            )
                            continue
        if attempt < max_retries - 1 and last_error:
            delay = base_delay * (2**attempt)
            logger.warning("All submit selectors failed, retrying in %.2fs", delay)
            await asyncio.sleep(delay)

    return False
