#!/usr/bin/env python3
"""Final deployment status check for all Render services."""

import json
import subprocess
import urllib.request
import urllib.error
import ssl
import time

def check_endpoint(url, timeout=10):
    """Check if an endpoint is responding."""
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Jobhuntin-Status-Check/1.0'})
        start = time.time()
        response = urllib.request.urlopen(req, timeout=timeout, context=ctx)
        elapsed = time.time() - start
        
        return {
            'url': url,
            'status': 'UP',
            'status_code': response.getcode(),
            'response_time_ms': int(elapsed * 1000),
            'content_type': response.headers.get('Content-Type', 'unknown')
        }
    except urllib.error.HTTPError as e:
        return {
            'url': url,
            'status': 'HTTP_ERROR',
            'status_code': e.code,
            'error': str(e.reason)
        }
    except urllib.error.URLError as e:
        return {
            'url': url,
            'status': 'DOWN',
            'error': str(e.reason)
        }
    except Exception as e:
        return {
            'url': url,
            'status': 'ERROR',
            'error': str(e)
        }

def get_render_services():
    """Get list of Render services via API."""
    try:
        result = subprocess.run(
            ['render', 'service', 'list', '--owner-id', 'acecondo', '--format', 'json'],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception as e:
        print(f"Error getting Render services: {e}")
    return []

def main():
    print("=" * 60)
    print("FINAL DEPLOYMENT STATUS REPORT")
    print("=" * 60)
    print()
    
    # Test endpoints
    endpoints = [
        ("API Health", "https://jobhuntin-api.onrender.com/health"),
        ("API Root", "https://jobhuntin-api.onrender.com/"),
        ("Web App", "https://jobhuntin-web.onrender.com"),
    ]
    
    print("ENDPOINT TESTS:")
    print("-" * 60)
    
    results = []
    for name, url in endpoints:
        print(f"\nTesting: {name}")
        print(f"  URL: {url}")
        result = check_endpoint(url)
        results.append((name, result))
        
        if result['status'] == 'UP':
            print(f"  Status: OK - UP (HTTP {result.get('status_code', 'N/A')})")
            print(f"  Response Time: {result.get('response_time_ms', 'N/A')}ms")
        elif result['status'] == 'HTTP_ERROR':
            print(f"  Status: WARN - HTTP {result.get('status_code', 'N/A')}")
            print(f"  Error: {result.get('error', 'N/A')}")
        else:
            print(f"  Status: FAIL - DOWN")
            print(f"  Error: {result.get('error', 'Unknown')}")
    
    # Get Render services
    print("\n\nRENDER SERVICES:")
    print("-" * 60)
    
    services = get_render_services()
    if services:
        for svc in services:
            name = svc.get('name', 'unknown')
            service_type = svc.get('type', 'unknown')
            status = svc.get('status', 'unknown')
            print(f"  • {name} ({service_type}): {status}")
    else:
        print("  Could not retrieve Render services list")
    
    # Summary
    print("\n\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    up_count = sum(1 for _, r in results if r['status'] == 'UP')
    total_count = len(results)
    
    print(f"Endpoints Responding: {up_count}/{total_count}")
    
    if up_count == total_count:
        print("\n** ALL SERVICES DEPLOYED SUCCESSFULLY! **")
    elif up_count > 0:
        print("\n-- PARTIAL DEPLOYMENT - Some services need attention --")
    else:
        print("\n-- ALL SERVICES DOWN - Check deployment --")
    
    print()

if __name__ == '__main__':
    main()
