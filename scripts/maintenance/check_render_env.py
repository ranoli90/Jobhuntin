"""Check and set environment variables on Render using correct API format."""

import os

import httpx
from dotenv import load_dotenv

load_dotenv()

RENDER_API_KEY = os.environ.get("RENDER_API_KEY")
SERVICE_ID = "srv-d63l79hr0fns73boblag"  # sorce-api


def list_env_vars():
    """List all current env vars."""
    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json",
    }

    resp = httpx.get(
        f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars",
        headers=headers,
        timeout=10,
    )
    print(f"List status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        current_keys = []
        for item in data:
            ev = item.get("envVar", {})
            key = ev.get("key")
            if key:
                current_keys.append(key)
        return current_keys
    return []


def update_env_var(key: str, value: str):
    """Try to set/update an env var."""
    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    # Try PUT to update first
    payload = {"value": value}

    # Get the env var ID first
    list_resp = httpx.get(
        f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars",
        headers=headers,
        timeout=10,
    )

    if list_resp.status_code == 200:
        data = list_resp.json()
        for item in data:
            ev = item.get("envVar", {})
            if ev.get("key") == key:
                ev_id = ev.get("id")
                # Update with PUT
                resp = httpx.put(
                    f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars/{ev_id}",
                    headers=headers,
                    json=payload,
                    timeout=10,
                )
                print(f"  Update {key}: {resp.status_code}")
                return resp.status_code in (200, 201, 204)

    return False


def main():
    print("Current environment variables on sorce-api:")
    current = list_env_vars()
    for key in sorted(current):
        print(f"  - {key}")

    # Required env vars from render.yaml
    required = [
        "ENV",
        "DATABASE_URL",  # From database
        "SUPABASE_URL",
        "SUPABASE_SERVICE_KEY",
        "SUPABASE_JWT_SECRET",
        "SUPABASE_STORAGE_BUCKET",
        "LLM_API_BASE",
        "LLM_API_KEY",
        "LLM_MODEL",
        "STRIPE_SECRET_KEY",
        "STRIPE_WEBHOOK_SECRET",
        "STRIPE_PRO_PRICE_ID",
        "STRIPE_TEAM_BASE_PRICE_ID",
        "STRIPE_TEAM_SEAT_PRICE_ID",
        "STRIPE_ENTERPRISE_PRICE_ID",
        "STRIPE_PRO_ANNUAL_PRICE_ID",
        "STRIPE_TEAM_ANNUAL_PRICE_ID",
        "STRIPE_ENTERPRISE_ANNUAL_PRICE_ID",
        "API_V2_PRO_PRICE_ID",
        "API_V2_METERED_PRICE_ID",
        "ADZUNA_APP_ID",
        "ADZUNA_API_KEY",
        "WEBHOOK_SIGNING_SECRET",
        "AGENT_ENABLED",
        "LOG_JSON",
        "LOG_LEVEL",
        "APP_BASE_URL",
        "RESEND_API_KEY",
    ]

    print("\n\nMissing environment variables:")
    missing = []
    for key in required:
        if (
            key not in current and key != "DATABASE_URL"
        ):  # DATABASE_URL comes from linked DB
            missing.append(key)
            print(f"  - {key}")

    print(f"\n\nTotal missing: {len(missing)}")

    # Update APP_BASE_URL first since it's critical for magic link
    if "APP_BASE_URL" in missing:
        print("\n\nSetting APP_BASE_URL...")
        update_env_var("APP_BASE_URL", "https://sorce-web.onrender.com")

    print("\n\n=== MANUAL SETUP REQUIRED ===")
    print("\nGo to https://dashboard.render.com/web/sorce-api/env-vars")
    print("\nAdd these missing environment variables:")
    print("\nPublic values:")
    print("  APP_BASE_URL = https://sorce-web.onrender.com")
    print("  ENV = prod")
    print("  SUPABASE_URL = https://zglovpfwyobbbaaocawz.supabase.co")
    print("  SUPABASE_STORAGE_BUCKET = resumes")
    print("  LLM_API_BASE = https://api.openai.com/v1")
    print("  LLM_MODEL = gpt-4o-mini")
    print("  STRIPE_PRO_PRICE_ID = price_1SyCGDFZF27VelA7tk9UQEos")
    print("  STRIPE_TEAM_BASE_PRICE_ID = price_1SyCGDFZF27VelA70XiRTwvx")
    print("  STRIPE_TEAM_SEAT_PRICE_ID = price_1SyCGEFZF27VelA70HPyVEoz")
    print("  STRIPE_ENTERPRISE_PRICE_ID = price_1SyCGDFZF27VelA7Iv7AnynR")
    print("  STRIPE_PRO_ANNUAL_PRICE_ID = price_1SyCGDFZF27VelA7km8z6pRq")
    print("  STRIPE_TEAM_ANNUAL_PRICE_ID = price_1SyCGEFZF27VelA7hBAzsH02")
    print("  STRIPE_ENTERPRISE_ANNUAL_PRICE_ID = price_1SyCGEFZF27VelA7bJNYVx8B")
    print("  API_V2_PRO_PRICE_ID = price_1SyCGEFZF27VelA7lHr9KhPh")
    print("  API_V2_METERED_PRICE_ID = price_1SyCGEFZF27VelA7G43q2L3t")
    print("  ADZUNA_APP_ID = sorce")
    print("  AGENT_ENABLED = true")
    print("  LOG_JSON = true")
    print("  LOG_LEVEL = INFO")

    print("\nSecret values (from your .env file):")
    secrets = [
        (
            "SUPABASE_SERVICE_KEY",
            os.environ.get("SUPABASE_SERVICE_KEY", "")[:20] + "...",
        ),
        ("SUPABASE_JWT_SECRET", os.environ.get("SUPABASE_JWT_SECRET", "")[:20] + "..."),
        ("LLM_API_KEY", os.environ.get("LLM_API_KEY", "")[:20] + "..."),
        ("STRIPE_SECRET_KEY", os.environ.get("STRIPE_SECRET_KEY", "")[:20] + "..."),
        ("ADZUNA_API_KEY", os.environ.get("ADZUNA_API_KEY", "")[:20] + "..."),
        (
            "WEBHOOK_SIGNING_SECRET",
            os.environ.get("WEBHOOK_SIGNING_SECRET", "")[:20] + "...",
        ),
        ("RESEND_API_KEY", "Get from https://resend.com"),
    ]
    for key, hint in secrets:
        if key not in current:
            print(f"  {key} = {hint}")


if __name__ == "__main__":
    main()
