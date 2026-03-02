"""Part 4: Test Harness and Local Sandbox.

Integration test suite that:
  - Serves a fake multi-step job application page via Playwright route interception
  - Creates test data in Postgres (user, profile, job, application)
  - Runs the ApplicationAgent in single-iteration mode
  - Verifies the full hold → answer → resume → submit lifecycle
  - Asserts on application statuses and application_events

Requires:
  - A running Postgres instance with the schema + migrations applied
  - DATABASE_URL env var pointing to it
  - playwright browsers installed (npx playwright install chromium)
"""

from __future__ import annotations

import json
import os

# Import the agent module (adjust path if running from project root)
import sys
import uuid

import asyncpg
import pytest
import pytest_asyncio
from playwright.async_api import Route, async_playwright

repo_root = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, repo_root)
sys.path.insert(0, os.path.join(repo_root, "apps"))
sys.path.insert(0, os.path.join(repo_root, "packages"))

from worker.agent import (
    ApplicationAgent,
)

from packages.backend.domain.repositories import record_event

# ---------------------------------------------------------------------------
# Fake application HTML – two-step form
# ---------------------------------------------------------------------------

FAKE_APPLICATION_HTML_STEP1 = """<!DOCTYPE html>
<html lang="en">
<head><title>Acme Corp – Apply</title></head>
<body>
<h1>Apply to Acme Corp</h1>
<form id="app-form" method="POST" action="/submit">

  <div id="step-1">
    <h2>Step 1: Personal Information</h2>

    <label for="first_name">First Name *</label>
    <input type="text" id="first_name" name="first_name" required />

    <label for="last_name">Last Name *</label>
    <input type="text" id="last_name" name="last_name" required />

    <label for="email">Email *</label>
    <input type="email" id="email" name="email" required />

    <label for="phone">Phone</label>
    <input type="tel" id="phone" name="phone" />

    <label for="clearance">Security Clearance Level *</label>
    <select id="clearance" name="clearance" required>
      <option value="">-- Select --</option>
      <option value="none">None</option>
      <option value="confidential">Confidential</option>
      <option value="secret">Secret</option>
      <option value="top_secret">Top Secret</option>
    </select>

    <button type="button" id="btn-next" onclick="goStep2()">Next</button>
  </div>

  <div id="step-2" style="display:none;">
    <h2>Step 2: Background</h2>

    <label for="education">Highest Education *</label>
    <input type="text" id="education" name="education" required />

    <p>Are you legally authorized to work in the US? *</p>
    <label><input type="radio" name="work_auth" value="yes" required /> Yes</label>
    <label><input type="radio" name="work_auth" value="no" /> No</label>

    <button type="submit">Submit Application</button>
  </div>

</form>

<script>
function goStep2() {
  document.getElementById('step-1').style.display = 'none';
  document.getElementById('step-2').style.display = 'block';
}
</script>
</body>
</html>
"""

FAKE_SUCCESS_HTML = """<!DOCTYPE html>
<html><body><h1>Application Received</h1><p>Thank you!</p></body></html>
"""

FAKE_APP_URL = "https://fake-careers.example.com/apply/senior-engineer"


# ---------------------------------------------------------------------------
# LLM mock – deterministic mapping for the fake form
# ---------------------------------------------------------------------------

async def mock_map_fields_via_llm(profile, form_fields, answered_inputs=None):
    """Deterministic mock for map_fields_via_llm that inspects form_fields
    to decide which fields can be filled from the profile and which are unresolved.
    """
    # Check if "clearance" appears in form fields
    has_clearance_field = any("clearance" in f["selector"].lower() for f in form_fields)
    # Check if a previously answered clearance answer is present
    has_clearance_answer = answered_inputs and any(
        "clearance" in (a.get("selector", "") or "").lower() for a in answered_inputs
    )

    field_values: dict[str, str] = {
        "#first_name": "Alice",
        "#last_name": "Smith",
        "#email": "alice@example.com",
        "#phone": "555-0100",
        "#education": "B.S. Computer Science",
    }

    # Work auth – always answerable from profile (we assume US citizen)
    field_values['input[name="work_auth"]'] = "yes"

    unresolved: list[dict[str, str]] = []

    if has_clearance_field and not has_clearance_answer:
        # First run: clearance is unresolvable
        unresolved.append({
            "selector": "#clearance",
            "question": "What is your security clearance level?",
        })
    elif has_clearance_field and has_clearance_answer:
        # Resume run: user already answered
        field_values["#clearance"] = "secret"

    return {
        "field_values": field_values,
        "unresolved_required_fields": unresolved,
    }


