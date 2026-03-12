#!/usr/bin/env python3
"""
API Key Configuration and Syntax Checker
Finds syntax errors and validates API key configuration.
"""

import os
import sys
import json
import subprocess
import re
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

def check_quoted_string_errors():
    """Check for common quoted string syntax errors"""
    print("🔍 Checking for Quoted String Syntax Errors...")
    print("=" * 60)
    
    key_files = [
        "render.yaml",
        "apps/api/main.py",
        "packages/backend/llm/client.py",
        "packages/backend/domain/repositories.py",
        "apps/worker/scaling.py",
    ]
    
    errors_found = []
    
    for file_path in key_files:
        full_path = project_root / file_path
        if not full_path.exists():
            print(f"⚠️  File not found: {file_path}")
            continue
            
        try:
            content = full_path.read_text(encoding='utf-8')
            
            # Check for common quoted string issues
            issues = []
            
            # 1. Check for triple quotes in YAML
            if file_path.endswith('.yaml'):
                if "'''" in content or '"\"' in content:
                    issues.append("Triple quotes detected")
            
            # 2. Check for unmatched quotes
            single_quotes = content.count("'")
            double_quotes = content.count('"')
            if single_quotes % 2 != 0 or double_quotes % 2 != 0:
                issues.append(f"Unmatched quotes (single: {single_quotes % 2}, double: {double_quotes % 2})")
            
            # 3. Check for problematic escape sequences
            problematic_patterns = [
                r'\\[^\n"\\\'t]',  # Invalid escape sequences
                r'\\[^n"\\\'\\r]',  # Invalid escape sequences
                r'\'[^\\n"\\\'r]',  # Single quote issues
            ]
            
            for pattern in problematic_patterns:
                if re.search(pattern, content):
                    issues.append(f"Problematic escape sequence: {pattern}")
            
            # 4. Check for environment variable syntax issues
            env_var_pattern = r'\$\{[^}]*\}'
            if re.search(env_var_pattern, content):
                issues.append("Environment variable syntax issue")
            
            # 5. Check for specific syntax errors around quotes
            quote_errors = [
                (r'\'[^\s\$\}]', "Single quote before variable"),
                (r'[\$\{][^\s]*\'', "Single quote after variable"),
                (r'"[^\s\$\}]', "Double quote before variable"),
                (r'[\$\{][^\s]*"', "Double quote after variable"),
            ]
            
            for pattern, description in quote_errors:
                if re.search(pattern, content):
                    issues.append(f"Quote syntax error: {description}")
            
            if issues:
                errors_found.append({
                    'file': file_path,
                    'issues': issues
                })
                print(f"❌ {file_path}:")
                for issue in issues:
                    print(f"   - {issue}")
            else:
                print(f"✅ {file_path}: No quote syntax errors")
                
        except Exception as e:
            print(f"❌ {file_path}: Error checking file - {e}")
            errors_found.append({
                'file': file_path,
                'issues': [f"File read error: {e}"]
            })
    
    return errors_found

def check_api_key_configuration():
    """Check API key configuration in render.yaml"""
    print("\n🔑 Checking API Key Configuration...")
    print("=" * 60)
    
    render_file = project_root / "render.yaml"
    if not render_file.exists():
        print("❌ render.yaml not found")
        return False
    
    try:
        content = render_file.read_text(encoding='utf-8')
        
        # Check for LLM_API_KEY configuration
        api_key_configs = []
        
        # Find all services with LLM_API_KEY
        services = re.findall(r'- name: ([^\n]+)', content)
        
        for service_name in services:
            service_start = content.find(f'- name: {service_name}')
            if service_start == -1:
                continue
                
            service_end = content.find('\n-', service_start + 1)
            if service_end == -1:
                service_content = content[service_start:]
            else:
                service_content = content[service_start:service_end]
            
            # Check for LLM_API_KEY in this service
            if 'LLM_API_KEY:' in service_content:
                api_key_configs.append(service_name)
                
                # Extract the sync status
                sync_match = re.search(r'LLM_API_KEY:\s*sync:\s*(\w+)', service_content)
                if sync_match:
                    sync_value = sync_match.group(1).strip()
                    if sync_value.lower() in ['false', 'no', '0']:
                        print(f"⚠️  {service_name}: LLM_API_KEY is set to sync: false (needs manual configuration)")
                    else:
                        print(f"✅ {service_name}: LLM_API_KEY is configured for sync")
                else:
                    print(f"⚠️  {service_name}: LLM_API_KEY found but sync status unclear")
        
        if not api_key_configs:
            print("⚠️  No LLM_API_KEY configurations found")
        
        # Check for other API keys
        other_keys = ['JWT_SECRET', 'CSRF_SECRET', 'STRIPE_SECRET_KEY']
        for key in other_keys:
            if f'{key}:' in content:
                sync_match = re.search(f'{key}:\\s*sync:\\s*(\\w+)', content)
                if sync_match:
                    sync_value = sync_match.group(1).strip()
                    if sync_value.lower() in ['false', 'no', '0']:
                        print(f"⚠️  {key}: Set to sync: false (needs manual configuration)")
        
        return len(api_key_configs) > 0
        
    except Exception as e:
        print(f"❌ Error checking render.yaml: {e}")
        return False

