#!/usr/bin/env python3
"""
Deployment Status and Fix Tool
Monitors deployment and provides automated fixes.
"""

import subprocess
import time
import json
from pathlib import Path

def check_deployment_status():
    """Check deployment status from multiple sources"""
    print("🔍 Checking Deployment Status...")
    print("=" * 60)
    
    # Check API health
    print("1. API Health Check...")
    try:
        result = subprocess.run([
            'curl', '-s', '-o', '/dev/null', 
            '-w', '%{http_code}',
            'https://sorce-api.onrender.com/health'
        ], capture_output=True, text=True, timeout=10)
        
        status_code = result.stdout.strip()
        if status_code == '200':
            print("✅ API is responding (200 OK)")
        else:
            print(f"❌ API not responding (HTTP {status_code})")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    # Check web frontend
    print("\n2. Web Frontend Check...")
    try:
        result = subprocess.run([
            'curl', '-s', '-o', '/dev/null',
            '-w', '%{http_code}',
            'https://sorce-web.onrender.com'
        ], capture_output=True, text=True, timeout=10)
        
        status_code = result.stdout.strip()
        if status_code == '200':
            print("✅ Web frontend is responding (200 OK)")
        else:
            print(f"❌ Web frontend not responding (HTTP {status_code})")
    except Exception as e:
        print(f"❌ Web check failed: {e}")
    
    # Check admin dashboard
    print("\n3. Admin Dashboard Check...")
    try:
        result = subprocess.run([
            'curl', '-s', '-o', '/dev/null',
            '-w', '%{http_code}',
            'https://sorce-admin.onrender.com'
        ], capture_output=True, text=True, timeout=10)
        
        status_code = result.stdout.strip()
        if status_code == '200':
            print("✅ Admin dashboard is responding (200 OK)")
        else:
            print(f"❌ Admin dashboard not responding (HTTP {status_code})")
    except Exception as e:
        print(f"❌ Admin check failed: {e}")

