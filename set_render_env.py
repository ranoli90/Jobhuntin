"""Set missing environment variables on Render for sorce-api service."""
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

RENDER_API_KEY = os.environ.get("RENDER_API_KEY")
SERVICE_ID = "srv-d63l79hr0fns73boblag"

def set_env_var(key: str, value: str, is_secret: bool = False):
    """Set or update an environment variable on Render."""
    if not RENDER_API_KEY:
        print(f"Error: RENDER_API_KEY not found")
        return False
    
    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    try:
        payload = {
            "key": key,
            "value": value
        }
        
        # For web services, use the env-vars endpoint with POST to add/update
        resp = httpx.post(
            f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if resp.status_code in (200, 201, 204):
            print(f"  [SET] {key}")
            return True
        elif resp.status_code == 409:
            # Already exists, try to update by finding it first
            list_resp = httpx.get(
                f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars",
                headers=headers,
                timeout=10
            )
            if list_resp.status_code == 200:
                env_vars = list_resp.json()
                for item in env_vars:
                    ev = item.get('envVar', {})
                    if ev.get('key') == key:
                        ev_id = ev.get('id')
                        # Update using PUT
                        update_resp = httpx.put(
                            f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars/{ev_id}",
                            headers=headers,
                            json={"value": value},
                            timeout=10
                        )
                        if update_resp.status_code in (200, 201, 204):
                            print(f"  [UPDATED] {key}")
                            return True
                        break
            print(f"  [ERROR updating {key}] {resp.status_code}: {resp.text[:200]}")
            return False
        else:
            print(f"  [ERROR setting {key}] {resp.status_code}: {resp.text[:200]}")
            return False
                
    except Exception as e:
        print(f"  [ERROR] {key}: {e}")
        return False

def main():
    print("Setting environment variables for sorce-api...")
    
    # Environment variables from render.yaml with their values
    env_vars = [
        # Public values
        ("ENV", "prod", False),
        ("SUPABASE_URL", "https://zglovpfwyobbbaaocawz.supabase.co", False),
        ("SUPABASE_STORAGE_BUCKET", "resumes", False),
        ("LLM_API_BASE", "https://api.openai.com/v1", False),
        ("LLM_MODEL", "gpt-4o-mini", False),
        ("STRIPE_PRO_PRICE_ID", "price_1SyCGDFZF27VelA7tk9UQEos", False),
        ("STRIPE_TEAM_BASE_PRICE_ID", "price_1SyCGDFZF27VelA70XiRTwvx", False),
        ("STRIPE_TEAM_SEAT_PRICE_ID", "price_1SyCGEFZF27VelA70HPyVEoz", False),
        ("STRIPE_ENTERPRISE_PRICE_ID", "price_1SyCGDFZF27VelA7Iv7AnynR", False),
        ("STRIPE_PRO_ANNUAL_PRICE_ID", "price_1SyCGDFZF27VelA7km8z6pRq", False),
        ("STRIPE_TEAM_ANNUAL_PRICE_ID", "price_1SyCGEFZF27VelA7hBAzsH02", False),
        ("STRIPE_ENTERPRISE_ANNUAL_PRICE_ID", "price_1SyCGEFZF27VelA7bJNYVx8B", False),
        ("API_V2_PRO_PRICE_ID", "price_1SyCGEFZF27VelA7lHr9KhPh", False),
        ("API_V2_METERED_PRICE_ID", "price_1SyCGEFZF27VelA7G43q2L3t", False),
        ("ADZUNA_APP_ID", "sorce", False),
        ("AGENT_ENABLED", "true", False),
        ("LOG_JSON", "true", False),
        ("LOG_LEVEL", "INFO", False),
        ("APP_BASE_URL", "https://sorce-web.onrender.com", False),
        
        # Secrets (values from .env)
        ("SUPABASE_SERVICE_KEY", os.environ.get("SUPABASE_SERVICE_KEY", ""), True),
        ("SUPABASE_JWT_SECRET", os.environ.get("SUPABASE_JWT_SECRET", ""), True),
        ("LLM_API_KEY", os.environ.get("LLM_API_KEY", ""), True),
        ("STRIPE_SECRET_KEY", os.environ.get("STRIPE_SECRET_KEY", ""), True),
        ("STRIPE_WEBHOOK_SECRET", os.environ.get("STRIPE_WEBHOOK_SECRET", ""), True),
        ("ADZUNA_API_KEY", os.environ.get("ADZUNA_API_KEY", ""), True),
        ("WEBHOOK_SIGNING_SECRET", os.environ.get("WEBHOOK_SIGNING_SECRET", ""), True),
        ("RESEND_API_KEY", os.environ.get("RESEND_API_KEY", ""), True),
    ]
    
    created = 0
    updated = 0
    failed = 0
    
    for key, value, is_secret in env_vars:
        if not value and is_secret:
            print(f"[SKIP] {key}: No value found in .env")
            failed += 1
            continue
            
        if set_env_var(key, value, is_secret):
            if is_secret:
                print(f"  Value: {'*' * 10}")
            else:
                print(f"  Value: {value[:50]}{'...' if len(value) > 50 else ''}")
            created += 1
        else:
            failed += 1
    
    print(f"\nDone! Created/Updated: {created}, Failed: {failed}")
    print("\nIMPORTANT: You need to manually set RESEND_API_KEY if you have one.")
    print("Get one at https://resend.com and add it as a secret env var.")

if __name__ == "__main__":
    main()
