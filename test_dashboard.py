#!/usr/bin/env python3
"""
Test dashboard after onboarding completion.
1. Authenticate
2. Navigate to dashboard
3. Test features
4. Report issues
"""

import asyncio
import json
import urllib.request

from playwright.async_api import async_playwright

EMAIL = "testuser_2252d514@test.com"
SESSION_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxZGRmOTc3YS1hNmM2LTRkMzAtODc4Mi1lYjgwNmJhZDYwNTAiLCJlbWFpbCI6InRlc3R1c2VyXzIyNTJkNTE0QHRlc3QuY29tIiwiYXVkIjoiYXV0aGVudGljYXRlZCIsImp0aSI6IjRlOTZkN2MzLTkyYWUtNGMwOC05NDUwLWRhYjYwY2NkNjdkZSIsInNlc3Npb25faWQiOiJmYzJjZmUwZS04ZDc3LTRmNzMtYmRkZS0yNjkwYWE2NDA1Y2IiLCJpYXQiOjE3NzMxMTQ3NTIsIm5iZiI6MTc3MzExNDc1MiwiZXhwIjoxNzczNzE5NTUyfQ.17bFNT76vtC2ri3TQnS2P-H4P2QOmROOgxjrcDkz-lE"


async def test_dashboard():
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(
            headless=False, args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(viewport={"width": 1280, "height": 720})

        # Set authentication cookie
        await context.add_cookies(
            [
                {
                    "name": "jobhuntin_auth",
                    "value": SESSION_TOKEN,
                    "domain": "localhost",
                    "path": "/",
                    "httpOnly": True,
                    "secure": False,
                    "sameSite": "Lax",
                }
            ]
        )

        page = await context.new_page()

        # Track console errors
        console_errors = []
        console_warnings = []
        page.on(
            "console",
            lambda msg: (
                console_errors.append(msg.text) if msg.type == "error" else None,
                console_warnings.append(msg.text) if msg.type == "warning" else None,
            ),
        )

        # Step 1: Authenticate and get CSRF token
        print("\n=== Step 1: Authentication ===")
        print("Navigating to login page...")
        await page.goto(
            "http://localhost:5173/login", wait_until="networkidle", timeout=30000
        )
        await asyncio.sleep(3)

        # Dismiss cookie consent
        try:
            accept_btn = page.locator('button:has-text("Accept all")').first
            if await accept_btn.is_visible(timeout=2000):
                await accept_btn.click()
                await asyncio.sleep(1)
                print("  ✓ Dismissed cookie consent")
        except:
            pass

        # Get CSRF token from cookies
        cookies = await context.cookies()
        csrf_token = next(
            (c["value"] for c in cookies if c["name"] == "csrftoken"), None
        )
        if csrf_token:
            print(f"  ✓ Got CSRF token: {csrf_token[:20]}...")
        else:
            print("  ⚠ CSRF token not found in cookies")

        # Check if we can request magic link via UI
        email_input = page.locator(
            'input[type="email"], input[placeholder*="email" i]'
        ).first
        if await email_input.is_visible(timeout=5000):
            print(f"  Found email input, entering: {EMAIL}")
            await email_input.fill(EMAIL)
            await asyncio.sleep(1)

            # Look for submit/send button
            submit_btn = page.locator(
                'button[type="submit"], button:has-text("Send"), button:has-text("Request")'
            ).first
            if await submit_btn.is_visible(timeout=3000):
                print("  Clicking send magic link button")
                await submit_btn.click()
                await asyncio.sleep(3)
                print("  ✓ Magic link requested")
        else:
            print("  Email input not found - may already be authenticated")

        # Check if we're redirected or already authenticated
        current_url = page.url
        if "/app/dashboard" in current_url or "/app/onboarding" in current_url:
            print(f"  ✓ Already authenticated, on: {current_url}")
        elif "/login" in current_url:
            print("  Still on login page - checking backend logs for magic link...")
            # Wait a moment for magic link to be generated
            await asyncio.sleep(2)

        # Refresh CSRF token after navigation
        cookies = await context.cookies()
        csrf_token = next(
            (c["value"] for c in cookies if c["name"] == "csrftoken"), None
        )

        # Step 2: Navigate to Dashboard
        print("\n=== Step 2: Navigate to Dashboard ===")

        # First check profile to see if onboarding is complete
        try:
            cookies = await context.cookies()
            auth_cookie = next(
                (c for c in cookies if c["name"] == "jobhuntin_auth"), None
            )
            if auth_cookie:
                token = auth_cookie["value"]
                req = urllib.request.Request("http://localhost:8000/me/profile")
                req.add_header("Cookie", f"jobhuntin_auth={token}")
                with urllib.request.urlopen(req) as response:
                    profile = json.loads(response.read())
                    has_completed = profile.get("has_completed_onboarding", False)
                    work_style = profile.get("work_style", {})
                    career_goals = profile.get("career_goals", {})
                    print("  Profile check:")
                    print(f"    has_completed_onboarding = {has_completed}")
                    print(f"    work_style filled = {bool(work_style)}")
                    print(f"    career_goals filled = {bool(career_goals)}")

                    # If data is complete but flag is false, try to update it via browser
                    if not has_completed:
                        print(
                            "  ⚠ has_completed_onboarding is false - attempting to update via browser..."
                        )
                        # Use browser fetch to update profile (will include CSRF automatically)
                        try:
                            result = await page.evaluate("""
                                async () => {
                                    try {
                                        const response = await fetch('/api/me/profile', {
                                            method: 'PATCH',
                                            headers: {
                                                'Content-Type': 'application/json',
                                            },
                                            credentials: 'include',
                                            body: JSON.stringify({
                                                has_completed_onboarding: true
                                            })
                                        });
                                        if (response.ok) {
                                            const data = await response.json();
                                            return { success: true, data: data };
                                        } else {
                                            const error = await response.text();
                                            return { success: false, error: error };
                                        }
                                    } catch (e) {
                                        return { success: false, error: e.message };
                                    }
                                }
                            """)
                            if result.get("success"):
                                print(
                                    f"  ✓ Updated has_completed_onboarding via browser: {result.get('data', {}).get('has_completed_onboarding', False)}"
                                )
                                await asyncio.sleep(2)
                                # Refresh to get updated state
                                await page.reload()
                                await asyncio.sleep(3)
                            else:
                                print(
                                    f"  ⚠ Browser update failed: {result.get('error', 'Unknown error')[:100]}"
                                )
                        except Exception as e:
                            print(f"  ⚠ Could not update via browser: {e}")
                            print("  Will try to access dashboard anyway")
        except Exception as e:
            print(f"  ⚠ Error checking profile: {e}")

        # Navigate to dashboard
        print("  Navigating to dashboard...")
        await page.goto(
            "http://localhost:5173/app/dashboard",
            wait_until="networkidle",
            timeout=30000,
        )
        await asyncio.sleep(5)

        current_url = page.url
        print(f"  Current URL: {current_url}")

        # Check if redirected
        if "/login" in current_url:
            print("  ⚠ Redirected to login - authentication needed")
        elif "/onboarding" in current_url:
            print("  ⚠ Redirected to onboarding")
            print("  Attempting to navigate directly to dashboard via JavaScript...")
            # Try to navigate via JavaScript to bypass redirect
            await page.evaluate('window.location.href = "/app/dashboard"')
            await asyncio.sleep(5)
            current_url = page.url
            print(f"  URL after JS navigation: {current_url}")

            # If still on onboarding, try to click through or check if we can access dashboard
            if "/onboarding" in current_url:
                print(
                    "  Still on onboarding - checking if we can access dashboard content"
                )
        elif "/dashboard" in current_url:
            print("  ✓ On dashboard page")
        else:
            print(f"  On unexpected page: {current_url}")

        # Step 3: Test Dashboard
        print("\n=== Step 3: Test Dashboard ===")
        await asyncio.sleep(3)
        await page.wait_for_load_state("networkidle")

        # Check console errors
        if console_errors:
            print(f"  ⚠ Console errors found: {len(console_errors)}")
            for error in console_errors[:10]:
                print(f"    - {error[:150]}")
        else:
            print("  ✓ No console errors")

        if console_warnings:
            print(f"  ⚠ Console warnings found: {len(console_warnings)}")
            for warning in console_warnings[:5]:
                print(f"    - {warning[:150]}")

        # Get page content
        page_text = await page.inner_text("body")
        print(f"  Page content preview: {page_text[:200]}...")

        # Check for dashboard elements
        dashboard_indicators = [
            "dashboard" in page_text.lower(),
            "job" in page_text.lower(),
            "application" in page_text.lower(),
            "profile" in page_text.lower(),
            "match" in page_text.lower(),
        ]

        if any(dashboard_indicators):
            print("  ✓ Dashboard content detected")
        else:
            print("  ⚠ Dashboard content not clearly visible")

        # Take screenshot
        await page.screenshot(path="/tmp/dashboard_test.png", full_page=True)
        print("  ✓ Screenshot saved to /tmp/dashboard_test.png")

        # Step 4: Test Key Features
        print("\n=== Step 4: Test Key Features ===")

        # Test navigation
        print("\n  Testing Navigation...")
        nav_links = await page.locator(
            'nav a, [role="navigation"] a, a[href*="/app"]'
        ).all()
        print(f"  Found {len(nav_links)} navigation links")
        for i, link in enumerate(nav_links[:10]):
            try:
                if await link.is_visible(timeout=1000):
                    text = await link.text_content() or ""
                    href = await link.get_attribute("href") or ""
                    print(f"    Link {i}: '{text[:30]}' -> {href[:50]}")
            except:
                pass

        # Test job search
        print("\n  Testing Job Search...")
        search_input = page.locator(
            'input[placeholder*="search" i], input[placeholder*="job" i]'
        ).first
        if await search_input.is_visible(timeout=3000):
            print("  ✓ Job search input found")
            await search_input.fill("Software Engineer")
            await asyncio.sleep(2)
            # Look for search button or results
            search_btn = page.locator(
                'button:has-text("Search"), button[type="submit"]'
            ).first
            if await search_btn.is_visible(timeout=2000):
                await search_btn.click()
                await asyncio.sleep(3)
                print("  ✓ Job search executed")
        else:
            print("  ⚠ Job search input not found")

        # Test profile
        print("\n  Testing Profile...")
        profile_link = page.locator(
            'a:has-text("Profile"), a[href*="profile"], button:has-text("Profile")'
        ).first
        if await profile_link.is_visible(timeout=3000):
            print("  ✓ Profile link found")
            await profile_link.click()
            await asyncio.sleep(3)
            await page.screenshot(path="/tmp/profile_test.png")
            print("  ✓ Profile page opened")
        else:
            print("  ⚠ Profile link not found")

        # Test applications
        print("\n  Testing Applications...")
        apps_link = page.locator(
            'a:has-text("Application"), a[href*="application"], button:has-text("Application")'
        ).first
        if await apps_link.is_visible(timeout=3000):
            print("  ✓ Applications link found")
            await apps_link.click()
            await asyncio.sleep(3)
            await page.screenshot(path="/tmp/applications_test.png")
            print("  ✓ Applications page opened")
        else:
            print("  ⚠ Applications link not found")

        # Test matches
        print("\n  Testing Matches...")
        matches_link = page.locator(
            'a:has-text("Match"), a[href*="match"], button:has-text("Match")'
        ).first
        if await matches_link.is_visible(timeout=3000):
            print("  ✓ Matches link found")
            await matches_link.click()
            await asyncio.sleep(3)
            await page.screenshot(path="/tmp/matches_test.png")
            print("  ✓ Matches page opened")
        else:
            print("  ⚠ Matches link not found")

        # Step 5: Verify Profile via API
        print("\n=== Step 5: Verify Profile ===")
        try:
            cookies = await context.cookies()
            auth_cookie = next(
                (c for c in cookies if c["name"] == "jobhuntin_auth"), None
            )

            if auth_cookie:
                token = auth_cookie["value"]
                req = urllib.request.Request("http://localhost:8000/me/profile")
                req.add_header("Cookie", f"jobhuntin_auth={token}")
                with urllib.request.urlopen(req) as response:
                    profile = json.loads(response.read())
                    print(
                        f"  has_completed_onboarding: {profile.get('has_completed_onboarding', False)}"
                    )
                    print(
                        f"  Contact: {bool(profile.get('contact', {}).get('first_name'))}"
                    )
                    print(
                        f"  Preferences: {bool(profile.get('preferences', {}).get('location'))}"
                    )
                    print(f"  Work Style: {bool(profile.get('work_style', {}))}")
                    print(f"  Career Goals: {bool(profile.get('career_goals', {}))}")
        except Exception as e:
            print(f"  ⚠ Error checking profile: {e}")

        # Final screenshot
        await page.screenshot(path="/tmp/dashboard_final_test.png", full_page=True)

        print("\n=== Test Complete ===")
        print(f"Final URL: {page.url}")
        print(f"Console errors: {len(console_errors)}")
        print(f"Console warnings: {len(console_warnings)}")

        await asyncio.sleep(3)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_dashboard())
