#!/usr/bin/env python3
"""
Complete migration runner - executes all steps for Supabase to Render migration
"""

import asyncio
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_complete_migration(render_database_url: str):
    """Run the complete migration process"""
    
    print("=== Starting Complete Migration: Supabase to Render ===")
    print()
    
    # Step 1: Validate the Render database URL
    if not render_database_url or not render_database_url.startswith("postgresql://"):
        print("❌ Invalid database URL format")
        print("Expected: postgresql://user:password@host:5432/database")
        return False
    
    print(f"✅ Database URL validated: {render_database_url[:50]}...")
    print()
    
    # Step 2: Test Render database connectivity
    print("🔍 Testing Render database connectivity...")
    try:
        import asyncpg
        conn = await asyncpg.connect(render_database_url)
        await conn.execute("SELECT 1")
        await conn.close()
        print("✅ Render database is accessible")
    except Exception as e:
        print(f"❌ Cannot connect to Render database: {e}")
        return False
    
    print()
    
    # Step 3: Run the migration
    print("🚀 Running database migration...")
    try:
        from migrate_to_render import DatabaseMigrator
        migrator = DatabaseMigrator()
        await migrator.run_full_migration(render_database_url)
        print("✅ Migration completed successfully!")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    print()
    
    # Step 4: Update environment file
    print("📝 Creating .env file with new database URL...")
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Update DATABASE_URL
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            if line.startswith('DATABASE_URL='):
                new_lines.append(f'DATABASE_URL={render_database_url}')
            elif line.startswith('SUPABASE_'):
                # Remove Supabase lines
                continue
            else:
                new_lines.append(line)
        
        with open(env_file, 'w') as f:
            f.write('\n'.join(new_lines))
        
        print("✅ Updated .env file")
    else:
        # Create new .env file
        env_content = f"""DATABASE_URL={render_database_url}
LLM_API_BASE=https://openrouter.ai/api/v1
LLM_API_KEY=your-api-key
LLM_MODEL=google/gemma-2-9b-it:free
ENV=local
AGENT_ENABLED=true
LOG_JSON=false
LOG_LEVEL=DEBUG
CSRF_SECRET=generate-random-secret
"""
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print("✅ Created new .env file")
    
    print()
    
    # Step 5: Summary
    print("=== Migration Summary ===")
    print("✅ Database schema migrated")
    print("✅ Data transferred from Supabase")
    print("✅ Configuration files updated")
    print("✅ Environment variables set")
    print()
    print("=== Next Steps ===")
    print("1. Test your application locally: python -m apps.api.main")
    print("2. Update your Render service environment variables")
    print("3. Deploy to Render")
    print("4. Verify all functionality works")
    print()
    print("=== Important Notes ===")
    print("- Authentication system needs to be updated (removed Supabase auth)")
    print("- File storage needs alternative if using Supabase Storage")
    print("- Realtime subscriptions have been removed")
    
    return True

def main():
    """Main entry point"""
    if len(sys.argv) != 2:
        print("Usage: python run_migration.py <render_database_url>")
        print()
        print("Example:")
        print("python run_migration.py postgresql://jobhuntin_user:password@host:5432/jobhuntin")
        sys.exit(1)
    
    render_url = sys.argv[1]
    
    try:
        success = asyncio.run(run_complete_migration(render_url))
        if success:
            print("\n🎉 Migration completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Migration failed. Check the errors above.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
