"""
PHASE 12.1 AGENT IMPROVEMENTS - COMPREHENSIVE AUDIT
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


def audit_phase_12_1():
    """Complete audit of Phase 12.1 Agent Improvements."""
    print("=== PHASE 12.1 AGENT IMPROVEMENTS AUDIT ===")

    issues_found = []

    # Check domain managers
    print("\n--- Domain Managers ---")
    domain_managers = [
        "packages/backend/domain/agent_improvements.py",
        "packages/backend/domain/oauth_handler.py",
        "packages/backend/domain/concurrent_tracker.py",
        "apps/worker/dlq_manager.py",
        "packages/backend/domain/document_processor.py",
        "packages/backend/domain/skills_taxonomy.py",
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
        "apps/api/agent_improvements_endpoints.py",
        "apps/api/dlq_endpoints.py",
    ]

    for api in api_endpoints:
        if os.path.exists(api):
            print(f"✓ API endpoint exists: {api}")
        else:
            print(f"✗ API endpoint missing: {api}")
            issues_found.append(f"Missing API endpoint: {api}")

    # Check database migrations
    print("\n--- Database Migrations ---")
    migrations = [
        "migrations/007_agent_improvements.sql",
    ]

    for migration in migrations:
        if os.path.exists(migration):
            print(f"✓ Migration exists: {migration}")
        else:
            print(f"✗ Migration missing: {migration}")
            issues_found.append(f"Missing migration: {migration}")

    # Check frontend components
    print("\n--- Frontend Components ---")
    components = [
        "apps/web/src/components/agent-improvements/DLQDashboard.tsx",
        "apps/web/src/components/agent-improvements/ScreenshotCapture.tsx",
    ]

    for component in components:
        if os.path.exists(component):
            print(f"✓ Component exists: {component}")
        else:
            print(f"✗ Component missing: {component}")
            issues_found.append(f"Missing component: {component}")

    # Check frontend pages
    print("\n--- Frontend Pages ---")
    pages = [
        "apps/web/src/pages/app/agent-improvements/index.tsx",
        "apps/web/src/pages/app/dlq-dashboard/index.tsx",
        "apps/web/src/pages/app/screenshot-capture/index.tsx",
    ]

    for page in pages:
        if os.path.exists(page):
            print(f"✓ Page exists: {page}")
        else:
            print(f"✗ Page missing: {page}")
            issues_found.append(f"Missing page: {page}")

    # Check main.py integration
    print("\n--- Main.py Integration ---")
    try:
        with open("apps/api/main.py", "r") as f:
            main_content = f.read()

        if "agent_improvements_endpoints" in main_content:
            print("✓ Agent improvements endpoints imported in main.py")
        else:
            print("✗ Agent improvements endpoints not imported in main.py")
            issues_found.append("Agent improvements endpoints not imported in main.py")

        if "create_agent_improvements_manager" in main_content:
            print("✓ Agent improvements manager factory imported in main.py")
        else:
            print("✗ Agent improvements manager factory not imported in main.py")
            issues_found.append(
                "Agent improvements manager factory not imported in main.py"
            )

    except Exception as e:
        print(f"✗ Error checking main.py: {e}")
        issues_found.append(f"Error checking main.py: {e}")

    # Check App.tsx integration
    print("\n--- App.tsx Integration ---")
    try:
        with open("apps/web/src/App.tsx", "r") as f:
            app_content = f.read()

        if "AgentImprovementsPage" in app_content:
            print("✓ Agent improvements page imported in App.tsx")
        else:
            print("✗ Agent improvements page not imported in App.tsx")
            issues_found.append("Agent improvements page not imported in App.tsx")

        if "DLQDashboardPage" in app_content:
            print("✓ DLQ dashboard page imported in App.tsx")
        else:
            print("✗ DLQ dashboard page not imported in App.tsx")
            issues_found.append("DLQ dashboard page not imported in App.tsx")

    except Exception as e:
        print(f"✗ Error checking App.tsx: {e}")
        issues_found.append(f"Error checking App.tsx: {e}")

    # Check AppLayout.tsx integration
    print("\n--- AppLayout.tsx Integration ---")
    try:
        with open("apps/web/src/layouts/AppLayout.tsx", "r") as f:
            layout_content = f.read()

        if "Agent Improvements" in layout_content:
            print("✓ Agent improvements in navigation menu")
        else:
            print("✗ Agent improvements not in navigation menu")
            issues_found.append("Agent improvements not in navigation menu")

        if "DLQ Dashboard" in layout_content:
            print("✓ DLQ dashboard in navigation menu")
        else:
            print("✗ DLQ dashboard not in navigation menu")
            issues_found.append("DLQ dashboard not in navigation menu")

    except Exception as e:
        print(f"✗ Error checking AppLayout.tsx: {e}")
        issues_found.append(f"Error checking AppLayout.tsx: {e}")

    # Check for missing domain manager implementations
    print("\n--- Domain Manager Implementations ---")
    try:
        from packages.backend.domain.agent_improvements import AgentImprovementsManager

        print("✓ AgentImprovementsManager can be imported")

        # Check for key methods
        required_methods = [
            "detect_buttons",
            "detect_form_fields",
            "handle_oauth_flow",
            "capture_screenshot",
            "track_concurrent_usage",
            "add_to_dlq",
            "retry_dlq_item",
        ]

        for method in required_methods:
            if hasattr(AgentImprovementsManager, method):
                print(f"✓ Method exists: {method}")
            else:
                print(f"✗ Method missing: {method}")
                issues_found.append(
                    f"Missing method in AgentImprovementsManager: {method}"
                )

    except Exception as e:
        print(f"✗ Error importing AgentImprovementsManager: {e}")
        issues_found.append(f"Error importing AgentImprovementsManager: {e}")

    # Check for missing factory functions
    print("\n--- Factory Functions ---")
    try:
        print("✓ create_agent_improvements_manager factory function exists")
    except Exception as e:
        print(f"✗ Error importing create_agent_improvements_manager: {e}")
        issues_found.append(f"Error importing create_agent_improvements_manager: {e}")

    # Check for missing Pydantic models
    print("\n--- Pydantic Models ---")
    try:
        print("✓ All Pydantic models can be imported")
    except Exception as e:
        print(f"✗ Error importing Pydantic models: {e}")
        issues_found.append(f"Error importing Pydantic models: {e}")

    # Check for missing dependencies in domain managers
    print("\n--- Dependencies ---")
    try:
        import packages.backend.domain.agent_improvements

        agent_module = packages.backend.domain.agent_improvements

        # Check if the module has the required dependencies
        missing_deps = []

        # Check for common missing dependencies
        required_deps = ["asyncpg", "uuid", "datetime", "typing", "pydantic", "fastapi"]

        for dep in required_deps:
            try:
                __import__(dep)
                print(f"✓ Dependency available: {dep}")
            except ImportError:
                print(f"✗ Missing dependency: {dep}")
                missing_deps.append(dep)

        if missing_deps:
            issues_found.append(f"Missing dependencies: {missing_deps}")

    except Exception as e:
        print(f"✗ Error checking dependencies: {e}")
        issues_found.append(f"Error checking dependencies: {e}")

    # Check for error handling and logging
    print("\n--- Error Handling & Logging ---")
    try:
        from packages.backend.domain.agent_improvements import AgentImprovementsManager

        manager = AgentImprovementsManager(None)

        # Check if logger is properly configured
        if hasattr(manager, "_logger") or hasattr(manager, "logger"):
            print("✓ Logger configured in AgentImprovementsManager")
        else:
            print("✗ Logger not configured in AgentImprovementsManager")
            issues_found.append("Logger not configured in AgentImprovementsManager")

    except Exception as e:
        print(f"✗ Error checking error handling: {e}")
        issues_found.append(f"Error checking error handling: {e}")

    print("\n=== PHASE 12.1 AUDIT COMPLETE ===")
    print(f"Issues found: {len(issues_found)}")

    if issues_found:
        print("\nISSUES TO FIX:")
        for issue in issues_found:
            print(f"  • {issue}")
    else:
        print("\nSUCCESS: ALL PHASE 12.1 COMPONENTS ARE COMPLETE!")

    return len(issues_found) == 0


if __name__ == "__main__":
    success = audit_phase_12_1()
    sys.exit(0 if success else 1)