def create_api_key_setup_guide():
    """Create API key setup guide"""
    print("\n📋 Creating API Key Setup Guide...")
    
    guide = """# API Key Configuration Guide for JobHuntin

## Required API Keys

### 1. OpenRouter API Key (LLM_API_KEY)
- Go to: https://openrouter.ai/keys
- Create account or sign in
- Generate new API key
- Copy the key

### 2. JWT Secret (JWT_SECRET)
- Generate random secret: openssl rand -hex 32
- Or use: python -c "import secrets; print(secrets.token_hex(32))"

### 3. CSRF Secret (CSRF_SECRET)
- Generate random secret: openssl rand -hex 32
- Or use: python -c "import secrets; print(secrets.token_hex(32))"

### 4. Stripe Secret Key (STRIPE_SECRET_KEY) - Optional
- Go to: https://dashboard.stripe.com/apikeys
- Create account or sign in
- Generate secret key (not publishable key)

## Render Dashboard Configuration

### Step 1: Go to Render Dashboard
1. Visit: https://dashboard.render.com
2. Select: jobhuntin-api service
3. Click: Environment tab

### Step 2: Add Environment Variables
For each required key, add:

#### LLM_API_KEY
- Key: LLM_API_KEY
- Value: your-openrouter-api-key-here
- Sync: false (IMPORTANT: Set to false for security)

#### JWT_SECRET
- Key: JWT_SECRET
- Value: your-jwt-secret-here
- Sync: false

#### CSRF_SECRET
- Key: CSRF_SECRET
- Value: your-csrf-secret-here
- Sync: false

#### STRIPE_SECRET_KEY (if using Stripe)
- Key: STRIPE_SECRET_KEY
- Value: sk_live_your-stripe-secret-key-here
- Sync: false

### Step 3: Save and Deploy
1. Click Save Changes
2. Wait for automatic deployment
3. Monitor deployment logs

## Quick Test Commands

### Test API Key Configuration
```bash
# Test locally (set keys first)
export LLM_API_KEY="your-key-here"
export JWT_SECRET="your-jwt-secret"
export CSRF_SECRET="your-csrf-secret"
PYTHONPATH=apps:packages:. python -c "
from api.main import app
print('API starts successfully with configured keys')
"
```

### Test Render API
```bash
# Check if API is responding
curl -s -o /dev/null -w "%{http_code}" https://sorce-api.onrender.com/health

# Check API documentation
curl -s -o /dev/null -w "%{http_code}" https://sorce-api.onrender.com/docs
```

## Common Issues and Fixes

### Issue: SyntaxError: EOL while scanning string literal
**Cause**: Unmatched quotes or escape sequences
**Fix**: 
1. Check for unmatched single/double quotes
2. Verify escape sequences are correct
3. Use triple quotes for multi-line strings

### Issue: quoted string errors in logs
**Cause**: Environment variables with special characters
**Fix**:
1. Properly escape special characters
2. Use single quotes for variables with special chars
3. Test variable expansion locally

### Issue: Service crashes with 503 error
**Cause**: Missing or incorrect API keys
**Fix**:
1. Verify all required environment variables
2. Check API key format and permissions
3. Ensure sync: false for sensitive keys

## Security Best Practices

1. Never commit API keys to git
2. Use sync: false for all secrets
3. Generate strong random secrets
4. Rotate keys regularly
5. Monitor API key usage

## Verification Checklist

- [ ] LLM_API_KEY configured in Render dashboard
- [ ] JWT_SECRET configured in Render dashboard  
- [ ] CSRF_SECRET configured in Render dashboard
- [ ] All secrets set to sync: false
- [ ] API responds with 200 OK
- [ ] No syntax errors in logs
- [ ] Services start successfully

## Support

If issues persist:
1. Check Render dashboard logs: https://dashboard.render.com/services/jobhuntin-api
2. Review recent deployments
3. Check environment variable syntax
4. Test configuration locally first
"""
    
    guide_file = project_root / "API_KEY_SETUP_GUIDE.md"
    guide_file.write_text(guide)
    print(f"✅ API key setup guide created: {guide_file}")

