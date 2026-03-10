#!/usr/bin/env python3
"""
Test job search functionality after backend fixes.
Tests: job loading, match scores, filters, sorting, console errors.
"""

import asyncio
from playwright.async_api import async_playwright
import json
import time

SESSION_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxZGRmOTc3YS1hNmM2LTRkMzAtODc4Mi1lYjgwNmJhZDYwNTAiLCJlbWFpbCI6InRlc3R1c2VyXzIyNTJkNTE0QHRlc3QuY29tIiwiYXVkIjoiYXV0aGVudGljYXRlZCIsImp0aSI6IjRlOTZkN2MzLTkyYWUtNGMwOC05NDUwLWRhYjYwY2NkNjdkZSIsInNlc3Npb25faWQiOiJmYzJjZmUwZS04ZDc3LTRmNzMtYmRkZS0yNjkwYWE2NDA1Y2IiLCJpYXQiOjE3NzMxMTQ3NTIsIm5iZiI6MTc3MzExNDc1MiwiZXhwIjoxNzczNzE5NTUyfQ.17bFNT76vtC2ri3TQnS2P-H4P2QOmROOgxjrcDkz-lE"


async def test_jobs_after_fix():
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
            "jobs_page_loaded": False,
            "jobs_displayed": False,
            "job_count": 0,
            "match_scores_found": False,
            "match_scores": [],
            "filters_available": [],
            "filters_tested": [],
            "sorting_options": [],
            "sorting_tested": [],
            "console_errors": [],
            "console_warnings": [],
            "api_calls": [],
            "screenshots": [],
        }

        def track_console(msg):
            if msg.type == "error":
                findings["console_errors"].append(msg.text)
            elif msg.type == "warning":
                findings["console_warnings"].append(msg.text)

        page.on("console", track_console)

        # Track API calls
        def track_request(req):
            if "localhost:8000" in req.url and (
                "jobs" in req.url or "profile" in req.url
            ):
                findings["api_calls"].append(
                    {"url": req.url, "method": req.method, "timestamp": time.time()}
                )

        page.on("request", track_request)

        print("=== Job Search Test After Fixes ===\n")

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
            print("   ⚠ Redirected to login (token may have expired)")
            await page.screenshot(
                path="/tmp/jobs_redirected_to_login.png", full_page=True
            )
            findings["screenshots"].append("/tmp/jobs_redirected_to_login.png")
            print("   ✓ Screenshot saved")

            # Still check for any errors on login page
            page_text = await page.inner_text("body")
            print(f"   Login page content: {page_text[:200]}...")

            with open("/tmp/jobs_test_findings.json", "w") as f:
                json.dump(findings, f, indent=2)

            print("\n=== Test Summary ===")
            print(f"Redirected to Login: {findings['redirected_to_login']}")
            print(f"Console Errors: {len(findings['console_errors'])}")
            print(f"Console Warnings: {len(findings['console_warnings'])}")
            print("\n⚠ Token expired - cannot test job search features")
            print("✓ Findings saved to /tmp/jobs_test_findings.json")

            await browser.close()
            return findings

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
        await asyncio.sleep(3)  # Wait for jobs to load

        page_text = await page.inner_text("body")

        # Look for job cards/listings
        job_selectors = [
            '[data-testid*="job"]',
            '[class*="job"]',
            '[class*="Job"]',
            'article[role="article"]',
            'div[class*="card"]',
            '[role="article"]',
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
                            ]
                        ):
                            job_elements.append(elem)
                            jobs_found = True
                    if jobs_found:
                        break
            except:
                continue

        if jobs_found:
            findings["jobs_displayed"] = True
            findings["job_count"] = len(job_elements)
            print(f"   ✓ Jobs displayed (found {len(job_elements)} job-like elements)")

            # Try to count more accurately by looking for job titles
            job_titles = await page.locator(
                'h2, h3, [class*="title"], [class*="Title"]'
            ).all()
            print(f"   Found {len(job_titles)} potential job title elements")
        else:
            print("   ⚠ No jobs clearly visible")
            # Check if still loading
            if "loading" in page_text.lower() or "load" in page_text.lower():
                print("   ⚠ Page still showing loading state")
            findings["issues"] = findings.get("issues", []) + [
                "Jobs not clearly visible"
            ]

        # Step 3: Check for Match Scores
        print("\n3. Checking for Match Scores...")
        match_score_patterns = [
            r"(\d+)%",  # Percentage match
            r"match.*?(\d+)",
            r"(\d+).*?match",
            r"score.*?(\d+)",
            r"(\d+).*?score",
        ]

        import re

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
                elem = page.locator(f"text=/{indicator}/i").first
                if await elem.is_visible(timeout=2000):
                    text = await elem.text_content() or ""
                    if any(char.isdigit() for char in text):
                        print(f"   ✓ Found match score indicator: '{indicator}'")
                        print(f"      Text: {text[:100]}")
                        match_scores_found = True
                        break
            except:
                continue

        if match_scores_found:
            findings["match_scores_found"] = True
            findings["match_scores"] = list(set(match_scores))  # Unique scores
            print(f"   ✓ Match scores found: {findings['match_scores']}")
        else:
            print("   ⚠ Match scores not clearly visible")

        # Step 4: Test Filters
        print("\n4. Testing Filters...")
        filter_keywords = [
            "filter",
            "location",
            "salary",
            "remote",
            "keyword",
            "search",
        ]

        filters_found = []
        for keyword in filter_keywords:
            try:
                selectors = [
                    f'input[placeholder*="{keyword}" i]',
                    f'button:has-text("{keyword}")',
                    f'select[aria-label*="{keyword}" i]',
                    f'[data-testid*="{keyword}"]',
                    f'label:has-text("{keyword}")',
                ]

                for selector in selectors:
                    try:
                        elem = page.locator(selector).first
                        if await elem.is_visible(timeout=1000):
                            text = await elem.text_content() or ""
                            if keyword.lower() in text.lower():
                                filters_found.append(keyword)
                                findings["filters_available"].append(keyword)
                                print(f"   ✓ Found filter: {keyword}")
                                break
                    except:
                        continue
            except:
                continue

        if not filters_found:
            print("   ⚠ No filters clearly visible")

        # Step 5: Test Sorting Options
        print("\n5. Testing Sorting Options...")
        sort_keywords = ["sort", "order", "by", "match", "salary", "date", "recent"]

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

        # Step 6: Check Console Errors
        print("\n6. Checking Console Errors...")
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

        # Step 7: Check API Calls
        print("\n7. Checking API Calls...")
        jobs_api_calls = [
            call for call in findings["api_calls"] if "jobs" in call["url"]
        ]
        print(f"   Jobs API calls: {len(jobs_api_calls)}")
        for call in jobs_api_calls[:3]:
            print(f"      {call['method']} {call['url'][:100]}")

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
        print(f"Filters Available: {len(findings['filters_available'])}")
        print(f"Sorting Options: {len(findings['sorting_options'])}")
        print(f"Console Errors: {len(unique_errors)}")
        print(f"Console Warnings: {len(unique_warnings)}")
        print(f"API Calls: {len(jobs_api_calls)}")

        # Save detailed report
        findings["unique_errors"] = unique_errors
        findings["unique_warnings"] = unique_warnings
        with open("/tmp/jobs_test_findings.json", "w") as f:
            json.dump(findings, f, indent=2)

        print("\n✓ Detailed findings saved to /tmp/jobs_test_findings.json")

        await asyncio.sleep(2)
        await browser.close()

        return findings


if __name__ == "__main__":
    asyncio.run(test_jobs_after_fix())
