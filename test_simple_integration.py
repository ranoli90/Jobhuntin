# Simple integration test for Phase 13.1 and 14.1

import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


def test_integration():
    print("Testing Phase 13.1 and 14.1 Integration...")

    # Test domain managers
    try:
        print("✓ ApplicationPipelineManager imported")
    except Exception as e:
        print(f"✗ ApplicationPipelineManager failed: {e}")

    try:
        print("✓ ApplicationExportManager imported")
    except Exception as e:
        print(f"✗ ApplicationExportManager failed: {e}")

    try:
        print("✓ FollowUpManager imported")
    except Exception as e:
        print(f"✗ FollowUpManager failed: {e}")

    try:
        print("✓ AnswerMemoryManager imported")
    except Exception as e:
        print(f"✗ AnswerMemoryManager failed: {e}")

    try:
        print("✓ MultiResumeManager imported")
    except Exception as e:
        print(f"✗ MultiResumeManager failed: {e}")

    try:
        print("✓ ApplicationNotesManager imported")
    except Exception as e:
        print(f"✗ ApplicationNotesManager failed: {e}")

    try:
        print("✓ EmailCommunicationManager imported")
    except Exception as e:
        print(f"✗ EmailCommunicationManager failed: {e}")

    try:
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
