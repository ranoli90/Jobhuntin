#!/usr/bin/env python3
"""Test dashboard after onboarding completion."""

import asyncio
from playwright.async_api import async_playwright


async def test_dashboard():
    """Test dashboard functionality."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()

        # First authenticate via verify-magic to get session
        page = await context.new_page()

        # Generate fresh token via magic-link endpoint (we'll use a simple approach)
        # For now, let's navigate to login and see if we can get a session
        print("1. Navigating to login...")
        await page.goto("http://localhost:5173/login", wait_until="networkidle")
        await asyncio.sleep(2)

        # Check if there's an email input - if so, we can request magic link
        email_input = page.locator('input[type="email"]').first
        if await email_input.is_visible(timeout=3000):
            await email_input.fill("testuser_2252d514@test.com")
            submit_btn = page.locator(
                'button[type="submit"], button:has-text("Send"), button:has-text("Sign in")'
            ).first
            if await submit_btn.is_visible(timeout=3000):
                await submit_btn.click()
                await asyncio.sleep(3)
                print("   Magic link requested")

        # For testing, let's directly navigate to dashboard with a token
        # We'll use the browser's localStorage/cookies if available
        print("\n2. Testing dashboard...")
        await page.goto("http://localhost:5173/app/dashboard", wait_until="networkidle")
        await asyncio.sleep(3)

        current_url = page.url
        print(f"   Current URL: {current_url}")

        # Collect console errors
        console_errors = []
        page.on(
            "console",
            lambda msg: (
                console_errors.append(f"{msg.type}: {msg.text}")
                if msg.type == "error"
                else None
            ),
        )

        # Check page content
        try:
            page_text = await page.inner_text("body")
            print(f"   Page contains: {page_text[:200]}...")
        except:
            pass

        # Take screenshot
        await page.screenshot(path="/tmp/dashboard_test.png", full_page=True)
        print("   Screenshot: /tmp/dashboard_test.png")

        # Check for specific dashboard elements
        dashboard_indicators = [
            "dashboard",
            "welcome",
            "jobs",
            "applications",
            "profile",
            "matches",
        ]
        found_indicators = []
        for indicator in dashboard_indicators:
            try:
                element = page.locator(f"text=/{indicator}/i").first
                if await element.is_visible(timeout=2000):
                    found_indicators.append(indicator)
            except:
                pass

        if found_indicators:
            print(f"   ✓ Found dashboard elements: {found_indicators}")
        else:
            print("   ⚠ No clear dashboard indicators found")

        # Check console errors
        await asyncio.sleep(2)
        if console_errors:
            print(f"\n   Console errors ({len(console_errors)}):")
            for err in console_errors[:5]:
                print(f"     - {err}")
        else:
            print("   ✓ No console errors")

        await asyncio.sleep(3)
        await browser.close()

        return current_url, console_errors, found_indicators


if __name__ == "__main__":
    asyncio.run(test_dashboard())
