#!/usr/bin/env python3
"""Check JobSpy sync status from database."""

import asyncio
import os
import ssl
import sys

async def check_jobspy_status():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        # Try Render database URL
        database_url = os.environ.get("RENDER_DATABASE_URL")
    
    if not database_url:
        print("ERROR: DATABASE_URL or RENDER_DATABASE_URL not set")
        sys.exit(1)
    
    # Create SSL context for Render PostgreSQL
    if "localhost" in database_url or "127.0.0.1" in database_url:
        ssl_context = False
    else:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
    
    import asyncpg
    conn = await asyncpg.connect(database_url, statement_cache_size=0, ssl=ssl_context)
    
    try:
        print("=" * 70)
        print("JOB SYNC STATUS FROM DATABASE")
        print("=" * 70)
        
        # Get sync configs
        configs = await conn.fetch("SELECT * FROM public.job_sync_config ORDER BY source")
        print("\n[Sync Configuration]")
        for c in configs:
            print(f"  {c['source']}: enabled={c['is_enabled']}, last_synced={c['last_synced_at']}")
        
        # Get recent runs (last 24 hours)
        recent_runs = await conn.fetch("""
            SELECT source, status, jobs_fetched, jobs_new, jobs_updated, 
                   jobs_skipped, duration_ms, started_at, completed_at, errors
            FROM public.job_sync_runs
            WHERE started_at > now() - interval '24 hours'
            ORDER BY started_at DESC
        """)
        
        print(f"\n[Recent Runs - Last 24 Hours] ({len(recent_runs)} runs)")
        
        if not recent_runs:
            print("  No recent runs found")
        else:
            for run in recent_runs:
                print(f"\n  Source: {run['source']}")
                print(f"    Status: {run['status']}")
                print(f"    Started: {run['started_at']}")
                print(f"    Completed: {run['completed_at']}")
                print(f"    Jobs: fetched={run['jobs_fetched']}, new={run['jobs_new']}, updated={run['jobs_updated']}, skipped={run['jobs_skipped']}")
                print(f"    Duration: {run['duration_ms']}ms")
                
                errors = run.get('errors')
                if errors:
                    print(f"    Errors: {errors}")
        
        # Get aggregated stats
        print("\n[Aggregated Stats - Last 24 Hours]")
        stats = await conn.fetch("""
            SELECT source, 
                   count(*) as run_count,
                   sum(jobs_fetched) as total_fetched,
                   sum(jobs_new) as total_new,
                   sum(jobs_updated) as total_updated,
                   sum(duration_ms) as total_duration_ms
            FROM public.job_sync_runs
            WHERE started_at > now() - interval '24 hours'
            GROUP BY source
            ORDER BY source
        """)
        
        for stat in stats:
            print(f"  {stat['source']}:")
            print(f"    Runs: {stat['run_count']}")
            print(f"    Total Jobs: fetched={stat['total_fetched']}, new={stat['total_new']}, updated={stat['total_updated']}")
            print(f"    Total Duration: {stat['total_duration_ms']}ms")
        
        # Check for failed runs
        failed_runs = await conn.fetch("""
            SELECT source, status, started_at, errors
            FROM public.job_sync_runs
            WHERE status = 'failed' AND started_at > now() - interval '24 hours'
            ORDER BY started_at DESC
        """)
        
        print(f"\n[Failed Runs] ({len(failed_runs)} failures)")
        for run in failed_runs:
            print(f"  {run['source']} at {run['started_at']}: {run['errors']}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_jobspy_status())
