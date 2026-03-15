"""
Database Statistics Endpoints for Phase 15.1 Database & Performance
"""

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from apps.api.dependencies import get_current_user, get_db_pool, get_tenant_id
from packages.backend.domain.cache_manager import CacheManager
from packages.backend.domain.connection_pool_manager import ConnectionPoolManager
from packages.backend.domain.database_performance_manager import (
    create_database_performance_manager,
)
from packages.backend.domain.index_analyzer import create_index_analyzer
from packages.backend.domain.performance_monitor import create_performance_monitor
from shared.logging_config import get_logger

logger = get_logger("sorce.database_stats_endpoints")
router = APIRouter(prefix="/database-stats", tags=["database-stats"])


@router.get("/tables")
async def get_database_tables(
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get database tables information."""
    try:
        # Create database performance manager
        db_manager = create_database_performance_manager(db_pool)

        # Get database statistics
        db_stats = await db_manager.get_database_statistics()

        # Get table list. Use pg_class.reltuples for row count (approximate but fast);
        # dynamic "FROM tablename" cannot be parameterized and was invalid SQL.
        query = """
            SELECT
                t.schemaname,
                t.tablename,
                'table' as table_type,
                pg_size_pretty(pg_total_relation_size(t.schemaname||'.'||t.tablename)) as size,
                pg_total_relation_size(t.schemaname||'.'||t.tablename) as size_bytes,
                COALESCE(c.reltuples::bigint, 0) as row_count
            FROM pg_tables t
            LEFT JOIN pg_namespace n ON n.nspname = t.schemaname
            LEFT JOIN pg_class c ON c.relname = t.tablename AND c.relnamespace = n.oid AND c.relkind = 'r'
            WHERE t.schemaname NOT IN ('information_schema', 'pg_catalog')
            ORDER BY t.schemaname, t.tablename
        """

        async with db_pool.acquire() as conn:
            results = await conn.fetch(query)

            tables = []
            for row in results:
                tables.append(
                    {
                        "schema_name": row[0],
                        "table_name": row[1],
                        "table_type": row[2],
                        "size": row[3],
                        "size_bytes": int(row[4]) if row[4] else 0,
                        "row_count": int(row[5]) if row[5] else 0,
                    }
                )

        return {
            "database_stats": db_stats,
            "tables": tables,
            "total_tables": len(tables),
            "total_size_mb": sum(t["size_bytes"] for t in tables) / (1024 * 1024),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get database tables: {str(e)}"
        )


@router.get("/tables/{table_name}")
async def get_table_details(
    table_name: str,
    include_statistics: bool = True,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, any]:
    """Get detailed table information."""
    try:
        # SECURITY: Validate table_name to prevent SQL injection
        if not _TABLE_NAME_RE.match(table_name):
            raise HTTPException(
                status_code=400,
                detail="Invalid table_name: must match ^[a-zA-Z_][a-zA-Z0-9_]*$",
            )
        # Create database performance manager
        db_manager = create_database_performance_manager(db_pool)

        # Get table statistics
        table_stats = await db_manager.get_table_statistics(table_name)

        # Get column information
        columns_query = """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length,
                numeric_precision,
                ordinal_position
            FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = $1
            ORDER BY ordinal_position
        """

        async with db_pool.acquire() as conn:
            results = await conn.fetch(columns_query, table_name)

            columns = []
            for row in results:
                columns.append(
                    {
                        "column_name": row[0],
                        "data_type": row[1],
                        "is_nullable": row[2],
                        "column_default": row[3],
                        "character_maximum_length": row[4],
                        "numeric_precision": row[5],
                        "ordinal_position": row[6],
                    }
                )

        # Get index information
        indexes_query = """
            SELECT
                indexname,
                indexdef,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch,
                pg_size_pretty(pg_relation_size(indexrelid::regclass)) as size,
                pg_relation_size(indexrelid::regclass) as size_bytes
            FROM pg_indexes
                WHERE schemaname = 'public' AND tablename = $1
            ORDER BY indexname
        """

        async with db_pool.acquire() as conn:
            index_results = await conn.fetch(indexes_query, table_name)

            indexes = []
            for row in index_results:
                indexes.append(
                    {
                        "index_name": row[0],
                        "definition": row[1],
                        "scans": int(row[2]) if row[2] else 0,
                        "tuples_read": int(row[3]) if row[3] else 0,
                        "tuples_returned": int(row[4]) if row[4] else 0,
                        "size": row[5],
                        "size_bytes": int(row[6]) if row[6] else 0,
                    }
                )

        # Get constraints
        constraints_query = """
            SELECT
                constraint_name,
                constraint_type,
                check_clause
            FROM information_schema.table_constraints
            WHERE table_schema = 'public' AND table_name = $1
            ORDER BY constraint_name
        """

        async with db_pool.acquire() as conn:
            constraint_results = await conn.fetch(constraints_query, table_name)

            constraints = []
            for row in constraint_results:
                constraints.append(
                    {
                        "constraint_name": row[0],
                        "constraint_type": row[1],
                        "check_clause": row[2],
                    }
                )

        return {
            "table_name": table_name,
            "statistics": table_stats,
            "columns": columns,
            "indexes": indexes,
            "constraints": constraints,
            "total_columns": len(columns),
            "total_indexes": len(indexes),
            "total_constraints": len(constraints),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get table details: {str(e)}"
        )


@router.get("/query-statistics")
async def get_query_statistics(
    time_period_hours: int = Query(default=1, ge=1, le=168),
    limit: int = Query(default=100, ge=1, le=1000),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get query performance statistics."""
    try:
        # Get query statistics from pg_stat_statements
        query = """
            SELECT
                query,
                calls,
                total_exec_time,
                mean_exec_time,
                std_exec_time,
                total_plan_time,
                rows,
                shared_blks_hit,
                shared_blks_read,
                local_blks_hit,
                local_blks_read,
                temp_blks_read,
                temp_blks_written
            FROM pg_stat_statements
            ORDER BY total_exec_time DESC
            LIMIT $1
        """

        async with db_pool.acquire() as conn:
            results = await conn.fetch(query, limit)

            query_stats = []
            for row in results:
                query_stats.append(
                    {
                        "query": row[0][:200] + "..." if len(row[0]) else row[0],
                        "calls": int(row[1]) if row[1] else 0,
                        "total_exec_time": float(row[2]) if row[2] else 0,
                        "mean_exec_time": float(row[3]) if row[3] else 0,
                        "std_exec_time": float(row[4]) if row[4] else 0,
                        "total_plan_time": float(row[5]) if row[5] else 0,
                        "rows": int(row[6]) if row[6] else 0,
                        "shared_blks_hit": int(row[7]) if row[7] else 0,
                        "shared_blks_read": int(row[8]) if row[8] else 0,
                        "local_blks_hit": int(row[9]) if row[9] else 0,
                        "local_blks_read": int(row[10]) if row[10] else 0,
                        "temp_blks_read": int(row[11]) if row[11] else 0,
                        "temp_blks_written": int(row[12]) if row[12] else 0,
                    }
                )

            return {
                "query_statistics": query_stats,
                "total_queries": len(query_stats),
                "period_hours": time_period_hours,
                "avg_execution_time": sum(q["mean_exec_time"] for q in query_stats)
                / len(query_stats)
                if query_stats
                else 1,
                "avg_rows_returned": sum(q["rows"] for q in query_stats)
                / len(query_stats)
                if query_stats
                else 1,
            }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get query statistics: {str(e)}"
        )


