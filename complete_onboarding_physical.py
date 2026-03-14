#!/usr/bin/env python3
"""
Script to physically complete the JobHuntin onboarding flow using Playwright.
This script actually clicks buttons and fills forms as instructed.
"""

import asyncio

from playwright.async_api import async_playwright

# Use valid session token from earlier successful authentication
# This token was successfully verified and has session_id
SESSION_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxZGRmOTc3YS1hNmM2LTRkMzAtODc4Mi1lYjgwNmJhZDYwNTAiLCJlbWFpbCI6InRlc3R1c2VyXzIyNTJkNTE0QHRlc3QuY29tIiwiYXVkIjoiYXV0aGVudGljYXRlZCIsImp0aSI6IjRlOTZkN2MzLTkyYWUtNGMwOC05NDUwLWRhYjYwY2NkNjdkZSIsInNlc3Npb25faWQiOiJmYzJjZmUwZS04ZDc3LTRmNzMtYmRkZS0yNjkwYWE2NDA1Y2IiLCJpYXQiOjE3NzMxMTQ3NTIsIm5iZiI6MTc3MzExNDc1MiwiZXhwIjoxNzczNzE5NTUyfQ.17bFNT76vtC2ri3TQnS2P-H4P2QOmROOgxjrcDkz-lE"


