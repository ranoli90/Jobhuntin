#!/usr/bin/env python3
"""
Complete migration to paid Render database
Handles database setup, table creation, data migration, and SEO automation
"""

import asyncio
import asyncpg
import sys
from pathlib import Path
import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("migration_internal.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class CompleteMigrator:
    def __init__(self):
        self.render_conn = None
        self.supabase_conn = None

    async def connect_to_render(self, database_url: str):
        """Connect to the paid Render database"""
        try:
            self.render_conn = await asyncpg.connect(
                database_url,
                server_settings={'application_name': 'complete_migration'}
            )
            logger.info("  Connected to paid Render database")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to Render: {e}")
            return False

    async def connect_to_supabase(self):
        """Connect to Supabase for data migration"""
        try:
            # Use existing Supabase connection from config
            from packages.shared.config import get_settings
            settings = get_settings()
            
            self.supabase_conn = await asyncpg.connect(
                settings.database_url,
                server_settings={'application_name': 'migration_source'}
            )
            logger.info("✅ Connected to Supabase database")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to Supabase: {e}")
            return False

    async def create_complete_schema(self):
        """Create complete database schema on Render"""
        logger.info("  Creating complete database schema...")
        
        try:
            # Enable extensions
            await self.render_conn.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
            await self.render_conn.execute("CREATE EXTENSION IF NOT EXISTS \"pg_trgm\"")
            
            # Create all tables from schema
            schema_file = Path(__file__).parent / "infra" / "supabase" / "schema.sql"
            if schema_file.exists():
                with open(schema_file, 'r') as f:
                    schema_sql = f.read()
                
                # Clean schema for Render
                schema_sql = self._clean_schema_for_render(schema_sql)
                logger.info(f"DEBUG SQL: {schema_sql[:500]}...") # Log first 500 chars
                # write to file for full inspection
                with open("debug_schema.sql", "w") as df:
                    df.write(schema_sql)
                
                await self.render_conn.execute(schema_sql)
                logger.info("  Core schema created")
            
            # Create additional tables for SEO automation
            await self._create_seo_tables()
            
            # Create enhanced tables for new features
            await self._create_enhanced_tables()
            
            logger.info("  Complete schema created successfully")
            return True
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"❌ Schema creation failed: {e}")
            return False

    def _clean_schema_for_render(self, schema_sql: str) -> str:
        """Remove Supabase-specific elements"""
        # Define schemas to remove references to
        generated_sql = schema_sql

        # 1. Remove references to auth.users
        generated_sql = generated_sql.replace("REFERENCES auth.users (id) ON DELETE CASCADE", "")
        generated_sql = generated_sql.replace("references auth.users (id) on delete cascade", "")
        generated_sql = generated_sql.replace("REFERENCES auth.users (id)", "")
        generated_sql = generated_sql.replace("references auth.users (id)", "")
        generated_sql = generated_sql.replace("auth.uid()", "NULL")
        
        # 2. Remove RLS policies entirely (too complex to migrate blindly)
        lines = generated_sql.split('\n')
        cleaned_lines = []
        skip_current_statement = False
        
        for line in lines:
            l = line.strip().lower()
            
            # Start skipping if it's a policy or RLS enablement
            if not skip_current_statement:
                if l.startswith("create policy") or (l.startswith("alter table") and "enable row level security" in l) or "alter publication" in l:
                    skip_current_statement = True
            
            # If we are valid to process (or just finished skipping previous)
            if not skip_current_statement:
                # Extension handling
                if "create extension" in l and "if not exists" not in l:
                     line = line.replace("CREATE EXTENSION", "CREATE EXTENSION IF NOT EXISTS")
                
                # Default auth/supabase handling
                if "extensions." in l:
                    line = line.replace("extensions.", "public.")
                
                cleaned_lines.append(line)
            
            # Check if we should stop skipping (semicolon at end of line)
            if skip_current_statement and line.strip().endswith(';'):
                skip_current_statement = False

        return '\n'.join(cleaned_lines)

    async def _create_seo_tables(self):
        """Create SEO automation tables"""
        logger.info("  Creating SEO automation tables...")
        
        seo_tables = """
        -- SEO Pages table
        CREATE TABLE IF NOT EXISTS seo_pages (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            path text UNIQUE NOT NULL,
            title text,
            description text,
            keywords text[],
            status text DEFAULT 'active',
            last_generated timestamptz,
            metadata jsonb DEFAULT '{}',
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        );

        -- SEO Keywords table
        CREATE TABLE IF NOT EXISTS seo_keywords (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            keyword text NOT NULL,
            volume integer DEFAULT 0,
            difficulty real DEFAULT 0.0,
            intent text,
            page_id uuid REFERENCES seo_pages(id) ON DELETE SET NULL,
            created_at timestamptz NOT NULL DEFAULT now()
        );

        -- SEO Analytics table
        CREATE TABLE IF NOT EXISTS seo_analytics (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            page_id uuid REFERENCES seo_pages(id) ON DELETE CASCADE,
            metric_name text NOT NULL,
            metric_value real NOT NULL,
            date date NOT NULL,
            source text DEFAULT 'internal',
            created_at timestamptz NOT NULL DEFAULT now()
        );

        -- SEO Tasks table
        CREATE TABLE IF NOT EXISTS seo_tasks (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            task_type text NOT NULL,
            status text DEFAULT 'pending',
            priority text DEFAULT 'medium',
            data jsonb DEFAULT '{}',
            scheduled_at timestamptz,
            completed_at timestamptz,
            error_message text,
            created_at timestamptz NOT NULL DEFAULT now()
        );

        -- Indexes for SEO tables
        CREATE INDEX IF NOT EXISTS idx_seo_pages_path ON seo_pages(path);
        CREATE INDEX IF NOT EXISTS idx_seo_pages_status ON seo_pages(status);
        CREATE INDEX IF NOT EXISTS idx_seo_keywords_keyword ON seo_keywords(keyword);
        CREATE INDEX IF NOT EXISTS idx_seo_keywords_page_id ON seo_keywords(page_id);
        CREATE INDEX IF NOT EXISTS idx_seo_analytics_page_id ON seo_analytics(page_id);
        CREATE INDEX IF NOT EXISTS idx_seo_analytics_date ON seo_analytics(date);
        CREATE INDEX IF NOT EXISTS idx_seo_tasks_status ON seo_tasks(status);
        CREATE INDEX IF NOT EXISTS idx_seo_tasks_type ON seo_tasks(task_type);
        """
        
        await self.render_conn.execute(seo_tables)
        logger.info("  SEO tables created")

    async def _create_enhanced_tables(self):
        """Create enhanced tables for new features"""
        logger.info("  Creating enhanced feature tables...")
        
        enhanced_tables = """
        -- Enhanced user profiles
        CREATE TABLE IF NOT EXISTS user_profiles (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id uuid REFERENCES users(id) ON DELETE CASCADE,
            bio text,
            skills text[],
            experience_years integer DEFAULT 0,
            linkedin_url text,
            github_url text,
            portfolio_url text,
            location text,
            salary_expectation integer,
            job_types text[],
            industries text[],
            preferences jsonb DEFAULT '{}',
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        );

        -- Job recommendations
        CREATE TABLE IF NOT EXISTS job_recommendations (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id uuid REFERENCES users(id) ON DELETE CASCADE,
            job_id uuid REFERENCES jobs(id) ON DELETE CASCADE,
            score real NOT NULL,
            reasons text[],
            status text DEFAULT 'pending',
            created_at timestamptz NOT NULL DEFAULT now()
        );

        -- Application analytics
        CREATE TABLE IF NOT EXISTS application_analytics (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            application_id uuid REFERENCES applications(id) ON DELETE CASCADE,
            event_type text NOT NULL,
            event_data jsonb DEFAULT '{}',
            timestamp timestamptz NOT NULL DEFAULT now()
        );

        -- System metrics
        CREATE TABLE IF NOT EXISTS system_metrics (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            metric_name text NOT NULL,
            metric_value real NOT NULL,
            tags jsonb DEFAULT '{}',
            timestamp timestamptz NOT NULL DEFAULT now()
        );

        -- Indexes for enhanced tables
        CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
        CREATE INDEX IF NOT EXISTS idx_job_recommendations_user_id ON job_recommendations(user_id);
        CREATE INDEX IF NOT EXISTS idx_job_recommendations_score ON job_recommendations(score);
        CREATE INDEX IF NOT EXISTS idx_application_analytics_app_id ON application_analytics(application_id);
        CREATE INDEX IF NOT EXISTS idx_system_metrics_name ON system_metrics(metric_name);
        CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(timestamp);
        """
        
        await self.render_conn.execute(enhanced_tables)
        logger.info("  Enhancd tables created")

    async def migrate_all_data(self):
        """Migrate all data from Supabase to Render"""
        logger.info("📦 Migrating all data...")
        
        if not self.supabase_conn:
            logger.warning("⚠️ No Supabase connection, skipping data migration")
            return True
        
        # List of tables to migrate (in dependency order)
        tables = [
            'users',
            'profiles', 
            'jobs',
            'applications',
            'application_inputs',
            'events',
            'answer_memory'
        ]
        
        try:
            for table_name in tables:
                logger.info(f"📦 Migrating {table_name}...")
                await self._migrate_table(table_name)
            
            logger.info("✅ All data migrated successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Data migration failed: {e}")
            return False

    async def _migrate_table(self, table_name: str):
        """Migrate a single table"""
        try:
            # Get data from Supabase
            supabase_data = await self.supabase_conn.fetch(f"SELECT * FROM {table_name}")
            
            if not supabase_data:
                logger.info(f"   No data in {table_name}")
                return
            
            # Get column information
            if supabase_data:
                columns = list(supabase_data[0].keys())
                columns_str = ', '.join(columns)
                placeholders = ', '.join([f'${i+1}' for i in range(len(columns))])
                
                # Insert into Render
                insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                
                for row in supabase_data:
                    values = [dict(row).get(col) for col in columns]
                    await self.render_conn.execute(insert_query, *values)
                
                logger.info(f"   ✅ Migrated {len(supabase_data)} rows from {table_name}")
            
        except Exception as e:
            logger.error(f"   ❌ Failed to migrate {table_name}: {e}")
            raise

    async def create_standalone_users(self):
        """Create standalone users table for Render"""
        logger.info("👥 Creating standalone users table...")
        
        users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            email       text UNIQUE NOT NULL,
            full_name   text,
            avatar_url  text,
            created_at  timestamptz NOT NULL DEFAULT now(),
            updated_at  timestamptz NOT NULL DEFAULT now()
        );
        
        CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
        
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS trigger AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        
        CREATE TRIGGER trg_users_updated_at
            BEFORE UPDATE ON users
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();
        """
        
        await self.render_conn.execute(users_table)
        logger.info("  Standalone users table created")

    async def update_environment_config(self, database_url: str):
        """Update environment configuration files"""
        logger.info("⚙️ Updating environment configuration...")
        
        try:
            # Update .env file
            env_file = Path(".env")
            if env_file.exists():
                with open(env_file, 'r') as f:
                    content = f.read()
                
                # Update DATABASE_URL and remove Supabase references
                lines = content.split('\n')
                new_lines = []
                
                for line in lines:
                    if line.startswith('DATABASE_URL='):
                        new_lines.append(f'DATABASE_URL={database_url}')
                    elif line.startswith('SUPABASE_'):
                        continue  # Remove Supabase lines
                    else:
                        new_lines.append(line)
                
                with open(env_file, 'w') as f:
                    f.write('\n'.join(new_lines))
                
                logger.info("✅ .env file updated")
            
            # Create Render environment file
            render_env_content = f"""# Render Environment Configuration
