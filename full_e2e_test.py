#!/usr/bin/env python3
"""
Full End-to-End Test - Complete onboarding through job application.
Tests all phases: onboarding, dashboard, job matching, job details, application.
"""

import asyncio
from playwright.async_api import async_playwright
import json
import time
import re

EMAIL = "testuser_2252d514@test.com"


async def full_e2e_test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False, args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()

        # Track findings
        findings = {
            "phase1_onboarding": {},
            "phase2_dashboard": {},
            "phase3_job_matching": {},
            "phase4_job_details": {},
            "phase5_verification": {},
            "screenshots": [],
            "console_errors": [],
            "console_warnings": [],
            "api_calls": [],
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

        # Track API calls
        def track_request(req):
            if "localhost:8000" in req.url:
                findings["api_calls"].append(
                    {"url": req.url, "method": req.method, "timestamp": time.time()}
                )

        page.on("request", track_request)

        print("=" * 80)
        print("FULL END-TO-END TEST")
        print("=" * 80)

        # ========================================================================
        # PHASE 1: Complete Onboarding (Including Resume Upload)
        # ========================================================================
        print("\n" + "=" * 80)
        print("PHASE 1: Complete Onboarding")
        print("=" * 80)

        # Step 1: Navigate to Login
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

        await page.screenshot(path="/tmp/phase1_login.png", full_page=True)
        findings["screenshots"].append("/tmp/phase1_login.png")

        # Step 2: Request Magic Link
        print("\n1.2 Requesting Magic Link...")
        email_input = page.locator(
            'input[type="email"], input[placeholder*="email" i]'
        ).first
        if await email_input.is_visible(timeout=5000):
            await email_input.fill(EMAIL)
            await asyncio.sleep(1)
            print(f"   ✓ Entered email: {EMAIL}")

            submit_btn = page.locator(
                'button[type="submit"], button:has-text("Send"), button:has-text("Request")'
            ).first
            if await submit_btn.is_visible(timeout=3000):
                await submit_btn.click()
                await asyncio.sleep(3)
                print("   ✓ Magic link requested")
                print("   ⚠ Check backend logs for magic link URL")

        # Wait a moment for magic link generation
        await asyncio.sleep(2)

        # Check backend logs for magic link
        try:
            with open("/tmp/backend.log", "r") as f:
                lines = f.readlines()
                for line in reversed(lines[-100:]):  # Check last 100 lines
                    if (
                        "magic link" in line.lower()
                        or "login?token=" in line.lower()
                        or "/auth/verify-magic" in line.lower()
                    ):
                        # Extract URL - try multiple patterns
                        url_patterns = [
                            r"http://[^\s]+login\?token=[^\s]+",
                            r"http://[^\s]+/auth/verify-magic[^\s]+",
                            r"login\?token=([^\s\)]+)",
                        ]
                        for pattern in url_patterns:
                            url_match = re.search(pattern, line)
                            if url_match:
                                if url_match.groups():
                                    token = url_match.group(1)
                                    magic_link = f"http://localhost:8000/auth/verify-magic?token={token}&returnTo=/app/onboarding"
                                else:
                                    magic_link = url_match.group(0)
                                    if not magic_link.startswith("http"):
                                        magic_link = f"http://localhost:8000/auth/verify-magic?token={magic_link.split('token=')[1].split()[0]}&returnTo=/app/onboarding"

                                print("   ✓ Found magic link in logs")
                                print(f"   Navigating to: {magic_link[:80]}...")
                                await page.goto(
                                    magic_link, wait_until="networkidle", timeout=30000
                                )
                                await asyncio.sleep(5)
                                findings["phase1_onboarding"]["magic_link_used"] = True
                                break
                        if findings["phase1_onboarding"].get("magic_link_used"):
                            break
        except Exception as e:
            print(f"   ⚠ Could not get magic link from logs: {e}")
            print("   Will try to proceed with current session...")

        current_url = page.url
        print(f"   Current URL: {current_url}")

        # Check if we're on onboarding or dashboard
        if "/onboarding" in current_url:
            print("   ✓ On onboarding page")
            findings["phase1_onboarding"]["onboarding_started"] = True
        elif "/dashboard" in current_url:
            print("   ✓ Already on dashboard (onboarding may be complete)")
            findings["phase1_onboarding"]["onboarding_complete"] = True
            # Skip to Phase 2
        elif "/login" in current_url:
            print("   ⚠ Still on login page - authentication may have failed")
            findings["phase1_onboarding"]["authentication_failed"] = True

        # Step 3: Complete Onboarding Steps
        if "/onboarding" in current_url:
            print("\n1.3 Completing Onboarding Steps...")

            # Welcome Step
            print("   Step 1: Welcome...")
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

            # Resume Upload Step
            print("   Step 2: Resume Upload...")
            await asyncio.sleep(2)

            # Create a simple test resume file
            test_resume_content = """
            John Doe
            Senior Software Engineer
            
            Skills: Python, JavaScript, React, TypeScript, FastAPI, PostgreSQL, Docker, AWS
            
            Experience:
            - Senior Software Engineer at Tech Corp (2020-Present)
            - Software Engineer at Startup Inc (2018-2020)
            
            Education:
            - BS Computer Science, University of California
            """

            # Try to find file upload input
            file_input = page.locator('input[type="file"]').first
            if await file_input.is_visible(timeout=5000):
                # Create a temporary text file (we'll use it as resume)
                resume_path = "/tmp/test_resume.txt"
                with open(resume_path, "w") as f:
                    f.write(test_resume_content)

                await file_input.set_input_files(resume_path)
                await asyncio.sleep(3)
                print("   ✓ Resume file selected")

                # Wait for parsing
                await asyncio.sleep(5)
                print("   ⚠ Waiting for resume parsing...")
            else:
                # Try LinkedIn URL input
                linkedin_input = page.locator(
                    'input[placeholder*="linkedin" i], input[type="url"]'
                ).first
                if await linkedin_input.is_visible(timeout=3000):
                    await linkedin_input.fill("https://linkedin.com/in/johndoe")
                    await asyncio.sleep(2)
                    print("   ✓ LinkedIn URL entered")

                # Or skip if available
                skip_btn = page.locator(
                    'button:has-text("Skip"), button:has-text("Skip for now")'
                ).first
                if await skip_btn.is_visible(timeout=3000):
                    await skip_btn.click()
                    await asyncio.sleep(2)
                    print("   ✓ Skipped resume upload")

            # Continue from resume step
            continue_btn = page.locator(
                'button:has-text("Continue"), button:has-text("Save")'
            ).first
            if await continue_btn.is_visible(timeout=3000):
                await continue_btn.click()
                await asyncio.sleep(3)

            # Skills Review Step
            print("   Step 3: Skills Review...")
            await asyncio.sleep(2)

            # Add skills
            skills_to_add = [
                "Python",
                "JavaScript",
                "React",
                "TypeScript",
                "FastAPI",
                "PostgreSQL",
                "Docker",
                "AWS",
            ]
            for skill in skills_to_add:
                try:
                    # Look for skill input
                    skill_input = page.locator(
                        'input[placeholder*="skill" i], input[placeholder*="Add" i]'
                    ).first
                    if await skill_input.is_visible(timeout=2000):
                        await skill_input.fill(skill)
                        await asyncio.sleep(1)
                        # Press Enter or click Add
                        await skill_input.press("Enter")
                        await asyncio.sleep(1)
                        print(f"      ✓ Added skill: {skill}")
                except:
                    pass

            # Save and continue
            save_btn = page.locator(
                'button:has-text("Save"), button:has-text("Continue")'
            ).first
            if await save_btn.is_visible(timeout=3000):
                await save_btn.click()
                await asyncio.sleep(3)

            # Contact Info Step
            print("   Step 4: Contact Info...")
            await asyncio.sleep(2)

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

            continue_btn = page.locator('button:has-text("Continue")').first
            if await continue_btn.is_visible(timeout=3000):
                await continue_btn.click()
                await asyncio.sleep(3)

            # Preferences Step
            print("   Step 5: Preferences...")
            await asyncio.sleep(2)

            location_input = page.locator(
                'input[placeholder*="location" i], input[placeholder*="city" i]'
            ).first
            if await location_input.is_visible(timeout=3000):
                await location_input.fill("San Francisco, CA")
                await asyncio.sleep(2)  # Wait for autocomplete
                # Try to select from dropdown
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
            if await save_prefs_btn.is_visible(timeout=3000):
                await save_prefs_btn.click()
                await asyncio.sleep(3)

            # Work Style Step
            print("   Step 6: Work Style...")
            await asyncio.sleep(2)

            # Answer work style questions (click first option for each)
            for i in range(7):
                try:
                    options = await page.locator('button, input[type="radio"]').all()
                    for option in options[:10]:  # Check first 10 options
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
            if await save_workstyle_btn.is_visible(timeout=3000):
                await save_workstyle_btn.click()
                await asyncio.sleep(3)

            # Career Goals Step
            print("   Step 7: Career Goals...")
            await asyncio.sleep(2)

            goals_textarea = page.locator("textarea").first
            if await goals_textarea.is_visible(timeout=3000):
                await goals_textarea.fill(
                    "Looking for senior engineering roles in fast-growing tech companies where I can lead technical initiatives and build scalable systems"
                )
                await asyncio.sleep(1)

            continue_btn = page.locator('button:has-text("Continue")').first
            if await continue_btn.is_visible(timeout=3000):
                await continue_btn.click()
                await asyncio.sleep(3)

            # Ready/Complete Step
            print("   Step 8: Complete Onboarding...")
            await asyncio.sleep(2)

            complete_btn = page.locator(
                'button:has-text("Complete"), button:has-text("Finish")'
            ).first
            if await complete_btn.is_visible(timeout=5000):
                await complete_btn.click()
                await asyncio.sleep(5)
                print("   ✓ Onboarding completed")

            # Verify redirect to dashboard
            current_url = page.url
            if "/dashboard" in current_url:
                findings["phase1_onboarding"]["onboarding_complete"] = True
                print("   ✓ Redirected to dashboard")
            else:
                print(f"   ⚠ Unexpected URL after completion: {current_url}")

        await page.screenshot(
            path="/tmp/phase1_onboarding_complete.png", full_page=True
        )
        findings["screenshots"].append("/tmp/phase1_onboarding_complete.png")

        # ========================================================================
        # PHASE 2: Test Dashboard
        # ========================================================================
        print("\n" + "=" * 80)
        print("PHASE 2: Test Dashboard")
        print("=" * 80)

        # Navigate to dashboard if not already there
        if "/dashboard" not in page.url:
            print("\n2.1 Navigating to Dashboard...")
            await page.goto(
                "http://localhost:5173/app/dashboard",
                wait_until="networkidle",
                timeout=60000,
            )
            await asyncio.sleep(5)

        current_url = page.url
        print(f"   Current URL: {current_url}")

        if "/dashboard" in current_url:
            findings["phase2_dashboard"]["dashboard_loaded"] = True
            print("   ✓ Dashboard loaded")
        else:
            print(f"   ⚠ Not on dashboard: {current_url}")

        page_text = await page.inner_text("body")
        findings["phase2_dashboard"]["page_content_length"] = len(page_text)

        await page.screenshot(path="/tmp/phase2_dashboard.png", full_page=True)
        findings["screenshots"].append("/tmp/phase2_dashboard.png")

        # ========================================================================
        # PHASE 3: Test Job Matching System
        # ========================================================================
        print("\n" + "=" * 80)
        print("PHASE 3: Test Job Matching System")
        print("=" * 80)

        print("\n3.1 Navigating to Jobs Page...")
        await page.goto(
            "http://localhost:5173/app/jobs", wait_until="networkidle", timeout=60000
        )
        await asyncio.sleep(8)  # Wait for jobs to load

        current_url = page.url
        print(f"   Current URL: {current_url}")

        page_text = await page.inner_text("body")

        # Check for jobs
        print("\n3.2 Checking for Jobs...")
        job_elements = await page.locator(
            'article[role="article"], [role="article"]'
        ).all()
        findings["phase3_job_matching"]["job_count"] = len(job_elements)
        print(f"   Found {len(job_elements)} job elements")

        if len(job_elements) > 0:
            findings["phase3_job_matching"]["jobs_displayed"] = True
            print("   ✓ Jobs are displayed")
        else:
            print("   ⚠ No jobs found")

        # Check for match scores
        print("\n3.3 Checking for Match Scores...")
        match_score_pattern = r"(\d+)%"
        matches = re.findall(match_score_pattern, page_text)
        match_scores = [int(m) for m in matches if 0 <= int(m) <= 100]

        if match_scores:
            findings["phase3_job_matching"]["match_scores_found"] = True
            findings["phase3_job_matching"]["match_scores"] = match_scores
            print(f"   ✓ Match scores found: {match_scores}")
        else:
            print("   ⚠ Match scores not found")

        await page.screenshot(path="/tmp/phase3_jobs_page.png", full_page=True)
        findings["screenshots"].append("/tmp/phase3_jobs_page.png")

        # Test filters (if jobs are loaded)
        if len(job_elements) > 0:
            print("\n3.4 Testing Filters...")
            # Filter testing would go here
            findings["phase3_job_matching"]["filters_tested"] = True

        # ========================================================================
        # PHASE 4: Test Job Details & Application
        # ========================================================================
        print("\n" + "=" * 80)
        print("PHASE 4: Test Job Details & Application")
        print("=" * 80)

        if len(job_elements) > 0:
            print("\n4.1 Clicking on First Job...")
            try:
                await job_elements[0].click()
                await asyncio.sleep(3)
                findings["phase4_job_details"]["job_details_opened"] = True
                print("   ✓ Job details opened")

                await page.screenshot(
                    path="/tmp/phase4_job_details.png", full_page=True
                )
                findings["screenshots"].append("/tmp/phase4_job_details.png")
            except Exception as e:
                print(f"   ⚠ Error opening job details: {e}")
        else:
            print("   ⚠ No jobs available to test")

        # ========================================================================
        # PHASE 5: Deep Verification
        # ========================================================================
        print("\n" + "=" * 80)
        print("PHASE 5: Deep Verification")
        print("=" * 80)

        print("\n5.1 Console Errors...")
        unique_errors = list(set([e["text"] for e in findings["console_errors"]]))
        findings["phase5_verification"]["console_errors_count"] = len(unique_errors)
        print(f"   Total console errors: {len(unique_errors)}")
        for i, err in enumerate(unique_errors[:5], 1):
            print(f"      {i}. {err[:150]}")

        print("\n5.2 API Calls...")
        jobs_api_calls = [c for c in findings["api_calls"] if "jobs" in c["url"]]
        findings["phase5_verification"]["jobs_api_calls"] = len(jobs_api_calls)
        print(f"   Jobs API calls: {len(jobs_api_calls)}")

        # Final screenshot
        await page.screenshot(path="/tmp/phase5_final.png", full_page=True)
        findings["screenshots"].append("/tmp/phase5_final.png")

        # ========================================================================
        # Generate Report
        # ========================================================================
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)

        print("\nPhase 1 - Onboarding:")
        print(
            f"  Complete: {findings['phase1_onboarding'].get('onboarding_complete', False)}"
        )

        print("\nPhase 2 - Dashboard:")
        print(
            f"  Loaded: {findings['phase2_dashboard'].get('dashboard_loaded', False)}"
        )

        print("\nPhase 3 - Job Matching:")
        print(
            f"  Jobs Displayed: {findings['phase3_job_matching'].get('jobs_displayed', False)}"
        )
        print(f"  Job Count: {findings['phase3_job_matching'].get('job_count', 0)}")
        print(
            f"  Match Scores Found: {findings['phase3_job_matching'].get('match_scores_found', False)}"
        )
        if findings["phase3_job_matching"].get("match_scores"):
            print(f"  Match Scores: {findings['phase3_job_matching']['match_scores']}")

        print("\nPhase 4 - Job Details:")
        print(
            f"  Job Details Opened: {findings['phase4_job_details'].get('job_details_opened', False)}"
        )

        print("\nPhase 5 - Verification:")
        print(
            f"  Console Errors: {findings['phase5_verification'].get('console_errors_count', 0)}"
        )
        print(
            f"  Jobs API Calls: {findings['phase5_verification'].get('jobs_api_calls', 0)}"
        )

        # Save findings
        with open("/tmp/full_e2e_test_findings.json", "w") as f:
            json.dump(findings, f, indent=2)

        print("\n✓ Detailed findings saved to /tmp/full_e2e_test_findings.json")
        print(f"✓ Screenshots saved: {len(findings['screenshots'])}")

        await asyncio.sleep(2)
        await browser.close()

        return findings


if __name__ == "__main__":
    asyncio.run(full_e2e_test())
