#!/usr/bin/env python3
"""
Complete onboarding - use JavaScript to manipulate React state for Skills step
"""

import asyncio

from playwright.async_api import async_playwright

SESSION_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxZGRmOTc3YS1hNmM2LTRkMzAtODc4Mi1lYjgwNmJhZDYwNTAiLCJlbWFpbCI6InRlc3R1c2VyXzIyNTJkNTE0QHRlc3QuY29tIiwiYXVkIjoiYXV0aGVudGljYXRlZCIsImp0aSI6IjRlOTZkN2MzLTkyYWUtNGMwOC05NDUwLWRhYjYwY2NkNjdkZSIsInNlc3Npb25faWQiOiJmYzJjZmUwZS04ZDc3LTRmNzMtYmRkZS0yNjkwYWE2NDA1Y2IiLCJpYXQiOjE3NzMxMTQ3NTIsIm5iZiI6MTc3MzExNDc1MiwiZXhwIjoxNzczNzE5NTUyfQ.17bFNT76vtC2ri3TQnS2P-H4P2QOmROOgxjrcDkz-lE"


async def complete_final():
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

        # Track console errors
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

        # Navigate through initial steps
        print("\n=== Navigating through initial steps ===")
        current_step = await get_step_number()
        print(f"  Current step: {current_step}")

        # Welcome
        if current_step == 1:
            await page.locator('button:has-text("Start setup")').first.click()
            await asyncio.sleep(8)
            current_step = await get_step_number()
            print(f"  Step after Welcome: {current_step}")

        # Preferences
        if current_step == 2:
            try:
                location = page.locator('input[placeholder*="location" i]').first
                if await location.is_visible(timeout=5000):
                    await location.fill("San Francisco, CA")
                    await asyncio.sleep(3)
                salary_inputs = await page.locator('input[type="number"]').all()
                if len(salary_inputs) > 0:
                    await salary_inputs[0].fill("100000")
                if len(salary_inputs) > 1:
                    await salary_inputs[1].fill("150000")

                # Try multiple button selectors
                save_btn = None
                for selector in [
                    'button:has-text("Save preferences")',
                    'button:has-text("Continue")',
                    "button[data-onboarding-next]",
                ]:
                    try:
                        btn = page.locator(selector).first
                        if await btn.is_visible(timeout=2000):
                            save_btn = btn
                            break
                    except:
                        pass

                if save_btn:
                    await save_btn.click()
                    await asyncio.sleep(8)
                else:
                    print("  ⚠ Save preferences button not found, trying JavaScript")
                    await page.evaluate("""
                        (() => {
                            const buttons = Array.from(document.querySelectorAll('button'));
                            const btn = buttons.find(b => b.textContent?.includes('Save') || b.textContent?.includes('Continue'));
                            if (btn && !btn.disabled) {
                                btn.click();
                                return true;
                            }
                            return false;
                        })()
                    """)
                    await asyncio.sleep(8)

                current_step = await get_step_number()
                print(f"  Step after Preferences: {current_step}")
            except Exception as e:
                print(f"  ⚠ Error in Preferences step: {e}")
                current_step = await get_step_number()

        # Resume
        if current_step == 3:
            await page.locator('button:has-text("Skip for now")').first.click()
            await asyncio.sleep(8)
            current_step = await get_step_number()
            print(f"  Step after Resume: {current_step}")

        # Skills - Use JavaScript to add skills directly
        print("\n=== Skills Step - Adding skills via JavaScript ===")
        await asyncio.sleep(5)
        current_step = await get_step_number()
        print(f"  Current step: {current_step}")

        if current_step == 4:
            # Try to add skills directly via React state
            result = await page.evaluate("""
                (() => {
                    // Find React component and add skills directly
                    // Look for the SkillReviewStep component's setRichSkills function
                    const reactRoot = document.querySelector('#root') || document.body;
                    const reactFiber = reactRoot._reactInternalFiber || reactRoot._reactInternalInstance;
                    
                    // Try to find the component by traversing React tree
                    function findComponent(node, targetName) {
                        if (!node) return null;
                        if (node.type && node.type.name === targetName) return node;
                        if (node.child) {
                            const found = findComponent(node.child, targetName);
                            if (found) return found;
                        }
                        if (node.sibling) {
                            const found = findComponent(node.sibling, targetName);
                            if (found) return found;
                        }
                        return null;
                    }
                    
                    // Alternative: Directly manipulate via DOM and events
                    // Add skills by clicking "Add your first skill" and filling form
                    const addBtn = Array.from(document.querySelectorAll('button')).find(b => 
                        b.textContent?.includes('Add your first skill') || b.textContent?.includes('Add a missing skill')
                    );
                    
                    if (addBtn) {
                        addBtn.click();
                        return 'clicked_add';
                    }
                    return 'not_found';
                })()
            """)
            print(f"  JavaScript result: {result}")
            await asyncio.sleep(3)

            # Wait for form and try to fill it
            try:
                # Try multiple input selectors
                inputs = await page.locator(
                    'input[type="text"], input[placeholder*="skill" i], input[placeholder*="name" i]'
                ).all()
                if len(inputs) > 0:
                    print(f"  Found {len(inputs)} input fields")
                    await inputs[0].fill("Python")
                    await asyncio.sleep(1)
                    await inputs[0].press("Enter")
                    await asyncio.sleep(3)
                    print("  ✓ Added Python skill")
                else:
                    print("  ⚠ No input fields found, trying JavaScript fill")
                    # Try JavaScript to fill form
                    filled = await page.evaluate("""
                        (() => {
                            const inputs = Array.from(document.querySelectorAll('input[type="text"]'));
                            const skillInput = inputs.find(inp => 
                                inp.placeholder?.toLowerCase().includes('skill') || 
                                inp.placeholder?.toLowerCase().includes('name')
                            );
                            if (skillInput) {
                                skillInput.value = 'Python';
                                skillInput.dispatchEvent(new Event('input', { bubbles: true }));
                                skillInput.dispatchEvent(new Event('change', { bubbles: true }));
                                return true;
                            }
                            return false;
                        })()
                    """)
                    if filled:
                        print("  ✓ Filled skill input via JavaScript")
                        await asyncio.sleep(2)
                        # Try to submit form
                        await page.evaluate("""
                            (() => {
                                const buttons = Array.from(document.querySelectorAll('button'));
                                const addBtn = buttons.find(b => b.textContent?.includes('Add Skill'));
                                if (addBtn && !addBtn.disabled) {
                                    addBtn.click();
                                    return true;
                                }
                                return false;
                            })()
                        """)
                        await asyncio.sleep(3)
            except Exception as e:
                print(f"  ⚠ Error filling form: {e}")

            # Click Save & Continue or Skip
            await asyncio.sleep(3)
            page_text = await page.inner_text("body")
            print(f"  Page contains 'python': {'python' in page_text.lower()}")
            print(f"  Page contains 'save': {'save' in page_text.lower()}")

            # Try to find Save & Continue button
            save_btn = None
            for selector in [
                'button:has-text("Save & Continue")',
                'button:has-text("Save and Continue")',
                "button[data-onboarding-next]",
                'button:has-text("Continue")',
            ]:
                try:
                    btn = page.locator(selector).first
                    if await btn.is_visible(timeout=2000):
                        text = await btn.text_content() or ""
                        if "skip" not in text.lower() and "back" not in text.lower():
                            save_btn = btn
                            print(f"  Found button: '{text}'")
                            break
                except:
                    pass

            if not save_btn:
                # Try Skip
                try:
                    save_btn = page.locator('button:has-text("Skip for now")').first
                    if await save_btn.is_visible(timeout=2000):
                        print("  Using Skip button")
                except:
                    pass

            if save_btn and await save_btn.is_visible(timeout=5000):
                text = await save_btn.text_content() or ""
                print(f"  Clicking: '{text}'")
                await save_btn.click()
                await asyncio.sleep(12)
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(3)
                new_step = await get_step_number()
                print(f"  Step after Skills: {new_step}")
                if new_step and new_step > 4:
                    print("  ✓ Skills step completed")
                else:
                    print(
                        f"  ⚠ Step didn't advance (still {new_step}), waiting longer..."
                    )
                    await asyncio.sleep(5)
                    new_step = await get_step_number()
                    print(f"  Step after longer wait: {new_step}")
            else:
                print("  ⚠ No Save/Skip button found")

        # Check what step 5 is (ConfirmContact or WorkStyle)
        print("\n=== Identifying Step 5 ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle")
        current_step = await get_step_number()
        print(f"  Current step: {current_step}")

        page_text = await page.inner_text("body")
        await page.screenshot(path="/tmp/step5_check.png")

        # Check if it's ConfirmContact step
        if (
            "contact" in page_text.lower()
            or "confirm" in page_text.lower()
            or "first name" in page_text.lower()
        ):
            print("  ✓ Step 5 is ConfirmContact")

            # Check if fields are already filled
            first_name = page.locator(
                'input[name*="first"], input[placeholder*="first" i]'
            ).first
            last_name = page.locator(
                'input[name*="last"], input[placeholder*="last" i]'
            ).first
            phone = page.locator('input[name*="phone"], input[type="tel"]').first

            filled = False
            try:
                if await first_name.is_visible(timeout=3000):
                    value = await first_name.input_value()
                    if value:
                        print(f"  First Name already filled: {value}")
                        filled = True
            except:
                pass

            if not filled:
                # Fill contact info
                print("  Filling contact info...")
                try:
                    if await first_name.is_visible(timeout=5000):
                        await first_name.fill("John")
                    if await last_name.is_visible(timeout=3000):
                        await last_name.fill("Doe")
                    if await phone.is_visible(timeout=3000):
                        await phone.fill("+1-555-123-4567")
                    print("  ✓ Contact info filled")
                except Exception as e:
                    print(f"  ⚠ Error filling contact: {e}")

            # Click Continue
            await asyncio.sleep(2)
            continue_btn = page.locator('button:has-text("Continue")').first
            if await continue_btn.is_visible(timeout=5000):
                await continue_btn.click()
                await asyncio.sleep(10)
                await page.wait_for_load_state("networkidle")
                new_step = await get_step_number()
                print(f"  Step after ConfirmContact: {new_step}")
                current_step = new_step

        # Work Style
        print("\n=== Work Style Step ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state("networkidle")
        current_step = await get_step_number()
        print(f"  Current step: {current_step}")

        # Wait for step 6 (Work Style is step 6 in role_first variant)
        max_wait = 30
        for i in range(max_wait):
            current_step = await get_step_number()
            if current_step == 6:
                break
            await asyncio.sleep(1)

        current_step = await get_step_number()
        print(f"  Final step check: {current_step}")

        if current_step == 6:
            print("  ✓ On Work Style step")

            # Answer all 7 questions
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

            # Click Save Work Style
            await asyncio.sleep(2)
            save_btn = page.locator(
                'button:has-text("Save Work Style"), button:has-text("Save work style"), button:has-text("Continue")'
            ).first
            if await save_btn.is_visible(timeout=5000):
                await save_btn.click()
                await asyncio.sleep(10)
                await page.wait_for_load_state("networkidle")
                new_step = await get_step_number()
                print(f"  Step after Work Style: {new_step}")
                if new_step and new_step > 6:
                    print("  ✓ Work Style step completed")

        # Career Goals
        print("\n=== Career Goals Step ===")
        await asyncio.sleep(5)
        current_step = await get_step_number()

        # Wait for step 7
        for i in range(30):
            current_step = await get_step_number()
            if current_step == 7:
                break
            await asyncio.sleep(1)

        if current_step == 7:
            print("  ✓ On Career Goals step")

            # Fill textarea
            await asyncio.sleep(3)
            textarea = page.locator("textarea").first
            if await textarea.is_visible(timeout=10000):
                await textarea.fill(
                    "Looking for senior engineering roles in fast-growing tech companies where I can lead technical initiatives and mentor junior developers"
                )
                print("  ✓ Filled career goals textarea")
                await asyncio.sleep(2)
            else:
                # Try JavaScript
                await page.evaluate("""
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
                print("  ✓ Filled textarea via JavaScript")

            # Click Continue
            await asyncio.sleep(2)
            continue_btn = page.locator('button:has-text("Continue")').first
            if await continue_btn.is_visible(timeout=5000):
                await continue_btn.click()
                await asyncio.sleep(10)
                await page.wait_for_load_state("networkidle")
                new_step = await get_step_number()
                print(f"  Step after Career Goals: {new_step}")
                if new_step and new_step > 7:
                    print("  ✓ Career Goals step completed")

        # Ready/Complete
        print("\n=== Ready/Complete Step ===")
        await asyncio.sleep(5)
        current_step = await get_step_number()

        # Wait for step 8
        for i in range(30):
            current_step = await get_step_number()
            if current_step == 8:
                break
            await asyncio.sleep(1)

        if current_step == 8:
            print("  ✓ On Ready step")

            # Find and click Complete button
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
                                break
                except:
                    pass

        # Verification
        print("\n=== Verification ===")
        await asyncio.sleep(5)
        final_url = page.url
        print(f"Final URL: {final_url}")
        await page.screenshot(path="/tmp/dashboard_final.png")

        if "/app/dashboard" in final_url:
            print("  ✓✓✓ Successfully redirected to dashboard! ✓✓✓")
        else:
            print(f"  Still on: {final_url}")

        # Check console errors
        if console_errors:
            print(f"\n⚠ Console errors: {len(console_errors)}")
            for i, error in enumerate(console_errors[:5]):
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
    asyncio.run(complete_final())
