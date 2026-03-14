#!/usr/bin/env python3
"""
Comprehensive job search and application flow testing.
Tests: job listing, match scores, filters, job details, application process, AI matching.
"""

import asyncio
import json
import time

from playwright.async_api import async_playwright

SESSION_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxZGRmOTc3YS1hNmM2LTRkMzAtODc4Mi1lYjgwNmJhZDYwNTAiLCJlbWFpbCI6InRlc3R1c2VyXzIyNTJkNTE0QHRlc3QuY29tIiwiYXVkIjoiYXV0aGVudGljYXRlZCIsImp0aSI6IjRlOTZkN2MzLTkyYWUtNGMwOC05NDUwLWRhYjYwY2NkNjdkZSIsInNlc3Npb25faWQiOiJmYzJjZmUwZS04ZDc3LTRmNzMtYmRkZS0yNjkwYWE2NDA1Y2IiLCJpYXQiOjE3NzMxMTQ3NTIsIm5iZiI6MTc3MzExNDc1MiwiZXhwIjoxNzczNzE5NTUyfQ.17bFNT76vtC2ri3TQnS2P-H4P2QOmROOgxjrcDkz-lE"


async def test_job_search_flow():
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
            "jobs_page_loaded": False,
            "jobs_displayed": False,
            "match_scores_found": False,
            "filters_available": [],
            "sorting_options": [],
            "job_details_accessible": False,
            "match_explanation_found": False,
            "application_flow_works": False,
            "ai_matching_working": False,
            "performance_metrics": {},
            "console_errors": [],
            "console_warnings": [],
            "issues": [],
            "screenshots": [],
        }

        def track_console(msg):
            if msg.type == "error":
                findings["console_errors"].append(msg.text)
            elif msg.type == "warning":
                findings["console_warnings"].append(msg.text)

        page.on("console", track_console)

        print("=== Job Search and Application Flow Test ===\n")

        # Step 1: Navigate to Jobs Page
        print("1. Navigating to Jobs Page...")
        start_time = time.time()
        await page.goto(
            "http://localhost:5173/app/jobs", wait_until="networkidle", timeout=60000
        )
        load_time = time.time() - start_time
        findings["performance_metrics"]["jobs_page_load"] = load_time
        print(f"   Load time: {load_time:.2f}s")

        await asyncio.sleep(5)  # Wait for content to render

        current_url = page.url
        print(f"   URL: {current_url}")

        if "/jobs" in current_url or "/app/jobs" in current_url:
            findings["jobs_page_loaded"] = True
            print("   ✓ Jobs page loaded")
        else:
            print(f"   ❌ Unexpected URL: {current_url}")
            return findings

        # Take screenshot
        await page.screenshot(path="/tmp/jobs_page_initial.png", full_page=True)
        findings["screenshots"].append("/tmp/jobs_page_initial.png")
        print("   ✓ Screenshot saved")

        # Step 2: Check for Jobs Displayed
        print("\n2. Checking for Jobs Displayed...")
        page_text = await page.inner_text("body")

        # Look for job-related keywords
        job_indicators = [
            "job",
            "position",
            "role",
            "company",
            "salary",
            "location",
            "match",
            "score",
            "apply",
            "remote",
            "full-time",
        ]

        found_indicators = [
            ind for ind in job_indicators if ind.lower() in page_text.lower()
        ]
        print(f"   Found indicators: {', '.join(found_indicators[:5])}")

        # Look for job cards/listings
        job_selectors = [
            '[data-testid*="job"]',
            '[class*="job"]',
            '[class*="Job"]',
            "article",
            '[role="article"]',
            'div[class*="card"]',
        ]

        jobs_found = False
        job_count = 0

        for selector in job_selectors:
            try:
                elements = await page.locator(selector).all()
                if len(elements) > 0:
                    print(
                        f"   Found {len(elements)} elements with selector: {selector}"
                    )
                    # Check if any contain job-like content
                    for i, elem in enumerate(elements[:5]):
                        text = await elem.text_content() or ""
                        if any(
                            keyword in text.lower()
                            for keyword in [
                                "engineer",
                                "developer",
                                "software",
                                "job",
                                "company",
                            ]
                        ):
                            jobs_found = True
                            job_count += 1
                    if jobs_found:
                        break
            except:
                continue

        if jobs_found:
            findings["jobs_displayed"] = True
            print(f"   ✓ Jobs displayed (found {job_count} job-like elements)")
        else:
            print("   ⚠ No jobs clearly visible - checking page structure...")
            # Try to find any list or grid of items
            lists = await page.locator('ul, ol, [role="list"]').all()
            print(f"   Found {len(lists)} list elements")
            findings["issues"].append("Jobs not clearly visible in expected format")

        # Step 3: Check for Match Scores
        print("\n3. Checking for Match Scores...")
        match_score_indicators = [
            "match",
            "score",
            "%",
            "match score",
            "compatibility",
            "fit",
            "rating",
            "match%",
        ]

        match_scores_found = False
        for indicator in match_score_indicators:
            try:
                # Look for text containing match score
                match_elem = page.locator(f"text=/{indicator}/i").first
                if await match_elem.is_visible(timeout=2000):
                    text = await match_elem.text_content() or ""
                    if any(char.isdigit() for char in text):  # Contains numbers
                        print(f"   ✓ Found match score indicator: '{indicator}'")
                        print(f"      Text: {text[:100]}")
                        match_scores_found = True
                        findings["match_scores_found"] = True
                        break
            except:
                continue

        if not match_scores_found:
            print("   ⚠ Match scores not clearly visible")
            findings["issues"].append("Match scores not found")

        # Step 4: Test Filters
        print("\n4. Testing Filters...")
        filter_keywords = [
            "filter",
            "location",
            "salary",
            "remote",
            "keyword",
            "search",
            "type",
            "company",
            "sort",
        ]

        filters_found = []
        for keyword in filter_keywords:
            try:
                # Look for input fields, buttons, or selects
                selectors = [
                    f'input[placeholder*="{keyword}" i]',
                    f'button:has-text("{keyword}")',
                    f'select[aria-label*="{keyword}" i]',
                    f'[data-testid*="{keyword}"]',
                ]

                for selector in selectors:
                    try:
                        elem = page.locator(selector).first
                        if await elem.is_visible(timeout=1000):
                            filters_found.append(keyword)
                            print(f"   ✓ Found filter: {keyword}")
                            findings["filters_available"].append(keyword)
                            break
                    except:
                        continue
            except:
                continue

        if not filters_found:
            print("   ⚠ No filters clearly visible")
            findings["issues"].append("Filters not found")

        # Step 5: Test Sorting Options
        print("\n5. Testing Sorting Options...")
        sort_keywords = ["sort", "order", "by", "match", "salary", "date", "relevance"]

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
                                findings["sorting_options"].append(keyword)
                                print(f"   ✓ Found sorting option: {keyword}")
                                break
                    except:
                        continue
            except:
                continue

        if not findings["sorting_options"]:
            print("   ⚠ No sorting options clearly visible")

        # Step 6: Test Job Details
        print("\n6. Testing Job Details...")

        # Try to click on first job-like element
        job_clicked = False
        for selector in job_selectors:
            try:
                elements = await page.locator(selector).all()
                for elem in elements[:3]:  # Try first 3
                    try:
                        text = await elem.text_content() or ""
                        if any(
                            keyword in text.lower()
                            for keyword in ["engineer", "developer", "software", "job"]
                        ):
                            # Check if it's clickable
                            if await elem.is_visible(timeout=2000):
                                print("   Attempting to click job element...")
                                await elem.click()
                                await asyncio.sleep(3)

                                # Check if we navigated or modal opened
                                new_url = page.url
                                page_text_after = await page.inner_text("body")

                                if (
                                    new_url != current_url
                                    or "detail" in page_text_after.lower()
                                    or "description" in page_text_after.lower()
                                ):
                                    findings["job_details_accessible"] = True
                                    job_clicked = True
                                    print("   ✓ Job details accessible")

                                    # Take screenshot
                                    await page.screenshot(
                                        path="/tmp/job_details.png", full_page=True
                                    )
                                    findings["screenshots"].append(
                                        "/tmp/job_details.png"
                                    )

                                    # Check for match explanation
                                    match_explanation_keywords = [
                                        "match",
                                        "why",
                                        "explanation",
                                        "fit",
                                        "reason",
                                        "compatibility",
                                    ]
                                    for keyword in match_explanation_keywords:
                                        try:
                                            exp_elem = page.locator(
                                                f"text=/{keyword}/i"
                                            ).first
                                            if await exp_elem.is_visible(timeout=2000):
                                                findings["match_explanation_found"] = (
                                                    True
                                                )
                                                print(
                                                    f"   ✓ Found match explanation indicator: {keyword}"
                                                )
                                                break
                                        except:
                                            continue

                                    break
                    except Exception:
                        continue
                if job_clicked:
                    break
            except:
                continue

        if not job_clicked:
            print("   ⚠ Could not access job details")
            findings["issues"].append("Job details not accessible")
            # Navigate back to jobs list
            await page.goto("http://localhost:5173/app/jobs", wait_until="networkidle")
            await asyncio.sleep(3)

        # Step 7: Test Application Process
        print("\n7. Testing Application Process...")

        # Look for apply button
        apply_selectors = [
            'button:has-text("Apply")',
            'button:has-text("Apply Now")',
            'a:has-text("Apply")',
            '[data-testid*="apply"]',
            'button[aria-label*="apply" i]',
        ]

        apply_button_found = False
        for selector in apply_selectors:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=3000):
                    print(f"   ✓ Found apply button: {selector}")
                    apply_button_found = True

                    # Check if button is enabled
                    is_disabled = await btn.get_attribute("disabled")
                    if is_disabled:
                        print("   ⚠ Apply button is disabled")
                    else:
                        print("   ✓ Apply button is enabled")
                        # Don't actually click to avoid creating test applications
                        # findings['application_flow_works'] = True

                    break
            except:
                continue

        if not apply_button_found:
            print("   ⚠ Apply button not found")
            findings["issues"].append("Apply button not found")

        # Step 8: Verify AI Matching Intelligence
        print("\n8. Verifying AI Matching Intelligence...")

        # Check console for matching-related logs
        matching_logs = [
            log
            for log in findings["console_errors"] + findings["console_warnings"]
            if any(
                keyword in log.lower()
                for keyword in ["match", "score", "ai", "matching", "compute"]
            )
        ]

        if matching_logs:
            print(f"   Found {len(matching_logs)} matching-related logs")
            for log in matching_logs[:3]:
                print(f"      - {log[:100]}")

        # Check if jobs match user profile
        # User profile: Python, JavaScript, React, TypeScript, FastAPI, PostgreSQL, Docker, AWS
        # Location: San Francisco, CA
        # Salary: 100k-150k
        # Remote: Yes

        user_skills = [
            "python",
            "javascript",
            "react",
            "typescript",
            "fastapi",
            "postgresql",
            "docker",
            "aws",
        ]
        page_text_lower = page_text.lower()

        skills_found_in_jobs = [
            skill for skill in user_skills if skill in page_text_lower
        ]
        if skills_found_in_jobs:
            print(
                f"   ✓ Found user skills in job listings: {', '.join(skills_found_in_jobs[:5])}"
            )
            findings["ai_matching_working"] = True
        else:
            print("   ⚠ User skills not clearly visible in job listings")

        # Check for location
        if "san francisco" in page_text_lower or "sf" in page_text_lower:
            print("   ✓ San Francisco location found in listings")
        else:
            print("   ⚠ San Francisco location not clearly visible")

        # Check for salary range
        if "100" in page_text or "150" in page_text or "$" in page_text:
            print("   ✓ Salary information present")
        else:
            print("   ⚠ Salary information not clearly visible")

        # Check for remote
        if "remote" in page_text_lower:
            print("   ✓ Remote jobs found")
        else:
            print("   ⚠ Remote jobs not clearly visible")

        # Step 9: Check Efficiency
        print("\n9. Checking Efficiency...")

        # Check for pre-computed indicators
        network_requests = []
        page.on(
            "request",
            lambda req: network_requests.append(
                {
                    "url": req.url,
                    "method": req.method,
                    "resource_type": req.resource_type,
                }
            ),
        )

        # Reload to capture network activity
        await page.reload(wait_until="networkidle")
        await asyncio.sleep(3)

        # Check for match score API calls
        match_api_calls = [
            req
            for req in network_requests
            if "match" in req["url"].lower() or "score" in req["url"].lower()
        ]
        if match_api_calls:
            print(f"   Found {len(match_api_calls)} match/score API calls")
            for call in match_api_calls[:3]:
                print(f"      - {call['method']} {call['url'][:80]}")
        else:
            print("   ⚠ No match/score API calls detected (may be pre-computed)")

        findings["performance_metrics"]["network_requests"] = len(network_requests)
        findings["performance_metrics"]["match_api_calls"] = len(match_api_calls)

        # Final screenshot
        await page.screenshot(path="/tmp/jobs_page_final.png", full_page=True)
        findings["screenshots"].append("/tmp/jobs_page_final.png")

        # Step 10: Generate Report
        print("\n=== Test Summary ===")
        print(f"Jobs Page Loaded: {findings['jobs_page_loaded']}")
        print(f"Jobs Displayed: {findings['jobs_displayed']}")
        print(f"Match Scores Found: {findings['match_scores_found']}")
        print(f"Filters Available: {len(findings['filters_available'])}")
        print(f"Sorting Options: {len(findings['sorting_options'])}")
        print(f"Job Details Accessible: {findings['job_details_accessible']}")
        print(f"Match Explanation Found: {findings['match_explanation_found']}")
        print(f"AI Matching Working: {findings['ai_matching_working']}")
        print(f"Console Errors: {len(findings['console_errors'])}")
        print(f"Console Warnings: {len(findings['console_warnings'])}")
        print(f"Issues Found: {len(findings['issues'])}")

        # Save detailed report
        with open("/tmp/job_search_test_report.json", "w") as f:
            json.dump(findings, f, indent=2)

        print("\n✓ Detailed report saved to /tmp/job_search_test_report.json")

        await asyncio.sleep(2)
        await browser.close()

        return findings


if __name__ == "__main__":
    asyncio.run(test_job_search_flow())