@router.get("/index-statistics")
async def get_index_statistics(
    time_period_hours: int = Query(default=24, ge=1, le=168),
    limit: int = Query(default=50, ge=1, le=500),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get index performance statistics."""
    try:
        # Get index statistics from pg_stat_user_indexes
        query = """
            SELECT
                schemaname,
                tablename,
                indexname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch,
                    pg_size_pretty(pg_relation_size(indexrelid::regclass)) as size,
                    pg_relation_size(indexrelid::regclass) as size_bytes
            FROM pg_stat_user_indexes
            WHERE schemaname = 'public'
            ORDER BY idx_scan DESC
            LIMIT $1
        """

        async with db_pool.acquire() as conn:
            results = await conn.fetch(query, limit)

            index_stats = []
            for row in results:
                index_stats.append(
                    {
                        "schema_name": row[0],
                        "table_name": row[1],
                        "index_name": row[2],
                        "scans": int(row[3]) if row[3] else 0,
                        "tuples_read": int(row[4]) if row[4] else 0,
                        "tuples_returned": int(row[5]) if row[5] else 0,
                        "size": row[6],
                        "size_bytes": int(row[7]) if row[7] else 0,
                    }
                )

            return {
                "index_statistics": index_stats,
                "total_indexes": len(index_stats),
                "period_hours": time_period_hours,
                "total_scans": sum(idx["scans"] for idx in index_stats),
                "total_reads": sum(idx["tuples_read"] for idx in index_stats),
                "total_returns": sum(idx["tuples_returned"] for idx in index_stats),
                "total_size_mb": sum(idx["size_bytes"] for idx in index_stats)
                / (1024 * 1024),
            }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get index statistics: {str(e)}"
        )


@router.get("/database-size")
async def get_database_size(
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get database size information."""
    try:
        # Get database size
        size_query = """
            SELECT
                pg_size_pretty(pg_database_size()) as database_size,
                pg_database_size() as database_size_bytes,
                pg_size_pretty(pg_total_relation_size()) as total_relation_size,
                pg_size_pretty(pg_indexes_size()) as indexes_size,
                pg_size_pretty(pg_toast_size()) as toast_size
            """

        async with db_pool.acquire() as conn:
            result = await conn.fetchrow(size_query)

            return {
                "database_size": result[0],
                "database_size_bytes": result[1],
                "total_relation_size": result[2],
                "indexes_size": result[3],
                "toast_size": result[4],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get database size: {str(e)}"
        )


@router.get("/table/{table_name}/size")
async def get_table_size(
    table_name: str,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get table size information."""
    try:
        # SECURITY: Validate table_name to prevent SQL injection
        if not _TABLE_NAME_RE.match(table_name):
            raise HTTPException(
                status_code=400,
                detail="Invalid table_name: must match ^[a-zA-Z_][a-zA-Z0-9_]*$",
            )
        # Table names cannot be parameterized in FROM; use regclass for size and
        # pg_class.reltuples for approximate row count (avoids dynamic SQL).
        qualified = f"public.{table_name}"
        size_query = """
            SELECT
                pg_size_pretty(pg_total_relation_size($1::regclass)) as size,
                pg_total_relation_size($1::regclass) as size_bytes,
                (SELECT reltuples::bigint FROM pg_class c
                 JOIN pg_namespace n ON n.oid = c.relnamespace
                 WHERE n.nspname = 'public' AND c.relname = $2 AND c.relkind = 'r') as row_count
        """

        async with db_pool.acquire() as conn:
            result = await conn.fetchrow(size_query, qualified, table_name)

            return {
                "table_name": table_name,
                "size": result[0],
                "size_bytes": int(result[1]) if result[1] else 0,
                "row_count": int(result[2]) if result[2] else 0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get table size: {str(e)}"
        )


@router.get("/performance-report")
async def get_performance_report(
    time_period_hours: int = Query(default=24, ge=1, le=168),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get comprehensive performance report."""
    try:
        # Create database performance manager
        db_manager = create_database_performance_manager(db_pool)

        # Get performance report
        report = await db_manager.get_performance_dashboard(
            tenant_id=tenant_id,
            time_period_hours=time_period_hours,
        )

        return report

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get performance report: {str(e)}"
        )


@router.get("/activity-log")
async def get_activity_log(
    time_period_hours: int = Query(default=24, ge=1, le=168),
    limit: int = Query(default=100, ge=1, le=1000),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get database activity log."""
    try:
        # Get recent activity from pg_stat_activity.
        # Use make_interval for parameterized interval; pg_stat_activity has no "timestamp" column.
        query = """
            SELECT
                pid,
                state,
                query_start,
                state_change,
                wait_event_type,
                query,
                wait_event,
                client_addr,
                backend_start,
                xact_start,
                query_id,
                backend_xact_start,
                backend_xact_end,
                query_hash,
                query_plan,
                state_change
            FROM pg_stat_activity
            WHERE state_change > NOW() - make_interval(hours => $1::int)
            ORDER BY state_change DESC NULLS LAST
            LIMIT $2
        """

        async with db_pool.acquire() as conn:
            results = await conn.fetch(query, time_period_hours, limit)

            activities = []
            for row in results:
                activities.append(
                    {
                        "pid": row[0],
                        "state": row[1],
                        "query_start": row[2],
                        "state_change": row[3],
                        "wait_event_type": row[4],
                        "query": row[5],
                        "wait_event": row[6],
                        "client_addr": row[7],
                        "backend_start": row[8],
                        "xact_start": row[9],
                        "query_id": row[10],
                        "backend_xact_start": row[11],
                        "backend_xact_end": row[12],
                        "query_hash": row[13],
                        "query_plan": row[14],
                        "last_state_change": row[15].isoformat() if row[15] else None,
                    }
                )

            return {
                "activities": activities,
                "total_activities": len(activities),
                "period_hours": time_period_hours,
            }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get activity log: {str(e)}"
        )


@router.get("/locks")
async def get_lock_status(
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
    transaction_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Get current lock status."""
    try:
        # Get lock information
        query = """
            SELECT
                locktype,
                mode,
                relation,
                page,
                tupleid,
                virtualxid,
                transactionid,
                pid,
                mode,
                granted,
                fastpath,
                wait_start,
                locktime
            FROM pg_locks
        """

        if transaction_id:
            query += " WHERE transactionid = $1"
        async with db_pool.acquire() as conn:
            results = (
                await conn.fetch(query, transaction_id)
                if transaction_id
                else await conn.fetch(query)
            )

            locks = []
            for row in results:
                locks.append(
                    {
                        "lock_type": row[0],
                        "mode": row[1],
                        "relation": row[2],
                        "page": row[3],
                        "tupleid": row[4],
                        "virtualxid": row[5],
                        "transactionid": row[6],
                        "pid": row[7],
                        "granted": row[8],
                        "fastpath": row[9],
                        "wait_start": row[10].isoformat() if row[10] else None,
                        "locktime": row[11],
                    }
                )

            return {
                "locks": locks,
                "total_locks": len(locks),
                "transaction_id": transaction_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get lock status: {str(e)}"
        )


_TABLE_NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


@router.post("/vacuum-analyze")
async def analyze_vacuum_requirements(
    table_name: Optional[str] = None,
    analyze_all: bool = False,
    dry_run: bool = True,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Analyze VACUUM requirements and generate recommendations."""
    try:
        if table_name is not None and not _TABLE_NAME_RE.match(table_name):
            raise HTTPException(
                status_code=400,
                detail="Invalid table_name: must match ^[a-zA-Z_][a-zA-Z0-9_]*$",
            )
        # Get VACUUM statistics
        vacuum_stats = await _get_vacuum_statistics(db_pool, table_name, analyze_all)

        # Generate recommendations
        recommendations = _generate_vacuum_recommendations(vacuum_stats)

        return {
            "table_name": table_name,
            "vacuum_stats": vacuum_stats,
            "recommendations": recommendations,
            "dry_run": dry_run,
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze VACUUM requirements: {str(e)}"
        )


@router.get("/bloat-analysis")
async def get_bloat_analysis(
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get database bloat analysis."""
    try:
        # Get table bloat statistics
        bloat_stats = await _get_bloat_statistics(db_pool)
        recommendations = _generate_bloat_recommendations(bloat_stats)

        return {
            "bloat_statistics": bloat_stats,
            "recommendations": recommendations,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get bloat analysis: {str(e)}"
        )


@router.get("/resource-usage")
async def get_resource_usage(
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get database resource usage."""
    try:
        # Get resource usage from pg_stat_database (only columns that exist in this view)
        query = """
            SELECT
                xact_commit,
                xact_rollback,
                blks_read,
                tup_returned,
                deadlocks,
                conflicts,
                temp_files,
                temp_bytes,
                blk_read_time,
                blk_write_time,
                stats_reset
            FROM pg_stat_database
            WHERE datname = current_database()
        """

        async with db_pool.acquire() as conn:
            result = await conn.fetchrow(query)

            resource_usage = {
                "xact_commit": result[0],
                "xact_rollback": result[1],
                "blks_read": result[2],
                "tup_returned": result[3],
                "deadlocks": result[4],
                "conflicts": result[5],
                "temp_files": result[6],
                "temp_bytes": result[7],
                "blk_read_time": result[8],
                "blk_write_time": result[9],
                "stats_reset": result[10].isoformat() if result[10] else None,
            }

        return resource_usage

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get resource usage: {str(e)}"
        )


@router.get("/slow-queries")
async def get_slow_queries(
    limit: int = Query(default=10, ge=1, le=100),
    min_execution_time: float = Query(default=1000.0),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get slow queries from pg_stat_statements."""
    try:
        # Get slow queries from pg_stat_statements
        query = """
            SELECT
                query,
                calls,
                mean_exec_time,
                total_exec_time,
                stddev_exec_time,
                rows,
                shared_blks_hit,
                shared_blks_read,
                local_blks_hit,
                local_blks_read,
                temp_blks_read,
                temp_blks_written
            FROM pg_stat_statements
            WHERE mean_exec_time > $1
            ORDER BY mean_exec_time DESC
            LIMIT $1
        """

        async with db_pool.acquire() as conn:
            results = await conn.fetch(query, min_execution_time, limit)

            slow_queries = []
            for row in results:
                slow_queries.append(
                    {
                        "query": row[0][:200] + "..." if len(row[0]) else row[0],
                        "calls": int(row[1]) if row[1] else 0,
                        "mean_exec_time": float(row[2]) if row[2] else 0,
                        "total_exec_time": float(row[3]) if row[3] else 0,
                        "stddev_exec_time": float(row[4]) if row[4] else 0,
                        "rows": int(row[5]) if row[5] else 0,
                        "shared_blks_hit": int(row[6]) if row[6] else 0,
                        "shared_blks_read": int(row[7]) if row[7] else 0,
                        "local_blks_hit": int(row[8]) if row[8] else 0,
                        "local_blks_read": int(row[9]) if row[9] else 0,
                        "temp_blks_read": int(row[10]) if row[10] else 0,
                        "temp_blks_written": int(row[11]) if row[11] else 0,
                    }
                )

            return {
                "slow_queries": slow_queries,
                "total_slow_queries": len(slow_queries),
                "period_hours": 1,
                "min_execution_time": min_execution_time,
                "avg_execution_time": sum(q["mean_exec_time"] for q in slow_queries)
                / len(slow_queries)
                if slow_queries
                else 0,
            }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get slow queries: {str(e)}"
        )


@router.get("/cache-hit-rates")
async def get_cache_hit_rates(
    time_period_hours: int = Query(default=24, ge=1, le=168),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get cache hit rates."""
    try:
        # Get cache statistics
        cache_stats = _get_cache_hit_rates(time_period_hours)

        return cache_stats

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get cache hit rates: {str(e)}"
        )


@router.get("/query-plan/{query_hash}")
async def get_query_plan(
    query_hash: str,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get query execution plan by hash."""
    try:
        # Get query plan by hash
        query_plan = await _get_query_plan_by_hash(db_pool, query_hash)

        return query_plan

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get query plan: {str(e)}"
        )


@router.get("/table/{table_name}/indexes")
async def get_table_indexes(
    table_name: str,
    include_usage_stats: bool = True,
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get all indexes for a table."""
    try:
        # SECURITY: Validate table_name to prevent SQL injection
        if not _TABLE_NAME_RE.match(table_name):
            raise HTTPException(
                status_code=400,
                detail="Invalid table_name: must match ^[a-zA-Z_][a-zA-Z0-9_]*$",
            )
        # Create index analyzer
        analyzer = create_index_analyzer(db_pool)

        # Analyze table indexes
        analysis = await analyzer.analyze_table_indexes(
            tenant_id=tenant_id,
            table_name=table_name,
            include_usage_stats=include_usage_stats,
        )

        return {
            "analysis_id": analysis.id,
            "table_name": analysis.table_name,
            "total_indexes": analysis.total_indexes,
            "unused_indexes": [
                {
                    "index_name": index.index_name,
                    "index_type": index.index_type.value,
                    "column_names": index.column_names,
                    "size_bytes": index.size_bytes,
                    "scans": index.scans,
                    "status": index.status.value,
                }
                for index in analysis.unused_indexes
            ],
            "underutilized_indexes": [
                {
                    "index_name": index.index_name,
                    "index_type": index.index_type.value,
                    "column_names": index.column_names,
                    "size_bytes": index.size_bytes,
                    "scans": index.scans,
                    "status": index.status.value,
                }
                for index in analysis.underutilized_indexes
            ],
            "missing_indexes": [
                {
                    "id": rec.id,
                    "recommendation_type": rec.recommendation_type.value,
                    "table_name": rec.table_name,
                    "column_names": rec.column_names,
                    "index_type": rec.index_type.value,
                    "priority": rec.priority,
                    "impact_score": rec.impact_score,
                    "implementation_cost": rec.implementation_cost,
                    "reasoning": rec.reasoning,
                    "sql_statement": rec.sql_statement,
                    "estimated_benefit": rec.estimated_benefit,
                }
                for rec in analysis.missing_indexes
            ],
            "fragmentation_score": analysis.fragmentation_score,
            "optimization_potential": analysis.optimization_potential,
            "created_at": analysis.created_at.isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get table indexes: {str(e)}"
        )


@router.get("/performance/export")
async def export_performance_data(
    format: str = Query(default="json", regex="^(json|csv)$"),
    time_period_hours: int = Query(default=24, ge=1, le=168),
    db_pool=Depends(get_db_pool),
    current_user=Depends(get_current_user),
    tenant_id=Depends(get_tenant_id),
) -> Any:
    """Export performance data."""
    try:
        # Create performance monitor
        monitor = create_performance_monitor(db_pool)

        # Get performance data
        dashboard = await monitor.get_dashboard(
            tenant_id=tenant_id,
            time_period_hours=time_period_hours,
        )

        if format == "json":
            return JSONResponse(
                content=dashboard,
                headers={
                    "Content-Disposition": f"attachment; filename=performance_{time_period_hours}hrs.json"
                },
            )
        elif format == "csv":
            # Convert to CSV format
            csv_data = _convert_performance_to_csv(dashboard)

            from fastapi.responses import Response

            return Response(
                content=csv_data,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=performance_{time_period_hours}hrs.csv"
                },
            )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to export performance data: {str(e)}"
        )


def _convert_performance_to_csv(data: Dict[str, Any]) -> str:
    """Convert performance data to CSV format."""
    try:
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(
            [
                "Category",
                "Metric",
                "Current Value",
                "Target Value",
                "Status",
                "Timestamp",
            ]
        )

        # Write system metrics
        if "system_metrics" in data:
            sys_metrics = data["system_metrics"]
            writer.writerow(
                [
                    "System",
                    "CPU %",
                    sys_metrics["cpu"]["percent"],
                    "70%",
                    "Good",
                    sys_metrics["timestamp"],
                ]
            )
            writer.writerow(
                [
                    "System",
                    "Memory %",
                    sys_metrics["memory"]["percent"],
                    "80%",
                    "Good",
                    sys_metrics["timestamp"],
                ]
            )
            writer.writerow(
                [
                    "System",
                    "Disk %",
                    sys_metrics["disk"]["percent"],
                    "75%",
                    "Good",
                    sys_metrics["timestamp"],
                ]
            )

        # Write database metrics
        if "database_metrics" in data:
            db_metrics = data["database_metrics"]
            writer.writerow(
                [
                    "Database",
                    "Connection Pool %",
                    db_metrics.get("connection_pool", {}).get("utilization", 0),
                    "80%",
                    "Good",
                    db_metrics["timestamp"],
                ]
            )
            writer.writerow(
                [
                    "Database",
                    "Avg Query Time (ms)",
                    db_metrics.get("queries", {}).get("avg_time_ms", 0),
                    "500ms",
                    "Good",
                    db_metrics["timestamp"],
                ]
            )
            writer.writerow(
                [
                    "Database",
                    "Index Hit Rate",
                    db_metrics.get("indexes", {}).get("hit_rate", 0.85),
                    "85%",
                    "Good",
                    db_metrics["timestamp"],
                ]
            )

        # Write application metrics
        if "application_metrics" in data:
            app_metrics = data["application_metrics"]
            writer.writerow(
                [
                    "Application",
                    "Response Time (ms)",
                    app_metrics.get("response_time_ms", 0),
                    "200ms",
                    "Good",
                    app_metrics["timestamp"],
                ]
            )

        return output.getvalue()

    except Exception as e:
        return f"Error converting to CSV: {str(e)}"


def _get_cache_hit_rates(time_period_hours: int) -> Dict[str, Any]:
    """Get cache hit rates."""
    try:
        # This would get actual cache hit rates from cache manager
        # For now, return placeholder data
        return {
            "memory_hit_rate": 0.85,
            "redis_hit_rate": 0.82,
            "overall_hit_rate": 0.84,
            "period_hours": time_period_hours,
        }
    except Exception as e:
        logger.error(f"Failed to get cache hit rates: {e}")
        return {}


async def _get_query_plan_by_hash(db_pool, query_hash: str) -> Dict[str, Any]:
    """Get query execution plan by hash."""
    try:
        # Placeholder - would query pg_stat_statements or similar
        return {"query_hash": query_hash, "plan": {}, "executions": 0}
    except Exception as e:
        logger.error(f"Failed to get query plan for {query_hash}: {e}")
        return {}


async def _get_vacuum_statistics(
    db_pool,
    table_name: Optional[str] = None,
    analyze_all: bool = False,
) -> Dict[str, Any]:
    """Get VACUUM statistics."""
    try:
        if table_name:
            vacuum_stats = await _get_table_vacuum_stats(db_pool, table_name)
        elif analyze_all:
            vacuum_stats = await _get_all_vacuum_stats(db_pool)
        else:
            vacuum_stats = await _get_all_vacuum_stats(db_pool)

        return vacuum_stats

    except Exception as e:
        logger.error(f"Failed to get VACUUM statistics: {e}")
        return {}


async def _get_table_vacuum_stats(db_pool, table_name: str) -> Dict[str, Any]:
    """Get VACUUM statistics for a specific table."""
    try:
        query = """
            SELECT schemaname, tablename,
                relpages, reltuples, dead_tuples, last_vacuum, autovacuum,
                vacuum_count, last_analyze, last_autoanalyze,
                last_autoanalyze_count, last_vacuum_timestamp, last_analyze_timestamp
            FROM pg_stat_user_tables
            WHERE schemaname = 'public' AND tablename = $1
        """
        async with db_pool.acquire() as conn:
            result = await conn.fetchrow(query, table_name)
            if not result:
                return {}
            return {
                "table_name": table_name,
                "relpages": result[2],
                "reltuples": result[3],
                "dead_tuples": result[4],
                "last_vacuum": result[5],
                "autovacuum": result[6],
                "vacuum_count": result[7],
                "last_analyze": result[8],
                "last_autoanalyze": result[9],
                "last_autoanalyze_count": result[10],
                "last_vacuum_timestamp": result[11],
                "last_analyze_timestamp": result[12],
            }
    except Exception as e:
        logger.error(f"Failed to get table VACUUM stats for {table_name}: {e}")
        return {}


async def _get_all_vacuum_stats(db_pool) -> Dict[str, Any]:
    """Get VACUUM statistics for all tables."""
    try:
        query = """
            SELECT schemaname, tablename,
                relpages, reltuples, dead_tuples, last_vacuum, autovacuum,
                vacuum_count, last_analyze, last_autoanalyze,
                last_autoanalyze_count, last_vacuum_timestamp, last_analyze_timestamp
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
            ORDER BY schemaname, tablename
        """
        async with db_pool.acquire() as conn:
            results = await conn.fetch(query)
            stats = {}
            for row in results:
                stats[f"{row[0]}.{row[1]}"] = {
                    "relpages": row[2],
                    "reltuples": row[3],
                    "dead_tuples": row[4],
                    "last_vacuum": row[5],
                    "autovacuum": row[6],
                    "vacuum_count": row[7],
                    "last_analyze": row[8],
                    "last_autoanalyze": row[9],
                    "last_autoanalyze_count": row[10],
                    "last_vacuum_timestamp": row[11],
                    "last_analyze_timestamp": row[12],
                }
            return stats
    except Exception as e:
        logger.error(f"Failed to get all VACUUM stats: {e}")
        return {}


async def _get_table_vacuum_stats(db_pool, table_name: str) -> Dict[str, Any]:
    """Get VACUUM statistics for a specific table."""
    try:
        query = """
            SELECT schemaname, tablename,
                relpages, reltuples, dead_tuples, last_vacuum, autovacuum,
                vacuum_count, last_analyze, last_autoanalyze,
                last_autoanalyze_count, last_vacuum_timestamp, last_analyze_timestamp
            FROM pg_stat_user_tables
            WHERE schemaname = 'public' AND tablename = $1
        """
        async with db_pool.acquire() as conn:
            result = await conn.fetchrow(query, table_name)
            if not result:
                return {}
            return {
                "table_name": table_name,
                "relpages": result[2],
                "reltuples": result[3],
                "dead_tuples": result[4],
                "last_vacuum": result[5],
                "autovacuum": result[6],
                "vacuum_count": result[7],
                "last_analyze": result[8],
                "last_autoanalyze": result[9],
                "last_autoanalyze_count": result[10],
                "last_vacuum_timestamp": result[11],
                "last_analyze_timestamp": result[12],
            }
    except Exception as e:
        logger.error(f"Failed to get table VACUUM stats for {table_name}: {e}")
        return {}


async def _get_bloat_statistics(db_pool) -> Dict[str, Any]:
    """Get database bloat statistics."""
    try:
        query = """
            SELECT schemaname, tablename,
                n_live_tup, n_dead_tup, n_tup_ins, n_tup_upd, n_tup_del,
                last_vacuum, last_autovacuum, vacuum_count
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
            """
        async with db_pool.acquire() as conn:
            results = await conn.fetch(query)
            if not results:
                return {
                    "total_rows": 0,
                    "live_rows": 0,
                    "dead_rows": 0,
                    "tables_analyzed": 0,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            total_live = sum(row[2] or 0 for row in results)
            total_dead = sum(row[3] or 0 for row in results)
            return {
                "total_rows": total_live + total_dead,
                "live_rows": total_live,
                "dead_rows": total_dead,
                "tables_analyzed": len(results),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
    except Exception as e:
        logger.error(f"Failed to get bloat statistics: {e}")
        return {}


def _generate_vacuum_recommendations(
    vacuum_stats: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Generate VACUUM recommendations."""
    try:
        recommendations = []

        # Check for tables that need VACUUM
        for table_name, stats in vacuum_stats.items():
            # Check if table needs VACUUM
            needs_vacuum = (
                stats["dead_tuples"] > stats["reltuples"] * 0.05
                or stats["avg_vacuum_age_days"] > 30
                or stats["vacuum_count"] < 1
            )

            if needs_vacuum:
                # Create VACUUM recommendation
                if stats["avg_vacuum_age_days"] > 30:
                    priority = "high"
                    impact_score = 0.8
                    cost = "medium"
                    reasoning = f"Table {table_name} hasn't been VACUUMed in {stats.get(
    'avg_vacuum_age_days', 0):.1f} days"
                else:
                    priority = "medium"
                    impact_score = 0.6
                    cost = "low"
                    reasoning = f"Table {table_name} needs VACUUM (last VACUUM: {stats['last_vacuum_timestamp']})"

                rec = {
                    "recommendation_type": "vacuum",
                    "table_name": table_name,
                    "priority": priority,
                    "impact_score": impact_score,
                    "implementation_cost": cost,
                    "reasoning": reasoning,
                    "sql_statement": f"VACUUM {table_name}",
                    "estimated_benefit": "Reduced fragmentation and improved performance",
                    "risks": ["Temporary performance impact during VACUUM"],
                }

                recommendations.append(rec)

        return recommendations

    except Exception as e:
        logger.error(f"Failed to generate VACUUM recommendations: {e}")
        return []


def _generate_bloat_recommendations(
    bloat_stats: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Generate bloat recommendations."""
    try:
        recommendations = []

        # Check for high bloat percentage tables
        for table_name, stats in bloat_stats.items():
            if stats["dead_tuples"] > stats["reltuples"] * 0.2:
                recommendations.append(
                    {
                        "recommendation_type": "reorganize",
                        "table_name": table_name,
                        "priority": "high",
                        "impact_score": 0.7,
                        "implementation_cost": "high",
                        "reasoning": f"Table {table_name} has high dead tuple ratio: {stats['dead_tuples']}/{stats['reltuples']} (
    {stats['dead_tuples'] / stats['reltuples'] * 100:.1f}%)",
                        "sql_statement": f"VACUUM FULL {table_name}",
                        "estimated_benefit": "Reduced bloat and improved performance",
                        "risks": ["Temporary performance impact during VACUUM"],
                    }
                )
            elif stats["dead_tuples"] > stats["reltuples"] * 0.1:
                recommendations.append(
                    {
                        "recommendation_type": "reorganize",
                        "table_name": table_name,
                        "priority": "medium",
                        "impact_score": 0.5,
                        "implementation_cost": "medium",
                        "reasoning": f"Table {table_name} has moderate dead tuple ratio: {stats['dead_tuples']}/{stats['reltuples']} (
    {stats['dead_tuples'] / stats['reltuples'] * 100:.1f}%)",
                        "sql_statement": f"VACUUM {table_name}",
                        "estimated_benefit": "Reduced bloat and improved performance",
                        "risks": ["Temporary performance impact during VACUUM"],
                    }
                )

        return recommendations
    except Exception as e:
        logger.error(f"Failed to generate bloat recommendations: {e}")
        return []


async def _get_table_vacuum_stats(db_pool, table_name: str) -> Dict[str, Any]:
    """Get VACUUM statistics for a specific table."""
    try:
        query = """
            SELECT schemaname, tablename,
                relpages, reltuples, dead_tuples, last_vacuum, autovacuum,
                vacuum_count, last_analyze, last_autoanalyze,
                last_autoanalyze_count, last_vacuum_timestamp, last_analyze_timestamp
            FROM pg_stat_user_tables
            WHERE schemaname = 'public' AND tablename = $1
        """
        async with db_pool.acquire() as conn:
            result = await conn.fetchrow(query, table_name)
            if not result:
                return {}
            return {
                "table_name": table_name,
                "relpages": result[2],
                "reltuples": result[3],
                "dead_tuples": result[4],
                "last_vacuum": result[5],
                "autovacuum": result[6],
                "vacuum_count": result[7],
                "last_analyze": result[8],
                "last_autoanalyze": result[9],
                "last_autoanalyze_count": result[10],
                "last_vacuum_timestamp": result[11],
                "last_analyze_timestamp": result[12],
            }
    except Exception as e:
        logger.error(f"Failed to get table VACUUM stats for {table_name}: {e}")
        return {}


async def _get_all_vacuum_stats(db_pool) -> Dict[str, Any]:
    """Get VACUUM statistics for all tables."""
    try:
        query = """
            SELECT schemaname, tablename,
                relpages, reltuples, dead_tuples, last_vacuum, autovacuum,
                vacuum_count, last_analyze, last_autoanalyze,
                last_autoanalyze_count, last_vacuum_timestamp, last_analyze_timestamp
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
            ORDER BY schemaname, tablename
            """
        async with db_pool.acquire() as conn:
            results = await conn.fetch(query)
            stats = {}
            for row in results:
                stats[f"{row[0]}.{row[1]}"] = {
                    "relpages": row[2],
                    "reltuples": row[3],
                    "dead_tuples": row[4],
                    "last_vacuum": row[5],
                    "autovacuum": row[6],
                    "vacuum_count": row[7],
                    "last_analyze": row[8],
                    "last_autoanalyze": row[9],
                    "last_autoanalyze_count": row[10],
                    "last_vacuum_timestamp": row[11],
                    "last_analyze_timestamp": row[12],
                }
            return stats
    except Exception as e:
        logger.error(f"Failed to get all VACUUM stats: {e}")
        return {}


async def _get_table_vacuum_timestamp(db_pool, table_name: str) -> Optional[datetime]:
    """Get last VACUUM timestamp for a table."""
    try:
        query = """
            SELECT last_vacuum_timestamp
            FROM pg_stat_user_tables
            WHERE schemaname = 'public' AND tablename = $1
        """
        async with db_pool.acquire() as conn:
            result = await conn.fetchrow(query, table_name)
            if result and result[0]:
                return datetime.fromisoformat(result[0])
            return None
    except Exception as e:
        logger.error(f"Failed to get VACUUM timestamp for {table_name}: {e}")
        return None


# Factory functions (create_database_performance_manager, create_query_optimizer, create_performance_monitor imported)
def create_cache_manager(redis_url: Optional[str] = None) -> CacheManager:
    """Create cache manager instance."""
    return CacheManager(redis_url)


def create_connection_pool_manager() -> ConnectionPoolManager:
    """Create connection pool manager instance."""
    return ConnectionPoolManager()
