#!/usr/bin/env python3
"""
Complete script to finish the full onboarding flow from start to finish.
Navigates through all steps and fills every field.
"""

import asyncio

from playwright.async_api import async_playwright

SESSION_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxZGRmOTc3YS1hNmM2LTRkMzAtODc4Mi1lYjgwNmJhZDYwNTAiLCJlbWFpbCI6InRlc3R1c2VyXzIyNTJkNTE0QHRlc3QuY29tIiwiYXVkIjoiYXV0aGVudGljYXRlZCIsImp0aSI6IjRlOTZkN2MzLTkyYWUtNGMwOC05NDUwLWRhYjYwY2NkNjdkZSIsInNlc3Npb25faWQiOiJmYzJjZmUwZS04ZDc3LTRmNzMtYmRkZS0yNjkwYWE2NDA1Y2IiLCJpYXQiOjE3NzMxMTQ3NTIsIm5iZiI6MTc3MzExNDc1MiwiZXhwIjoxNzczNzE5NTUyfQ.17bFNT76vtC2ri3TQnS2P-H4P2QOmROOgxjrcDkz-lE"


async def complete_full_onboarding():
    async with async_playwright() as p:
        print("Launching browser...")
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

        # Track console errors
        console_errors = []
        page.on(
            "console",
            lambda msg: (
                console_errors.append(msg.text) if msg.type == "error" else None
            ),
        )

        # Navigate to onboarding
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
                print("  ✓ Dismissed cookie consent")
        except:
            pass

        # Helper function to get current step info
        async def get_current_step():
            page_text = await page.inner_text("body")
            step_text = ""
            try:
                step_indicator = page.locator(r"text=/STEP \d+ OF \d+/i").first
                if await step_indicator.is_visible(timeout=2000):
                    step_text = await step_indicator.text_content() or ""
            except:
                pass
            return page_text, step_text

        # Helper function to click continue/next button
        async def click_next_button():
            for selector in [
                'button:has-text("Save preferences")',
                'button:has-text("Save & Continue")',
                'button:has-text("Continue")',
                'button:has-text("Next")',
            ]:
                try:
                    btn = page.locator(selector).first
                    if await btn.is_visible(timeout=3000):
                        text = await btn.text_content()
                        print(f"  Clicking: '{text}'")
                        await btn.click()
                        await asyncio.sleep(8)
                        return True
                except:
                    continue
            return False

        # Step 1: Welcome
        print("\n=== Step 1: Welcome ===")
        page_text, step_text = await get_current_step()
        print(f"  Current step: {step_text}")

        if "welcome" in page_text.lower() or "start setup" in page_text.lower():
            start_btn = page.locator(
                'button:has-text("Start setup"), button:has-text("Get Started")'
            ).first
            if await start_btn.is_visible(timeout=5000):
                await start_btn.click()
                await asyncio.sleep(5)
                print("  ✓ Welcome step completed")

        # Step 2: Preferences (comes first in variant)
        print("\n=== Step 2: Preferences ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle")
        page_text, step_text = await get_current_step()
        print(f"  Current step: {step_text}")
        await page.screenshot(path="/tmp/step2_preferences.png")

        if (
            "preferences" in page_text.lower()
            or "location" in page_text.lower()
            or "role" in page_text.lower()
        ):
            print("  ✓ Confirmed on Preferences step")

            # Fill Location
            location_input = page.locator(
                'input[placeholder*="location" i], input[placeholder*="Remote" i], input[role="combobox"]'
            ).first
            if await location_input.is_visible(timeout=5000):
                await location_input.fill("San Francisco, CA")
                await asyncio.sleep(2)
                try:
                    dropdown = page.locator(
                        'div[role="option"], li[role="option"]'
                    ).first
                    if await dropdown.is_visible(timeout=2000):
                        await dropdown.click()
                except:
                    pass
                print("  ✓ Filled Location")

            # Fill Role Type
            role_inputs = await page.locator('input[role="combobox"]').all()
            if len(role_inputs) > 1:
                await role_inputs[1].fill("Senior Software Engineer")
                await asyncio.sleep(2)
                try:
                    dropdown = page.locator(
                        'div[role="option"], li[role="option"]'
                    ).first
                    if await dropdown.is_visible(timeout=2000):
                        await dropdown.click()
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
            if await click_next_button():
                print("  ✓ Preferences step completed")

        # Step 3: Resume
        print("\n=== Step 3: Resume ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle")
        page_text, step_text = await get_current_step()
        print(f"  Current step: {step_text}")
        await page.screenshot(path="/tmp/step3_resume.png")

        if (
            "resume" in page_text.lower()
            or "upload" in page_text.lower()
            or "linkedin" in page_text.lower()
        ):
            print("  ✓ Confirmed on Resume step")

            # Fill LinkedIn URL
            linkedin_input = page.locator(
                'input[type="url"], input[placeholder*="linkedin" i]'
            ).first
            if await linkedin_input.is_visible(timeout=5000):
                await linkedin_input.fill("https://linkedin.com/in/johndoe")
                print("  ✓ Filled LinkedIn URL")
                await asyncio.sleep(2)

            # Click Continue or Skip
            skip_btn = page.locator('button:has-text("Skip for now")').first
            if await skip_btn.is_visible(timeout=3000):
                await skip_btn.click()
                await asyncio.sleep(5)
                print("  ✓ Clicked Skip for now")
            elif await click_next_button():
                print("  ✓ Resume step completed")

        # Step 4: Skills
        print("\n=== Step 4: Skills ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle")
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(3)
        page_text, step_text = await get_current_step()
        print(f"  Current step: {step_text}")
        await page.screenshot(path="/tmp/step4_skills.png")

        if "skill" in page_text.lower() and (
            "review" in page_text.lower() or "add" in page_text.lower()
        ):
            print("  ✓ Confirmed on Skills step")

            # Debug: List all inputs
            all_inputs = await page.locator("input, textarea").all()
            print(f"  Found {len(all_inputs)} input/textarea elements")
            for i, inp in enumerate(all_inputs[:10]):
                try:
                    if await inp.is_visible(timeout=1000):
                        placeholder = await inp.get_attribute("placeholder") or ""
                        name = await inp.get_attribute("name") or ""
                        input_type = await inp.get_attribute("type") or ""
                        print(
                            f"    Input {i}: type='{input_type}', name='{name}', placeholder='{placeholder[:40]}'"
                        )
                except:
                    pass

            skills = [
                "Python",
                "JavaScript",
                "React",
                "TypeScript",
                "FastAPI",
                "PostgreSQL",
                "Docker",
                "AWS",
                "Node.js",
            ]

            # Find skills input - try multiple strategies
            skills_input = None

            # Strategy 1: By placeholder
            for inp in all_inputs:
                try:
                    if await inp.is_visible(timeout=2000):
                        placeholder = await inp.get_attribute("placeholder") or ""
                        name = await inp.get_attribute("name") or ""
                        if "skill" in placeholder.lower() or "skill" in name.lower():
                            skills_input = inp
                            print(
                                f"  Found skills input by placeholder/name: '{placeholder}'"
                            )
                            break
                except:
                    continue

            # Strategy 2: Find input near "Add skill" text
            if not skills_input:
                try:
                    add_skill_elem = page.locator("text=/add.*skill/i").first
                    if await add_skill_elem.is_visible(timeout=2000):
                        # Try to find input in same container
                        parent = add_skill_elem.locator(
                            'xpath=ancestor::*[contains(@class, "skill") or contains(@class, "add")]'
                        )
                        skills_input = parent.locator('input[type="text"]').first
                        if await skills_input.is_visible(timeout=2000):
                            print("  Found skills input near 'Add skill' text")
                except:
                    pass

            # Strategy 3: Use first visible text input that's not clearly something else
            if not skills_input:
                for inp in all_inputs:
                    try:
                        if await inp.is_visible(timeout=1000):
                            input_type = await inp.get_attribute("type") or ""
                            placeholder = await inp.get_attribute("placeholder") or ""
                            if (
                                input_type in ["text", ""]
                                and "email" not in placeholder.lower()
                                and "phone" not in placeholder.lower()
                                and "location" not in placeholder.lower()
                                and "name" not in placeholder.lower()
                            ):
                                skills_input = inp
                                print(
                                    f"  Using first available text input: '{placeholder[:30]}'"
                                )
                                break
                    except:
                        continue

            if skills_input:
                for skill in skills:
                    try:
                        await skills_input.fill(skill)
                        await asyncio.sleep(0.8)
                        await skills_input.press("Enter")
                        await asyncio.sleep(1.5)
                        # Try clicking Add button if visible
                        try:
                            add_btn = page.locator(
                                'button:has-text("Add"), button[type="submit"]'
                            ).first
                            if await add_btn.is_visible(timeout=500):
                                await add_btn.click()
                                await asyncio.sleep(0.5)
                        except:
                            pass
                        print(f"  ✓ Added skill: {skill}")
                    except Exception as e:
                        print(f"  ⚠ Error adding {skill}: {e}")
            else:
                print("  ⚠ Could not find skills input - skills may already be loaded")

            # Click Continue - try multiple selectors
            continue_clicked = False
            for selector in [
                'button:has-text("Save & Continue")',
                'button:has-text("Continue")',
                'button:has-text("Next")',
                'button:has-text("Skip for now")',
            ]:
                try:
                    btn = page.locator(selector).first
                    if await btn.is_visible(timeout=3000):
                        text = await btn.text_content()
                        if "preferences" not in text.lower() or "save" in text.lower():
                            print(f"  Clicking: '{text}'")
                            await btn.click()
                            await asyncio.sleep(8)
                            continue_clicked = True
                            print("  ✓ Skills step completed")
                            break
                except:
                    continue

            if not continue_clicked:
                print("  ⚠ Could not find continue button on Skills step")

        # Step 5: Contact
        print("\n=== Step 5: Contact ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle")
        page_text, step_text = await get_current_step()
        print(f"  Current step: {step_text}")
        await page.screenshot(path="/tmp/step5_contact.png")

        if (
            "contact" in page_text.lower()
            or "first name" in page_text.lower()
            or "confirm your details" in page_text.lower()
        ):
            print("  ✓ Confirmed on Contact step")

            # Fill First Name
            for selector in ['input[name*="first" i]', 'input[placeholder*="first" i]']:
                try:
                    inp = page.locator(selector).first
                    if await inp.is_visible(timeout=3000):
                        await inp.fill("John")
                        print("  ✓ Filled First Name")
                        break
                except:
                    continue

            # Fill Last Name
            for selector in ['input[name*="last" i]', 'input[placeholder*="last" i]']:
                try:
                    inp = page.locator(selector).first
                    if await inp.is_visible(timeout=3000):
                        await inp.fill("Doe")
                        print("  ✓ Filled Last Name")
                        break
                except:
                    continue

            # Fill Phone
            for selector in [
                'input[type="tel"]',
                'input[name*="phone" i]',
                'input[placeholder*="phone" i]',
            ]:
                try:
                    inp = page.locator(selector).first
                    if await inp.is_visible(timeout=3000):
                        await inp.fill("+1-555-123-4567")
                        print("  ✓ Filled Phone")
                        break
                except:
                    continue

            # Click Continue
            if await click_next_button():
                print("  ✓ Contact step completed")

        # Step 6: Work Style
        print("\n=== Step 6: Work Style ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle")
        page_text, step_text = await get_current_step()
        print(f"  Current step: {step_text}")
        await page.screenshot(path="/tmp/step6_workstyle.png")

        if "work style" in page_text.lower() or "workstyle" in page_text.lower():
            print("  ✓ Confirmed on Work Style step")

            # Fill all text inputs
            text_inputs = await page.locator('input[type="text"], textarea').all()
            filled = 0
            for inp in text_inputs:
                try:
                    if await inp.is_visible(timeout=2000):
                        placeholder = await inp.get_attribute("placeholder") or ""
                        value = await inp.input_value()
                        if (
                            not value
                            and "email" not in placeholder.lower()
                            and "phone" not in placeholder.lower()
                            and "location" not in placeholder.lower()
                            and "name" not in placeholder.lower()
                        ):
                            await inp.fill(
                                "I prefer collaborative environments with clear communication"
                            )
                            filled += 1
                except:
                    pass

            # Select radio buttons (one per group)
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
                except:
                    pass

            print(f"  Filled {filled} text fields, selected {selected} radio options")

            # Click Continue
            if await click_next_button():
                print("  ✓ Work Style step completed")

        # Step 7: Career Goals
        print("\n=== Step 7: Career Goals ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle")
        page_text, step_text = await get_current_step()
        print(f"  Current step: {step_text}")
        await page.screenshot(path="/tmp/step7_careergoals.png")

        if "career" in page_text.lower() or "goal" in page_text.lower():
            print("  ✓ Confirmed on Career Goals step")

            # Fill all textareas
            textareas = await page.locator("textarea").all()
            for textarea in textareas:
                try:
                    if await textarea.is_visible(timeout=2000):
                        value = await textarea.input_value()
                        if not value:
                            await textarea.fill(
                                "Looking for senior engineering roles in fast-growing tech companies where I can lead technical initiatives and mentor junior developers"
                            )
                            print("  ✓ Filled career goals textarea")
                            break
                except:
                    continue

            # Fill text inputs
            text_inputs = await page.locator('input[type="text"]').all()
            filled = 0
            for inp in text_inputs:
                try:
                    if await inp.is_visible(timeout=2000):
                        value = await inp.input_value()
                        placeholder = await inp.get_attribute("placeholder") or ""
                        if (
                            not value
                            and "email" not in placeholder.lower()
                            and "phone" not in placeholder.lower()
                            and "name" not in placeholder.lower()
                        ):
                            await inp.fill(
                                "Build innovative products that impact millions of users"
                            )
                            filled += 1
                            if filled >= 3:
                                break
                except:
                    pass

            # Click Continue
            if await click_next_button():
                print("  ✓ Career Goals step completed")

        # Step 8: Ready/Complete
        print("\n=== Step 8: Ready/Complete ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle")
        page_text, step_text = await get_current_step()
        print(f"  Current step: {step_text}")
        await page.screenshot(path="/tmp/step8_ready.png")

        if (
            "ready" in page_text.lower()
            or "complete" in page_text.lower()
            or "finish" in page_text.lower()
            or "you're all set" in page_text.lower()
        ):
            print("  ✓ Confirmed on Ready step")

            # Find and click Complete button
            complete_clicked = False
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
                            print(f"  Clicking: '{text}'")
                            await btn.click()
                            await asyncio.sleep(10)
                            complete_clicked = True
                            print("  ✓ Clicked Complete button")
                            break
                except:
                    pass

            if not complete_clicked:
                # Try specific selectors
                for selector in [
                    'button:has-text("Complete Onboarding")',
                    'button:has-text("Complete")',
                    'button:has-text("Finish")',
                ]:
                    try:
                        btn = page.locator(selector).first
                        if await btn.is_visible(timeout=3000):
                            text = await btn.text_content()
                            print(f"  Clicking: '{text}'")
                            await btn.click()
                            await asyncio.sleep(10)
                            complete_clicked = True
                            break
                    except:
                        continue

        # Final verification
        print("\n=== Final Verification ===")
        await asyncio.sleep(5)
        final_url = page.url
        print(f"Final URL: {final_url}")
        await page.screenshot(path="/tmp/onboarding_final.png")

        if "/app/dashboard" in final_url:
            print("  ✓ Successfully redirected to dashboard!")
        else:
            print(f"  ⚠ Still on: {final_url}")

        # Check console errors
        if console_errors:
            print(f"\n⚠ Console errors: {len(console_errors)}")
            for error in console_errors[:5]:
                print(f"  - {error}")
        else:
            print("\n✓ No console errors")

        # Verify profile
        print("\n=== Verifying Profile ===")
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
                print(f"  Contact: {profile.get('contact', {})}")
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
        print("\n=== Onboarding Flow Complete ===")


if __name__ == "__main__":
    asyncio.run(complete_full_onboarding())
