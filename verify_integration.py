"""
Phase 13.1 and 14.1 Integration Verification

This script verifies that all the new features are properly integrated into the system.
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def verify_phase_13_1():
    """Verify Phase 13.1 Communication System integration."""
    print("=== PHASE 13.1 COMMUNICATION SYSTEM ===")
    
    # Test email communications
    try:
        from packages.backend.domain.email_communications import (
            EmailCommunicationManager,
            EmailTemplate,
        )
        print("SUCCESS: Email communications system integrated")
    except Exception as e:
        print(f"FAILED: Email communications failed: {e}")
        return False
    
    # Test enhanced notifications
    try:
        from packages.backend.domain.enhanced_notifications import (
            EnhancedNotificationManager,
            NotificationContent,
            NotificationCategory,
            NotificationPriority,
        )
        print("SUCCESS: Enhanced notifications system integrated")
    except Exception as e:
        print(f"FAILED: Enhanced notifications failed: {e}")
        return False
    
    return True

def verify_phase_14_1():
    """Verify Phase 14.1 User Experience integration."""
    print("\n=== PHASE 14.1 USER EXPERIENCE ===")
    
    # Test pipeline view
    try:
        from packages.backend.domain.application_pipeline import (
            ApplicationPipelineManager,
            PipelineView,
            PipelineStage,
        )
        print("SUCCESS: Pipeline view system integrated")
    except Exception as e:
        print(f"FAILED: Pipeline view failed: {e}")
        return False
    
    # Test application export
    try:
        from packages.backend.domain.application_export import (
            ApplicationExportManager,
            ExportConfig,
        )
        print("SUCCESS: Application export system integrated")
    except Exception as e:
        print(f"FAILED: Application export failed: {e}")
        return False
    
    # Test follow-up reminders
    try:
        from packages.backend.domain.follow_up_reminders import (
            FollowUpManager,
            FollowUpReminder,
            ReminderSchedule,
        )
        print("SUCCESS: Follow-up reminders system integrated")
    except Exception as e:
        print(f"FAILED: Follow-up reminders failed: {e}")
        return False
    
    # Test answer memory
    try:
        from packages.backend.domain.answer_memory import (
            AnswerMemoryManager,
            InterviewQuestion,
            AnswerAttempt,
            AnswerMemory,
        )
        print("SUCCESS: Answer memory system integrated")
    except Exception as e:
        print(f"FAILED: Answer memory failed: {e}")
        return False
    
    # Test multi-resume support
    try:
        from packages.backend.domain.multi_resume import (
            MultiResumeManager,
            ResumeVersion,
            ResumeComparison,
            ResumeAnalytics,
        )
        print("SUCCESS: Multi-resume support system integrated")
    except Exception as e:
        print(f"FAILED: Multi-resume support failed: {e}")
        return False
    
    # Test application notes
    try:
        from packages.backend.domain.application_notes import (
            ApplicationNotesManager,
            ApplicationNote,
            NoteTemplate,
        )
        print("SUCCESS: Application notes system integrated")
    except Exception as e:
        print(f"FAILED: Application notes failed: {e}")
        return False
    
    return True

def verify_database_schema():
    """Verify database schema files exist."""
    print("\n=== DATABASE SCHEMA ===")
    
    migration_file = "migrations/008_user_experience_features.sql"
    if os.path.exists(migration_file):
        print(f"SUCCESS: Database migration file exists: {migration_file}")
    else:
        print(f"FAILED: Database migration file missing: {migration_file}")
        return False
    
    return True

def verify_api_endpoints():
    """Verify API endpoint files exist."""
    print("\n=== API ENDPOINTS ===")
    
    # Check user experience endpoints
    ux_file = "apps/api/user_experience_endpoints.py"
    if os.path.exists(ux_file):
        print(f"SUCCESS: User experience endpoints exist: {ux_file}")
    else:
        print(f"FAILED: User experience endpoints missing: {ux_file}")
        return False
    
    # Check communication endpoints
    comm_file = "apps/api/communication_endpoints.py"
    if os.path.exists(comm_file):
        print(f"SUCCESS: Communication endpoints exist: {comm_file}")
    else:
        print(f"FAILED: Communication endpoints missing: {comm_file}")
        return False
    
    return True

def verify_main_api_integration():
    """Verify main.py integration."""
    print("\n=== MAIN API INTEGRATION ===")
    
    try:
        # Check if the routers are mentioned in main.py
        with open("apps/api/main.py", "r") as f:
            content = f.read()
            
        if "user_experience_endpoints" in content:
            print("SUCCESS: User experience endpoints referenced in main.py")
        else:
            print("FAILED: User experience endpoints not referenced in main.py")
            return False
        
        if "communication_endpoints" in content:
            print("SUCCESS: Communication endpoints referenced in main.py")
        else:
            print("FAILED: Communication endpoints not referenced in main.py")
            return False
        
        return True
    except Exception as e:
        print(f"FAILED: Failed to check main.py integration: {e}")
        return False

def main():
    """Run all verification tests."""
    print("PHASE 13.1 & 14.1 INTEGRATION VERIFICATION")
    print("=" * 50)
    
    success = True
    
    # Verify Phase 13.1
    if not verify_phase_13_1():
        success = False
    
    # Verify Phase 14.1
    if not verify_phase_14_1():
        success = False
    
    # Verify database schema
    if not verify_database_schema():
        success = False
    
    # Verify API endpoints
    if not verify_api_endpoints():
        success = False
    
    # Verify main API integration
    if not verify_main_api_integration():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("SUCCESS: ALL INTEGRATION TESTS PASSED")
        print("SUCCESS: Phase 13.1 and 14.1 are properly integrated into the system")
        print("\nNEXT STEPS:")
        print("1. Run database migrations: apply migrations/008_user_experience_features.sql")
        print("2. Test API endpoints with actual database connection")
        print("3. Verify frontend integration")
    else:
        print("FAILED: SOME INTEGRATION TESTS FAILED")
        print("FAILED: Please fix the issues above before proceeding")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