DATABASE_URL={database_url}
ENV=prod
AGENT_ENABLED=true
LOG_JSON=true
LOG_LEVEL=INFO

# LLM Configuration
LLM_API_BASE=https://openrouter.ai/api/v1
LLM_API_KEY=your-api-key
LLM_MODEL=anthropic/claude-3.5-sonnet

# SEO Automation
SEO_ENABLED=true
SEO_CRON_SCHEDULE=0 2 * * *
SEO_BATCH_SIZE=50

# Other services (keep existing values)
"""
            
            with open(".env.render", 'w') as f:
                f.write(render_env_content)
            
            logger.info("✅ Render environment configuration created")
            return True
            
        except Exception as e:
            logger.error(f"❌ Environment update failed: {e}")
            return False

    async def setup_seo_automation(self):
        """Setup SEO automation on the new database"""
        logger.info("  Setting up SEO automation...")
        
        try:
            # Create SEO automation functions
            seo_functions = """
            -- SEO page generation function
            CREATE OR REPLACE FUNCTION generate_seo_page(
                page_path text,
                page_title text,
                page_description text,
                keywords text[] DEFAULT '{}'
            ) RETURNS uuid AS $$
            DECLARE
                page_id uuid;
            BEGIN
                INSERT INTO seo_pages (path, title, description, keywords, last_generated)
                VALUES (page_path, page_title, page_description, keywords, now())
                RETURNING id INTO page_id;
                
                RETURN page_id;
            END;
            $$ LANGUAGE plpgsql;

            -- SEO analytics tracking function
            CREATE OR REPLACE FUNCTION track_seo_metric(
                page_path text,
                metric_name text,
                metric_value real,
                metric_date date DEFAULT CURRENT_DATE
            ) RETURNS void AS $$
            BEGIN
                INSERT INTO seo_analytics (page_id, metric_name, metric_value, date)
                SELECT id, metric_name, metric_value, metric_date
                FROM seo_pages
                WHERE path = page_path;
            END;
            $$ LANGUAGE plpgsql;

            -- SEO task scheduler function
            CREATE OR REPLACE FUNCTION schedule_seo_task(
                task_type text,
                task_data jsonb DEFAULT '{}',
                scheduled_at timestamptz DEFAULT now()
            ) RETURNS uuid AS $$
            DECLARE
                task_id uuid;
            BEGIN
                INSERT INTO seo_tasks (task_type, data, scheduled_at)
                VALUES (task_type, task_data, scheduled_at)
                RETURNING id INTO task_id;
                
                RETURN task_id;
            END;
            $$ LANGUAGE plpgsql;
            """
            
            await self.render_conn.execute(seo_functions)
            logger.info("  SEO automation functions created")
            
            # Seed initial SEO data
            await self._seed_seo_data()
            
            logger.info("  SEO automation setup complete")
            return True
            
        except Exception as e:
            logger.error(f"  SEO automation setup failed: {e}")
            return False

    async def _seed_seo_data(self):
        """Seed initial SEO data"""
        logger.info("  Seeding initial SEO data...")
        
        seed_data = """
        -- Insert core pages
        INSERT INTO seo_pages (path, title, description, keywords) VALUES
        ('/', 'JobHuntin - AI-Powered Job Application Automation', 'Automate your job applications with AI-powered resume optimization and intelligent form filling.', '{"job search", "AI automation", "resume optimization", "job applications"}'),
        ('/pricing', 'Pricing Plans - JobHuntin', 'Choose the perfect pricing plan for your job search needs. Free, Pro, and Enterprise options available.', '{"pricing", "plans", "cost", "subscription"}'),
        ('/about', 'About JobHuntin', 'Learn about JobHuntin''s mission to revolutionize job searching with AI technology.', '{"about", "company", "mission", "team"}'),
        ('/contact', 'Contact JobHuntin', 'Get in touch with the JobHuntin team for support, questions, or feedback.', '{"contact", "support", "help", "feedback"}')
        ON CONFLICT (path) DO NOTHING;

        -- Insert initial keywords
        INSERT INTO seo_keywords (keyword, volume, difficulty, intent, page_id) 
        SELECT 
            unnest(ARRAY['job search automation', 'AI resume builder', 'automatic job applications', 'job search tools']),
            unnest(ARRAY[10000, 8000, 5000, 12000]),
            unnest(ARRAY[0.7, 0.6, 0.8, 0.5]),
            unnest(ARRAY['commercial', 'informational', 'transactional', 'informational']),
            id
        FROM seo_pages 
        WHERE path = '/'
        ON CONFLICT DO NOTHING;
        """
        
        await self.render_conn.execute(seed_data)
        logger.info("  SEO data seeded")

    async def run_complete_migration(self, database_url: str):
        """Run the complete migration process"""
        logger.info("  Starting complete migration to paid database...")
        
        try:
            # Connect to databases
            if not await self.connect_to_render(database_url):
                return False
            
            # await self.connect_to_supabase()  # Optional, for data migration
            
            # Wipe existing schema to ensure fresh start
            logger.info("  Wiping existing schema...")
            await self.render_conn.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO postgres; GRANT ALL ON SCHEMA public TO public;")
            logger.info("  Schema wiped")

            # Create complete schema
            if not await self.create_complete_schema():
                return False
            
            # Create standalone users table
            # await self.create_standalone_users()
            
            # Migrate all data
            # await self.migrate_all_data()
            
            # Setup SEO automation
            if not await self.setup_seo_automation():
                return False
            
            # Update environment configuration
            # if not await self.update_environment_config(database_url):
            #     return False
            
            logger.info("  Complete migration successful!")
            return True
            
        except Exception as e:
            logger.error(f"  Migration failed: {e}")
            return False
        
        finally:
            # Close connections
            if self.render_conn:
                await self.render_conn.close()
            if self.supabase_conn:
                await self.supabase_conn.close()

async def main():
    """Main migration function"""
    if len(sys.argv) != 2:
        print("Usage: python complete_migration.py <render_database_url>")
        print("Example: python complete_migration.py postgresql://user:pass@host:5432/dbname")
        sys.exit(1)
    
    database_url = sys.argv[1]
    
    migrator = CompleteMigrator()
    success = await migrator.run_complete_migration(database_url)
    
    if success:
        print("\n  COMPLETE MIGRATION SUCCESSFUL!")
        print("\n=== NEXT STEPS ===")
        print("1. Test the application locally")
        print("2. Update Render service environment variables")
        print("3. Deploy to Render")
        print("4. Verify SEO automation is working")
        print("5. Monitor system performance")
        sys.exit(0)
    else:
        print("\n  Migration failed. Check the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
