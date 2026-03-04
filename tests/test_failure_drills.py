"""Part 4: Failure Drills.

Concrete test scenarios that simulate production failures:
  1. LLM outage – map_fields_via_llm raises consistently
  2. DOM structure change – page missing critical fields
  3. DB transient failure – connection errors during processing

Each test:
  - Sets up controlled failure conditions
  - Runs the agent
  - Asserts correct status, events, and error messages
"""

from __future__ import annotations

import json
import os
import sys
import uuid

import asyncpg
import pytest
import pytest_asyncio
from playwright.async_api import Route, async_playwright

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages"))

from worker.agent import (
    ApplicationAgent,
)

from backend.domain.repositories import record_event

# ---------------------------------------------------------------------------
# Shared test fixtures (reuse from test_integration.py)
# ---------------------------------------------------------------------------

# DATABASE_URL moved to conftest.py


@pytest_asyncio.fixture
async def playwright_instance():
    async with async_playwright() as pw:
        yield pw


@pytest_asyncio.fixture
async def browser(playwright_instance):
    b = await playwright_instance.chromium.launch(headless=True)
    yield b
    await b.close()


# ---------------------------------------------------------------------------
# Test data helpers
# ---------------------------------------------------------------------------

async def create_test_user(conn: asyncpg.Connection) -> str:
    user_id = str(uuid.uuid4())
    await conn.execute(
        """
        INSERT INTO public.users (id, full_name, email)
        VALUES ($1, 'Test User', 'test@example.com')
        ON CONFLICT (id) DO NOTHING
        """,
        user_id,
    )
    return user_id


async def create_test_profile(conn: asyncpg.Connection, user_id: str) -> None:
    profile_data = {
        "contact": {
            "full_name": "Test User",
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "phone": "555-0199",
            "location": "NYC",
            "linkedin_url": "",
            "portfolio_url": "",
        },
        "education": [],
        "experience": [],
        "skills": {"technical": [], "soft": []},
        "certifications": [],
        "languages": ["English"],
        "summary": "Test user",
    }
    await conn.execute(
        """
        INSERT INTO public.profiles (user_id, profile_data)
        VALUES ($1, $2::jsonb)
        ON CONFLICT (user_id) DO UPDATE SET profile_data = EXCLUDED.profile_data
        """,
        user_id,
        json.dumps(profile_data),
    )


async def create_test_job(
    conn: asyncpg.Connection,
    application_url: str = "https://drill.example.com/apply",
) -> str:
    job_id = str(uuid.uuid4())
    await conn.execute(
        """
        INSERT INTO public.jobs (id, external_id, title, company, application_url)
        VALUES ($1, $2, 'Drill Job', 'DrillCorp', $3)
        """,
        job_id,
        f"drill-{uuid.uuid4().hex[:8]}",
        application_url,
    )
    return job_id


async def create_test_application(
    conn: asyncpg.Connection, user_id: str, job_id: str
) -> str:
    app_id = str(uuid.uuid4())
    await conn.execute(
        """
        INSERT INTO public.applications (id, user_id, job_id, status)
        VALUES ($1, $2, $3, 'QUEUED')
        """,
        app_id,
        user_id,
        job_id,
    )
    await record_event(conn, app_id, "CREATED", {"user_id": user_id, "job_id": job_id})
    return app_id


# ---------------------------------------------------------------------------
# Assertion helpers
# ---------------------------------------------------------------------------

async def assert_status(conn, app_id: str, expected: str) -> dict:
    row = await conn.fetchrow(
        "SELECT * FROM public.applications WHERE id = $1", app_id
    )
    assert row is not None, f"Application {app_id} not found"
    assert row["status"] == expected, (
        f"Expected '{expected}', got '{row['status']}'"
    )
    return dict(row)


async def assert_event(conn, app_id: str, event_type: str) -> dict:
    row = await conn.fetchrow(
        """
        SELECT * FROM public.application_events
        WHERE application_id = $1 AND event_type = $2
        ORDER BY created_at DESC LIMIT 1
        """,
        app_id,
        event_type,
    )
    assert row is not None, f"Event '{event_type}' not found for {app_id}"
    return dict(row)


