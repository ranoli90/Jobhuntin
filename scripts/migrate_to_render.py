#!/usr/bin/env python3
"""
Script to migrate data from Supabase to Render PostgreSQL database
"""
import os
import asyncpg
from dotenv import load_dotenv

async def migrate_data():
    # Load environment variables
    load_dotenv()
    
    # Source (Supabase)
    supabase_url = os.getenv('SUPABASE_URL')
    
    # Destination (Render)
    render_url = os.getenv('RENDER_DB_URL')
    
    if not supabase_url or not render_url:
        print("Error: Missing database URLs in environment")
        return
    
    try:
        # Connect to both databases
        print("Connecting to databases...")
        src_pool = await asyncpg.create_pool(supabase_url)
        dst_pool = await asyncpg.create_pool(render_url)
        
        async with src_pool.acquire() as src_conn, dst_pool.acquire() as dst_conn:
            print("Starting data migration...")
            
            # Get list of tables to migrate
            tables = await src_conn.fetch(
                """SELECT table_name FROM information_schema.tables 
                   WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"""
            )
            
            for table in tables:
                table_name = table['table_name']
                print(f"Migrating table: {table_name}")
                
                # Get all data from source table
                data = await src_conn.fetch(f"SELECT * FROM {table_name}")
                
                if not data:
                    continue
                
                # Get column names
                columns = list(data[0].keys())
                
                # Create table in destination if not exists
                await dst_conn.execute(
                    f"""CREATE TABLE IF NOT EXISTS {table_name} (
                       {', '.join(f'{col} TEXT' for col in columns)}
                    )"""
                )
                
                # Insert data
                for row in data:
                    values = [row[col] for col in columns]
                    await dst_conn.execute(
                        f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(f'${i+1}' for i in range(len(values)))})",
                        *values
                    )
                
            print("Data migration completed successfully!")
    
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        if 'src_pool' in locals():
            await src_pool.close()
        if 'dst_pool' in locals():
            await dst_pool.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(migrate_data())
