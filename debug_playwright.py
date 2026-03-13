#!/usr/bin/env python3
"""
Debug script to verify Playwright browser installation status.
This helps diagnose why browsers aren't being found.
"""

import subprocess
import sys
import os

def check_browser_installation():
    """Check the status of Playwright browser installation."""
    print("=" * 60)
    print("PLAYWRIGHT BROWSER DEBUG INFO")
    print("=" * 60)
    
    # 1. Check Python version and executable
    print(f"\n1. Python executable: {sys.executable}")
    print(f"   Python version: {sys.version}")
    
    # 2. Check Playwright version
    try:
        import playwright
        print(f"\n2. Playwright package version: {playwright.__version__}")
    except ImportError as e:
        print(f"\n2. ERROR: Playwright not installed: {e}")
        return
    
    # 3. Check playwright driver version
    try:
        from playwright._driver import _get_driver_version
        driver_version = _get_driver_version()
        print(f"   Playwright driver version: {driver_version}")
    except Exception as e:
        print(f"   Could not get driver version: {e}")
    
    # 4. Check browser cache location
    print(f"\n3. Browser cache location:")
    try:
        # Common cache locations
        cache_paths = [
            os.path.expanduser("~/.cache/ms-playwright"),
            "/opt/render/.cache/ms-playwright",
            os.environ.get("PLAYWRIGHT_BROWSERS_PATH", ""),
        ]
        
        for path in cache_paths:
            if path and os.path.exists(path):
                print(f"   Found: {path}")
                # List contents
                try:
                    contents = os.listdir(path)
                    for item in contents:
                        item_path = os.path.join(path, item)
                        print(f"      - {item}")
                        if os.path.isdir(item_path):
                            subcontents = os.listdir(item_path)[:5]  # First 5 items
                            for sub in subcontents:
                                print(f"          - {sub}")
                except Exception as e:
                    print(f"      Error listing: {e}")
    except Exception as e:
        print(f"   Error checking cache: {e}")
    
    # 5. Try to launch browser directly
    print(f"\n4. Attempting to launch browser:")
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as pw:
            print("   Playwright sync context started")
            
            # Try headless=True (default)
            try:
                print("   Trying: chromium.launch(headless=True)...")
                browser = pw.chromium.launch(headless=True, timeout=10000)
                print("   SUCCESS: Browser launched headless=True")
                browser.close()
                return True
            except Exception as e:
                print(f"   FAILED: {e}")
            
            # Try headless=False
            try:
                print("   Trying: chromium.launch(headless=False)...")
                browser = pw.chromium.launch(headless=False, timeout=10000)
                print("   SUCCESS: Browser launched headless=False")
                browser.close()
                return True
            except Exception as e:
                print(f"   FAILED: {e}")
            
            # Try with channel="chromium"
            try:
                print("   Trying: chromium.launch(channel='chromium')...")
                browser = pw.chromium.launch(headless=True, channel="chromium", timeout=10000)
                print("   SUCCESS: Browser launched with channel='chromium'")
                browser.close()
                return True
            except Exception as e:
                print(f"   FAILED: {e}")
                
    except Exception as e:
        print(f"   ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("ALL BROWSER LAUNCH METHODS FAILED")
    print("=" * 60)
    
    # 6. Try to install browser
    print(f"\n5. Attempting to install browser:")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            capture_output=True,
            text=True,
            timeout=300
        )
        print(f"   Return code: {result.returncode}")
        if result.stdout:
            print(f"   Stdout: {result.stdout[:500]}")
        if result.stderr:
            print(f"   Stderr: {result.stderr[:500]}")
    except subprocess.TimeoutExpired:
        print("   ERROR: Install command timed out")
    except Exception as e:
        print(f"   ERROR: {e}")
    
    return False


if __name__ == "__main__":
    success = check_browser_installation()
    sys.exit(0 if success else 1)
