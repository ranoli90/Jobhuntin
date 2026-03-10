#!/usr/bin/env python3
"""Complete onboarding by first authenticating via verify-magic, then completing all steps."""
import asyncio
import httpx
from playwright.async_api import async_playwright

FRESH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxZGRmOTc3YS1hNmM2LTRkMzAtODc4Mi1lYjgwNmJhZDYwNTAiLCJlbWFpbCI6InRlc3R1c2VyXzIyNTJkNTE0QHRlc3QuY29tIiwiYXVkIjoiYXV0aGVudGljYXRlZCIsImp0aSI6ImZjMjc0NjJmLWRjMGQtNDVmNy05ZjczLWZjNzY3MmU1OTViMCIsImlhdCI6MTc3MzEyMDA1MCwibmJmIjoxNzczMTIwMDUwLCJleHAiOjE3NzMyMDY0NTAsIm5ld191c2VyIjpmYWxzZX0.jdR8ghZ96AbXtCpCHPndrU6GzXiL-2RhnSPzdkjCs2Q"

async def authenticate_and_complete():
    # Step 1: Authenticate via verify-magic to get session cookie
    async with httpx.AsyncClient(follow_redirects=False) as client:
        resp = await client.get(
            f"http://localhost:8000/api/auth/verify-magic?token={FRESH_TOKEN}&returnTo=/app/onboarding"
        )
        print(f"Auth response status: {resp.status_code}")
        print(f"Auth cookies: {resp.cookies}")
        print(f"Auth headers: {dict(resp.headers)}")
        
        # Get the session cookie
        session_cookie = resp.cookies.get('jobhuntin_auth') or resp.cookies.get('session')
        csrf_cookie = resp.cookies.get('csrftoken')
        
        if not session_cookie:
            print("ERROR: No session cookie received!")
            print(f"All cookies: {resp.cookies}")
            return
    
    # Step 2: Use Playwright with the session cookie
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        
        # Set cookies from auth response
        cookies_to_set = []
        if session_cookie:
            cookies_to_set.append({
                'name': 'jobhuntin_auth',
                'value': session_cookie,
                'domain': 'localhost',
                'path': '/',
                'httpOnly': True,
                'secure': False,
                'sameSite': 'Lax'
            })
        if csrf_cookie:
            cookies_to_set.append({
                'name': 'csrftoken',
                'value': csrf_cookie,
                'domain': 'localhost',
                'path': '/',
                'httpOnly': False,
                'secure': False,
                'sameSite': 'None'
            })
        
        if cookies_to_set:
            await context.add_cookies(cookies_to_set)
            print(f"Set {len(cookies_to_set)} cookies in browser context")
        
        page = await context.new_page()
        await page.goto('http://localhost:5173/app/onboarding', wait_until='networkidle')
        await asyncio.sleep(3)
        
        # Check if we're logged in
        current_url = page.url
        print(f"Initial URL: {current_url}")
        if 'login' in current_url:
            print("ERROR: Still redirected to login!")
            await asyncio.sleep(5)
            await browser.close()
            return
        
        steps_completed = []
        
        # Step 1: Welcome - Click "Start setup" or "Continue"
        try:
            start_btn = page.locator('button:has-text("Start setup"), button:has-text("Continue"):not(:has-text("Restart"))').first
            if await start_btn.is_visible(timeout=5000):
                await start_btn.click()
                await asyncio.sleep(3)
                steps_completed.append("Welcome")
                print("✓ Welcome step")
        except Exception as e:
            print(f"Welcome step: {e}")
        
        # Step 2: Resume - Skip
        try:
            skip_btn = page.locator('button:has-text("Skip for now"), button:has-text("Skip")').first
            if await skip_btn.is_visible(timeout=5000):
                await skip_btn.click()
                await asyncio.sleep(3)
                steps_completed.append("Resume")
                print("✓ Resume step (skipped)")
        except Exception as e:
            print(f"Resume step: {e}")
        
        # Step 3: Skills
        try:
            # Look for "Add Your First Skill" or existing skills
            add_btn = page.locator('button:has-text("Add"), button:has-text("Add Your First Skill"), button:has-text("Add Missing Skill")').first
            if await add_btn.is_visible(timeout=5000):
                skills = ["Python", "JavaScript", "React", "TypeScript", "FastAPI", "PostgreSQL", "Docker", "AWS"]
                for skill in skills:
                    await add_btn.click()
                    await asyncio.sleep(1)
                    skill_input = page.locator('input[placeholder*="skill" i], input[placeholder*="Skill name" i]').first
                    if await skill_input.is_visible(timeout=3000):
                        await skill_input.fill(skill)
                        await asyncio.sleep(0.5)
                        # Try Enter or Add button
                        add_skill_btn = page.locator('button[type="submit"], button:has-text("Add Skill"), button:has-text("Add")').first
                        if await add_skill_btn.is_visible(timeout=2000):
                            await add_skill_btn.click()
                        else:
                            await skill_input.press("Enter")
                        await asyncio.sleep(1.5)
                        # Re-find add button if form closed
                        add_btn = page.locator('button:has-text("Add"), button:has-text("Add Missing Skill")').first
                steps_completed.append("Skills")
                print("✓ Skills step")
        except Exception as e:
            print(f"Skills step: {e}")
        
        # Save & Continue on Skills
        try:
            save_skills = page.locator('button[data-onboarding-next], button:has-text("Save & Continue"), button:has-text("Continue"):not(:has-text("Restart"))').first
            if await save_skills.is_visible(timeout=5000):
                await save_skills.wait_for(state='visible', timeout=5000)
                if not await save_skills.is_disabled():
                    await save_skills.click()
                    await asyncio.sleep(5)
                    print("✓ Saved skills")
        except Exception as e:
            print(f"Save skills: {e}")
        
        # Step 4: Contact
        try:
            first_name = page.locator('input[name*="first" i], input[placeholder*="First name" i]').first
            if await first_name.is_visible(timeout=5000):
                if not await first_name.input_value():
                    await first_name.fill("John")
            last_name = page.locator('input[name*="last" i], input[placeholder*="Last name" i]').first
            if await last_name.is_visible(timeout=5000):
                if not await last_name.input_value():
                    await last_name.fill("Doe")
            phone = page.locator('input[type="tel"], input[placeholder*="phone" i]').first
            if await phone.is_visible(timeout=5000):
                if not await phone.input_value():
                    await phone.fill("+1-555-123-4567")
            
            continue_btn = page.locator('button[data-onboarding-next], button:has-text("Continue"):not(:has-text("Restart"))').first
            if await continue_btn.is_visible(timeout=5000):
                if not await continue_btn.is_disabled():
                    await continue_btn.click()
                    await asyncio.sleep(3)
                    steps_completed.append("Contact")
                    print("✓ Contact step")
        except Exception as e:
            print(f"Contact step: {e}")
        
        # Step 5: Preferences
        try:
            location = page.locator('input[placeholder*="location" i], input[name*="location" i]').first
            if await location.is_visible(timeout=5000):
                if not await location.input_value():
                    await location.fill("San Francisco, CA")
                    await asyncio.sleep(2)  # Wait for autocomplete
            
            role = page.locator('input[placeholder*="role" i], input[name*="role" i]').first
            if await role.is_visible(timeout=5000):
                if not await role.input_value():
                    await role.fill("Senior Software Engineer")
            
            salary_inputs = await page.locator('input[type="number"]').all()
            if len(salary_inputs) >= 2:
                if not await salary_inputs[0].input_value():
                    await salary_inputs[0].fill("100000")
                if not await salary_inputs[1].input_value():
                    await salary_inputs[1].fill("150000")
            
            remote_cb = page.locator('input[type="checkbox"]').first
            if await remote_cb.is_visible(timeout=5000):
                if not await remote_cb.is_checked():
                    await remote_cb.check()
            
            save_prefs = page.locator('button:has-text("Save preferences"), button[data-onboarding-next], button:has-text("Continue"):not(:has-text("Restart"))').first
            if await save_prefs.is_visible(timeout=5000):
                if not await save_prefs.is_disabled():
                    await save_prefs.click()
                    await asyncio.sleep(5)
                    steps_completed.append("Preferences")
                    print("✓ Preferences step")
        except Exception as e:
            print(f"Preferences step: {e}")
        
        # Step 6: Work Style
        try:
            # Answer 7 questions by clicking option buttons
            for q in range(7):
                await asyncio.sleep(1)
                # Find all visible buttons
                all_btns = await page.locator('button').all()
                clicked = False
                for btn in all_btns:
                    try:
                        if await btn.is_visible(timeout=500):
                            text = (await btn.text_content() or '').strip().lower()
                            # Skip navigation buttons
                            if any(x in text for x in ['back', 'continue', 'save', 'skip', 'restart', 'finish', 'complete']):
                                continue
                            # Click first option button
                            if len(text) > 0 and len(text) < 50:
                                await btn.click()
                                clicked = True
                                await asyncio.sleep(1.5)
                                break
                    except:
                        pass
                if not clicked:
                    print(f"  Warning: Could not click option for question {q+1}")
            
            # Save work style
            save_workstyle = page.locator('button[data-onboarding-next], button:has-text("Save"), button:has-text("Continue"):not(:has-text("Restart"))').first
            if await save_workstyle.is_visible(timeout=5000):
                if not await save_workstyle.is_disabled():
                    await save_workstyle.click()
                    await asyncio.sleep(5)
                    steps_completed.append("WorkStyle")
                    print("✓ Work Style step")
        except Exception as e:
            print(f"Work Style step: {e}")
        
        # Step 7: Career Goals
        try:
            goals = page.locator('textarea').first
            if await goals.is_visible(timeout=5000):
                await goals.fill("Looking for senior engineering roles in fast-growing tech companies where I can lead technical initiatives and build scalable systems.")
            
            continue_btn = page.locator('button[data-onboarding-next], button:has-text("Continue"):not(:has-text("Restart"))').first
            if await continue_btn.is_visible(timeout=5000):
                if not await continue_btn.is_disabled():
                    await continue_btn.click()
                    await asyncio.sleep(3)
                    steps_completed.append("CareerGoals")
                    print("✓ Career Goals step")
        except Exception as e:
            print(f"Career Goals step: {e}")
        
        # Step 8: Complete
        try:
            complete = page.locator('button:has-text("Complete"), button:has-text("Finish"), button:has-text("Complete Onboarding")').first
            if await complete.is_visible(timeout=5000):
                if not await complete.is_disabled():
                    await complete.click()
                    await asyncio.sleep(5)
                    steps_completed.append("Complete")
                    print("✓ Complete step")
        except Exception as e:
            print(f"Complete step: {e}")
        
        final_url = page.url
        print(f"\n=== SUMMARY ===")
        print(f"Steps completed: {steps_completed}")
        print(f"Final URL: {final_url}")
        
        await asyncio.sleep(5)
        await browser.close()
        return final_url, steps_completed

if __name__ == "__main__":
    asyncio.run(authenticate_and_complete())