# ---------------------------------------------------------------------------
# Fake form HTML (valid form for LLM drill)
# ---------------------------------------------------------------------------

SIMPLE_FORM_HTML = """<!DOCTYPE html>
<html><body>
<form method="POST" action="/submit">
  <label for="name">Name *</label>
  <input type="text" id="name" name="name" required />
  <button type="submit">Submit</button>
</form>
</body></html>
"""

SUCCESS_HTML = "<!DOCTYPE html><html><body><h1>Done</h1></body></html>"


# ===================================================================
# Drill 1: LLM Outage
# ===================================================================

@pytest.mark.skip(reason="Requires registered blueprints - skip until agent is fully implemented")
@pytest.mark.asyncio
async def test_llm_outage_marks_failed(db_pool, browser, clean_db):
    """When map_fields_via_llm raises consistently, the agent should:
    - Mark the application as FAILED
    - Record a FAILED event with the error message
    - Set last_error on the application row.
    """
    async with db_pool.acquire() as conn:
        user_id = await create_test_user(conn)
        await create_test_profile(conn, user_id)
        job_id = await create_test_job(conn)
        app_id = await create_test_application(conn, user_id, job_id)

    # Mock map_fields_via_llm to always raise (simulates LLM outage)
    async def failing_map_fields(profile, form_fields, answered_inputs=None):
        raise ConnectionError("LLM service unavailable: upstream timeout")

    async def context_factory():
        ctx = await browser.new_context(viewport={"width": 1280, "height": 900})
        async def handle_route(route: Route) -> None:
            if "/apply" in route.request.url:
                await route.fulfill(status=200, content_type="text/html", body=SIMPLE_FORM_HTML)
            elif "/submit" in route.request.url:
                await route.fulfill(status=200, content_type="text/html", body=SUCCESS_HTML)
            else:
                await route.continue_()
        await ctx.route("**/*", handle_route)
        return ctx

    agent = ApplicationAgent(db_pool, context_factory)

    # Patch map_fields_via_llm at the module level
    import worker.agent as agent_module
    original_map = agent_module.map_fields_via_llm
    agent_module.map_fields_via_llm = failing_map_fields

    try:
        worked = await agent.run_once()
        assert worked, "Agent should have claimed the task"

        async with db_pool.acquire() as conn:
            app_row = await assert_status(conn, app_id, "FAILED")
            assert "LLM service unavailable" in (app_row["last_error"] or ""), (
                f"Expected LLM error in last_error, got: {app_row['last_error']}"
            )

            event = await assert_event(conn, app_id, "FAILED")
            payload = event["payload"]
            if isinstance(payload, str):
                payload = json.loads(payload)
            assert "LLM service unavailable" in payload.get("error_message", "")
    finally:
        agent_module.map_fields_via_llm = original_map


@pytest.mark.skip(reason="Requires registered blueprints - skip until agent is fully implemented")
@pytest.mark.asyncio
async def test_llm_outage_preserves_events(db_pool, browser, clean_db):
    """Even on LLM failure, CLAIMED and STARTED_PROCESSING events should exist."""
    async with db_pool.acquire() as conn:
        user_id = await create_test_user(conn)
        await create_test_profile(conn, user_id)
        job_id = await create_test_job(conn)
        app_id = await create_test_application(conn, user_id, job_id)

    async def failing_map_fields(profile, form_fields, answered_inputs=None):
        raise RuntimeError("LLM 503: service degraded")

    async def context_factory():
        ctx = await browser.new_context(viewport={"width": 1280, "height": 900})
        async def handle_route(route: Route) -> None:
            await route.fulfill(status=200, content_type="text/html", body=SIMPLE_FORM_HTML)
        await ctx.route("**/*", handle_route)
        return ctx

    agent = ApplicationAgent(db_pool, context_factory)
    import worker.agent as agent_module
    original = agent_module.map_fields_via_llm
    agent_module.map_fields_via_llm = failing_map_fields

    try:
        await agent.run_once()

        async with db_pool.acquire() as conn:
            await assert_event(conn, app_id, "CLAIMED")
            await assert_event(conn, app_id, "STARTED_PROCESSING")
            await assert_event(conn, app_id, "FAILED")
    finally:
        agent_module.map_fields_via_llm = original


