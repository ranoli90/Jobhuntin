#!/usr/bin/env python3
"""Unsuspend all background worker services."""

import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('RENDER_API_TOKEN')
headers = {'Authorization': f'Bearer {token}'}

def unsuspend_service(service_id, service_name):
    """Unsuspend a service."""
    try:
        response = requests.patch(
            f'https://api.render.com/v1/services/{service_id}',
            headers=headers,
            json={'suspended': False}
        )
        
        if response.status_code == 200:
            print(f"   ✅ Successfully unsuspended {service_name}")
            return True
        else:
            print(f"   ❌ Failed to unsuspend {service_name}: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
    except Exception as e:
        print(f"   ❌ Error unsuspending {service_name}: {e}")
        return False

def main():
    print("🔧 Unsuspending all background worker services...")
    
    # Get all services
    response = requests.get('https://api.render.com/v1/services', headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Error getting services: {response.status_code}")
        return
    
    services_data = response.json()
    services = []
    
    # Extract services from nested structure
    for item in services_data:
        if isinstance(item, dict) and 'service' in item:
            services.append(item['service'])
    
    print(f"📊 Found {len(services)} services")
    
    # Find suspended background workers
    suspended_workers = []
    for service in services:
        if (service.get('suspended', False) and 
            service.get('type') == 'background_worker'):
            suspended_workers.append(service)
    
    print(f"\n🚨 SUSPENDED BACKGROUND WORKERS: {len(suspended_workers)}")
    
    if not suspended_workers:
        print("✅ No suspended background workers found!")
        return
    
    # Unsuspend each worker
    success_count = 0
    for service in suspended_workers:
        service_name = service.get('name', 'unknown')
        service_id = service.get('id')
        
        print(f"\n📋 Processing: {service_name}")
        print(f"   ID: {service_id}")
        
        if unsuspend_service(service_id, service_name):
            success_count += 1
        
        # Small delay to avoid rate limiting
        time.sleep(1)
    
    # Verify results
    print(f"\n{'='*60}")
    print(f"📊 RESULTS")
    print(f"{'='*60}")
    print(f"   Workers to unsuspend: {len(suspended_workers)}")
    print(f"   Successfully unsuspended: {success_count}")
    print(f"   Failed: {len(suspended_workers) - success_count}")
    
    # Final verification
    print(f"\n🔍 Verifying unsuspension...")
    time.sleep(3)  # Wait for changes to propagate
    
    verify_response = requests.get('https://api.render.com/v1/services', headers=headers)
    if verify_response.status_code == 200:
        verify_data = verify_response.json()
        still_suspended = []
        
        for item in verify_data:
            if isinstance(item, dict) and 'service' in item:
                service = item['service']
                if (service.get('suspended', False) and 
                    service.get('type') == 'background_worker'):
                    still_suspended.append(service.get('name', 'unknown'))
        
        if still_suspended:
            print(f"   ⚠️  Still suspended: {still_suspended}")
        else:
            print(f"   ✅ All background workers are now active!")
    
    print(f"\n📋 NEXT STEPS:")
    print(f"   1. Monitor worker startup logs")
    print(f"   2. Check if workers are processing tasks")
    print(f"   3. Verify API endpoints are working")
    print(f"   4. Test auto-apply functionality")
    print(f"   5. Check job queue processing")

if __name__ == "__main__":
    main()
