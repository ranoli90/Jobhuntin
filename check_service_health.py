#!/usr/bin/env python3
"""Check service health and identify real issues."""

import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('RENDER_API_TOKEN')
headers = {'Authorization': f'Bearer {token}'}

def main():
    print("🔍 Checking service health and identifying issues...")
    
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
    
    # Check each service
    for service in services:
        service_name = service.get('name', 'unknown')
        service_id = service.get('id')
        service_type = service.get('type', 'unknown')
        status = service.get('status', 'unknown')
        suspended = service.get('suspended', False)
        
        print(f"\n{'='*60}")
        print(f"📋 Service: {service_name}")
        print(f"   Type: {service_type}")
        print(f"   Status: {status}")
        print(f"   Suspended: {suspended}")
        print(f"   ID: {service_id}")
        
        # Check if service is actually running by trying to access it
        if service_type == 'web_service':
            dashboard_url = service.get('dashboardUrl', '')
            if dashboard_url:
                print(f"   🌐 Dashboard URL: {dashboard_url}")
                
                # Try to access the service
                try:
                    service_response = requests.get(dashboard_url, timeout=10)
                    if service_response.status_code == 200:
                        print(f"   ✅ Service is accessible")
                    else:
                        print(f"   🔴 Service returned status: {service_response.status_code}")
                except Exception as e:
                    print(f"   🔴 Service not accessible: {e}")
        
        elif service_type == 'background_worker':
            print(f"   🔧 Background worker - checking recent activity...")
            
            # Get recent deploys to see if they're actually running
            deploys_response = requests.get(f'https://api.render.com/v1/services/{service_id}/deploys', headers=headers)
            if deploys_response.status_code == 200:
                deploys = deploys_response.json()
                
                if deploys:
                    latest_deploy = deploys[0]  # Most recent
                    deploy_status = latest_deploy.get('status', 'unknown')
                    created_at = latest_deploy.get('createdAt', 'unknown')
                    
                    print(f"   🚀 Latest deploy: {deploy_status}")
                    print(f"      Created: {created_at}")
                    
                    if deploy_status not in ['live', 'succeeded', 'ready']:
                        print(f"   🔴 DEPLOY ISSUE: {deploy_status}")
                        
                        # Get deploy logs
                        deploy_id = latest_deploy.get('id')
                        if deploy_id:
                            logs_response = requests.get(
                                f'https://api.render.com/v1/services/{service_id}/deploys/{deploy_id}/logs',
                                headers=headers
                            )
                            
                            if logs_response.status_code == 200:
                                logs = logs_response.json()
                                print(f"   📋 Deploy logs: {len(logs)} entries")
                                
                                # Look for error patterns
                                for log in logs[-10:]:  # Last 10 entries
                                    if isinstance(log, str):
                                        log_str = log.lower()
                                    else:
                                        log_str = str(log).lower()
                                    
                                    if any(keyword in log_str for keyword in [
                                        'error', 'exception', 'failed', 'traceback', '500',
                                        'module not found', 'import error', 'syntax error',
                                        'permission denied', 'connection refused',
                                        'timeout', 'killed', 'exited', 'crashed'
                                    ]):
                                        print(f"      🔴 ERROR: {log[:100]}...")
                    else:
                        print(f"   ✅ Latest deploy successful")
                else:
                    print(f"   ⚠️  No deploy history found")
        
        elif service_type == 'static_site':
            print(f"   🌐 Static site - checking accessibility...")
            
            dashboard_url = service.get('dashboardUrl', '')
            if dashboard_url:
                print(f"   🌐 Site URL: {dashboard_url}")
                
                try:
                    site_response = requests.get(dashboard_url, timeout=10)
                    if site_response.status_code == 200:
                        print(f"   ✅ Site is accessible")
                    else:
                        print(f"   🔴 Site returned status: {site_response.status_code}")
                except Exception as e:
                    print(f"   🔴 Site not accessible: {e}")
        
        # Check service details for configuration issues
        service_details = service.get('serviceDetails', {})
        if service_details:
            env_vars = service_details.get('env', [])
            if env_vars:
                print(f"   🔧 Environment variables: {len(env_vars)}")
                
                # Look for missing critical environment variables
                env_keys = [var.get('key', '') for var in env_vars]
                critical_vars = ['DATABASE_URL', 'RENDER_API_TOKEN', 'LLM_API_KEY']
                
                missing_vars = [var for var in critical_vars if var not in env_keys]
                if missing_vars:
                    print(f"   🔴 Missing critical variables: {missing_vars}")
                else:
                    print(f"   ✅ Critical variables present")
        
        # Check suspension details
        if suspended:
            print(f"   🚨 SERVICE IS SUSPENDED!")
            suspenders = service.get('suspenders', [])
            if suspenders:
                print(f"   Suspended by: {suspenders}")
        
        print(f"   📊 Summary: {'HEALTHY' if not suspended and status != 'failed' else 'ISSUES DETECTED'}")

if __name__ == "__main__":
    main()
