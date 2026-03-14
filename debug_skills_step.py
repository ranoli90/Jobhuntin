#!/usr/bin/env python3
"""Debug Skills step to understand what's happening"""

import asyncio

from playwright.async_api import async_playwright

SESSION_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxZGRmOTc3YS1hNmM2LTRkMzAtODc4Mi1lYjgwNmJhZDYwNTAiLCJlbWFpbCI6InRlc3R1c2VyXzIyNTJkNTE0QHRlc3QuY29tIiwiYXVkIjoiYXV0aGVudGljYXRlZCIsImp0aSI6IjRlOTZkN2MzLTkyYWUtNGMwOC05NDUwLWRhYjYwY2NkNjdkZSIsInNlc3Npb25faWQiOiJmYzJjZmUwZS04ZDc3LTRmNzMtYmRkZS0yNjkwYWE2NDA1Y2IiLCJpYXQiOjE3NzMxMTQ3NTIsIm5iZiI6MTc3MzExNDc1MiwiZXhwIjoxNzczNzE5NTUyfQ.17bFNT76vtC2ri3TQnS2P-H4P2QOmROOgxjrcDkz-lE"


async def debug_skills():
    async with async_playwright() as p:
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

        # Navigate through initial steps
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

        # Navigate to Skills step
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

        # Welcome
        current_step = await get_step_number()
        if current_step == 1:
            await page.locator('button:has-text("Start setup")').first.click()
            await asyncio.sleep(8)

        # Preferences
        current_step = await get_step_number()
        if current_step == 2:
            location = page.locator('input[placeholder*="location" i]').first
            if await location.is_visible(timeout=5000):
                await location.fill("San Francisco, CA")
                await asyncio.sleep(3)
            salary_inputs = await page.locator('input[type="number"]').all()
            if len(salary_inputs) > 0:
                await salary_inputs[0].fill("100000")
            if len(salary_inputs) > 1:
                await salary_inputs[1].fill("150000")
            await page.locator('button:has-text("Save preferences")').first.click()
            await asyncio.sleep(8)

        # Resume
        current_step = await get_step_number()
        if current_step == 3:
            await page.locator('button:has-text("Skip for now")').first.click()
            await asyncio.sleep(8)

        # Skills - Debug
        await asyncio.sleep(5)
        current_step = await get_step_number()
        print(f"Current step: {current_step}")

        # Take screenshot
        await page.screenshot(path="/tmp/debug_skills_page.png", full_page=True)

        # Get all buttons
        all_buttons = await page.locator("button").all()
        print(f"\nFound {len(all_buttons)} buttons:")
        for i, btn in enumerate(all_buttons):
            try:
                if await btn.is_visible(timeout=2000):
                    text = await btn.text_content() or ""
                    disabled = await btn.get_attribute("disabled")
                    print(f"  {i + 1}. '{text[:50]}' (disabled: {disabled})")
            except:
                pass

        # Get all inputs
        all_inputs = await page.locator("input, textarea").all()
        print(f"\nFound {len(all_inputs)} inputs:")
        for i, inp in enumerate(all_inputs):
            try:
                if await inp.is_visible(timeout=2000):
                    placeholder = await inp.get_attribute("placeholder") or ""
                    value = await inp.input_value()
                    inp_type = await inp.get_attribute("type") or "text"
                    print(
                        f"  {i + 1}. type={inp_type}, placeholder='{placeholder[:50]}', value='{value[:50]}'"
                    )
            except:
                pass

        # Get page text
        page_text = await page.inner_text("body")
        print(f"\nPage contains 'skill': {'skill' in page_text.lower()}")
        print(f"Page contains 'python': {'python' in page_text.lower()}")
        print(f"Page contains 'save': {'save' in page_text.lower()}")
        print(f"Page contains 'continue': {'continue' in page_text.lower()}")

        # Try to add a skill
        print("\n=== Trying to add skill ===")
        add_btn = page.locator(
            'button:has-text("Add your first skill"), button:has-text("Add a missing skill")'
        ).first
        if await add_btn.is_visible(timeout=5000):
            print("  Found 'Add skill' button, clicking...")
            await add_btn.click()
            await asyncio.sleep(4)
            await page.screenshot(path="/tmp/debug_after_add_click.png")

        # Find input after clicking Add
        skills_input = page.locator('input[type="text"]').first
        if await skills_input.is_visible(timeout=5000):
            print("  Found skills input, filling 'Python'...")
            await skills_input.fill("Python")
            await asyncio.sleep(1)
            await skills_input.press("Enter")
            await asyncio.sleep(3)
            await page.screenshot(path="/tmp/debug_after_python.png")

            # Check if Python was added
            page_text_after = await page.inner_text("body")
            if "python" in page_text_after.lower():
                print("  ✓ Python skill added")
            else:
                print("  ⚠ Python skill not found in page")

        # Find Save button
        print("\n=== Looking for Save button ===")
        save_buttons = []
        for btn in all_buttons:
            try:
                if await btn.is_visible(timeout=2000):
                    text = await btn.text_content() or ""
                    if (
                        ("save" in text.lower() or "continue" in text.lower())
                        and "skip" not in text.lower()
                        and "back" not in text.lower()
                    ):
                        disabled = await btn.get_attribute("disabled")
                        save_buttons.append((text, disabled, btn))
            except:
                pass

        print(f"Found {len(save_buttons)} potential Save buttons:")
        for text, disabled, btn in save_buttons:
            print(f"  '{text}' (disabled: {disabled})")
            if not disabled:
                print(f"  → Clicking '{text}'...")
                await btn.click()
                await asyncio.sleep(10)
                new_step = await get_step_number()
                print(f"  Step after click: {new_step}")
                await page.screenshot(path="/tmp/debug_after_save_click.png")
                break

        await asyncio.sleep(5)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(debug_skills())