async def complete_onboarding():
    async with async_playwright() as p:
        # Launch browser in headed mode
        print("Launching browser...")
        browser = await p.chromium.launch(
            headless=False, args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(viewport={"width": 1280, "height": 720})

        # Set authentication cookie BEFORE creating page
        print("\n=== Step 1: Setting Authentication Cookie ===")
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
        print("  ✓ Authentication cookie set")

        page = await context.new_page()

        # Track console errors
        console_errors = []
        page.on(
            "console",
            lambda msg: (
                console_errors.append({"type": msg.type, "text": msg.text})
                if msg.type == "error"
                else None
            ),
        )

        # Navigate directly to onboarding with cookie already set
        print("\n=== Step 2: Navigate to Onboarding ===")
        print("Navigating to: http://localhost:5173/app/onboarding")
        await page.goto(
            "http://localhost:5173/app/onboarding",
            wait_until="networkidle",
            timeout=30000,
        )
        await asyncio.sleep(5)  # Wait for page to fully load

        current_url = page.url
        print(f"Current URL: {current_url}")
        await page.screenshot(path="/tmp/step1_auth.png")

        # Verify we're on onboarding page
        if "/app/onboarding" not in current_url:
            print(f"⚠ Not on onboarding page, current URL: {current_url}")
        else:
            print("  ✓ Successfully on onboarding page")

        # Step 3: Welcome Step
        print("\n=== Step 3: Welcome Step ===")
        await page.screenshot(path="/tmp/step2_welcome.png")

        # First, dismiss cookie consent if present
        print("  Checking for cookie consent...")
        cookie_accept_selectors = [
            'button:has-text("Accept all")',
            'button:has-text("Accept")',
            'button:has-text("I agree")',
            'button[id*="accept"]',
        ]
        for selector in cookie_accept_selectors:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=2000):
                    text = await btn.text_content()
                    print(f"  Dismissing cookie consent: '{text}'")
                    await btn.click()
                    await asyncio.sleep(2)
                    break
            except:
                continue

        # Look for Get Started, Start Setup, or Continue button
        welcome_clicked = False
        welcome_selectors = [
            'button:has-text("Get Started")',
            'button:has-text("Start Setup")',
            'button:has-text("Start setup")',
            'button:has-text("Continue")',
            'button:has-text("Next")',
            'a:has-text("Get Started")',
            'a:has-text("Continue")',
        ]

        for selector in welcome_selectors:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=3000):
                    text = await btn.text_content()
                    # Skip cookie consent buttons
                    if (
                        "accept" in text.lower()
                        or "reject" in text.lower()
                        or "manage" in text.lower()
                    ):
                        continue
                    print(f"  Found button: '{text}' using selector: {selector}")
                    await btn.click()
                    await asyncio.sleep(5)  # Wait longer for step transition
                    welcome_clicked = True
                    print("  ✓ Welcome step completed")
                    break
            except:
                continue

        if not welcome_clicked:
            print("  ⚠ Could not find welcome button, trying any button...")
            try:
                all_buttons = await page.locator('button, a[role="button"]').all()
                for btn in all_buttons:
                    if await btn.is_visible(timeout=2000):
                        text = await btn.text_content()
                        # Skip cookie consent and restart buttons
                        if (
                            text
                            and "accept" not in text.lower()
                            and "reject" not in text.lower()
                            and "manage" not in text.lower()
                            and "restart" not in text.lower()
                        ):
                            if (
                                "start" in text.lower()
                                or "setup" in text.lower()
                                or "continue" in text.lower()
                                or "next" in text.lower()
                            ):
                                print(f"  Clicking button: '{text.strip()}'")
                                await btn.click()
                                await asyncio.sleep(5)
                                welcome_clicked = True
                                break
            except Exception as e:
                print(f"  Error: {e}")

        # Step 4: Resume Step
        print("\n=== Step 4: Resume Step ===")
        await asyncio.sleep(5)  # Wait longer for step transition
        await page.wait_for_load_state("networkidle")
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(3)  # Additional wait for React to render
        await page.screenshot(path="/tmp/step3_resume.png")

        # Check which step we're actually on by looking for step-specific content
        page_text = await page.inner_text("body")
        if "Location" in page_text and "Role type" in page_text:
            print(
                "  ⚠ Detected Preferences step instead of Resume step - may have skipped ahead"
            )
        elif (
            "resume" in page_text.lower()
            or "upload" in page_text.lower()
            or "linkedin" in page_text.lower()
        ):
            print("  ✓ Confirmed on Resume step")

        # Scroll to make sure all elements are visible
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(1)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(1)
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(1)

        # Debug: Print ALL elements to understand page structure
        print("  Debugging page structure...")
        all_elements = await page.locator(
            'input, textarea, button, label, div[role="textbox"]'
        ).all()
        print(f"  Found {len(all_elements)} relevant elements total")

        # Try to find elements by text content or labels
        page_text = await page.inner_text("body")
        if "LinkedIn" in page_text or "linkedin" in page_text.lower():
            print("  ✓ LinkedIn text found in page")
        if "resume" in page_text.lower() or "upload" in page_text.lower():
            print("  ✓ Resume/upload text found in page")

        # Look for input fields more broadly - including contenteditable divs
        visible_inputs = []
        for i, elem in enumerate(all_elements):
            try:
                tag = await elem.evaluate("el => el.tagName")
                name = await elem.get_attribute("name") or ""
                placeholder = await elem.get_attribute("placeholder") or ""
                input_type = await elem.get_attribute("type") or ""
                id_attr = await elem.get_attribute("id") or ""
                role = await elem.get_attribute("role") or ""
                visible = await elem.is_visible()
                text = await elem.text_content() or ""
                if visible:
                    visible_inputs.append(elem)
                    print(
                        f"    {tag} {i}: type='{input_type}', role='{role}', name='{name}', id='{id_attr}', placeholder='{placeholder[:30]}', text='{text[:30]}'"
                    )
            except:
                pass

        print(f"  Found {len(visible_inputs)} visible elements")

        # Try to find LinkedIn URL input - use more comprehensive selectors
        linkedin_filled = False

        # First, try to find by label text and then find associated input
        try:
            # Look for any element containing "LinkedIn" text
            linkedin_elements = await page.locator("text=/linkedin/i").all()
            for linkedin_elem in linkedin_elements:
                try:
                    # Try to find input in parent, sibling, or nearby
                    parent = linkedin_elem.locator("xpath=..")
                    # Look for input in parent or following siblings
                    linkedin_input = parent.locator("input").first
                    if await linkedin_input.is_visible(timeout=2000):
                        await linkedin_input.fill("https://linkedin.com/in/johndoe")
                        print("  ✓ Filled LinkedIn URL by finding label")
                        linkedin_filled = True
                        break
                except:
                    continue
        except:
            pass

        # Try standard selectors
        if not linkedin_filled:
            linkedin_selectors = [
                'input[type="url"]',
                'input[placeholder*="linkedin" i]',
                'input[placeholder*="LinkedIn" i]',
                'input[name*="linkedin" i]',
                'input[id*="linkedin" i]',
                'input[aria-label*="linkedin" i]',
            ]

            for selector in linkedin_selectors:
                try:
                    linkedin_inputs = await page.locator(selector).all()
                    for linkedin_input in linkedin_inputs:
                        if await linkedin_input.is_visible(timeout=2000):
                            await linkedin_input.fill("https://linkedin.com/in/johndoe")
                            print(f"  ✓ Filled LinkedIn URL using: {selector}")
                            linkedin_filled = True
                            await asyncio.sleep(1)
                            break
                    if linkedin_filled:
                        break
                except:
                    continue

        # If still not found, look through visible inputs for URL-type inputs
        if not linkedin_filled:
            for elem in visible_inputs:
                try:
                    tag = await elem.evaluate("el => el.tagName")
                    input_type = await elem.get_attribute("type") or ""
                    placeholder = (
                        await elem.get_attribute("placeholder") or ""
                    ).lower()

                    if tag == "INPUT" and (
                        input_type == "url"
                        or "linkedin" in placeholder
                        or "url" in placeholder
                    ):
                        await elem.fill("https://linkedin.com/in/johndoe")
                        print("  ✓ Filled LinkedIn URL by checking input attributes")
                        linkedin_filled = True
                        break
                except:
                    continue

        # If no LinkedIn input, try to find Skip button
        if not linkedin_filled:
            print("  No LinkedIn input found, looking for Skip button...")
            skip_selectors = [
                'button:has-text("Skip for now")',
                'button:has-text("Skip")',
                'button:has-text("Continue without")',
            ]
            for selector in skip_selectors:
                try:
                    skip_btn = page.locator(selector).first
                    if await skip_btn.is_visible(timeout=2000):
                        text = await skip_btn.text_content()
                        print(f"  Found skip button: '{text}'")
                        await skip_btn.click()
                        await asyncio.sleep(3)
                        break
                except:
                    continue

        # Click Continue on Resume step - but only if we're actually on Resume step
        page_text_check = await page.inner_text("body")
        if (
            "resume" in page_text_check.lower()
            or "upload" in page_text_check.lower()
            or "linkedin" in page_text_check.lower()
        ):
            resume_continue_clicked = False
            # Look for Continue button with arrow icon (data-onboarding-next)
            continue_selectors = [
                "button[data-onboarding-next]",
                'button:has-text("Continue"):not(:has-text("Restart")):not(:has-text("preferences"))',
                'button:has-text("Next")',
            ]
            for selector in continue_selectors:
                try:
                    buttons = await page.locator(selector).all()
                    for btn in buttons:
                        if await btn.is_visible(timeout=2000):
                            text = await btn.text_content() or ""
                            # Skip "Save preferences" and "Restart" buttons
                            if (
                                "preferences" in text.lower()
                                or "restart" in text.lower()
                            ):
                                continue
                            # Wait for button to be enabled
                            is_disabled = await btn.is_disabled()
                            if is_disabled:
                                print(f"  Button '{text}' is disabled, waiting...")
                                for _ in range(10):
                                    await asyncio.sleep(0.5)
                                    if not await btn.is_disabled():
                                        break

                            if not await btn.is_disabled():
                                print(f"  Clicking continue: '{text}'")
                                await btn.click()
                                await asyncio.sleep(
                                    5
                                )  # Wait longer for step transition
                                resume_continue_clicked = True
                                print("  ✓ Resume step completed")
                                break
                    if resume_continue_clicked:
                        break
                except:
                    continue
        else:
            print(f"  ⚠ Not on Resume step (detected: {page_text_check[:100]}...)")

        # Step 5: Skills Step
        print("\n=== Step 5: Skills Step ===")
        await asyncio.sleep(5)  # Wait longer for step transition
        await page.wait_for_load_state("networkidle")
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(3)
        await page.screenshot(path="/tmp/step4_skills.png")

        # Check which step we're actually on
        page_text_check = await page.inner_text("body")
        if "skill" in page_text_check.lower() and (
            "review" in page_text_check.lower() or "add" in page_text_check.lower()
        ):
            print("  ✓ Confirmed on Skills step")

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
            skills_added = 0

            # Find skills input field - look specifically for skill-related inputs
            skills_input = None
            skills_selectors = [
                'input[placeholder*="skill" i]',
                'input[placeholder*="Add skill" i]',
                'input[placeholder*="Skill name" i]',
            ]

            for selector in skills_selectors:
                try:
                    inputs = await page.locator(selector).all()
                    for inp in inputs:
                        if await inp.is_visible(timeout=2000):
                            placeholder = await inp.get_attribute("placeholder") or ""
                            if "skill" in placeholder.lower():
                                skills_input = inp
                                print(
                                    f"  Found skills input using: {selector}, placeholder: '{placeholder}'"
                                )
                                break
                    if skills_input:
                        break
                except:
                    continue

            if skills_input:
                for skill in skills:
                    try:
                        await skills_input.fill(skill)
                        await asyncio.sleep(0.8)
                        # Try pressing Enter
                        await skills_input.press("Enter")
                        await asyncio.sleep(1)
                        # Or try clicking Add button
                        add_btns = await page.locator(
                            'button:has-text("Add"), button[type="submit"], button:has-text("+")'
                        ).all()
                        for add_btn in add_btns:
                            if await add_btn.is_visible(timeout=1000):
                                await add_btn.click()
                                await asyncio.sleep(0.5)
                                break
                        print(f"  ✓ Added skill: {skill}")
                        skills_added += 1
                    except Exception as e:
                        print(f"  ⚠ Error adding skill {skill}: {e}")
            else:
                print(
                    "  ⚠ Could not find skills input field - skills may already be loaded from resume"
                )

            print(f"  Added {skills_added} skills")

            # Click Continue on Skills step - wait for button to be enabled
            skills_continue_clicked = False
            for selector in [
                "button[data-onboarding-next]",
                'button:has-text("Save & Continue")',
                'button:has-text("Continue"):not(:has-text("Restart"))',
                'button:has-text("Next")',
            ]:
                try:
                    btn = page.locator(selector).first
                    # Wait for button to be visible AND enabled
                    await btn.wait_for(state="visible", timeout=5000)
                    # Check if disabled
                    is_disabled = await btn.is_disabled()
                    if is_disabled:
                        print("  Button is disabled, waiting for it to be enabled...")
                        # Wait up to 10 seconds for button to be enabled
                        for _ in range(20):
                            await asyncio.sleep(0.5)
                            is_disabled = await btn.is_disabled()
                            if not is_disabled:
                                break

                    if not await btn.is_disabled():
                        text = await btn.text_content()
                        # Skip "Save preferences" button
                        if "preferences" in text.lower() or "restart" in text.lower():
                            continue
                        print(f"  Clicking continue: '{text}'")
                        await btn.click()
                        await asyncio.sleep(5)  # Wait for step transition
                        skills_continue_clicked = True
                        print("  ✓ Skills step completed")
                        break
                    else:
                        print("  ⚠ Button still disabled after waiting")
                except Exception as e:
                    print(f"  ⚠ Error with selector {selector}: {e}")
                    continue
        else:
            print(f"  ⚠ Not on Skills step (page content: {page_text_check[:100]}...)")

        # Step 6: Contact Step
        print("\n=== Step 6: Contact Step ===")
        await asyncio.sleep(2)
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path="/tmp/step5_contact.png")

        # Fill First Name
        first_name_filled = False
        for selector in [
            'input[name*="first" i]',
            'input[placeholder*="first" i]',
            'input[placeholder*="First" i]',
        ]:
            try:
                inp = page.locator(selector).first
                if await inp.is_visible(timeout=2000):
                    await inp.fill("John")
                    print("  ✓ Filled First Name")
                    first_name_filled = True
                    break
            except:
                continue

        # Fill Last Name
        last_name_filled = False
        for selector in [
            'input[name*="last" i]',
            'input[placeholder*="last" i]',
            'input[placeholder*="Last" i]',
        ]:
            try:
                inp = page.locator(selector).first
                if await inp.is_visible(timeout=2000):
                    await inp.fill("Doe")
                    print("  ✓ Filled Last Name")
                    last_name_filled = True
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
                if await inp.is_visible(timeout=2000):
                    await inp.fill("+1-555-123-4567")
                    print("  ✓ Filled Phone")
                    phone_filled = True
                    break
            except:
                continue

        # Click Continue on Contact step
        for selector in ['button:has-text("Continue")', 'button:has-text("Next")']:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=3000):
                    text = await btn.text_content()
                    print(f"  Clicking continue: '{text}'")
                    await btn.click()
                    await asyncio.sleep(3)
                    print("  ✓ Contact step completed")
                    break
            except:
                continue

        # Step 7: Preferences Step
        print("\n=== Step 7: Preferences Step ===")
        await asyncio.sleep(2)
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path="/tmp/step6_preferences.png")

        # Fill Location
        location_filled = False
        for selector in [
            'input[name*="location" i]',
            'input[placeholder*="location" i]',
            'input[placeholder*="Location" i]',
        ]:
            try:
                inp = page.locator(selector).first
                if await inp.is_visible(timeout=2000):
                    await inp.fill("San Francisco")
                    await asyncio.sleep(1)
                    # Try to select from dropdown if it appears
                    dropdown_option = page.locator(
                        'div[role="option"], li[role="option"]'
                    ).first
                    if await dropdown_option.is_visible(timeout=2000):
                        await dropdown_option.click()
                    print("  ✓ Filled Location")
                    location_filled = True
                    break
            except:
                continue

        # Fill Role Type/Job Title
        role_filled = False
        for selector in [
            'input[name*="role" i]',
            'input[name*="title" i]',
            'input[placeholder*="role" i]',
            'input[placeholder*="title" i]',
        ]:
            try:
                inp = page.locator(selector).first
                if await inp.is_visible(timeout=2000):
                    await inp.fill("Senior Software Engineer")
                    print("  ✓ Filled Role/Title")
                    role_filled = True
                    break
            except:
                continue

        # Fill Salary Min
        salary_min_filled = False
        for selector in ['input[name*="salary_min" i]', 'input[type="number"]']:
            try:
                inp = page.locator(selector).first
                if await inp.is_visible(timeout=2000):
                    await inp.fill("100000")
                    print("  ✓ Filled Salary Min")
                    salary_min_filled = True
                    break
            except:
                continue

        # Fill Salary Max
        salary_max_filled = False
        salary_max_inputs = await page.locator('input[type="number"]').all()
        if len(salary_max_inputs) > 1:
            try:
                await salary_max_inputs[1].fill("150000")
                print("  ✓ Filled Salary Max")
                salary_max_filled = True
            except:
                pass

        # Check Remote checkbox
        remote_checked = False
        for selector in ['input[type="checkbox"]', 'input[name*="remote" i]']:
            try:
                checkbox = page.locator(selector).first
                if await checkbox.is_visible(timeout=2000):
                    if not await checkbox.is_checked():
                        await checkbox.check()
                        print("  ✓ Checked Remote")
                        remote_checked = True
                    break
            except:
                continue

        # Click Continue on Preferences step - look for "Save preferences" button
        preferences_saved = False
        for selector in [
            'button:has-text("Save preferences")',
            "button[data-onboarding-next]",
            'button:has-text("Continue"):not(:has-text("Restart"))',
            'button:has-text("Next")',
        ]:
            try:
                btn = page.locator(selector).first
                await btn.wait_for(state="visible", timeout=5000)
                # Wait for button to be enabled
                is_disabled = await btn.is_disabled()
                if is_disabled:
                    print("  Button is disabled, waiting...")
                    for _ in range(10):
                        await asyncio.sleep(0.5)
                        if not await btn.is_disabled():
                            break

                if not await btn.is_disabled():
                    text = await btn.text_content()
                    print(f"  Clicking continue: '{text}'")
                    await btn.click()
                    await asyncio.sleep(5)  # Wait for save and step transition
                    preferences_saved = True
                    print("  ✓ Preferences step completed")
                    break
            except Exception as e:
                print(f"  ⚠ Error with selector {selector}: {e}")
                continue

        # Step 8: Work Style Step
        print("\n=== Step 8: Work Style Step ===")
        await asyncio.sleep(3)
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path="/tmp/step7_workstyle.png")

        # Work Style step has multiple choice questions - need to click option buttons
        # Look for question cards with option buttons
        page_text_check = await page.inner_text("body")
        if (
            "work style" in page_text_check.lower()
            or "workstyle" in page_text_check.lower()
        ):
            print("  ✓ Confirmed on Work Style step")

            # Answer questions by clicking option buttons
            # Each question has multiple option buttons - click the first option for each question
            option_buttons = await page.locator(
                'button:has-text("high"), button:has-text("medium"), button:has-text("low"), button:has-text("async"), button:has-text("sync"), button:has-text("fast"), button:has-text("steady"), button:has-text("solo"), button:has-text("team"), button:has-text("lead"), button:has-text("early"), button:has-text("growth"), button:has-text("enterprise"), button:has-text("docs"), button:has-text("building"), button:has-text("pairing"), button:has-text("courses"), button:has-text("ic"), button:has-text("tech"), button:has-text("manager"), button:has-text("founder"), button:has-text("open")'
            ).all()

            answered = 0
            for i, btn in enumerate(option_buttons[:10]):  # Answer up to 10 options
                try:
                    if await btn.is_visible(timeout=2000):
                        text = await btn.text_content()
                        await btn.click()
                        await asyncio.sleep(1)  # Wait for question to advance
                        answered += 1
                        print(f"  ✓ Answered question {answered}")
                except:
                    pass

            print(f"  Answered {answered} work style questions")

            # Wait for Continue button to be enabled (needs at least 4 answers)
            continue_btn = page.locator(
                'button[data-onboarding-next], button:has-text("Save"), button:has-text("Continue"):not(:has-text("Restart"))'
            ).first
            if await continue_btn.is_visible(timeout=5000):
                # Wait for button to be enabled
                is_disabled = await continue_btn.is_disabled()
                if is_disabled:
                    print("  Button disabled, waiting for enough answers...")
                    for _ in range(20):
                        await asyncio.sleep(0.5)
                        is_disabled = await continue_btn.is_disabled()
                        if not is_disabled:
                            break

                if not await continue_btn.is_disabled():
                    text = await continue_btn.text_content()
                    print(f"  Clicking continue: '{text}'")
                    await continue_btn.click()
                    await asyncio.sleep(5)
                    print("  ✓ Work Style step completed")
                else:
                    print("  ⚠ Continue button still disabled - may need more answers")
        else:
            print("  ⚠ Not on Work Style step")

        # Step 9: Career Goals Step
        print("\n=== Step 9: Career Goals Step ===")
        await asyncio.sleep(2)
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path="/tmp/step8_careergoals.png")

        # Fill career goals textarea
        goals_filled = False
        for selector in [
            'textarea[name*="goal" i]',
            'textarea[placeholder*="goal" i]',
            "textarea",
        ]:
            try:
                textarea = page.locator(selector).first
                if await textarea.is_visible(timeout=3000):
                    await textarea.fill(
                        "Looking for senior engineering roles in fast-growing tech companies where I can lead technical initiatives and mentor junior developers"
                    )
                    print("  ✓ Filled Career Goals")
                    goals_filled = True
                    break
            except:
                continue

        # Fill any other goal fields
        other_inputs = await page.locator('input[type="text"], textarea').all()
        for inp in other_inputs[1:3]:  # Fill 2 more if available
            try:
                if await inp.is_visible(timeout=2000):
                    await inp.fill(
                        "Build innovative products that impact millions of users"
                    )
            except:
                pass

        # Click Continue on Career Goals step
        for selector in ['button:has-text("Continue")', 'button:has-text("Next")']:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=3000):
                    text = await btn.text_content()
                    print(f"  Clicking continue: '{text}'")
                    await btn.click()
                    await asyncio.sleep(3)
                    print("  ✓ Career Goals step completed")
                    break
            except:
                continue

        # Step 10: Ready/Complete Step
        print("\n=== Step 10: Ready/Complete Step ===")
        await asyncio.sleep(2)
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path="/tmp/step9_ready.png")

        # Click Complete/Finish button
        complete_clicked = False
        for selector in [
            'button:has-text("Complete Onboarding")',
            'button:has-text("Complete")',
            'button:has-text("Finish")',
            'button:has-text("Finish Setup")',
        ]:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=3000):
                    text = await btn.text_content()
                    print(f"  Clicking complete: '{text}'")
                    await btn.click()
                    await asyncio.sleep(5)
                    complete_clicked = True
                    print("  ✓ Ready step completed - Onboarding finished!")
                    break
            except:
                continue

        # Step 11: Verify and Test
        print("\n=== Step 11: Verify and Test ===")
        await asyncio.sleep(3)
        final_url = page.url
        print(f"Final URL: {final_url}")
        await page.screenshot(path="/tmp/step10_final.png")

        # Check if redirected to dashboard
        if "/app/dashboard" in final_url:
            print("  ✓ Redirected to dashboard")
        else:
            print(f"  ⚠ Still on: {final_url}")

        # Print console errors
        if console_errors:
            print(f"\n⚠ Console errors found: {len(console_errors)}")
            for error in console_errors[:10]:
                print(f"  - {error['text']}")
        else:
            print("\n✓ No console errors detected")

        # Wait before closing
        print("\nWaiting 5 seconds before closing...")
        await asyncio.sleep(5)

        # Close browser
        await browser.close()
        print("\n=== Onboarding Flow Complete ===")


if __name__ == "__main__":
    asyncio.run(complete_onboarding())
