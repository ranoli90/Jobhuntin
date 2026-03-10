#!/usr/bin/env python3
"""
Script to complete remaining onboarding steps: Skills → Work Style → Career Goals → Ready
Starts from current state and completes all remaining steps.
"""
import asyncio
from playwright.async_api import async_playwright

SESSION_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxZGRmOTc3YS1hNmM2LTRkMzAtODc4Mi1lYjgwNmJhZDYwNTAiLCJlbWFpbCI6InRlc3R1c2VyXzIyNTJkNTE0QHRlc3QuY29tIiwiYXVkIjoiYXV0aGVudGljYXRlZCIsImp0aSI6IjRlOTZkN2MzLTkyYWUtNGMwOC05NDUwLWRhYjYwY2NkNjdkZSIsInNlc3Npb25faWQiOiJmYzJjZmUwZS04ZDc3LTRmNzMtYmRkZS0yNjkwYWE2NDA1Y2IiLCJpYXQiOjE3NzMxMTQ3NTIsIm5iZiI6MTc3MzExNDc1MiwiZXhwIjoxNzczNzE5NTUyfQ.17bFNT76vtC2ri3TQnS2P-H4P2QOmROOgxjrcDkz-lE"

async def complete_remaining():
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(headless=False, args=['--no-sandbox', '--disable-dev-shm-usage'])
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        
        await context.add_cookies([{
            'name': 'jobhuntin_auth',
            'value': SESSION_TOKEN,
            'domain': 'localhost',
            'path': '/',
            'httpOnly': True,
            'secure': False,
            'sameSite': 'Lax'
        }])
        
        page = await context.new_page()
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        
        print("\n=== Navigating to Onboarding ===")
        await page.goto('http://localhost:5173/app/onboarding', wait_until='networkidle', timeout=30000)
        await asyncio.sleep(5)
        
        # Dismiss cookie consent
        try:
            accept_btn = page.locator('button:has-text("Accept all")').first
            if await accept_btn.is_visible(timeout=2000):
                await accept_btn.click()
                await asyncio.sleep(1)
        except:
            pass
        
        # Helper to get current step
        async def get_step_info():
            page_text = await page.inner_text('body')
            step_text = ""
            try:
                step_elem = page.locator('text=/STEP \\d+ OF \\d+/i').first
                if await step_elem.is_visible(timeout=2000):
                    step_text = await step_elem.text_content() or ""
            except:
                pass
            return page_text, step_text
        
        # Helper to click next/continue button
        async def click_next():
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
                        disabled = await btn.get_attribute('disabled')
                        if not disabled:
                            print(f"  Clicking: '{text}'")
                            await btn.click()
                            await asyncio.sleep(8)
                            return True
                except:
                    continue
            return False
        
        # Navigate through completed steps to get to Skills
        print("\n=== Navigating to Skills Step ===")
        page_text, step_text = await get_step_info()
        print(f"  Starting at: {step_text}")
        
        # Welcome step
        if 'welcome' in page_text.lower() or 'start setup' in page_text.lower():
            print("  On Welcome step, clicking Start setup...")
            start_btn = page.locator('button:has-text("Start setup")').first
            if await start_btn.is_visible(timeout=5000):
                await start_btn.click()
                await asyncio.sleep(5)
        
        # Preferences step
        await asyncio.sleep(3)
        page_text, step_text = await get_step_info()
        if 'preferences' in page_text.lower() or 'location' in page_text.lower():
            print("  On Preferences step, filling and continuing...")
            location_input = page.locator('input[placeholder*="location" i], input[role="combobox"]').first
            if await location_input.is_visible(timeout=3000):
                await location_input.fill("San Francisco, CA")
                await asyncio.sleep(2)
            salary_inputs = await page.locator('input[type="number"]').all()
            if len(salary_inputs) > 0:
                await salary_inputs[0].fill("100000")
            if len(salary_inputs) > 1:
                await salary_inputs[1].fill("150000")
            await click_next()
        
        # Resume step
        await asyncio.sleep(3)
        page_text, step_text = await get_step_info()
        if 'resume' in page_text.lower() or 'upload' in page_text.lower():
            print("  On Resume step, skipping...")
            skip_btn = page.locator('button:has-text("Skip for now")').first
            if await skip_btn.is_visible(timeout=3000):
                await skip_btn.click()
                await asyncio.sleep(5)
        
        # Step 1: Skills Step
        print("\n=== Step 1: Skills Step ===")
        await asyncio.sleep(3)
        page_text, step_text = await get_step_info()
        print(f"  Current step: {step_text}")
        await page.screenshot(path='/tmp/skills_step_current.png')
        
        # Check if we're on Skills step
        if 'skill' in page_text.lower() and ('review' in page_text.lower() or 'add' in page_text.lower()):
            print("  ✓ Confirmed on Skills step")
            
            # Check if skills are already present
            skills_present = 'javascript' in page_text.lower() or 'python' in page_text.lower() or 'react' in page_text.lower()
            
            if not skills_present:
                print("  No skills detected, adding skills...")
                # Click "Add your first skill" button
                add_btn = page.locator('button:has-text("Add your first skill"), button:has-text("Add a missing skill")').first
                if await add_btn.is_visible(timeout=5000):
                    await add_btn.click()
                    await asyncio.sleep(4)
                    print("  ✓ Clicked add skill button")
                
                skills = ["Python", "JavaScript", "React", "TypeScript", "FastAPI", "PostgreSQL", "Docker", "AWS"]
                for skill in skills:
                    try:
                        # Re-find input field each time (it may be recreated by React)
                        await asyncio.sleep(1)
                        skills_input = None
                        
                        # Try multiple strategies to find input
                        all_inputs = await page.locator('input').all()
                        for inp in all_inputs:
                            try:
                                if await inp.is_visible(timeout=2000):
                                    placeholder = await inp.get_attribute('placeholder') or ''
                                    input_type = await inp.get_attribute('type') or ''
                                    if input_type in ['text', ''] and ('skill' in placeholder.lower() or 'react' in placeholder.lower() or 'python' in placeholder.lower() or not placeholder):
                                        skills_input = inp
                                        break
                            except:
                                continue
                        
                        if not skills_input:
                            # Try finding by clicking in the input area
                            try:
                                input_area = page.locator('input[type="text"]').first
                                if await input_area.is_visible(timeout=2000):
                                    await input_area.click()
                                    await asyncio.sleep(0.5)
                                    skills_input = input_area
                            except:
                                pass
                        
                        if skills_input:
                            await skills_input.fill(skill)
                            await asyncio.sleep(0.8)
                            await skills_input.press("Enter")
                            await asyncio.sleep(2)  # Wait longer for React to process
                            print(f"  ✓ Added skill: {skill}")
                        else:
                            print(f"  ⚠ Could not find input for {skill}, may already be added")
                    except Exception as e:
                        print(f"  ⚠ Error adding {skill}: {e}")
            else:
                print("  ✓ Skills already present")
            
            # Click "Save & Continue" button - try multiple strategies
            await asyncio.sleep(3)
            
            # List all buttons to debug
            all_buttons = await page.locator('button').all()
            print(f"  Found {len(all_buttons)} buttons on page")
            button_info = []
            for i, btn in enumerate(all_buttons):
                try:
                    if await btn.is_visible(timeout=1000):
                        text = await btn.text_content() or ''
                        disabled = await btn.get_attribute('disabled')
                        classes = await btn.get_attribute('class') or ''
                        button_info.append((i, text, disabled, classes))
                        print(f"    Button {i}: '{text[:50]}', disabled={disabled}")
                except:
                    pass
            
            # Try multiple button selectors
            continue_clicked = False
            for selector in [
                'button:has-text("Save & Continue")',
                'button:has-text("Continue")',
                'button:has-text("Next")',
                'button:has-text("Save")',
            ]:
                try:
                    btn = page.locator(selector).first
                    if await btn.is_visible(timeout=3000):
                        text = await btn.text_content()
                        disabled = await btn.get_attribute('disabled')
                        if not disabled:
                            print(f"  Clicking: '{text}'")
                            await btn.click()
                            await asyncio.sleep(10)
                            await page.wait_for_load_state('networkidle')
                            # Verify we moved to next step
                            new_page_text, new_step = await get_step_info()
                            if 'work style' in new_page_text.lower() or 'contact' in new_page_text.lower() or 'career' in new_page_text.lower() or int(new_step.split()[1]) > 4 if new_step else False:
                                print("  ✓ Skills step completed - moved to next step")
                                continue_clicked = True
                                break
                except:
                    continue
            
            if not continue_clicked:
                # Try "Skip for now" as fallback
                skip_btn = page.locator('button:has-text("Skip for now")').first
                if await skip_btn.is_visible(timeout=3000):
                    print("  Clicking 'Skip for now' to proceed")
                    await skip_btn.click()
                    await asyncio.sleep(8)
                    continue_clicked = True
                    print("  ✓ Skipped Skills step")
            
            if not continue_clicked:
                # Try clicking any button that's not Back/Restart/Add
                print("  Trying to click any available button (not Back/Restart/Add)...")
                for i, text, disabled, classes in button_info:
                    if text and 'back' not in text.lower() and 'restart' not in text.lower() and 'add' not in text.lower() and not disabled:
                        try:
                            btn = all_buttons[i]
                            if await btn.is_visible(timeout=2000):
                                print(f"  Clicking button: '{text[:40]}'")
                                await btn.click()
                                await asyncio.sleep(10)
                                await page.wait_for_load_state('networkidle')
                                new_page_text, new_step = await get_step_info()
                                if 'work style' in new_page_text.lower() or 'contact' in new_page_text.lower() or 'career' in new_page_text.lower():
                                    print("  ✓ Moved to next step")
                                    continue_clicked = True
                                    break
                        except:
                            pass
            
            if not continue_clicked:
                print("  ⚠ Could not find or click continue/skip button")
                # Take screenshot for debugging
                await page.screenshot(path='/tmp/skills_step_stuck.png')
        
        # Step 2: Work Style Step
        print("\n=== Step 2: Work Style Step ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state('networkidle')
        page_text, step_text = await get_step_info()
        print(f"  Current step: {step_text}")
        await page.screenshot(path='/tmp/workstyle_step_current.png')
        
        if 'work style' in page_text.lower() or 'workstyle' in page_text.lower():
            print("  ✓ Confirmed on Work Style step")
            
            # Answer work style questions by clicking radio buttons
            # Select one radio from each group
            radios = await page.locator('input[type="radio"]').all()
            selected_groups = set()
            selected_count = 0
            
            print(f"  Found {len(radios)} radio buttons")
            for radio in radios:
                try:
                    if await radio.is_visible(timeout=1000):
                        name = await radio.get_attribute('name') or ''
                        if name and name not in selected_groups:
                            await radio.check()
                            await asyncio.sleep(0.5)
                            selected_count += 1
                            selected_groups.add(name)
                            print(f"  ✓ Selected radio option in group: {name}")
                            if selected_count >= 4:  # Answer at least 4 questions
                                break
                except:
                    pass
            
            # Fill any text inputs
            text_inputs = await page.locator('input[type="text"], textarea').all()
            filled = 0
            for inp in text_inputs:
                try:
                    if await inp.is_visible(timeout=2000):
                        value = await inp.input_value()
                        placeholder = await inp.get_attribute('placeholder') or ''
                        if not value and 'email' not in placeholder.lower() and 'phone' not in placeholder.lower() and 'location' not in placeholder.lower():
                            await inp.fill("I prefer collaborative environments with clear communication")
                            filled += 1
                            print(f"  ✓ Filled text field: '{placeholder[:30]}'")
                except:
                    pass
            
            # Select checkboxes
            checkboxes = await page.locator('input[type="checkbox"]').all()
            checked = 0
            for checkbox in checkboxes:
                try:
                    if await checkbox.is_visible(timeout=1000) and not await checkbox.is_checked():
                        await checkbox.check()
                        await asyncio.sleep(0.3)
                        checked += 1
                except:
                    pass
            
            print(f"  Answered {selected_count} questions, filled {filled} text fields, checked {checked} checkboxes")
            
            # Click "Save work style" or Continue button
            await asyncio.sleep(2)
            continue_btn = page.locator('button:has-text("Save work style"), button:has-text("Continue"), button:has-text("Next")').first
            if await continue_btn.is_visible(timeout=5000):
                text = await continue_btn.text_content()
                disabled = await continue_btn.get_attribute('disabled')
                print(f"  Found button: '{text}', disabled={disabled}")
                if not disabled:
                    print(f"  Clicking: '{text}'")
                    await continue_btn.click()
                    await asyncio.sleep(10)
                    await page.wait_for_load_state('networkidle')
                    print("  ✓ Work Style step completed")
                else:
                    print("  ⚠ Button is disabled")
            else:
                print("  ⚠ Continue button not found")
        else:
            print(f"  ⚠ Not on Work Style step. Page shows: {page_text[:100]}...")
        
        # Step 3: Career Goals Step
        print("\n=== Step 3: Career Goals Step ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state('networkidle')
        page_text, step_text = await get_step_info()
        print(f"  Current step: {step_text}")
        await page.screenshot(path='/tmp/careergoals_step_current.png')
        
        if 'career' in page_text.lower() or 'goal' in page_text.lower():
            print("  ✓ Confirmed on Career Goals step")
            
            # Fill career goals textarea
            textareas = await page.locator('textarea').all()
            goals_filled = False
            for textarea in textareas:
                try:
                    if await textarea.is_visible(timeout=3000):
                        value = await textarea.input_value()
                        if not value:
                            await textarea.fill("Looking for senior engineering roles in fast-growing tech companies where I can lead technical initiatives and mentor junior developers")
                            print("  ✓ Filled career goals textarea")
                            goals_filled = True
                            break
                except:
                    continue
            
            # Fill other text inputs if available
            text_inputs = await page.locator('input[type="text"]').all()
            for inp in text_inputs:
                try:
                    if await inp.is_visible(timeout=2000):
                        value = await inp.input_value()
                        placeholder = await inp.get_attribute('placeholder') or ''
                        if not value and 'email' not in placeholder.lower() and 'phone' not in placeholder.lower() and 'name' not in placeholder.lower():
                            await inp.fill("Build innovative products that impact millions of users")
                            print(f"  ✓ Filled text input: '{placeholder[:30]}'")
                except:
                    pass
            
            # Click Continue
            await asyncio.sleep(2)
            continue_btn = page.locator('button:has-text("Continue"), button:has-text("Next")').first
            if await continue_btn.is_visible(timeout=5000):
                text = await continue_btn.text_content()
                print(f"  Clicking: '{text}'")
                await continue_btn.click()
                await asyncio.sleep(10)
                await page.wait_for_load_state('networkidle')
                print("  ✓ Career Goals step completed")
            else:
                print("  ⚠ Continue button not found")
        else:
            print(f"  ⚠ Not on Career Goals step. Page shows: {page_text[:100]}...")
        
        # Step 4: Ready/Complete Step
        print("\n=== Step 4: Ready/Complete Step ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state('networkidle')
        page_text, step_text = await get_step_info()
        print(f"  Current step: {step_text}")
        await page.screenshot(path='/tmp/ready_step_current.png')
        
        if 'ready' in page_text.lower() or 'complete' in page_text.lower() or 'finish' in page_text.lower() or 'you\'re all set' in page_text.lower():
            print("  ✓ Confirmed on Ready step")
            
            # Find and click Complete button
            all_buttons = await page.locator('button').all()
            complete_clicked = False
            
            for btn in all_buttons:
                try:
                    if await btn.is_visible(timeout=2000):
                        text = await btn.text_content() or ''
                        if text and ('complete' in text.lower() or 'finish' in text.lower()) and 'back' not in text.lower() and 'restart' not in text.lower():
                            disabled = await btn.get_attribute('disabled')
                            if not disabled:
                                print(f"  Clicking: '{text}'")
                                await btn.click()
                                await asyncio.sleep(10)
                                await page.wait_for_load_state('networkidle')
                                complete_clicked = True
                                print("  ✓ Clicked Complete button")
                                break
                except:
                    pass
            
            if not complete_clicked:
                # Try specific selectors
                complete_btn = page.locator('button:has-text("Complete Onboarding"), button:has-text("Complete"), button:has-text("Finish")').first
                if await complete_btn.is_visible(timeout=3000):
                    text = await complete_btn.text_content()
                    print(f"  Clicking: '{text}'")
                    await complete_btn.click()
                    await asyncio.sleep(10)
                    print("  ✓ Onboarding completed!")
        else:
            print(f"  ⚠ Not on Ready step. Page shows: {page_text[:100]}...")
        
        # Step 5: Verify Completion and Test Dashboard
        print("\n=== Step 5: Verify Completion ===")
        await asyncio.sleep(5)
        final_url = page.url
        print(f"Final URL: {final_url}")
        await page.screenshot(path='/tmp/final_state.png')
        
        if '/app/dashboard' in final_url:
            print("  ✓ Successfully redirected to dashboard!")
            
            # Test dashboard sections
            print("\n=== Testing Dashboard ===")
            await asyncio.sleep(3)
            page_text = await page.inner_text('body')
            
            # Check for jobs section
            if 'job' in page_text.lower() or 'application' in page_text.lower():
                print("  ✓ Dashboard content loaded")
            
            # Try to browse jobs if available
            try:
                jobs_link = page.locator('a:has-text("Jobs"), button:has-text("Browse Jobs")').first
                if await jobs_link.is_visible(timeout=3000):
                    await jobs_link.click()
                    await asyncio.sleep(3)
                    print("  ✓ Clicked Jobs link")
            except:
                pass
            
            # Check applications view
            try:
                apps_link = page.locator('a:has-text("Applications"), button:has-text("Applications")').first
                if await apps_link.is_visible(timeout=3000):
                    await apps_link.click()
                    await asyncio.sleep(3)
                    print("  ✓ Clicked Applications link")
            except:
                pass
            
            await page.screenshot(path='/tmp/dashboard_test.png')
        else:
            print(f"  ⚠ Still on: {final_url}")
        
        # Check console errors
        if console_errors:
            print(f"\n⚠ Console errors found: {len(console_errors)}")
            for error in console_errors[:10]:
                print(f"  - {error}")
        else:
            print("\n✓ No console errors detected")
        
        # Verify profile
        print("\n=== Verifying Profile ===")
        try:
            import json
            import urllib.request
            req = urllib.request.Request('http://localhost:8000/me/profile')
            req.add_header('Cookie', f'jobhuntin_auth={SESSION_TOKEN}')
            with urllib.request.urlopen(req) as response:
                profile = json.loads(response.read())
                print(f"  has_completed_onboarding: {profile.get('has_completed_onboarding', False)}")
                print(f"  Contact: {bool(profile.get('contact', {}).get('first_name'))}")
                print(f"  Preferences: {bool(profile.get('preferences', {}).get('location'))}")
                print(f"  Work Style: {bool(profile.get('work_style', {}))}")
                print(f"  Career Goals: {bool(profile.get('career_goals', {}))}")
        except Exception as e:
            print(f"  ⚠ Error checking profile: {e}")
        
        print("\nWaiting 5 seconds before closing...")
        await asyncio.sleep(5)
        await browser.close()
        print("\n=== Onboarding Completion Script Finished ===")

if __name__ == "__main__":
    asyncio.run(complete_remaining())
