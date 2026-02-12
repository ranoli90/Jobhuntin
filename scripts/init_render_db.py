#!/usr/bin/env python3
"""
Initialize fresh database schema on Render
"""
import asyncpg
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_schema(conn):
    """Initialize database schema"""
    # Get schema from file
    schema_file = Path(__file__).parent.parent / "infra" / "supabase" / "schema.sql"
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")
    
    schema_sql = schema_file.read_text()
    
    # Remove Supabase-specific elements
    schema_sql = schema_sql.replace("REFERENCES auth.users (id)", "")
    schema_sql = schema_sql.split("-- Row-Level Security")[0]
    
    # Execute schema
    await conn.execute(schema_sql)
    logger.info("Database schema initialized")

async def main():
    """Main execution"""
    if len(sys.argv) < 2:
        logger.error("Usage: python init_render_db.py <database_url>")
        return
    
    db_url = sys.argv[1]
    
    try:
        conn = await asyncpg.connect(db_url)
        try:
            await init_schema(conn)
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Failed to initialize schema: {e}")
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
