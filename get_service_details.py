#!/usr/bin/env python3
"""Get detailed service information and check for actual issues."""

import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('RENDER_API_TOKEN')
headers = {'Authorization': f'Bearer {token}'}

def get_service_details(service_id):
    """Get detailed service information."""
    try:
        response = requests.get(f'https://api.render.com/v1/services/{service_id}', headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"  ⚠️  Could not get service details: {response.status_code}")
            return {}
    except Exception as e:
        print(f"  ⚠️  Error getting service details: {e}")
        return {}

def get_service_health(service_id):
    """Check service health."""
    try:
        response = requests.get(f'https://api.render.com/v1/services/{service_id}/health', headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"  ⚠️  Health check failed: {response.status_code}")
            return {}
    except Exception as e:
        print(f"  ⚠️  Error checking health: {e}")
        return {}

def get_service_metrics(service_id):
    """Get service metrics."""
    try:
        response = requests.get(f'https://api.render.com/v1/services/{service_id}/metrics', headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"  ⚠️  Could not get metrics: {response.status_code}")
            return {}
    except Exception as e:
        print(f"  ⚠️  Error getting metrics: {e}")
        return {}

def main():
    print("🔍 Getting detailed service information...")
    
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
    
    # Check each service in detail
    for service in services:
        service_name = service.get('name', 'unknown')
        service_id = service.get('id')
        service_type = service.get('type', 'unknown')
        status = service.get('status', 'unknown')
        
        print(f"\n{'='*60}")
        print(f"📋 Service: {service_name}")
        print(f"   Type: {service_type}")
        print(f"   Status: {status}")
        print(f"   ID: {service_id}")
        print(f"   Owner: {service.get('ownerId', 'unknown')}")
        print(f"   Created: {service.get('createdAt', 'unknown')}")
        print(f"   Updated: {service.get('updatedAt', 'unknown')}")
        
        # Check service details
        print(f"\n🔍 Getting detailed information...")
        details = get_service_details(service_id)
        
        if details:
            print(f"   📊 Service details available")
            
            # Look for service-specific info
            if 'serviceDetails' in details:
                service_details = details['serviceDetails']
                print(f"   📋 Environment: {service_details.get('env', 'unknown')}")
                print(f"   📋 Plan: {service_details.get('plan', 'unknown')}")
                print(f"   📋 Runtime: {service_details.get('runtime', 'unknown')}")
                print(f"   📋 Region: {service_details.get('region', 'unknown')}")
                
                # Check for build settings
                build_command = service_details.get('buildCommand', '')
                start_command = service_details.get('startCommand', '')
                
                if build_command:
                    print(f"   🔨 Build command: {build_command}")
                if start_command:
                    print(f"   🚀 Start command: {start_command}")
                
                # Check for environment variables
                env_vars = service_details.get('env', [])
                if env_vars:
                    print(f"   🔧 Environment variables: {len(env_vars)}")
                    for var in env_vars[:5]:  # First 5 env vars
                        key = var.get('key', 'unknown')
                        value = var.get('value', 'unknown')
                        print(f"      {key}: {value[:50]}{'...' if len(value) > 50 else ''}")
        
        # Check health
        print(f"\n❤️  Checking health...")
        health = get_service_health(service_id)
        
        if health:
            print(f"   ✅ Health check passed")
            if 'status' in health:
                print(f"   📊 Health status: {health['status']}")
            if 'checks' in health:
                for check in health['checks']:
                    check_name = check.get('name', 'unknown')
                    check_status = check.get('status', 'unknown')
                    print(f"      {check_name}: {check_status}")
        else:
            print(f"   ⚠️  Health check failed or not available")
        
        # Check metrics
        print(f"\n📈 Getting metrics...")
        metrics = get_service_metrics(service_id)
        
        if metrics:
            print(f"   📊 Metrics available")
            
            # Look for common metrics
            if 'cpu' in metrics:
                cpu = metrics['cpu']
                print(f"      CPU: {cpu}")
            if 'memory' in metrics:
                memory = metrics['memory']
                print(f"      Memory: {memory}")
            if 'activeConnections' in metrics:
                connections = metrics['activeConnections']
                print(f"      Active connections: {connections}")
            if 'httpRequests' in metrics:
                requests = metrics['httpRequests']
                print(f"      HTTP requests: {requests}")
        else:
            print(f"   ⚠️  Metrics not available")
        
        # Check for suspension info
        suspended = service.get('suspended', False)
        if suspended:
            print(f"\n🚨 SERVICE SUSPENDED!")
            suspenders = service.get('suspenders', [])
            if suspenders:
                print(f"   Suspended by: {suspenders}")
        
        # Check for recent activity
        print(f"\n🔍 Checking recent activity...")
        
        # Get recent events
        events_response = requests.get(f'https://api.render.com/v1/services/{service_id}/events', headers=headers)
        if events_response.status_code == 200:
            events = events_response.json()
            
            if events:
                print(f"   📅 Found {len(events)} recent events")
                
                # Look for problematic events
                recent_events = events[-5:]  # Last 5 events
                
                for event in recent_events:
                    event_type = event.get('type', 'unknown')
                    timestamp = event.get('timestamp', 'unknown')
                    details = event.get('details', {})
                    
                    if any(keyword in event_type.lower() for keyword in ['failed', 'error', 'suspended', 'crashed']):
                        print(f"      🚨 {event_type}: {timestamp}")
                        if isinstance(details, dict):
                            for key, value in details.items():
                                print(f"         {key}: {value}")
                        else:
                            print(f"         Details: {str(details)[:100]}...")
                    else:
                        print(f"      📝 {event_type}: {timestamp}")
            else:
                print(f"   📅 No recent events")
        else:
            print(f"   ⚠️  Could not get events: {events_response.status_code}")

if __name__ == "__main__":
    main()
