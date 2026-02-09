"""
Part 2: Hardened Agent and DOM Handling

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
import time
from typing import Any, TypedDict

import asyncpg
from playwright.async_api import (
    BrowserContext,
    Page,
    async_playwright,
)

from backend.blueprints.registry import get_blueprint, load_default_blueprints
from backend.domain.evaluations import record_system_evaluation
from backend.domain.experiments import get_variant_for_tenant
from backend.domain.models import (
    CanonicalProfile,
    normalize_profile,
)
from backend.domain.notifications import notify_application_submitted, notify_hold_questions
from backend.domain.repositories import (
    ApplicationRepo,
    EventRepo,
    InputRepo,
    JobRepo,
    ProfileRepo,
    db_transaction,
)
from backend.llm.client import LLMClient
from backend.llm.contracts import (
    DomMappingResponse_V1,
    build_dom_mapping_prompt,
)
from backend.llm.prompt_registry import get_prompt
from shared.config import get_settings
from shared.logging_config import LogContext, get_logger, setup_logging
from shared.metrics import RateLimiter, incr, observe
from shared.telemetry import setup_telemetry

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
    name="agent_llm",
    max_calls=_settings.llm_rate_limit_per_minute, window_seconds=60.0
)
_processing_limiter = RateLimiter(
    name="agent_processing",
    max_calls=_settings.max_applications_per_minute, window_seconds=60.0
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
    type: str         # text | email | tel | select | textarea | checkbox | radio | file | …
    required: bool
    step_index: int
    options: list[FormFieldOption] | None


# record_event imported from backend.domain.repositories

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

async def create_pool() -> asyncpg.Pool:
    s = get_settings()
    return await asyncpg.create_pool(s.database_url, min_size=s.db_pool_min, max_size=s.db_pool_max)


async def claim_task(pool: asyncpg.Pool) -> dict | None:
    """Atomically claim the next task, ordered by priority_score DESC (ENTERPRISE > TEAM > PRO > FREE)."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM public.claim_next_prioritized($1)", MAX_ATTEMPTS,
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
        if (el.id) return '#' + el.id;
        if (el.name) return el.tagName.toLowerCase() + '[name="' + el.name + '"]';
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


async def extract_form_fields_single_step(page: Page, step_index: int) -> list[FormField]:
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

        fields.append(FormField(
            selector=f["selector"],
            label=f["label"],
            type=f["type"],
            required=f["required"],
            step_index=step_index,
            options=f.get("options"),
        ))
    return fields


async def detect_next_button(page: Page) -> bool:
    """Check if there's a 'Next' / 'Continue' button (not a Submit)."""
    next_selectors = [
        'button:has-text("Next")',
        'button:has-text("Continue")',
        'input[type="button"][value*="Next" i]',
    ]
    for sel in next_selectors:
        btn = page.locator(sel).first
        if await btn.count() > 0:
            return True
    return False


async def click_next_button(page: Page) -> bool:
    """Click the Next/Continue button and wait for the step transition."""
    next_selectors = [
        'button:has-text("Next")',
        'button:has-text("Continue")',
        'input[type="button"][value*="Next" i]',
    ]
    for sel in next_selectors:
        btn = page.locator(sel).first
        if await btn.count() > 0:
            await btn.click()
            await page.wait_for_timeout(1000)
            return True
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


async def map_fields_via_llm(
    profile: CanonicalProfile,
    form_fields: list[FormField],
    answered_inputs: list[dict] | None = None,
    prompt_version: str | None = None,
) -> dict:
    """Use the LLM client with the versioned DOM mapping contract."""
    prompt = build_mapping_prompt(profile, form_fields, answered_inputs, prompt_version)
    result = await _llm_client.call(
        prompt=prompt,
        response_format=DomMappingResponse_V1,
    )
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
) -> None:
    """Fill each field using selector → value from the LLM mapping."""
    field_lookup: dict[str, FormField] = {f["selector"]: f for f in form_fields}

    for selector, value in field_values.items():
        ff = field_lookup.get(selector)
        field_type = ff["type"] if ff else "text"

        try:
            el = page.locator(selector).first
            step_idx = ff["step_index"] if ff else "?"

            if field_type == "select":
                await _fill_select(el, value)
            elif field_type == "radio":
                await _fill_radio(page, selector, el, value)
            elif field_type == "checkbox":
                await _fill_checkbox(el, value)
            elif field_type == "textarea":
                await el.fill(value)
            elif field_type == "file":
                logger.warning("File upload for %s – skipping (not supported yet)", selector)
            else:
                await el.fill(value)

            logger.info("Filled [step:%s] %s = %s", step_idx, selector, value[:60])

        except Exception as exc:
            logger.warning("Could not fill %s: %s", selector, exc)


