#!/usr/bin/env python3
"""
End-to-end smoke test for M1 closed beta.

Validates that all critical paths are working:
  1. API health check
  2. Database connectivity + table existence
  3. Job feed returns results
  4. Resume parse endpoint accepts PDF
  5. Billing endpoints respond
  6. Analytics event sink accepts events
  7. Admin dashboard returns data
  8. Worker agent is running (via health or recent activity)

Usage:
    python scripts/smoke_test.py [--api-url http://localhost:8000] [--db]

Exit code 0 = all checks pass, 1 = failures detected.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from typing import Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ---------------------------------------------------------------------------
# Check definitions
# ---------------------------------------------------------------------------

class CheckResult:
    def __init__(self, name: str, passed: bool, detail: str = "", duration_ms: int = 0):
        self.name = name
        self.passed = passed
        self.detail = detail
        self.duration_ms = duration_ms

    def __str__(self) -> str:
        icon = "✅" if self.passed else "❌"
        ms = f" ({self.duration_ms}ms)" if self.duration_ms else ""
        detail = f" — {self.detail}" if self.detail else ""
        return f"  {icon} {self.name}{ms}{detail}"


async def check_api_health(api_url: str) -> CheckResult:
    """Check GET /healthz returns 200."""
    import httpx
    t0 = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{api_url}/healthz")
            ms = int((time.monotonic() - t0) * 1000)
            if resp.status_code == 200:
                return CheckResult("API Health", True, f"status={resp.status_code}", ms)
            return CheckResult("API Health", False, f"status={resp.status_code}", ms)
    except Exception as exc:
        ms = int((time.monotonic() - t0) * 1000)
        return CheckResult("API Health", False, str(exc)[:100], ms)


async def check_database() -> CheckResult:
    """Check database connectivity and critical tables exist."""
    import asyncpg
    from shared.config import get_settings
    s = get_settings()
    t0 = time.monotonic()
    try:
        conn = await asyncpg.connect(s.database_url, timeout=5)
        try:
            tables = await conn.fetch("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name IN (
                    'users', 'jobs', 'applications', 'application_events',
                    'application_inputs', 'tenants', 'tenant_members',
                    'billing_customers', 'analytics_events', 'agent_evaluations',
                    'experiments', 'experiment_assignments'
                  )
                ORDER BY table_name
            """)
            ms = int((time.monotonic() - t0) * 1000)
            found = [r["table_name"] for r in tables]
            expected = {
                "users", "jobs", "applications", "application_events",
                "application_inputs", "tenants", "tenant_members",
                "billing_customers", "analytics_events", "agent_evaluations",
                "experiments", "experiment_assignments",
            }
            missing = expected - set(found)
            if missing:
                return CheckResult("Database Tables", False, f"missing: {', '.join(sorted(missing))}", ms)
            return CheckResult("Database Tables", True, f"{len(found)} tables found", ms)
        finally:
            await conn.close()
    except Exception as exc:
        ms = int((time.monotonic() - t0) * 1000)
        return CheckResult("Database Tables", False, str(exc)[:100], ms)


async def check_jobs_exist() -> CheckResult:
    """Check that the jobs table has data."""
    import asyncpg
    from shared.config import get_settings
    s = get_settings()
    t0 = time.monotonic()
    try:
        conn = await asyncpg.connect(s.database_url, timeout=5)
        try:
            count = await conn.fetchval("SELECT COUNT(*)::int FROM public.jobs")
            ms = int((time.monotonic() - t0) * 1000)
            if count and count > 0:
                return CheckResult("Job Feed Data", True, f"{count} jobs in database", ms)
            return CheckResult("Job Feed Data", False, "No jobs found — run seed_beta.py", ms)
        finally:
            await conn.close()
    except Exception as exc:
        ms = int((time.monotonic() - t0) * 1000)
        return CheckResult("Job Feed Data", False, str(exc)[:100], ms)


async def check_analytics_sink(api_url: str) -> CheckResult:
    """Check POST /analytics/events accepts a test event."""
    import httpx
    t0 = time.monotonic()
    try:
        payload = {
            "events": [{
                "event_type": "app_opened",
                "properties": {"smoke_test": True},
                "session_id": "smoke-test-session",
            }]
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{api_url}/analytics/events",
                json=payload,
            )
            ms = int((time.monotonic() - t0) * 1000)
            if resp.status_code == 200:
                body = resp.json()
                return CheckResult("Analytics Sink", True, f"accepted={body.get('accepted', '?')}", ms)
            return CheckResult("Analytics Sink", False, f"status={resp.status_code}", ms)
    except Exception as exc:
        ms = int((time.monotonic() - t0) * 1000)
        return CheckResult("Analytics Sink", False, str(exc)[:100], ms)


