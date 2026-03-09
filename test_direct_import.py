# Direct test of Phase 13.1 and 14.1 modules

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


def test_direct_imports():
    print("Testing direct imports...")

    try:
        # Test direct import of one module
        exec("""
import sys
sys.path.insert(0, '.')

from packages.backend.domain.application_pipeline import ApplicationPipelineManager
print("✓ Direct import of ApplicationPipelineManager works")
""")
    except Exception as e:
        print(f"X Direct import failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_direct_imports()
