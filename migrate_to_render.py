#!/usr/bin/env python3
"""
Migration script: Supabase to Render PostgreSQL
Handles schema migration and data transfer.
"""

import asyncio
import asyncpg
import os
import sys
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from packages.shared.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    def __init__(self):
        self.settings = get_settings()
        self.supabase_conn = None
        self.render_conn = None

    async def connect_supabase(self):
        """Connect to Supabase database."""
        try:
            self.supabase_conn = await asyncpg.connect(
                self.settings.database_url,
                server_settings={'application_name': 'migration_supabase'}
            )
            logger.info("Connected to Supabase database")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            raise

    async def connect_render(self, render_url: str):
        """Connect to Render PostgreSQL database."""
        try:
            self.render_conn = await asyncpg.connect(
                render_url,
                server_settings={'application_name': 'migration_render'}
            )
            logger.info("Connected to Render database")
        except Exception as e:
            logger.error(f"Failed to connect to Render: {e}")
            raise

    async def create_render_schema(self):
        """Create database schema on Render."""
        logger.info("Creating database schema on Render...")
        
        schema_file = project_root / "infra" / "supabase" / "schema.sql"
        if not schema_file.exists():
            logger.error(f"Schema file not found: {schema_file}")
            raise FileNotFoundError(f"Schema file not found: {schema_file}")

        with open(schema_file, 'r') as f:
            schema_sql = f.read()

        # Remove Supabase-specific parts
        schema_sql = self._clean_schema_for_render(schema_sql)
        
        await self.render_conn.execute(schema_sql)
        logger.info("Schema created successfully on Render")

    def _clean_schema_for_render(self, schema_sql: str) -> str:
        """Remove Supabase-specific elements from schema."""
        # Remove auth.users references (Render doesn't have Supabase auth)
        schema_sql = schema_sql.replace("REFERENCES auth.users (id)", "")
        
        # Remove Supabase realtime publications
        lines = schema_sql.split('\n')
        cleaned_lines = []
        skip_next = False
        
        for line in lines:
            if 'ALTER PUBLICATION supabase_realtime' in line:
                skip_next = True
                continue
            if skip_next and line.strip() == ';':
                skip_next = False
                continue
            if not skip_next:
                cleaned_lines.append(line)
        
        # Remove RLS policies (Render doesn't have Supabase RLS)
        cleaned_sql = '\n'.join(cleaned_lines)
        cleaned_sql = cleaned_sql.split('-- Row-Level Security')[0]
        
        return cleaned_sql

    async def migrate_table_data(self, table_name: str):
        """Migrate data from Supabase table to Render table."""
        logger.info(f"Migrating data from {table_name}...")
        
        try:
            # Get data from Supabase
            supabase_data = await self.supabase_conn.fetch(f"SELECT * FROM {table_name}")
            
            if not supabase_data:
                logger.info(f"No data found in {table_name}")
                return
            
            # Insert into Render
            columns = [col.name for col in supabase_data[0].columns]
            columns_str = ', '.join(columns)
            placeholders = ', '.join([f'${i+1}' for i in range(len(columns))])
            
            insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
            
            for row in supabase_data:
                values = [getattr(row, col) for col in columns]
                await self.render_conn.execute(insert_query, *values)
            
            logger.info(f"Migrated {len(supabase_data)} rows from {table_name}")
            
        except Exception as e:
            logger.error(f"Failed to migrate {table_name}: {e}")
            raise

    async def create_users_table_standalone(self):
        """Create standalone users table for Render (without auth.users dependency)."""
        logger.info("Creating standalone users table for Render...")
        
        await self.render_conn.execute("""
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
        """)
        
        logger.info("Standalone users table created")

    async def run_full_migration(self, render_url: str):
        """Run complete migration from Supabase to Render."""
        try:
            # Connect to both databases
            await self.connect_supabase()
            await self.connect_render(render_url)
            
            # Create schema (modified for Render)
            await self.create_render_schema()
            
            # Create standalone users table
            await self.create_users_table_standalone()
            
            # List of tables to migrate (in order of dependencies)
            tables = [
                'users',
                'profiles', 
                'jobs',
                'applications',
                'application_inputs'
            ]
            
            # Migrate data for each table
            for table in tables:
                await self.migrate_table_data(table)
            
            logger.info("Migration completed successfully!")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
        finally:
            # Close connections
            if self.supabase_conn:
                await self.supabase_conn.close()
            if self.render_conn:
                await self.render_conn.close()

async def main():
    """Main migration function."""
    if len(sys.argv) != 2:
        print("Usage: python migrate_to_render.py <render_database_url>")
        sys.exit(1)
    
    render_url = sys.argv[1]
    
    migrator = DatabaseMigrator()
    await migrator.run_full_migration(render_url)

if __name__ == "__main__":
    asyncio.run(main())
