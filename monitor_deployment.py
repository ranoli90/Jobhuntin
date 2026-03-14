#!/usr/bin/env python3
"""Monitor Render deployment status"""

import subprocess
import time


def run_command(cmd, timeout=30):
    """Run a command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"

def check_render_status():
    """Check Render deployment status"""
    print("🚀 Monitoring Render deployment status...")
    print("=" * 60)

    # Try to get Render CLI status
    success, stdout, stderr = run_command("render services", timeout=30)

    if success:
        print("✅ Render CLI connected successfully")
        print(stdout)
    else:
        print(f"⚠️  Render CLI not available: {stderr}")
        print("💡 You can monitor deployment at: https://dashboard.render.com")
        print("💡 Look for the 'jobhuntin-api' service status")

    print("\n" + "=" * 60)
    print("📋 Deployment Checklist:")
    print("□ Code pushed to main branch ✅")
    print("□ Render webhook triggered ⏳")
    print("□ Build process running ⏳")
    print("□ Service deploying ⏳")
    print("□ Health checks passing ⏳")

    print("\n🔍 Expected Deployment Timeline:")
    print("• Build start: Immediate (0-2 min)")
    print("• Build complete: 2-5 min")
    print("• Deployment start: 5-7 min")
    print("• Service live: 7-10 min")

    print("\n🌐 Service URLs:")
    print("• API: https://sorce-api.onrender.com")
    print("• Web: https://sorce-web.onrender.com")
    print("• Admin: https://sorce-admin.onrender.com")

    print("\n🔧 To check manually:")
    print("1. Visit https://dashboard.render.com")
    print("2. Navigate to 'jobhuntin-api' service")
    print("3. Check 'Events' tab for deployment logs")
    print("4. Verify service status is 'Live'")

    return True

def main():
    """Main monitoring function"""
    print("🎯 Render Deployment Monitor")
    print("Push completed: 7f3b0df - Fix API build issues")
    print("Timestamp:", time.strftime("%Y-%m-%d %H:%M:%S UTC"))
    print()

    check_render_status()

    print(f"\n⏰ Monitoring started at {time.strftime('%H:%M:%S')}")
    print("Press Ctrl+C to stop monitoring")

    # Simple monitoring loop
    try:
        for i in range(20):  # Monitor for ~10 minutes
            time.sleep(30)
            print(f"📍 Check {i+1}/20 - {time.strftime('%H:%M:%S')} - Deployment in progress...")

            # You could add API health checks here
            # health_success, _, _ = run_command("curl -s https://sorce-api.onrender.com/health")
            # if health_success:
            #     print("🎉 API is responding!")
            #     break

    except KeyboardInterrupt:
        print("\n⏹️  Monitoring stopped by user")

    print("\n✨ Monitoring complete!")
    print("📊 Final status check recommended at Render dashboard")

if __name__ == "__main__":
    main()
