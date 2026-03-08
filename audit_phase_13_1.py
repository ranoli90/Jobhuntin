"""
Phase 13.1 Communication System - Complete Audit and Implementation
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def audit_phase_13_1():
    """Comprehensive audit of Phase 13.1 Communication System."""
    print("=== PHASE 13.1 COMMUNICATION SYSTEM AUDIT ===")
    
    issues_found = []
    
    # Check domain managers
    print("\n--- Domain Managers ---")
    domain_managers = [
        "packages/backend/domain/email_communication_manager.py",
        "packages/backend/domain/notification_manager.py", 
        "packages/backend/domain/semantic_notification_matcher.py",
        "packages/backend/domain/alert_processor.py",
        "packages/backend/domain/user_interest_profiler.py",
        "packages/backend/domain/notification_batch_processor.py",
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
        "apps/api/communications_endpoints.py",
        "apps/api/notifications_endpoints.py",
        "apps/api/alerts_endpoints.py",
        "apps/api/email_endpoints.py",
        "apps/api/batch_notifications_endpoints.py",
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
        "migrations/008_communication_system.sql",
        "migrations/009_notification_semantic_tags.sql",
        "migrations/010_user_interests.sql",
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
        "apps/web/src/components/communications/EmailManager.tsx",
        "apps/web/src/components/communications/NotificationManager.tsx",
        "apps/web/src/components/communications/AlertProcessor.tsx",
        "apps/web/src/components/communications/SemanticMatcher.tsx",
        "apps/web/src/components/communications/UserInterests.tsx",
        "apps/web/src/components/communications/BatchProcessor.tsx",
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
        "apps/web/src/pages/app/communications/index.tsx",
        "apps/web/src/pages/app/communications/email/index.tsx",
        "apps/web/src/pages/app/communications/notifications/index.tsx",
        "apps/web/src/pages/app/communications/alerts/index.tsx",
        "apps/web/src/pages/app/communications/preferences/index.tsx",
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
        
        if "communications_endpoints" in main_content:
            print("SUCCESS: Communications endpoints imported in main.py")
        else:
            print("FAILED: Communications endpoints not imported in main.py")
            issues_found.append("Communications endpoints not imported in main.py")
        
        if "notifications_endpoints" in main_content:
            print("SUCCESS: Notifications endpoints imported in main.py")
        else:
            print("FAILED: Notifications endpoints not imported in main.py")
            issues_found.append("Notifications endpoints not imported in main.py")
        
        if "alerts_endpoints" in main_content:
            print("SUCCESS: Alerts endpoints imported in main.py")
        else:
            print("FAILED: Alerts endpoints not imported in main.py")
            issues_found.append("Alerts endpoints not imported in main.py")
        
    except Exception as e:
        print(f"FAILED: Error reading main.py: {e}")
        issues_found.append(f"Error reading main.py: {e}")
    
    # Check frontend routing
    print("\n--- Frontend Routing ---")
    try:
        with open("apps/web/src/App.tsx", "r") as f:
            app_content = f.read()
        
        if "communications" in app_content:
            print("SUCCESS: Communications routes in App.tsx")
        else:
            print("FAILED: Communications routes not in App.tsx")
            issues_found.append("Communications routes not in App.tsx")
        
        if "EmailManager" in app_content:
            print("SUCCESS: EmailManager imported in App.tsx")
        else:
            print("FAILED: EmailManager not imported in App.tsx")
            issues_found.append("EmailManager not imported in App.tsx")
        
        if "NotificationManager" in app_content:
            print("SUCCESS: NotificationManager imported in App.tsx")
        else:
            print("FAILED: NotificationManager not imported in App.tsx")
            issues_found.append("NotificationManager not imported in App.tsx")
        
    except Exception as e:
        print(f"FAILED: Error reading App.tsx: {e}")
        issues_found.append(f"Error reading App.tsx: {e}")
    
    # Check navigation menu
    print("\n--- Navigation Menu ---")
    try:
        with open("apps/web/src/layouts/AppLayout.tsx", "r") as f:
            layout_content = f.read()
        
        if "Communications" in layout_content:
            print("SUCCESS: Communications in navigation menu")
        else:
            print("FAILED: Communications not in navigation menu")
            issues_found.append("Communications not in navigation menu")
        
        if "Email Manager" in layout_content:
            print("SUCCESS: Email Manager in navigation menu")
        else:
            print("FAILED: Email Manager not in navigation menu")
            issues_found.append("Email Manager not in navigation menu")
        
        if "Notifications" in layout_content:
            print("SUCCESS: Notifications in navigation menu")
        else:
            print("FAILED: Notifications not in navigation menu")
            issues_found.append("Notifications not in navigation menu")
        
    except Exception as e:
        print(f"FAILED: Error reading AppLayout.tsx: {e}")
        issues_found.append(f"Error reading AppLayout.tsx: {e}")
    
    # Check domain manager implementations
    print("\n--- Domain Manager Implementations ---")
    try:
        # Check EmailCommunicationManager
        if os.path.exists("packages/backend/domain/email_communication_manager.py"):
            with open("packages/backend/domain/email_communication_manager.py", "r") as f:
                content = f.read()
            
            required_methods = ["send_email", "send_template_email", "get_email_preferences", "update_email_preferences"]
            for method in required_methods:
                if f"def {method}" in content:
                    print(f"SUCCESS: EmailCommunicationManager has method: {method}")
                else:
                    print(f"FAILED: EmailCommunicationManager missing method: {method}")
                    issues_found.append(f"EmailCommunicationManager missing method: {method}")
        
        # Check NotificationManager
        if os.path.exists("packages/backend/domain/notification_manager.py"):
            with open("packages/backend/domain/notification_manager.py", "r") as f:
                content = f.read()
            
            required_methods = ["send_notification", "send_batch_notifications", "get_user_preferences", "update_preferences"]
            for method in required_methods:
                if f"def {method}" in content:
                    print(f"SUCCESS: NotificationManager has method: {method}")
                else:
                    print(f"FAILED: NotificationManager missing method: {method}")
                    issues_found.append(f"NotificationManager missing method: {method}")
        
        # Check SemanticNotificationMatcher
        if os.path.exists("packages/backend/domain/semantic_notification_matcher.py"):
            with open("packages/backend/domain/semantic_notification_matcher.py", "r") as f:
                content = f.read()
            
            required_methods = ["calculate_relevance", "match_notifications", "update_user_profile"]
            for method in required_methods:
                if f"def {method}" in content:
                    print(f"SUCCESS: SemanticNotificationMatcher has method: {method}")
                else:
                    print(f"FAILED: SemanticNotificationMatcher missing method: {method}")
                    issues_found.append(f"SemanticNotificationMatcher missing method: {method}")
        
    except Exception as e:
        print(f"FAILED: Error checking domain manager implementations: {e}")
        issues_found.append(f"Error checking domain manager implementations: {e}")
    
    # Check database tables exist
    print("\n--- Database Tables ---")
    required_tables = [
        "email_communications_log",
        "email_preferences",
        "notification_delivery_tracking",
        "notification_semantic_tags",
        "user_interests",
        "alert_processing_log",
        "notification_batches",
        "user_preferences",
    ]
    
    try:
        with open("migrations/007_agent_improvements.sql", "r") as f:
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
    
    print(f"\n=== PHASE 13.1 AUDIT COMPLETE ===")
    print(f"Issues found: {len(issues_found)}")
    
    if issues_found:
        print("\nISSUES TO FIX:")
        for issue in issues_found:
            print(f"  • {issue}")
    else:
        print("\nSUCCESS: ALL PHASE 13.1 COMPONENTS ARE COMPLETE!")
    
    return len(issues_found) == 0

if __name__ == "__main__":
    success = audit_phase_13_1()
    sys.exit(0 if success else 1)
