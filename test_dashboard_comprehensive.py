#!/usr/bin/env python3
"""
Comprehensive dashboard testing and issue reporting.
"""

import asyncio
from playwright.async_api import async_playwright
import json

SESSION_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxZGRmOTc3YS1hNmM2LTRkMzAtODc4Mi1lYjgwNmJhZDYwNTAiLCJlbWFpbCI6InRlc3R1c2VyXzIyNTJkNTE0QHRlc3QuY29tIiwiYXVkIjoiYXV0aGVudGljYXRlZCIsImp0aSI6IjRlOTZkN2MzLTkyYWUtNGMwOC05NDUwLWRhYjYwY2NkNjdkZSIsInNlc3Npb25faWQiOiJmYzJjZmUwZS04ZDc3LTRmNzMtYmRkZS0yNjkwYWE2NDA1Y2IiLCJpYXQiOjE3NzMxMTQ3NTIsIm5iZiI6MTc3MzExNDc1MiwiZXhwIjoxNzczNzE5NTUyfQ.17bFNT76vtC2ri3TQnS2P-H4P2QOmROOgxjrcDkz-lE"


async def test_dashboard_comprehensive():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False, args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(viewport={"width": 1280, "height": 720})

        # Set auth cookie
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

        # Track issues
        issues = {
            "console_errors": [],
            "console_warnings": [],
            "missing_elements": [],
            "broken_features": [],
            "cors_errors": [],
            "navigation_issues": [],
        }

        def track_console(msg):
            if msg.type == "error":
                issues["console_errors"].append(msg.text)
                if "CORS" in msg.text:
                    issues["cors_errors"].append(msg.text)
            elif msg.type == "warning":
                issues["console_warnings"].append(msg.text)

        page.on("console", track_console)

        print("=== Dashboard Comprehensive Test ===\n")

        # Step 1: Navigate to Dashboard
        print("1. Navigating to dashboard...")
        await page.goto(
            "http://localhost:5173/app/dashboard",
            wait_until="networkidle",
            timeout=30000,
        )
        await asyncio.sleep(5)

        current_url = page.url
        print(f"   URL: {current_url}")

        if "/login" in current_url:
            print("   ❌ Redirected to login - authentication failed")
            return
        elif "/onboarding" in current_url:
            print("   ❌ Redirected to onboarding - onboarding not complete")
            return
        else:
            print("   ✓ Dashboard loaded successfully")

        # Take screenshot
        await page.screenshot(path="/tmp/dashboard_comprehensive.png", full_page=True)
        print("   ✓ Screenshot saved")

        # Step 2: Check Console Errors
        print("\n2. Checking console errors...")
        unique_errors = list(set(issues["console_errors"]))
        print(f"   Found {len(unique_errors)} unique console errors")

        # Categorize errors
        cors_count = len(issues["cors_errors"])
        if cors_count > 0:
            print(f"   ⚠ CORS errors: {cors_count}")
            print(f"      Example: {issues['cors_errors'][0][:150]}")

        # Step 3: Test Navigation
        print("\n3. Testing Navigation...")
        nav_items = [
            ("Dashboard", "/app/dashboard"),
            ("Jobs", "/app/jobs"),
            ("Applications", "/app/applications"),
            ("Holds", "/app/holds"),
            ("Team", "/app/team"),
            ("Billing", "/app/billing"),
            ("Settings", "/app/settings"),
        ]

        for nav_text, expected_path in nav_items:
            try:
                # Try multiple selectors
                selectors = [
                    f'a:has-text("{nav_text}")',
                    f'[href*="{expected_path}"]',
                    f'button:has-text("{nav_text}")',
                ]

                found = False
                for selector in selectors:
                    try:
                        link = page.locator(selector).first
                        if await link.is_visible(timeout=2000):
                            href = await link.get_attribute("href") or ""
                            print(f"   ✓ {nav_text}: {href}")
                            found = True
                            break
                    except:
                        continue

                if not found:
                    print(f"   ⚠ {nav_text}: Not found")
                    issues["missing_elements"].append(f"Navigation: {nav_text}")
            except Exception as e:
                print(f"   ❌ {nav_text}: Error - {e}")
                issues["navigation_issues"].append(f"{nav_text}: {e}")

        # Step 4: Test Dashboard Features
        print("\n4. Testing Dashboard Features...")

        # Check for key sections
        sections = [
            "Your Dashboard",
            "Find Jobs",
            "Active Applications",
            "Success Rate",
        ]

        for section in sections:
            try:
                elem = page.locator(f"text=/{section}/i").first
                if await elem.is_visible(timeout=2000):
                    print(f"   ✓ Section found: {section}")
                else:
                    print(f"   ⚠ Section not visible: {section}")
                    issues["missing_elements"].append(f"Section: {section}")
            except:
                print(f"   ⚠ Section not found: {section}")
                issues["missing_elements"].append(f"Section: {section}")

        # Step 5: Test Job Search
        print("\n5. Testing Job Search...")
        try:
            # Try to navigate to jobs page
            jobs_link = page.locator('a:has-text("Jobs"), [href*="/app/jobs"]').first
            if await jobs_link.is_visible(timeout=3000):
                print("   ✓ Jobs link found")
                await jobs_link.click()
                await asyncio.sleep(3)
                await page.screenshot(path="/tmp/jobs_page.png")
                print("   ✓ Navigated to jobs page")

                # Look for search input
                search_inputs = [
                    'input[placeholder*="search" i]',
                    'input[placeholder*="job" i]',
                    'input[type="search"]',
                ]

                found_search = False
                for selector in search_inputs:
                    try:
                        inp = page.locator(selector).first
                        if await inp.is_visible(timeout=2000):
                            print(f"   ✓ Job search input found: {selector}")
                            found_search = True
                            break
                    except:
                        continue

                if not found_search:
                    print("   ⚠ Job search input not found")
                    issues["missing_elements"].append("Job search input")
            else:
                print("   ⚠ Jobs link not found")
                issues["missing_elements"].append("Jobs navigation link")
        except Exception as e:
            print(f"   ❌ Job search test failed: {e}")
            issues["broken_features"].append(f"Job search: {e}")

        # Step 6: Test Applications
        print("\n6. Testing Applications...")
        try:
            await page.goto(
                "http://localhost:5173/app/applications",
                wait_until="networkidle",
                timeout=30000,
            )
            await asyncio.sleep(3)
            await page.screenshot(path="/tmp/applications_page.png")
            print("   ✓ Applications page loaded")

            # Check for applications content
            page_text = await page.inner_text("body")
            if "application" in page_text.lower() or "applied" in page_text.lower():
                print("   ✓ Applications content visible")
            else:
                print("   ⚠ Applications content not clearly visible")
        except Exception as e:
            print(f"   ❌ Applications test failed: {e}")
            issues["broken_features"].append(f"Applications: {e}")

        # Step 7: Test Profile/Settings
        print("\n7. Testing Profile/Settings...")
        try:
            await page.goto(
                "http://localhost:5173/app/settings",
                wait_until="networkidle",
                timeout=30000,
            )
            await asyncio.sleep(3)
            await page.screenshot(path="/tmp/settings_page.png")
            print("   ✓ Settings page loaded")
        except Exception as e:
            print(f"   ❌ Settings test failed: {e}")
            issues["broken_features"].append(f"Settings: {e}")

        # Step 8: Generate Report
        print("\n=== Test Summary ===")
        print(f"Console Errors: {len(unique_errors)}")
        print(f"Console Warnings: {len(set(issues['console_warnings']))}")
        print(f"CORS Errors: {cors_count}")
        print(f"Missing Elements: {len(issues['missing_elements'])}")
        print(f"Broken Features: {len(issues['broken_features'])}")
        print(f"Navigation Issues: {len(issues['navigation_issues'])}")

        # Save detailed report
        report = {
            "dashboard_accessible": True,
            "console_errors_count": len(unique_errors),
            "console_warnings_count": len(set(issues["console_warnings"])),
            "cors_errors_count": cors_count,
            "cors_error_examples": list(set(issues["cors_errors"]))[:5],
            "missing_elements": issues["missing_elements"],
            "broken_features": issues["broken_features"],
            "navigation_issues": issues["navigation_issues"],
            "screenshots": [
                "/tmp/dashboard_comprehensive.png",
                "/tmp/jobs_page.png",
                "/tmp/applications_page.png",
                "/tmp/settings_page.png",
            ],
        }

        with open("/tmp/dashboard_test_report.json", "w") as f:
            json.dump(report, f, indent=2)

        print("\n✓ Detailed report saved to /tmp/dashboard_test_report.json")

        await asyncio.sleep(2)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_dashboard_comprehensive())
