#!/usr/bin/env python3
"""
Script to complete the JobHuntin onboarding flow using Playwright.
"""

import asyncio

from playwright.async_api import async_playwright

# Authentication token
AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxZGRmOTc3YS1hNmM2LTRkMzAtODc4Mi1lYjgwNmJhZDYwNTAiLCJlbWFpbCI6InRlc3R1c2VyXzIyNTJkNTE0QHRlc3QuY29tIiwiYXVkIjoiYXV0aGVudGljYXRlZCIsImp0aSI6IjRlOTZkN2MzLTkyYWUtNGMwOC05NDUwLWRhYjYwY2NkNjdkZSIsInNlc3Npb25faWQiOiJmYzJjZmUwZS04ZDc3LTRmNzMtYmRkZS0yNjkwYWE2NDA1Y2IiLCJpYXQiOjE3NzMxMTQ3NTIsIm5iZiI6MTc3MzExNDc1MiwiZXhwIjoxNzczNzE5NTUyfQ.17bFNT76vtC2ri3TQnS2P-H4P2QOmROOgxjrcDkz-lE"


async def complete_onboarding():
    async with async_playwright() as p:
        # Launch browser in headed mode so we can see it
        browser = await p.chromium.launch(
            headless=False, args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context()
        page = await context.new_page()

        # Set authentication cookie
        await context.add_cookies(
            [
                {
                    "name": "jobhuntin_auth",
                    "value": AUTH_TOKEN,
                    "domain": "localhost",
                    "path": "/",
                    "httpOnly": True,
                    "secure": False,
                    "sameSite": "Lax",
                }
            ]
        )

        # Navigate to onboarding
        print("Navigating to onboarding page...")
        await page.goto(
            "http://localhost:5173/app/onboarding", wait_until="networkidle"
        )
        await asyncio.sleep(3)

        # Take screenshot for debugging
        await page.screenshot(path="/tmp/onboarding_start.png")
        print("Screenshot saved to /tmp/onboarding_start.png")

        # Check for console errors
        console_errors = []
        page.on(
            "console",
            lambda msg: (
                console_errors.append(msg.text) if msg.type == "error" else None
            ),
        )

        # Debug: Print page title and URL
        print(f"Page title: {await page.title()}")
        print(f"Current URL: {page.url}")

        # Wait for page to fully load
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        # Debug: Print page content
        page_content = await page.content()
        print("Page loaded, checking for onboarding steps...")

        # Step 1: Welcome Step
        print("\n=== Step 1: Welcome Step ===")
        try:
            # Look for "Get Started" or "Continue" button (not "Restart")
            welcome_buttons = [
                'button:has-text("Get Started")',
                'button:has-text("Continue"):not(:has-text("Restart"))',
                'button[data-testid*="welcome"]',
                'button[aria-label*="start" i]',
            ]

            clicked = False
            for selector in welcome_buttons:
                try:
                    btn = page.locator(selector).first
                    if await btn.is_visible(timeout=3000):
                        text = await btn.text_content()
                        if "restart" not in text.lower():
                            print(f"  Clicking: '{text}'")
                            await btn.click()
                            await asyncio.sleep(3)
                            clicked = True
                            print("✓ Welcome step completed")
                            break
                except:
                    continue

            if not clicked:
                print("  ⚠ Could not find welcome button, trying to proceed...")
        except Exception as e:
            print(f"  ⚠ Welcome step error: {e}")

        # Step 2: Resume Step
        print("\n=== Step 2: Resume Step ===")
        try:
            await asyncio.sleep(2)
            await page.wait_for_load_state("networkidle")

            # Check if we're on resume step by looking for upload area or LinkedIn input
            linkedin_input = page.locator(
                'input[name*="linkedin" i], input[placeholder*="linkedin" i], input[id*="linkedin" i]'
            ).first

            # Try to find LinkedIn URL input (ResumeStep has this)
            if await linkedin_input.is_visible(timeout=5000):
                print("  Found LinkedIn input - filling LinkedIn URL")
                await linkedin_input.fill("https://linkedin.com/in/johndoe")
                await asyncio.sleep(1)
                print("  ✓ Filled LinkedIn URL")

            # Wait a moment for any validation
            await asyncio.sleep(1)

            # Try to find and click Continue button - look for button with arrow or "Continue" text
            continue_selectors = [
                "button[data-onboarding-next]",
                'button:has-text("Continue"):not(:has-text("Restart"))',
                'button:has-text("Next")',
                'button[type="button"]:has(svg)',  # Button with icon (arrow)
            ]

            clicked = False
            for selector in continue_selectors:
                try:
                    buttons = await page.locator(selector).all()
                    for btn in buttons:
                        if await btn.is_visible(timeout=2000):
                            text = await btn.text_content() or ""
                            # Skip "Restart" button
                            if "restart" not in text.lower():
                                print(f"  Clicking Continue button: '{text.strip()}'")
                                await btn.click()
                                await asyncio.sleep(4)  # Wait for step transition
                                clicked = True
                                print("✓ Resume step completed")
                                break
                    if clicked:
                        break
                except:
                    continue

            if not clicked:
                print("  ⚠ Could not find Continue button on Resume step")
        except Exception as e:
            print(f"  ⚠ Resume step error: {e}")
            import traceback

            traceback.print_exc()

        # Step 3: Skills Step
        print("\n=== Step 3: Skills Step ===")
        try:
            await asyncio.sleep(3)  # Wait for step transition
            await page.wait_for_load_state("networkidle")

            # Debug: Check what's on the page
            page_title = await page.title()
            current_url = page.url
            print(f"  Current URL: {current_url}")

            # Look for skill input - could be in a form or modal
            skill_input_selectors = [
                'input[placeholder*="skill" i]',
                'input[placeholder*="Add skill" i]',
                'input[placeholder*="Enter skill" i]',
                'input[type="text"]:not([type="hidden"])',
                'input[name*="skill" i]',
            ]

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
            skill_input_found = None

            # Find the skill input field
            for selector in skill_input_selectors:
                try:
                    skill_input = page.locator(selector).first
                    if await skill_input.is_visible(timeout=3000):
                        skill_input_found = skill_input
                        print(f"  Found skill input using: {selector}")
                        break
                except:
                    continue

            if skill_input_found:
                for skill in skills:
                    try:
                        # Clear and fill
                        await skill_input_found.clear()
                        await skill_input_found.fill(skill)
                        await asyncio.sleep(0.8)  # Wait for AI suggestions

                        # Try Enter key first
                        await skill_input_found.press("Enter")
                        await asyncio.sleep(0.5)

                        # Or look for Add button
                        add_btn = page.locator(
                            'button:has-text("Add"), button[aria-label*="add" i], button[type="button"]:has(svg)'
                        ).first
                        if await add_btn.is_visible(timeout=1000):
                            await add_btn.click()
                            await asyncio.sleep(0.5)

                        skills_added += 1
                        print(f"  ✓ Added skill: {skill}")
                    except Exception as e:
                        print(f"  ⚠ Could not add skill {skill}: {e}")
            else:
                print("  ⚠ Could not find skill input field")

            print(f"  Total skills added: {skills_added}")

            # Click Continue - wait a bit for skills to be processed
            await asyncio.sleep(2)
            continue_selectors = [
                "button[data-onboarding-next]",
                'button:has-text("Continue"):not(:has-text("Restart"))',
                'button:has-text("Next")',
            ]

            clicked = False
            for selector in continue_selectors:
                try:
                    continue_btn = page.locator(selector).first
                    if await continue_btn.is_visible(timeout=5000):
                        text = await continue_btn.text_content()
                        print(f"  Clicking Continue: '{text}'")
                        await continue_btn.click()
                        await asyncio.sleep(4)
                        clicked = True
                        print("✓ Skills step completed")
                        break
                except:
                    continue

            if not clicked:
                print("  ⚠ Could not find Continue button on Skills step")
        except Exception as e:
            print(f"  ⚠ Skills step error: {e}")
            import traceback

            traceback.print_exc()

        # Step 4: Contact Step
        print("\n=== Step 4: Contact Step ===")
        try:
            await asyncio.sleep(2)
            await page.wait_for_load_state("networkidle")

            # Phone - try multiple selectors
            phone_selectors = [
                'input[name="phone"]',
                'input[type="tel"]',
                'input[placeholder*="phone" i]',
                'input[id*="phone" i]',
            ]
            for selector in phone_selectors:
                try:
                    phone_input = page.locator(selector).first
                    if await phone_input.is_visible(timeout=2000):
                        await phone_input.fill("+1-555-123-4567")
                        print("  ✓ Filled phone")
                        break
                except:
                    continue

            # First name / Last name
            first_name = page.locator(
                'input[name*="first" i], input[placeholder*="first name" i]'
            ).first
            if await first_name.is_visible(timeout=2000):
                await first_name.fill("John")
                print("  ✓ Filled first name")

            last_name = page.locator(
                'input[name*="last" i], input[placeholder*="last name" i]'
            ).first
            if await last_name.is_visible(timeout=2000):
                await last_name.fill("Doe")
                print("  ✓ Filled last name")

            # LinkedIn (if not already filled in Resume step)
            linkedin_selectors = [
                'input[name*="linkedin" i]',
                'input[placeholder*="linkedin" i]',
                'input[id*="linkedin" i]',
            ]
            for selector in linkedin_selectors:
                try:
                    linkedin_input = page.locator(selector).first
                    if await linkedin_input.is_visible(timeout=2000):
                        current_value = await linkedin_input.input_value()
                        if not current_value:
                            await linkedin_input.fill("https://linkedin.com/in/johndoe")
                            print("  ✓ Filled LinkedIn")
                        break
                except:
                    continue

            # Portfolio/GitHub
            portfolio_selectors = [
                'input[name*="portfolio" i]',
                'input[name*="github" i]',
                'input[placeholder*="portfolio" i]',
                'input[placeholder*="github" i]',
            ]
            for selector in portfolio_selectors:
                try:
                    portfolio_input = page.locator(selector).first
                    if await portfolio_input.is_visible(timeout=2000):
                        await portfolio_input.fill("https://github.com/johndoe")
                        print("  ✓ Filled portfolio")
                        break
                except:
                    continue

            # Click Continue
            continue_btn = page.locator(
                'button:has-text("Continue"):not(:has-text("Restart")), button:has-text("Next")'
            ).first
            if await continue_btn.is_visible(timeout=5000):
                await continue_btn.click()
                await asyncio.sleep(3)
                print("✓ Contact step completed")
        except Exception as e:
            print(f"  ⚠ Contact step error: {e}")

        # Step 5: Preferences Step
        print("\n=== Step 5: Preferences Step ===")
        try:
            await asyncio.sleep(2)
            await page.wait_for_load_state("networkidle")

            # Location - could be autocomplete
            location_selectors = [
                'input[name="location"]',
                'input[placeholder*="location" i]',
                'input[id*="location" i]',
                'input[type="text"]',  # Fallback
            ]
            for selector in location_selectors:
                try:
                    location_input = page.locator(selector).first
                    if await location_input.is_visible(timeout=2000):
                        await location_input.fill("San Francisco")
                        await asyncio.sleep(1)
                        # Try to select from dropdown if autocomplete
                        try:
                            dropdown_option = page.locator(
                                'li, div[role="option"]:has-text("San Francisco")'
                            ).first
                            if await dropdown_option.is_visible(timeout=1000):
                                await dropdown_option.click()
                        except:
                            pass
                        print("  ✓ Filled location")
                        break
                except:
                    continue

            # Role Type / Job Title
            role_selectors = [
                'input[name*="role" i]',
                'input[name*="title" i]',
                'input[placeholder*="role" i]',
                'input[placeholder*="job title" i]',
            ]
            for selector in role_selectors:
                try:
                    role_input = page.locator(selector).first
                    if await role_input.is_visible(timeout=2000):
                        await role_input.fill("Software Engineer")
                        print("  ✓ Filled role type")
                        break
                except:
                    continue

            # Salary Min
            salary_min_selectors = [
                'input[name="salary_min"]',
                'input[name*="min" i][type="number"]',
                'input[placeholder*="min" i]',
            ]
            for selector in salary_min_selectors:
                try:
                    salary_min = page.locator(selector).first
                    if await salary_min.is_visible(timeout=2000):
                        await salary_min.fill("100000")
                        print("  ✓ Filled salary min")
                        break
                except:
                    continue

            # Salary Max
            salary_max_selectors = [
                'input[name="salary_max"]',
                'input[name*="max" i][type="number"]',
                'input[placeholder*="max" i]',
            ]
            for selector in salary_max_selectors:
                try:
                    salary_max = page.locator(selector).first
                    if await salary_max.is_visible(timeout=2000):
                        await salary_max.fill("150000")
                        print("  ✓ Filled salary max")
                        break
                except:
                    continue

            # Remote preference - could be checkbox or select
            remote_checkbox = page.locator(
                'input[type="checkbox"][name*="remote" i], input[type="checkbox"]'
            ).first
            if await remote_checkbox.is_visible(timeout=2000):
                if not await remote_checkbox.is_checked():
                    await remote_checkbox.check()
                    print("  ✓ Checked remote preference")

            # Or try select dropdown
            remote_select = page.locator('select[name*="remote" i]').first
            if await remote_select.is_visible(timeout=2000):
                await remote_select.select_option("Remote")
                print("  ✓ Selected remote preference")

            # Click Continue
            continue_btn = page.locator(
                'button:has-text("Continue"):not(:has-text("Restart")), button:has-text("Next")'
            ).first
            if await continue_btn.is_visible(timeout=5000):
                await continue_btn.click()
                await asyncio.sleep(3)
                print("✓ Preferences step completed")
        except Exception as e:
            print(f"  ⚠ Preferences step error: {e}")

        # Step 6: Work Style Step
        print("\n=== Step 6: Work Style Step ===")
        try:
            await asyncio.sleep(2)
            await page.wait_for_load_state("networkidle")

            # Work style questions - could be radio buttons, checkboxes, or text inputs
            # Try to find and answer questions
            text_inputs = await page.locator('input[type="text"], textarea').all()
            for i, input_field in enumerate(text_inputs[:10]):  # Fill up to 10 inputs
                try:
                    if await input_field.is_visible(timeout=2000):
                        placeholder = (
                            await input_field.get_attribute("placeholder") or ""
                        )
                        name = await input_field.get_attribute("name") or ""
                        # Fill with appropriate answer based on field
                        if (
                            "communication" in placeholder.lower()
                            or "communication" in name.lower()
                        ):
                            await input_field.fill(
                                "I prefer clear, direct communication with regular check-ins"
                            )
                        elif "team" in placeholder.lower() or "team" in name.lower():
                            await input_field.fill(
                                "I work best in collaborative teams of 3-5 people"
                            )
                        elif (
                            "management" in placeholder.lower()
                            or "management" in name.lower()
                        ):
                            await input_field.fill(
                                "I prefer supportive managers who provide clear direction"
                            )
                        else:
                            await input_field.fill(
                                "I value work-life balance and flexible schedules"
                            )
                        print(f"  ✓ Filled field {i + 1}")
                except:
                    pass

            # Try radio buttons or checkboxes
            radio_buttons = await page.locator('input[type="radio"]').all()
            for i, radio in enumerate(radio_buttons[:5]):
                try:
                    if await radio.is_visible(timeout=1000):
                        await radio.check()
                except:
                    pass

            # Click Continue
            continue_btn = page.locator(
                'button:has-text("Continue"):not(:has-text("Restart")), button:has-text("Next")'
            ).first
            if await continue_btn.is_visible(timeout=5000):
                await continue_btn.click()
                await asyncio.sleep(3)
                print("✓ Work Style step completed")
        except Exception as e:
            print(f"  ⚠ Work Style step error: {e}")

        # Step 7: Career Goals Step
        print("\n=== Step 7: Career Goals Step ===")
        try:
            await asyncio.sleep(2)
            await page.wait_for_load_state("networkidle")

            # Career goals - usually textarea
            goals_selectors = [
                'textarea[name*="goal" i]',
                'textarea[placeholder*="goal" i]',
                'textarea[placeholder*="career" i]',
                "textarea",
            ]
            for selector in goals_selectors:
                try:
                    goals_input = page.locator(selector).first
                    if await goals_input.is_visible(timeout=2000):
                        await goals_input.fill(
                            "Looking for senior engineering roles in fast-growing tech companies where I can lead technical initiatives and mentor junior developers. My long-term goal is to become an engineering manager or principal engineer."
                        )
                        print("  ✓ Filled career goals")
                        break
                except:
                    continue

            # Short-term goals
            short_term = page.locator(
                'textarea[placeholder*="short" i], input[placeholder*="short" i]'
            ).first
            if await short_term.is_visible(timeout=2000):
                await short_term.fill(
                    "Secure a senior engineering position within 3 months"
                )
                print("  ✓ Filled short-term goals")

            # Long-term goals
            long_term = page.locator(
                'textarea[placeholder*="long" i], input[placeholder*="long" i]'
            ).first
            if await long_term.is_visible(timeout=2000):
                await long_term.fill(
                    "Become an engineering manager or principal engineer"
                )
                print("  ✓ Filled long-term goals")

            # Click Continue
            continue_btn = page.locator(
                'button:has-text("Continue"):not(:has-text("Restart")), button:has-text("Next")'
            ).first
            if await continue_btn.is_visible(timeout=5000):
                await continue_btn.click()
                await asyncio.sleep(3)
                print("✓ Career Goals step completed")
        except Exception as e:
            print(f"  ⚠ Career Goals step error: {e}")

        # Step 8: Complete/Ready Step
        print("\n=== Step 8: Ready/Complete Step ===")
        try:
            await asyncio.sleep(2)
            await page.wait_for_load_state("networkidle")

            # Click Complete/Finish button
            complete_selectors = [
                'button:has-text("Complete Onboarding")',
                'button:has-text("Complete")',
                'button:has-text("Finish")',
                'button:has-text("Get Started")',
            ]
            for selector in complete_selectors:
                try:
                    complete_btn = page.locator(selector).first
                    if await complete_btn.is_visible(timeout=3000):
                        text = await complete_btn.text_content()
                        print(f"  Clicking: '{text}'")
                        await complete_btn.click()
                        await asyncio.sleep(5)  # Wait for redirect
                        print("✓ Onboarding completed!")
                        break
                except:
                    continue
        except Exception as e:
            print(f"  ⚠ Ready step error: {e}")

        # Check final URL
        final_url = page.url
        print(f"\nFinal URL: {final_url}")

        # Print console errors if any
        if console_errors:
            print(f"\nConsole errors found: {len(console_errors)}")
            for error in console_errors[:5]:
                print(f"  - {error}")
        else:
            print("\n✓ No console errors detected")

        # Wait a bit before closing
        await asyncio.sleep(5)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(complete_onboarding())
