# Simple integration test for Phase 13.1 and 14.1

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_integration():
    print("Testing Phase 13.1 and 14.1 Integration...")
    
    # Test domain managers
    try:
        from packages.backend.domain.application_pipeline import ApplicationPipelineManager
        print("SUCCESS: ApplicationPipelineManager imported")
    except Exception as e:
        print(f"FAILED: ApplicationPipelineManager failed: {e}")
    
    try:
        from packages.backend.domain.application_export import ApplicationExportManager
        print("SUCCESS: ApplicationExportManager imported")
    except Exception as e:
        print(f"FAILED: ApplicationExportManager failed: {e}")
    
    try:
        from packages.backend.domain.follow_up_reminders import FollowUpManager
        print("SUCCESS: FollowUpManager imported")
    except Exception as e:
        print(f"FAILED: FollowUpManager failed: {e}")
    
    try:
        from packages.backend.domain.answer_memory import AnswerMemoryManager
        print("SUCCESS: AnswerMemoryManager imported")
    except Exception as e:
        print(f"FAILED: AnswerMemoryManager failed: {e}")
    
    try:
        from packages.backend.domain.multi_resume import MultiResumeManager
        print("SUCCESS: MultiResumeManager imported")
    except Exception as e:
        print(f"FAILED: MultiResumeManager failed: {e}")
    
    try:
        from packages.backend.domain.application_notes import ApplicationNotesManager
        print("SUCCESS: ApplicationNotesManager imported")
    except Exception as e:
        print(f"FAILED: ApplicationNotesManager failed: {e}")
    
    try:
        from packages.backend.domain.email_communications import EmailCommunicationManager
        print("SUCCESS: EmailCommunicationManager imported")
    except Exception as e:
        print(f"FAILED: EmailCommunicationManager failed: {e}")
    
    try:
        from packages.backend.domain.enhanced_notifications import EnhancedNotificationManager
        print("SUCCESS: EnhancedNotificationManager imported")
    except Exception as e:
        print(f"FAILED: EnhancedNotificationManager failed: {e}")
    
    print("\nIntegration test completed!")

if __name__ == "__main__":
    test_integration()
