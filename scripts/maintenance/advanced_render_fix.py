"""Advanced Render API debugging and DATABASE_URL fix."""

import json
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

RENDER_API_KEY = os.environ.get("RENDER_API_KEY")
SERVICE_ID = "srv-d63l79hr0fns73boblag"


def test_api_access():
    """Test basic API access and list services."""
    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json",
    }

    try:
        print("Testing API access...")
        resp = httpx.get(
            "https://api.render.com/v1/services", headers=headers, timeout=10
        )
        print(f"Services list status: {resp.status_code}")

        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ API access working. Found {len(data)} services")

            # Find our service
            for service in data:
                if service.get("service", {}).get("id") == SERVICE_ID:
                    print(
                        f"✅ Found sorce-api: {service.get('service', {}).get('name')}"
                    )
                    return True

            print("❌ sorce-api not found in services list")
            return False
        else:
            print(f"❌ API access failed: {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def get_service_details():
    """Get detailed service info."""
    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json",
    }

    try:
        print(f"\nGetting service details for {SERVICE_ID}...")
        resp = httpx.get(
            f"https://api.render.com/v1/services/{SERVICE_ID}",
            headers=headers,
            timeout=10,
        )
        print(f"Service details status: {resp.status_code}")

        if resp.status_code == 200:
            data = resp.json()
            service = data.get("service", {})
            print(f"✅ Service: {service.get('name')}")
            print(f"   Status: {service.get('status')}")
            print(f"   Type: {service.get('serviceType')}")
            return data
        else:
            print(f"❌ Failed: {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def list_env_vars():
    """List current environment variables."""
    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json",
    }

    try:
        print("\nListing environment variables...")
        resp = httpx.get(
            f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars",
            headers=headers,
            timeout=10,
        )
        print(f"Env vars status: {resp.status_code}")

        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ Found {len(data)} environment variables")

            for item in data:
                ev = item.get("envVar", {})
                key = ev.get("key", "")
                value = ev.get("value", "")
                if "DATABASE" in key or "DB" in key:
                    print(f"   {key}: {value[:50] if value else 'NOT SET'}...")

            return data
        else:
            print(f"❌ Failed: {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def update_env_var_patch():
    """Try PATCH method to update env var."""
    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ Error: DATABASE_URL not set in .env")
        return False

    # Try PATCH to update existing or create new
    payload = {"envVars": [{"key": "DATABASE_URL", "value": db_url}]}

    try:
        print("\nTrying PATCH method...")
        resp = httpx.patch(
            f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars",
            headers=headers,
            json=payload,
            timeout=10,
        )
        print(f"PATCH status: {resp.status_code}")
        print(f"Response: {resp.text[:500]}")

        if resp.status_code in (200, 204):
            print("✅ DATABASE_URL updated via PATCH!")
            return True
        else:
            print("❌ PATCH failed")
            return False
    except Exception as e:
        print(f"❌ PATCH error: {e}")
        return False


def update_env_var_put():
    """Try PUT method for specific env var."""
    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ Error: DATABASE_URL not set in .env")
        return False

    # Try PUT with specific env var ID
    payload = {"key": "DATABASE_URL", "value": db_url}

    try:
        print("\nTrying PUT method...")
        # Try different endpoints
        endpoints = [
            f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars/DATABASE_URL",
            f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars",
        ]

        for endpoint in endpoints:
            print(f"Trying: {endpoint}")
            resp = httpx.put(endpoint, headers=headers, json=payload, timeout=10)
            print(f"PUT status: {resp.status_code}")

            if resp.status_code in (200, 201, 204):
                print("✅ DATABASE_URL updated via PUT!")
                return True
            elif resp.status_code != 404:
                print(f"Response: {resp.text[:200]}")

        return False
    except Exception as e:
        print(f"❌ PUT error: {e}")
        return False


def create_env_var_post():
    """Try POST with different payload structure."""
    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ Error: DATABASE_URL not set in .env")
        return False

    # Try different payload structures
    payloads = [
        {"key": "DATABASE_URL", "value": db_url},
        {"envVar": {"key": "DATABASE_URL", "value": db_url}},
        {"environmentVariable": {"key": "DATABASE_URL", "value": db_url}},
    ]

    try:
        print("\nTrying POST with different payloads...")

        for i, payload in enumerate(payloads):
            print(f"\nPayload {i + 1}: {json.dumps(payload, indent=2)}")
            resp = httpx.post(
                f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars",
                headers=headers,
                json=payload,
                timeout=10,
            )
            print(f"POST status: {resp.status_code}")

            if resp.status_code in (200, 201, 204):
                print("✅ DATABASE_URL created via POST!")
                return True
            elif resp.status_code == 400:
                print(f"Bad request: {resp.text[:300]}")
            elif resp.status_code == 405:
                print("Method not allowed - trying next payload...")

        return False
    except Exception as e:
        print(f"❌ POST error: {e}")
        return False


def trigger_deploy():
    """Trigger a new deploy after setting env vars."""
    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    try:
        print("\nTriggering deploy...")
        resp = httpx.post(
            f"https://api.render.com/v1/services/{SERVICE_ID}/deploys",
            headers=headers,
            json={},
            timeout=10,
        )
        print(f"Deploy status: {resp.status_code}")

        if resp.status_code in (200, 201):
            data = resp.json()
            deploy = data.get("deploy", {})
            print(f"✅ Deploy triggered! ID: {deploy.get('id')}")
            return True
        else:
            print(f"❌ Deploy failed: {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Deploy error: {e}")
        return False


def main():
    print("=" * 70)
    print("Advanced Render API Debugging")
    print("=" * 70)

    if not RENDER_API_KEY:
        print("❌ RENDER_API_KEY not found in .env")
        return

    # Test API access
    if not test_api_access():
        return

    # Get service details
    get_service_details()

    # List current env vars
    list_env_vars()

    # Try different methods to set DATABASE_URL
    print("\n" + "=" * 70)
    print("Attempting to set DATABASE_URL...")
    print("=" * 70)

    success = False

    # Try PATCH first
    if update_env_var_patch():
        success = True

    # Try PUT
    if not success and update_env_var_put():
        success = True

    # Try POST with different payloads
    if not success and create_env_var_post():
        success = True

    if success:
        print("\n✅ DATABASE_URL set successfully!")
        trigger_deploy()
    else:
        print("\n❌ All API methods failed. Manual intervention required.")
        print("\nManual steps:")
        print("1. https://dashboard.render.com/web/sorce-api/env-vars")
        print("2. Add DATABASE_URL: <YOUR_DATABASE_URL>")
        print("3. Save and deploy")


if __name__ == "__main__":
    main()
