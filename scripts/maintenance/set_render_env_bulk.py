"""Set missing environment variables on Render for sorce-api using bulk PATCH API."""

import os

import httpx
from dotenv import load_dotenv

load_dotenv()

RENDER_API_KEY = os.environ.get("RENDER_API_KEY")
SERVICE_ID = "srv-d63l79hr0fns73boblag"


def set_env_vars_bulk():
    """Set all missing environment variables at once using bulk PATCH API."""
    if not RENDER_API_KEY:
        print("Error: RENDER_API_KEY not found")
        return False

    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    # Build env vars array - only include ones with values
    env_vars = []

    # Plain values
    plain_vars = [
        ("APP_BASE_URL", "https://sorce-web.onrender.com"),
        ("ENV", "prod"),
        (
            "SUPABASE_URL",
            os.environ.get("SUPABASE_URL", "https://zglovpfwyobbbaaocawz.supabase.co"),
        ),
        ("SUPABASE_STORAGE_BUCKET", "resumes"),
        ("LLM_API_BASE", "https://api.openai.com/v1"),
        ("LLM_MODEL", "gpt-4o-mini"),
        ("STRIPE_PRO_PRICE_ID", "price_1SyCGDFZF27VelA7tk9UQEos"),
        ("EMAIL_FROM", "hello@skedaddle.app"),
    ]

    for key, value in plain_vars:
        if value:
            env_vars.append({"key": key, "value": value})
            print(f"[ADD] {key} = {value}")

    # Secret values
    secret_vars = [
        ("SUPABASE_SERVICE_KEY", os.environ.get("SUPABASE_SERVICE_KEY", "")),
        ("SUPABASE_JWT_SECRET", os.environ.get("SUPABASE_JWT_SECRET", "")),
        ("LLM_API_KEY", os.environ.get("LLM_API_KEY", "")),
        ("STRIPE_SECRET_KEY", os.environ.get("STRIPE_SECRET_KEY", "")),
        ("STRIPE_WEBHOOK_SECRET", os.environ.get("STRIPE_WEBHOOK_SECRET", "")),
        ("RESEND_API_KEY", os.environ.get("RESEND_API_KEY", "")),
    ]

    for key, value in secret_vars:
        if value:
            env_vars.append({"key": key, "value": value})
            print(f"[ADD SECRET] {key} = {value[:20]}...")
        else:
            print(f"[SKIP] {key}: No value found")

    if not env_vars:
        print("No env vars to set!")
        return False

    try:
        # Use bulk PATCH endpoint
        print(f"\nSending {len(env_vars)} env vars to Render API...")

        # Try bulk update endpoint
        resp = httpx.put(
            f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars",
            headers=headers,
            json=env_vars,
            timeout=30,
        )

        print(f"Response status: {resp.status_code}")
        print(f"Response body: {resp.text[:500]}")

        if resp.status_code in (200, 201, 204):
            print("\n[✓] Successfully updated environment variables!")
            return True
        else:
            print(f"\n[✗] Failed to update: {resp.status_code}")
            return False

    except Exception as e:
        print(f"\n[✗] Error: {e}")
        return False


if __name__ == "__main__":
    print("Setting environment variables for sorce-api...")
    print("Service ID:", SERVICE_ID)
    print()

    if set_env_vars_bulk():
        print("\nNext steps:")
        print("1. Go to https://dashboard.render.com/web/sorce-api")
        print("2. Click 'Manual Deploy' -> 'Deploy latest commit'")
        print("3. Wait for deployment to complete")
    else:
        print("\nBulk update failed. Trying individual updates...")