def check_git_status():
    """Check git status"""
    print("\n📋 Git Status...")
    print("=" * 60)
    
    try:
        result = subprocess.run([
            'git', 'status', '--porcelain=2'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            if result.stdout.strip():
                print("✅ Working directory is clean")
            else:
                print("⚠️  Uncommitted changes:")
                print(result.stdout)
        else:
            print("❌ Git status check failed")
    except Exception as e:
        print(f"❌ Git check failed: {e}")

def check_recent_commits():
    """Check recent commits"""
    print("\n📝 Recent Commits...")
    print("=" * 60)
    
    try:
        result = subprocess.run([
            'git', 'log', '--oneline', '-5'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("Recent commits:")
            for line in result.stdout.strip().split('\n'):
                print(f"  {line}")
        else:
            print("❌ Git log check failed")
    except Exception as e:
        print(f"❌ Git log check failed: {e}")

def create_deployment_script():
    """Create deployment script"""
    print("\n🚀 Creating Deployment Script...")
    
    deployment_script = '''#!/bin/bash
# Deployment Script for JobHuntin
# Run this to trigger and monitor deployment

echo "🚀 Starting JobHuntin Deployment..."
echo "=================================="

# Push changes
echo "📤 Pushing changes..."
git push origin main

if [ $? -eq 0 ]; then
    echo "✅ Changes pushed successfully"
else
    echo "❌ Push failed"
    exit 1
fi

# Monitor deployment
echo "⏱️  Monitoring deployment..."
echo "=================================="

for i in {1..20}; do
    echo "Check $i: $(date)"
    
    # Check API
    API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://sorce-api.onrender.com/health)
    
    # Check Web
    WEB_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://sorce-web.onrender.com)
    
    # Check Admin
    ADMIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://sorce-admin.onrender.com)
    
    echo "  API: $API_STATUS | Web: $WEB_STATUS | Admin: $ADMIN_STATUS"
    
    if [ "$API_STATUS" = "200" ] && [ "$WEB_STATUS" = "200" ]; then
        echo "🎉 DEPLOYMENT SUCCESSFUL!"
        echo "🌐 API: https://sorce-api.onrender.com"
        echo "🌐 Web: https://sorce-web.onrender.com"
        echo "🌐 Admin: https://sorce-admin.onrender.com"
        break
    fi
    
    sleep 30
done

echo "📊 Final Status Check..."
echo "=================================="
echo "API: $(curl -s -o /dev/null -w "%{http_code}" https://sorce-api.onrender.com/health)"
echo "Web: $(curl -s -o /dev/null -w "%{http_code}" https://sorce-web.onrender.com)"
echo "Admin: $(curl -s -o /dev/null -w "%{http_code}" https://sorce-admin.onrender.com)"
'''
    
    script_file = Path("deploy_and_monitor.sh")
    script_file.write_text(deployment_script)
    script_file.chmod(0o755)
    
    print(f"✅ Deployment script created: {script_file}")
    print("🚀 Run with: ./deploy_and_monitor.sh")

def create_troubleshooting_guide():
    """Create troubleshooting guide"""
    print("\n📚 Creating Troubleshooting Guide...")
    
    guide = '''# JobHuntin Deployment Troubleshooting Guide

## Quick Status Check
```bash
# Check all services
curl -s -o /dev/null -w "API: %{http_code}" https://sorce-api.onrender.com/health
curl -s -o /dev/null -w "Web: %{http_code}" https://sorce-web.onrender.com
curl -s -o /dev/null -w "Admin: %{http_code}" https://sorce-admin.onrender.com
```

## Common Issues and Fixes

### 1. Import Errors
**Problem**: ModuleNotFoundError
**Fix**: Check PYTHONPATH in render.yaml
```bash
# Should be:
PYTHONPATH=apps:packages:.

# NOT in startCommand (only in envVars)
```

### 2. Build Failures
**Problem**: pip install fails
**Fix**: Check requirements.txt
```bash
# Test locally
pip install -r requirements.txt

# Check for conflicts
pip check
```

### 3. Runtime Errors
**Problem**: Service starts but crashes
**Fix**: Check logs in Render dashboard
- Go to Render dashboard
- Click on jobhuntin-api service
- Check "Events" tab
- Look for error messages

### 4. Database Connection Issues
**Problem**: Database connection failed
**Fix**: Check DATABASE_URL
- Verify database is running
- Check connection string format
- Test connection locally

### 5. Environment Variable Issues
**Problem**: Missing environment variables
**Fix**: Check Render dashboard
- Go to service settings
- Verify all required env vars are set
- Check for typos in variable names

## Debug Commands

### Enhanced Debugging
```bash
# IPDB (recommended)
python -m ipdb -c "from api.main import app; import ipdb; ipdb.set_trace()"

# Pudb (visual)
python -m pudb -c "from api.main import app; import pudb; pudb.set_trace()"

# Test imports
python -c "
import sys
sys.path.insert(0, 'apps:packages:.')
from api.main import app
print('SUCCESS: API loads correctly')
"
```

### Monitor Deployment
```bash
# Run automated monitoring
./deploy_and_monitor.sh

# Manual monitoring
watch -n 10 'curl -s -o /dev/null -w "%{http_code}" https://sorce-api.onrender.com/health'
```

## Render Dashboard URLs
- Dashboard: https://dashboard.render.com
- API Service: https://dashboard.render.com/services/jobhuntin-api
- Web Service: https://dashboard.render.com/services/jobhuntin-web
- Admin Service: https://dashboard.render.com/services/jobhuntin-admin

## Getting Help
1. Check this guide for common issues
2. Use debug commands for detailed testing
3. Monitor logs in Render dashboard
4. Check git status and recent commits
5. Test locally before deploying

## Emergency Fixes
If deployment is completely broken:

1. **Rollback to previous commit**
```bash
git log --oneline -10
git checkout <previous-working-commit>
git push origin main --force
```

2. **Rebuild from scratch**
```bash
# Clean git state
git clean -fd
git reset --hard HEAD

# Re-push fixes
git add .
git commit -m "Emergency fix"
git push origin main
```
'''
    
    guide_file = Path("TROUBLESHOOTING.md")
    guide_file.write_text(guide)
    print(f"✅ Troubleshooting guide created: {guide_file}")

def main():
    """Main function"""
    print("🔍 JobHuntin Deployment Status Tool")
    print("=" * 60)
    
    # Run all checks
    check_deployment_status()
    check_git_status()
    check_recent_commits()
    
    # Create helpful files
    create_deployment_script()
    create_troubleshooting_guide()
    
    print("\n📊 SUMMARY")
    print("=" * 60)
    print("✅ Status check complete")
    print("✅ Deployment script created")
    print("✅ Troubleshooting guide created")
    print("\n💡 NEXT STEPS:")
    print("1. Run: ./deploy_and_monitor.sh")
    print("2. Check: TROUBLESHOOTING.md")
    print("3. Monitor: Render dashboard")
    print("4. Debug: Use debug commands from debug_commands.txt")

if __name__ == "__main__":
    main()
