#!/usr/bin/env python3
"""
Complete onboarding using JavaScript execution as fallback for button clicks.
Checks console errors and completes all remaining steps.
"""

import asyncio
from playwright.async_api import async_playwright

SESSION_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxZGRmOTc3YS1hNmM2LTRkMzAtODc4Mi1lYjgwNmJhZDYwNTAiLCJlbWFpbCI6InRlc3R1c2VyXzIyNTJkNTE0QHRlc3QuY29tIiwiYXVkIjoiYXV0aGVudGljYXRlZCIsImp0aSI6IjRlOTZkN2MzLTkyYWUtNGMwOC05NDUwLWRhYjYwY2NkNjdkZSIsInNlc3Npb25faWQiOiJmYzJjZmUwZS04ZDc3LTRmNzMtYmRkZS0yNjkwYWE2NDA1Y2IiLCJpYXQiOjE3NzMxMTQ3NTIsIm5iZiI6MTc3MzExNDc1MiwiZXhwIjoxNzczNzE5NTUyfQ.17bFNT76vtC2ri3TQnS2P-H4P2QOmROOgxjrcDkz-lE"


async def complete_with_js():
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

        # Track console errors and warnings
        console_errors = []
        console_warnings = []
        page.on(
            "console",
            lambda msg: (
                console_errors.append(msg.text) if msg.type == "error" else None,
                console_warnings.append(msg.text) if msg.type == "warning" else None,
            ),
        )

        print("\n=== Navigating to Onboarding ===")
        await page.goto(
            "http://localhost:5173/app/onboarding",
            wait_until="networkidle",
            timeout=30000,
        )
        await asyncio.sleep(5)

        # Dismiss cookie consent
        try:
            accept_btn = page.locator('button:has-text("Accept all")').first
            if await accept_btn.is_visible(timeout=2000):
                await accept_btn.click()
                await asyncio.sleep(1)
        except:
            pass

        # Helper to get step number
        async def get_step_number():
            try:
                step_elem = page.locator("text=/Step \\d+ of \\d+/i").first
                if await step_elem.is_visible(timeout=2000):
                    text = await step_elem.text_content() or ""
                    import re

                    match = re.search(r"Step\s+(\d+)", text, re.IGNORECASE)
                    if match:
                        return int(match.group(1))
            except:
                pass
            return None

        # Helper to click button with JS fallback
        async def click_button_robust(selector, description):
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=5000):
                    disabled = await btn.get_attribute("disabled")
                    if not disabled:
                        print(f"  Clicking '{description}' via Playwright")
                        await btn.click()
                        return True
            except:
                pass

            # Try JavaScript execution
            try:
                result = await page.evaluate(f"""
                    (() => {{
                        const btn = document.querySelector('{selector}') || 
                                   Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('{description.split()[0]}'));
                        if (btn && !btn.disabled) {{
                            btn.click();
                            return true;
                        }}
                        return false;
                    }})()
                """)
                if result:
                    print(f"  Clicked '{description}' via JavaScript")
                    return True
            except Exception as e:
                print(f"  JS click failed: {e}")

            return False

        # Step 1: Check Console Errors
        print("\n=== Step 1: Checking Console Errors ===")
        await asyncio.sleep(2)
        if console_errors:
            print(f"  ⚠ Found {len(console_errors)} console errors:")
            for i, error in enumerate(console_errors[:10]):
                print(f"    {i + 1}. {error[:150]}")
            await page.screenshot(path="/tmp/console_errors.png")
        else:
            print("  ✓ No console errors detected")

        if console_warnings:
            print(
                f"  ⚠ Found {len(console_warnings)} console warnings (showing first 5):"
            )
            for i, warning in enumerate(console_warnings[:5]):
                print(f"    {i + 1}. {warning[:150]}")

        # Navigate through initial steps to get to Skills
        print("\n=== Navigating to Skills Step ===")
        current_step = await get_step_number()
        print(f"  Current step: {current_step}")

        # Welcome
        if current_step == 1:
            page_text = await page.inner_text("body")
            if "welcome" in page_text.lower() or "start setup" in page_text.lower():
                await click_button_robust(
                    'button:has-text("Start setup")', "Start setup"
                )
                await asyncio.sleep(8)
                current_step = await get_step_number()
                print(f"  Step after Welcome: {current_step}")

        # Preferences
        if current_step == 2 or current_step == 1:
            page_text = await page.inner_text("body")
            if "preferences" in page_text.lower() or "location" in page_text.lower():
                print("  On Preferences step, filling...")
                location = page.locator('input[placeholder*="location" i]').first
                if await location.is_visible(timeout=5000):
                    await location.fill("San Francisco, CA")
                    await asyncio.sleep(3)
                salary_inputs = await page.locator('input[type="number"]').all()
                if len(salary_inputs) > 0:
                    await salary_inputs[0].fill("100000")
                if len(salary_inputs) > 1:
                    await salary_inputs[1].fill("150000")
                await click_button_robust(
                    'button:has-text("Save preferences")', "Save preferences"
                )
                await asyncio.sleep(8)
                current_step = await get_step_number()
                print(f"  Step after Preferences: {current_step}")

        # Resume
        if current_step == 3 or current_step == 2:
            page_text = await page.inner_text("body")
            if "resume" in page_text.lower():
                print("  On Resume step, skipping...")
                await click_button_robust(
                    'button:has-text("Skip for now")', "Skip for now"
                )
                await asyncio.sleep(8)
                current_step = await get_step_number()
                print(f"  Step after Resume: {current_step}")

        # Step 2: Skills
        print("\n=== Step 2: Skills Step ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle")
        current_step = await get_step_number()
        print(f"  Current step: {current_step}")
        page_text = await page.inner_text("body")
        await page.screenshot(path="/tmp/skills_step_check.png")

        if current_step == 4 or "skill" in page_text.lower():
            print("  ✓ On Skills step")

            # Check if skills are already present
            if (
                "python" not in page_text.lower()
                and "javascript" not in page_text.lower()
            ):
                # Click "Add your first skill" button
                add_btn_clicked = await click_button_robust(
                    'button:has-text("Add your first skill"), button:has-text("Add a missing skill")',
                    "Add skill",
                )
                if add_btn_clicked:
                    await asyncio.sleep(4)
                    print("  ✓ Clicked add skill button")

                # Add skills one by one
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
                            # Verify skill was added
                            page_text_after = await page.inner_text("body")
                            if skill.lower() in page_text_after.lower():
                                print(f"  ✓ Added skill: {skill}")
                            else:
                                print(f"  ⚠ Skill {skill} may not have been added")
                    except Exception as e:
                        print(f"  ⚠ Error adding {skill}: {e}")
            else:
                print("  Skills already present")

            # Click "Save & Continue" - try multiple methods including direct nextStep call
            await asyncio.sleep(3)
            save_clicked = False

            # Method 1: Playwright click
            save_btn = page.locator(
                'button:has-text("Save & Continue"), button:has-text("Continue")'
            ).first
            if await save_btn.is_visible(timeout=5000):
                disabled = await save_btn.get_attribute("disabled")
                if not disabled:
                    print("  Clicking 'Save & Continue' via Playwright")
                    await save_btn.click()
                    save_clicked = True

            # Method 2: JavaScript click
            if not save_clicked:
                result = await page.evaluate("""
                    (() => {
                        const buttons = Array.from(document.querySelectorAll('button'));
                        const saveBtn = buttons.find(b => {
                            const text = b.textContent || '';
                            return (text.includes('Save & Continue') || text.includes('Continue')) && !b.disabled;
                        });
                        if (saveBtn) {
                            saveBtn.click();
                            return true;
                        }
                        return false;
                    })()
                """)
                if result:
                    print("  Clicked 'Save & Continue' via JavaScript")
                    save_clicked = True

            # Method 3: Try to find and click the actual button that handles skills save
            if not save_clicked:
                # Look for button with specific handlers
                all_buttons = await page.locator("button").all()
                for btn in all_buttons:
                    try:
                        if await btn.is_visible(timeout=1000):
                            text = await btn.text_content() or ""
                            if (
                                ("save" in text.lower() or "continue" in text.lower())
                                and "skip" not in text.lower()
                                and "back" not in text.lower()
                            ):
                                disabled = await btn.get_attribute("disabled")
                                if not disabled:
                                    print(f"  Trying button: '{text}'")
                                    await btn.click()
                                    await asyncio.sleep(8)
                                    new_step = await get_step_number()
                                    if new_step and new_step > 4:
                                        save_clicked = True
                                        print(f"  ✓ Advanced to step {new_step}")
                                        break
                    except:
                        pass

            if save_clicked:
                await asyncio.sleep(10)
                await page.wait_for_load_state("networkidle")
                new_step = await get_step_number()
                print(f"  Step after Skills: {new_step}")
                if new_step and new_step > 4:
                    print("  ✓ Skills step completed")
                else:
                    print("  ⚠ Step didn't advance, trying Skip...")
                    skip_clicked = await click_button_robust(
                        'button:has-text("Skip for now")', "Skip for now"
                    )
                    if skip_clicked:
                        await asyncio.sleep(10)
                        await page.wait_for_load_state("networkidle")
                        new_step = await get_step_number()
                        print(f"  Step after Skip: {new_step}")
                        if new_step and new_step > 4:
                            print(
                                f"  ✓ Skills step skipped, advanced to step {new_step}"
                            )
                        else:
                            print("  ⚠ Skip didn't advance step either")
            else:
                # Try Skip
                print("  Save button not found, trying Skip...")
                await click_button_robust(
                    'button:has-text("Skip for now")', "Skip for now"
                )
                await asyncio.sleep(8)

        # Step 3: Work Style
        print("\n=== Step 3: Work Style Step ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle")
        current_step = await get_step_number()
        print(f"  Current step: {current_step}")
        page_text = await page.inner_text("body")
        await page.screenshot(path="/tmp/workstyle_step_check.png")

        # Wait for step 6
        max_wait = 30
        for i in range(max_wait):
            current_step = await get_step_number()
            if current_step == 6:
                break
            await asyncio.sleep(1)

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
                            # Click via JavaScript if needed
                            try:
                                await radio.check()
                            except:
                                await page.evaluate(f'''
                                    document.querySelector('input[type="radio"][name="{name}"]')?.click();
                                ''')
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

            # Click Save Work Style
            await asyncio.sleep(2)
            save_clicked = await click_button_robust(
                'button:has-text("Save Work Style"), button:has-text("Save work style"), button:has-text("Continue")',
                "Save Work Style",
            )
            if save_clicked:
                await asyncio.sleep(10)
                await page.wait_for_load_state("networkidle")
                new_step = await get_step_number()
                print(f"  Step after Work Style: {new_step}")
                if new_step and new_step > 6:
                    print("  ✓ Work Style step completed")

        # Step 4: Career Goals
        print("\n=== Step 4: Career Goals Step ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle")
        current_step = await get_step_number()
        print(f"  Current step: {current_step}")

        # Wait for step 7
        max_wait = 30
        for i in range(max_wait):
            current_step = await get_step_number()
            if current_step == 7:
                break
            await asyncio.sleep(1)

        page_text = await page.inner_text("body")
        await page.screenshot(path="/tmp/careergoals_step_check.png")

        if (
            current_step == 7
            or "career" in page_text.lower()
            or "goal" in page_text.lower()
        ):
            print("  ✓ On Career Goals step")

            # Wait for textarea to load
            await asyncio.sleep(3)

            # Try to find and fill textarea using multiple methods
            textarea_filled = False

            # Method 1: Standard textarea
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

            # Method 2: JavaScript fill
            if not textarea_filled:
                result = await page.evaluate("""
                    (() => {
                        const textarea = document.querySelector('textarea');
                        if (textarea) {
                            textarea.value = "Looking for senior engineering roles in fast-growing tech companies where I can lead technical initiatives and mentor junior developers";
                            textarea.dispatchEvent(new Event('input', { bubbles: true }));
                            textarea.dispatchEvent(new Event('change', { bubbles: true }));
                            return true;
                        }
                        return false;
                    })()
                """)
                if result:
                    print("  ✓ Filled textarea via JavaScript")
                    textarea_filled = True

            # Method 3: Contenteditable
            if not textarea_filled:
                contenteditable = page.locator('[contenteditable="true"]').first
                if await contenteditable.is_visible(timeout=5000):
                    await contenteditable.fill(
                        "Looking for senior engineering roles in fast-growing tech companies where I can lead technical initiatives and mentor junior developers"
                    )
                    print("  ✓ Filled contenteditable")
                    textarea_filled = True

            # Click Continue
            await asyncio.sleep(2)
            continue_clicked = await click_button_robust(
                'button:has-text("Continue"), button:has-text("Next")', "Continue"
            )
            if continue_clicked:
                await asyncio.sleep(10)
                await page.wait_for_load_state("networkidle")
                new_step = await get_step_number()
                print(f"  Step after Career Goals: {new_step}")
                if new_step and new_step > 7:
                    print("  ✓ Career Goals step completed")

        # Step 5: Ready/Complete
        print("\n=== Step 5: Ready/Complete Step ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle")
        current_step = await get_step_number()
        print(f"  Current step: {current_step}")

        # Wait for step 8
        max_wait = 30
        for i in range(max_wait):
            current_step = await get_step_number()
            if current_step == 8:
                break
            await asyncio.sleep(1)

        page_text = await page.inner_text("body")
        await page.screenshot(path="/tmp/ready_step_check.png")

        if (
            current_step == 8
            or "ready" in page_text.lower()
            or "complete" in page_text.lower()
            or "finish" in page_text.lower()
        ):
            print("  ✓ On Ready step")

            # Find and click Complete button using multiple methods
            complete_clicked = False

            # Method 1: Playwright click
            all_buttons = await page.locator("button").all()
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
                                complete_clicked = True
                                break
                except:
                    pass

            # Method 2: JavaScript click
            if not complete_clicked:
                result = await page.evaluate("""
                    (() => {
                        const buttons = Array.from(document.querySelectorAll('button'));
                        const completeBtn = buttons.find(b => {
                            const text = b.textContent || '';
                            return (text.includes('Complete') || text.includes('Finish')) && 
                                   !text.includes('Back') && !text.includes('Restart') && !b.disabled;
                        });
                        if (completeBtn) {
                            completeBtn.click();
                            return true;
                        }
                        return false;
                    })()
                """)
                if result:
                    print("  Clicked Complete button via JavaScript")
                    await asyncio.sleep(10)
                    complete_clicked = True

            if complete_clicked:
                print("  ✓ Onboarding completed!")
            else:
                print("  ⚠ Complete button not found or not clickable")

        # Step 6: Verification
        print("\n=== Step 6: Verification ===")
        await asyncio.sleep(5)
        final_url = page.url
        print(f"Final URL: {final_url}")
        await page.screenshot(path="/tmp/dashboard_final_check.png")

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
            print(f"\n⚠ Final console errors: {len(console_errors)}")
            for i, error in enumerate(console_errors[:10]):
                print(f"  {i + 1}. {error[:200]}")
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
                if profile.get("has_completed_onboarding"):
                    print("  ✓✓✓ ONBOARDING COMPLETED! ✓✓✓")
        except Exception as e:
            print(f"  Error checking profile: {e}")

        await asyncio.sleep(3)
        await browser.close()
        print("\n=== Script Complete ===")


if __name__ == "__main__":
    asyncio.run(complete_with_js())
