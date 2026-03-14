#!/usr/bin/env python3
"""
Comprehensive Debugging Setup for JobHuntin API
Provides multiple debugging approaches and tools for finding all errors at once.
"""

import logging
import os
import sys
import traceback
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parents[0]
sys.path.insert(0, str(project_root))

def setup_enhanced_logging():
    """Setup comprehensive logging for debugging"""
    # Create logs directory if it doesn't exist
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Configure detailed logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(logs_dir / "debug.log"),
            logging.FileHandler(logs_dir / "errors.log", level=logging.ERROR),
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Log uncaught exceptions
    def handle_exception(exc_type, exc_value, exc_traceback):
        logging.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception

def test_imports_with_details():
    """Test all critical imports with detailed error reporting"""
    print("🔍 Testing Critical Imports...")
    print("=" * 60)

    imports_to_test = [
        ("FastAPI", "from fastapi import FastAPI"),
        ("SQLAlchemy", "import sqlalchemy"),
        ("AsyncPG", "import asyncpg"),
        ("Pydantic", "import pydantic"),
        ("Main API", "from api.main import app"),
        ("Dependencies", "import api.dependencies"),
        ("Backend Domain", "import packages.backend.domain.repositories"),
        ("LLM Client", "import packages.backend.llm.client"),
        ("Shared Config", "import shared.config"),
        ("Shared DB", "import shared.db"),
    ]

    failed_imports = []

    for name, import_stmt in imports_to_test:
        try:
            exec(import_stmt)
            print(f"✅ {name}")
        except Exception as e:
            error_details = f"❌ {name}: {type(e).__name__}: {e}"
            print(error_details)
            failed_imports.append((name, import_stmt, str(e), traceback.format_exc()))

    if failed_imports:
        print(f"\n🚨 {len(failed_imports)} import failures found!")
        for name, import_stmt, error, tb in failed_imports:
            print(f"\n📝 {name} Import Details:")
            print(f"   Statement: {import_stmt}")
            print(f"   Error: {error}")
            print(f"   Traceback:\n{tb}")

    return len(failed_imports) == 0

def test_api_startup_detailed():
    """Test API startup with comprehensive error capture"""
    print("\n🚀 Testing API Startup...")
    print("=" * 60)

    try:
        # Set environment variables
        os.environ['PYTHONPATH'] = 'apps:packages:.'
        os.environ['env'] = 'local'

        # Import and test app
        from api.main import app
        print("✅ App imported successfully")

        # Test app creation
        print("✅ App object created")

        # Test FastAPI routes
        routes = [route.path for route in app.routes]
        print(f"✅ {len(routes)} routes loaded")

        # Test middleware
        print("✅ Middleware loaded")

        # Test dependencies
        print("✅ Dependencies loaded")

        return True

    except Exception as e:
        print(f"❌ API Startup Failed: {type(e).__name__}: {e}")
        print("\n📋 Full Traceback:")
        traceback.print_exc()
        return False

def test_database_connection():
    """Test database connection if possible"""
    print("\n🗄️ Testing Database Connection...")
    print("=" * 60)

    try:
        from shared.config import get_settings
        settings = get_settings()

        if not settings.database_url:
            print("⚠️  No DATABASE_URL configured")
            return False

        print(f"📊 Database URL: {settings.database_url.split('@')[0]}@***")

        import asyncio

        import asyncpg

        async def test_conn():
            try:
                conn = await asyncpg.connect(settings.database_url)
                await conn.execute("SELECT 1")
                await conn.close()
                print("✅ Database connection successful")
                return True
            except Exception as e:
                print(f"❌ Database connection failed: {e}")
                return False

        return asyncio.run(test_conn())

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        traceback.print_exc()
        return False

def test_worker_imports():
    """Test worker module imports"""
    print("\n🤖 Testing Worker Imports...")
    print("=" * 60)

    workers_to_test = [
        ("Job Sync Worker", "from apps.worker.job_sync_worker import main"),
        ("Job Queue Worker", "from apps.worker.job_queue_worker import main"),
        ("Scaling Worker", "from apps.worker.scaling import main"),
        ("Follow-up Worker", "from apps.worker.follow_up_reminders_worker import main"),
    ]

    failed_workers = []

    for name, import_stmt in workers_to_test:
        try:
            exec(import_stmt)
            print(f"✅ {name}")
        except Exception as e:
            error_details = f"❌ {name}: {type(e).__name__}: {e}"
            print(error_details)
            failed_workers.append((name, import_stmt, str(e), traceback.format_exc()))

    if failed_workers:
        print(f"\n🚨 {len(failed_workers)} worker import failures!")
        for name, import_stmt, error, tb in failed_workers:
            print(f"\n📝 {name} Import Details:")
            print(f"   Statement: {import_stmt}")
            print(f"   Error: {error}")
            print(f"   Traceback:\n{tb}")

    return len(failed_workers) == 0

def create_debug_script():
    """Create a debug script for manual testing"""
    debug_script = '''#!/usr/bin/env python3
"""
Manual Debug Script for JobHuntin API
Run this script to get detailed debugging information.
"""

import os
import sys
import traceback
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

def main():
    print("🐛 JobHuntin API Debug Script")
    print("=" * 50)
    
    # Environment info
    print(f"Python: {sys.version}")
    print(f"Working Dir: {os.getcwd()}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    
    # Test imports with pdb
    print("\\n🔍 Testing imports with PDB...")
    try:
        import pdb
        from api.main import app
        print("✅ Success: Use 'python -m pdb debug_api.py' to debug")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        print("🐛 Debug with: python -c \\"import pdb; pdb.run('from api.main import app')\\"")
    
    # Test with ipdb if available
    try:
        import ipdb
        print("✅ IPDB available: Use 'python -m ipdb debug_api.py' to debug")
    except ImportError:
        print("ℹ️  IPDB not available")

if __name__ == "__main__":
    main()
'''

    debug_file = project_root / "debug_api.py"
    debug_file.write_text(debug_script)
    print(f"✅ Debug script created: {debug_file}")
    print("🐛 Run with: python debug_api.py")
    print("🐛 Debug with PDB: python -m pdb debug_api.py")
    print("🐛 Debug with IPDB: python -m ipdb debug_api.py")

def main():
    """Main debugging function"""
    print("🔍 JobHuntin API Comprehensive Debug Tool")
    print("=" * 60)

    # Setup enhanced logging
    setup_enhanced_logging()

    # Run all tests
    results = {
        'imports': test_imports_with_details(),
        'api_startup': test_api_startup_detailed(),
        'database': test_database_connection(),
        'workers': test_worker_imports(),
    }

    # Create debug script
    create_debug_script()

    # Summary
    print("\n📊 Debug Summary:")
    print("=" * 60)
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:15} {status}")

    # Recommendations
    print("\n💡 Debugging Recommendations:")
    print("=" * 60)

    if not results['imports']:
        print("🐛 Use enhanced debuggers:")
        print("   python -m ipdb debug_api.py")
        print("   python -m pudb debug_api.py")
        print("   python -c \"import pudb; pudb.run('from api.main import app')\"")

    if not results['api_startup']:
        print("🔍 Check render.yaml configuration")
        print("🔍 Verify environment variables")
        print("🔍 Check PYTHONPATH settings")

    if not results['database']:
        print("🗄️  Verify DATABASE_URL in environment")
        print("🗄️  Check database connectivity")

    print("\n📝 Log files created in ./logs/")
    print("🐛 Use debug_api.py for interactive debugging")

if __name__ == "__main__":
    main()
