#!/usr/bin/env python3
"""
Fix DATABASE_URL for Render services
"""

import os
import subprocess
import json

def run_command(cmd):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), 1

def main():
    # Supabase connection details from the provided info
    supabase_project_id = "zglovpfwyobbbaaocawz"
    supabase_host = "aws-0-us-east-1.pooler.supabase.com"  # From error logs
    
    # Construct proper DATABASE_URL
    # Format: postgresql://[user]:[password]@[host]:[port]/[database]
    
    # We need to get the actual database credentials from Supabase
    # For now, let's use the transaction pooler format
    database_url = f"postgresql://postgres.{supabase_project_id}:{'ravhuv-gitqec-nixvY4'}@{supabase_host}:6543/postgres"
    
    print("=== DATABASE_URL FIX ===")
    print(f"Constructed DATABASE_URL: {database_url}")
    print()
    
    # Set environment variable for the API service
    service_id = "srv-d63l79hr0fns73boblag"  # jobhuntin-api
    
    print(f"Setting DATABASE_URL for service {service_id}...")
    
    # Using Render CLI to set environment variable
    cmd = f'render env set DATABASE_URL="{database_url}" --service-id {service_id}'
    print(f"Command: {cmd}")
    
    stdout, stderr, code = run_command(cmd)
    
    if code == 0:
        print("✅ DATABASE_URL set successfully!")
        print(stdout)
    else:
        print(f"❌ Failed to set DATABASE_URL: {stderr}")
        
        # Alternative: Manual instructions
        print("\n=== MANUAL SETUP INSTRUCTIONS ===")
        print("1. Go to Render Dashboard")
        print("2. Navigate to jobhuntin-api service")
        print("3. Go to Environment tab")
        print("4. Add new environment variable:")
        print(f"   Key: DATABASE_URL")
        print(f"   Value: {database_url}")
        print("5. Save and redeploy the service")

if __name__ == "__main__":
    main()
