#!/usr/bin/env python3
"""
Comprehensive Render API Testing Suite
Tests all API endpoints on the production Render deployment
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Dict

import aiohttp


class RenderAPITester:
    def __init__(self):
        # Update this with your actual Render API URL
        self.api_base = (
            "https://jobhuntin-api.onrender.com"  # Typical Render URL pattern
        )
        self.session = None
        self.auth_token = None
        self.test_results = []

    async def setup(self):
        """Initialize HTTP session and setup"""
        self.session = aiohttp.ClientSession()
        print(f"🚀 Testing Render API at: {self.api_base}")

    async def cleanup(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()

    async def test_endpoint(
        self,
        method: str,
        path: str,
        data: Dict = None,
        headers: Dict = None,
        expected_status: int = 200,
    ) -> Dict:
        """Test a single API endpoint"""
        url = f"{self.api_base}{path}"
        start_time = datetime.now()

        try:
            async with self.session.request(
                method=method, url=url, json=data, headers=headers
            ) as response:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                # Try to get response text
                try:
                    response_text = await response.text()
                    response_data = json.loads(response_text) if response_text else {}
                except Exception:
                    response_data = {"raw_response": response_text[:500]}

                result = {
                    "endpoint": f"{method} {path}",
                    "status_code": response.status,
                    "expected_status": expected_status,
                    "duration_seconds": duration,
                    "success": response.status == expected_status,
                    "response": response_data,
                    "headers": dict(response.headers),
                    "timestamp": datetime.now().isoformat(),
                }

                self.test_results.append(result)
                return result

        except Exception as e:
            result = {
                "endpoint": f"{method} {path}",
                "status_code": 0,
                "expected_status": expected_status,
                "duration_seconds": (datetime.now() - start_time).total_seconds(),
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
            self.test_results.append(result)
            return result

    async def test_health_endpoints(self):
        """Test health and status endpoints"""
        print("\n🏥 Testing Health Endpoints...")

        tests = [
            ("GET", "/health", None, None, 200),
            ("GET", "/", None, None, 200),
            ("GET", "/docs", None, None, 200),
        ]

        for method, path, data, headers, expected in tests:
            result = await self.test_endpoint(method, path, data, headers, expected)
            status = "✅" if result["success"] else "❌"
            print(
                f"  {status} {result['endpoint']} - {result['status_code']} ({result['duration_seconds']:.2f}s)"
            )

    async def test_auth_endpoints(self):
        """Test authentication endpoints"""
        print("\n🔐 Testing Authentication Endpoints...")

        # Test magic link request
        result = await self.test_endpoint(
            "POST",
            "/auth/magic-link",
            {"email": "test@example.com"},
            expected_status=200,
        )
        status = "✅" if result["success"] else "❌"
        print(f"  {status} POST /auth/magic-link - {result['status_code']}")

        # Test user info (will likely fail without auth)
        result = await self.test_endpoint("GET", "/auth/me", expected_status=401)
        status = "✅" if result["success"] else "❌"
        print(f"  {status} GET /auth/me - {result['status_code']}")

    async def test_job_endpoints(self):
        """Test job-related endpoints"""
        print("\n💼 Testing Job Endpoints...")

        tests = [
            ("GET", "/jobs", None, None, 200),
            ("GET", "/jobs/search", None, None, 200),
            ("GET", "/jobs/featured", None, None, 200),
        ]

        for method, path, data, headers, expected in tests:
            result = await self.test_endpoint(method, path, data, headers, expected)
            status = "✅" if result["success"] else "❌"
            print(
                f"  {status} {result['endpoint']} - {result['status_code']} ({result['duration_seconds']:.2f}s)"
            )

    async def test_user_endpoints(self):
        """Test user profile endpoints"""
        print("\n👤 Testing User Endpoints...")

        # These will likely fail without authentication, which is expected
        tests = [
            ("GET", "/me/profile", None, None, 401),
            ("GET", "/me/applications", None, None, 401),
            ("GET", "/me/answer-memory", None, None, 401),
        ]

        for method, path, data, headers, expected in tests:
            result = await self.test_endpoint(method, path, data, headers, expected)
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {result['endpoint']} - {result['status_code']}")

    async def test_admin_endpoints(self):
        """Test admin endpoints"""
        print("\n⚙️ Testing Admin Endpoints...")

        tests = [
            ("GET", "/admin/stats", None, None, 401),  # Should require auth
            ("GET", "/admin/users", None, None, 401),  # Should require auth
        ]

        for method, path, data, headers, expected in tests:
            result = await self.test_endpoint(method, path, data, headers, expected)
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {result['endpoint']} - {result['status_code']}")

    async def test_ai_endpoints(self):
        """Test AI-powered endpoints"""
        print("\n🤖 Testing AI Endpoints...")

        # Test onboarding questions (may fail without auth)
        result = await self.test_endpoint(
            "POST",
            "/ai/onboarding/questions",
            {"profile": {"experience": "5 years", "role": "Software Engineer"}},
            expected_status=401,  # Expected to require auth
        )
        status = "✅" if result["success"] else "❌"
        print(f"  {status} POST /ai/onboarding/questions - {result['status_code']}")

    async def generate_report(self):
        """Generate comprehensive test report"""
        print("\n📊 Generating Test Report...")

        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - successful_tests

        avg_duration = (
            sum(r["duration_seconds"] for r in self.test_results) / total_tests
        )

        report = {
            "summary": {
                "total_tests": total_tests,
                "successful": successful_tests,
                "failed": failed_tests,
                "success_rate": f"{(successful_tests / total_tests * 100):.1f}%",
                "average_duration": f"{avg_duration:.2f}s",
                "api_base": self.api_base,
                "test_time": datetime.now().isoformat(),
            },
            "results": self.test_results,
        }

        # Save report to file
        with open("render_api_test_report.json", "w") as f:
            json.dump(report, f, indent=2)

        print("\n📋 Test Summary:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Successful: {successful_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {(successful_tests / total_tests * 100):.1f}%")
        print(f"   Avg Duration: {avg_duration:.2f}s")
        print("   Report saved to: render_api_test_report.json")

        return report

    async def run_all_tests(self):
        """Run comprehensive API test suite"""
        print("🧪 Starting Render API Test Suite...")

        await self.setup()

        try:
            await self.test_health_endpoints()
            await self.test_auth_endpoints()
            await self.test_job_endpoints()
            await self.test_user_endpoints()
            await self.test_admin_endpoints()
            await self.test_ai_endpoints()

            report = await self.generate_report()
            return report

        finally:
            await self.cleanup()


async def main():
    """Main test runner"""
    tester = RenderAPITester()

    try:
        await tester.run_all_tests()

        # Exit with error code if any tests failed
        failed_tests = sum(1 for r in tester.test_results if not r["success"])
        if failed_tests > 0:
            print(
                f"\n❌ {failed_tests} tests failed. Check render_api_test_report.json for details."
            )
            sys.exit(1)
        else:
            print("\n✅ All tests passed! Render API is working correctly.")

    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
