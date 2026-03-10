#!/usr/bin/env python3
"""Complete onboarding with fresh token and proper step handling."""
import asyncio
from playwright.async_api import async_playwright

FRESH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxZGRmOTc3YS1hNmM2LTRkMzAtODc4Mi1lYjgwNmJhZDYwNTAiLCJlbWFpbCI6InRlc3R1c2VyXzIyNTJkNTE0QHRlc3QuY29tIiwiYXVkIjoiYXV0aGVudGljYXRlZCIsImp0aSI6ImZjMjc0NjJmLWRjMGQtNDVmNy05ZjczLWZjNzY3MmU1OTViMCIsImlhdCI6MTc3MzEyMDA1MCwibmJmIjoxNzczMTIwMDUwLCJleHAiOjE3NzMyMDY0NTAsIm5ld191c2VyIjpmYWxzZX0.jdR8ghZ96AbXtCpCHPndrU6GzXiL-2RhnSPzdkjCs2Q"

async def complete_onboarding():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        
        # Set fresh auth cookie
        await context.add_cookies([{
            'name': 'jobhuntin_auth',
            'value': FRESH_TOKEN,
            'domain': 'localhost',
            'path': '/',
            'httpOnly': True,
            'secure': False,
            'sameSite': 'Lax'
        }])
        
        page = await context.new_page()
        await page.goto('http://localhost:5173/app/onboarding', wait_until='networkidle')
        await asyncio.sleep(3)
        
        # Track progress
        steps_completed = []
        
        # Step 1: Welcome
        start_btn = page.locator('button:has-text("Start setup")').first
        if await start_btn.is_visible(timeout=5000):
            await start_btn.click()
            await asyncio.sleep(3)
            steps_completed.append("Welcome")
        
        # Step 2: Resume - Skip
        skip_btn = page.locator('button:has-text("Skip for now")').first
        if await skip_btn.is_visible(timeout=5000):
            await skip_btn.click()
            await asyncio.sleep(3)
            steps_completed.append("Resume")
        
        # Step 3: Skills - Click "Add Your First Skill" or "Add Missing Skill"
        add_btn = page.locator('button:has-text("Add"), button:has-text("Add Your First Skill"), button:has-text("Add Missing Skill")').first
        if await add_btn.is_visible(timeout=5000):
            await add_btn.click()
            await asyncio.sleep(1)
            # Fill skill name
            skill_input = page.locator('input[placeholder*="skill" i], input[placeholder*="Skill name" i]').first
            if await skill_input.is_visible(timeout=3000):
                skills = ["Python", "JavaScript", "React", "TypeScript", "FastAPI", "PostgreSQL", "Docker", "AWS"]
                for skill in skills:
                    await skill_input.fill(skill)
                    # Click "Add Skill" button
                    add_skill_btn = page.locator('button[type="submit"], button:has-text("Add Skill")').first
                    if await add_skill_btn.is_visible(timeout=2000):
                        await add_skill_btn.click()
                    else:
                        await skill_input.press("Enter")
                    await asyncio.sleep(1)
                    # Click "Add Your First Skill" again if form closed
                    if not await skill_input.is_visible(timeout=1000):
                        add_btn = page.locator('button:has-text("Add"), button:has-text("Add Missing Skill")').first
                        if await add_btn.is_visible(timeout=2000):
                            await add_btn.click()
                            await asyncio.sleep(1)
                            skill_input = page.locator('input[placeholder*="skill" i]').first
            steps_completed.append("Skills")
        
        # Click Save & Continue on Skills
        save_skills = page.locator('button[data-onboarding-next], button:has-text("Save & Continue"), button:has-text("Continue"):not(:has-text("Restart"))').first
        if await save_skills.is_visible(timeout=5000):
            if not await save_skills.is_disabled():
                await save_skills.click()
                await asyncio.sleep(5)
        
        # Step 4: Contact - Fill if not filled
        first_name = page.locator('input[name*="first" i]').first
        if await first_name.is_visible(timeout=3000):
            if not await first_name.input_value():
                await first_name.fill("John")
        last_name = page.locator('input[name*="last" i]').first
        if await last_name.is_visible(timeout=3000):
            if not await last_name.input_value():
                await last_name.fill("Doe")
        phone = page.locator('input[type="tel"]').first
        if await phone.is_visible(timeout=3000):
            if not await phone.input_value():
                await phone.fill("+1-555-123-4567")
        
        continue_btn = page.locator('button[data-onboarding-next], button:has-text("Continue"):not(:has-text("Restart"))').first
        if await continue_btn.is_visible(timeout=5000):
            if not await continue_btn.is_disabled():
                await continue_btn.click()
                await asyncio.sleep(3)
                steps_completed.append("Contact")
        
        # Step 5: Preferences - Fill if needed, then Save
        location = page.locator('input[placeholder*="location" i]').first
        if await location.is_visible(timeout=3000):
            if not await location.input_value():
                await location.fill("San Francisco")
                await asyncio.sleep(1)
        role = page.locator('input[placeholder*="role" i], input[placeholder*="Product Manager" i]').first
        if await role.is_visible(timeout=3000):
            if not await role.input_value():
                await role.fill("Senior Software Engineer")
        salary_min = page.locator('input[type="number"]').first
        if await salary_min.is_visible(timeout=3000):
            if not await salary_min.input_value():
                await salary_min.fill("100000")
        salary_max_inputs = await page.locator('input[type="number"]').all()
        if len(salary_max_inputs) > 1:
            if not await salary_max_inputs[1].input_value():
                await salary_max_inputs[1].fill("150000")
        remote_cb = page.locator('input[type="checkbox"]').first
        if await remote_cb.is_visible(timeout=3000):
            if not await remote_cb.is_checked():
                await remote_cb.check()
        
        save_prefs = page.locator('button:has-text("Save preferences"), button[data-onboarding-next]').first
        if await save_prefs.is_visible(timeout=5000):
            if not await save_prefs.is_disabled():
                await save_prefs.click()
                await asyncio.sleep(5)
                steps_completed.append("Preferences")
        
        # Step 6: Work Style - Answer 7 questions
        for i in range(7):
            await asyncio.sleep(1)
            # Find visible option buttons
            option_btns = await page.locator('button').all()
            for btn in option_btns:
                try:
                    if await btn.is_visible(timeout=500):
                        text = (await btn.text_content() or '').lower()
                        # Click first reasonable option button
                        if any(word in text for word in ['high', 'medium', 'low', 'async', 'sync', 'fast', 'steady', 'solo', 'team', 'lead', 'early', 'growth', 'enterprise', 'docs', 'building', 'pairing', 'courses', 'ic', 'tech', 'manager', 'founder', 'open', 'flexible', 'methodical']):
                            if 'back' not in text and 'continue' not in text and 'save' not in text and 'skip' not in text:
                                await btn.click()
                                await asyncio.sleep(1.5)
                                break
                except:
                    pass
        
        # Click Save work style
        save_workstyle = page.locator('button[data-onboarding-next], button:has-text("Save"), button:has-text("Continue"):not(:has-text("Restart"))').first
        if await save_workstyle.is_visible(timeout=5000):
            if not await save_workstyle.is_disabled():
                await save_workstyle.click()
                await asyncio.sleep(5)
                steps_completed.append("WorkStyle")
        
        # Step 7: Career Goals
        goals = page.locator('textarea').first
        if await goals.is_visible(timeout=5000):
            await goals.fill("Looking for senior engineering roles in fast-growing tech companies where I can lead technical initiatives")
        
        continue_btn = page.locator('button[data-onboarding-next], button:has-text("Continue"):not(:has-text("Restart"))').first
        if await continue_btn.is_visible(timeout=5000):
            if not await continue_btn.is_disabled():
                await continue_btn.click()
                await asyncio.sleep(3)
                steps_completed.append("CareerGoals")
        
        # Step 8: Complete
        complete = page.locator('button:has-text("Complete"), button:has-text("Finish"), button:has-text("Complete Onboarding")').first
        if await complete.is_visible(timeout=5000):
            if not await complete.is_disabled():
                await complete.click()
                await asyncio.sleep(5)
                steps_completed.append("Complete")
        
        final_url = page.url
        print(f"\nSteps completed: {steps_completed}")
        print(f"Final URL: {final_url}")
        
        await asyncio.sleep(3)
        await browser.close()
        return final_url, steps_completed

if __name__ == "__main__":
    asyncio.run(complete_onboarding())
