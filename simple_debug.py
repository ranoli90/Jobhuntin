#!/usr/bin/env python3
"""
Simple Debug Tool for JobHuntin API
Finds all errors quickly with multiple debugging approaches.
"""

import os
import sys
import traceback
import subprocess
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

def test_imports_fast():
    """Fast import testing with detailed errors"""
    print("Testing Critical Imports...")
    print("=" * 50)
    
    imports_to_test = [
        ("FastAPI", "from fastapi import FastAPI"),
        ("Main API", "from api.main import app"),
        ("Dependencies", "import api.dependencies"),
        ("Backend Domain", "import packages.backend.domain.repositories"),
        ("LLM Client", "import packages.backend.llm.client"),
        ("Shared Config", "import shared.config"),
        ("Workers", "from apps.worker.scaling import main"),
    ]
    
    failed_imports = []
    
    for name, import_stmt in imports_to_test:
        try:
            exec(import_stmt)
            print(f"✅ {name}")
        except Exception as e:
            print(f"❌ {name}: {type(e).__name__}: {e}")
            failed_imports.append((name, import_stmt, str(e), traceback.format_exc()))
    
    if failed_imports:
        print(f"\n🚨 {len(failed_imports)} FAILED IMPORTS:")
        for name, import_stmt, error, tb in failed_imports:
            print(f"\n📝 {name}:")
            print(f"   Import: {import_stmt}")
            print(f"   Error: {error}")
            print(f"   Traceback:\n{tb}")
    
    return len(failed_imports) == 0

def test_api_startup():
    """Test API startup"""
    print("\nTesting API Startup...")
    print("=" * 50)
    
    try:
        os.environ['PYTHONPATH'] = 'apps:packages:.'
        os.environ['env'] = 'local'
        
        from api.main import app
        print("✅ App imported")
        
        routes = [route.path for route in app.routes]
        print(f"✅ {len(routes)} routes loaded")
        
        return True
        
    except Exception as e:
        print(f"❌ API Startup Failed: {type(e).__name__}: {e}")
        print("\n📋 Full Traceback:")
        traceback.print_exc()
        return False

def test_syntax():
    """Test syntax of all Python files"""
    print("\nTesting Python Syntax...")
    print("=" * 50)
    
    syntax_errors = []
    
    # Test key files
    key_files = [
        "apps/api/main.py",
        "apps/api/dependencies.py",
        "packages/backend/domain/repositories.py",
        "packages/backend/llm/client.py",
        "apps/worker/scaling.py",
    ]
    
    for file_path in key_files:
        try:
            result = subprocess.run([
                sys.executable, '-m', 'py_compile', file_path
            ], capture_output=True, text=True, cwd=project_root)
            
            if result.returncode == 0:
                print(f"✅ {file_path}")
            else:
                print(f"❌ {file_path}: {result.stderr}")
                syntax_errors.append((file_path, result.stderr))
                
        except Exception as e:
            print(f"❌ {file_path}: {e}")
            syntax_errors.append((file_path, str(e)))
    
    if syntax_errors:
        print(f"\n🚨 {len(syntax_errors)} SYNTAX ERRORS:")
        for file_path, error in syntax_errors:
            print(f"\n📝 {file_path}:")
            print(f"   Error: {error}")
    
    return len(syntax_errors) == 0

def create_debug_commands():
    """Create debug command shortcuts"""
    print("\nCreating Debug Commands...")
    
    debug_commands = '''
# Debug Commands for JobHuntin API

# 1. Basic PDB Debugging
python -m pdb -c "from api.main import app; print('API loaded successfully'); import pdb; pdb.set_trace()"

# 2. IPDB Debugging (enhanced)
python -m ipdb -c "from api.main import app; print('API loaded successfully'); import ipdb; ipdb.set_trace()"

# 3. Pudb Debugging (visual)
python -m pudb -c "from api.main import app; print('API loaded successfully'); import pudb; pudb.set_trace()"

# 4. Test with environment
PYTHONPATH=apps:packages:. python -c "from api.main import app; print('SUCCESS: API can start')"

# 5. Test specific imports
python -c "from packages.backend.llm.client import LLMClient; print('LLM Client OK')"

# 6. Test worker
python -c "from apps.worker.scaling import main; print('Worker scaling OK')"

# 7. Check all imports at once
python -c "
import sys
sys.path.insert(0, 'apps:packages:.')
try:
    from api.main import app
    from packages.backend.domain.repositories import ApplicationRepo
    from packages.backend.llm.client import LLMClient
    from apps.worker.scaling import main
    print('SUCCESS: ALL CRITICAL IMPORTS WORK')
except Exception as e:
    print(f'IMPORT ERROR: {e}')
    import traceback
    traceback.print_exc()
"
'''
    
    commands_file = project_root / "debug_commands.txt"
    commands_file.write_text(debug_commands)
    print(f"Debug commands saved to: {commands_file}")

def check_render_config():
    """Check render.yaml configuration"""
    print("\nChecking render.yaml...")
    print("=" * 50)
    
    render_file = project_root / "render.yaml"
    if render_file.exists():
        content = render_file.read_text()
        
        # Check for common issues
        issues = []
        
        if 'PYTHONPATH=apps:packages:.' in content and 'PYTHONPATH' in content:
            issues.append("PYTHONPATH defined in both startCommand and envVars")
        
        if content.count('PYTHONPATH=apps:packages:.') > 1:
            issues.append("Multiple PYTHONPATH assignments in startCommand")
        
        if issues:
            print("Configuration Issues Found:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("render.yaml configuration looks good")
    else:
        print("render.yaml not found")

def main():
    """Main debug function"""
    print("JobHuntin API Debug Tool")
    print("=" * 50)
    
    # Run all tests
    results = {
        'imports': test_imports_fast(),
        'syntax': test_syntax(),
        'api_startup': test_api_startup(),
    }
    
    # Additional checks
    check_render_config()
    create_debug_commands()
    
    # Summary
    print("\nDEBUG SUMMARY:")
    print("=" * 50)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name:15} {status}")
    
    # Quick recommendations
    print("\nQUICK FIXES:")
    print("=" * 50)
    
    if not results['imports']:
        print("All imports working! Try deployment now.")
        print("Check API: https://sorce-api.onrender.com/health")
    
    if not results['syntax']:
        print("All syntax correct!")
    
    if not results['api_startup']:
        print("API can start successfully!")
    
    if not all(results.values()):
        print("\nDEBUG OPTIONS:")
        print("1. Run: python debug_commands.txt (copy commands)")
        print("2. Use: python -m ipdb for enhanced debugging")
        print("3. Use: python -m pudb for visual debugging")
        print("4. Check logs in Render dashboard")

if __name__ == "__main__":
    main()
