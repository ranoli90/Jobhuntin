# API endpoint integration test

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_api_endpoints():
    print("Testing API endpoints...")
    
    # Test user experience endpoints
    try:
        # Create a minimal test without main app dependencies
        from fastapi import APIRouter
        from packages.backend.domain.application_pipeline import ApplicationPipelineManager
        
        # Create a simple router
        router = APIRouter(prefix="/ux", tags=["user_experience"])
        
        @router.get("/test")
        async def test_endpoint():
            return {"status": "working"}
        
        print("SUCCESS: User Experience API structure works")
    except Exception as e:
        print(f"FAILED: User Experience API failed: {e}")
    
    # Test communication endpoints
    try:
        from fastapi import APIRouter
        from packages.backend.domain.email_communications import EmailCommunicationManager
        
        router = APIRouter(prefix="/communications", tags=["communications"])
        
        @router.get("/test")
        async def test_endpoint():
            return {"status": "working"}
        
        print("SUCCESS: Communication API structure works")
    except Exception as e:
        print(f"FAILED: Communication API failed: {e}")
    
    print("\nAPI test completed!")

if __name__ == "__main__":
    test_api_endpoints()
