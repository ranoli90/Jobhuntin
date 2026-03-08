"""
Phase 12.1 Agent Improvements - Missing Components Audit
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def audit_missing_components():
    """Find missing components for Phase 12.1."""
    print("=== MISSING COMPONENTS AUDIT ===")
    
    missing_items = []
    
    # Check domain managers
    domain_managers = [
        "packages/backend/domain/oauth_handler.py", 
        "packages/backend/domain/concurrent_tracker.py",
        "packages/backend/domain/dlq_manager.py",
    ]
    
    print("Missing Domain Managers:")
    for dm in domain_managers:
        if not os.path.exists(dm):
            missing_items.append(f"Domain Manager: {dm}")
            print(f"  - {dm}")
    
    # Check API endpoints
    api_endpoints = [
        "apps/api/oauth_endpoints.py",
        "apps/api/concurrent_usage_endpoints.py",
        "apps/api/screenshot_endpoints.py",
        "apps/api/document_tracking_endpoints.py",
        "apps/api/performance_metrics_endpoints.py",
    ]
    
    print("\nMissing API Endpoints:")
    for api in api_endpoints:
        if not os.path.exists(api):
            missing_items.append(f"API Endpoint: {api}")
            print(f"  - {api}")
    
    # Check database tables that should exist
    database_tables = [
        "oauth_credentials",
        "concurrent_usage_sessions", 
        "screenshot_captures",
        "document_type_tracking",
        "agent_performance_metrics",
        "notification_semantic_tags",
        "user_interests",
    ]
    
    print("\nMissing Database Tables:")
    for table in database_tables:
        # Check if table exists in migration files
        found = False
        try:
            with open("migrations/007_agent_improvements.sql", "r") as f:
                content = f.read()
                if table in content:
                    found = True
        except:
            pass
        
        if not found:
            missing_items.append(f"Database Table: {table}")
            print(f"  - {table}")
    
    # Check frontend components
    frontend_components = [
        "apps/web/src/components/agent-improvements/OAuthHandler.tsx",
        "apps/web/src/components/agent-improvements/ConcurrentUsageMonitor.tsx",
        "apps/web/src/components/agent-improvements/DocumentProcessor.tsx",
        "apps/web/src/components/agent-improvements/PerformanceMetrics.tsx",
    ]
    
    print("\nMissing Frontend Components:")
    for component in frontend_components:
        if not os.path.exists(component):
            missing_items.append(f"Frontend Component: {component}")
            print(f"  - {component}")
    
    print(f"\nTOTAL MISSING ITEMS: {len(missing_items)}")
    
    return missing_items

if __name__ == "__main__":
    missing = audit_missing_components()
    if missing:
        print("\nMISSING ITEMS TO CREATE:")
        for item in missing:
            print(f"  - {item}")
        print("\nThese components need to be created for complete Phase 12.1 implementation.")
    else:
        print("\nAll Phase 12.1 components are present!")
