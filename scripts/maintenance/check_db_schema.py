import asyncio
import asyncpg
import os
import json
from dotenv import load_dotenv

load_dotenv()

async def check_db():
    # Try multiple common env var names
    db_url = os.environ.get('DATABASE_URL') or os.environ.get('SUPABASE_DB_URL')
    
    if not db_url:
        print("Error: No database URL found in environment variables.")
        return

    # Handle common connection issues like local DNS or missing port
    print(f"Connecting to: {db_url.split('@')[-1]}")
    
    try:
        # Use a longer timeout for remote connections
        conn = await asyncio.wait_for(asyncpg.connect(db_url), timeout=10.0)
        
        # Check columns in applications table
        columns = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = 'applications'
            ORDER BY column_name
        """)
        
        print('--- Columns in applications ---')
        for col in columns:
            print(f"{col['column_name']}: {col['data_type']}")
        
        # Check function definition
        func = await conn.fetchval("""
            SELECT pg_get_functiondef(p.oid)
            FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            WHERE n.nspname = 'public' AND p.proname = 'claim_next_prioritized'
        """)
        
        print('\n--- Function claim_next_prioritized ---')
        if func:
            print(func)
        else:
            print("Function not found!")
            
        await conn.close()
    except asyncio.TimeoutError:
        print("Error: Connection timed out. Is the DB reachable?")
    except Exception as e:
        print(f"Error connecting to DB: {e}")
        # If DNS fails, try to print the hostname we tried to reach
        import socket
        try:
            hostname = db_url.split('@')[-1].split(':')[0].split('/')[0]
            print(f"Attempting to resolve hostname: {hostname}")
            ip = socket.gethostbyname(hostname)
            print(f"Resolved to IP: {ip}")
        except Exception as dns_err:
            print(f"DNS resolution failed: {dns_err}")

if __name__ == '__main__':
    asyncio.run(check_db())
