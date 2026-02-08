"""Fix DATABASE_URL for sorce-api service"""
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

RENDER_API_KEY = os.environ.get("RENDER_API_KEY")
SERVICE_ID = "srv-d63l79hr0fns73boblag"

def get_database_info():
    """Get database connection info from Render"""
    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json",
    }

    try:
        # List databases
        resp = httpx.get("https://api.render.com/v1/databases", headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            print("Available databases:")
            for db in data:
                db_data = db.get('database', {})
                print(f"  - {db_data.get('name')} (ID: {db_data.get('id')})")
                print(f"    Connection: {db_data.get('connectionString', 'N/A')[:50]}...")
            return data
    except Exception as e:
        print(f"Error: {e}")
    return None

def check_current_env():
    """Check current env vars on sorce-api"""
    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json",
    }

    try:
        resp = httpx.get(
            f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars",
            headers=headers,
            timeout=10
        )

        if resp.status_code == 200:
            data = resp.json()
            print("Current environment variables:")
            for item in data:
                ev = item.get('envVar', {})
                key = ev.get('key', '')
                value = ev.get('value', '')
                if 'DATABASE' in key or 'DB' in key:
                    print(f"  {key}: {value[:50] if value else 'NOT SET'}...")
            return data
    except Exception as e:
        print(f"Error checking env: {e}")
    return None

def set_database_url():
    """Set DATABASE_URL directly"""
    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    # The database connection string from Supabase (sorce-db)
    # Using Transaction Pooler (port 6543) for better connection management on Render
    # Format: postgres://[user].[project_ref]:[password]@[pooler_host]:6543/[db_name]
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ Error: DATABASE_URL not found in environment variables.")
        print("Please set DATABASE_URL in your .env file.")
        return False

    payload = {
        "key": "DATABASE_URL",
        "value": db_url
    }

    try:
        print("\nSetting DATABASE_URL...")
        resp = httpx.post(
            f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars",
            headers=headers,
            json=payload,
            timeout=10
        )

        print(f"Status: {resp.status_code}")
        if resp.status_code in (200, 201, 204):
            print("✅ DATABASE_URL set successfully!")
            return True
        else:
            print(f"❌ Failed: {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("=" * 60)
    print("Fixing DATABASE_URL for sorce-api")
    print("=" * 60)

    if not RENDER_API_KEY:
        print("Error: RENDER_API_KEY not found in .env")
        return

    # Check current state
    print("\n1. Checking current environment...")
    check_current_env()

    # Get database info
    print("\n2. Checking database info...")
    get_database_info()

    # Try to set DATABASE_URL
    print("\n3. Setting DATABASE_URL...")
    if set_database_url():
        print("\n✅ Done! DATABASE_URL has been set.")
        print("\nNext steps:")
        print("1. Go to https://dashboard.render.com/web/sorce-api")
        print("2. Click 'Manual Deploy' -> 'Deploy latest commit'")
        print("3. The service should start successfully")
    else:
        print("\n❌ Could not set DATABASE_URL via API.")
        print("\nManual fix:")
        print("1. Go to https://dashboard.render.com/web/sorce-api/env-vars")
        print("2. Add/Update DATABASE_URL with:")
        print("   postgresql://postgres:SorceDB2026Secure@db.zglovpfwyobbbaaocawz.supabase.co:5432/postgres")
        print("3. Deploy the service")

if __name__ == "__main__":
    main()
