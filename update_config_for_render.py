#!/usr/bin/env python3
"""
Update configuration files for Render PostgreSQL migration
"""

import os
import re
from pathlib import Path
import sys

def update_env_example():
    """Update .env.example to use Render instead of Supabase."""
    env_file = Path(__file__).parent / ".env.example"
    
    if not env_file.exists():
        print(f"❌ .env.example not found")
        return False
    
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Replace Supabase section with Render
    new_content = re.sub(
        r'# ── Supabase ─────────────────────────────────────────────────\n.*?DATABASE_URL=postgresql://postgres\.project:password@aws-0-region\.pooler\.supabase\.com:6543/postgres',
        '''# ── Render PostgreSQL ────────────────────────────────────────
# Get this from your Render PostgreSQL dashboard
DATABASE_URL=postgresql://jobhuntin_user:password@host:5432/jobhuntin''',
        content,
        flags=re.DOTALL
    )
    
    # Remove other Supabase references
    new_content = re.sub(r'SUPABASE_.*?\n', '', new_content)
    
    with open(env_file, 'w') as f:
        f.write(new_content)
    
    print("✅ Updated .env.example")
    return True

def update_config_py():
    """Update config.py to remove Supabase dependencies."""
    config_file = Path(__file__).parent / "packages" / "shared" / "config.py"
    
    if not config_file.exists():
        print(f"❌ config.py not found")
        return False
    
    with open(config_file, 'r') as f:
        content = f.read()
    
    # Remove Supabase section
    new_content = re.sub(
        r'    # ── Supabase ─────────────────────────────────────────────────\n.*?    supabase_storage_bucket: str = "resumes"',
        '',
        content,
        flags=re.DOTALL
    )
    
    # Update validation to remove Supabase checks
    new_content = re.sub(
        r'            if not self\.supabase_jwt_secret:\s*\n\s*missing\.append\("SUPABASE_JWT_SECRET"\)\s*\n.*?if not self\.supabase_service_key:\s*\n\s*missing\.append\("SUPABASE_SERVICE_KEY"\)',
        '',
        new_content,
        flags=re.DOTALL
    )
    
    with open(config_file, 'w') as f:
        f.write(new_content)
    
    print("✅ Updated packages/shared/config.py")
    return True

def update_main_py():
    """Update main.py to remove Supabase-specific code."""
    main_file = Path(__file__).parent / "apps" / "api" / "main.py"
    
    if not main_file.exists():
        print(f"❌ main.py not found")
        return False
    
    with open(main_file, 'r') as f:
        content = f.read()
    
    # Remove Supabase-specific SSL handling
    new_content = re.sub(
        r'        if "pooler\.supabase\.com" not in settings\.database_url and "supabase\.co" not in settings\.database_url:.*?return True',
        '        # Standard PostgreSQL SSL verification\n        if "sslmode" in settings.database_url:\n            import ssl as _ssl\n            ssl_ctx = _ssl.create_default_context()\n            ca_path = getattr(settings, "db_ssl_ca_cert_path", "")\n            if ca_path:\n                ssl_ctx.load_verify_locations(ca_path)\n            engine.dialect.init_connect_pool.append(lambda conn: conn.connection.set_sslcontext(ssl_ctx))\n        return True',
        content,
        flags=re.DOTALL
    )
    
    with open(main_file, 'w') as f:
        f.write(new_content)
    
    print("✅ Updated apps/api/main.py")
    return True

def create_render_env():
    """Create a new .env.render template."""
    env_content = """# ============================================================
# SORCE - Render Environment Configuration
# ============================================================
# Copy this to your Render service environment variables

# -- Render PostgreSQL -----------------------------------------------
DATABASE_URL=postgresql://jobhuntin_user:YOUR_PASSWORD@YOUR_HOST:5432/jobhuntin

# -- LLM / OpenRouter ------------------------------------------------
LLM_API_BASE=https://openrouter.ai/api/v1
LLM_API_KEY=sk-or-your-key
LLM_MODEL=google/gemma-2-9b-it:free

# -- Adzuna Job Board API --------------------------------------------
ADZUNA_APP_ID=your-app-id
ADZUNA_API_KEY=your-api-key

# -- Stripe ----------------------------------------------------------
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxx

# -- App Config ------------------------------------------------------
ENV=prod
AGENT_ENABLED=true
LOG_JSON=true
LOG_LEVEL=INFO
CSRF_SECRET=generate-random-secret

# -- App URLs --------------------------------------------------------
APP_BASE_URL=https://your-app.onrender.com
"""
    
    env_file = Path(__file__).parent / ".env.render"
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ Created .env.render template")
    return True

def main():
    """Run all configuration updates."""
    print("=== Updating Configuration for Render PostgreSQL ===")
    print()
    
    success = True
    
    # Update all configuration files
    success &= update_env_example()
    success &= update_config_py() 
    success &= update_main_py()
    success &= create_render_env()
    
    if success:
        print()
        print("✅ All configuration files updated!")
        print()
        print("=== NEXT STEPS ===")
        print("1. Create Render PostgreSQL database")
        print("2. Get the DATABASE_URL from Render dashboard")
        print("3. Update your Render service environment")
        print("4. Run migration script: python migrate_to_render.py <DATABASE_URL>")
        print("5. Test the application")
    else:
        print("❌ Some updates failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
