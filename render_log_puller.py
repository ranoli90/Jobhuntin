#!/usr/bin/env python3
"""
Render API Log Puller
Pulls full logs from Render services using the Render API
"""

import requests
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

class RenderLogPuller:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.render.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def get_services(self):
        """Get all services"""
        response = requests.get(f"{self.base_url}/services", headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to get services: {response.status_code}")
            return None
    
    def get_service_logs(self, service_id, start_time=None, end_time=None, limit=1000):
        """Get logs for a specific service"""
        url = f"{self.base_url}/services/{service_id}/logs"
        
        params = {
            "limit": limit
        }
        
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to get logs: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    
    def get_all_service_logs(self, service_id, hours_back=24):
        """Get all logs for a service in the last N hours"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        
        start_timestamp = int(start_time.timestamp() * 1000)
        end_timestamp = int(end_time.timestamp() * 1000)
        
        all_logs = []
        has_more = True
        current_start = start_timestamp
        current_end = end_timestamp
        
        page = 1
        while has_more and page <= 50:  # Safety limit of 50 pages
            print(f"📄 Fetching log page {page}...")
            
            logs_data = self.get_service_logs(
                service_id, 
                start_time=current_start, 
                end_time=current_end
            )
            
            if not logs_data:
                break
            
            logs = logs_data.get("logs", [])
            all_logs.extend(logs)
            
            has_more = logs_data.get("hasMore", False)
            
            if has_more:
                current_start = logs_data.get("nextStartTime", current_start)
                current_end = logs_data.get("nextEndTime", current_end)
            
            page += 1
            time.sleep(0.1)  # Rate limiting
        
        return all_logs
    
    def find_service_by_name(self, service_name):
        """Find service by name"""
        services = self.get_services()
        if not services:
            return None
        
        for service in services:
            if service.get("name") == service_name:
                return service
        
        return None
    
    def save_logs_to_file(self, logs, filename):
        """Save logs to a file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, default=str)
        print(f"✅ Logs saved to {filename}")
    
    def analyze_logs(self, logs):
        """Analyze logs for common issues"""
        if not logs:
            print("❌ No logs to analyze")
            return
        
        print(f"\n📊 Log Analysis ({len(logs)} entries)")
        print("=" * 60)
        
        # Count log levels
        error_count = 0
        warning_count = 0
        info_count = 0
        
        # Common error patterns
        error_patterns = [
            "ModuleNotFoundError",
            "ImportError", 
            "SyntaxError",
            "ConnectionError",
            "DatabaseError",
            "KeyError",
            "AttributeError",
            "TypeError",
            "ValueError",
            "HTTP 503",
            "HTTP 500",
            "HTTP 404",
            "crash",
            "failed",
            "error"
        ]
        
        recent_errors = []
        
        for log in logs[-50:]:  # Check last 50 logs
            message = log.get("message", "").lower()
            timestamp = log.get("timestamp", "")
            
            # Count log levels
            if "error" in message:
                error_count += 1
                recent_errors.append(f"{timestamp}: {message}")
            elif "warning" in message:
                warning_count += 1
            elif "info" in message:
                info_count += 1
            
            # Check for specific error patterns
            for pattern in error_patterns:
                if pattern.lower() in message:
                    recent_errors.append(f"{timestamp}: {pattern}")
        
        print(f"📈 Log Levels:")
        print(f"   Errors: {error_count}")
        print(f"   Warnings: {warning_count}")
        print(f"   Info: {info_count}")
        
        if recent_errors:
            print(f"\n🚨 Recent Errors/Issues:")
            for error in recent_errors[-10:]:  # Show last 10 errors
                print(f"   {error}")
        
        # Check for specific deployment issues
        deployment_issues = []
        for log in logs:
            message = log.get("message", "")
            if "ModuleNotFoundError" in message:
                deployment_issues.append("Import/Module issue detected")
            if "database" in message.lower() and "error" in message.lower():
                deployment_issues.append("Database connection issue")
            if "port" in message.lower() and "error" in message.lower():
                deployment_issues.append("Port binding issue")
        
        if deployment_issues:
            print(f"\n🎯 Potential Deployment Issues:")
            for issue in set(deployment_issues):
                print(f"   - {issue}")

def main():
    print("🔍 Render API Log Puller")
    print("=" * 60)
    
    # You need to provide your API key
    api_key = input("Enter your Render API key (or set RENDER_API_KEY env var): ").strip()
    
    if not api_key:
        api_key = os.environ.get("RENDER_API_KEY")
        if not api_key:
            print("❌ No API key provided")
            return
    
    puller = RenderLogPuller(api_key)
    
    # Find the jobhuntin-api service
    print("\n🔍 Finding jobhuntin-api service...")
    service = puller.find_service_by_name("jobhuntin-api")
    
    if not service:
        print("❌ jobhuntin-api service not found")
        services = puller.get_services()
        if services:
            print("Available services:")
            for s in services:
                print(f"   - {s.get('name')} ({s.get('type')})")
        return
    
    service_id = service.get("id")
    print(f"✅ Found service: {service.get('name')} (ID: {service_id})")
    print(f"   Status: {service.get('status')}")
    print(f"   Type: {service.get('type')}")
    
    # Pull logs
    print(f"\n📥 Pulling logs from last 24 hours...")
    logs = puller.get_all_service_logs(service_id, hours_back=24)
    
    if not logs:
        print("❌ No logs retrieved")
        return
    
    print(f"✅ Retrieved {len(logs)} log entries")
    
    # Save logs
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"jobhuntin_api_logs_{timestamp}.json"
    puller.save_logs_to_file(logs, logs)
    
    # Analyze logs
    puller.analyze_logs(logs)
    
    # Show recent logs
    print(f"\n📋 Recent Logs (last 10):")
    print("=" * 60)
    for log in logs[-10:]:
        timestamp = log.get("timestamp", "")
        message = log.get("message", "")
        print(f"{timestamp}: {message}")

if __name__ == "__main__":
    main()
