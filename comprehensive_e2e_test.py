#!/usr/bin/env python3
"""
Comprehensive End-to-End Test - Complete flow including resume upload.
Tests: Authentication, Full Onboarding, Dashboard, Job Matching, Job Details, Application.
"""

import asyncio
import json
import os
import re
import time

from playwright.async_api import async_playwright

EMAIL = "testuser_2252d514@test.com"


async def comprehensive_e2e_test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False, args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()

        # Track comprehensive findings
        findings = {
            "step1_authentication": {},
            "step2_onboarding": {},
            "step3_dashboard": {},
            "step4_job_matching": {},
            "step5_job_details": {},
            "step6_application": {},
            "step7_verification": {},
            "screenshots": [],
            "console_errors": [],
            "console_warnings": [],
            "api_calls": [],
            "network_responses": [],
            "performance_metrics": {},
        }

        def track_console(msg):
            if msg.type == "error":
                findings["console_errors"].append(
                    {"text": msg.text, "timestamp": time.time()}
                )
            elif msg.type == "warning":
                findings["console_warnings"].append(
                    {"text": msg.text, "timestamp": time.time()}
                )

        page.on("console", track_console)

        # Track API calls and responses
        def track_request(req):
            if "localhost:8000" in req.url:
                findings["api_calls"].append(
                    {"url": req.url, "method": req.method, "timestamp": time.time()}
                )

        def track_response(resp):
            if "localhost:8000" in resp.url:
                findings["network_responses"].append(
                    {
                        "url": resp.url,
                        "status": resp.status,
                        "status_text": resp.status_text,
                        "timestamp": time.time(),
                    }
                )

        page.on("request", track_request)
        page.on("response", track_response)

        print("=" * 80)
        print("COMPREHENSIVE END-TO-END TEST")
        print("=" * 80)

        # ========================================================================
        # STEP 1: Navigate to Login & Authenticate
        # ========================================================================
        print("\n" + "=" * 80)
        print("STEP 1: Navigate to Login & Authenticate")
        print("=" * 80)

        print("\n1.1 Navigating to Login Page...")
        start_time = time.time()
        await page.goto(
            "http://localhost:5173/login", wait_until="networkidle", timeout=60000
        )
        load_time = time.time() - start_time
        findings["performance_metrics"]["login_page_load"] = load_time
        print(f"   Load time: {load_time:.2f}s")

        await asyncio.sleep(2)

        # Dismiss cookie consent
        try:
            accept_btn = page.locator('button:has-text("Accept all")').first
            if await accept_btn.is_visible(timeout=2000):
                await accept_btn.click()
                await asyncio.sleep(1)
                print("   ✓ Dismissed cookie consent")
        except:
            pass

        await page.screenshot(path="/tmp/step1_login_page.png", full_page=True)
        findings["screenshots"].append("/tmp/step1_login_page.png")

        print("\n1.2 Entering Email...")
        # Use the correct selector found via DOM inspection
        email_input = page.locator("#login-email").first
        if await email_input.is_visible(timeout=5000):
            await email_input.fill(EMAIL)
            await asyncio.sleep(3)  # Wait for validation and button to enable
            print(f"   ✓ Entered email: {EMAIL}")
        else:
            print("   ⚠ Email input not found")

        print("\n1.3 Clicking Send Magic Link...")
        # Find the submit button - look for button with type="submit" that's not disabled
        # and contains "Continue" text (not "Continue with Google")
        submit_btn = None
        try:
            # Get all submit buttons
            all_buttons = await page.locator('button[type="submit"]').all()
            for btn in all_buttons:
                if await btn.is_visible(timeout=1000):
                    text = await btn.text_content() or ""
                    is_disabled = await btn.get_attribute("disabled")
                    aria_disabled = await btn.get_attribute("aria-disabled")
                    # Look for Continue button that's not disabled and not "Continue with Google"
                    if (
                        "Continue" in text
                        and "Google" not in text
                        and not is_disabled
                        and aria_disabled != "true"
                    ):
                        submit_btn = btn
                        break
        except:
            pass

        if submit_btn:
            await submit_btn.click()
            await asyncio.sleep(5)
            print("   ✓ Magic link requested")
            findings["step1_authentication"]["magic_link_requested"] = True
        else:
            # Fallback: try to find by text content
            try:
                submit_btn = page.locator(
                    'button:has-text("Continue"):not(:has-text("Google"))'
                ).first
                is_disabled = await submit_btn.get_attribute("disabled")
                if not is_disabled:
                    await submit_btn.click()
                    await asyncio.sleep(5)
                    print("   ✓ Magic link requested (fallback)")
                    findings["step1_authentication"]["magic_link_requested"] = True
                else:
                    print("   ⚠ Submit button is disabled")
            except Exception as e:
                print(f"   ⚠ Could not click submit button: {e}")

        # Try to get magic link from backend API response or logs
        print("\n1.4 Attempting to Authenticate...")
        await asyncio.sleep(2)

        # Check if we can use verify-magic endpoint directly
        # First, try to get token from backend response
        try:
            # Make API call to get magic link token
            response = await page.evaluate(
                """
                async () => {
                    try {
                        const response = await fetch('http://localhost:8000/auth/magic-link', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({email: arguments[0]})
                        });
                        return await response.json();
                    } catch(e) {
                        return {error: e.message};
                    }
                }
            """,
                EMAIL,
            )

            if response and "status" in response:
                print("   ✓ Magic link API call successful")
                # Try to extract token from recent backend logs
                try:
                    with open("/tmp/backend.log", "r") as f:
                        lines = f.readlines()
                        for line in reversed(lines[-200:]):
                            if "jti" in line.lower() and EMAIL.split("@")[0] in line:
                                # Try to extract jti
                                jti_match = re.search(
                                    r'jti["\s]+([a-f0-9-]+)', line, re.IGNORECASE
                                )
                                if jti_match:
                                    jti = jti_match.group(1)
                                    print(f"   ✓ Found JTI in logs: {jti[:20]}...")
                                    # We'd need the full token, but let's try navigating
                                    break
                except:
                    pass
        except Exception as e:
            print(f"   ⚠ Could not get token: {e}")

        # Wait a bit and check current URL
        await asyncio.sleep(3)
        current_url = page.url
        print(f"   Current URL: {current_url}")

        if "/onboarding" in current_url or "/dashboard" in current_url:
            findings["step1_authentication"]["authenticated"] = True
            print("   ✓ Authenticated successfully")
        elif "/login" in current_url:
            print("   ⚠ Still on login page - will try to proceed")
            # Try navigating directly to onboarding
            await page.goto(
                "http://localhost:5173/app/onboarding",
                wait_until="networkidle",
                timeout=60000,
            )
            await asyncio.sleep(3)
            current_url = page.url
            if "/onboarding" in current_url or "/dashboard" in current_url:
                findings["step1_authentication"]["authenticated"] = True
                print("   ✓ Can access protected routes")

        await page.screenshot(path="/tmp/step1_after_auth.png", full_page=True)
        findings["screenshots"].append("/tmp/step1_after_auth.png")

        # ========================================================================
        # STEP 2: Complete FULL Onboarding (Including Resume Upload)
        # ========================================================================
        print("\n" + "=" * 80)
        print("STEP 2: Complete FULL Onboarding")
        print("=" * 80)

        # Navigate to onboarding
        print("\n2.1 Navigating to Onboarding...")
        await page.goto(
            "http://localhost:5173/app/onboarding",
            wait_until="networkidle",
            timeout=60000,
        )
        await asyncio.sleep(3)

        current_url = page.url
        print(f"   Current URL: {current_url}")

        if "/dashboard" in current_url:
            print("   ✓ Already completed onboarding - redirecting to dashboard")
            findings["step2_onboarding"]["already_complete"] = True
            # Skip to Step 3
        elif "/onboarding" in current_url:
            print("   ✓ On onboarding page - will complete all steps")
            findings["step2_onboarding"]["onboarding_started"] = True

            # Welcome Step
            print("\n2.2 Welcome Step...")
            await asyncio.sleep(2)
            try:
                start_btn = page.locator(
                    'button:has-text("Start"), button:has-text("Continue"), button:has-text("Get Started")'
                ).first
                if await start_btn.is_visible(timeout=5000):
                    await start_btn.click()
                    await asyncio.sleep(3)
                    print("   ✓ Welcome step completed")
            except Exception as e:
                print(f"   ⚠ Welcome step: {e}")

            # Resume Upload Step (CRITICAL)
            print("\n2.3 Resume Upload Step (CRITICAL)...")
            await asyncio.sleep(3)

            # Check if test resume exists
            resume_path = "/workspace/test_resume.txt"
            if os.path.exists(resume_path):
                print(f"   ✓ Test resume found: {resume_path}")

                # Try to find file upload input
                file_input = page.locator('input[type="file"]').first
                if await file_input.is_visible(timeout=5000):
                    print("   ✓ File upload input found")
                    await file_input.set_input_files(resume_path)
                    await asyncio.sleep(2)
                    print("   ✓ Resume file selected")

                    # Wait for parsing
                    print("   ⚠ Waiting for resume parsing...")
                    await asyncio.sleep(8)  # Wait longer for parsing

                    # Check for parsed data
                    page_text = await page.inner_text("body")
                    if (
                        "python" in page_text.lower()
                        or "javascript" in page_text.lower()
                    ):
                        print("   ✓ Skills appear to be extracted")
                        findings["step2_onboarding"]["resume_parsed"] = True

                    await page.screenshot(
                        path="/tmp/step2_resume_uploaded.png", full_page=True
                    )
                    findings["screenshots"].append("/tmp/step2_resume_uploaded.png")
                else:
                    print(
                        "   ⚠ File upload input not found - trying alternative methods"
                    )
                    # Try LinkedIn URL input
                    linkedin_input = page.locator(
                        'input[placeholder*="linkedin" i], input[type="url"]'
                    ).first
                    if await linkedin_input.is_visible(timeout=3000):
                        await linkedin_input.fill("https://linkedin.com/in/johndoe")
                        await asyncio.sleep(2)
                        print("   ✓ LinkedIn URL entered as alternative")
            else:
                print(f"   ⚠ Test resume not found at {resume_path}")

            # Continue from resume step
            continue_btn = page.locator(
                'button:has-text("Continue"), button:has-text("Save")'
            ).first
            if await continue_btn.is_visible(timeout=5000):
                await continue_btn.click()
                await asyncio.sleep(3)
                print("   ✓ Continued from resume step")

            # Skills Review Step
            print("\n2.4 Skills Review Step...")
            await asyncio.sleep(3)

            # Verify extracted skills
            page_text = await page.inner_text("body")
            skills_to_check = [
                "python",
                "javascript",
                "react",
                "typescript",
                "fastapi",
                "postgresql",
                "docker",
                "aws",
            ]
            found_skills = [s for s in skills_to_check if s in page_text.lower()]
            print(f"   Found skills in page: {found_skills}")
            findings["step2_onboarding"]["skills_extracted"] = found_skills

            # Add any missing skills
            for skill in skills_to_check:
                if skill not in found_skills:
                    try:
                        skill_input = page.locator(
                            'input[placeholder*="skill" i], input[placeholder*="Add" i]'
                        ).first
                        if await skill_input.is_visible(timeout=2000):
                            await skill_input.fill(skill.capitalize())
                            await asyncio.sleep(1)
                            await skill_input.press("Enter")
                            await asyncio.sleep(1)
                            print(f"      ✓ Added skill: {skill}")
                    except:
                        pass

            await page.screenshot(path="/tmp/step2_skills_review.png", full_page=True)
            findings["screenshots"].append("/tmp/step2_skills_review.png")

            # Save and continue
            save_btn = page.locator(
                'button:has-text("Save"), button:has-text("Continue")'
            ).first
            if await save_btn.is_visible(timeout=5000):
                await save_btn.click()
                await asyncio.sleep(3)

            # Contact Info Step
            print("\n2.5 Contact Info Step...")
            await asyncio.sleep(3)

            # Fill contact info
            first_name_input = page.locator(
                'input[placeholder*="first" i], input[name*="first" i]'
            ).first
            if await first_name_input.is_visible(timeout=3000):
                await first_name_input.fill("John")
                await asyncio.sleep(1)

            last_name_input = page.locator(
                'input[placeholder*="last" i], input[name*="last" i]'
            ).first
            if await last_name_input.is_visible(timeout=3000):
                await last_name_input.fill("Doe")
                await asyncio.sleep(1)

            phone_input = page.locator(
                'input[type="tel"], input[placeholder*="phone" i]'
            ).first
            if await phone_input.is_visible(timeout=3000):
                await phone_input.fill("+1-555-123-4567")
                await asyncio.sleep(1)

            linkedin_input = page.locator(
                'input[placeholder*="linkedin" i], input[type="url"]'
            ).first
            if await linkedin_input.is_visible(timeout=3000):
                await linkedin_input.fill("https://linkedin.com/in/johndoe")
                await asyncio.sleep(1)

            continue_btn = page.locator('button:has-text("Continue")').first
            if await continue_btn.is_visible(timeout=5000):
                await continue_btn.click()
                await asyncio.sleep(3)

            # Preferences Step
            print("\n2.6 Preferences Step...")
            await asyncio.sleep(3)

            location_input = page.locator(
                'input[placeholder*="location" i], input[placeholder*="city" i]'
            ).first
            if await location_input.is_visible(timeout=3000):
                await location_input.fill("San Francisco, CA")
                await asyncio.sleep(2)
                # Try to select from autocomplete
                try:
                    dropdown_item = page.locator("text=San Francisco").first
                    if await dropdown_item.is_visible(timeout=2000):
                        await dropdown_item.click()
                        await asyncio.sleep(1)
                except:
                    pass

            role_input = page.locator(
                'input[placeholder*="role" i], input[placeholder*="title" i]'
            ).first
            if await role_input.is_visible(timeout=3000):
                await role_input.fill("Senior Software Engineer")
                await asyncio.sleep(1)

            salary_min_input = page.locator(
                'input[placeholder*="min" i], input[type="number"]'
            ).first
            if await salary_min_input.is_visible(timeout=3000):
                await salary_min_input.fill("100000")
                await asyncio.sleep(1)

            salary_max_input = page.locator('input[placeholder*="max" i]').first
            if await salary_max_input.is_visible(timeout=3000):
                await salary_max_input.fill("150000")
                await asyncio.sleep(1)

            remote_checkbox = page.locator(
                'input[type="checkbox"][aria-label*="remote" i], label:has-text("Remote")'
            ).first
            if await remote_checkbox.is_visible(timeout=3000):
                await remote_checkbox.click()
                await asyncio.sleep(1)

            save_prefs_btn = page.locator(
                'button:has-text("Save"), button:has-text("Continue")'
            ).first
            if await save_prefs_btn.is_visible(timeout=5000):
                await save_prefs_btn.click()
                await asyncio.sleep(3)

            # Work Style Step
            print("\n2.7 Work Style Step...")
            await asyncio.sleep(3)

            # Answer work style questions
            for i in range(7):
                try:
                    options = await page.locator('button, input[type="radio"]').all()
                    for option in options[:15]:
                        if await option.is_visible(timeout=1000):
                            try:
                                await option.click()
                                await asyncio.sleep(1)
                                break
                            except:
                                continue
                except:
                    pass

            save_workstyle_btn = page.locator(
                'button:has-text("Save"), button:has-text("Continue")'
            ).first
            if await save_workstyle_btn.is_visible(timeout=5000):
                await save_workstyle_btn.click()
                await asyncio.sleep(3)

            # Career Goals Step
            print("\n2.8 Career Goals Step...")
            await asyncio.sleep(3)

            goals_textarea = page.locator("textarea").first
            if await goals_textarea.is_visible(timeout=3000):
                await goals_textarea.fill(
                    "Looking for senior engineering roles in fast-growing tech companies where I can lead technical initiatives and build scalable systems"
                )
                await asyncio.sleep(1)

            continue_btn = page.locator('button:has-text("Continue")').first
            if await continue_btn.is_visible(timeout=5000):
                await continue_btn.click()
                await asyncio.sleep(3)

            # Complete Step
            print("\n2.9 Complete Onboarding...")
            await asyncio.sleep(3)

            complete_btn = page.locator(
                'button:has-text("Complete"), button:has-text("Finish")'
            ).first
            if await complete_btn.is_visible(timeout=5000):
                await complete_btn.click()
                await asyncio.sleep(5)
                print("   ✓ Onboarding completed")
                findings["step2_onboarding"]["onboarding_complete"] = True

            # Verify redirect
            current_url = page.url
            if "/dashboard" in current_url:
                print("   ✓ Redirected to dashboard")
            else:
                print(f"   ⚠ Unexpected URL: {current_url}")

        await page.screenshot(path="/tmp/step2_onboarding_complete.png", full_page=True)
        findings["screenshots"].append("/tmp/step2_onboarding_complete.png")

        # ========================================================================
        # STEP 3: Test Dashboard
        # ========================================================================
        print("\n" + "=" * 80)
        print("STEP 3: Test Dashboard")
        print("=" * 80)

        # Navigate to dashboard
        print("\n3.1 Navigating to Dashboard...")
        await page.goto(
            "http://localhost:5173/app/dashboard",
            wait_until="networkidle",
            timeout=60000,
        )
        await asyncio.sleep(5)

        current_url = page.url
        print(f"   Current URL: {current_url}")

        if "/dashboard" in current_url:
            findings["step3_dashboard"]["dashboard_loaded"] = True
            print("   ✓ Dashboard loaded")
        else:
            print(f"   ⚠ Not on dashboard: {current_url}")

        page_text = await page.inner_text("body")
        findings["step3_dashboard"]["page_content_length"] = len(page_text)

        # Check for console errors
        unique_errors = list(set([e["text"] for e in findings["console_errors"]]))
        if unique_errors:
            print(f"   ⚠ Console errors found: {len(unique_errors)}")
        else:
            print("   ✓ No console errors")

        await page.screenshot(path="/tmp/step3_dashboard.png", full_page=True)
        findings["screenshots"].append("/tmp/step3_dashboard.png")

        # ========================================================================
        # STEP 4: Test Job Matching System (DEEP DIVE)
        # ========================================================================
        print("\n" + "=" * 80)
        print("STEP 4: Test Job Matching System (DEEP DIVE)")
        print("=" * 80)

        print("\n4.1 Navigating to Jobs Page...")
        start_time = time.time()
        await page.goto(
            "http://localhost:5173/app/jobs", wait_until="networkidle", timeout=60000
        )
        load_time = time.time() - start_time
        findings["performance_metrics"]["jobs_page_load"] = load_time
        print(f"   Load time: {load_time:.2f}s")

        await asyncio.sleep(10)  # Wait for jobs to load

        current_url = page.url
        print(f"   Current URL: {current_url}")

        page_text = await page.inner_text("body")

        # Check for jobs
        print("\n4.2 Checking for Jobs...")
        job_elements = await page.locator(
            'article[role="article"], [role="article"]'
        ).all()
        job_count = len(job_elements)
        findings["step4_job_matching"]["job_count"] = job_count
        print(f"   Found {job_count} job elements")

        if job_count > 0:
            findings["step4_job_matching"]["jobs_displayed"] = True
            print("   ✓ Jobs are displayed")
        else:
            print("   ⚠ No jobs found")

        # Check for match scores
        print("\n4.3 Verifying Match Scores...")
        match_score_pattern = r"(\d+)%"
        matches = re.findall(match_score_pattern, page_text)
        match_scores = [int(m) for m in matches if 0 <= int(m) <= 100]

        if match_scores:
            findings["step4_job_matching"]["match_scores_found"] = True
            findings["step4_job_matching"]["match_scores"] = match_scores
            print(f"   ✓ Match scores found: {match_scores}")
        else:
            print("   ⚠ Match scores not found in text")
            # Try to find match score elements
            try:
                score_elements = await page.locator("text=/match|score|%/i").all()
                if score_elements:
                    print(
                        f"   Found {len(score_elements)} potential match score elements"
                    )
            except:
                pass

        await page.screenshot(path="/tmp/step4_jobs_with_scores.png", full_page=True)
        findings["screenshots"].append("/tmp/step4_jobs_with_scores.png")

        # Test filters (if jobs are loaded)
        if job_count > 0:
            print("\n4.4 Testing Filters...")

            # Location filter
            print("   Testing Location Filter...")
            location_input = page.locator('input[placeholder*="location" i]').first
            if await location_input.is_visible(timeout=3000):
                await location_input.fill("San Francisco")
                await asyncio.sleep(3)
                print("   ✓ Location filter applied")
                findings["step4_job_matching"]["location_filter_tested"] = True
                await page.screenshot(
                    path="/tmp/step4_location_filter.png", full_page=True
                )
                findings["screenshots"].append("/tmp/step4_location_filter.png")

            # Salary filter
            print("   Testing Salary Filter...")
            salary_input = page.locator(
                'input[placeholder*="salary" i], input[type="number"]'
            ).first
            if await salary_input.is_visible(timeout=3000):
                await salary_input.fill("100000")
                await asyncio.sleep(3)
                print("   ✓ Salary filter applied")
                findings["step4_job_matching"]["salary_filter_tested"] = True

            # Remote filter
            print("   Testing Remote Filter...")
            remote_checkbox = page.locator(
                'input[type="checkbox"][aria-label*="remote" i]'
            ).first
            if await remote_checkbox.is_visible(timeout=3000):
                await remote_checkbox.click()
                await asyncio.sleep(3)
                print("   ✓ Remote filter applied")
                findings["step4_job_matching"]["remote_filter_tested"] = True

            # Keyword search
            print("   Testing Keyword Search...")
            search_input = page.locator(
                'input[placeholder*="search" i], input[placeholder*="keyword" i]'
            ).first
            if await search_input.is_visible(timeout=3000):
                await search_input.fill("Python")
                await asyncio.sleep(3)
                print("   ✓ Keyword search applied (Python)")
                findings["step4_job_matching"]["keyword_search_tested"] = True

            # Sorting
            print("   Testing Sorting...")
            sort_select = page.locator('select, button:has-text("Sort")').first
            if await sort_select.is_visible(timeout=3000):
                # Try to select "Match Score"
                try:
                    await sort_select.select_option("match_score")
                    await asyncio.sleep(3)
                    print("   ✓ Sorted by match score")
                    findings["step4_job_matching"]["sorting_tested"] = True
                except:
                    pass

        # ========================================================================
        # STEP 5: Test Job Details
        # ========================================================================
        print("\n" + "=" * 80)
        print("STEP 5: Test Job Details")
        print("=" * 80)

        if job_count > 0:
            print("\n5.1 Clicking on First Job...")
            try:
                await job_elements[0].click()
                await asyncio.sleep(5)
                findings["step5_job_details"]["job_details_opened"] = True
                print("   ✓ Job details opened")

                page_text = await page.inner_text("body")

                # Check for match score in details
                if re.search(r"\d+%", page_text):
                    print("   ✓ Match score found in job details")
                    findings["step5_job_details"]["match_score_in_details"] = True

                # Check for match explanation
                if "match" in page_text.lower() and (
                    "why" in page_text.lower() or "explanation" in page_text.lower()
                ):
                    print("   ✓ Match explanation found")
                    findings["step5_job_details"]["match_explanation_found"] = True

                await page.screenshot(path="/tmp/step5_job_details.png", full_page=True)
                findings["screenshots"].append("/tmp/step5_job_details.png")
            except Exception as e:
                print(f"   ⚠ Error opening job details: {e}")
        else:
            print("   ⚠ No jobs available to test")

        # ========================================================================
        # STEP 6: Test Application Flow
        # ========================================================================
        print("\n" + "=" * 80)
        print("STEP 6: Test Application Flow")
        print("=" * 80)

        if job_count > 0:
            print("\n6.1 Applying to a Job...")
            # Navigate back to jobs list if needed
            if "/jobs" not in page.url:
                await page.goto(
                    "http://localhost:5173/app/jobs", wait_until="networkidle"
                )
                await asyncio.sleep(5)

            # Look for apply button or swipe
            apply_btn = page.locator(
                'button:has-text("Apply"), button:has-text("Swipe")'
            ).first
            if await apply_btn.is_visible(timeout=5000):
                await apply_btn.click()
                await asyncio.sleep(3)
                print("   ✓ Application submitted")
                findings["step6_application"]["application_submitted"] = True
            else:
                print("   ⚠ Apply button not found")

            print("\n6.2 Checking Applications Page...")
            await page.goto(
                "http://localhost:5173/app/applications",
                wait_until="networkidle",
                timeout=60000,
            )
            await asyncio.sleep(5)

            page_text = await page.inner_text("body")
            if "application" in page_text.lower():
                print("   ✓ Applications page loaded")
                findings["step6_application"]["applications_page_loaded"] = True

            await page.screenshot(path="/tmp/step6_applications.png", full_page=True)
            findings["screenshots"].append("/tmp/step6_applications.png")
        else:
            print("   ⚠ No jobs available to test application flow")

        # ========================================================================
        # STEP 7: Deep Verification
        # ========================================================================
        print("\n" + "=" * 80)
        print("STEP 7: Deep Verification")
        print("=" * 80)

        print("\n7.1 Console Errors...")
        unique_errors = list(set([e["text"] for e in findings["console_errors"]]))
        findings["step7_verification"]["console_errors_count"] = len(unique_errors)
        findings["step7_verification"]["console_errors"] = unique_errors[:10]
        print(f"   Total console errors: {len(unique_errors)}")
        for i, err in enumerate(unique_errors[:5], 1):
            print(f"      {i}. {err[:150]}")

        print("\n7.2 Network Requests...")
        jobs_api_calls = [c for c in findings["api_calls"] if "jobs" in c["url"]]
        successful_jobs_calls = [
            r
            for r in findings["network_responses"]
            if "jobs" in r["url"] and r["status"] == 200
        ]
        findings["step7_verification"]["jobs_api_calls"] = len(jobs_api_calls)
        findings["step7_verification"]["successful_jobs_calls"] = len(
            successful_jobs_calls
        )
        print(f"   Jobs API calls: {len(jobs_api_calls)}")
        print(f"   Successful calls: {len(successful_jobs_calls)}")

        print("\n7.3 Performance Metrics...")
        for metric, value in findings["performance_metrics"].items():
            print(f"   {metric}: {value:.2f}s")

        # Final screenshot
        await page.screenshot(path="/tmp/step7_final.png", full_page=True)
        findings["screenshots"].append("/tmp/step7_final.png")

        # ========================================================================
        # Generate Comprehensive Report
        # ========================================================================
        print("\n" + "=" * 80)
        print("COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)

        print("\nStep 1 - Authentication:")
        print(
            f"  Authenticated: {findings['step1_authentication'].get('authenticated', False)}"
        )

        print("\nStep 2 - Onboarding:")
        print(
            f"  Complete: {findings['step2_onboarding'].get('onboarding_complete', False)}"
        )
        print(
            f"  Resume Parsed: {findings['step2_onboarding'].get('resume_parsed', False)}"
        )
        print(
            f"  Skills Extracted: {len(findings['step2_onboarding'].get('skills_extracted', []))}"
        )

        print("\nStep 3 - Dashboard:")
        print(f"  Loaded: {findings['step3_dashboard'].get('dashboard_loaded', False)}")

        print("\nStep 4 - Job Matching:")
        print(
            f"  Jobs Displayed: {findings['step4_job_matching'].get('jobs_displayed', False)}"
        )
        print(f"  Job Count: {findings['step4_job_matching'].get('job_count', 0)}")
        print(
            f"  Match Scores Found: {findings['step4_job_matching'].get('match_scores_found', False)}"
        )
        if findings["step4_job_matching"].get("match_scores"):
            print(f"  Match Scores: {findings['step4_job_matching']['match_scores']}")

        print("\nStep 5 - Job Details:")
        print(
            f"  Job Details Opened: {findings['step5_job_details'].get('job_details_opened', False)}"
        )
        print(
            f"  Match Explanation: {findings['step5_job_details'].get('match_explanation_found', False)}"
        )

        print("\nStep 6 - Application:")
        print(
            f"  Application Submitted: {findings['step6_application'].get('application_submitted', False)}"
        )

        print("\nStep 7 - Verification:")
        print(
            f"  Console Errors: {findings['step7_verification'].get('console_errors_count', 0)}"
        )
        print(
            f"  Successful API Calls: {findings['step7_verification'].get('successful_jobs_calls', 0)}"
        )

        # Save comprehensive findings
        with open("/tmp/comprehensive_e2e_test_findings.json", "w") as f:
            json.dump(findings, f, indent=2)

        print(
            "\n✓ Comprehensive findings saved to /tmp/comprehensive_e2e_test_findings.json"
        )
        print(f"✓ Screenshots saved: {len(findings['screenshots'])}")

        await asyncio.sleep(2)
        await browser.close()

        return findings


if __name__ == "__main__":
    asyncio.run(comprehensive_e2e_test())
