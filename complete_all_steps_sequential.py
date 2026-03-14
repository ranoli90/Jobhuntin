#!/usr/bin/env python3
"""
Complete all onboarding steps sequentially with proper navigation.
"""

import asyncio

from playwright.async_api import async_playwright

SESSION_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxZGRmOTc3YS1hNmM2LTRkMzAtODc4Mi1lYjgwNmJhZDYwNTAiLCJlbWFpbCI6InRlc3R1c2VyXzIyNTJkNTE0QHRlc3QuY29tIiwiYXVkIjoiYXV0aGVudGljYXRlZCIsImp0aSI6IjRlOTZkN2MzLTkyYWUtNGMwOC05NDUwLWRhYjYwY2NkNjdkZSIsInNlc3Npb25faWQiOiJmYzJjZmUwZS04ZDc3LTRmNzMtYmRkZS0yNjkwYWE2NDA1Y2IiLCJpYXQiOjE3NzMxMTQ3NTIsIm5iZiI6MTc3MzExNDc1MiwiZXhwIjoxNzczNzE5NTUyfQ.17bFNT76vtC2ri3TQnS2P-H4P2QOmROOgxjrcDkz-lE"


async def complete_all_steps():
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
        console_messages = []
        page.on(
            "console",
            lambda msg: (
                console_errors.append(msg.text) if msg.type == "error" else None,
                console_messages.append(f"{msg.type}: {msg.text}")
                if msg.type in ["error", "warning"]
                else None,
            ),
        )

        print("\n=== Navigating to Onboarding ===")
        await page.goto(
            "http://localhost:5173/app/onboarding",
            wait_until="networkidle",
            timeout=30000,
        )
        await asyncio.sleep(5)

        # Helper to get step number
        async def get_step_number():
            try:
                # Try multiple selectors
                selectors = [
                    "text=/Step \\d+ of \\d+/i",
                    "text=/STEP \\d+ OF \\d+/i",
                    '*:has-text("Step")',
                ]
                for selector in selectors:
                    try:
                        step_elem = page.locator(selector).first
                        if await step_elem.is_visible(timeout=2000):
                            text = await step_elem.text_content() or ""
                            import re

                            # Match "Step 1 of 8" or "STEP 1 OF 8"
                            match = re.search(
                                r"(?:STEP|Step)\s+(\d+)", text, re.IGNORECASE
                            )
                            if match:
                                step_num = int(match.group(1))
                                print(
                                    f"    [DEBUG] Found step {step_num} using selector: {selector}"
                                )
                                return step_num
                    except:
                        continue

                # Fallback: search all text on page
                page_text = await page.inner_text("body")
                import re

                match = re.search(
                    r"(?:STEP|Step)\s+(\d+)\s+(?:of|OF)", page_text, re.IGNORECASE
                )
                if match:
                    step_num = int(match.group(1))
                    print(f"    [DEBUG] Found step {step_num} from page text")
                    return step_num
            except Exception as e:
                print(f"    [DEBUG] Error getting step number: {e}")
            return None

        # Step 1: Welcome
        print("\n=== Step 1: Welcome ===")
        current_step = await get_step_number()
        print(f"  Current step: {current_step}")
        if current_step == 1:
            start_btn = page.locator('button:has-text("Start setup")').first
            if await start_btn.is_visible(timeout=5000):
                disabled = await start_btn.get_attribute("disabled")
                print(f"  Button disabled: {disabled}")
                if not disabled:
                    print("  Clicking 'Start setup'")
                    # Try JavaScript click as fallback
                    try:
                        await start_btn.click()
                        await asyncio.sleep(2)
                    except:
                        # Try JavaScript execution
                        await page.evaluate(
                            "document.querySelector(\"button:has-text('Start setup')\")?.click()"
                        )
                        await asyncio.sleep(2)

                    # Wait for network activity
                    try:
                        await page.wait_for_load_state("networkidle", timeout=10000)
                    except:
                        pass
                    await asyncio.sleep(5)

                    # Check console errors
                    if console_errors:
                        print(f"    Console errors found: {len(console_errors)}")
                        for err in console_errors[:3]:
                            print(f"      - {err[:100]}")

                    new_step = await get_step_number()
                    print(f"  Step after click: {new_step}")
                    if new_step and new_step > 1:
                        print("  ✓ Welcome completed")
                    else:
                        print("  ⚠ Step didn't advance")
                        # Try clicking again or using different method
                        print("  Trying alternative click method...")
                        await page.evaluate("""
                            const btn = Array.from(document.querySelectorAll("button")).find(b => b.textContent.includes("Start setup"));
                            if (btn) btn.click();
                        """)
                        await asyncio.sleep(5)
                        new_step = await get_step_number()
                        print(f"  Step after alternative click: {new_step}")
                else:
                    print("  ⚠ Button is disabled")

        # Step 2: Preferences (comes before Resume in variant)
        print("\n=== Step 2: Preferences ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle")
        current_step = await get_step_number()
        print(f"  Current step: {current_step}")
        page_text = await page.inner_text("body")

        # Wait for step 2
        if current_step == 1:
            # Still on step 1, wait for transition
            for i in range(10):
                await asyncio.sleep(1)
                current_step = await get_step_number()
                if current_step == 2:
                    break

        if current_step == 2 or "preferences" in page_text.lower():
            print("  ✓ On Preferences step")
            location = page.locator('input[placeholder*="location" i]').first
            if await location.is_visible(timeout=5000):
                await location.fill("San Francisco, CA")
                await asyncio.sleep(3)
            salary_inputs = await page.locator('input[type="number"]').all()
            if len(salary_inputs) > 0:
                await salary_inputs[0].fill("100000")
            if len(salary_inputs) > 1:
                await salary_inputs[1].fill("150000")
            save_btn = page.locator('button:has-text("Save preferences")').first
            if await save_btn.is_visible(timeout=5000):
                print("  Clicking 'Save preferences'")
                await save_btn.click()
                await asyncio.sleep(8)
                await page.wait_for_load_state("networkidle")
                new_step = await get_step_number()
                print(f"  Step after save: {new_step}")
                if new_step and new_step > 2:
                    print("  ✓ Preferences completed")
                else:
                    print("  ⚠ Step didn't advance")

        # Step 3: Resume
        print("\n=== Step 3: Resume ===")
        await asyncio.sleep(5)
        current_step = await get_step_number()
        print(f"  Current step: {current_step}")
        page_text = await page.inner_text("body")

        if current_step == 3 or "resume" in page_text.lower():
            print("  ✓ On Resume step")
            skip_btn = page.locator('button:has-text("Skip for now")').first
            if await skip_btn.is_visible(timeout=5000):
                await skip_btn.click()
                await asyncio.sleep(8)
                print("  ✓ Resume skipped")

        # Step 4: Skills
        print("\n=== Step 4: Skills ===")
        await asyncio.sleep(5)
        current_step = await get_step_number()
        print(f"  Current step: {current_step}")
        page_text = await page.inner_text("body")

        if current_step == 4 or (
            "skill" in page_text.lower() and "review" in page_text.lower()
        ):
            print("  ✓ On Skills step")
            skip_btn = page.locator('button:has-text("Skip for now")').first
            if await skip_btn.is_visible(timeout=5000):
                await skip_btn.click()
                await asyncio.sleep(8)
                print("  ✓ Skills skipped")

        # Step 5: Contact
        print("\n=== Step 5: Contact ===")
        await asyncio.sleep(5)
        current_step = await get_step_number()
        print(f"  Current step: {current_step}")
        page_text = await page.inner_text("body")

        if (
            current_step == 5
            or "contact" in page_text.lower()
            or "first name" in page_text.lower()
        ):
            print("  ✓ On Contact step")
            first_name = page.locator('input[name*="first" i]').first
            if await first_name.is_visible(timeout=5000):
                await first_name.fill("John")
            last_name = page.locator('input[name*="last" i]').first
            if await last_name.is_visible(timeout=5000):
                await last_name.fill("Doe")
            phone = page.locator('input[type="tel"]').first
            if await phone.is_visible(timeout=5000):
                await phone.fill("+1-555-123-4567")
            continue_btn = page.locator('button:has-text("Continue")').first
            if await continue_btn.is_visible(timeout=5000):
                await continue_btn.click()
                await asyncio.sleep(8)
                print("  ✓ Contact completed")

        # Step 6: Work Style
        print("\n=== Step 6: Work Style ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle")
        await page.wait_for_load_state("domcontentloaded")
        current_step = await get_step_number()
        print(f"  Current step: {current_step}")
        page_text = await page.inner_text("body")
        await page.screenshot(path="/tmp/workstyle_sequential.png")

        # Wait until we're actually on step 6
        max_wait = 30
        for i in range(max_wait):
            current_step = await get_step_number()
            if current_step == 6:
                break
            await asyncio.sleep(1)

        if current_step == 6:
            print("  ✓ On Work Style step (verified)")

            # Wait for radio buttons to load
            await asyncio.sleep(3)

            # Answer all questions
            radios = await page.locator('input[type="radio"]').all()
            print(f"  Found {len(radios)} radio buttons")

            selected_groups = set()
            answered = 0
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
                            if answered >= 7:
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

            # Click Save
            await asyncio.sleep(2)
            save_btn = page.locator(
                'button:has-text("Save Work Style"), button:has-text("Save work style"), button:has-text("Continue")'
            ).first
            if await save_btn.is_visible(timeout=5000):
                text = await save_btn.text_content()
                disabled = await save_btn.get_attribute("disabled")
                print(f"  Found button: '{text}', disabled={disabled}")
                if not disabled:
                    print(f"  Clicking: '{text}'")
                    await save_btn.click()
                    await asyncio.sleep(10)
                    await page.wait_for_load_state("networkidle")
                    new_step = await get_step_number()
                    print(f"  ✓ Work Style completed, now on step {new_step}")
                else:
                    print("  ⚠ Button is disabled - may need to answer more questions")
            else:
                print("  ⚠ Save button not found")
        else:
            print(f"  ⚠ Not on step 6, current step: {current_step}")

        # Step 7: Career Goals
        print("\n=== Step 7: Career Goals ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle")
        await page.wait_for_load_state("domcontentloaded")
        current_step = await get_step_number()
        print(f"  Current step: {current_step}")

        # Wait until we're actually on step 7
        max_wait = 30
        for i in range(max_wait):
            current_step = await get_step_number()
            if current_step == 7:
                break
            await asyncio.sleep(1)

        page_text = await page.inner_text("body")
        await page.screenshot(path="/tmp/careergoals_sequential.png")

        if current_step == 7:
            print("  ✓ On Career Goals step (verified)")

            # Wait for elements to load
            await asyncio.sleep(3)

            # Try to find and fill textarea - wait longer
            textarea_filled = False
            textarea = page.locator("textarea").first
            if await textarea.is_visible(timeout=10000):
                value = await textarea.input_value()
                if not value:
                    await textarea.fill(
                        "Looking for senior engineering roles in fast-growing tech companies where I can lead technical initiatives and mentor junior developers"
                    )
                    print("  ✓ Filled career goals textarea")
                    textarea_filled = True
                    await asyncio.sleep(2)

            if not textarea_filled:
                # Try contenteditable
                contenteditable = page.locator('[contenteditable="true"]').first
                if await contenteditable.is_visible(timeout=5000):
                    await contenteditable.fill(
                        "Looking for senior engineering roles in fast-growing tech companies where I can lead technical initiatives and mentor junior developers"
                    )
                    print("  ✓ Filled contenteditable")
                    textarea_filled = True

            # Click Continue
            await asyncio.sleep(2)
            continue_btn = page.locator(
                'button:has-text("Continue"), button:has-text("Next")'
            ).first
            if await continue_btn.is_visible(timeout=5000):
                text = await continue_btn.text_content()
                disabled = await continue_btn.get_attribute("disabled")
                print(f"  Found button: '{text}', disabled={disabled}")
                if not disabled:
                    print(f"  Clicking: '{text}'")
                    await continue_btn.click()
                    await asyncio.sleep(10)
                    await page.wait_for_load_state("networkidle")
                    new_step = await get_step_number()
                    print(f"  ✓ Career Goals completed, now on step {new_step}")
                else:
                    print("  ⚠ Button is disabled")
            else:
                print("  ⚠ Continue button not found")
        else:
            print(f"  ⚠ Not on step 7, current step: {current_step}")

        # Step 8: Ready/Complete
        print("\n=== Step 8: Ready/Complete ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle")
        await page.wait_for_load_state("domcontentloaded")
        current_step = await get_step_number()
        print(f"  Current step: {current_step}")

        # Wait until we're actually on step 8
        max_wait = 30
        for i in range(max_wait):
            current_step = await get_step_number()
            if current_step == 8:
                break
            await asyncio.sleep(1)

        page_text = await page.inner_text("body")
        await page.screenshot(path="/tmp/ready_sequential.png")

        if current_step == 8:
            print("  ✓ On Ready step (verified)")

            # Find Complete button
            all_buttons = await page.locator("button").all()
            print(f"  Found {len(all_buttons)} buttons")
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
                print("  ⚠ Complete button not found or not clickable")
        else:
            print(f"  ⚠ Not on step 8, current step: {current_step}")

        # Final verification
        print("\n=== Final Verification ===")
        await asyncio.sleep(5)
        final_url = page.url
        print(f"Final URL: {final_url}")
        await page.screenshot(path="/tmp/dashboard_final_sequential.png")

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

        if console_errors:
            print(f"\n⚠ Console errors: {len(console_errors)}")
        else:
            print("\n✓ No console errors")

        await asyncio.sleep(3)
        await browser.close()
        print("\n=== Complete ===")


if __name__ == "__main__":
    asyncio.run(complete_all_steps())