# ===================================================================
# Drill 2: DOM Structure Change
# ===================================================================

@pytest.mark.skip(reason="Requires registered blueprints - skip until agent is fully implemented")
@pytest.mark.asyncio
async def test_dom_no_form_fields(db_pool, browser, clean_db):
    """Page has no form fields (e.g., redesigned page).
    Agent should FAIL with 'No form fields' in the error.
    """
    empty_html = "<!DOCTYPE html><html><body><h1>We've moved!</h1><p>Apply elsewhere.</p></body></html>"

    async with db_pool.acquire() as conn:
        user_id = await create_test_user(conn)
        await create_test_profile(conn, user_id)
        job_id = await create_test_job(conn)
        app_id = await create_test_application(conn, user_id, job_id)

    async def context_factory():
        ctx = await browser.new_context(viewport={"width": 1280, "height": 900})
        async def handle_route(route: Route) -> None:
            await route.fulfill(status=200, content_type="text/html", body=empty_html)
        await ctx.route("**/*", handle_route)
        return ctx

    agent = ApplicationAgent(db_pool, context_factory)
    worked = await agent.run_once()
    assert worked

    async with db_pool.acquire() as conn:
        app_row = await assert_status(conn, app_id, "FAILED")
        assert "No form fields" in (app_row["last_error"] or "")

        event = await assert_event(conn, app_id, "FAILED")
        payload = event["payload"]
        if isinstance(payload, str):
            payload = json.loads(payload)
        assert "No form fields" in payload.get("error_message", "")


@pytest.mark.skip(reason="Requires registered blueprints - skip until agent is fully implemented")
@pytest.mark.asyncio
async def test_dom_missing_submit_button(db_pool, browser, clean_db):
    """Page has form fields but no submit button.
    Agent should FAIL with 'submit button' in the error.
    """
    no_submit_html = """<!DOCTYPE html>
    <html><body>
    <form>
      <label for="name">Name</label>
      <input type="text" id="name" name="name" required />
      <!-- No submit button -->
    </form>
    </body></html>"""

    async with db_pool.acquire() as conn:
        user_id = await create_test_user(conn)
        await create_test_profile(conn, user_id)
        job_id = await create_test_job(conn)
        app_id = await create_test_application(conn, user_id, job_id)

    # Mock map_fields_via_llm to return a valid mapping (no unresolved)
    async def mock_map_fields(profile, form_fields, answered_inputs=None):
        return {
            "field_values": {"#name": "Test User"},
            "unresolved_required_fields": [],
        }

    async def context_factory():
        ctx = await browser.new_context(viewport={"width": 1280, "height": 900})
        async def handle_route(route: Route) -> None:
            await route.fulfill(status=200, content_type="text/html", body=no_submit_html)
        await ctx.route("**/*", handle_route)
        return ctx

    agent = ApplicationAgent(db_pool, context_factory)
    import worker.agent as agent_module
    original = agent_module.map_fields_via_llm
    agent_module.map_fields_via_llm = mock_map_fields

    try:
        worked = await agent.run_once()
        assert worked

        async with db_pool.acquire() as conn:
            app_row = await assert_status(conn, app_id, "FAILED")
            assert "submit button" in (app_row["last_error"] or "").lower(), (
                f"Expected 'submit button' in last_error, got: {app_row['last_error']}"
            )
    finally:
        agent_module.map_fields_via_llm = original


# ===================================================================
# Drill 3: DB Transient Failure (connection error during processing)
# ===================================================================

@pytest.mark.skip(reason="Requires registered blueprints - skip until agent is fully implemented")
@pytest.mark.asyncio
async def test_db_transient_failure_during_event_write(db_pool, browser, clean_db):
    """Simulate a transient DB failure during record_event.
    The agent's _handle_failure path should still surface a clean FAILED status
    or leave the app in a recoverable state (PROCESSING → picked up on restart).

    We verify the agent doesn't crash/hang and produces a meaningful error.
    """
    async with db_pool.acquire() as conn:
        user_id = await create_test_user(conn)
        await create_test_profile(conn, user_id)
        job_id = await create_test_job(conn)
        app_id = await create_test_application(conn, user_id, job_id)

    call_count = 0

