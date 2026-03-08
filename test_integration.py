# Test script to verify Phase 13.1 and 14.1 integration

def test_imports():
    print("Testing Phase 13.1 Communication System imports...")
    
    try:
        from packages.backend.domain.email_communications import EmailCommunicationManager
        print("✓ EmailCommunicationManager imported")
    except Exception as e:
        print(f"✗ EmailCommunicationManager import failed: {e}")
    
    try:
        from packages.backend.domain.enhanced_notifications import EnhancedNotificationManager
        print("✓ EnhancedNotificationManager imported")
    except Exception as e:
        print(f"✗ EnhancedNotificationManager import failed: {e}")
    
    print("\nTesting Phase 14.1 User Experience imports...")
    
    try:
        from packages.backend.domain.application_pipeline import ApplicationPipelineManager
        print("✓ ApplicationPipelineManager imported")
    except Exception as e:
        print(f"✗ ApplicationPipelineManager import failed: {e}")
    
    try:
        from packages.backend.domain.application_export import ApplicationExportManager
        print("✓ ApplicationExportManager imported")
    except Exception as e:
        print(f"✗ ApplicationExportManager import failed: {e}")
    
    try:
        from packages.backend.domain.follow_up_reminders import FollowUpManager
        print("✓ FollowUpManager imported")
    except Exception as e:
        print(f"✗ FollowUpManager import failed: {e}")
    
    try:
        from packages.backend.domain.answer_memory import AnswerMemoryManager
        print("✓ AnswerMemoryManager imported")
    except Exception as e:
        print(f"✗ AnswerMemoryManager import failed: {e}")
    
    try:
        from packages.backend.domain.multi_resume import MultiResumeManager
        print("✓ MultiResumeManager imported")
    except Exception as e:
        print(f"✗ MultiResumeManager import failed: {e}")
    
    try:
        from packages.backend.domain.application_notes import ApplicationNotesManager
        print("✓ ApplicationNotesManager imported")
    except Exception as e:
        print(f"✗ ApplicationNotesManager import failed: {e}")
    
    print("\nTesting API endpoint imports...")
    
    try:
        from apps.api.communication_endpoints import router as comm_router
        print("✓ Communication endpoints imported")
    except Exception as e:
        print(f"✗ Communication endpoints import failed: {e}")
    
    try:
        from apps.api.user_experience_endpoints import router as ux_router
        print("✓ User experience endpoints imported")
    except Exception as e:
        print(f"✗ User experience endpoints import failed: {e}")
    
    try:
        from apps.api.dlq_endpoints import router as dlq_router
        print("✓ DLQ endpoints imported")
    except Exception as e:
        print(f"✗ DLQ endpoints import failed: {e}")

if __name__ == "__main__":
    test_imports()
