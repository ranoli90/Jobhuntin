"""
Database Read Replicas Configuration and Management

This module provides read replica support for PostgreSQL databases,
enabling horizontal scaling of read operations and improved performance.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Union

import asyncpg

from shared.config import get_settings
from shared.logging_config import get_logger
from shared.metrics import incr, observe

logger = get_logger("sorce.db_read_replicas")


class ReadReplicaManager:
    """Manages database read replicas with load balancing and failover."""
    
    def __init__(self):
        self.settings = get_settings()
        self.replica_pools: Dict[str, asyncpg.Pool] = {}
        self.primary_pool: Optional[asyncpg.Pool] = None
        self.current_replica_index = 0
        self.health_check_interval = 30  # seconds
        self.health_check_task: Optional[asyncio.Task] = None
        self.replica_health: Dict[str, bool] = {}
        
    async def initialize(self) -> None:
        """Initialize primary and replica connection pools."""
        try:
            # Initialize primary connection pool
            await self._initialize_primary_pool()
            
            # Initialize replica connection pools
            await self._initialize_replica_pools()
            
            # Start health checking
            await self._start_health_checking()
            
            logger.info("Read replica manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize read replica manager: {e}")
            raise
    
    async def _initialize_primary_pool(self) -> None:
        """Initialize primary database connection pool."""
        try:
            self.primary_pool = await self._create_connection_pool(
                self.settings.database_url,
                pool_name="primary",
                min_size=self.settings.db_pool_min,
                max_size=self.settings.db_pool_max,
            )
            logger.info("Primary database pool initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize primary pool: {e}")
            raise
    
    async def _initialize_replica_pools(self) -> None:
        """Initialize read replica connection pools."""
        replica_urls = self._get_replica_urls()
        
        for i, replica_url in enumerate(replica_urls):
            try:
                pool = await self._create_connection_pool(
                    replica_url,
                    pool_name=f"replica_{i}",
                    min_size=max(1, self.settings.db_pool_min // 2),
                    max_size=max(2, self.settings.db_pool_max // 2),
                )
                self.replica_pools[f"replica_{i}"] = pool
                self.replica_health[f"replica_{i}"] = True
                logger.info(f"Replica {i} pool initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize replica {i}: {e}")
                self.replica_health[f"replica_{i}"] = False
    
    def _get_replica_urls(self) -> List[str]:
        """Get read replica URLs from settings or environment."""
        urls = []
        
        # Try to get from settings
        if hasattr(self.settings, 'database_read_urls'):
            if isinstance(self.settings.database_read_urls, str):
                urls = [self.settings.database_read_urls]
            elif isinstance(self.settings.database_read_urls, list):
                urls = self.settings.database_read_urls
        
        # Try environment variable
        if not urls:
            read_url = self.settings.__dict__.get('DATABASE_READ_URL')
            if read_url:
                urls = [read_url]
        
        # If no replicas configured, use primary for reads
        if not urls:
            logger.warning("No read replicas configured, using primary for reads")
            urls = [self.settings.database_url]
        
        return urls
    
    async def _create_connection_pool(
        self,
        url: str,
        pool_name: str,
        min_size: int,
        max_size: int,
    ) -> asyncpg.Pool:
        """Create a database connection pool."""
        from shared.db import resolve_dsn_ipv4
        
        dsn = resolve_dsn_ipv4(url)
        
        return await asyncpg.create_pool(
            dsn,
            min_size=min_size,
            max_size=max_size,
            command_timeout=60,
            statement_cache_size=0,  # Critical for PGBouncer/Render
            server_settings={
                'application_name': f'sorce_{pool_name}',
                'jit': 'off',  # Disable JIT for better performance
            },
        )
    
    async def _start_health_checking(self) -> None:
        """Start periodic health checking of replicas."""
        self.health_check_task = asyncio.create_task(self._health_check_loop())
    
    async def _health_check_loop(self) -> None:
        """Periodically check health of all replicas."""
        while True:
            try:
                await self._check_replica_health()
                await asyncio.sleep(self.health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(self.health_check_interval)
    
    async def _check_replica_health(self) -> None:
        """Check health of all replica connections."""
        for replica_name, pool in self.replica_pools.items():
            try:
                async with pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                    if not self.replica_health.get(replica_name, False):
                        logger.info(f"Replica {replica_name} is back online")
                        self.replica_health[replica_name] = True
                    
            except Exception as e:
                if self.replica_health.get(replica_name, False):
                    logger.warning(f"Replica {replica_name} is unhealthy: {e}")
                    self.replica_health[replica_name] = False
    
    async def get_read_connection(self) -> asyncpg.Connection:
        """Get a connection from a healthy read replica."""
        healthy_replicas = [
            name for name, healthy in self.replica_health.items()
            if healthy and name in self.replica_pools
        ]
        
        if not healthy_replicas:
            logger.warning("No healthy replicas available, falling back to primary")
            if self.primary_pool:
                return await self.primary_pool.acquire()
            else:
                raise Exception("No database connections available")
        
        # Round-robin selection
        replica_name = healthy_replicas[self.current_replica_index % len(healthy_replicas)]
        self.current_replica_index += 1
        
        pool = self.replica_pools[replica_name]
        connection = await pool.acquire()
        
        # Record metrics
        incr("db.read_replica.connection")
        observe("db.read_replica.pool_size", pool.get_size())
        
        return connection
    
    async def get_write_connection(self) -> asyncpg.Connection:
        """Get a connection from the primary database."""
        if not self.primary_pool:
            raise Exception("Primary database pool not available")
        
        connection = await self.primary_pool.acquire()
        
        # Record metrics
        incr("db.primary.connection")
        observe("db.primary.pool_size", self.primary_pool.get_size())
        
        return connection
    
    async def execute_read_query(
        self,
        query: str,
        *args: Any,
        fetch: str = "all",
    ) -> Union[List[Dict[str, Any]], Dict[str, Any], None]:
        """Execute a read query on a replica."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            async with await self.get_read_connection() as conn:
                if fetch == "all":
                    result = await conn.fetch(query, *args)
                elif fetch == "one":
                    result = await conn.fetchrow(query, *args)
                elif fetch == "val":
                    result = await conn.fetchval(query, *args)
                else:
                    raise ValueError(f"Invalid fetch mode: {fetch}")
                
                # Record metrics
                duration = asyncio.get_event_loop().time() - start_time
                observe("db.read_replica.query_duration", duration)
                incr("db.read_replica.query_success")
                
                return result
                
        except Exception as e:
            incr("db.read_replica.query_error")
            logger.error(f"Read query failed: {e}")
            raise
    
    async def execute_write_query(
        self,
        query: str,
        *args: Any,
        fetch: str = "all",
    ) -> Union[List[Dict[str, Any]], Dict[str, Any], None]:
        """Execute a write query on the primary database."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            async with await self.get_write_connection() as conn:
                if fetch == "all":
                    result = await conn.fetch(query, *args)
                elif fetch == "one":
                    result = await conn.fetchrow(query, *args)
                elif fetch == "val":
                    result = await conn.fetchval(query, *args)
                elif fetch == "execute":
                    result = await conn.execute(query, *args)
                else:
                    raise ValueError(f"Invalid fetch mode: {fetch}")
                
                # Record metrics
                duration = asyncio.get_event_loop().time() - start_time
                observe("db.primary.query_duration", duration)
                incr("db.primary.query_success")
                
                return result
                
        except Exception as e:
            incr("db.primary.query_error")
            logger.error(f"Write query failed: {e}")
            raise
    
    async def execute_transaction(
        self,
        queries: List[tuple[str, tuple[Any, ...]]],
        read_only: bool = False,
    ) -> List[Any]:
        """Execute multiple queries in a transaction."""
        if read_only:
            conn = await self.get_read_connection()
        else:
            conn = await self.get_write_connection()
        
        try:
            async with conn.transaction():
                results = []
                for query, args in queries:
                    if query.strip().upper().startswith("SELECT"):
                        result = await conn.fetch(query, *args)
                    else:
                        result = await conn.execute(query, *args)
                    results.append(result)
                
                return results
                
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            raise
        finally:
            await conn.release()
    
    async def get_replica_status(self) -> Dict[str, Any]:
        """Get status of all replicas."""
        status = {
            "primary": {
                "healthy": self.primary_pool is not None,
                "pool_size": self.primary_pool.get_size() if self.primary_pool else 0,
            },
            "replicas": {},
        }
        
        for replica_name, pool in self.replica_pools.items():
            status["replicas"][replica_name] = {
                "healthy": self.replica_health.get(replica_name, False),
                "pool_size": pool.get_size(),
            }
        
        return status
    
    async def close(self) -> None:
        """Close all connection pools."""
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
        
        if self.primary_pool:
            await self.primary_pool.close()
        
        for pool in self.replica_pools.values():
            await pool.close()
        
        logger.info("All database pools closed")


# Global instance
replica_manager = ReadReplicaManager()


# Dependency injection functions
async def get_read_connection() -> asyncpg.Connection:
    """Get a read connection from the replica manager."""
    return await replica_manager.get_read_connection()


async def get_write_connection() -> asyncpg.Connection:
    """Get a write connection from the replica manager."""
    return await replica_manager.get_write_connection()


# Database query helpers
async def execute_read_query(
    query: str,
    *args: Any,
    fetch: str = "all",
) -> Union[List[Dict[str, Any]], Dict[str, Any], None]:
    """Execute a read query."""
    return await replica_manager.execute_read_query(query, *args, fetch=fetch)


async def execute_write_query(
    query: str,
    *args: Any,
    fetch: str = "all",
) -> Union[List[Dict[str, Any]], Dict[str, Any], None]:
    """Execute a write query."""
    return await replica_manager.execute_write_query(query, *args, fetch=fetch)


async def execute_transaction(
    queries: List[tuple[str, tuple[Any, ...]]],
    read_only: bool = False,
) -> List[Any]:
    """Execute multiple queries in a transaction."""
    return await replica_manager.execute_transaction(queries, read_only)


# Initialization function
async def initialize_read_replicas() -> None:
    """Initialize the read replica manager."""
    await replica_manager.initialize()


# Cleanup function
async def cleanup_read_replicas() -> None:
    """Cleanup the read replica manager."""
    await replica_manager.close()
