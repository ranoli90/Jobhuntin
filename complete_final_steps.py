#!/usr/bin/env python3
"""
Complete the final onboarding steps: Work Style → Career Goals → Ready
"""

import asyncio

from playwright.async_api import async_playwright

SESSION_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxZGRmOTc3YS1hNmM2LTRkMzAtODc4Mi1lYjgwNmJhZDYwNTAiLCJlbWFpbCI6InRlc3R1c2VyXzIyNTJkNTE0QHRlc3QuY29tIiwiYXVkIjoiYXV0aGVudGljYXRlZCIsImp0aSI6IjRlOTZkN2MzLTkyYWUtNGMwOC05NDUwLWRhYjYwY2NkNjdkZSIsInNlc3Npb25faWQiOiJmYzJjZmUwZS04ZDc3LTRmNzMtYmRkZS0yNjkwYWE2NDA1Y2IiLCJpYXQiOjE3NzMxMTQ3NTIsIm5iZiI6MTc3MzExNDc1MiwiZXhwIjoxNzczNzE5NTUyfQ.17bFNT76vtC2ri3TQnS2P-H4P2QOmROOgxjrcDkz-lE"


async def complete_final_steps():
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

        # Helper to get step number
        async def get_step_number():
            try:
                step_elem = page.locator(
                    "text=/STEP \\d+ OF \\d+/i, text=/Step \\d+ of \\d+/i"
                ).first
                if await step_elem.is_visible(timeout=2000):
                    text = await step_elem.text_content() or ""
                    import re

                    match = re.search(r"(?:STEP|Step) (\d+)", text, re.IGNORECASE)
                    if match:
                        return int(match.group(1))
            except:
                pass
            return None

        # Navigate to Work Style step
        print("\n=== Navigating to Work Style Step ===")
        await asyncio.sleep(3)
        page_text = await page.inner_text("body")
        current_step = await get_step_number()
        print(f"  Current step: {current_step}")
        print(f"  Page preview: {page_text[:200]}...")

        # If not on step 6, navigate through previous steps
        # Check what step we're actually on by page content
        if "welcome" in page_text.lower() and "start setup" in page_text.lower():
            print("  On Welcome step, clicking through...")
            start_btn = page.locator('button:has-text("Start setup")').first
            if await start_btn.is_visible(timeout=3000):
                await start_btn.click()
                await asyncio.sleep(5)

        if "resume" in page_text.lower() or "upload" in page_text.lower():
            print("  On Resume step, skipping...")
            skip_btn = page.locator('button:has-text("Skip for now")').first
            if await skip_btn.is_visible(timeout=3000):
                await skip_btn.click()
                await asyncio.sleep(5)

        if "skill" in page_text.lower() and "review" in page_text.lower():
            print("  On Skills step, skipping...")
            skip_btn = page.locator('button:has-text("Skip for now")').first
            if await skip_btn.is_visible(timeout=3000):
                await skip_btn.click()
                await asyncio.sleep(5)

        if "contact" in page_text.lower() or "first name" in page_text.lower():
            print("  On Contact step, filling and continuing...")
            first_name = page.locator('input[name*="first" i]').first
            if await first_name.is_visible(timeout=3000):
                await first_name.fill("John")
            last_name = page.locator('input[name*="last" i]').first
            if await last_name.is_visible(timeout=3000):
                await last_name.fill("Doe")
            phone = page.locator('input[type="tel"]').first
            if await phone.is_visible(timeout=3000):
                await phone.fill("+1-555-123-4567")
            continue_btn = page.locator('button:has-text("Continue")').first
            if await continue_btn.is_visible(timeout=3000):
                await continue_btn.click()
                await asyncio.sleep(5)

        if "preferences" in page_text.lower() or "location" in page_text.lower():
            print("  On Preferences step, filling and continuing...")
            location = page.locator('input[placeholder*="location" i]').first
            if await location.is_visible(timeout=3000):
                await location.fill("San Francisco, CA")
                await asyncio.sleep(2)
            save_btn = page.locator('button:has-text("Save preferences")').first
            if await save_btn.is_visible(timeout=3000):
                await save_btn.click()
                await asyncio.sleep(5)

        if current_step and current_step < 6:
            # Quick navigation through previous steps
            page_text = await page.inner_text("body")
            if "welcome" in page_text.lower():
                start_btn = page.locator('button:has-text("Start setup")').first
                if await start_btn.is_visible(timeout=3000):
                    await start_btn.click()
                    await asyncio.sleep(5)
            if "resume" in page_text.lower():
                skip_btn = page.locator('button:has-text("Skip for now")').first
                if await skip_btn.is_visible(timeout=3000):
                    await skip_btn.click()
                    await asyncio.sleep(5)
            if "skill" in page_text.lower():
                skip_btn = page.locator('button:has-text("Skip for now")').first
                if await skip_btn.is_visible(timeout=3000):
                    await skip_btn.click()
                    await asyncio.sleep(5)
            if "contact" in page_text.lower():
                # Fill contact quickly
                first_name = page.locator('input[name*="first" i]').first
                if await first_name.is_visible(timeout=3000):
                    await first_name.fill("John")
                last_name = page.locator('input[name*="last" i]').first
                if await last_name.is_visible(timeout=3000):
                    await last_name.fill("Doe")
                phone = page.locator('input[type="tel"]').first
                if await phone.is_visible(timeout=3000):
                    await phone.fill("+1-555-123-4567")
                continue_btn = page.locator('button:has-text("Continue")').first
                if await continue_btn.is_visible(timeout=3000):
                    await continue_btn.click()
                    await asyncio.sleep(5)
            if "preferences" in page_text.lower():
                # Fill preferences quickly
                location = page.locator('input[placeholder*="location" i]').first
                if await location.is_visible(timeout=3000):
                    await location.fill("San Francisco, CA")
                    await asyncio.sleep(2)
                save_btn = page.locator('button:has-text("Save preferences")').first
                if await save_btn.is_visible(timeout=3000):
                    await save_btn.click()
                    await asyncio.sleep(5)

        # Step 1: Work Style
        print("\n=== Step 1: Work Style ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle")
        current_step = await get_step_number()
        print(f"  Current step: {current_step}")
        page_text = await page.inner_text("body")
        await page.screenshot(path="/tmp/workstyle_final.png")

        if current_step == 6 or "work style" in page_text.lower():
            print("  ✓ On Work Style step")

            # Answer all 7 questions by clicking radio buttons
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

            # Click Save or Continue
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

        # Step 2: Career Goals
        print("\n=== Step 2: Career Goals ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle")
        current_step = await get_step_number()
        print(f"  Current step: {current_step}")
        page_text = await page.inner_text("body")
        await page.screenshot(path="/tmp/careergoals_final.png")

        if (
            current_step == 7
            or "career" in page_text.lower()
            or "goal" in page_text.lower()
        ):
            print("  ✓ On Career Goals step")

            # Wait longer for elements to load
            await asyncio.sleep(3)
            await page.wait_for_load_state("domcontentloaded")

            # Try multiple selectors for textarea
            textarea_filled = False

            # Try standard textarea
            textareas = await page.locator("textarea").all()
            print(f"  Found {len(textareas)} textareas with 'textarea' selector")

            for textarea in textareas:
                try:
                    if await textarea.is_visible(timeout=3000):
                        value = await textarea.input_value()
                        if not value:
                            await textarea.fill(
                                "Looking for senior engineering roles in fast-growing tech companies where I can lead technical initiatives and mentor junior developers"
                            )
                            print("  ✓ Filled career goals textarea")
                            textarea_filled = True
                            await asyncio.sleep(2)
                            break
                except Exception as e:
                    print(f"  Error with textarea: {e}")
                    continue

            # Try contenteditable divs
            if not textarea_filled:
                contenteditable = await page.locator('[contenteditable="true"]').all()
                print(f"  Found {len(contenteditable)} contenteditable elements")
                for elem in contenteditable:
                    try:
                        if await elem.is_visible(timeout=3000):
                            text = await elem.inner_text()
                            if not text or len(text) < 10:
                                await elem.fill(
                                    "Looking for senior engineering roles in fast-growing tech companies where I can lead technical initiatives and mentor junior developers"
                                )
                                print("  ✓ Filled contenteditable element")
                                textarea_filled = True
                                break
                    except:
                        continue

            # Try all input/textarea elements
            if not textarea_filled:
                all_inputs = await page.locator("input, textarea").all()
                print(f"  Found {len(all_inputs)} total input/textarea elements")
                for inp in all_inputs:
                    try:
                        if await inp.is_visible(timeout=2000):
                            tag = await inp.evaluate("el => el.tagName")
                            placeholder = await inp.get_attribute("placeholder") or ""
                            value = await inp.input_value()
                            print(
                                f"    Input: tag={tag}, placeholder='{placeholder[:30]}', value='{value[:30]}'"
                            )
                            if "goal" in placeholder.lower() or (
                                tag.lower() == "textarea" and not value
                            ):
                                await inp.fill(
                                    "Looking for senior engineering roles in fast-growing tech companies where I can lead technical initiatives and mentor junior developers"
                                )
                                print("  ✓ Filled input/textarea")
                                textarea_filled = True
                                break
                    except:
                        pass

            # Fill text inputs if any
            text_inputs = await page.locator('input[type="text"]').all()
            for inp in text_inputs:
                try:
                    if await inp.is_visible(timeout=2000):
                        value = await inp.input_value()
                        if not value:
                            await inp.fill("Build innovative products")
                except:
                    pass

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

        # Step 3: Ready/Complete
        print("\n=== Step 3: Ready/Complete ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle")
        current_step = await get_step_number()
        print(f"  Current step: {current_step}")
        page_text = await page.inner_text("body")
        await page.screenshot(path="/tmp/ready_final.png")

        if (
            current_step == 8
            or "ready" in page_text.lower()
            or "complete" in page_text.lower()
            or "finish" in page_text.lower()
        ):
            print("  ✓ On Ready step")

            # Find and click Complete button
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

        # Verification
        print("\n=== Verification ===")
        await asyncio.sleep(5)
        final_url = page.url
        print(f"Final URL: {final_url}")
        await page.screenshot(path="/tmp/dashboard_final_screenshot.png")

        if "/app/dashboard" in final_url:
            print("  ✓ Successfully redirected to dashboard!")

            # Test dashboard
            await asyncio.sleep(3)
            page_text = await page.inner_text("body")
            if "job" in page_text.lower() or "dashboard" in page_text.lower():
                print("  ✓ Dashboard content loaded")
        else:
            print(f"  Still on: {final_url}")

        # Check console errors
        if console_errors:
            print(f"\n⚠ Console errors: {len(console_errors)}")
            for error in console_errors[:5]:
                print(f"  - {error}")
        else:
            print("\n✓ No console errors")

        # Verify profile
        print("\n=== Profile Verification ===")
        try:
            import json
            import urllib.request

            req = urllib.request.Request("http://localhost:8000/me/profile")
            req.add_header("Cookie", f"jobhuntin_auth={SESSION_TOKEN}")
            with urllib.request.urlopen(req) as response:
                profile = json.loads(response.read())
                print(
                    f"  has_completed_onboarding: {profile.get('has_completed_onboarding', False)}"
                )
                print(f"  Work Style: {bool(profile.get('work_style', {}))}")
                print(f"  Career Goals: {bool(profile.get('career_goals', {}))}")
        except Exception as e:
            print(f"  Error: {e}")

        await asyncio.sleep(3)
        await browser.close()
        print("\n=== Complete ===")


if __name__ == "__main__":
    asyncio.run(complete_final_steps())
