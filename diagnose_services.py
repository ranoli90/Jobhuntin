#!/usr/bin/env python3
"""Diagnose actual service issues using correct API calls."""

import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('RENDER_API_TOKEN')
headers = {'Authorization': f'Bearer {token}'}

def main():
    print("🔍 Diagnosing service issues...")
    
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
    
    # Check each service for actual issues
    issues_found = []
    
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
        
        # Check for actual problems
        service_issues = []
        
        if suspended:
            service_issues.append("SUSPENDED")
            issues_found.append(f"{service_name}: SUSPENDED")
        
        if status in ['failed', 'error', 'crashed']:
            service_issues.append(f"STATUS: {status}")
            issues_found.append(f"{service_name}: Status is {status}")
        
        if status == 'unknown':
            service_issues.append("STATUS_UNKNOWN")
            issues_found.append(f"{service_name}: Status unknown")
        
        # Get recent deploys to check for build failures
        try:
            deploys_response = requests.get(f'https://api.render.com/v1/services/{service_id}/deploys', headers=headers)
            if deploys_response.status_code == 200:
                deploys = deploys_response.json()
                
                if deploys:
                    # Check last few deploys for failures
                    recent_deploys = deploys[:5]  # Last 5 deploys
                    failed_deploys = [d for d in recent_deploys if d.get('status') in ['failed', 'build_failed', 'deploy_failed']]
                    
                    if failed_deploys:
                        service_issues.append(f"RECENT_DEPLOY_FAILURES: {len(failed_deploys)}")
                        issues_found.append(f"{service_name}: {len(failed_deploys)} recent deploy failures")
                        
                        print(f"   🔴 Recent deploy failures: {len(failed_deploys)}")
                        for deploy in failed_deploys[:2]:  # Show last 2 failed deploys
                            deploy_id = deploy.get('id', 'unknown')
                            deploy_status = deploy.get('status', 'unknown')
                            created_at = deploy.get('createdAt', 'unknown')
                            
                            print(f"      🚨 Deploy {deploy_id}: {deploy_status}")
                            print(f"         Created: {created_at}")
                            
                            # Try to get deploy logs
                            try:
                                logs_response = requests.get(
                                    f'https://api.render.com/v1/services/{service_id}/deploys/{deploy_id}/logs',
                                    headers=headers
                                )
                                
                                if logs_response.status_code == 200:
                                    logs = logs_response.json()
                                    print(f"         📋 Deploy logs: {len(logs)} entries")
                                    
                                    # Look for error patterns
                                    for log in logs[-3:]:  # Last 3 entries
                                        if isinstance(log, str):
                                            log_str = log.lower()
                                        else:
                                            log_str = str(log).lower()
                                        
                                        if any(keyword in log_str for keyword in [
                                            'error', 'exception', 'failed', 'traceback', 'module not found',
                                            'import error', 'syntax error', 'permission denied',
                                            'connection refused', 'timeout', 'killed', 'exited'
                                        ]):
                                            print(f"            🔴 ERROR: {log[:80]}...")
                            except Exception as e:
                                print(f"         ⚠️  Could not get deploy logs: {e}")
                    else:
                        print(f"   ✅ Recent deploys successful")
                else:
                    print(f"   ⚠️  No deploy history found")
            else:
                print(f"   ⚠️  Could not get deploys: {deploys_response.status_code}")
        
        except Exception as e:
            print(f"   ⚠️  Error checking deploys: {e}")
        
        # Try to access service directly if it's a web service
        if service_type == 'web_service':
            dashboard_url = service.get('dashboardUrl', '')
            if dashboard_url:
                try:
                    service_response = requests.get(dashboard_url, timeout=10)
                    if service_response.status_code == 200:
                        print(f"   ✅ Service is accessible")
                    else:
                        service_issues.append(f"HTTP_{service_response.status_code}")
                        issues_found.append(f"{service_name}: HTTP {service_response.status_code}")
                        print(f"   🔴 Service returned HTTP {service_response.status_code}")
                except Exception as e:
                    service_issues.append(f"INACCESSIBLE: {str(e)[:50]}")
                    issues_found.append(f"{service_name}: Inaccessible")
                    print(f"   🔴 Service not accessible: {e}")
        
        elif service_type == 'static_site':
            dashboard_url = service.get('dashboardUrl', '')
            if dashboard_url:
                try:
                    site_response = requests.get(dashboard_url, timeout=10)
                    if site_response.status_code == 200:
                        print(f"   ✅ Site is accessible")
                    else:
                        service_issues.append(f"HTTP_{site_response.status_code}")
                        issues_found.append(f"{service_name}: HTTP {site_response.status_code}")
                        print(f"   🔴 Site returned HTTP {site_response.status_code}")
                except Exception as e:
                    service_issues.append(f"INACCESSIBLE: {str(e)[:50]}")
                    issues_found.append(f"{service_name}: Inaccessible")
                    print(f"   🔴 Site not accessible: {e}")
        
        # Check environment variables for missing critical configs
        service_details = service.get('serviceDetails', {})
        if service_details:
            env_vars = service_details.get('env', [])
            if isinstance(env_vars, list):
                env_keys = [var.get('key', '') if isinstance(var, dict) else '' for var in env_vars]
                
                # Check for critical environment variables based on service type
                if service_type == 'web_service':
                    critical_vars = ['DATABASE_URL', 'LLM_API_KEY', 'RENDER_API_TOKEN']
                elif service_type == 'background_worker':
                    critical_vars = ['DATABASE_URL', 'RENDER_API_TOKEN']
                else:
                    critical_vars = []
                
                missing_vars = [var for var in critical_vars if var not in env_keys]
                if missing_vars:
                    service_issues.append(f"MISSING_ENV: {missing_vars}")
                    issues_found.append(f"{service_name}: Missing {missing_vars}")
                    print(f"   🔴 Missing environment variables: {missing_vars}")
        
        # Summary for this service
        if service_issues:
            print(f"   🔴 ISSUES FOUND: {', '.join(service_issues)}")
        else:
            print(f"   ✅ No issues detected")
    
    # Overall summary
    print(f"\n{'='*60}")
    print(f"📊 OVERALL SUMMARY")
    print(f"{'='*60}")
    
    if issues_found:
        print(f"🔴 SERVICES WITH ISSUES: {len(issues_found)}")
        for issue in issues_found:
            print(f"   • {issue}")
    else:
        print(f"✅ ALL SERVICES HEALTHY")
    
    print(f"\n📋 SERVICES BREAKDOWN:")
    service_types = {}
    for service in services:
        stype = service.get('type', 'unknown')
        service_types[stype] = service_types.get(stype, 0) + 1
    
    for stype, count in service_types.items():
        print(f"   {stype}: {count}")

if __name__ == "__main__":
    main()
