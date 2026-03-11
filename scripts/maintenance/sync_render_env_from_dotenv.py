#!/usr/bin/env python3
"""Sync all Render environment variables from .env file.

Uses RENDER_API_KEY from .env. Never hardcode credentials.

Usage:
  cp .env.example .env
  # Fill in .env with your values
  export RENDER_API_KEY=rnd_xxx   # or add to .env
  python scripts/maintenance/sync_render_env_from_dotenv.py [--dry-run]

Service IDs are resolved by name from Render API.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import httpx
from dotenv import dotenv_values, load_dotenv

load_dotenv(ROOT / ".env")

RENDER_API_KEY = os.environ.get("RENDER_API_KEY") or os.environ.get("RENDER_API_TOKEN")
BASE = "https://api.render.com/v1"


# Service name -> env vars to sync from .env (keys only; values from .env)
# pragma: allowlist secret
SERVICE_ENV_MAP = {
    "jobhuntin-api": [
        "DATABASE_URL", "DATABASE_READ_URL", "REDIS_URL", "JWT_SECRET", "CSRF_SECRET",
        "WEBHOOK_SIGNING_SECRET", "RESEND_API_KEY", "RESEND_WEBHOOK_SECRET", "EMAIL_FROM",
        "API_PUBLIC_URL", "APP_BASE_URL", "STORAGE_TYPE", "MAGIC_LINK_BIND_TO_IP",
        "LLM_API_KEY", "LLM_API_BASE", "LLM_MODEL", "STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET",
        "ADZUNA_APP_ID", "ADZUNA_API_KEY", "RECAPTCHA_SECRET_KEY", "AGENT_ENABLED",
        "RENDER_DISK_PATH", "env",
    ],
    "sorce-api": [
        "DATABASE_URL", "DATABASE_READ_URL", "REDIS_URL", "JWT_SECRET", "CSRF_SECRET",
        "WEBHOOK_SIGNING_SECRET", "RESEND_API_KEY", "RESEND_WEBHOOK_SECRET", "EMAIL_FROM",
        "API_PUBLIC_URL", "APP_BASE_URL", "STORAGE_TYPE", "MAGIC_LINK_BIND_TO_IP",
        "LLM_API_KEY", "LLM_API_BASE", "LLM_MODEL", "STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET",
        "ADZUNA_APP_ID", "ADZUNA_API_KEY", "RECAPTCHA_SECRET_KEY", "AGENT_ENABLED",
        "RENDER_DISK_PATH", "env", "ENV",
    ],
    "jobhuntin-web": ["VITE_API_URL", "VITE_APP_BASE_URL", "NODE_VERSION"],
    "jobhuntin-seo-engine": [
        "DATABASE_URL", "REDIS_URL", "LLM_API_KEY", "GOOGLE_SERVICE_ACCOUNT_KEY",
        "GOOGLE_SEARCH_CONSOLE_SITE", "GSC_API_KEY", "INDEXNOW_API_KEY",
    ],
    "jobhuntin-job-sync": [
        "DATABASE_URL", "env", "PYTHONPATH", "JOBSPY_USE_FREE_PROXIES",
        "JOBSPY_PROXIES", "JOBSPY_SOURCES", "JOBSPY_RESULTS_PER_SOURCE", "JOBSPY_HOURS_OLD",
    ],
    "jobhuntin-job-queue": ["DATABASE_URL", "env", "PYTHONPATH"],
    "jobhuntin-follow-up-reminders": ["DATABASE_URL", "env", "PYTHONPATH"],
    "sorce-auto-apply-agent": [
        "DATABASE_URL", "DATABASE_READ_URL", "LLM_API_KEY", "LLM_API_BASE", "LLM_MODEL",
        "AGENT_ENABLED", "STORAGE_TYPE", "APP_BASE_URL", "CSRF_SECRET", "JWT_SECRET",
        "WEBHOOK_SIGNING_SECRET", "REDIS_URL", "BROWSERLESS_URL", "BROWSERLESS_TOKEN",
        "env", "ENV",
    ],
    "jobhuntin-job-alerts-daily": ["DATABASE_URL", "env", "PYTHONPATH", "ALERT_FREQUENCY"],
    "jobhuntin-job-alerts-weekly": ["DATABASE_URL", "env", "PYTHONPATH", "ALERT_FREQUENCY"],
    "jobhuntin-weekly-digest": ["DATABASE_URL", "env", "PYTHONPATH", "RESEND_API_KEY", "EMAIL_FROM"],
}


def get_services(token: str) -> list[dict]:
    """Fetch all services from Render API."""
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    resp = httpx.get(f"{BASE}/services?limit=50", headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    items = data if isinstance(data, list) else data.get("services", [])
    return [i.get("service", i) for i in items if isinstance(i, dict)]


def get_env_vars(token: str, service_id: str) -> list[dict]:
    """Fetch env vars for a service. Returns list of {envVar: {id, key, ...}}."""
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    resp = httpx.get(f"{BASE}/services/{service_id}/env-vars", headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "envVars" in data:
        return data["envVars"]
    if isinstance(data, dict):
        return data.get("envVars", data.get("env_vars", []))
    return []


def set_env_var(token: str, service_id: str, key: str, value: str, dry_run: bool) -> bool:
    """Add or update env var. Returns True on success."""
    if dry_run:
        print(f"    [DRY-RUN] {key}=***")
        return True
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    # Check if exists
    current = get_env_vars(token, service_id)
    for item in current:
        ev = item.get("envVar", {})
        if ev.get("key") == key:
            ev_id = ev.get("id")
            r = httpx.put(
                f"{BASE}/services/{service_id}/env-vars/{ev_id}",
                headers=headers,
                json={"value": value},
                timeout=30,
            )
            return r.status_code in (200, 201, 204)
    # Add new
    r = httpx.post(
        f"{BASE}/services/{service_id}/env-vars",
        headers=headers,
        json={"key": key, "value": value},
        timeout=30,
    )
    return r.status_code in (200, 201, 204)


def main() -> int:
    ap = argparse.ArgumentParser(description="Sync .env to Render services")
    ap.add_argument("--dry-run", action="store_true", help="Print only, do not set")
    args = ap.parse_args()

    if not RENDER_API_KEY:
        print("ERROR: Set RENDER_API_KEY or RENDER_API_TOKEN in .env or environment")
        return 1

    env = dotenv_values(ROOT / ".env") or {}
    # Override with actual env (for secrets not in .env file)
    for k, v in os.environ.items():
        if k.startswith(("RENDER_", "DATABASE_", "REDIS_", "JWT_", "CSRF_", "LLM_", "STRIPE_",
                        "RESEND_", "ADZUNA_", "RECAPTCHA_", "GOOGLE_", "GSC_", "INDEXNOW_")):
            env[k] = v

    # Defaults for vars that may not be in .env
    defaults = {
        "env": "prod",
        "ENV": "prod",
        "PYTHONPATH": "apps:packages:.",
        "NODE_VERSION": "20",
        "ALERT_FREQUENCY": "daily",  # for weekly cron, overwritten in render.yaml
    }

    services = get_services(RENDER_API_KEY)
    name_to_id = {s.get("name", ""): s.get("id") for s in services if s.get("id")}

    updated = 0
    skipped = 0
    for svc_name, keys in SERVICE_ENV_MAP.items():
        sid = name_to_id.get(svc_name)
        if not sid:
            continue
        print(f"\n--- {svc_name} ({sid}) ---")
        for key in keys:
            val = env.get(key) or defaults.get(key)
            if val is None or val == "":
                if key in ("DATABASE_URL", "GOOGLE_SERVICE_ACCOUNT_KEY", "RESEND_API_KEY"):
                    print(f"  [SKIP] {key}: not in .env (set in Render dashboard if needed)")
                    skipped += 1
                continue
            if set_env_var(RENDER_API_KEY, sid, key, str(val), args.dry_run):
                print(f"  [SET] {key}")
                updated += 1
            else:
                print(f"  [FAIL] {key}")
                skipped += 1

    print(f"\nDone. Updated: {updated}, Skipped: {skipped}")
    if args.dry_run:
        print("(Dry run - no changes made)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