# Make record_event fail on the 2nd call (STARTED_PROCESSING),
    # but succeed on subsequent calls (FAILED event write)
    original_record_event = record_event

    async def flaky_record_event(conn, application_id, event_type, payload=None, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 2:  # Fail on STARTED_PROCESSING (2nd call, after CLAIMED)
            raise asyncpg.InterfaceError("connection lost during write")
        return await original_record_event(conn, application_id, event_type, payload, **kwargs)

    async def context_factory():
        ctx = await browser.new_context(viewport={"width": 1280, "height": 900})
        async def handle_route(route: Route) -> None:
            await route.fulfill(status=200, content_type="text/html", body=SIMPLE_FORM_HTML)
        await ctx.route("**/*", handle_route)
        return ctx

    agent = ApplicationAgent(db_pool, context_factory)

    # Patch record_event at the repositories module level (EventRepo.emit delegates here)
    import backend.domain.repositories as repo_module
    original_re = repo_module.record_event
    repo_module.record_event = flaky_record_event

    try:
        worked = await agent.run_once()
        assert worked, "Agent should have claimed the task"

        # The agent should have caught the exception and attempted failure handling.
        # Because the transient error happens inside _process_application,
        # _handle_failure should run and mark as FAILED.
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT status, last_error FROM public.applications WHERE id = $1",
                app_id,
            )
            assert row is not None
            # Either FAILED (if _handle_failure succeeded) or PROCESSING (if it also failed)
            assert row["status"] in ("FAILED", "PROCESSING"), (
                f"Expected FAILED or PROCESSING, got {row['status']}"
            )
            if row["status"] == "FAILED":
                assert "connection lost" in (row["last_error"] or "").lower()
    finally:
        repo_module.record_event = original_re


# ---------------------------------------------------------------------------
# Backwards compatibility: JSON parsing tolerance
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_profile_with_extra_fields():
    """Verify normalize_profile handles profiles with unknown extra fields
    gracefully (forward-compatible JSON parsing).
    """
    from backend.domain.models import normalize_profile

    raw = {
        "contact": {
            "full_name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "",
            "location": "",
            "linkedin_url": "",
            "portfolio_url": "",
            "twitter_handle": "@jane",  # NEW field, not in canonical schema
        },
        "education": [],
        "experience": [],
        "skills": {"technical": [], "soft": [], "languages": ["Python"]},  # extra key in skills
        "certifications": [],
        "languages": [],
        "summary": "",
        "new_top_level_key": "should be ignored",
    }

    profile = normalize_profile(raw)
    assert profile.contact.full_name == "Jane Doe"



@pytest.mark.asyncio
async def test_application_input_meta_with_unknown_keys(db_pool, clean_db):
    """Verify that application_inputs rows with extra keys in meta
    are read without errors (forward-compatible).
    """
    async with db_pool.acquire() as conn:
        user_id = await create_test_user(conn)
        job_id = await create_test_job(conn)
        app_id = await create_test_application(conn, user_id, job_id)

        # Insert an input with extra meta keys
        await conn.execute(
            """
            INSERT INTO public.application_inputs
                (application_id, selector, question, field_type, meta)
            VALUES ($1, '#foo', 'What?', 'text', $2::jsonb)
            """,
            app_id,
            json.dumps({
                "field_type": "text",
                "label": "Foo",
                "options": None,
                "step_index": 0,
                "new_meta_key": "should not break anything",
                "nested": {"deep": True},
            }),
        )

        row = await conn.fetchrow(
            "SELECT meta FROM public.application_inputs WHERE application_id = $1",
            app_id,
        )
        meta = row["meta"]
        if isinstance(meta, str):
            meta = json.loads(meta)

        # Access via .get() with defaults – the pattern used everywhere
        assert meta.get("field_type", "text") == "text"
        assert meta.get("new_meta_key") == "should not break anything"
        assert meta.get("nonexistent_key", "default") == "default"


# ---------------------------------------------------------------------------
# How to run
# ---------------------------------------------------------------------------
#
# export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/postgres"
# pytest tests/test_failure_drills.py -v -s
#
