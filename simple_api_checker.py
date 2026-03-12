#!/usr/bin/env python3
"""
Simple API Key Configuration Checker
"""

import os
import re
from pathlib import Path

def main():
    print("API Key Configuration Checker")
    print("=" * 50)
    
    # Check render.yaml
    render_file = Path("render.yaml")
    if not render_file.exists():
        print("❌ render.yaml not found")
        return
    
    content = render_file.read_text()
    
    # Check for LLM_API_KEY configuration
    if "LLM_API_KEY:" in content:
        print("✅ LLM_API_KEY found in render.yaml")
        
        # Check sync status
        sync_match = re.search(r'LLM_API_KEY:\s*sync:\s*(\w+)', content)
        if sync_match:
            sync_value = sync_match.group(1).strip()
            if sync_value.lower() in ['false', 'no', '0']:
                print("⚠️  LLM_API_KEY is set to sync: false")
                print("   This means you need to configure it manually in Render dashboard")
            else:
                print("✅ LLM_API_KEY sync status:", sync_value)
        else:
            print("⚠️  LLM_API_KEY sync status unclear")
    else:
        print("❌ LLM_API_KEY not found in render.yaml")
    
    # Check for other required keys
    required_keys = ['JWT_SECRET', 'CSRF_SECRET']
    for key in required_keys:
        if f'{key}:' in content:
            print(f"✅ {key} found")
        else:
            print(f"❌ {key} not found")
    
    print("\n📋 Setup Instructions:")
    print("1. Go to: https://dashboard.render.com")
    print("2. Select: jobhuntin-api service")
    print("3. Add environment variables with sync: false")
    print("4. Required keys: LLM_API_KEY, JWT_SECRET, CSRF_SECRET")
    
    print("\n🔑 Generate API Keys:")
    print("OpenRouter: https://openrouter.ai/keys")
    print("JWT Secret: python -c 'import secrets; print(secrets.token_hex(32))'")
    print("CSRF Secret: python -c 'import secrets; print(secrets.token_hex(32))'")

if __name__ == "__main__":
    main()
