#!/usr/bin/env python3
"""Get logs for all 7 services using correct API endpoints."""

import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('RENDER_API_TOKEN')
headers = {'Authorization': f'Bearer {token}'}

def get_service_deploys(service_id):
    """Get recent deploys for a service."""
    try:
        response = requests.get(f'https://api.render.com/v1/services/{service_id}/deploys', headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"  ⚠️  Could not get deploys: {response.status_code}")
            return []
    except Exception as e:
        print(f"  ⚠️  Error getting deploys: {e}")
        return []

def get_service_events(service_id):
    """Get events for a service."""
    try:
        response = requests.get(f'https://api.render.com/v1/services/{service_id}/events', headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"  ⚠️  Could not get events: {response.status_code}")
            return []
    except Exception as e:
        print(f"  ⚠️  Error getting events: {e}")
        return []

def get_audit_logs():
    """Get audit logs for all services."""
    try:
        response = requests.get('https://api.render.com/v1/owners/tea-d6p1rv6a2pns73f4sucg/audit-logs', headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"  ⚠️  Could not get audit logs: {response.status_code}")
            return []
    except Exception as e:
        print(f"  ⚠️  Error getting audit logs: {e}")
        return []

def main():
    print("🔍 Getting logs for all 7 services...")
    
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
    
    # Get audit logs first
    print("\n🔍 Getting audit logs...")
    audit_logs = get_audit_logs()
    
    if audit_logs:
        print(f"✅ Found {len(audit_logs)} audit logs")
        
        # Look for service-specific errors
        for service in services:
            service_name = service.get('name', 'unknown')
            service_id = service.get('id')
            
            print(f"\n📋 Checking audit logs for {service_name}...")
            
            service_errors = []
            for log in audit_logs:
                message = str(log.get('message', '')).lower()
                timestamp = log.get('timestamp', '')
                
                # Check if this log mentions this service
                if service_id in message or service_name.lower() in message:
                    if any(keyword in message for keyword in [
                        'error', 'exception', 'failed', 'traceback', '500', 'crash',
                        'timeout', 'exit', 'panic', 'database', 'migration',
                        'deploy', 'build', 'import', 'module', 'dependency',
                        'connection', 'startup', 'shutdown', 'suspended'
                    ]):
                        service_errors.append({
                            'timestamp': timestamp,
                            'message': log.get('message', ''),
                            'level': log.get('level', 'unknown')
                        })
            
            if service_errors:
                print(f"  🔴 Found {len(service_errors)} errors:")
                for i, error in enumerate(service_errors[-5:], 1):  # Last 5 errors
                    print(f"    {i}. {error['timestamp']}")
                    print(f"       {error['message'][:150]}...")
            else:
                print(f"  ✅ No errors found in audit logs")
    
    # Now check each service individually
    print(f"\n🔍 Checking individual service status...")
    
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
        print(f"   🚀 Getting recent deploys...")
        deploys = get_service_deploys(service_id)
        
        if deploys:
            print(f"   📊 Found {len(deploys)} recent deploys")
            
            # Check for failed deploys
            failed_deploys = [d for d in deploys if d.get('status') in ['failed', 'build_failed', 'deploy_failed']]
            
            if failed_deploys:
                print(f"   🔴 Found {len(failed_deploys)} failed deploys:")
                
                for deploy in failed_deploys[:3]:  # Last 3 failed deploys
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
                            
                            # Show error messages
                            for log in logs[-3:]:  # Last 3 log entries
                                if isinstance(log, dict):
                                    message = log.get('message', str(log))
                                    if any(keyword in message.lower() for keyword in ['error', 'failed', 'exception', 'traceback']):
                                        print(f"            🔴 {message[:100]}...")
                                else:
                                    print(f"            📝 {str(log)[:100]}...")
                        else:
                            print(f"         ⚠️  Could not get deploy logs: {logs_response.status_code}")
                    except Exception as e:
                        print(f"         ⚠️  Error getting deploy logs: {e}")
            else:
                print(f"   ✅ All recent deploys successful")
        else:
            print(f"   ⚠️  Could not get deploy information")
        
        # Get service events
        print(f"   📅 Getting service events...")
        events = get_service_events(service_id)
        
        if events:
            print(f"   📊 Found {len(events)} events")
            
            # Look for error events
            error_events = [e for e in events if e.get('type') in ['build.failed', 'deploy.failed', 'service.suspended']]
            
            if error_events:
                print(f"   🔴 Found {len(error_events)} error events:")
                for event in error_events[-3:]:  # Last 3 error events
                    event_type = event.get('type', 'unknown')
                    timestamp = event.get('timestamp', 'unknown')
                    details = event.get('details', {})
                    
                    print(f"      🚨 Event {event_type}: {timestamp}")
                    if isinstance(details, dict):
                        for key, value in details.items():
                            print(f"         {key}: {value}")
                    else:
                        print(f"         Details: {str(details)[:100]}...")
            else:
                print(f"   ✅ No error events found")
        else:
            print(f"   ⚠️  Could not get events")

if __name__ == "__main__":
    main()