# ---------------------------------------------------------------------------
# Test fixtures
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
    """Insert a test user into public.users. Returns user_id (uuid string)."""
    user_id = str(uuid.uuid4())
    # In a real Supabase setup, auth.users would exist first.
    # For local testing against a vanilla Postgres, we insert directly.
    await conn.execute(
        """
        INSERT INTO public.users (id, full_name, email)
        VALUES ($1, 'Alice Smith', 'alice@example.com')
        ON CONFLICT (id) DO NOTHING
        """,
        user_id,
    )
    return user_id


async def create_test_profile(conn: asyncpg.Connection, user_id: str) -> None:
    """Insert a canonical profile for the test user."""
    profile_data = {
        "contact": {
            "full_name": "Alice Smith",
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
            "phone": "555-0100",
            "location": "San Francisco, CA",
            "linkedin_url": "",
            "portfolio_url": "",
        },
        "education": [
            {
                "institution": "MIT",
                "degree": "B.S.",
                "field_of_study": "Computer Science",
                "start_date": "2014",
                "end_date": "2018",
                "gpa": "3.8",
            }
        ],
        "experience": [
            {
                "company": "TechCorp",
                "title": "Senior Engineer",
                "start_date": "2020",
                "end_date": "present",
                "location": "San Francisco, CA",
                "responsibilities": ["Led backend architecture"],
            }
        ],
        "skills": {
            "technical": ["Python", "TypeScript", "PostgreSQL"],
            "soft": ["Leadership"],
        },
        "certifications": [],
        "languages": ["English"],
        "summary": "Experienced software engineer",
        "current_title": "Senior Engineer",
        "current_company": "TechCorp",
        "years_experience": 6,
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


async def create_test_job(conn: asyncpg.Connection) -> str:
    """Insert a test job pointing to the fake application URL. Returns job_id."""
    job_id = str(uuid.uuid4())
    await conn.execute(
        """
        INSERT INTO public.jobs (id, external_id, title, company, application_url, description)
        VALUES ($1, $2, 'Senior Engineer', 'Acme Corp', $3, 'A great role.')
        """,
        job_id,
        f"adzuna-{uuid.uuid4().hex[:8]}",
        FAKE_APP_URL,
    )
    return job_id


async def create_test_application(
    conn: asyncpg.Connection,
    user_id: str,
    job_id: str,
) -> str:
    """Insert a QUEUED application. Returns application_id."""
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
    # Emit CREATED event
    await record_event(conn, app_id, "CREATED", {"user_id": user_id, "job_id": job_id})
    return app_id


# ---------------------------------------------------------------------------
# Assertion helpers
# ---------------------------------------------------------------------------

async def assert_application_status(
    conn: asyncpg.Connection,
    app_id: str,
    expected_status: str,
) -> dict:
    row = await conn.fetchrow(
        "SELECT * FROM public.applications WHERE id = $1", app_id
    )
    assert row is not None, f"Application {app_id} not found"
    actual = row["status"]
    assert actual == expected_status, (
        f"Expected status '{expected_status}', got '{actual}' for application {app_id}"
    )
    return dict(row)


async def assert_event_exists(
    conn: asyncpg.Connection,
    app_id: str,
    event_type: str,
) -> dict:
    row = await conn.fetchrow(
        """
        SELECT * FROM public.application_events
        WHERE application_id = $1 AND event_type = $2
        ORDER BY created_at DESC LIMIT 1
        """,
        app_id,
        event_type,
    )
    assert row is not None, (
        f"Event '{event_type}' not found for application {app_id}"
    )
    return dict(row)


async def get_application_inputs(
    conn: asyncpg.Connection,
    app_id: str,
) -> list[dict]:
    rows = await conn.fetch(
        "SELECT * FROM public.application_inputs WHERE application_id = $1 ORDER BY created_at",
        app_id,
    )
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Route interceptor – serves the fake application page
# ---------------------------------------------------------------------------

async def setup_route_interception(page):
    """Use Playwright's page.route() to intercept requests to the fake URL
    and serve our test HTML. No separate HTTP server needed.
    """

    async def handle_route(route: Route) -> None:
        url = route.request.url

        if "/apply/" in url and route.request.method == "GET":
            await route.fulfill(
                status=200,
                content_type="text/html",
                body=FAKE_APPLICATION_HTML_STEP1,
            )
        elif "/submit" in url and route.request.method == "POST":
            await route.fulfill(
                status=200,
                content_type="text/html",
                body=FAKE_SUCCESS_HTML,
            )
        else:
            await route.continue_()

    await page.route("**/*", handle_route)


# ---------------------------------------------------------------------------
# Monkey-patch map_fields_via_llm in the agent module for tests
# ---------------------------------------------------------------------------

def patch_map_fields():
    """Replace the agent's map_fields_via_llm with our deterministic mock."""
    import worker.agent as agent_module
    agent_module.map_fields_via_llm = mock_map_fields_via_llm


# ---------------------------------------------------------------------------
# Integration test: full hold → answer → resume → submit lifecycle
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Requires registered blueprints - skip until agent is fully implemented")
@pytest.mark.asyncio
async def test_full_application_lifecycle(db_pool, browser, clean_db):
    """End-to-end test:
    1. Create test data
    2. Run agent once → expect REQUIRES_INPUT (clearance question)
    3. Simulate user answer
    4. Run agent again → expect APPLIED
    5. Verify events.
    """
    patch_map_fields()

    async with db_pool.acquire() as conn:
        user_id = await create_test_user(conn)
        await create_test_profile(conn, user_id)
        job_id = await create_test_job(conn)
        app_id = await create_test_application(conn, user_id, job_id)

    # Build agent with a context factory that sets up route interception
    async def context_factory():
        ctx = await browser.new_context(
            viewport={"width": 1280, "height": 900},
        )
        page = await ctx.new_page()
        await setup_route_interception(page)
        await page.close()  # Agent creates its own page; we just need the context
        return ctx

    # We need route interception on the agent's page too.
    # Override context_factory to add interception on every new page.
    async def context_factory_with_routes():
        ctx = await browser.new_context(viewport={"width": 1280, "height": 900})
        # Intercept at context level
        async def handle_route(route: Route) -> None:
            url = route.request.url
            if "/apply/" in url and route.request.method == "GET":
                await route.fulfill(status=200, content_type="text/html", body=FAKE_APPLICATION_HTML_STEP1)
            elif "/submit" in url and route.request.method == "POST":
                await route.fulfill(status=200, content_type="text/html", body=FAKE_SUCCESS_HTML)
            else:
                await route.continue_()
        await ctx.route("**/*", handle_route)
        return ctx

    agent = ApplicationAgent(db_pool, context_factory_with_routes)

    # ---------------------------------------------------------------
    # Run 1: Agent should hit REQUIRES_INPUT (clearance unresolvable)
    # ---------------------------------------------------------------
    worked = await agent.run_once()
    assert worked, "Agent should have claimed and processed a task"

    async with db_pool.acquire() as conn:
        await assert_application_status(conn, app_id, "REQUIRES_INPUT")
        await assert_event_exists(conn, app_id, "CLAIMED")
        await assert_event_exists(conn, app_id, "STARTED_PROCESSING")
        await assert_event_exists(conn, app_id, "REQUIRES_INPUT_RAISED")

        # Verify application_inputs row was created for clearance
        inputs = await get_application_inputs(conn, app_id)
        assert len(inputs) >= 1, "Expected at least one application_input row"
        clearance_input = next(
            (i for i in inputs if "clearance" in i["selector"].lower()), None
        )
        assert clearance_input is not None, "Expected a clearance question input"
        assert clearance_input["answer"] is None, "Answer should be NULL initially"

    # ---------------------------------------------------------------
    # Simulate user answering the clearance question
    # ---------------------------------------------------------------
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE public.application_inputs
            SET    answer = 'Secret', answered_at = now(), resolved = true
            WHERE  id = $1
            """,
            clearance_input["id"],
        )
        await record_event(conn, app_id, "USER_ANSWERED", {
            "input_id": str(clearance_input["id"]),
            "answer": "Secret",
        })
        # Re-queue the application (simulates POST /agent/resume_task)
        await conn.execute(
            """
            UPDATE public.applications
            SET    status = 'QUEUED', last_error = NULL, updated_at = now()
            WHERE  id = $1
            """,
            app_id,
        )
        await record_event(conn, app_id, "RETRY_SCHEDULED", {"answered_count": 1})

    # ---------------------------------------------------------------
    # Run 2: Agent should resume, fill clearance, and submit → APPLIED
    # ---------------------------------------------------------------
    worked = await agent.run_once()
    assert worked, "Agent should have claimed the re-queued task"

    async with db_pool.acquire() as conn:
        await assert_application_status(conn, app_id, "APPLIED")
        await assert_event_exists(conn, app_id, "SUBMITTED")

        # Verify attempt_count incremented
        app_row = await conn.fetchrow(
            "SELECT attempt_count FROM public.applications WHERE id = $1", app_id
        )
        assert app_row["attempt_count"] == 2, (
            f"Expected attempt_count=2, got {app_row['attempt_count']}"
        )

    # ---------------------------------------------------------------
    # Verify no extra work
    # ---------------------------------------------------------------
    worked = await agent.run_once()
    assert not worked, "No more tasks should be available"


@pytest.mark.skip(reason="Requires registered blueprints - skip until agent is fully implemented")
@pytest.mark.asyncio
async def test_agent_failure_on_no_form_fields(db_pool, browser, clean_db):
    """When the page has no form fields, the agent should mark FAILED."""
    patch_map_fields()

    empty_html = "<!DOCTYPE html><html><body><h1>No form here</h1></body></html>"

    async with db_pool.acquire() as conn:
        user_id = await create_test_user(conn)
        await create_test_profile(conn, user_id)
        job_id = str(uuid.uuid4())
        await conn.execute(
            """
            INSERT INTO public.jobs (id, external_id, title, company, application_url)
            VALUES ($1, $2, 'Bad Job', 'BadCorp', 'https://bad.example.com/apply')
            """,
            job_id,
            f"bad-{uuid.uuid4().hex[:8]}",
        )
        app_id = await create_test_application(conn, user_id, job_id)

    async def context_factory_empty():
        ctx = await browser.new_context(viewport={"width": 1280, "height": 900})
        async def handle_route(route: Route) -> None:
            await route.fulfill(status=200, content_type="text/html", body=empty_html)
        await ctx.route("**/*", handle_route)
        return ctx

    agent = ApplicationAgent(db_pool, context_factory_empty)
    worked = await agent.run_once()
    assert worked

    async with db_pool.acquire() as conn:
        await assert_application_status(conn, app_id, "FAILED")
        await assert_event_exists(conn, app_id, "FAILED")

        app_row = await conn.fetchrow(
            "SELECT last_error FROM public.applications WHERE id = $1", app_id
        )
        assert "No form fields" in (app_row["last_error"] or ""), (
            f"Expected 'No form fields' in last_error, got: {app_row['last_error']}"
        )


# ---------------------------------------------------------------------------
# How to run locally (instructions in comments)
# ---------------------------------------------------------------------------
#
# 1. Start a local Postgres (or Supabase local):
#      supabase start
#    OR:
#      docker run -d --name sorce-pg -p 5432:5432 \
#        -e POSTGRES_PASSWORD=postgres postgres:16
#
# 2. Apply schema + migrations:
#      psql $DATABASE_URL -f supabase/schema.sql
#      psql $DATABASE_URL -f supabase/migrations.sql
#
#    NOTE: For vanilla Postgres (no auth.users), you may need to create a
#    stub auth schema:
#      CREATE SCHEMA IF NOT EXISTS auth;
#      CREATE TABLE IF NOT EXISTS auth.users (id uuid PRIMARY KEY);
#    and insert a row before running tests, or temporarily drop the FK
#    on public.users.id.
#
# 3. Install Python dependencies:
#      pip install asyncpg playwright pytest pytest-asyncio
#      python -m playwright install chromium
#
# 4. Set environment:
#      export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/postgres"
#
# 5. Run the tests:
#      pytest tests/test_integration.py -v -s
#
# 6. (Optional) Run the worker against the fake page manually:
#      export HEADLESS=true
#      python -m worker.agent
#
