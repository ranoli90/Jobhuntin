#!/usr/bin/env python3
"""
Comprehensive job search test after backend restart.
Tests: job loading, match scores, filters, sorting, job details, console errors.
"""

import asyncio
from playwright.async_api import async_playwright
import json
import time
import re

SESSION_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxZGRmOTc3YS1hNmM2LTRkMzAtODc4Mi1lYjgwNmJhZDYwNTAiLCJlbWFpbCI6InRlc3R1c2VyXzIyNTJkNTE0QHRlc3QuY29tIiwiYXVkIjoiYXV0aGVudGljYXRlZCIsImp0aSI6IjRlOTZkN2MzLTkyYWUtNGMwOC05NDUwLWRhYjYwY2NkNjdkZSIsInNlc3Npb25faWQiOiJmYzJjZmUwZS04ZDc3LTRmNzMtYmRkZS0yNjkwYWE2NDA1Y2IiLCJpYXQiOjE3NzMxMTQ3NTIsIm5iZiI6MTc3MzExNDc1MiwiZXhwIjoxNzczNzE5NTUyfQ.17bFNT76vtC2ri3TQnS2P-H4P2QOmROOgxjrcDkz-lE"
EMAIL = "testuser_2252d514@test.com"


async def test_jobs_comprehensive():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False, args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})

        # Set auth cookie
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

        # Track findings
        findings = {
            "redirected_to_login": False,
            "authenticated": False,
            "jobs_page_loaded": False,
            "jobs_displayed": False,
            "job_count": 0,
            "match_scores_found": False,
            "match_scores": [],
            "filters_tested": {},
            "sorting_tested": {},
            "job_details_accessed": False,
            "console_errors": [],
            "console_warnings": [],
            "api_responses": [],
            "screenshots": [],
        }

        def track_console(msg):
            if msg.type == "error":
                findings["console_errors"].append(msg.text)
            elif msg.type == "warning":
                findings["console_warnings"].append(msg.text)

        page.on("console", track_console)

        # Track API responses
        def track_response(resp):
            if "localhost:8000" in resp.url and (
                "jobs" in resp.url or "profile" in resp.url
            ):
                findings["api_responses"].append(
                    {
                        "url": resp.url,
                        "status": resp.status,
                        "status_text": resp.status_text,
                    }
                )

        page.on("response", track_response)

        print("=== Comprehensive Job Search Test ===\n")

        # Step 1: Navigate to Jobs Page
        print("1. Navigating to Jobs Page...")
        start_time = time.time()
        await page.goto(
            "http://localhost:5173/app/jobs", wait_until="networkidle", timeout=60000
        )
        load_time = time.time() - start_time
        print(f"   Load time: {load_time:.2f}s")

        await asyncio.sleep(5)  # Wait for content to render

        current_url = page.url
        print(f"   Current URL: {current_url}")

        # Check if redirected to login
        if "/login" in current_url:
            findings["redirected_to_login"] = True
            print("   ⚠ Redirected to login - going through login flow...")

            # Dismiss cookie consent if present
            try:
                accept_btn = page.locator('button:has-text("Accept all")').first
                if await accept_btn.is_visible(timeout=2000):
                    await accept_btn.click()
                    await asyncio.sleep(1)
            except:
                pass

            # Enter email
            email_input = page.locator(
                'input[type="email"], input[placeholder*="email" i]'
            ).first
            if await email_input.is_visible(timeout=5000):
                await email_input.fill(EMAIL)
                await asyncio.sleep(1)

                # Click send magic link
                submit_btn = page.locator(
                    'button[type="submit"], button:has-text("Send"), button:has-text("Request")'
                ).first
                if await submit_btn.is_visible(timeout=3000):
                    await submit_btn.click()
                    await asyncio.sleep(3)
                    print("   ✓ Magic link requested")

            # Check backend logs for magic link or wait
            print("   ⚠ Need magic link from backend logs to complete login")
            print("   Will proceed with current session state...")

            # Try navigating to jobs again
            await page.goto(
                "http://localhost:5173/app/jobs",
                wait_until="networkidle",
                timeout=60000,
            )
            await asyncio.sleep(5)
            current_url = page.url

            if "/login" in current_url:
                print(
                    "   ❌ Still on login page - cannot proceed without authentication"
                )
                await page.screenshot(
                    path="/tmp/jobs_login_required.png", full_page=True
                )
                findings["screenshots"].append("/tmp/jobs_login_required.png")

                with open("/tmp/jobs_test_findings.json", "w") as f:
                    json.dump(findings, f, indent=2)

                print("\n=== Test Summary ===")
                print("⚠ Authentication required - cannot test job search")
                print("✓ Findings saved to /tmp/jobs_test_findings.json")

                await browser.close()
                return findings
            else:
                findings["authenticated"] = True
                print("   ✓ Authenticated successfully")

        if "/jobs" in current_url or "/app/jobs" in current_url:
            findings["jobs_page_loaded"] = True
            print("   ✓ Jobs page loaded")
        else:
            print(f"   ⚠ Unexpected URL: {current_url}")

        # Take initial screenshot
        await page.screenshot(path="/tmp/jobs_page_initial.png", full_page=True)
        findings["screenshots"].append("/tmp/jobs_page_initial.png")
        print("   ✓ Screenshot saved")

        # Step 2: Check for Jobs Displayed
        print("\n2. Checking for Jobs Displayed...")
        await asyncio.sleep(5)  # Wait for jobs to load

        page_text = await page.inner_text("body")

        # Check if still loading
        if "loading" in page_text.lower() and "no jobs" not in page_text.lower():
            print("   ⚠ Page still showing loading state, waiting longer...")
            await asyncio.sleep(5)
            page_text = await page.inner_text("body")

        # Look for job cards/listings
        job_selectors = [
            'article[role="article"]',
            '[role="article"]',
            '[data-testid*="job"]',
            '[class*="job-card"]',
            '[class*="JobCard"]',
        ]

        jobs_found = False
        job_elements = []

        for selector in job_selectors:
            try:
                elements = await page.locator(selector).all()
                if len(elements) > 0:
                    print(
                        f"   Found {len(elements)} elements with selector: {selector}"
                    )
                    for elem in elements:
                        text = await elem.text_content() or ""
                        # Check if it looks like a job card
                        if any(
                            keyword in text.lower()
                            for keyword in [
                                "engineer",
                                "developer",
                                "software",
                                "company",
                                "salary",
                                "location",
                                "remote",
                                "apply",
                            ]
                        ):
                            job_elements.append(elem)
                            jobs_found = True
                    if jobs_found:
                        break
            except:
                continue

        # Also count by looking for job titles
        job_titles = await page.locator(
            'h2, h3, [class*="title"], [class*="Title"]'
        ).all()
        potential_jobs = []
        for title in job_titles:
            text = await title.text_content() or ""
            if any(
                keyword in text.lower()
                for keyword in [
                    "engineer",
                    "developer",
                    "software",
                    "manager",
                    "analyst",
                ]
            ):
                potential_jobs.append(text)

        if jobs_found or potential_jobs:
            findings["jobs_displayed"] = True
            job_count = max(len(job_elements), len(potential_jobs))
            findings["job_count"] = job_count
            print(f"   ✓ Jobs displayed (found {job_count} jobs)")
            if potential_jobs:
                print(f"   Job titles found: {', '.join(potential_jobs[:3])}")
        else:
            print("   ⚠ No jobs clearly visible")
            if "no jobs" in page_text.lower() or "empty" in page_text.lower():
                print("   ⚠ Page indicates no jobs available")

        # Step 3: Check for Match Scores
        print("\n3. Checking for Match Scores...")
        match_score_patterns = [
            r"(\d+)%",  # Percentage match
            r"match.*?(\d+)%",
            r"(\d+)%.*?match",
            r"score.*?(\d+)",
            r"(\d+).*?score",
        ]

        match_scores_found = False
        match_scores = []

        # Look for match score indicators in page text
        for pattern in match_score_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            if matches:
                for match in matches:
                    try:
                        score = int(match)
                        if 0 <= score <= 100:  # Valid match score range
                            match_scores.append(score)
                            match_scores_found = True
                    except:
                        continue

        # Also look for visual indicators
        match_indicators = ["match", "score", "%", "compatibility", "fit"]
        for indicator in match_indicators:
            try:
                elems = await page.locator(f"text=/{indicator}/i").all()
                for elem in elems[:5]:
                    if await elem.is_visible(timeout=1000):
                        text = await elem.text_content() or ""
                        # Check if it contains a number
                        if re.search(r"\d+", text):
                            print(f"   ✓ Found match score indicator: '{indicator}'")
                            print(f"      Text: {text[:100]}")
                            match_scores_found = True
                            # Extract number
                            num_match = re.search(r"(\d+)", text)
                            if num_match:
                                try:
                                    score = int(num_match.group(1))
                                    if 0 <= score <= 100:
                                        match_scores.append(score)
                                except:
                                    pass
                            break
            except:
                continue

        if match_scores_found:
            findings["match_scores_found"] = True
            findings["match_scores"] = sorted(list(set(match_scores)))  # Unique scores
            print(f"   ✓ Match scores found: {findings['match_scores']}")
        else:
            print("   ⚠ Match scores not clearly visible")

        # Step 4: Test Filters
        print("\n4. Testing Filters...")

        # Location filter
        print("   Testing Location Filter...")
        location_selectors = [
            'input[placeholder*="location" i]',
            'input[placeholder*="city" i]',
            'select[aria-label*="location" i]',
            'button:has-text("location")',
        ]

        location_filter_found = False
        for selector in location_selectors:
            try:
                elem = page.locator(selector).first
                if await elem.is_visible(timeout=2000):
                    print(f"      ✓ Found location filter: {selector}")
                    location_filter_found = True
                    findings["filters_tested"]["location"] = "found"
                    break
            except:
                continue

        if not location_filter_found:
            print("      ⚠ Location filter not found")
            findings["filters_tested"]["location"] = "not_found"

        # Salary filter
        print("   Testing Salary Filter...")
        salary_selectors = [
            'input[placeholder*="salary" i]',
            'input[type="number"][placeholder*="min" i]',
            'input[type="number"][placeholder*="max" i]',
            'button:has-text("salary")',
        ]

        salary_filter_found = False
        for selector in salary_selectors:
            try:
                elem = page.locator(selector).first
                if await elem.is_visible(timeout=2000):
                    print(f"      ✓ Found salary filter: {selector}")
                    salary_filter_found = True
                    findings["filters_tested"]["salary"] = "found"
                    break
            except:
                continue

        if not salary_filter_found:
            print("      ⚠ Salary filter not found")
            findings["filters_tested"]["salary"] = "not_found"

        # Remote filter
        print("   Testing Remote Filter...")
        remote_selectors = [
            'input[type="checkbox"][aria-label*="remote" i]',
            'button:has-text("remote")',
            'label:has-text("remote")',
            '[data-testid*="remote"]',
        ]

        remote_filter_found = False
        for selector in remote_selectors:
            try:
                elem = page.locator(selector).first
                if await elem.is_visible(timeout=2000):
                    print(f"      ✓ Found remote filter: {selector}")
                    remote_filter_found = True
                    findings["filters_tested"]["remote"] = "found"
                    break
            except:
                continue

        if not remote_filter_found:
            print("      ⚠ Remote filter not found")
            findings["filters_tested"]["remote"] = "not_found"

        # Step 5: Test Sorting Options
        print("\n5. Testing Sorting Options...")
        sort_keywords = ["sort", "order", "match", "salary", "date", "recent"]

        sorting_found = False
        for keyword in sort_keywords:
            try:
                selectors = [
                    f'button:has-text("{keyword}")',
                    f'select:has-text("{keyword}")',
                    '[aria-label*="sort" i]',
                    '[data-testid*="sort"]',
                ]

                for selector in selectors:
                    try:
                        elem = page.locator(selector).first
                        if await elem.is_visible(timeout=1000):
                            text = await elem.text_content() or ""
                            if keyword.lower() in text.lower():
                                findings["sorting_tested"][keyword] = "found"
                                print(f"   ✓ Found sorting option: {keyword}")
                                sorting_found = True
                                break
                    except:
                        continue
                if sorting_found:
                    break
            except:
                continue

        if not sorting_found:
            print("   ⚠ No sorting options clearly visible")

        # Step 6: Click on a Job to See Details
        print("\n6. Testing Job Details...")

        if job_elements:
            try:
                first_job = job_elements[0]
                print("   Clicking on first job...")
                await first_job.click()
                await asyncio.sleep(3)

                # Check if details opened (modal, drawer, or new page)
                page_text_after = await page.inner_text("body")
                current_url_after = page.url

                if (
                    "detail" in page_text_after.lower()
                    or "description" in page_text_after.lower()
                    or current_url_after != current_url
                ):
                    findings["job_details_accessed"] = True
                    print("   ✓ Job details accessible")

                    await page.screenshot(path="/tmp/job_details.png", full_page=True)
                    findings["screenshots"].append("/tmp/job_details.png")
                    print("   ✓ Screenshot saved")
                else:
                    print("   ⚠ Job details may not have opened")
            except Exception as e:
                print(f"   ⚠ Error clicking job: {e}")
        else:
            print("   ⚠ No jobs available to click")

        # Step 7: Check Console Errors
        print("\n7. Checking Console Errors...")
        unique_errors = list(set(findings["console_errors"]))
        unique_warnings = list(set(findings["console_warnings"]))

        print(f"   Console Errors: {len(unique_errors)}")
        if unique_errors:
            for i, err in enumerate(unique_errors[:5], 1):
                print(f"      {i}. {err[:150]}")

        print(f"   Console Warnings: {len(unique_warnings)}")
        if unique_warnings:
            for i, warn in enumerate(unique_warnings[:3], 1):
                print(f"      {i}. {warn[:150]}")

        # Check API responses
        print(f"\n   API Responses: {len(findings['api_responses'])}")
        successful_jobs_calls = [
            r
            for r in findings["api_responses"]
            if "jobs" in r["url"] and r["status"] == 200
        ]
        print(f"   Successful jobs API calls: {len(successful_jobs_calls)}")
        for resp in successful_jobs_calls[:3]:
            print(f"      {resp['status']} {resp['url'][:100]}")

        # Final screenshot
        await page.screenshot(path="/tmp/jobs_page_final.png", full_page=True)
        findings["screenshots"].append("/tmp/jobs_page_final.png")
        print("\n   ✓ Final screenshot saved")

        # Step 8: Generate Report
        print("\n=== Test Summary ===")
        print(f"Jobs Page Loaded: {findings['jobs_page_loaded']}")
        print(f"Jobs Displayed: {findings['jobs_displayed']}")
        print(f"Job Count: {findings['job_count']}")
        print(f"Match Scores Found: {findings['match_scores_found']}")
        if findings["match_scores"]:
            print(f"Match Scores: {findings['match_scores']}")
        print(f"Filters Tested: {len(findings['filters_tested'])}")
        for filter_name, status in findings["filters_tested"].items():
            print(f"   - {filter_name}: {status}")
        print(f"Sorting Options: {len(findings['sorting_tested'])}")
        print(f"Job Details Accessed: {findings['job_details_accessed']}")
        print(f"Console Errors: {len(unique_errors)}")
        print(f"Console Warnings: {len(unique_warnings)}")
        print(f"Successful API Calls: {len(successful_jobs_calls)}")

        # Save detailed report
        findings["unique_errors"] = unique_errors
        findings["unique_warnings"] = unique_warnings
        findings["successful_api_calls"] = len(successful_jobs_calls)
        with open("/tmp/jobs_test_findings.json", "w") as f:
            json.dump(findings, f, indent=2)

        print("\n✓ Detailed findings saved to /tmp/jobs_test_findings.json")

        await asyncio.sleep(2)
        await browser.close()

        return findings


if __name__ == "__main__":
    asyncio.run(test_jobs_comprehensive())