async def _fill_select(el: Any, value: str) -> None:
    # Try by value first, fall back to label
    try:
        await el.select_option(value=value)
    except Exception:
        await el.select_option(label=value)


async def _fill_radio(page: Page, selector: str, el: Any, value: str) -> None:
    # Click the radio with matching value
    radio = page.locator(f'{selector.split("[")[0]}[value="{value}"]').first
    if await radio.count() > 0:
        await radio.check()
    else:
        await el.check()


async def _fill_checkbox(el: Any, value: str) -> None:
    should_check = value.lower() in ("true", "yes", "1", "on")
    if should_check:
        await el.check()
    else:
        await el.uncheck()


async def submit_form(page: Page, selectors: list[str] | None = None) -> bool:
    """Click the submit button and wait for navigation or network idle."""
    submit_selectors = selectors or [
        'button[type="submit"]',
        'input[type="submit"]',
        'button:has-text("Submit")',
        'button:has-text("Apply")',
        'button:has-text("Send Application")',
        'button:has-text("Send")',
    ]
    for sel in submit_selectors:
        btn = page.locator(sel).first
        if await btn.count() > 0:
            try:
                async with page.expect_navigation(wait_until="networkidle", timeout=30_000):
                    await btn.click()
            except Exception:
                # Some forms don't navigate; accept the click as success
                await btn.click()
                await page.wait_for_timeout(3000)
            return True
    return False


# ---------------------------------------------------------------------------
# FormAgent – blueprint-parameterized core engine
# ---------------------------------------------------------------------------

