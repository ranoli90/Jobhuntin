#!/usr/bin/env python3
"""
Direct Dashboard Log Access
Opens the Render dashboard directly to view logs
"""

import webbrowser
from pathlib import Path


def open_dashboard_logs():
    """Open Render dashboard logs directly"""

    # Direct URLs for the jobhuntin-api service
    dashboard_urls = [
        "https://dashboard.render.com/web/srv-d6p4l03h46gs73ftvuj0",
        "https://dashboard.render.com/services/jobhuntin-api",
        "https://dashboard.render.com/services/jobhuntin-api/logs",
        "https://dashboard.render.com/services/jobhuntin-api/events"
    ]

    print("🔍 Opening Render Dashboard Logs...")
    print("=" * 60)

    for i, url in enumerate(dashboard_urls, 1):
        print(f"{i}. {url}")
        try:
            webbrowser.open(url)
            print("   ✅ Opened in browser")
        except Exception as e:
            print(f"   ❌ Failed to open: {e}")

        if i < len(dashboard_urls):
            input("Press Enter to continue to next URL...")

    print("\n📋 What to look for in the logs:")
    print("=" * 60)
    print("1. Recent deployment errors")
    print("2. Import/Module errors")
    print("3. Database connection issues")
    print("4. Environment variable problems")
    print("5. Startup failures")

    print("\n🔍 Common Error Patterns:")
    print("=" * 60)
    print("- ModuleNotFoundError: Missing imports")
    print("- ImportError: Import path issues")
    print("- ConnectionError: Database issues")
    print("- KeyError: Missing environment variables")
    print("- SyntaxError: Code syntax issues")
    print("- HTTP 503/500: Service startup failures")

    print("\n💡 Quick Fix Checklist:")
    print("=" * 60)
    print("✅ API Key: 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")
    print("✅ JWT Secret: 5ac9f551548b8c8eb2f45db7da24bec59e48039bf37daf8f988cbb2acde45ceec")
    print("✅ CSRF Secret: f900e6e287d1da3c644b7121e9b68fb6035e7a9f829b8ce2e6fb")
    print("✅ PYTHONPATH: apps:packages:.")

    print("\n🌐 Service URLs:")
    print("=" * 60)
    print("API: https://sorce-api.onrender.com")
    print("Web: https://sorce-web.onrender.com")
    print("Health: https://sorce-api.onrender.com/health")
    print("Docs: https://sorce-api.onrender.com/docs")

def create_log_summary():
    """Create a log summary template"""
    summary = """# JobHuntin API Log Analysis

## Service Information
- **Service**: jobhuntin-api
- **Service ID**: srv-d6p4l03h46gs73ftvuj0
- **Type**: web_service (Docker)
- **URL**: https://sorce-api.onrender.com
- **Dashboard**: https://dashboard.render.com/web/srv-d6p4l03h46gs73ftvuj0

## Configuration
- **API Key**: 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
- **JWT Secret**: 5ac9f551548b8c8eb2f45db7da24bec59e48039bf37daf8f988cbb2acde45ceec
- **CSRF Secret**: f900e6e287d1da3c644b7121e9b68fb6035e7a9f829b8ce2e6fb
- **PYTHONPATH**: apps:packages:.

## Recent Deployment
- **Commit**: 08965d9 - "Add API key configuration and Render log pulling tools"
- **Push Time**: Just now
- **Expected**: Automatic deployment should trigger

## Log Analysis Checklist
- [ ] Build logs show successful pip install
- [ ] No import/module errors
- [ ] Database connection successful
- [ ] Environment variables loaded correctly
- [ ] Service starts without crashing
- [ ] Health check passes

## Common Issues to Check
1. **Import Errors**: ModuleNotFoundError, ImportError
2. **Environment Issues**: Missing LLM_API_KEY, JWT_SECRET, CSRF_SECRET
3. **Database Issues**: Connection failures, wrong DATABASE_URL
4. **Port Issues**: Port binding problems
5. **Resource Issues**: Memory/CPU limits exceeded

## Next Steps
1. Check dashboard logs for specific errors
2. Verify environment variables in Render dashboard
3. Test API health endpoint
4. Monitor deployment progress
"""

    summary_file = Path("LOG_ANALYSIS_TEMPLATE.md")
    summary_file.write_text(summary)
    print(f"📝 Log analysis template created: {summary_file}")

if __name__ == "__main__":
    open_dashboard_logs()
    create_log_summary()
