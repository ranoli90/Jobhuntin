#!/usr/bin/env python3
"""
Sync Render service environment variables to production-ready values.

Updates jobhuntin-api, jobhuntin-web, and jobhuntin-seo-engine with correct
URLs and configuration. Preserves existing secrets (DATABASE_URL, API keys, etc.).

Usage:
  export RENDER_API_KEY=your-key
  PYTHONPATH=packages python scripts/sync_render_envs.py

Required: Create a Redis instance on Render and add REDIS_URL to jobhuntin-api
manually if not set (API fails startup in prod without it).
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages"))

from shared.render_api import require_render_client, RenderAPIError

# Production URLs (Render deployment)
API_URL = "https://sorce-api.onrender.com"
WEB_URL = "https://sorce-web.onrender.com"

SERVICES = {
    "jobhuntin-api": {
        "id": "srv-d63l79hr0fns73boblag",
        "updates": {
            "ENV": "prod",
            "APP_BASE_URL": WEB_URL,
            "API_PUBLIC_URL": API_URL,
            "STORAGE_TYPE": "render_disk",
            "LLM_API_BASE": "https://openrouter.ai/api/v1",
            "LLM_MODEL": "google/gemini-2.0-flash",
            "EMAIL_FROM": "JobHuntin <noreply@jobhuntin.com>",
            "LOG_JSON": "true",
            "LOG_LEVEL": "INFO",
        },
    },
    "jobhuntin-web": {
        "id": "srv-d63spbogjchc739akan0",
        "updates": {
            "NODE_VERSION": "20",
            "VITE_API_URL": API_URL,
            "VITE_APP_BASE_URL": WEB_URL,
            "VITE_GA_ID": "G-P1QLYH3M13",
        },
    },
    "jobhuntin-seo-engine": {
        "id": "srv-d66aadsr85hc73dastfg",
        "updates": {
            "NODE_VERSION": "20",
            "NODE_ENV": "production",
            "LLM_API_BASE": "https://openrouter.ai/api/v1",
            "LLM_MODEL": "google/gemini-2.0-flash",
            "GOOGLE_SEARCH_CONSOLE_SITE": WEB_URL,
        },
        "remove_keys": ["llm-api-base", "llm-model"],
    },
}


def main() -> int:
    client = require_render_client()
    updated = 0
    errors = []

    for name, cfg in SERVICES.items():
        sid = cfg["id"]
        updates = cfg["updates"]
        remove_keys = cfg.get("remove_keys")
        try:
            client.bulk_set_env_vars(
                sid, updates, preserve_existing=True, remove_keys=remove_keys
            )
            print(f"✅ {name}: updated {len(updates)} env vars")
            updated += 1
        except RenderAPIError as e:
            print(f"❌ {name}: {e}")
            errors.append((name, str(e)))
            continue

    if errors:
        print("\n⚠️  Some services failed. Check RENDER_API_KEY and retry.")
        return 1

    print(f"\n✅ All {updated} services updated.")
    print("\nNext steps:")
    print("1. Ensure REDIS_URL is set on jobhuntin-api (create Redis on Render if needed)")
    print("2. Trigger redeploy: make render-trigger-deploy or via Render dashboard")
    print("3. Verify: https://sorce-api.onrender.com/health")
    return 0


if __name__ == "__main__":
    sys.exit(main())
