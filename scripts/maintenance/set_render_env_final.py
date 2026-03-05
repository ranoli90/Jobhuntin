"""Set missing environment variables on Render for sorce-api."""

import os

import httpx
from dotenv import load_dotenv

load_dotenv()

RENDER_API_KEY = os.environ.get("RENDER_API_KEY")
SERVICE_ID = "srv-d63l79hr0fns73boblag"


def set_env_var(key: str, value: str):
    """Set or update an environment variable on Render web service."""
    if not RENDER_API_KEY:
        print("Error: RENDER_API_KEY not found")
        return False

    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    try:
        # First check if it exists
        list_resp = httpx.get(
            f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars",
            headers=headers,
            timeout=10,
        )

        existing_id = None
        if list_resp.status_code == 200:
            data = list_resp.json()
            for item in data:
                ev = item.get("envVar", {})
                if ev.get("key") == key:
                    existing_id = ev.get("id")
                    break

        if existing_id:
            # Update existing - PUT with just the value
            resp = httpx.put(
                f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars/{existing_id}",
                headers=headers,
                json={"value": value},
                timeout=10,
            )
            if resp.status_code in (200, 201, 204):
                print(f"  [UPDATED] {key}")
                return True
            else:
                print(f"  [ERROR updating {key}] {resp.status_code}: {resp.text[:200]}")
                return False
        else:
            # Create new - POST with key and value
            resp = httpx.post(
                f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars",
                headers=headers,
                json={"key": key, "value": value},
                timeout=10,
            )
            if resp.status_code in (200, 201, 204):
                print(f"  [CREATED] {key}")
                return True
            elif resp.status_code == 409:
                # Conflict - var exists but we didn't find it, try force update
                print(f"  [CONFLICT] {key}, retrying...")
                return False
            else:
                print(f"  [ERROR creating {key}] {resp.status_code}: {resp.text[:200]}")
                return False

    except Exception as e:
        print(f"  [ERROR] {key}: {e}")
        return False


def main():
    print("Setting missing environment variables for sorce-api...")

    # Get values from .env
    env_vars = [
        ("APP_BASE_URL", "https://sorce-web.onrender.com"),
        ("ENV", "prod"),
        (
            "SUPABASE_URL",
            os.environ.get("SUPABASE_URL", "https://zglovpfwyobbbaaocawz.supabase.co"),
        ),
        ("SUPABASE_SERVICE_KEY", os.environ.get("SUPABASE_SERVICE_KEY", "")),
        ("SUPABASE_JWT_SECRET", os.environ.get("SUPABASE_JWT_SECRET", "")),
        ("SUPABASE_STORAGE_BUCKET", "resumes"),
        ("LLM_API_BASE", "https://api.openai.com/v1"),
        ("LLM_API_KEY", os.environ.get("LLM_API_KEY", "")),
        ("LLM_MODEL", "gpt-4o-mini"),
        ("STRIPE_SECRET_KEY", os.environ.get("STRIPE_SECRET_KEY", "")),
        ("STRIPE_WEBHOOK_SECRET", os.environ.get("STRIPE_WEBHOOK_SECRET", "")),
        ("STRIPE_PRO_PRICE_ID", "price_1SyCGDFZF27VelA7tk9UQEos"),
        ("RESEND_API_KEY", os.environ.get("RESEND_API_KEY", "")),
        ("EMAIL_FROM", "hello@skedaddle.app"),
    ]

    success = 0
    failed = 0

    for key, value in env_vars:
        if not value:
            print(f"[SKIP] {key}: No value found")
            failed += 1
            continue

        # Mask secrets in output
        display_value = value[:20] + "..." if len(value) > 30 else value
        print(f"\nSetting {key} = {display_value}")

        if set_env_var(key, value):
            success += 1
        else:
            failed += 1

    print(f"\n\nDone! Success: {success}, Failed: {failed}")

    if failed > 0:
        print("\nFailed to set some variables via API.")
        print(
            "Please manually add them at: https://dashboard.render.com/web/sorce-api/env-vars"
        )


if __name__ == "__main__":
    main()
