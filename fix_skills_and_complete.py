#!/usr/bin/env python3
"""
Script to fix Skills step and complete remaining onboarding steps.
Uses comprehensive debugging to find the correct selectors.
"""

import asyncio

from playwright.async_api import async_playwright

SESSION_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxZGRmOTc3YS1hNmM2LTRkMzAtODc4Mi1lYjgwNmJhZDYwNTAiLCJlbWFpbCI6InRlc3R1c2VyXzIyNTJkNTE0QHRlc3QuY29tIiwiYXVkIjoiYXV0aGVudGljYXRlZCIsImp0aSI6IjRlOTZkN2MzLTkyYWUtNGMwOC05NDUwLWRhYjYwY2NkNjdkZSIsInNlc3Npb25faWQiOiJmYzJjZmUwZS04ZDc3LTRmNzMtYmRkZS0yNjkwYWE2NDA1Y2IiLCJpYXQiOjE3NzMxMTQ3NTIsIm5iZiI6MTc3MzExNDc1MiwiZXhwIjoxNzczNzE5NTUyfQ.17bFNT76vtC2ri3TQnS2P-H4P2QOmROOgxjrcDkz-lE"


async def fix_and_complete():
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

        # Dismiss cookie consent
        try:
            accept_btn = page.locator('button:has-text("Accept all")').first
            if await accept_btn.is_visible(timeout=2000):
                await accept_btn.click()
                await asyncio.sleep(1)
        except:
            pass

        # Navigate through steps until we reach Skills
        print("\n=== Navigating to Skills Step ===")

        # Click through Welcome if needed
        try:
            start_btn = page.locator('button:has-text("Start setup")').first
            if await start_btn.is_visible(timeout=3000):
                await start_btn.click()
                await asyncio.sleep(5)
        except:
            pass

        # Navigate through Preferences
        page_text = await page.inner_text("body")
        if "preferences" in page_text.lower() or "location" in page_text.lower():
            print("  On Preferences step, filling and continuing...")
            # Quick fill preferences
            location_input = page.locator(
                'input[placeholder*="location" i], input[role="combobox"]'
            ).first
            if await location_input.is_visible(timeout=3000):
                await location_input.fill("San Francisco, CA")
                await asyncio.sleep(2)
            salary_inputs = await page.locator('input[type="number"]').all()
            if len(salary_inputs) > 0:
                await salary_inputs[0].fill("100000")
            if len(salary_inputs) > 1:
                await salary_inputs[1].fill("150000")
            save_btn = page.locator('button:has-text("Save preferences")').first
            if await save_btn.is_visible(timeout=3000):
                await save_btn.click()
                await asyncio.sleep(5)

        # Navigate through Resume
        page_text = await page.inner_text("body")
        if "resume" in page_text.lower() or "upload" in page_text.lower():
            print("  On Resume step, skipping...")
            skip_btn = page.locator('button:has-text("Skip for now")').first
            if await skip_btn.is_visible(timeout=3000):
                await skip_btn.click()
                await asyncio.sleep(5)

        # Now we should be on Skills step
        print("\n=== Skills Step - Comprehensive Debugging ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle")
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(3)
        await page.screenshot(path="/tmp/skills_step_debug.png")

        page_text = await page.inner_text("body")
        print(f"  Page text preview: {page_text[:500]}...")

        # Get ALL elements
        all_elements = await page.locator("*").all()
        print(f"  Total elements on page: {len(all_elements)}")

        # Find all inputs
        all_inputs = await page.locator("input, textarea").all()
        print(f"  Found {len(all_inputs)} input/textarea elements")

        for i, inp in enumerate(all_inputs):
            try:
                if await inp.is_visible(timeout=1000):
                    tag = await inp.evaluate("el => el.tagName")
                    input_type = await inp.get_attribute("type") or ""
                    name = await inp.get_attribute("name") or ""
                    id_attr = await inp.get_attribute("id") or ""
                    placeholder = await inp.get_attribute("placeholder") or ""
                    value = await inp.input_value()
                    classes = await inp.get_attribute("class") or ""
                    print(
                        f"    Input {i}: tag={tag}, type='{input_type}', name='{name}', id='{id_attr}', placeholder='{placeholder[:40]}', value='{value[:30]}', classes='{classes[:50]}'"
                    )
            except:
                pass

        # Find all buttons
        all_buttons = await page.locator("button").all()
        print(f"  Found {len(all_buttons)} button elements")

        for i, btn in enumerate(all_buttons[:15]):
            try:
                if await btn.is_visible(timeout=1000):
                    text = await btn.text_content() or ""
                    classes = await btn.get_attribute("class") or ""
                    disabled = await btn.get_attribute("disabled")
                    print(
                        f"    Button {i}: text='{text[:40]}', disabled={disabled}, classes='{classes[:50]}'"
                    )
            except:
                pass

        # Click "Add your first skill" or "Add a missing skill" button to reveal input
        add_skill_btn = page.locator(
            'button:has-text("Add your first skill"), button:has-text("Add a missing skill")'
        ).first
        if await add_skill_btn.is_visible(timeout=5000):
            print("  Clicking 'Add your first skill' button to reveal input...")
            await add_skill_btn.click()
            await asyncio.sleep(3)
            await page.wait_for_load_state("domcontentloaded")
            print("  ✓ Clicked add skill button")

        # Now find the skills input that should be visible
        skills_input = None
        await asyncio.sleep(2)

        # Find input that appeared after clicking the button
        all_inputs_after = await page.locator("input, textarea").all()
        print(
            f"  Found {len(all_inputs_after)} input/textarea elements after clicking button"
        )

        for inp in all_inputs_after:
            try:
                if await inp.is_visible(timeout=2000):
                    placeholder = await inp.get_attribute("placeholder") or ""
                    name = await inp.get_attribute("name") or ""
                    input_type = await inp.get_attribute("type") or ""
                    if (
                        "skill" in placeholder.lower()
                        or "skill" in name.lower()
                        or (input_type in ["text", ""] and not placeholder)
                    ):
                        skills_input = inp
                        print(
                            f"  ✓ Found skills input: placeholder='{placeholder}', name='{name}'"
                        )
                        break
            except:
                continue

        # If still not found, use first visible text input
        if not skills_input:
            for inp in all_inputs_after:
                try:
                    if await inp.is_visible(timeout=1000):
                        input_type = await inp.get_attribute("type") or ""
                        placeholder = await inp.get_attribute("placeholder") or ""
                        if (
                            input_type in ["text", ""]
                            and "email" not in placeholder.lower()
                            and "phone" not in placeholder.lower()
                        ):
                            skills_input = inp
                            print(
                                f"  ✓ Using first available text input: '{placeholder[:30]}'"
                            )
                            break
                except:
                    continue

        # Try to add skills
        if skills_input:
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
                    await skills_input.click()
                    await asyncio.sleep(0.5)
                    await skills_input.fill(skill)
                    await asyncio.sleep(0.5)
                    await skills_input.press("Enter")
                    await asyncio.sleep(2)
                    # Try clicking Add button if visible
                    try:
                        add_btn = page.locator(
                            'button:has-text("Add"), button[type="submit"]'
                        ).first
                        if await add_btn.is_visible(timeout=1000):
                            await add_btn.click()
                            await asyncio.sleep(1)
                    except:
                        pass
                    print(f"  ✓ Added skill: {skill}")
                except Exception as e:
                    print(f"  ⚠ Error adding {skill}: {e}")
        else:
            print(
                "  ⚠ Could not find skills input after clicking button - may need to skip"
            )

        # Find and click Continue button (or Skip if no skills added)
        await asyncio.sleep(3)
        all_buttons_after = await page.locator("button").all()
        print(f"  Found {len(all_buttons_after)} buttons after adding skills")
        for i, btn in enumerate(all_buttons_after[:10]):
            try:
                if await btn.is_visible(timeout=1000):
                    text = await btn.text_content() or ""
                    disabled = await btn.get_attribute("disabled")
                    print(f"    Button {i}: text='{text[:40]}', disabled={disabled}")
            except:
                pass

        continue_clicked = False

        # Try multiple button selectors
        for selector in [
            'button:has-text("Save & Continue")',
            'button:has-text("Continue")',
            'button:has-text("Next")',
            'button:has-text("Done")',
        ]:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=3000):
                    text = await btn.text_content()
                    disabled = await btn.get_attribute("disabled")
                    if not disabled:
                        print(f"  Clicking continue button: '{text}'")
                        await btn.click()
                        await asyncio.sleep(10)  # Wait longer for step transition
                        # Verify we moved to next step
                        await page.wait_for_load_state("networkidle")
                        new_page_text = await page.inner_text("body")
                        if (
                            "work style" in new_page_text.lower()
                            or "contact" in new_page_text.lower()
                            or "career" in new_page_text.lower()
                        ):
                            continue_clicked = True
                            print("  ✓ Skills step completed - moved to next step")
                            break
                        else:
                            print(
                                f"  ⚠ Still on Skills step after clicking, page shows: {new_page_text[:100]}..."
                            )
            except:
                continue

        if not continue_clicked:
            # Try Skip button if Continue not available
            skip_btn = page.locator('button:has-text("Skip for now")').first
            if await skip_btn.is_visible(timeout=3000):
                print("  Clicking 'Skip for now' button")
                await skip_btn.click()
                await asyncio.sleep(10)
                continue_clicked = True
                print("  ✓ Skills step skipped")

        if not continue_clicked:
            print("  ⚠ Could not find or click continue/skip button")
            # Try clicking any button that's not Back/Restart
            for btn in all_buttons_after:
                try:
                    if await btn.is_visible(timeout=2000):
                        text = await btn.text_content() or ""
                        if (
                            text
                            and "back" not in text.lower()
                            and "restart" not in text.lower()
                            and "add" not in text.lower()
                        ):
                            disabled = await btn.get_attribute("disabled")
                            if not disabled:
                                print(f"  Trying button: '{text}'")
                                await btn.click()
                                await asyncio.sleep(10)
                                break
                except:
                    pass

        # Continue with Work Style and Career Goals
        print("\n=== Work Style Step ===")
        await asyncio.sleep(8)
        await page.wait_for_load_state("networkidle")
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(3)
        page_text = await page.inner_text("body")
        step_indicator = ""
        try:
            step_elem = page.locator(r"text=/STEP \d+ OF \d+/i").first
            if await step_elem.is_visible(timeout=2000):
                step_indicator = await step_elem.text_content() or ""
        except:
            pass
        print(f"  Current step indicator: {step_indicator}")
        print(f"  Page text preview: {page_text[:300]}...")
        await page.screenshot(path="/tmp/workstyle_step.png")

        if (
            "work style" in page_text.lower()
            or "workstyle" in page_text.lower()
            or "step 6" in step_indicator.lower()
            or "step 5" in step_indicator.lower()
        ):
            print("  ✓ On Work Style step")

            # Debug: List all inputs
            all_inputs = await page.locator("input, textarea, select").all()
            print(f"  Found {len(all_inputs)} input/textarea/select elements")

            # Fill all text inputs and textareas
            text_inputs = await page.locator('input[type="text"], textarea').all()
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
                            and "location" not in placeholder.lower()
                            and "name" not in placeholder.lower()
                        ):
                            await inp.fill(
                                "I prefer collaborative environments with clear communication and regular feedback"
                            )
                            filled += 1
                            print(f"  ✓ Filled text field: '{placeholder[:30]}'")
                except:
                    pass

            # Select radios (one per group)
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

            # Select checkboxes
            checkboxes = await page.locator('input[type="checkbox"]').all()
            checked = 0
            for checkbox in checkboxes:
                try:
                    if (
                        await checkbox.is_visible(timeout=1000)
                        and not await checkbox.is_checked()
                    ):
                        await checkbox.check()
                        await asyncio.sleep(0.3)
                        checked += 1
                except:
                    pass

            print(
                f"  Filled {filled} text fields, selected {selected} radio options, checked {checked} checkboxes"
            )

            # Click Continue
            continue_btn = page.locator(
                'button:has-text("Continue"), button:has-text("Next"), button:has-text("Save")'
            ).first
            if await continue_btn.is_visible(timeout=3000):
                text = await continue_btn.text_content()
                print(f"  Clicking: '{text}'")
                await continue_btn.click()
                await asyncio.sleep(8)
                print("  ✓ Work Style step completed")
            else:
                print("  ⚠ Continue button not found on Work Style step")
        else:
            print(
                f"  ⚠ Not on Work Style step. Step indicator: {step_indicator}, Page preview: {page_text[:100]}..."
            )

        # Career Goals
        print("\n=== Career Goals Step ===")
        await asyncio.sleep(8)
        await page.wait_for_load_state("networkidle")
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(3)
        page_text = await page.inner_text("body")
        step_indicator = ""
        try:
            step_elem = page.locator(r"text=/STEP \d+ OF \d+/i").first
            if await step_elem.is_visible(timeout=2000):
                step_indicator = await step_elem.text_content() or ""
        except:
            pass
        print(f"  Current step indicator: {step_indicator}")
        print(f"  Page text preview: {page_text[:300]}...")
        await page.screenshot(path="/tmp/careergoals_step.png")

        if (
            "career" in page_text.lower()
            or "goal" in page_text.lower()
            or "step 7" in step_indicator.lower()
            or "step 6" in step_indicator.lower()
        ):
            print("  ✓ On Career Goals step")

            # Debug: List all inputs
            all_inputs = await page.locator("input, textarea, select").all()
            print(f"  Found {len(all_inputs)} input/textarea/select elements")

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
                except:
                    pass

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
            continue_btn = page.locator(
                'button:has-text("Continue"), button:has-text("Next"), button:has-text("Save")'
            ).first
            if await continue_btn.is_visible(timeout=3000):
                text = await continue_btn.text_content()
                print(f"  Clicking: '{text}'")
                await continue_btn.click()
                await asyncio.sleep(8)
                print("  ✓ Career Goals step completed")
            else:
                print("  ⚠ Continue button not found on Career Goals step")
        else:
            print(
                f"  ⚠ Not on Career Goals step. Step indicator: {step_indicator}, Page preview: {page_text[:100]}..."
            )

        # Ready/Complete
        print("\n=== Ready Step ===")
        await asyncio.sleep(8)
        await page.wait_for_load_state("networkidle")
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(3)
        page_text = await page.inner_text("body")
        step_indicator = ""
        try:
            step_elem = page.locator(r"text=/STEP \d+ OF \d+/i").first
            if await step_elem.is_visible(timeout=2000):
                step_indicator = await step_elem.text_content() or ""
        except:
            pass
        print(f"  Current step indicator: {step_indicator}")
        print(f"  Page text preview: {page_text[:300]}...")
        await page.screenshot(path="/tmp/ready_step.png")

        if (
            "ready" in page_text.lower()
            or "complete" in page_text.lower()
            or "finish" in page_text.lower()
            or "you're all set" in page_text.lower()
            or "step 8" in step_indicator.lower()
        ):
            print("  ✓ On Ready step")

            # Find Complete button - try all buttons
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
                            print(f"  Clicking: '{text}'")
                            await btn.click()
                            await asyncio.sleep(10)
                            complete_clicked = True
                            print("  ✓ Onboarding completed!")
                            break
                except:
                    pass

            if not complete_clicked:
                # Try specific selectors
                complete_btn = page.locator(
                    'button:has-text("Complete"), button:has-text("Finish")'
                ).first
                if await complete_btn.is_visible(timeout=3000):
                    text = await complete_btn.text_content()
                    print(f"  Clicking: '{text}'")
                    await complete_btn.click()
                    await asyncio.sleep(10)
                    print("  ✓ Onboarding completed!")
                else:
                    print("  ⚠ Complete button not found")
        else:
            print(
                f"  ⚠ Not on Ready step. Step indicator: {step_indicator}, Page preview: {page_text[:100]}..."
            )

        # Final check
        final_url = page.url
        print(f"\nFinal URL: {final_url}")

        if "/app/dashboard" in final_url:
            print("  ✓ Successfully redirected to dashboard!")
        else:
            print(f"  ⚠ Still on: {final_url}")

        await asyncio.sleep(3)
        await browser.close()
        print("\n=== Script Complete ===")


if __name__ == "__main__":
    asyncio.run(fix_and_complete())
