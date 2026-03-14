#!/usr/bin/env python3
"""
Script to complete the remaining onboarding steps.
Picks up from current state and completes: Contact → Work Style → Career Goals → Ready
"""

import asyncio

from playwright.async_api import async_playwright

# Valid session token
SESSION_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxZGRmOTc3YS1hNmM2LTRkMzAtODc4Mi1lYjgwNmJhZDYwNTAiLCJlbWFpbCI6InRlc3R1c2VyXzIyNTJkNTE0QHRlc3QuY29tIiwiYXVkIjoiYXV0aGVudGljYXRlZCIsImp0aSI6IjRlOTZkN2MzLTkyYWUtNGMwOC05NDUwLWRhYjYwY2NkNjdkZSIsInNlc3Npb25faWQiOiJmYzJjZmUwZS04ZDc3LTRmNzMtYmRkZS0yNjkwYWE2NDA1Y2IiLCJpYXQiOjE3NzMxMTQ3NTIsIm5iZiI6MTc3MzExNDc1MiwiZXhwIjoxNzczNzE5NTUyfQ.17bFNT76vtC2ri3TQnS2P-H4P2QOmROOgxjrcDkz-lE"


async def complete_remaining_steps():
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
        except:
            pass

        # Detect current step
        page_text = await page.inner_text("body")
        print(f"\nCurrent page content preview: {page_text[:200]}...")

        # Function to wait for step transition
        async def wait_for_step_transition(expected_keywords, timeout=10):
            for i in range(timeout):
                await asyncio.sleep(1)
                current_text = await page.inner_text("body")
                if any(kw in current_text.lower() for kw in expected_keywords):
                    return True
            return False

        # Function to click continue button
        async def click_continue():
            for selector in [
                'button:has-text("Continue")',
                'button:has-text("Next")',
                'button:has-text("Save & Continue")',
            ]:
                try:
                    btn = page.locator(selector).first
                    if await btn.is_visible(timeout=2000):
                        text = await btn.text_content()
                        if (
                            "preferences" not in text.lower()
                            or "save preferences" in text.lower()
                        ):
                            print(f"  Clicking: '{text}'")
                            await btn.click()
                            await asyncio.sleep(6)
                            return True
                except:
                    continue
            return False

        # Step 1: Resume Step (if we're on it)
        if "resume" in page_text.lower() or "upload" in page_text.lower():
            print("\n=== Completing Resume Step ===")
            # Find LinkedIn input
            linkedin_input = page.locator(
                'input[type="url"], input[placeholder*="linkedin" i]'
            ).first
            if await linkedin_input.is_visible(timeout=3000):
                await linkedin_input.fill("https://linkedin.com/in/johndoe")
                print("  ✓ Filled LinkedIn URL")
                await asyncio.sleep(1)

            # Click Continue or Skip
            await click_continue()
            await wait_for_step_transition(["skill", "contact", "preferences"])

        # Step 2: Skills Step (if we're on it)
        page_text = await page.inner_text("body")
        if "skill" in page_text.lower() and (
            "review" in page_text.lower() or "add" in page_text.lower()
        ):
            print("\n=== Completing Skills Step ===")
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

            # Find skills input
            skills_input = None
            all_inputs = await page.locator("input").all()
            for inp in all_inputs:
                try:
                    if await inp.is_visible(timeout=1000):
                        placeholder = await inp.get_attribute("placeholder") or ""
                        if "skill" in placeholder.lower():
                            skills_input = inp
                            break
                except:
                    continue

            if skills_input:
                for skill in skills:
                    try:
                        await skills_input.fill(skill)
                        await asyncio.sleep(0.5)
                        await skills_input.press("Enter")
                        await asyncio.sleep(1)
                        print(f"  ✓ Added skill: {skill}")
                    except:
                        pass

            # Click Continue
            await click_continue()
            await wait_for_step_transition(["contact", "first name", "last name"])

        # Step 3: Contact Step
        print("\n=== Completing Contact Step ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle")
        page_text = await page.inner_text("body")

        if (
            "contact" in page_text.lower()
            or "first name" in page_text.lower()
            or "confirm your details" in page_text.lower()
        ):
            print("  ✓ Confirmed on Contact step")

            # Fill First Name
            first_filled = False
            for selector in ['input[name*="first" i]', 'input[placeholder*="first" i]']:
                try:
                    inp = page.locator(selector).first
                    if await inp.is_visible(timeout=3000):
                        await inp.fill("John")
                        print("  ✓ Filled First Name")
                        first_filled = True
                        break
                except:
                    continue

            # Fill Last Name
            last_filled = False
            for selector in ['input[name*="last" i]', 'input[placeholder*="last" i]']:
                try:
                    inp = page.locator(selector).first
                    if await inp.is_visible(timeout=3000):
                        await inp.fill("Doe")
                        print("  ✓ Filled Last Name")
                        last_filled = True
                        break
                except:
                    continue

            # Fill Phone
            phone_filled = False
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
                        phone_filled = True
                        break
                except:
                    continue

            # Click Continue
            if await click_continue():
                print("  ✓ Contact step completed")
                await wait_for_step_transition(["work style", "workstyle", "career"])

        # Step 4: Work Style Step
        print("\n=== Completing Work Style Step ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle")
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(3)
        page_text = await page.inner_text("body")
        await page.screenshot(path="/tmp/step_workstyle_detailed.png")

        if "work style" in page_text.lower() or "workstyle" in page_text.lower():
            print("  ✓ Confirmed on Work Style step")

            # Debug: List all inputs
            all_inputs = await page.locator("input, textarea, select").all()
            print(f"  Found {len(all_inputs)} input/textarea/select elements")

            # Fill all text inputs and textareas
            text_inputs = await page.locator('input[type="text"], textarea').all()
            filled = 0
            for inp in text_inputs:
                try:
                    if await inp.is_visible(timeout=2000):
                        placeholder = await inp.get_attribute("placeholder") or ""
                        name = await inp.get_attribute("name") or ""
                        value = await inp.input_value()
                        # Skip if already filled or if it's clearly not a work style field
                        if (
                            value
                            or "email" in placeholder.lower()
                            or "phone" in placeholder.lower()
                            or "location" in placeholder.lower()
                            or "name" in placeholder.lower()
                        ):
                            continue
                        await inp.fill(
                            "I prefer collaborative environments with clear communication and regular feedback"
                        )
                        filled += 1
                        print(
                            f"  ✓ Filled text field: '{placeholder[:30]}' or '{name[:30]}'"
                        )
                except:
                    pass

            # Select radio buttons - try to select one from each group
            radios = await page.locator('input[type="radio"]').all()
            selected = 0
            selected_groups = set()
            for radio in radios:
                try:
                    if await radio.is_visible(timeout=1000):
                        name = await radio.get_attribute("name") or ""
                        if name and name not in selected_groups:
                            if not await radio.is_checked():
                                await radio.check()
                                await asyncio.sleep(0.5)
                                selected += 1
                                selected_groups.add(name)
                                print(f"  ✓ Selected radio: '{name}'")
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
            for selector in [
                'button:has-text("Continue")',
                'button:has-text("Next")',
                'button:has-text("Save")',
            ]:
                try:
                    btn = page.locator(selector).first
                    if await btn.is_visible(timeout=3000):
                        text = await btn.text_content()
                        if "preferences" not in text.lower() or "save" in text.lower():
                            print(f"  Clicking: '{text}'")
                            await btn.click()
                            await asyncio.sleep(8)
                            print("  ✓ Work Style step completed")
                            break
                except:
                    continue

        # Step 5: Career Goals Step
        print("\n=== Completing Career Goals Step ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle")
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(3)
        page_text = await page.inner_text("body")
        await page.screenshot(path="/tmp/step_careergoals_detailed.png")

        if "career" in page_text.lower() or "goal" in page_text.lower():
            print("  ✓ Confirmed on Career Goals step")

            # Debug: List all inputs
            all_inputs = await page.locator("input, textarea, select").all()
            print(f"  Found {len(all_inputs)} input/textarea/select elements")

            # Fill career goals textarea - try all textareas
            goals_filled = False
            textareas = await page.locator("textarea").all()
            for textarea in textareas:
                try:
                    if await textarea.is_visible(timeout=2000):
                        placeholder = await textarea.get_attribute("placeholder") or ""
                        name = await textarea.get_attribute("name") or ""
                        value = await textarea.input_value()
                        if not value:  # Only fill if empty
                            await textarea.fill(
                                "Looking for senior engineering roles in fast-growing tech companies where I can lead technical initiatives and mentor junior developers"
                            )
                            print(
                                f"  ✓ Filled textarea: '{placeholder[:30]}' or '{name[:30]}'"
                            )
                            goals_filled = True
                            break
                except:
                    continue

            # Fill other text inputs
            text_inputs = await page.locator('input[type="text"]').all()
            filled_others = 0
            for inp in text_inputs:
                try:
                    if await inp.is_visible(timeout=2000):
                        value = await inp.input_value()
                        placeholder = await inp.get_attribute("placeholder") or ""
                        # Skip if already filled or if it's clearly not a goal field
                        if (
                            value
                            or "email" in placeholder.lower()
                            or "phone" in placeholder.lower()
                            or "name" in placeholder.lower()
                        ):
                            continue
                        await inp.fill(
                            "Build innovative products that impact millions of users"
                        )
                        filled_others += 1
                        print(f"  ✓ Filled text input: '{placeholder[:30]}'")
                        if filled_others >= 3:
                            break
                except:
                    pass

            # Select dropdowns/selects if any
            selects = await page.locator("select").all()
            for select in selects:
                try:
                    if await select.is_visible(timeout=2000):
                        options = await select.locator("option").all()
                        if len(options) > 1:
                            await select.select_option(index=1)  # Select second option
                            print("  ✓ Selected dropdown option")
                except:
                    pass

            # Click Continue
            for selector in [
                'button:has-text("Continue")',
                'button:has-text("Next")',
                'button:has-text("Save")',
            ]:
                try:
                    btn = page.locator(selector).first
                    if await btn.is_visible(timeout=3000):
                        text = await btn.text_content()
                        if "preferences" not in text.lower() or "save" in text.lower():
                            print(f"  Clicking: '{text}'")
                            await btn.click()
                            await asyncio.sleep(8)
                            print("  ✓ Career Goals step completed")
                            break
                except:
                    continue

        # Step 6: Ready/Complete Step
        print("\n=== Completing Ready Step ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle")
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(3)
        page_text = await page.inner_text("body")
        await page.screenshot(path="/tmp/step_ready_detailed.png")

        print(f"  Page content preview: {page_text[:300]}...")

        if (
            "ready" in page_text.lower()
            or "complete" in page_text.lower()
            or "finish" in page_text.lower()
            or "you're all set" in page_text.lower()
        ):
            print("  ✓ Confirmed on Ready step")

            # Find all buttons
            all_buttons = await page.locator("button").all()
            print(f"  Found {len(all_buttons)} buttons")
            for i, btn in enumerate(all_buttons[:10]):
                try:
                    if await btn.is_visible(timeout=1000):
                        text = await btn.text_content()
                        print(f"    Button {i}: '{text}'")
                except:
                    pass

            # Click Complete button - try multiple selectors
            complete_clicked = False
            for selector in [
                'button:has-text("Complete Onboarding")',
                'button:has-text("Complete")',
                'button:has-text("Finish")',
                'button:has-text("Finish Setup")',
                'button:has-text("You\'re all set")',
            ]:
                try:
                    buttons = await page.locator(selector).all()
                    for btn in buttons:
                        if await btn.is_visible(timeout=3000):
                            text = await btn.text_content()
                            # Skip if it's a back button or restart
                            if "back" in text.lower() or "restart" in text.lower():
                                continue
                            print(f"  Clicking: '{text}'")
                            await btn.click()
                            await asyncio.sleep(10)  # Wait for redirect
                            complete_clicked = True
                            print("  ✓ Ready step completed - Onboarding finished!")
                            break
                    if complete_clicked:
                        break
                except:
                    continue

            # If no specific button found, try clicking the last visible button that's not Back/Restart
            if not complete_clicked:
                print("  Trying to find complete button by process of elimination...")
                for btn in all_buttons:
                    try:
                        if await btn.is_visible(timeout=1000):
                            text = await btn.text_content() or ""
                            if (
                                text
                                and "back" not in text.lower()
                                and "restart" not in text.lower()
                                and len(text.strip()) > 0
                            ):
                                if (
                                    "complete" in text.lower()
                                    or "finish" in text.lower()
                                    or "ready" in text.lower()
                                    or "start" not in text.lower()
                                ):
                                    print(f"  Clicking button: '{text}'")
                                    await btn.click()
                                    await asyncio.sleep(10)
                                    complete_clicked = True
                                    break
                    except:
                        pass

        # Final verification
        print("\n=== Final Verification ===")
        await asyncio.sleep(3)
        final_url = page.url
        print(f"Final URL: {final_url}")
        await page.screenshot(path="/tmp/onboarding_final_state.png")

        if "/app/dashboard" in final_url:
            print("  ✓ Successfully redirected to dashboard")
        else:
            print(f"  ⚠ Still on: {final_url}")

        # Check console errors
        if console_errors:
            print(f"\n⚠ Console errors: {len(console_errors)}")
            for error in console_errors[:5]:
                print(f"  - {error}")
        else:
            print("\n✓ No console errors")

        print("\nWaiting 5 seconds before closing...")
        await asyncio.sleep(5)
        await browser.close()
        print("\n=== Script Complete ===")


if __name__ == "__main__":
    asyncio.run(complete_remaining_steps())
