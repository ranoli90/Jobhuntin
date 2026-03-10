#!/usr/bin/env python3
"""
Complete onboarding with proper step verification.
Uses step indicator (STEP X OF 8) and form element presence to verify steps.
"""
import asyncio
from playwright.async_api import async_playwright

SESSION_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxZGRmOTc3YS1hNmM2LTRkMzAtODc4Mi1lYjgwNmJhZDYwNTAiLCJlbWFpbCI6InRlc3R1c2VyXzIyNTJkNTE0QHRlc3QuY29tIiwiYXVkIjoiYXV0aGVudGljYXRlZCIsImp0aSI6IjRlOTZkN2MzLTkyYWUtNGMwOC05NDUwLWRhYjYwY2NkNjdkZSIsInNlc3Npb25faWQiOiJmYzJjZmUwZS04ZDc3LTRmNzMtYmRkZS0yNjkwYWE2NDA1Y2IiLCJpYXQiOjE3NzMxMTQ3NTIsIm5iZiI6MTc3MzExNDc1MiwiZXhwIjoxNzczNzE5NTUyfQ.17bFNT76vtC2ri3TQnS2P-H4P2QOmROOgxjrcDkz-lE"

async def complete_with_verification():
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
        
        # Helper to get step number
        async def get_step_number():
            try:
                step_elem = page.locator('text=/STEP \\d+ OF \\d+/i').first
                if await step_elem.is_visible(timeout=2000):
                    text = await step_elem.text_content() or ""
                    # Extract number: "STEP 4 OF 8" -> 4
                    import re
                    match = re.search(r'STEP (\d+)', text)
                    if match:
                        return int(match.group(1))
            except:
                pass
            return None
        
        # Navigate to Skills step (step 4)
        print("\n=== Navigating to Skills Step ===")
        current_step = await get_step_number()
        print(f"  Current step: {current_step}")
        
        # Click through steps until we reach step 4 (Skills)
        while current_step is None or current_step < 4:
            page_text = await page.inner_text('body')
            
            if current_step == 1 or 'welcome' in page_text.lower():
                start_btn = page.locator('button:has-text("Start setup")').first
                if await start_btn.is_visible(timeout=3000):
                    await start_btn.click()
                    await asyncio.sleep(5)
            
            elif current_step == 2 or 'preferences' in page_text.lower():
                location_input = page.locator('input[placeholder*="location" i]').first
                if await location_input.is_visible(timeout=3000):
                    await location_input.fill("San Francisco, CA")
                    await asyncio.sleep(2)
                save_btn = page.locator('button:has-text("Save preferences")').first
                if await save_btn.is_visible(timeout=3000):
                    await save_btn.click()
                    await asyncio.sleep(5)
            
            elif current_step == 3 or 'resume' in page_text.lower():
                skip_btn = page.locator('button:has-text("Skip for now")').first
                if await skip_btn.is_visible(timeout=3000):
                    await skip_btn.click()
                    await asyncio.sleep(5)
            
            await asyncio.sleep(2)
            current_step = await get_step_number()
            print(f"  Step after navigation: {current_step}")
        
        # Step 4: Skills - Skip it
        print("\n=== Step 4: Skills (Skipping) ===")
        current_step = await get_step_number()
        if current_step == 4:
            skip_btn = page.locator('button:has-text("Skip for now")').first
            if await skip_btn.is_visible(timeout=5000):
                print("  Clicking 'Skip for now'")
                await skip_btn.click()
                await asyncio.sleep(8)
                new_step = await get_step_number()
                if new_step and new_step > 4:
                    print(f"  ✓ Advanced to step {new_step}")
                else:
                    print(f"  ⚠ Still on step {new_step}")
        
        # Step 5: Work Style
        print("\n=== Step 5: Work Style ===")
        await asyncio.sleep(5)
        current_step = await get_step_number()
        print(f"  Current step: {current_step}")
        
        # Verify we're on Work Style by checking for radio buttons
        radios = await page.locator('input[type="radio"]').all()
        if current_step == 5 and len(radios) > 0:
            print("  ✓ Verified on Work Style step (radios present)")
            
            # Answer questions
            selected_groups = set()
            selected = 0
            for radio in radios:
                try:
                    if await radio.is_visible(timeout=1000):
                        name = await radio.get_attribute('name') or ''
                        if name and name not in selected_groups:
                            await radio.check()
                            await asyncio.sleep(0.5)
                            selected += 1
                            selected_groups.add(name)
                            if selected >= 4:
                                break
                except:
                    pass
            
            print(f"  Answered {selected} questions")
            
            # Click Continue
            continue_btn = page.locator('button:has-text("Continue"), button:has-text("Save work style")').first
            if await continue_btn.is_visible(timeout=5000):
                await continue_btn.click()
                await asyncio.sleep(10)
                new_step = await get_step_number()
                print(f"  ✓ Work Style completed, now on step {new_step}")
        else:
            print(f"  ⚠ Not on Work Style step (step={current_step}, radios={len(radios)})")
        
        # Step 6: Career Goals
        print("\n=== Step 6: Career Goals ===")
        await asyncio.sleep(5)
        current_step = await get_step_number()
        print(f"  Current step: {current_step}")
        
        # Verify we're on Career Goals by checking for textarea
        textareas = await page.locator('textarea').all()
        if current_step == 6 and len(textareas) > 0:
            print("  ✓ Verified on Career Goals step (textarea present)")
            
            # Fill textarea
            for textarea in textareas:
                try:
                    if await textarea.is_visible(timeout=3000):
                        value = await textarea.input_value()
                        if not value:
                            await textarea.fill("Looking for senior engineering roles in fast-growing tech companies where I can lead technical initiatives and mentor junior developers")
                            print("  ✓ Filled career goals")
                            await asyncio.sleep(2)
                            break
                except:
                    continue
            
            # Click Continue
            continue_btn = page.locator('button:has-text("Continue"), button:has-text("Next")').first
            if await continue_btn.is_visible(timeout=5000):
                await continue_btn.click()
                await asyncio.sleep(10)
                new_step = await get_step_number()
                print(f"  ✓ Career Goals completed, now on step {new_step}")
        else:
            print(f"  ⚠ Not on Career Goals step (step={current_step}, textareas={len(textareas)})")
        
        # Step 7-8: Ready/Complete
        print("\n=== Step 7-8: Ready/Complete ===")
        await asyncio.sleep(5)
        current_step = await get_step_number()
        print(f"  Current step: {current_step}")
        
        if current_step and current_step >= 7:
            page_text = await page.inner_text('body')
            if 'ready' in page_text.lower() or 'complete' in page_text.lower() or 'finish' in page_text.lower():
                print("  ✓ On Ready step")
                
                # Find Complete button
                all_buttons = await page.locator('button').all()
                for btn in all_buttons:
                    try:
                        if await btn.is_visible(timeout=2000):
                            text = await btn.text_content() or ''
                            if text and ('complete' in text.lower() or 'finish' in text.lower()) and 'back' not in text.lower():
                                print(f"  Clicking: '{text}'")
                                await btn.click()
                                await asyncio.sleep(10)
                                print("  ✓ Onboarding completed!")
                                break
                    except:
                        pass
        
        # Final verification
        print("\n=== Final Verification ===")
        await asyncio.sleep(5)
        final_url = page.url
        print(f"Final URL: {final_url}")
        
        if '/app/dashboard' in final_url:
            print("  ✓ Redirected to dashboard!")
        else:
            print(f"  Still on: {final_url}")
        
        # Check profile
        try:
            import json
            import urllib.request
            req = urllib.request.Request('http://localhost:8000/me/profile')
            req.add_header('Cookie', f'jobhuntin_auth={SESSION_TOKEN}')
            with urllib.request.urlopen(req) as response:
                profile = json.loads(response.read())
                print(f"\n  has_completed_onboarding: {profile.get('has_completed_onboarding', False)}")
                print(f"  Work Style: {bool(profile.get('work_style', {}))}")
                print(f"  Career Goals: {bool(profile.get('career_goals', {}))}")
        except Exception as e:
            print(f"  Error: {e}")
        
        await asyncio.sleep(3)
        await browser.close()
        print("\n=== Complete ===")

if __name__ == "__main__":
    asyncio.run(complete_with_verification())