class FormAgent:
    """
    Generic form-filling agent engine.

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

    # -- public entry points -----------------------------------------------

    async def run_forever(self) -> None:
        """Infinite polling loop with event-driven wake-up."""
        logger.info("Agent started – event-driven + polling every %ds", self.poll_interval)
        
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
                await asyncio.wait_for(self.wake_event.wait(), timeout=self.poll_interval)
                # logger.debug("Woke up by event")
            except asyncio.TimeoutError:
                # logger.debug("Woke up by timeout")
                pass

    async def _listen_loop(self) -> None:
        """Dedicated connection for LISTEN/NOTIFY."""
        settings = get_settings()
        while True:
            try:
                # Use a dedicated connection for listening
                conn = await asyncpg.connect(settings.database_url)
                try:
                    await conn.add_listener("job_queue", lambda *args: self.wake_event.set())
                    logger.info("Listening for 'job_queue' notifications...")
                    # Keep connection open indefinitely
                    while not conn.is_closed():
                        await asyncio.sleep(60) # Keep-alive check or just sleep
                        # Optional: check connection health
                        if conn.is_closed():
                            break
                finally:
                    await conn.close()
            except Exception as e:
                logger.error(f"Listener connection failed: {e}. Retrying in 5s...")
                await asyncio.sleep(5)

    async def run_once(self) -> bool:
        """Claim and process a single task. Returns True if work was done."""
        # Guardrail: emergency stop
        if not _settings.agent_enabled:
            logger.warning("Agent is disabled (AGENT_ENABLED=false), skipping")
            incr("agent.disabled_skip")
            return False

        # Guardrail: processing rate limit
        if not await _processing_limiter.acquire():
            logger.warning("Processing rate limit reached (%d/min), backing off",
                           _settings.max_applications_per_minute)
            incr("agent.rate_limited", {"limiter": "processing"})
            return False

        task = await claim_task(self.pool)
        if task is None:
            return False

        app_id = str(task["id"])
        tenant_id = str(task["tenant_id"]) if task.get("tenant_id") else None
        blueprint_key = task.get("blueprint_key", _settings.default_blueprint_key)
        LogContext.set(
            application_id=app_id,
            user_id=str(task["user_id"]),
            job_id=str(task["job_id"]),
            tenant_id=tenant_id,
        )
        incr("agent.tasks_claimed", tags={"tenant_id": tenant_id or "none", "blueprint": blueprint_key})
        logger.info("Claimed task %s (attempt %d, blueprint=%s)", app_id, task["attempt_count"], blueprint_key)

        context: BrowserContext = await self._context_factory()
        page = await context.new_page()

        try:
            await self._process_task(page, task)
        except Exception as exc:
            await self._handle_failure(task, exc)
        finally:
            await context.close()
            LogContext.clear()

        return True

    # -- core processing ---------------------------------------------------

    async def _process_task(self, page: Page, task: dict) -> None:
        ctx = await self._build_context(task)
        await self._emit_started(ctx)

        # Navigate & Extract
        await self._navigate_to_app(page, ctx)
        form_fields = await self._extract_fields(page)

        # LLM Mapping
        mapping = await self._map_fields(form_fields, ctx)

        # Hold Logic
        if mapping["unresolved_required_fields"]:
            await self._enter_hold(ctx["app_id"], mapping["unresolved_required_fields"], form_fields, tenant_id=ctx["tenant_id"])
            return

        # Fill & Submit
        await self._fill_form(page, mapping, form_fields, ctx)
        await self._submit_application(page, ctx)

        # Success
        await self._handle_success(task, ctx)

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
            "application_url": job["application_url"]
        }

    async def _emit_started(self, ctx: dict) -> None:
        async with self.pool.acquire() as conn:
            await EventRepo.emit(conn, ctx["app_id"], "STARTED_PROCESSING", {
                "application_url": ctx["application_url"],
                "attempt": ctx["attempt"],
                "blueprint": ctx["blueprint_key"],
            }, tenant_id=ctx["tenant_id"])

    async def _navigate_to_app(self, page: Page, ctx: dict) -> None:
        """Navigate to the application URL."""
        try:
            await page.goto(ctx["application_url"], wait_until="networkidle", timeout=PAGE_TIMEOUT_MS)
        except Exception as exc:
            raise RuntimeError(f"Page load timeout for {ctx['application_url']}: {exc}") from exc

    async def _extract_fields(self, page: Page) -> list[FormField]:
        form_fields = await extract_all_form_fields(page)
        if not form_fields:
            raise RuntimeError("No form fields detected on the page")
        logger.info("Extracted %d fields across %d step(s)",
                     len(form_fields),
                     max((f["step_index"] for f in form_fields), default=0) + 1)
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
                variant = await get_variant_for_tenant(conn, "dom_mapping_prompt", ctx["tenant_id"])
            if variant:
                prompt_version = variant
                logger.info("Experiment assigned prompt version: %s", prompt_version)

        # LLM mapping
        if not await _llm_limiter.acquire():
            raise RuntimeError("LLM rate limit exceeded; will retry on next poll")

        t0 = time.monotonic()
        mapping = await map_fields_via_llm(ctx["profile"], form_fields, answered_inputs, prompt_version)
        llm_duration = time.monotonic() - t0
        observe("agent.llm_latency_seconds", llm_duration)
        logger.info("LLM mapping completed in %.2fs (prompt=%s)", llm_duration, prompt_version or "default")
        return mapping

    async def _fill_form(self, page: Page, mapping: dict, form_fields: list[FormField], ctx: dict) -> None:
        # Re-navigate if needed (for multi-step consistency)
        await page.goto(ctx["application_url"], wait_until="networkidle", timeout=PAGE_TIMEOUT_MS)

        max_step = max((f["step_index"] for f in form_fields), default=0)
        for step in range(max_step + 1):
            step_values = {
                sel: val for sel, val in mapping["field_values"].items()
                if any(f["selector"] == sel and f["step_index"] == step for f in form_fields)
            }
            step_fields = [f for f in form_fields if f["step_index"] == step]

            if step_values:
                await fill_form_from_mapping(page, step_values, step_fields)

            if step < max_step:
                advanced = await click_next_button(page)
                if not advanced:
                    logger.warning("Could not advance from step %d to %d", step, step + 1)
                    break

    async def _submit_application(self, page: Page, ctx: dict) -> None:
        """Click the submit button."""
        submitted = await submit_form(page, ctx["blueprint"].submit_button_selectors())
        if not submitted:
            raise RuntimeError("Could not locate a submit button on the form")

    async def _handle_success(self, task: dict, ctx: dict) -> None:
        async with self.pool.acquire() as conn:
            final_status = await ctx["blueprint"].on_task_completed(conn, task, ctx["tenant_id"])

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

        incr("agent.tasks_completed", tags={"tenant_id": ctx["tenant_id"] or "none", "blueprint": ctx["blueprint_key"]})
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
            logger.warning("Push notification failed for %s: %s", ctx["app_id"], push_exc)

    # -- hold logic --------------------------------------------------------

    async def _enter_hold(
        self,
        app_id: str,
        unresolved: list[dict[str, str]],
        form_fields: list[FormField],
        tenant_id: str | None = None,
    ) -> None:
        logger.info("Application %s → REQUIRES_INPUT (%d unresolved)",
                     app_id, len(unresolved))
        async with db_transaction(self.pool) as conn:
            await InputRepo.insert_unresolved(conn, app_id, unresolved, form_fields, tenant_id=tenant_id)
            await update_application_status(conn, app_id, "REQUIRES_INPUT")
            await EventRepo.emit(conn, app_id, "REQUIRES_INPUT_RAISED", {
                "unresolved_fields": [u["selector"] for u in unresolved],
                "count": len(unresolved),
            }, tenant_id=tenant_id)
        incr("agent.applications_requires_input", tags={"tenant_id": tenant_id or "none"})

        # Push notification: hold questions need answers
        try:
            # Fetch user_id from the application
            async with self.pool.acquire() as notify_conn:
                app_row = await notify_conn.fetchrow(
                    "SELECT user_id, job_id FROM public.applications WHERE id = $1", app_id,
                )
                if app_row:
                    job_row = await notify_conn.fetchrow(
                        "SELECT company FROM public.jobs WHERE id = $1", str(app_row["job_id"]),
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

    async def _handle_failure(self, task: dict, exc: Exception) -> None:
        app_id = str(task["id"])
        tenant_id = str(task["tenant_id"]) if task.get("tenant_id") else None
        attempt = task["attempt_count"]
        error_msg = str(exc)[:1000]

        logger.exception("Application %s failed (attempt %d): %s", app_id, attempt, exc)

        user_id = str(task["user_id"]) if task.get("user_id") else None

        async with db_transaction(self.pool) as conn:
            # Check if we reached max attempts
            if attempt >= MAX_ATTEMPTS:
                logger.error("Application %s reached max attempts. Moving to DLQ.", app_id)
                await update_application_status(conn, app_id, "FAILED", error_message=error_msg)
                
                # Insert into DLQ
                await conn.execute("""
                    INSERT INTO public.job_dead_letter_queue 
                    (application_id, tenant_id, failure_reason, attempt_count, last_error, payload)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, app_id, tenant_id, "MAX_ATTEMPTS_REACHED", attempt, error_msg, json.dumps(task, default=str))
                
                incr("agent.dlq_insertion", tags={"tenant_id": tenant_id or "none"})
            else:
                # Just fail for retry (claim logic will picking it up if status resets or we implement strict retry backoff)
                # Currently claim_next only picks QUEUED or old PROCESSING.
                # We need to set it back to QUEUED or keep it FAILED?
                # If we set to FAILED, it won't be picked up again depending on claim_next logic.
                # claim_next: WHERE (status = 'QUEUED' OR ...)
                # So we should probably set it back to QUEUED so it retries? 
                # Or 'PENDING'?
                # The original code set it to "FAILED". 
                # If "FAILED" is terminal, then retry logic is broken in original code?
                # Let's assume standard behavior: update to 'QUEUED' for retry, or system external force.
                # But typically "FAILED" means manual intervention or retry logic handles it.
                # NOTE: Original code set "FAILED". I will preserve that but maybe add a note.
                # Actually, `claim_next` usually picks up 'QUEUED'. 
                # If we want retry, we should probably set to 'QUEUED' with backoff.
                # But for now, I'll stick to original behavior + DLQ logic.
                await update_application_status(conn, app_id, "FAILED", error_message=error_msg)

            await EventRepo.emit(conn, app_id, "FAILED", {
                "error_message": error_msg,
                "attempt_count": attempt,
            }, tenant_id=tenant_id)

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
    pool = await create_pool()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=s.playwright_headless)

        async def context_factory() -> BrowserContext:
            return await browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
            )

        agent = FormAgent(pool, context_factory)
        logger.info("Worker heartbeat: env=%s, poll=%ds, max_attempts=%d",
                     s.env.value, s.poll_interval_seconds, s.max_attempts)
        await agent.run_forever()


# Backward-compatible alias so existing tests/imports still work
ApplicationAgent = FormAgent


def main() -> None:
    asyncio.run(worker_loop())


if __name__ == "__main__":
    main()
