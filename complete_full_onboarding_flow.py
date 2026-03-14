#!/usr/bin/env python3
"""
Complete full onboarding flow from authentication to completion.
"""

import asyncio
import json
import urllib.request

from playwright.async_api import async_playwright

EMAIL = "testuser_2252d514@test.com"
# Use existing session token
SESSION_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxZGRmOTc3YS1hNmM2LTRkMzAtODc4Mi1lYjgwNmJhZDYwNTAiLCJlbWFpbCI6InRlc3R1c2VyXzIyNTJkNTE0QHRlc3QuY29tIiwiYXVkIjoiYXV0aGVudGljYXRlZCIsImp0aSI6IjRlOTZkN2MzLTkyYWUtNGMwOC05NDUwLWRhYjYwY2NkNjdkZSIsInNlc3Npb25faWQiOiJmYzJjZmUwZS04ZDc3LTRmNzMtYmRkZS0yNjkwYWE2NDA1Y2IiLCJpYXQiOjE3NzMxMTQ3NTIsIm5iZiI6MTc3MzExNDc1MiwiZXhwIjoxNzczNzE5NTUyfQ.17bFNT76vtC2ri3TQnS2P-H4P2QOmROOgxjrcDkz-lE"


async def complete_full_flow():
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

        console_errors = []
        page.on(
            "console",
            lambda msg: (
                console_errors.append(msg.text) if msg.type == "error" else None
            ),
        )

        # Step 1: Navigate to onboarding (already authenticated)
        print("\n=== Step 1: Navigate to Onboarding ===")
        await page.goto(
            "http://localhost:5173/app/onboarding",
            wait_until="networkidle",
            timeout=30000,
        )
        await asyncio.sleep(5)

        # Dismiss cookie consent if present
        try:
            accept_btn = page.locator('button:has-text("Accept all")').first
            if await accept_btn.is_visible(timeout=2000):
                await accept_btn.click()
                await asyncio.sleep(1)
                print("  ✓ Dismissed cookie consent")
        except:
            pass

        # Helper to get step number
        async def get_step_number():
            try:
                # Try multiple selectors for step indicator
                selectors = [
                    "text=/STEP \\d+ OF \\d+/i",
                    "text=/Step \\d+ of \\d+/i",
                    '[class*="step"]',
                ]
                for selector in selectors:
                    try:
                        step_elem = page.locator(selector).first
                        if await step_elem.is_visible(timeout=2000):
                            text = await step_elem.text_content() or ""
                            import re

                            match = re.search(
                                r"(?:STEP|Step) (\d+)", text, re.IGNORECASE
                            )
                            if match:
                                return int(match.group(1))
                    except:
                        continue
            except:
                pass
            return None

        # Helper to wait for step transition
        async def wait_for_step(target_step, timeout=30):
            for i in range(timeout):
                await asyncio.sleep(1)
                current = await get_step_number()
                if current == target_step:
                    return True
            return False

        # Step 3: Welcome
        print("\n=== Step 3: Welcome Step ===")
        await asyncio.sleep(3)
        page_text = await page.inner_text("body")
        current_step = await get_step_number()
        print(f"  Current step: {current_step}")
        print(f"  Page contains 'welcome': {'welcome' in page_text.lower()}")

        if current_step == 1 or (
            "welcome" in page_text.lower() and "start setup" in page_text.lower()
        ):
            start_btn = page.locator(
                'button:has-text("Start setup"), button:has-text("Get Started")'
            ).first
            if await start_btn.is_visible(timeout=5000):
                print("  Clicking 'Start setup'")
                await start_btn.click()
                await asyncio.sleep(8)
                new_step = await get_step_number()
                print(f"  Step after click: {new_step}")
                print("  ✓ Welcome step completed")

        # Step 4: Resume - Skip
        print("\n=== Step 4: Resume Step (Skipping) ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle")
        page_text = await page.inner_text("body")
        current_step = await get_step_number()
        print(f"  Current step: {current_step}")
        print(f"  Page contains 'resume': {'resume' in page_text.lower()}")

        if (
            current_step == 2
            or current_step == 3
            or ("resume" in page_text.lower() and "upload" in page_text.lower())
        ):
            skip_btn = page.locator('button:has-text("Skip for now")').first
            if await skip_btn.is_visible(timeout=5000):
                print("  Clicking 'Skip for now'")
                await skip_btn.click()
                await asyncio.sleep(8)
                new_step = await get_step_number()
                print(f"  Step after skip: {new_step}")
                print("  ✓ Resume step skipped")

        # Step 5: Skills
        print("\n=== Step 5: Skills Step ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle")
        page_text = await page.inner_text("body")
        current_step = await get_step_number()
        print(f"  Current step: {current_step}")
        print(f"  Page contains 'skill': {'skill' in page_text.lower()}")
        await page.screenshot(path="/tmp/skills_step_start.png")

        if "skill" in page_text.lower() and (
            "review" in page_text.lower() or "add" in page_text.lower()
        ):
            print("  ✓ On Skills step")

            # Check if skills are already present
            if "python" in page_text.lower() or "javascript" in page_text.lower():
                print("  Skills already present, proceeding...")
            else:
                # Click "Add your first skill" button
                add_btn = page.locator(
                    'button:has-text("Add your first skill"), button:has-text("Add a missing skill")'
                ).first
                if await add_btn.is_visible(timeout=5000):
                    print("  Clicking 'Add your first skill'")
                    await add_btn.click()
                    await asyncio.sleep(4)

                # Add skills
                skills = [
                    "Python",
                    "JavaScript",
                    "React",
                    "TypeScript",
                    "FastAPI",
                    "PostgreSQL",
                    "Docker",
                    "AWS",
                ]
                for skill in skills:
                    try:
                        # Re-find input each time
                        await asyncio.sleep(1)
                        skills_input = page.locator('input[type="text"]').first
                        if await skills_input.is_visible(timeout=3000):
                            await skills_input.fill(skill)
                            await asyncio.sleep(0.8)
                            await skills_input.press("Enter")
                            await asyncio.sleep(2)
                            print(f"  ✓ Added skill: {skill}")
                    except Exception as e:
                        print(f"  ⚠ Error adding {skill}: {e}")

            # Click "Save & Continue"
            await asyncio.sleep(3)
            save_continue_btn = page.locator(
                'button:has-text("Save & Continue"), button:has-text("Continue")'
            ).first
            if await save_continue_btn.is_visible(timeout=5000):
                text = await save_continue_btn.text_content()
                disabled = await save_continue_btn.get_attribute("disabled")
                if not disabled:
                    print(f"  Clicking: '{text}'")
                    await save_continue_btn.click()
                    await asyncio.sleep(10)
                    await wait_for_step(5, timeout=15)
                    print("  ✓ Skills step completed")
                else:
                    print("  ⚠ Button is disabled")
            else:
                # Try Skip button
                skip_btn = page.locator('button:has-text("Skip for now")').first
                if await skip_btn.is_visible(timeout=3000):
                    print("  Clicking 'Skip for now'")
                    await skip_btn.click()
                    await asyncio.sleep(8)
                    print("  ✓ Skills step skipped")

        # Step 6: Contact
        print("\n=== Step 6: Contact Step ===")
        await asyncio.sleep(5)
        current_step = await get_step_number()
        print(f"  Current step: {current_step}")

        page_text = await page.inner_text("body")
        if (
            "contact" in page_text.lower()
            or "first name" in page_text.lower()
            or current_step == 4
            or current_step == 5
        ):
            print("  ✓ On Contact step")

            # Fill First Name
            first_name_input = page.locator(
                'input[name*="first" i], input[placeholder*="first" i]'
            ).first
            if await first_name_input.is_visible(timeout=5000):
                await first_name_input.fill("John")
                print("  ✓ Filled First Name")
                await asyncio.sleep(1)

            # Fill Last Name
            last_name_input = page.locator(
                'input[name*="last" i], input[placeholder*="last" i]'
            ).first
            if await last_name_input.is_visible(timeout=5000):
                await last_name_input.fill("Doe")
                print("  ✓ Filled Last Name")
                await asyncio.sleep(1)

            # Fill Phone
            phone_input = page.locator(
                'input[type="tel"], input[name*="phone" i]'
            ).first
            if await phone_input.is_visible(timeout=5000):
                await phone_input.fill("+1-555-123-4567")
                print("  ✓ Filled Phone")
                await asyncio.sleep(1)

            # Click Continue
            continue_btn = page.locator(
                'button:has-text("Continue"), button:has-text("Next")'
            ).first
            if await continue_btn.is_visible(timeout=5000):
                text = await continue_btn.text_content()
                disabled = await continue_btn.get_attribute("disabled")
                if not disabled:
                    print(f"  Clicking: '{text}'")
                    await continue_btn.click()
                    await asyncio.sleep(8)
                    print("  ✓ Contact step completed")

        # Step 7: Preferences
        print("\n=== Step 7: Preferences Step ===")
        await asyncio.sleep(5)
        current_step = await get_step_number()
        print(f"  Current step: {current_step}")

        page_text = await page.inner_text("body")
        if (
            "preferences" in page_text.lower()
            or "location" in page_text.lower()
            or current_step == 2
        ):
            print("  ✓ On Preferences step")

            # Fill Location
            location_input = page.locator(
                'input[placeholder*="location" i], input[role="combobox"]'
            ).first
            if await location_input.is_visible(timeout=5000):
                await location_input.fill("San Francisco, CA")
                await asyncio.sleep(3)
                # Wait for dropdown and select
                try:
                    dropdown_option = page.locator(
                        'div[role="option"], li[role="option"]'
                    ).first
                    if await dropdown_option.is_visible(timeout=2000):
                        await dropdown_option.click()
                        await asyncio.sleep(1)
                except:
                    pass
                print("  ✓ Filled Location")

            # Fill Role Type
            role_inputs = await page.locator('input[role="combobox"]').all()
            if len(role_inputs) > 1:
                await role_inputs[1].fill("Senior Software Engineer")
                await asyncio.sleep(3)
                try:
                    dropdown_option = page.locator(
                        'div[role="option"], li[role="option"]'
                    ).first
                    if await dropdown_option.is_visible(timeout=2000):
                        await dropdown_option.click()
                except:
                    pass
                print("  ✓ Filled Role Type")

            # Fill Salary Min
            salary_inputs = await page.locator('input[type="number"]').all()
            if len(salary_inputs) > 0:
                await salary_inputs[0].fill("100000")
                print("  ✓ Filled Salary Min")
            if len(salary_inputs) > 1:
                await salary_inputs[1].fill("150000")
                print("  ✓ Filled Salary Max")

            # Check Remote
            checkboxes = await page.locator('input[type="checkbox"]').all()
            for checkbox in checkboxes:
                try:
                    label = await checkbox.evaluate(
                        'el => el.closest("label")?.textContent || ""'
                    )
                    if "remote" in label.lower() and await checkbox.is_visible(
                        timeout=1000
                    ):
                        if not await checkbox.is_checked():
                            await checkbox.check()
                            print("  ✓ Checked Remote")
                            break
                except:
                    continue

            # Click Save preferences
            save_btn = page.locator(
                'button:has-text("Save preferences"), button:has-text("Continue")'
            ).first
            if await save_btn.is_visible(timeout=5000):
                text = await save_btn.text_content()
                disabled = await save_btn.get_attribute("disabled")
                if not disabled:
                    print(f"  Clicking: '{text}'")
                    await save_btn.click()
                    await asyncio.sleep(8)
                    print("  ✓ Preferences step completed")

        # Step 8: Work Style
        print("\n=== Step 8: Work Style Step ===")
        await asyncio.sleep(5)
        current_step = await get_step_number()
        print(f"  Current step: {current_step}")

        page_text = await page.inner_text("body")
        if (
            "work style" in page_text.lower()
            or "workstyle" in page_text.lower()
            or current_step == 6
        ):
            print("  ✓ On Work Style step")

            # Answer all questions by clicking radio buttons (one per group)
            radios = await page.locator('input[type="radio"]').all()
            selected_groups = set()
            answered = 0

            print(f"  Found {len(radios)} radio buttons")
            for radio in radios:
                try:
                    if await radio.is_visible(timeout=1000):
                        name = await radio.get_attribute("name") or ""
                        if name and name not in selected_groups:
                            await radio.check()
                            await asyncio.sleep(0.5)
                            answered += 1
                            selected_groups.add(name)
                            print(f"  ✓ Answered question {answered} (group: {name})")
                            if answered >= 7:  # Answer all 7 questions
                                break
                except:
                    pass

            # Fill any text inputs
            text_inputs = await page.locator('input[type="text"], textarea').all()
            for inp in text_inputs:
                try:
                    if await inp.is_visible(timeout=2000):
                        value = await inp.input_value()
                        if not value:
                            await inp.fill("I prefer collaborative environments")
                except:
                    pass

            # Click Save or Continue
            await asyncio.sleep(2)
            continue_btn = page.locator(
                'button:has-text("Save work style"), button:has-text("Continue"), button:has-text("Next")'
            ).first
            if await continue_btn.is_visible(timeout=5000):
                text = await continue_btn.text_content()
                disabled = await continue_btn.get_attribute("disabled")
                if not disabled:
                    print(f"  Clicking: '{text}'")
                    await continue_btn.click()
                    await asyncio.sleep(10)
                    print("  ✓ Work Style step completed")

        # Step 9: Career Goals
        print("\n=== Step 9: Career Goals Step ===")
        await asyncio.sleep(5)
        current_step = await get_step_number()
        print(f"  Current step: {current_step}")

        page_text = await page.inner_text("body")
        if (
            "career" in page_text.lower()
            or "goal" in page_text.lower()
            or current_step == 7
        ):
            print("  ✓ On Career Goals step")

            # Fill textarea
            textareas = await page.locator("textarea").all()
            for textarea in textareas:
                try:
                    if await textarea.is_visible(timeout=3000):
                        value = await textarea.input_value()
                        if not value:
                            await textarea.fill(
                                "Looking for senior engineering roles in fast-growing tech companies where I can lead technical initiatives and mentor junior developers"
                            )
                            print("  ✓ Filled career goals")
                            await asyncio.sleep(2)
                            break
                except:
                    continue

            # Click Continue
            continue_btn = page.locator(
                'button:has-text("Continue"), button:has-text("Next")'
            ).first
            if await continue_btn.is_visible(timeout=5000):
                text = await continue_btn.text_content()
                disabled = await continue_btn.get_attribute("disabled")
                if not disabled:
                    print(f"  Clicking: '{text}'")
                    await continue_btn.click()
                    await asyncio.sleep(10)
                    print("  ✓ Career Goals step completed")

        # Step 10: Ready/Complete
        print("\n=== Step 10: Ready/Complete Step ===")
        await asyncio.sleep(5)
        current_step = await get_step_number()
        print(f"  Current step: {current_step}")

        page_text = await page.inner_text("body")
        if (
            "ready" in page_text.lower()
            or "complete" in page_text.lower()
            or "finish" in page_text.lower()
            or current_step == 8
        ):
            print("  ✓ On Ready step")

            # Find and click Complete button
            all_buttons = await page.locator("button").all()
            complete_clicked = False

            for btn in all_buttons:
                try:
                    if await btn.is_visible(timeout=2000):
                        text = await btn.text_content() or ""
                        if (
                            text
                            and ("complete" in text.lower() or "finish" in text.lower())
                            and "back" not in text.lower()
                            and "restart" not in text.lower()
                        ):
                            disabled = await btn.get_attribute("disabled")
                            if not disabled:
                                print(f"  Clicking: '{text}'")
                                await btn.click()
                                await asyncio.sleep(10)
                                await page.wait_for_load_state("networkidle")
                                complete_clicked = True
                                print("  ✓ Onboarding completed!")
                                break
                except:
                    pass

            if not complete_clicked:
                # Try specific selectors
                complete_btn = page.locator(
                    'button:has-text("Complete Onboarding"), button:has-text("Complete"), button:has-text("Finish")'
                ).first
                if await complete_btn.is_visible(timeout=3000):
                    text = await complete_btn.text_content()
                    print(f"  Clicking: '{text}'")
                    await complete_btn.click()
                    await asyncio.sleep(10)
                    print("  ✓ Onboarding completed!")

        # Step 11: Verification
        print("\n=== Step 11: Verification ===")
        await asyncio.sleep(5)
        final_url = page.url
        print(f"Final URL: {final_url}")
        await page.screenshot(path="/tmp/dashboard_final.png")

        if "/app/dashboard" in final_url:
            print("  ✓ Successfully redirected to dashboard!")

            # Test dashboard
            print("\n=== Testing Dashboard ===")
            await asyncio.sleep(3)
            page_text = await page.inner_text("body")

            if (
                "job" in page_text.lower()
                or "application" in page_text.lower()
                or "dashboard" in page_text.lower()
            ):
                print("  ✓ Dashboard content loaded")

            # Try to browse jobs
            try:
                jobs_link = page.locator(
                    'a:has-text("Jobs"), button:has-text("Browse Jobs"), a[href*="jobs"]'
                ).first
                if await jobs_link.is_visible(timeout=3000):
                    await jobs_link.click()
                    await asyncio.sleep(3)
                    print("  ✓ Clicked Jobs link")
            except:
                pass

            # Check applications
            try:
                apps_link = page.locator(
                    'a:has-text("Applications"), button:has-text("Applications")'
                ).first
                if await apps_link.is_visible(timeout=3000):
                    await apps_link.click()
                    await asyncio.sleep(3)
                    print("  ✓ Clicked Applications link")
            except:
                pass
        else:
            print(f"  ⚠ Still on: {final_url}")

        # Check console errors
        if console_errors:
            print(f"\n⚠ Console errors found: {len(console_errors)}")
            for error in console_errors[:10]:
                print(f"  - {error}")
        else:
            print("\n✓ No console errors detected")

        # Verify profile via API
        print("\n=== Profile Verification ===")
        try:
            # Get cookies from browser
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

        print("\nWaiting 5 seconds before closing...")
        await asyncio.sleep(5)
        await browser.close()
        print("\n=== Full Onboarding Flow Complete ===")


if __name__ == "__main__":
    asyncio.run(complete_full_flow())
