#!/usr/bin/env python3
"""
Script to directly complete the JobHuntin onboarding flow by actually clicking and filling forms.
"""
import asyncio
from playwright.async_api import async_playwright

# Magic link token
MAGIC_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxZGRmOTc3YS1hNmM2LTRkMzAtODc4Mi1lYjgwNmJhZDYwNTAiLCJlbWFpbCI6InRlc3R1c2VyXzIyNTJkNTE0QHRlc3QuY29tIiwiYXVkIjoiYXV0aGVudGljYXRlZCIsImp0aSI6ImQxMTI1NDE1LTBjMGQtNDQ1OC04MTE0LTUwMjFlOTJhODc5NiIsImlhdCI6MTc3MzExMzgyMiwibmJmIjoxNzczMTEzODIyLCJleHAiOjE3NzMxMTc0MjIsIm5ld191c2VyIjpmYWxzZX0.n1CaP2h_pi1OAx8UfNOYVQaGKZLhDkvraewuiGdn0WA"

async def complete_onboarding():
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(headless=False, args=['--no-sandbox', '--disable-dev-shm-usage'])
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()
        
        # Track console errors
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        
        # Step 1: Navigate and authenticate
        print("\n=== Step 1: Navigate to Onboarding ===")
        verify_url = f"http://localhost:8000/auth/verify-magic?token={MAGIC_TOKEN}&returnTo=/app/onboarding"
        print(f"Navigating to verify-magic endpoint...")
        await page.goto(verify_url, wait_until='networkidle', timeout=30000)
        await asyncio.sleep(3)
        
        # If redirected to login, navigate directly to onboarding
        current_url = page.url
        if '/login' in current_url or '/app/onboarding' not in current_url:
            print("Navigating directly to onboarding...")
            await page.goto('http://localhost:5173/app/onboarding', wait_until='networkidle')
            await asyncio.sleep(3)
        
        print(f"Current URL: {page.url}")
        await page.screenshot(path='/tmp/onboarding_start.png')
        
        # Dismiss cookie consent if present
        try:
            accept_btn = page.locator('button:has-text("Accept all"), button:has-text("Accept")').first
            if await accept_btn.is_visible(timeout=2000):
                await accept_btn.click()
                await asyncio.sleep(1)
                print("  ✓ Dismissed cookie consent")
        except:
            pass
        
        # Step 2: Welcome Step
        print("\n=== Step 2: Welcome Step ===")
        await asyncio.sleep(2)
        
        # Find and click Start setup button
        start_btn = page.locator('button:has-text("Start setup"), button:has-text("Get Started"), button:has-text("Start Setup")').first
        if await start_btn.is_visible(timeout=5000):
            text = await start_btn.text_content()
            print(f"  Clicking: '{text}'")
            await start_btn.click()
            await asyncio.sleep(4)
            print("  ✓ Welcome step completed")
        else:
            print("  ⚠ Could not find Start setup button")
        
        # NOTE: The app uses an A/B test variant where step order is:
        # Welcome → Preferences → Resume → Skills → Contact → Work Style → Career Goals → Ready
        # So after Welcome, we go to Preferences (which we already handled)
        # Then Resume, then Skills, etc.
        
        # Step 3: Resume Step (comes after Preferences in the variant)
        print("\n=== Step 3: Resume Step ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state('networkidle')
        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(3)
        await page.screenshot(path='/tmp/step_resume.png')
        
        # Check which step we're on
        page_text = await page.inner_text('body')
        if 'resume' in page_text.lower() or 'upload' in page_text.lower() or 'linkedin' in page_text.lower():
            print("  ✓ Confirmed on Resume step")
        
        # Find LinkedIn URL input
        linkedin_input = None
        for selector in ['input[type="url"]', 'input[placeholder*="linkedin" i]', 'input[placeholder*="LinkedIn" i]']:
            try:
                inp = page.locator(selector).first
                if await inp.is_visible(timeout=3000):
                    linkedin_input = inp
                    break
            except:
                continue
        
        if linkedin_input:
            await linkedin_input.fill("https://linkedin.com/in/johndoe")
            print("  ✓ Filled LinkedIn URL")
            await asyncio.sleep(1)
        else:
            print("  ⚠ LinkedIn input not found, will try Skip button")
        
        # Click Continue or Skip
        continue_clicked = False
        for selector in [
            'button:has-text("Continue")',
            'button:has-text("Skip for now")',
            'button:has-text("Next")',
        ]:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=3000):
                    text = await btn.text_content()
                    if 'preferences' not in text.lower() and 'save' not in text.lower():
                        print(f"  Clicking: '{text}'")
                        await btn.click()
                        await asyncio.sleep(5)
                        continue_clicked = True
                        print("  ✓ Resume step completed")
                        break
            except:
                continue
        
        # Step 4: Skills Step
        print("\n=== Step 4: Skills Step ===")
        await asyncio.sleep(5)  # Wait longer for step transition
        await page.wait_for_load_state('networkidle')
        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(3)
        await page.screenshot(path='/tmp/step_skills.png')
        
        # Debug: Check what's on the page
        page_text = await page.inner_text('body')
        print(f"  Page content preview: {page_text[:200]}...")
        
        skills = ["Python", "JavaScript", "React", "TypeScript", "FastAPI", "PostgreSQL", "Docker", "AWS", "Node.js"]
        skills_added = 0
        
        # Find skills input field - try more comprehensive selectors
        skills_input = None
        all_inputs = await page.locator('input, textarea').all()
        print(f"  Found {len(all_inputs)} total input/textarea elements")
        
        for inp in all_inputs:
            try:
                if await inp.is_visible(timeout=1000):
                    placeholder = await inp.get_attribute('placeholder') or ''
                    name = await inp.get_attribute('name') or ''
                    input_type = await inp.get_attribute('type') or ''
                    if 'skill' in placeholder.lower() or 'skill' in name.lower():
                        skills_input = inp
                        print(f"  Found skills input: placeholder='{placeholder}', name='{name}', type='{input_type}'")
                        break
            except:
                continue
        
        # If not found by placeholder/name, try finding by context (near "Add skill" text)
        if not skills_input:
            try:
                add_skill_text = page.locator('text=/add.*skill/i').first
                if await add_skill_text.is_visible(timeout=2000):
                    # Find input near this text
                    parent = add_skill_text.locator('xpath=ancestor::*[contains(@class, "skill") or contains(@class, "add")]')
                    skills_input = parent.locator('input[type="text"]').first
                    if await skills_input.is_visible(timeout=2000):
                        print("  Found skills input near 'Add skill' text")
            except:
                pass
        
        if skills_input:
            for skill in skills:
                try:
                    await skills_input.fill(skill)
                    await asyncio.sleep(0.5)
                    await skills_input.press("Enter")
                    await asyncio.sleep(1)
                    # Try clicking Add button if visible
                    try:
                        add_btn = page.locator('button:has-text("Add"), button[type="submit"]').first
                        if await add_btn.is_visible(timeout=500):
                            await add_btn.click()
                            await asyncio.sleep(0.5)
                    except:
                        pass
                    print(f"  ✓ Added skill: {skill}")
                    skills_added += 1
                except Exception as e:
                    print(f"  ⚠ Error adding {skill}: {e}")
        else:
            print("  ⚠ Skills input not found - may already have skills from resume")
        
        print(f"  Added {skills_added} skills")
        
        # Click Continue on Skills step
        for selector in ['button:has-text("Save & Continue")', 'button:has-text("Continue")', 'button:has-text("Next")']:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=3000):
                    text = await btn.text_content()
                    if 'preferences' not in text.lower():
                        print(f"  Clicking: '{text}'")
                        await btn.click()
                        await asyncio.sleep(5)
                        print("  ✓ Skills step completed")
                        break
            except:
                continue
        
        # Step 5: Contact Step
        print("\n=== Step 5: Contact Step ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state('networkidle')
        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(3)
        await page.screenshot(path='/tmp/step_contact.png')
        
        # Debug: Check what's on the page
        page_text = await page.inner_text('body')
        print(f"  Page content preview: {page_text[:200]}...")
        if 'first name' in page_text.lower() or 'contact' in page_text.lower():
            print("  ✓ Confirmed on Contact step")
        
        # Find all inputs and try to match by label text
        all_inputs = await page.locator('input, textarea').all()
        print(f"  Found {len(all_inputs)} total input/textarea elements")
        
        # Fill First Name - try finding by label
        first_name_filled = False
        try:
            first_label = page.locator('text=/first.*name/i, label:has-text("First")').first
            if await first_label.is_visible(timeout=2000):
                # Find associated input
                first_input = first_label.locator('xpath=following::input[1] | ../input').first
                if await first_input.is_visible(timeout=2000):
                    await first_input.fill("John")
                    print("  ✓ Filled First Name (by label)")
                    first_name_filled = True
        except:
            pass
        
        if not first_name_filled:
            for selector in ['input[name*="first" i]', 'input[placeholder*="first" i]', 'input[placeholder*="First" i]']:
                try:
                    inp = page.locator(selector).first
                    if await inp.is_visible(timeout=2000):
                        await inp.fill("John")
                        print("  ✓ Filled First Name")
                        first_name_filled = True
                        break
                except:
                    continue
        
        # Fill Last Name - try finding by label
        last_name_filled = False
        try:
            last_label = page.locator('text=/last.*name/i, label:has-text("Last")').first
            if await last_label.is_visible(timeout=2000):
                last_input = last_label.locator('xpath=following::input[1] | ../input').first
                if await last_input.is_visible(timeout=2000):
                    await last_input.fill("Doe")
                    print("  ✓ Filled Last Name (by label)")
                    last_name_filled = True
        except:
            pass
        
        if not last_name_filled:
            for selector in ['input[name*="last" i]', 'input[placeholder*="last" i]', 'input[placeholder*="Last" i]']:
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
        for selector in ['input[type="tel"]', 'input[name*="phone" i]', 'input[placeholder*="phone" i]']:
            try:
                inp = page.locator(selector).first
                if await inp.is_visible(timeout=2000):
                    await inp.fill("+1-555-123-4567")
                    print("  ✓ Filled Phone")
                    phone_filled = True
                    break
            except:
                continue
        
        # Click Continue
        for selector in ['button:has-text("Continue")', 'button:has-text("Next")']:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=3000):
                    text = await btn.text_content()
                    print(f"  Clicking: '{text}'")
                    await btn.click()
                    await asyncio.sleep(5)
                    print("  ✓ Contact step completed")
                    break
            except:
                continue
        
        # Step 6: Preferences Step
        print("\n=== Step 6: Preferences Step ===")
        await asyncio.sleep(3)
        await page.wait_for_load_state('networkidle')
        await page.screenshot(path='/tmp/step_preferences.png')
        
        # Fill Location
        location_filled = False
        for selector in ['input[placeholder*="location" i]', 'input[placeholder*="Remote" i]', 'input[role="combobox"]']:
            try:
                inputs = await page.locator(selector).all()
                for inp in inputs:
                    if await inp.is_visible(timeout=2000):
                        placeholder = await inp.get_attribute('placeholder') or ''
                        if 'location' in placeholder.lower() or 'remote' in placeholder.lower() or 'san francisco' in placeholder.lower():
                            await inp.fill("San Francisco, CA")
                            await asyncio.sleep(1)
                            # Try selecting from dropdown
                            try:
                                dropdown = page.locator('div[role="option"], li[role="option"]').first
                                if await dropdown.is_visible(timeout=2000):
                                    await dropdown.click()
                            except:
                                pass
                            print("  ✓ Filled Location")
                            location_filled = True
                            break
                if location_filled:
                    break
            except:
                continue
        
        # Fill Role Type
        role_filled = False
        for selector in ['input[placeholder*="role" i]', 'input[placeholder*="Product Manager" i]', 'input[role="combobox"]']:
            try:
                inputs = await page.locator(selector).all()
                for inp in inputs:
                    if await inp.is_visible(timeout=2000):
                        placeholder = await inp.get_attribute('placeholder') or ''
                        if 'role' in placeholder.lower() or 'manager' in placeholder.lower():
                            await inp.fill("Senior Software Engineer")
                            await asyncio.sleep(1)
                            # Try selecting from dropdown
                            try:
                                dropdown = page.locator('div[role="option"], li[role="option"]').first
                                if await dropdown.is_visible(timeout=2000):
                                    await dropdown.click()
                            except:
                                pass
                            print("  ✓ Filled Role Type")
                            role_filled = True
                            break
                if role_filled:
                    break
            except:
                continue
        
        # Fill Salary Min
        salary_min_filled = False
        for selector in ['input[type="number"]', 'input[placeholder*="80000" i]']:
            try:
                inputs = await page.locator(selector).all()
                for inp in inputs[:2]:  # Check first 2 number inputs
                    if await inp.is_visible(timeout=2000):
                        placeholder = await inp.get_attribute('placeholder') or ''
                        if '80000' in placeholder or 'min' in placeholder.lower():
                            await inp.fill("100000")
                            print("  ✓ Filled Salary Min")
                            salary_min_filled = True
                            break
                if salary_min_filled:
                    break
            except:
                pass
        
        # Fill Salary Max
        salary_max_filled = False
        salary_inputs = await page.locator('input[type="number"]').all()
        if len(salary_inputs) > 1:
            try:
                await salary_inputs[1].fill("150000")
                print("  ✓ Filled Salary Max")
                salary_max_filled = True
            except:
                pass
        
        # Check Remote checkbox
        remote_checked = False
        checkboxes = await page.locator('input[type="checkbox"]').all()
        for checkbox in checkboxes:
            try:
                label = await checkbox.evaluate('el => el.closest("label")?.textContent || ""')
                if 'remote' in label.lower() and await checkbox.is_visible(timeout=1000):
                    if not await checkbox.is_checked():
                        await checkbox.check()
                        print("  ✓ Checked Remote")
                        remote_checked = True
                        break
            except:
                continue
        
        # Click Continue
        for selector in ['button:has-text("Save preferences")', 'button:has-text("Continue")', 'button:has-text("Next")']:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=3000):
                    text = await btn.text_content()
                    print(f"  Clicking: '{text}'")
                    await btn.click()
                    await asyncio.sleep(8)  # Wait longer for step transition
                    # Verify we moved to next step
                    await page.wait_for_load_state('networkidle')
                    page_text_after = await page.inner_text('body')
                    if 'resume' in page_text_after.lower() or 'upload' in page_text_after.lower():
                        print("  ✓ Preferences step completed - moved to Resume step")
                    else:
                        print(f"  ⚠ Step transition unclear, page shows: {page_text_after[:100]}...")
                    break
            except:
                continue
        
        # Step 7: Resume Step (comes after Preferences in variant)
        print("\n=== Step 7: Resume Step (after Preferences) ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state('networkidle')
        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(3)
        await page.screenshot(path='/tmp/step_resume_after_prefs.png')
        
        # Check which step we're on
        page_text = await page.inner_text('body')
        if 'resume' in page_text.lower() or 'upload' in page_text.lower():
            print("  ✓ Confirmed on Resume step")
            
            # Find LinkedIn URL input
            linkedin_input = None
            for selector in ['input[type="url"]', 'input[placeholder*="linkedin" i]', 'input[placeholder*="LinkedIn" i]']:
                try:
                    inp = page.locator(selector).first
                    if await inp.is_visible(timeout=3000):
                        linkedin_input = inp
                        break
                except:
                    continue
            
            if linkedin_input:
                await linkedin_input.fill("https://linkedin.com/in/johndoe")
                print("  ✓ Filled LinkedIn URL")
                await asyncio.sleep(1)
            
            # Click Continue or Skip
            for selector in [
                'button:has-text("Continue")',
                'button:has-text("Skip for now")',
                'button:has-text("Next")',
            ]:
                try:
                    btn = page.locator(selector).first
                    if await btn.is_visible(timeout=3000):
                        text = await btn.text_content()
                        if 'preferences' not in text.lower() and 'save' not in text.lower():
                            print(f"  Clicking: '{text}'")
                            await btn.click()
                            await asyncio.sleep(8)
                            print("  ✓ Resume step completed")
                            break
                except:
                    continue
        else:
            print(f"  ⚠ Not on Resume step, page shows: {page_text[:100]}...")
        
        # Step 8: Skills Step
        print("\n=== Step 8: Skills Step ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state('networkidle')
        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(3)
        await page.screenshot(path='/tmp/step_skills_after_resume.png')
        
        # Check which step we're on
        page_text = await page.inner_text('body')
        if 'skill' in page_text.lower() and ('review' in page_text.lower() or 'add' in page_text.lower()):
            print("  ✓ Confirmed on Skills step")
            
            skills = ["Python", "JavaScript", "React", "TypeScript", "FastAPI", "PostgreSQL", "Docker", "AWS", "Node.js"]
            skills_added = 0
            
            # Find skills input field
            skills_input = None
            all_inputs = await page.locator('input, textarea').all()
            for inp in all_inputs:
                try:
                    if await inp.is_visible(timeout=1000):
                        placeholder = await inp.get_attribute('placeholder') or ''
                        name = await inp.get_attribute('name') or ''
                        if 'skill' in placeholder.lower() or 'skill' in name.lower():
                            skills_input = inp
                            print(f"  Found skills input: '{placeholder}'")
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
                        try:
                            add_btn = page.locator('button:has-text("Add"), button[type="submit"]').first
                            if await add_btn.is_visible(timeout=500):
                                await add_btn.click()
                                await asyncio.sleep(0.5)
                        except:
                            pass
                        print(f"  ✓ Added skill: {skill}")
                        skills_added += 1
                    except Exception as e:
                        print(f"  ⚠ Error adding {skill}: {e}")
            
            print(f"  Added {skills_added} skills")
            
            # Click Continue on Skills step
            for selector in ['button:has-text("Save & Continue")', 'button:has-text("Continue")', 'button:has-text("Next")']:
                try:
                    btn = page.locator(selector).first
                    if await btn.is_visible(timeout=3000):
                        text = await btn.text_content()
                        if 'preferences' not in text.lower():
                            print(f"  Clicking: '{text}'")
                            await btn.click()
                            await asyncio.sleep(8)
                            print("  ✓ Skills step completed")
                            break
                except:
                    continue
        else:
            print(f"  ⚠ Not on Skills step, page shows: {page_text[:100]}...")
        
        # Step 9: Contact Step
        print("\n=== Step 9: Contact Step ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state('networkidle')
        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(3)
        await page.screenshot(path='/tmp/step_contact_after_skills.png')
        
        # Check which step we're on
        page_text = await page.inner_text('body')
        if 'contact' in page_text.lower() or 'first name' in page_text.lower() or 'confirm your details' in page_text.lower():
            print("  ✓ Confirmed on Contact step")
            
            # Fill First Name
            first_name_filled = False
            try:
                first_label = page.locator('text=/first.*name/i, label:has-text("First")').first
                if await first_label.is_visible(timeout=2000):
                    first_input = first_label.locator('xpath=following::input[1] | ../input').first
                    if await first_input.is_visible(timeout=2000):
                        await first_input.fill("John")
                        print("  ✓ Filled First Name")
                        first_name_filled = True
            except:
                pass
            
            if not first_name_filled:
                for selector in ['input[name*="first" i]', 'input[placeholder*="first" i]']:
                    try:
                        inp = page.locator(selector).first
                        if await inp.is_visible(timeout=2000):
                            await inp.fill("John")
                            print("  ✓ Filled First Name")
                            break
                    except:
                        continue
            
            # Fill Last Name
            last_name_filled = False
            try:
                last_label = page.locator('text=/last.*name/i, label:has-text("Last")').first
                if await last_label.is_visible(timeout=2000):
                    last_input = last_label.locator('xpath=following::input[1] | ../input').first
                    if await last_input.is_visible(timeout=2000):
                        await last_input.fill("Doe")
                        print("  ✓ Filled Last Name")
                        last_name_filled = True
            except:
                pass
            
            if not last_name_filled:
                for selector in ['input[name*="last" i]', 'input[placeholder*="last" i]']:
                    try:
                        inp = page.locator(selector).first
                        if await inp.is_visible(timeout=2000):
                            await inp.fill("Doe")
                            print("  ✓ Filled Last Name")
                            break
                    except:
                        continue
            
            # Fill Phone
            for selector in ['input[type="tel"]', 'input[name*="phone" i]', 'input[placeholder*="phone" i]']:
                try:
                    inp = page.locator(selector).first
                    if await inp.is_visible(timeout=2000):
                        await inp.fill("+1-555-123-4567")
                        print("  ✓ Filled Phone")
                        break
                except:
                    continue
            
            # Click Continue
            for selector in ['button:has-text("Continue")', 'button:has-text("Next")']:
                try:
                    btn = page.locator(selector).first
                    if await btn.is_visible(timeout=3000):
                        text = await btn.text_content()
                        print(f"  Clicking: '{text}'")
                        await btn.click()
                        await asyncio.sleep(8)
                        print("  ✓ Contact step completed")
                        break
                except:
                    continue
        else:
            print(f"  ⚠ Not on Contact step, page shows: {page_text[:100]}...")
        
        # Step 10: Work Style Step
        print("\n=== Step 7: Work Style Step ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state('networkidle')
        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(3)
        await page.screenshot(path='/tmp/step_workstyle.png')
        
        # Debug: Check what's on the page
        page_text = await page.inner_text('body')
        print(f"  Page content preview: {page_text[:300]}...")
        if 'work style' in page_text.lower() or 'workstyle' in page_text.lower():
            print("  ✓ Confirmed on Work Style step")
        
        # Find all interactive elements
        all_inputs = await page.locator('input, textarea, select, button').all()
        print(f"  Found {len(all_inputs)} total interactive elements")
        
        # Fill text inputs and textareas
        text_inputs = await page.locator('input[type="text"], textarea').all()
        filled_count = 0
        for inp in text_inputs:
            try:
                if await inp.is_visible(timeout=2000):
                    placeholder = await inp.get_attribute('placeholder') or ''
                    # Skip if it's clearly not a work style field
                    if 'email' in placeholder.lower() or 'phone' in placeholder.lower() or 'location' in placeholder.lower():
                        continue
                    await inp.fill("I prefer collaborative environments with clear communication and regular feedback")
                    filled_count += 1
                    print(f"  ✓ Filled text field: '{placeholder[:30]}'")
            except:
                pass
        
        # Select radio buttons
        radio_buttons = await page.locator('input[type="radio"]').all()
        selected_count = 0
        for radio in radio_buttons:
            try:
                if await radio.is_visible(timeout=1000):
                    if not await radio.is_checked():
                        await radio.check()
                        await asyncio.sleep(0.5)
                        selected_count += 1
            except:
                pass
        
        # Select checkboxes
        checkboxes = await page.locator('input[type="checkbox"]').all()
        checked_count = 0
        for checkbox in checkboxes:
            try:
                if await checkbox.is_visible(timeout=1000):
                    if not await checkbox.is_checked():
                        await checkbox.check()
                        await asyncio.sleep(0.3)
                        checked_count += 1
            except:
                pass
        
        print(f"  Filled {filled_count} text fields, selected {selected_count} radio options, checked {checked_count} checkboxes")
        
        # Click Continue
        for selector in ['button:has-text("Continue")', 'button:has-text("Next")']:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=3000):
                    text = await btn.text_content()
                    print(f"  Clicking: '{text}'")
                    await btn.click()
                    await asyncio.sleep(5)
                    print("  ✓ Work Style step completed")
                    break
            except:
                continue
        
        # Step 11: Career Goals Step
        print("\n=== Step 11: Career Goals Step ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state('networkidle')
        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(3)
        await page.screenshot(path='/tmp/step_careergoals.png')
        
        # Debug: Check what's on the page
        page_text = await page.inner_text('body')
        print(f"  Page content preview: {page_text[:300]}...")
        if 'career' in page_text.lower() or 'goal' in page_text.lower():
            print("  ✓ Confirmed on Career Goals step")
        
        # Find all textareas and text inputs
        all_text_fields = await page.locator('textarea, input[type="text"]').all()
        print(f"  Found {len(all_text_fields)} text fields")
        
        # Fill career goals textarea - try finding by label or placeholder
        goals_filled = False
        try:
            # Try finding by label text
            goal_label = page.locator('text=/career.*goal/i, label:has-text("goal")').first
            if await goal_label.is_visible(timeout=2000):
                goal_textarea = goal_label.locator('xpath=following::textarea[1] | ../textarea | following::input[1]').first
                if await goal_textarea.is_visible(timeout=2000):
                    await goal_textarea.fill("Looking for senior engineering roles in fast-growing tech companies where I can lead technical initiatives and mentor junior developers")
                    print("  ✓ Filled Career Goals (by label)")
                    goals_filled = True
        except:
            pass
        
        if not goals_filled:
            for selector in ['textarea[name*="goal" i]', 'textarea[placeholder*="goal" i]', 'textarea']:
                try:
                    textarea = page.locator(selector).first
                    if await textarea.is_visible(timeout=2000):
                        await textarea.fill("Looking for senior engineering roles in fast-growing tech companies where I can lead technical initiatives and mentor junior developers")
                        print("  ✓ Filled Career Goals")
                        goals_filled = True
                        break
                except:
                    continue
        
        # Fill other text inputs if available
        filled_others = 0
        for inp in all_text_fields:
            try:
                if await inp.is_visible(timeout=1000):
                    placeholder = await inp.get_attribute('placeholder') or ''
                    value = await inp.input_value()
                    # Skip if already filled or if it's not a goal-related field
                    if value or 'email' in placeholder.lower() or 'phone' in placeholder.lower() or 'location' in placeholder.lower():
                        continue
                    await inp.fill("Build innovative products that impact millions of users")
                    filled_others += 1
                    if filled_others >= 2:
                        break
            except:
                pass
        
        if filled_others > 0:
            print(f"  ✓ Filled {filled_others} additional goal fields")
        
        # Click Continue
        for selector in ['button:has-text("Continue")', 'button:has-text("Next")']:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=3000):
                    text = await btn.text_content()
                    print(f"  Clicking: '{text}'")
                    await btn.click()
                    await asyncio.sleep(5)
                    print("  ✓ Career Goals step completed")
                    break
            except:
                continue
        
        # Step 12: Ready/Complete Step
        print("\n=== Step 12: Ready/Complete Step ===")
        await asyncio.sleep(5)
        await page.wait_for_load_state('networkidle')
        await page.wait_for_load_state('domcontentloaded')
        await asyncio.sleep(3)
        await page.screenshot(path='/tmp/step_ready.png')
        
        # Click Complete button
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
                    print(f"  Clicking: '{text}'")
                    await btn.click()
                    await asyncio.sleep(8)  # Wait longer for redirect
                    complete_clicked = True
                    print("  ✓ Ready step completed - Onboarding finished!")
                    break
            except:
                continue
        
        # Step 13: Verify and Test
        print("\n=== Step 13: Verify and Test ===")
        await asyncio.sleep(3)
        final_url = page.url
        print(f"Final URL: {final_url}")
        await page.screenshot(path='/tmp/step_final.png')
        
        if '/app/dashboard' in final_url:
            print("  ✓ Successfully redirected to dashboard")
        else:
            print(f"  ⚠ Still on: {final_url}")
        
        # Print console errors
        if console_errors:
            print(f"\n⚠ Console errors found: {len(console_errors)}")
            for error in console_errors[:10]:
                print(f"  - {error}")
        else:
            print("\n✓ No console errors detected")
        
        print("\nWaiting 5 seconds before closing...")
        await asyncio.sleep(5)
        await browser.close()
        print("\n=== Onboarding Flow Complete ===")

if __name__ == "__main__":
    asyncio.run(complete_onboarding())
