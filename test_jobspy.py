"""Test JobSpy integration."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "packages"))

async def test_jobspy():
    from backend.domain.jobspy_client import JobSpyClient

    client = JobSpyClient()
    print(f"Sources configured: {client.sources}")

    print("Testing JobSpy fetch (Indeed only, 5 results)...")
    jobs = await client.fetch_jobs(
        search_term="software engineer",
        location="Remote",
        results_wanted=5,
        hours_old=168,
        sources=["indeed"]
    )

    print(f"Fetched {len(jobs)} jobs")
    if jobs:
        print(f"Sample: {jobs[0]['title']} at {jobs[0]['company']}")
        print(f"Source: {jobs[0]['source']}")
        print(f"URL: {jobs[0]['application_url'][:60]}...")

    return jobs

if __name__ == "__main__":
    asyncio.run(test_jobspy())
