#!/usr/bin/env python3
"""Get service errors using audit logs and deploys endpoints."""

import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('RENDER_API_KEY')
headers = {'Authorization': f'Bearer {token}'}

def main():
    print("🔍 Getting service errors and failures...")
    
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
    
    # Get audit logs for errors
    print("\n🔍 Getting audit logs...")
    audit_response = requests.get(
        'https://api.render.com/v1/owners/tea-d63jqusr85hc73b9bun0/audit-logs',
        headers=headers
    )
    
    if audit_response.status_code == 200:
        audit_logs = audit_response.json()
        print(f"✅ Found {len(audit_logs)} audit logs")
        
        # Look for error patterns
        error_logs = []
        for log in audit_logs:
            message = str(log.get('message', '')).lower()
            timestamp = log.get('timestamp', '')
            
            if any(keyword in message for keyword in [
                'error', 'exception', 'failed', 'traceback', '500', 'crash',
                'timeout', 'exit', 'panic', 'database', 'migration',
                'deploy', 'build', 'import', 'module', 'dependency',
                'connection', 'startup', 'shutdown', 'suspended'
            ]):
                error_logs.append({
                    'timestamp': timestamp,
                    'message': log.get('message', ''),
                    'level': log.get('level', 'unknown')
                })
        
        print(f"\n🔴 ERROR LOGS FOUND: {len(error_logs)}")
        for i, error in enumerate(error_logs[-10:], 1):  # Last 10 errors
            print(f"  {i}. {error['timestamp']}")
            print(f"     {error['message'][:200]}...")
            print()
    
    # Check each service for deploys and status
    print("\n🔍 Checking service deploys...")
    
    for service in services:
        service_name = service.get('name', 'unknown')
        service_id = service.get('id')
        service_type = service.get('type', 'unknown')
        status = service.get('status', 'unknown')
        
        print(f"\n📋 Service: {service_name}")
        print(f"   Type: {service_type}")
        print(f"   Status: {status}")
        print(f"   ID: {service_id}")
        
        # Get recent deploys
        deploys_response = requests.get(
            f'https://api.render.com/v1/services/{service_id}/deploys',
            headers=headers
        )
        
        if deploys_response.status_code == 200:
            deploys = deploys_response.json()
            
            if isinstance(deploys, list):
                print(f"   📊 Recent deploys: {len(deploys)}")
                
                for deploy in deploys[:3]:  # Last 3 deploys
                    deploy_status = deploy.get('status', 'unknown')
                    deploy_created = deploy.get('createdAt', 'unknown')
                    deploy_id = deploy.get('id', 'unknown')
                    
                    print(f"      🚀 Deploy {deploy_id}: {deploy_status}")
                    print(f"         Created: {deploy_created}")
                    
                    # Get deploy logs if failed
                    if deploy_status in ['failed', 'build_failed', 'deploy_failed']:
                        print(f"         ❌ FAILED DEPLOY - Getting logs...")
                        
                        # Try to get deploy logs
                        logs_response = requests.get(
                            f'https://api.render.com/v1/services/{service_id}/deploys/{deploy_id}/logs',
                            headers=headers
                        )
                        
                        if logs_response.status_code == 200:
                            logs = logs_response.json()
                            print(f"         📋 Deploy logs: {len(logs)} entries")
                            
                            for log in logs[-5:]:  # Last 5 log entries
                                print(f"            {log}")
                        else:
                            print(f"         ⚠️  Could not get deploy logs: {logs_response.status_code}")
                    
                    print()
            else:
                print(f"   📊 Deploys: Unexpected format")
        else:
            print(f"   ⚠️  Could not get deploys: {deploys_response.status_code}")

if __name__ == "__main__":
    main()
