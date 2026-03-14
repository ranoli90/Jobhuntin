#!/usr/bin/env python3
"""
Render API Configuration Script
Configures API keys in render.yaml with proper formatting.
"""

import re
from pathlib import Path


def update_render_yaml_with_api_key():
    """Update render.yaml with the provided API key"""
    api_key = "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"

    render_file = Path("render.yaml")
    if not render_file.exists():
        print("❌ render.yaml not found")
        return False

    content = render_file.read_text()

    # Find the jobhuntin-api service
    api_service_start = content.find("    name: jobhuntin-api")
    if api_service_start == -1:
        print("❌ jobhuntin-api service not found in render.yaml")
        return False

    # Find the envVars section for jobhuntin-api
    env_vars_start = content.find("envVars:", api_service_start)
    if env_vars_start == -1:
        print("❌ envVars section not found for jobhuntin-api")
        return False

    # Find the next service or end of file
    next_service = content.find("\n  -", env_vars_start + 1)
    if next_service == -1:
        next_service = len(content)

    service_section = content[api_service_start:next_service]

    # Check if LLM_API_KEY already exists
    if "LLM_API_KEY:" in service_section:
        print("⚠️  LLM_API_KEY already exists in jobhuntin-api service")
        print("   Updating existing key...")

        # Replace existing LLM_API_KEY
        pattern = r'(LLM_API_KEY:\s*)[^\n]*'
        replacement = f'\\1{api_key}'
        updated_section = re.sub(pattern, replacement, service_section)
    else:
        print("✅ Adding new LLM_API_KEY to jobhuntin-api service")

        # Add LLM_API_KEY after the existing envVars
        insert_pos = env_vars_start + len("envVars:")
        new_llm_key = f'      - key: LLM_API_KEY\n        value: {api_key}\n        sync: false\n'

        updated_section = service_section[:insert_pos] + new_llm_key + service_section[insert_pos:]

    # Replace the service section in the full content
    updated_content = content[:api_service_start] + updated_section + content[next_service:]

    # Write back to file
    render_file.write_text(updated_content)
    print("✅ Updated render.yaml with LLM_API_KEY")

    # Also update the worker service
    worker_service_start = content.find("- name: sorce-auto-apply-agent")
    if worker_service_start != -1:
        worker_env_vars_start = content.find("envVars:", worker_service_start)
        if worker_env_vars_start != -1:
            next_worker = content.find("\n  -", worker_service_start + 1)
            if next_worker == -1:
                next_worker = len(content)

            worker_section = content[worker_service_start:next_worker]

            if "LLM_API_KEY:" in worker_section:
                print("⚠️  LLM_API_KEY already exists in worker service")
                pattern = r'(LLM_API_KEY:\s*)[^\n]*'
                replacement = f'\\1{api_key}'
                updated_worker_section = re.sub(pattern, replacement, worker_section)
            else:
                print("✅ Adding new LLM_API_KEY to worker service")
                insert_pos = worker_env_vars_start + len("envVars:")
                new_llm_key = f'      - key: LLM_API_KEY\n        value: {api_key}\n        sync: false\n'
                updated_worker_section = worker_section[:insert_pos] + new_llm_key + worker_section[insert_pos:]

            updated_content = updated_content[:worker_service_start] + updated_worker_section + content[next_worker:]
            render_file.write_text(updated_content)
            print("✅ Updated render.yaml with LLM_API_KEY for worker service")

    return True

def generate_secrets():
    """Generate JWT and CSRF secrets"""
    import secrets

    jwt_secret = secrets.token_hex(32)
    csrf_secret = secrets.token_hex(32)

    print(f"🔑 Generated JWT_SECRET: {jwt_secret}")
    print(f"🔑 Generated CSRF_SECRET: {csrf_secret}")

    return jwt_secret, csrf_secret

def create_deployment_script():
    """Create deployment script with secrets"""
    jwt_secret, csrf_secret = generate_secrets()

    script = f'''#!/bin/bash
# JobHuntin Deployment Script with API Keys

echo "🚀 Configuring JobHuntin API Keys..."
echo "=================================="

# Set environment variables
export LLM_API_KEY="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"
export JWT_SECRET="{jwt_secret}"
export CSRF_SECRET="{csrf_secret}"

echo "✅ API Key configured"
echo "✅ JWT Secret configured"
echo "✅ CSRF Secret configured"

echo ""
echo "📋 Next Steps:"
echo "1. Go to: https://dashboard.render.com"
echo "2. Select: jobhuntin-api service"
echo "3. Add Environment Variables:"
echo "   - LLM_API_KEY: ${{LLM_API_KEY}}"
echo "   - JWT_SECRET: ${{JWT_SECRET}}"
echo "   - CSRF_SECRET: ${{CSRF_SECRET}}"
echo "   - Set all to sync: false"
echo "4. Click Save Changes"
echo "5. Monitor deployment logs"

echo ""
echo "🔍 Testing API startup..."
PYTHONPATH=apps:packages:. python -c "
from api.main import app
print('✅ API should start successfully now!')
"

echo ""
echo "🌐 Checking API health..."
sleep 10
curl -s -o /dev/null -w "%{{http_code}}" https://sorce-api.onrender.com/health
echo ""
echo "✅ Configuration complete!"
'''

    script_file = Path("deploy_with_keys.sh")
    script_file.write_text(script)
    script_file.chmod(0o755)

    print(f"✅ Deployment script created: {script_file}")
    print("Run with: ./deploy_with_keys.sh")

def main():
    print("🔧 Render API Key Configuration")
    print("=" * 60)

    # Update render.yaml
    if update_render_yaml_with_api_key():
        print("✅ render.yaml updated successfully")

        # Create deployment script
        create_deployment_script()

        print("\n📋 SUMMARY:")
        print("=" * 60)
        print("✅ LLM_API_KEY configured in render.yaml")
        print("✅ JWT_SECRET and CSRF_SECRET generated")
        print("✅ Deployment script created")
        print("\n💡 NEXT STEPS:")
        print("1. Run: ./deploy_with_keys.sh")
        print("2. Monitor deployment in Render dashboard")
        print("3. Verify API health: https://sorce-api.onrender.com/health")
    else:
        print("❌ Failed to update render.yaml")

if __name__ == "__main__":
    main()
