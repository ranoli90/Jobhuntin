#!/usr/bin/env python3
"""
Deployment verification script for auto-apply worker service.
Validates that all components are properly configured and functional.
"""

import asyncio
import sys
import time
from typing import Any, Dict

# Add the project root to Python path
sys.path.insert(0, '.')

from shared.config import get_settings
from shared.logging_config import get_logger

logger = get_logger("sorce.deployment.verify")


class DeploymentVerifier:
    """Verifies deployment configuration and functionality."""
    
    def __init__(self):
        self.settings = get_settings()
        self.verification_results = {}
        
    async def verify_all(self) -> bool:
        """Run all verification checks."""
        logger.info("Starting deployment verification...")
        
        checks = [
            ("environment", self._verify_environment),
            ("dependencies", self._verify_dependencies),
            ("database", self._verify_database),
            ("browser", self._verify_browser),
            ("configuration", self._verify_configuration),
            ("permissions", self._verify_permissions),
        ]
        
        all_passed = True
        for check_name, check_func in checks:
            try:
                logger.info("Running %s verification...", check_name)
                result = await check_func()
                self.verification_results[check_name] = result
                if not result.get("passed", False):
                    all_passed = False
                    logger.error("❌ %s verification failed: %s", check_name, result.get("error", "Unknown error"))
                else:
                    logger.info("✅ %s verification passed", check_name)
            except Exception as e:
                all_passed = False
                logger.error("❌ %s verification error: %s", check_name, e)
                self.verification_results[check_name] = {"passed": False, "error": str(e)}
        
        # Print summary
        self._print_summary()
        return all_passed
    
    async def _verify_environment(self) -> Dict[str, Any]:
        """Verify environment variables."""
        required_vars = {
            "DATABASE_URL": self.settings.database_url,
            "LLM_API_KEY": self.settings.llm_api_key,
            "LLM_API_BASE": self.settings.llm_api_base,
        }
        
        missing_vars = [name for name, value in required_vars.items() if not value]
        
        if missing_vars:
            return {
                "passed": False,
                "error": f"Missing environment variables: {missing_vars}",
                "missing_vars": missing_vars,
            }
        
        return {"passed": True, "message": "All required environment variables set"}
    
    async def _verify_dependencies(self) -> Dict[str, Any]:
        """Verify required dependencies are available."""
        try:
            import playwright
            import asyncpg
            import fastapi
            import pydantic
            
            versions = {
                "playwright": playwright.__version__,
                "asyncpg": asyncpg.__version__,
                "fastapi": fastapi.__version__,
                "pydantic": pydantic.__version__,
            }
            
            return {
                "passed": True,
                "message": "All dependencies available",
                "versions": versions,
            }
        except ImportError as e:
            return {"passed": False, "error": f"Missing dependency: {e}"}
    
    async def _verify_database(self) -> Dict[str, Any]:
        """Verify database connectivity."""
        try:
            from shared.db import get_db_pool
            
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                # Test basic connectivity
                await conn.fetchval("SELECT 1")
                
                # Test table existence
                tables = await conn.fetch("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                """)
                
                table_names = [row["table_name"] for row in tables]
                required_tables = ["users", "jobs", "applications", "background_jobs"]
                
                missing_tables = [t for t in required_tables if t not in table_names]
                
                if missing_tables:
                    return {
                        "passed": False,
                        "error": f"Missing database tables: {missing_tables}",
                        "existing_tables": table_names,
                    }
            
            return {
                "passed": True,
                "message": "Database connectivity verified",
                "table_count": len(table_names),
            }
            
        except Exception as e:
            return {"passed": False, "error": f"Database verification failed: {e}"}
    
    async def _verify_browser(self) -> Dict[str, Any]:
        """Verify browser functionality."""
        try:
            from apps.worker.scaling import BrowserPoolManager
            
            browser_pool = BrowserPoolManager()
            await browser_pool.start()
            
            health_status = await browser_pool.health_check()
            await browser_pool.shutdown()
            
            if not health_status["healthy"]:
                return {
                    "passed": False,
                    "error": f"Browser health check failed: {health_status['browser_status']}",
                    "health_status": health_status,
                }
            
            return {
                "passed": True,
                "message": "Browser functionality verified",
                "browser_info": {
                    "connected": health_status["browser_connected"],
                    "remote": health_status["is_remote"],
                    "headless": health_status["is_headless"],
                },
            }
            
        except Exception as e:
            return {"passed": False, "error": f"Browser verification failed: {e}"}
    
    async def _verify_configuration(self) -> Dict[str, Any]:
        """Verify configuration settings."""
        config_checks = {
            "agent_enabled": self.settings.agent_enabled,
            "worker_concurrency": getattr(self.settings, 'worker_concurrency', 50),
            "browser_context_max_uses": getattr(self.settings, 'browser_context_max_uses', 10),
            "poll_interval": getattr(self.settings, 'poll_interval_seconds', 2),
        }
        
        # Validate reasonable values
        if config_checks["worker_concurrency"] < 1 or config_checks["worker_concurrency"] > 100:
            return {
                "passed": False,
                "error": f"Invalid worker_concurrency: {config_checks['worker_concurrency']}",
            }
        
        if config_checks["browser_context_max_uses"] < 1 or config_checks["browser_context_max_uses"] > 50:
            return {
                "passed": False,
                "error": f"Invalid browser_context_max_uses: {config_checks['browser_context_max_uses']}",
            }
        
        return {
            "passed": True,
            "message": "Configuration verified",
            "config": config_checks,
        }
    
    async def _verify_permissions(self) -> Dict[str, Any]:
        """Verify file system permissions."""
        import os
        
        # Check write permissions in key directories
        directories_to_check = [
            ".",
            "logs",
            "temp",
            "/tmp",
        ]
        
        permissions_ok = True
        permission_results = {}
        
        for directory in directories_to_check:
            try:
                if os.path.exists(directory):
                    test_file = os.path.join(directory, ".deployment_test")
                    with open(test_file, 'w') as f:
                        f.write("test")
                    os.remove(test_file)
                    permission_results[directory] = "writable"
                else:
                    permission_results[directory] = "not_found"
            except Exception as e:
                permission_results[directory] = f"error: {e}"
                permissions_ok = False
        
        return {
            "passed": permissions_ok,
            "message": "File permissions verified" if permissions_ok else "File permission issues detected",
            "permissions": permission_results,
        }
    
    def _print_summary(self) -> None:
        """Print verification summary."""
        print("\n" + "="*60)
        print("DEPLOYMENT VERIFICATION SUMMARY")
        print("="*60)
        
        total_checks = len(self.verification_results)
        passed_checks = sum(1 for result in self.verification_results.values() if result.get("passed", False))
        
        for check_name, result in self.verification_results.items():
            status = "✅ PASS" if result.get("passed", False) else "❌ FAIL"
            print(f"{status:<10} {check_name.title():<15} {result.get('message', result.get('error', ''))}")
        
        print("-" * 60)
        print(f"Overall: {passed_checks}/{total_checks} checks passed")
        
        if passed_checks == total_checks:
            print("🎉 DEPLOYMENT VERIFICATION SUCCESSFUL!")
            print("The auto-apply worker is ready for production use.")
        else:
            print("⚠️  DEPLOYMENT VERIFICATION FAILED!")
            print("Please address the failing checks before deploying to production.")
        
        print("="*60)


async def main():
    """Main verification function."""
    verifier = DeploymentVerifier()
    success = await verifier.verify_all()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
