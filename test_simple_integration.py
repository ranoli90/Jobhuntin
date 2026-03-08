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
        print("✓ ApplicationPipelineManager imported")
    except Exception as e:
        print(f"✗ ApplicationPipelineManager failed: {e}")
    
    try:
        from packages.backend.domain.application_export import ApplicationExportManager
        print("✓ ApplicationExportManager imported")
    except Exception as e:
        print(f"✗ ApplicationExportManager failed: {e}")
    
    try:
        from packages.backend.domain.follow_up_reminders import FollowUpManager
        print("✓ FollowUpManager imported")
    except Exception as e:
        print(f"✗ FollowUpManager failed: {e}")
    
    try:
        from packages.backend.domain.answer_memory import AnswerMemoryManager
        print("✓ AnswerMemoryManager imported")
    except Exception as e:
        print(f"✗ AnswerMemoryManager failed: {e}")
    
    try:
        from packages.backend.domain.multi_resume import MultiResumeManager
        print("✓ MultiResumeManager imported")
    except Exception as e:
        print(f"✗ MultiResumeManager failed: {e}")
    
    try:
        from packages.backend.domain.application_notes import ApplicationNotesManager
        print("✓ ApplicationNotesManager imported")
    except Exception as e:
        print(f"✗ ApplicationNotesManager failed: {e}")
    
    try:
        from packages.backend.domain.email_communications import EmailCommunicationManager
        print("✓ EmailCommunicationManager imported")
    except Exception as e:
        print(f"✗ EmailCommunicationManager failed: {e}")
    
    try:
        from packages.backend.domain.enhanced_notifications import EnhancedNotificationManager
        print("✓ EnhancedNotificationManager imported")
    except Exception as e:
        print(f"✗ EnhancedNotificationManager failed: {e}")
    
    # Test API endpoints (without main app imports)
    try:
        # Test just the router creation
        from fastapi import APIRouter
        router = APIRouter(prefix="/test", tags=["test"])
        print("✓ API Router creation works")
    except Exception as e:
        print(f"✗ API Router failed: {e}")
    
    print("\nIntegration test completed!")

if __name__ == "__main__":
    test_integration()
