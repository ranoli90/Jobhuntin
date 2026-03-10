#!/usr/bin/env python3
"""
Skip Skills step and complete remaining: Work Style → Career Goals → Ready
"""

import asyncio
from playwright.async_api import async_playwright

SESSION_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxZGRmOTc3YS1hNmM2LTRkMzAtODc4Mi1lYjgwNmJhZDYwNTAiLCJlbWFpbCI6InRlc3R1c2VyXzIyNTJkNTE0QHRlc3QuY29tIiwiYXVkIjoiYXV0aGVudGljYXRlZCIsImp0aSI6IjRlOTZkN2MzLTkyYWUtNGMwOC05NDUwLWRhYjYwY2NkNjdkZSIsInNlc3Npb25faWQiOiJmYzJjZmUwZS04ZDc3LTRmNzMtYmRkZS0yNjkwYWE2NDA1Y2IiLCJpYXQiOjE3NzMxMTQ3NTIsIm5iZiI6MTc3MzExNDc1MiwiZXhwIjoxNzczNzE5NTUyfQ.17bFNT76vtC2ri3TQnS2P-H4P2QOmROOgxjrcDkz-lE"


async def skip_and_complete():
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(
            headless=False, args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(viewport={"width": 1280, "height": 720})

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
        console_errors = []
        page.on(
            "console",
            lambda msg: (
                console_errors.append(msg.text) if msg.type == "error" else None
            ),
        )

        print("\n=== Navigating to Onboarding ===")
        await page.goto(
            "http://localhost:5173/app/onboarding",
            wait_until="networkidle",
            timeout=30000,
        )
        await asyncio.sleep(5)

        # Navigate to Skills step
        print("\n=== Navigating to Skills Step ===")
        # Click through Welcome
        try:
            start_btn = page.locator('button:has-text("Start setup")').first
            if await start_btn.is_visible(timeout=3000):
                await start_btn.click()
                await asyncio.sleep(5)
        except:
            pass

        # Click through Preferences
        page_text = await page.inner_text("body")
        if "preferences" in page_text.lower():
            location_input = page.locator('input[placeholder*="location" i]').first
            if await location_input.is_visible(timeout=3000):
                await location_input.fill("San Francisco, CA")
                await asyncio.sleep(2)
            save_btn = page.locator('button:has-text("Save preferences")').first
            if await save_btn.is_visible(timeout=3000):
                await save_btn.click()
                await asyncio.sleep(5)

        # Click through Resume
        page_text = await page.inner_text("body")
        if "resume" in page_text.lower():
            skip_btn = page.locator('button:has-text("Skip for now")').first
            if await skip_btn.is_visible(timeout=3000):
                await skip_btn.click()
                await asyncio.sleep(5)

        # Skip Skills step
        print("\n=== Skipping Skills Step ===")
        await asyncio.sleep(5)
        page_text = await page.inner_text("body")
        if "skill" in page_text.lower():
            skip_btn = page.locator('button:has-text("Skip for now")').first
            if await skip_btn.is_visible(timeout=5000):
                print("  Clicking 'Skip for now' on Skills step")
                await skip_btn.click()
                await asyncio.sleep(8)
                print("  ✓ Skipped Skills step")

        # Work Style Step
        print("\n=== Work Style Step ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle")
        page_text = await page.inner_text("body")
        await page.screenshot(path="/tmp/workstyle_final.png")

        if "work style" in page_text.lower() or "workstyle" in page_text.lower():
            print("  ✓ On Work Style step")

            # Answer questions by clicking radio buttons
            radios = await page.locator('input[type="radio"]').all()
            selected_groups = set()
            selected = 0
            for radio in radios:
                try:
                    if await radio.is_visible(timeout=1000):
                        name = await radio.get_attribute("name") or ""
                        if name and name not in selected_groups:
                            await radio.check()
                            await asyncio.sleep(0.5)
                            selected += 1
                            selected_groups.add(name)
                            if selected >= 4:
                                break
                except:
                    pass

            print(f"  Answered {selected} questions")

            # Fill text inputs
            text_inputs = await page.locator('input[type="text"], textarea').all()
            for inp in text_inputs:
                try:
                    if await inp.is_visible(timeout=2000):
                        value = await inp.input_value()
                        if not value:
                            await inp.fill("I prefer collaborative environments")
                except:
                    pass

            # Click Continue
            continue_btn = page.locator(
                'button:has-text("Continue"), button:has-text("Save work style"), button:has-text("Next")'
            ).first
            if await continue_btn.is_visible(timeout=5000):
                text = await continue_btn.text_content()
                print(f"  Clicking: '{text}'")
                await continue_btn.click()
                await asyncio.sleep(10)
                print("  ✓ Work Style step completed")

        # Career Goals Step
        print("\n=== Career Goals Step ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle")
        page_text = await page.inner_text("body")
        await page.screenshot(path="/tmp/careergoals_final.png")

        if "career" in page_text.lower() or "goal" in page_text.lower():
            print("  ✓ On Career Goals step")

            # Debug: List all inputs
            all_inputs = await page.locator("input, textarea").all()
            print(f"  Found {len(all_inputs)} input/textarea elements")

            # Fill textarea
            textareas = await page.locator("textarea").all()
            filled = False
            for textarea in textareas:
                try:
                    if await textarea.is_visible(timeout=3000):
                        value = await textarea.input_value()
                        if not value:
                            await textarea.fill(
                                "Looking for senior engineering roles in fast-growing tech companies where I can lead technical initiatives and mentor junior developers"
                            )
                            print("  ✓ Filled career goals textarea")
                            filled = True
                            await asyncio.sleep(2)
                            break
                except Exception as e:
                    print(f"  Error filling textarea: {e}")
                    continue

            # Fill text inputs
            text_inputs = await page.locator('input[type="text"]').all()
            for inp in text_inputs:
                try:
                    if await inp.is_visible(timeout=2000):
                        value = await inp.input_value()
                        if not value:
                            await inp.fill("Build innovative products")
                except:
                    pass

            # List all buttons
            all_buttons = await page.locator("button").all()
            print(f"  Found {len(all_buttons)} buttons")
            for i, btn in enumerate(all_buttons[:10]):
                try:
                    if await btn.is_visible(timeout=1000):
                        text = await btn.text_content() or ""
                        print(f"    Button {i}: '{text[:40]}'")
                except:
                    pass

            # Click Continue - try all possible selectors
            continue_clicked = False
            for selector in [
                'button:has-text("Continue")',
                'button:has-text("Next")',
                'button:has-text("Save")',
                'button:has-text("Done")',
            ]:
                try:
                    btn = page.locator(selector).first
                    if await btn.is_visible(timeout=3000):
                        text = await btn.text_content()
                        disabled = await btn.get_attribute("disabled")
                        if not disabled:
                            print(f"  Clicking: '{text}'")
                            await btn.click()
                            await asyncio.sleep(10)
                            await page.wait_for_load_state("networkidle")
                            continue_clicked = True
                            print("  ✓ Career Goals step completed")
                            break
                except:
                    continue

            if not continue_clicked:
                print("  ⚠ Continue button not found or disabled")

        # Ready Step
        print("\n=== Ready Step ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle")
        page_text = await page.inner_text("body")
        await page.screenshot(path="/tmp/ready_final.png")

        if (
            "ready" in page_text.lower()
            or "complete" in page_text.lower()
            or "finish" in page_text.lower()
        ):
            print("  ✓ On Ready step")

            # Click Complete
            all_buttons = await page.locator("button").all()
            for btn in all_buttons:
                try:
                    if await btn.is_visible(timeout=2000):
                        text = await btn.text_content() or ""
                        if (
                            text
                            and ("complete" in text.lower() or "finish" in text.lower())
                            and "back" not in text.lower()
                        ):
                            print(f"  Clicking: '{text}'")
                            await btn.click()
                            await asyncio.sleep(10)
                            print("  ✓ Onboarding completed!")
                            break
                except:
                    pass

        # Verify
        print("\n=== Verification ===")
        await asyncio.sleep(5)
        final_url = page.url
        print(f"Final URL: {final_url}")

        if "/app/dashboard" in final_url:
            print("  ✓ Redirected to dashboard!")
        else:
            print(f"  Still on: {final_url}")

        # Check profile
        try:
            import json
            import urllib.request

            req = urllib.request.Request("http://localhost:8000/me/profile")
            req.add_header("Cookie", f"jobhuntin_auth={SESSION_TOKEN}")
            with urllib.request.urlopen(req) as response:
                profile = json.loads(response.read())
                print(
                    f"\n  has_completed_onboarding: {profile.get('has_completed_onboarding', False)}"
                )
                print(f"  Work Style: {bool(profile.get('work_style', {}))}")
                print(f"  Career Goals: {bool(profile.get('career_goals', {}))}")
        except Exception as e:
            print(f"  Error: {e}")

        await asyncio.sleep(3)
        await browser.close()
        print("\n=== Complete ===")


if __name__ == "__main__":
    asyncio.run(skip_and_complete())
