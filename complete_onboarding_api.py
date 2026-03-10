#!/usr/bin/env python3
"""Complete onboarding via API, then test dashboard."""
import asyncio
import httpx
import jwt as pyjwt
from playwright.async_api import async_playwright

USER_ID = "1ddf977a-a6c6-4d30-8782-eb806bad6050"
EMAIL = "testuser_2252d514@test.com"

# Get JWT_SECRET from env or use a test secret
import os
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")

async def create_auth_token():
    """Create a valid JWT token for the user."""
    payload = {
        "sub": USER_ID,
        "email": EMAIL,
        "aud": "authenticated",
        "jti": f"test-{USER_ID}",
        "iat": 1733120050,
        "nbf": 1733120050,
        "exp": 1733206450,  # 24 hours
        "new_user": False
    }
    return pyjwt.encode(payload, JWT_SECRET, algorithm="HS256")

async def complete_onboarding_via_api():
    """Complete onboarding by calling API endpoints directly."""
    token = await create_auth_token()
    
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 1. Save skills
        print("1. Saving skills...")
        skills_data = {
            "skills": [
                {"name": "Python", "category": "programming_language"},
                {"name": "JavaScript", "category": "programming_language"},
                {"name": "React", "category": "framework"},
                {"name": "TypeScript", "category": "programming_language"},
                {"name": "FastAPI", "category": "framework"},
                {"name": "PostgreSQL", "category": "database"},
                {"name": "Docker", "category": "devops"},
                {"name": "AWS", "category": "cloud"}
            ]
        }
        try:
            resp = await client.post(
                "http://localhost:8000/api/user/skills",
                headers=headers,
                json=skills_data,
                timeout=10.0
            )
            print(f"   Skills response: {resp.status_code}")
            if resp.status_code != 200:
                print(f"   Error: {resp.text}")
        except Exception as e:
            print(f"   Skills error: {e}")
        
        # 2. Save work style (check what endpoint exists)
        print("2. Saving work style...")
        work_style_data = {
            "answers": {
                "work_pace": "fast",
                "communication_style": "async",
                "team_size": "medium",
                "company_stage": "growth",
                "documentation": "building",
                "pairing": "occasional",
                "learning": "courses",
                "career_path": "ic"
            }
        }
        # Try to update profile with work style
        try:
            resp = await client.patch(
                f"http://localhost:8000/api/user/profile",
                headers=headers,
                json={"work_style": work_style_data["answers"]},
                timeout=10.0
            )
            print(f"   Work style response: {resp.status_code}")
            if resp.status_code != 200:
                print(f"   Error: {resp.text}")
        except Exception as e:
            print(f"   Work style error: {e}")
        
        # 3. Save career goals
        print("3. Saving career goals...")
        career_goals = "Looking for senior engineering roles in fast-growing tech companies where I can lead technical initiatives and build scalable systems."
        try:
            resp = await client.patch(
                f"http://localhost:8000/api/user/profile",
                headers=headers,
                json={"career_goals": career_goals},
                timeout=10.0
            )
            print(f"   Career goals response: {resp.status_code}")
            if resp.status_code != 200:
                print(f"   Error: {resp.text}")
        except Exception as e:
            print(f"   Career goals error: {e}")
        
        # 4. Mark onboarding as complete
        print("4. Completing onboarding...")
        try:
            resp = await client.post(
                "http://localhost:8000/api/growth/onboarding/complete",
                headers=headers,
                json={},
                timeout=10.0
            )
            print(f"   Complete response: {resp.status_code}")
            if resp.status_code == 200:
                print(f"   ✓ Onboarding completed!")
            else:
                print(f"   Error: {resp.text}")
        except Exception as e:
            print(f"   Complete error: {e}")
        
        return token

async def test_dashboard(token: str):
    """Test the dashboard after onboarding completion."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        
        # Set auth cookie
        await context.add_cookies([{
            'name': 'jobhuntin_auth',
            'value': token,
            'domain': 'localhost',
            'path': '/',
            'httpOnly': True,
            'secure': False,
            'sameSite': 'Lax'
        }])
        
        page = await context.new_page()
        
        # Navigate to dashboard
        print("\n5. Testing dashboard...")
        await page.goto('http://localhost:5173/app/dashboard', wait_until='networkidle')
        await asyncio.sleep(3)
        
        # Check for console errors
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        
        # Check URL
        final_url = page.url
        print(f"   Final URL: {final_url}")
        
        if 'login' in final_url:
            print("   ✗ Still redirected to login")
        else:
            print("   ✓ Dashboard loaded")
        
        # Take screenshot
        await page.screenshot(path='/tmp/dashboard_after_onboarding.png')
        print("   Screenshot saved to /tmp/dashboard_after_onboarding.png")
        
        # Check for errors
        await asyncio.sleep(2)
        if console_errors:
            print(f"   Console errors: {console_errors[:5]}")
        else:
            print("   ✓ No console errors")
        
        # Check page content
        page_text = await page.inner_text('body')
        if 'dashboard' in page_text.lower() or 'welcome' in page_text.lower():
            print("   ✓ Dashboard content visible")
        else:
            print(f"   ⚠ Unexpected content: {page_text[:200]}")
        
        await asyncio.sleep(3)
        await browser.close()
        
        return final_url, console_errors

async def main():
    print("=== Completing Onboarding via API ===\n")
    token = await complete_onboarding_via_api()
    print("\n=== Testing Dashboard ===\n")
    await test_dashboard(token)
    print("\n=== Done ===")

if __name__ == "__main__":
    asyncio.run(main())