def create_syntax_fixer():
    """Create a tool to fix common syntax errors"""
    print("\n🔧 Creating Syntax Fixer...")
    
    fixer_script = """#!/usr/bin/env python3
"""
Automatic Syntax Fixer for JobHuntin
Fixes common quoted string and environment variable issues.
"""

import re
import sys
from pathlib import Path

def fix_yaml_quotes(file_path):
    \"\"\"Fix quote issues in YAML files\"\"\"
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix common YAML quote issues
    fixes = [
        # Fix triple quotes
        (r"'''", "'"),
        (r'""'"', '"'),
        
        # Fix environment variable quoting
        (r'\\$\\{([^}]+)\\}', r'$\\1'),
        
        # Fix quote escaping
        (r"'\\$\\{([^}]+)\\}'", r"'\\$\\1'"),
        (r'"\\$\\{([^}]+)\\}"', r'"\\$\\1'"),
    ]
    
    original_content = content
    for pattern, replacement in fixes:
        content = re.sub(pattern, replacement, content)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Fixed quotes in {file_path}")
        return True
    
    return False

def fix_python_quotes(file_path):
    \"\"\"Fix quote issues in Python files\"\"\"
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix common Python quote issues
    fixes = [
        # Fix f-string quote issues
        (r"f'([^']*?)'([^']*?)'", r'f"\\1\\2"'),
        (r'f"([^"]*?)"([^"]*?)"', r"f'\\1\\2'"),
        
        # Fix environment variable expansion
        (r'"\\$\\{([^}]+)\\}"', r'os.environ.get("\\1", "")'),
        (r"'\\$\\{([^}]+)\\}'", r'os.environ.get("\\1", "")'),
    ]
    
    original_content = content
    for pattern, replacement in fixes:
        content = re.sub(pattern, replacement, content)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Fixed quotes in {file_path}")
        return True
    
    return False

def main():
    \"\"\"Main fixer function\"\"\"
    if len(sys.argv) != 2:
        print("Usage: python syntax_fixer.py <file_path>")
        return
    
    file_path = sys.argv[1]
    
    if not Path(file_path).exists():
        print(f"File not found: {file_path}")
        return
    
    if file_path.endswith('.yaml'):
        fix_yaml_quotes(file_path)
    elif file_path.endswith('.py'):
        fix_python_quotes(file_path)
    else:
        print("Unsupported file type. Use .yaml or .py files.")

if __name__ == "__main__":
    main()
"""
    
    fixer_file = project_root / "syntax_fixer.py"
    fixer_file.write_text(fixer_script)
    print(f"✅ Syntax fixer created: {fixer_file}")
    print("Usage: python syntax_fixer.py <file_path>")

def main():
    \"\"\"Main function\"\"\"
    print("🔑 API Key Configuration and Syntax Checker")
    print("=" * 60)
    
    # Check for quoted string errors
    quote_errors = check_quoted_string_errors()
    
    # Check API key configuration
    api_configured = check_api_key_configuration()
    
    # Create setup guide
    create_api_key_setup_guide()
    
    # Create syntax fixer
    create_syntax_fixer()
    
    # Summary
    print("\n📊 SUMMARY")
    print("=" * 60)
    
    if quote_errors:
        print(f"❌ Found {len(quote_errors)} files with quote syntax errors:")
        for error in quote_errors:
            print(f"   - {error['file']}: {', '.join(error['issues'])}")
        print("\n🔧 Fix with: python syntax_fixer.py <file_path>")
    else:
        print("✅ No quote syntax errors found")
    
    if api_configured:
        print("✅ API key configuration found in render.yaml")
    else:
        print("⚠️  API key configuration may be missing")
    
    print("\n💡 NEXT STEPS:")
    print("1. Read API_KEY_SETUP_GUIDE.md")
    print("2. Configure API keys in Render dashboard")
    print("3. Use syntax_fixer.py if needed")
    print("4. Test deployment after configuration")

if __name__ == "__main__":
    main()
