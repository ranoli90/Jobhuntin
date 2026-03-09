"""
Phase 14.1 User Experience - Complete Audit and Implementation
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


def audit_phase_14_1():
    """Comprehensive audit of Phase 14.1 User Experience."""
    print("=== PHASE 14.1 USER EXPERIENCE AUDIT ===")

    issues_found = []

    # Check domain managers
    print("\n--- Domain Managers ---")
    domain_managers = [
        "packages/backend/domain/user_experience_manager.py",
        "packages/backend/domain/ui_analytics_manager.py",
        "packages/backend/domain/feedback_manager.py",
        "packages/backend/domain/ab_testing_manager.py",
        "packages/backend/domain/user_behavior_analyzer.py",
        "packages/backend/domain/ux_metrics_collector.py",
    ]

    for dm in domain_managers:
        if os.path.exists(dm):
            print(f"SUCCESS: Domain manager exists: {dm}")
        else:
            print(f"FAILED: Domain manager missing: {dm}")
            issues_found.append(f"Missing domain manager: {dm}")

    # Check API endpoints
    print("\n--- API Endpoints ---")
    api_endpoints = [
        "apps/api/user_experience_endpoints.py",
        "apps/api/ui_analytics_endpoints.py",
        "apps/api/feedback_endpoints.py",
        "apps/api/ab_testing_endpoints.py",
        "apps/api/user_behavior_endpoints.py",
        "apps/api/ux_metrics_endpoints.py",
    ]

    for api in api_endpoints:
        if os.path.exists(api):
            print(f"SUCCESS: API endpoint exists: {api}")
        else:
            print(f"FAILED: API endpoint missing: {api}")
            issues_found.append(f"Missing API endpoint: {api}")

    # Check database migrations
    print("\n--- Database Migrations ---")
    migrations = [
        "migrations/009_user_experience.sql",
        "migrations/010_ui_analytics.sql",
        "migrations/011_feedback_system.sql",
    ]

    for migration in migrations:
        if os.path.exists(migration):
            print(f"SUCCESS: Migration exists: {migration}")
        else:
            print(f"FAILED: Migration missing: {migration}")
            issues_found.append(f"Missing migration: {migration}")

    # Check frontend components
    print("\n--- Frontend Components ---")
    components = [
        "apps/web/src/components/user-experience/UXDashboard.tsx",
        "apps/web/src/components/user-experience/FeedbackCollector.tsx",
        "apps/web/src/components/user-experience/ABTestingInterface.tsx",
        "apps/web/src/components/user-experience/BehaviorAnalytics.tsx",
        "apps/web/src/components/user-experience/UXMetrics.tsx",
        "apps/web/src/components/user-experience/UserJourney.tsx",
    ]

    for component in components:
        if os.path.exists(component):
            print(f"SUCCESS: Component exists: {component}")
        else:
            print(f"FAILED: Component missing: {component}")
            issues_found.append(f"Missing component: {component}")

    # Check frontend pages
    print("\n--- Frontend Pages ---")
    pages = [
        "apps/web/src/pages/app/user-experience/index.tsx",
        "apps/web/src/pages/app/user-experience/dashboard/index.tsx",
        "apps/web/src/pages/app/user-experience/feedback/index.tsx",
        "apps/web/src/pages/app/user-experience/analytics/index.tsx",
        "apps/web/src/pages/app/user-experience/ab-testing/index.tsx",
        "apps/web/src/pages/app/user-experience/journey/index.tsx",
    ]

    for page in pages:
        if os.path.exists(page):
            print(f"SUCCESS: Page exists: {page}")
        else:
            print(f"FAILED: Page missing: {page}")
            issues_found.append(f"Missing page: {page}")

    # Check main API integration
    print("\n--- Main API Integration ---")
    try:
        with open("apps/api/main.py", "r") as f:
            main_content = f.read()

        if "user_experience_endpoints" in main_content:
            print("SUCCESS: User experience endpoints imported in main.py")
        else:
            print("FAILED: User experience endpoints not imported in main.py")
            issues_found.append("User experience endpoints not imported in main.py")

        if "ui_analytics_endpoints" in main_content:
            print("SUCCESS: UI analytics endpoints imported in main.py")
        else:
            print("FAILED: UI analytics endpoints not imported in main.py")
            issues_found.append("UI analytics endpoints not imported in main.py")

        if "feedback_endpoints" in main_content:
            print("SUCCESS: Feedback endpoints imported in main.py")
        else:
            print("FAILED: Feedback endpoints not imported in main.py")
            issues_found.append("Feedback endpoints not imported in main.py")

    except Exception as e:
        print(f"FAILED: Error reading main.py: {e}")
        issues_found.append(f"Error reading main.py: {e}")

    # Check frontend routing
    print("\n--- Frontend Routing ---")
    try:
        with open("apps/web/src/App.tsx", "r") as f:
            app_content = f.read()

        if "user-experience" in app_content:
            print("SUCCESS: User experience routes in App.tsx")
        else:
            print("FAILED: User experience routes not in App.tsx")
            issues_found.append("User experience routes not in App.tsx")

        if "UXDashboard" in app_content:
            print("SUCCESS: UXDashboard imported in App.tsx")
        else:
            print("FAILED: UXDashboard not imported in App.tsx")
            issues_found.append("UXDashboard not imported in App.tsx")

        if "FeedbackCollector" in app_content:
            print("SUCCESS: FeedbackCollector imported in App.tsx")
        else:
            print("FAILED: FeedbackCollector not imported in App.tsx")
            issues_found.append("FeedbackCollector not imported in App.tsx")

    except Exception as e:
        print(f"FAILED: Error reading App.tsx: {e}")
        issues_found.append(f"Error reading App.tsx: {e}")

    # Check navigation menu
    print("\n--- Navigation Menu ---")
    try:
        with open("apps/web/src/layouts/AppLayout.tsx", "r") as f:
            layout_content = f.read()

        if "User Experience" in layout_content:
            print("SUCCESS: User Experience in navigation menu")
        else:
            print("FAILED: User Experience not in navigation menu")
            issues_found.append("User Experience not in navigation menu")

        if "UX Dashboard" in layout_content:
            print("SUCCESS: UX Dashboard in navigation menu")
        else:
            print("FAILED: UX Dashboard not in navigation menu")
            issues_found.append("UX Dashboard not in navigation menu")

        if "Feedback" in layout_content:
            print("SUCCESS: Feedback in navigation menu")
        else:
            print("FAILED: Feedback not in navigation menu")
            issues_found.append("Feedback not in navigation menu")

    except Exception as e:
        print(f"FAILED: Error reading AppLayout.tsx: {e}")
        issues_found.append(f"Error reading AppLayout.tsx: {e}")

    # Check domain manager implementations
    print("\n--- Domain Manager Implementations ---")
    try:
        # Check UserExperienceManager
        if os.path.exists("packages/backend/domain/user_experience_manager.py"):
            with open("packages/backend/domain/user_experience_manager.py", "r") as f:
                content = f.read()

            required_methods = [
                "track_user_session",
                "calculate_ux_score",
                "get_user_journey",
                "get_ux_insights",
            ]
            for method in required_methods:
                if f"def {method}" in content:
                    print(f"SUCCESS: UserExperienceManager has method: {method}")
                else:
                    print(f"FAILED: UserExperienceManager missing method: {method}")
                    issues_found.append(
                        f"UserExperienceManager missing method: {method}"
                    )

        # Check UIAnalyticsManager
        if os.path.exists("packages/backend/domain/ui_analytics_manager.py"):
            with open("packages/backend/domain/ui_analytics_manager.py", "r") as f:
                content = f.read()

            required_methods = [
                "track_page_view",
                "track_user_action",
                "get_analytics_summary",
                "get_conversion_funnel",
            ]
            for method in required_methods:
                if f"def {method}" in content:
                    print(f"SUCCESS: UIAnalyticsManager has method: {method}")
                else:
                    print(f"FAILED: UIAnalyticsManager missing method: {method}")
                    issues_found.append(f"UIAnalyticsManager missing method: {method}")

        # Check FeedbackManager
        if os.path.exists("packages/backend/domain/feedback_manager.py"):
            with open("packages/backend/domain/feedback_manager.py", "r") as f:
                content = f.read()

            required_methods = [
                "collect_feedback",
                "analyze_sentiment",
                "get_feedback_summary",
                "get_nps_score",
            ]
            for method in required_methods:
                if f"def {method}" in content:
                    print(f"SUCCESS: FeedbackManager has method: {method}")
                else:
                    print(f"FAILED: FeedbackManager missing method: {method}")
                    issues_found.append(f"FeedbackManager missing method: {method}")

    except Exception as e:
        print(f"FAILED: Error checking domain manager implementations: {e}")
        issues_found.append(f"Error checking domain manager implementations: {e}")

    # Check database tables exist
    print("\n--- Database Tables ---")
    required_tables = [
        "user_sessions",
        "page_views",
        "user_actions",
        "feedback_responses",
        "ab_test_experiments",
        "ab_test_variants",
        "user_journeys",
        "ux_metrics",
        "conversion_events",
        "user_satisfaction_scores",
    ]

    try:
        with open("migrations/009_user_experience.sql", "r") as f:
            migration_content = f.read()

        for table in required_tables:
            if f"CREATE TABLE IF NOT EXISTS {table}" in migration_content:
                print(f"SUCCESS: Database table exists: {table}")
            else:
                print(f"FAILED: Database table missing: {table}")
                issues_found.append(f"Missing database table: {table}")
    except Exception as e:
        print(f"FAILED: Error checking database tables: {e}")
        issues_found.append(f"Error checking database tables: {e}")

    print("\n=== PHASE 14.1 AUDIT COMPLETE ===")
    print(f"Issues found: {len(issues_found)}")

    if issues_found:
        print("\nISSUES TO FIX:")
        for issue in issues_found:
            print(f"  • {issue}")
    else:
        print("\nSUCCESS: ALL PHASE 14.1 COMPONENTS ARE COMPLETE!")

    return len(issues_found) == 0


if __name__ == "__main__":
    success = audit_phase_14_1()
    sys.exit(0 if success else 1)
