#!/usr/bin/env python
"""
Load testing script for API endpoints using locust.

Usage:
    pip install locust
    locust -f scripts/load_test.py --host https://sorce-api.onrender.com

Then open http://localhost:8089 to run tests.
"""

import random
from locust import HttpUser, task, between


class APIUser(HttpUser):
    """Simulated API user for load testing."""
    
    wait_time = between(1, 3)
    
    def on_start(self):
        """Called when a user starts."""
        self.test_token = "test-jwt-token-placeholder"
    
    @task(10)
    def health_check(self):
        """Test health endpoint - most frequent."""
        self.client.get("/health", name="/health")
    
    @task(5)
    def deep_health_check(self):
        """Test deep healthz endpoint."""
        self.client.get("/healthz", name="/healthz")
    
    @task(3)
    def get_api_docs(self):
        """Test API docs endpoint."""
        self.client.get("/docs", name="/docs")
    
    @task(2)
    def get_openapi(self):
        """Test OpenAPI spec."""
        self.client.get("/openapi.json", name="/openapi.json")
    
    @task(1)
    def match_job(self):
        """Test job matching endpoint (requires auth)."""
        headers = {"Authorization": f"Bearer {self.test_token}"}
        self.client.post(
            "/ai/match-job",
            json={
                "job_id": str(random.uuid4()),
                "profile": {
                    "skills": ["Python", "FastAPI", "PostgreSQL"],
                    "experience_years": 5,
                    "location": "Remote"
                }
            },
            headers=headers,
            name="/ai/match-job"
        )


class JobSearchUser(HttpUser):
    """Simulated job search user."""
    
    wait_time = between(2, 5)
    
    @task(5)
    def search_jobs(self):
        """Test job search."""
        self.client.get(
            "/jobs",
            params={
                "q": random.choice(["python", "react", "golang", "rust"]),
                "location": random.choice(["Remote", "New York", "San Francisco"]),
                "page": 1
            },
            name="/jobs"
        )
    
    @task(2)
    def get_job_details(self):
        """Test job details."""
        job_id = str(random.uuid4())
        self.client.get(f"/jobs/{job_id}", name="/jobs/[id]")


class AuthenticatedUser(HttpUser):
    """Simulated authenticated user with profile operations."""
    
    wait_time = between(3, 8)
    
    def on_start(self):
        self.test_token = "test-jwt-token-placeholder"
    
    @task(3)
    def get_profile(self):
        """Get user profile."""
        headers = {"Authorization": f"Bearer {self.test_token}"}
        self.client.get("/me/profile", headers=headers, name="/me/profile")
    
    @task(2)
    def get_dashboard(self):
        """Get user dashboard."""
        headers = {"Authorization": f"Bearer {self.test_token}"}
        self.client.get("/me/dashboard", headers=headers, name="/me/dashboard")
    
    @task(1)
    def get_answer_memory(self):
        """Get answer memory."""
        headers = {"Authorization": f"Bearer {self.test_token}"}
        self.client.get("/me/answer-memory", headers=headers, name="/me/answer-memory")


# For running without Locust UI
if __name__ == "__main__":
    import argparse
    import requests
    import time
    import concurrent.futures
    
    parser = argparse.ArgumentParser(description="Simple load test")
    parser.add_argument("--host", default="https://sorce-api.onrender.com")
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--concurrency", type=int, default=10)
    args = parser.parse_args()
    
    def make_request(_):
        try:
            start = time.time()
            resp = requests.get(f"{args.host}/healthz", timeout=10)
            duration = time.time() - start
            return {"status": resp.status_code, "duration": duration}
        except Exception as e:
            return {"error": str(e)}
    
    print(f"Running {args.requests} requests with {args.concurrency} concurrent users...")
    
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        results = list(executor.map(make_request, range(args.requests)))
    
    total_time = time.time() - start_time
    
    successes = [r for r in results if "status" in r and r["status"] == 200]
    failures = [r for r in results if "error" in r or r.get("status") != 200]
    durations = [r["duration"] for r in successes if "duration" in r]
    
    print(f"\nResults:")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Requests: {args.requests}")
    print(f"  Success: {len(successes)} ({len(successes)/args.requests*100:.1f}%)")
    print(f"  Failures: {len(failures)} ({len(failures)/args.requests*100:.1f}%)")
    if durations:
        print(f"  Avg latency: {sum(durations)/len(durations)*1000:.1f}ms")
        print(f"  P99 latency: {sorted(durations)[int(len(durations)*0.99)]*1000:.1f}ms")