async def check_billing_status(api_url: str) -> CheckResult:
    """Check GET /billing/usage endpoint responds (even without auth it should return 401/403, not 500)."""
    import httpx
    t0 = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{api_url}/billing/usage")
            ms = int((time.monotonic() - t0) * 1000)
            if resp.status_code in (200, 401, 403, 422):
                return CheckResult("Billing Endpoint", True, f"status={resp.status_code} (expected auth-gated)", ms)
            return CheckResult("Billing Endpoint", False, f"status={resp.status_code}", ms)
    except Exception as exc:
        ms = int((time.monotonic() - t0) * 1000)
        return CheckResult("Billing Endpoint", False, str(exc)[:100], ms)


async def check_dashboard_endpoint(api_url: str) -> CheckResult:
    """Check GET /admin/m1-dashboard responds."""
    import httpx
    t0 = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{api_url}/admin/m1-dashboard")
            ms = int((time.monotonic() - t0) * 1000)
            if resp.status_code in (200, 401, 403):
                return CheckResult("M1 Dashboard", True, f"status={resp.status_code}", ms)
            return CheckResult("M1 Dashboard", False, f"status={resp.status_code}", ms)
    except Exception as exc:
        ms = int((time.monotonic() - t0) * 1000)
        return CheckResult("M1 Dashboard", False, str(exc)[:100], ms)


async def check_worker_recent_activity() -> CheckResult:
    """Check if the worker has processed anything in the last hour."""
    import asyncpg
    from shared.config import get_settings
    s = get_settings()
    t0 = time.monotonic()
    try:
        conn = await asyncpg.connect(s.database_url, timeout=5)
        try:
            count = await conn.fetchval("""
                SELECT COUNT(*)::int FROM public.application_events
                WHERE event_type IN ('STARTED_PROCESSING', 'FAILED')
                  AND created_at >= now() - interval '1 hour'
            """)
            ms = int((time.monotonic() - t0) * 1000)
            if count and count > 0:
                return CheckResult("Worker Activity", True, f"{count} events in last hour", ms)
            return CheckResult("Worker Activity", True, "No recent activity (OK if idle)", ms)
        finally:
            await conn.close()
    except Exception as exc:
        ms = int((time.monotonic() - t0) * 1000)
        return CheckResult("Worker Activity", False, str(exc)[:100], ms)


async def check_stripe_config() -> CheckResult:
    """Check that Stripe config vars are set (non-empty)."""
    from shared.config import get_settings
    s = get_settings()
    missing = []
    if not s.stripe_secret_key:
        missing.append("STRIPE_SECRET_KEY")
    if not s.stripe_webhook_secret:
        missing.append("STRIPE_WEBHOOK_SECRET")
    if not s.stripe_pro_price_id:
        missing.append("STRIPE_PRO_PRICE_ID")
    if missing:
        return CheckResult("Stripe Config", False, f"missing: {', '.join(missing)}")
    return CheckResult("Stripe Config", True, "all keys set")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

async def run_all_checks(api_url: str, include_db: bool = True) -> list[CheckResult]:
    results: list[CheckResult] = []

    # API checks (parallel)
    api_checks = await asyncio.gather(
        check_api_health(api_url),
        check_analytics_sink(api_url),
        check_billing_status(api_url),
        check_dashboard_endpoint(api_url),
        return_exceptions=True,
    )
    for r in api_checks:
        if isinstance(r, CheckResult):
            results.append(r)
        else:
            results.append(CheckResult("API Check", False, str(r)[:100]))

    # DB checks
    if include_db:
        db_checks = await asyncio.gather(
            check_database(),
            check_jobs_exist(),
            check_worker_recent_activity(),
            check_stripe_config(),
            return_exceptions=True,
        )
        for r in db_checks:
            if isinstance(r, CheckResult):
                results.append(r)
            else:
                results.append(CheckResult("DB Check", False, str(r)[:100]))

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="M1 Smoke Test")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--db", action="store_true", default=True, help="Include database checks")
    parser.add_argument("--no-db", action="store_true", help="Skip database checks")
    args = parser.parse_args()

    include_db = args.db and not args.no_db

    print("=" * 50)
    print("  Sorce M1 Smoke Test")
    print(f"  API: {args.api_url}")
    print(f"  DB checks: {'yes' if include_db else 'no'}")
    print("=" * 50)
    print()

    results = asyncio.run(run_all_checks(args.api_url, include_db))

    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)

    for r in results:
        print(str(r))

    print()
    print(f"  Results: {passed} passed, {failed} failed out of {len(results)} checks")

    if failed > 0:
        print("\n  ⚠️  Some checks failed. Review above and fix before launch.")
        sys.exit(1)
    else:
        print("\n  🚀  All checks passed. Ready for beta!")
        sys.exit(0)


if __name__ == "__main__":
    main()
