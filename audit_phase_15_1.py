"""
Phase 15.1 Database & Performance Audit Script
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import database connection
try:
    import asyncpg

    from shared.logging_config import get_logger

    logger = get_logger("phase15_audit")
except ImportError as e:
    print(f"Import error: {e}")
    logger = None


class Phase15Auditor:
    """Auditor for Phase 15.1 Database & Performance requirements."""

    def __init__(self):
        self.results = {
            "domain_managers": {"missing": [], "existing": []},
            "api_endpoints": {"missing": [], "existing": []},
            "database_migrations": {"missing": [], "existing": []},
            "performance_optimizations": {"missing": [], "existing": []},
            "monitoring_systems": {"missing": [], "existing": []},
            "caching_systems": {"missing": [], "existing": []},
            "database_optimizations": {"missing": [], "existing": []},
            "api_optimizations": {"missing": [], "existing": []},
        }

        # Database URL from memory
        self.db_url = "postgresql://jobhuntin_user:60BpsY53MYOO4fGFlvZKwDpiXB9Up9lL@dpg-d66ck524d50c73bas62g-a:5432/jobhuntin"

    async def run_audit(self) -> Dict[str, Any]:
        """Run comprehensive Phase 15.1 audit."""
        print("Starting Phase 15.1 Database & Performance Audit...")

        # Check domain managers
        await self._check_domain_managers()

        # Check API endpoints
        await self._check_api_endpoints()

        # Check database migrations
        await self._check_database_migrations()

        # Check performance optimizations
        await self._check_performance_optimizations()

        # Check monitoring systems
        await self._check_monitoring_systems()

        # Check caching systems
        await self._check_caching_systems()

        # Check database optimizations
        await self._check_database_optimizations()

        # Check API optimizations
        await self._check_api_optimizations()

        # Generate report
        self._generate_report()

        return self.results

    async def _check_domain_managers(self) -> None:
        """Check for required domain managers."""
        print("\nChecking Domain Managers...")

        required_managers = [
            "packages/backend/domain/database_performance_manager.py",
            "packages/backend/domain/query_optimizer.py",
            "packages/backend/domain/cache_manager.py",
            "packages/backend/domain/connection_pool_manager.py",
            "packages/backend/domain/index_analyzer.py",
            "packages/backend/domain/performance_monitor.py",
        ]

        for manager_path in required_managers:
            full_path = project_root / manager_path
            if full_path.exists():
                self.results["domain_managers"]["existing"].append(manager_path)
                print(f"  SUCCESS: {manager_path}")
            else:
                self.results["domain_managers"]["missing"].append(manager_path)
                print(f"  FAILED: {manager_path}")

    async def _check_api_endpoints(self) -> None:
        """Check for required API endpoints."""
        print("\nChecking API Endpoints...")

        required_endpoints = [
            "apps/api/performance_endpoints.py",
            "apps/api/database_stats_endpoints.py",
            "apps/api/cache_endpoints.py",
            "apps/api/query_optimization_endpoints.py",
            "apps/api/monitoring_endpoints.py",
        ]

        for endpoint_path in required_endpoints:
            full_path = project_root / endpoint_path
            if full_path.exists():
                self.results["api_endpoints"]["existing"].append(endpoint_path)
                print(f"  SUCCESS: {endpoint_path}")
            else:
                self.results["api_endpoints"]["missing"].append(endpoint_path)
                print(f"  FAILED: {endpoint_path}")

    async def _check_database_migrations(self) -> None:
        """Check for required database migrations."""
        print("\nChecking Database Migrations...")

        required_migrations = [
            "migrations/010_database_performance.sql",
            "migrations/011_monitoring_tables.sql",
            "migrations/012_caching_tables.sql",
        ]

        for migration_path in required_migrations:
            full_path = project_root / migration_path
            if full_path.exists():
                self.results["database_migrations"]["existing"].append(migration_path)
                print(f"  SUCCESS: {migration_path}")
            else:
                self.results["database_migrations"]["missing"].append(migration_path)
                print(f"  FAILED: {migration_path}")

    async def _check_performance_optimizations(self) -> None:
        """Check for performance optimizations."""
        print("\nChecking Performance Optimizations...")

        # Check for performance-related configurations
        performance_files = [
            "shared/performance_config.py",
            "shared/query_cache.py",
            "shared/connection_pool.py",
            "shared/metrics_collector.py",
        ]

        for perf_file in performance_files:
            full_path = project_root / perf_file
            if full_path.exists():
                self.results["performance_optimizations"]["existing"].append(perf_file)
                print(f"  SUCCESS: {perf_file}")
            else:
                self.results["performance_optimizations"]["missing"].append(perf_file)
                print(f"  FAILED: {perf_file}")

    async def _check_monitoring_systems(self) -> None:
        """Check for monitoring systems."""
        print("\nChecking Monitoring Systems...")

        monitoring_files = [
            "shared/monitoring.py",
            "shared/metrics.py",
            "shared/alerting.py",
            "shared/health_checks.py",
            "shared/performance_metrics.py",
        ]

        for monitor_file in monitoring_files:
            full_path = project_root / monitor_file
            if full_path.exists():
                self.results["monitoring_systems"]["existing"].append(monitor_file)
                print(f"  SUCCESS: {monitor_file}")
            else:
                self.results["monitoring_systems"]["missing"].append(monitor_file)
                print(f"  FAILED: {monitor_file}")

    async def _check_caching_systems(self) -> None:
        """Check for caching systems."""
        print("\nChecking Caching Systems...")

        cache_files = [
            "shared/redis_cache.py",
            "shared/memory_cache.py",
            "shared/cache_manager.py",
            "shared/cache_strategies.py",
        ]

        for cache_file in cache_files:
            full_path = project_root / cache_file
            if full_path.exists():
                self.results["caching_systems"]["existing"].append(cache_file)
                print(f"  SUCCESS: {cache_file}")
            else:
                self.results["caching_systems"]["missing"].append(cache_file)
                print(f"  FAILED: {cache_file}")

    async def _check_database_optimizations(self) -> None:
        """Check for database optimizations."""
        print("\nChecking Database Optimizations...")

        # Check for existing database optimizations in migrations
        migration_files = list(project_root.glob("migrations/*.sql"))

        optimization_indicators = []
        for migration_file in migration_files:
            try:
                content = migration_file.read_text(encoding="utf-8")
                if any(
                    indicator in content.lower()
                    for indicator in [
                        "index",
                        "partition",
                        "optimize",
                        "vacuum",
                        "analyze",
                        "performance",
                        "cache",
                        "pool",
                        "connection",
                    ]
                ):
                    optimization_indicators.append(migration_file.name)
                    print(f"  SUCCESS: Found optimization in: {migration_file.name}")
            except Exception as e:
                print(f"  WARNING: Error reading {migration_file}: {e}")

        self.results["database_optimizations"]["existing"] = optimization_indicators

        # Check for specific optimization patterns
        if len(optimization_indicators) < 3:
            self.results["database_optimizations"]["missing"].append(
                "Additional database optimizations needed"
            )

    async def _check_api_optimizations(self) -> None:
        """Check for API optimizations."""
        print("\nChecking API Optimizations...")

        # Check API files for optimization patterns
        api_files = list(project_root.glob("apps/api/*.py"))

        optimization_indicators = []
        for api_file in api_files:
            try:
                content = api_file.read_text(encoding="utf-8")
                if any(
                    indicator in content.lower()
                    for indicator in [
                        "cache",
                        "pool",
                        "optimize",
                        "async",
                        "performance",
                        "limit",
                        "pagination",
                        "batch",
                        "bulk",
                    ]
                ):
                    optimization_indicators.append(api_file.name)
                    print(f"  SUCCESS: Found optimization in: {api_file.name}")
            except Exception as e:
                print(f"  WARNING: Error reading {api_file}: {e}")

        self.results["api_optimizations"]["existing"] = optimization_indicators

        # Check for specific optimization patterns
        if len(optimization_indicators) < 5:
            self.results["api_optimizations"]["missing"].append(
                "Additional API optimizations needed"
            )

    async def _check_database_connection(self) -> bool:
        """Test database connection."""
        try:
            conn = await asyncpg.connect(self.db_url)
            await conn.execute("SELECT 1")
            await conn.close()
            return True
        except Exception as e:
            if logger:
                logger.error(f"Database connection failed: {e}")
            return False

    def _generate_report(self) -> None:
        """Generate audit report."""
        print("\n" + "=" * 80)
        print("PHASE 15.1 DATABASE & PERFORMANCE AUDIT REPORT")
        print("=" * 80)

        total_missing = 0
        total_existing = 0

        for category, results in self.results.items():
            missing_count = len(results["missing"])
            existing_count = len(results["existing"])

            total_missing += missing_count
            total_existing += existing_count

            status = "COMPLETE" if missing_count == 0 else "INCOMPLETE"

            print(f"\n{category.replace('_', ' ').title()}: {status}")
            print(f"  Existing: {existing_count}")
            print(f"  Missing: {missing_count}")

            if results["missing"]:
                print("  Missing items:")
                for item in results["missing"]:
                    print(f"    - {item}")

        print("\nSUMMARY:")
        print(f"  Total Existing Components: {total_existing}")
        print(f"  Total Missing Components: {total_missing}")
        print(
            f"  Completion Status: {(total_existing / (total_existing + total_missing) * 100):.1f}%"
        )

        if total_missing == 0:
            print("\nPhase 15.1 is COMPLETE!")
        else:
            print(f"\nPhase 15.1 requires {total_missing} additional components.")

        print("=" * 80)


async def main():
    """Main audit function."""
    auditor = Phase15Auditor()
    results = await auditor.run_audit()

    # Save results to file
    results_file = project_root / "phase15_audit_results.json"
    try:
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to: {results_file}")
    except Exception as e:
        print(f"Error saving results: {e}")

    return results


if __name__ == "__main__":
    asyncio.run(main())
