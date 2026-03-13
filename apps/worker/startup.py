"""Enhanced startup script for auto-apply worker with comprehensive error handling and monitoring."""

from __future__ import annotations

import asyncio
import contextlib
import os
import signal
import sys
import time
from typing import Any

from shared.config import get_settings
from shared.logging_config import get_logger
from shared.metrics import incr, observe

logger = get_logger("sorce.worker.startup")


class WorkerStartupManager:
    """Manages worker startup with comprehensive error handling and monitoring."""
    
    def __init__(self, instance_count: int = 2):
        self.instance_count = instance_count
        self._shutdown = asyncio.Event()
        self._startup_time = time.time()
        self._startup_phase = "initializing"
        
    async def startup_sequence(self) -> bool:
        """Execute complete startup sequence with validation."""
        try:
            self._startup_phase = "environment_check"
            await self._check_environment()
            
            self._startup_phase = "dependencies_check"
            await self._check_dependencies()
            
            self._startup_phase = "database_check"
            await self._check_database()
            
            self._startup_phase = "browser_check"
            await self._check_browser()
            
            self._startup_phase = "worker_initialization"
            success = await self._initialize_workers()
            
            if success:
                self._startup_phase = "ready"
                startup_duration = time.time() - self._startup_time
                logger.info("Worker startup completed successfully in %.2f seconds", startup_duration)
                observe("worker.startup.duration", startup_duration)
                incr("worker.startup.success")
                return True
            else:
                self._startup_phase = "failed"
                incr("worker.startup.failure")
                return False
                
        except Exception as e:
            self._startup_phase = "error"
            logger.error("Worker startup failed during %s phase: %s", self._startup_phase, e)
            incr("worker.startup.error")
            return False
    
    async def _check_environment(self) -> None:
        """Check environment variables and configuration."""
        logger.info("Checking environment configuration...")
        
        s = get_settings()
        required_vars = {
            "database_url": s.database_url,
            "llm_api_key": s.llm_api_key,
            "llm_api_base": s.llm_api_base,
        }
        
        missing_vars = [name for name, value in required_vars.items() if not value]
        if missing_vars:
            raise RuntimeError(f"Missing required environment variables: {missing_vars}")
        
        logger.info("Environment check passed")
    
    async def _check_dependencies(self) -> None:
        """Check that all required dependencies are available."""
        logger.info("Checking dependencies...")
        
        try:
            import playwright
            from playwright.async_api import async_playwright
            logger.info("Playwright version: %s", playwright.__version__)
        except ImportError as e:
            raise RuntimeError(f"Playwright not available: {e}")
        
        try:
            import asyncpg
            logger.info("asyncpg version: %s", asyncpg.__version__)
        except ImportError as e:
            raise RuntimeError(f"asyncpg not available: {e}")
        
        logger.info("Dependency check passed")
    
    async def _check_database(self) -> None:
        """Check database connectivity."""
        logger.info("Checking database connectivity...")
        
        try:
            from shared.db import get_db_pool
            
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1 as test")
                if result != 1:
                    raise RuntimeError("Database test query failed")
            
            logger.info("Database check passed")
            
        except Exception as e:
            raise RuntimeError(f"Database check failed: {e}")
    
    async def _check_browser(self) -> None:
        """Check browser functionality."""
        logger.info("Checking browser functionality...")
        
        try:
            from .scaling import BrowserPoolManager
            
            browser_pool = BrowserPoolManager()
            await browser_pool.start()
            
            health_status = await browser_pool.health_check()
            if not health_status["healthy"]:
                raise RuntimeError(f"Browser health check failed: {health_status['browser_status']}")
            
            await browser_pool.shutdown()
            logger.info("Browser check passed: %s", health_status["browser_status"])
            
        except Exception as e:
            raise RuntimeError(f"Browser check failed: {e}")
    
    async def _initialize_workers(self) -> bool:
        """Initialize worker instances."""
        logger.info("Initializing %d worker instances...", self.instance_count)
        
        try:
            from .scaling import WorkerScaler
            
            scaler = WorkerScaler(instance_count=self.instance_count)
            
            # Set up signal handlers for graceful shutdown
            loop = asyncio.get_event_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                with contextlib.suppress(NotImplementedError):
                    loop.add_signal_handler(sig, lambda: asyncio.create_task(self._graceful_shutdown(scaler)))
            
            # Start workers
            await scaler.start()
            
            logger.info("All workers started successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize workers: %s", e)
            return False
    
    async def _graceful_shutdown(self, scaler: Any) -> None:
        """Handle graceful shutdown of workers."""
        logger.info("Initiating graceful shutdown...")
        self._shutdown.set()
        
        try:
            await scaler.shutdown()
            logger.info("Graceful shutdown completed")
        except Exception as e:
            logger.error("Error during graceful shutdown: %s", e)
    
    def get_startup_status(self) -> dict[str, Any]:
        """Get current startup status."""
        return {
            "phase": self._startup_phase,
            "instance_count": self.instance_count,
            "startup_time": self._startup_time,
            "uptime_seconds": time.time() - self._startup_time,
            "shutdown_requested": self._shutdown.is_set(),
        }


async def main() -> None:
    """Main startup function."""
    # Parse command line arguments
    instance_count = 2
    for idx, arg in enumerate(sys.argv):
        if arg == "--instances" and idx + 1 < len(sys.argv):
            instance_count = int(sys.argv[idx + 1])
    
    logger.info("Starting auto-apply worker with %d instances...", instance_count)
    
    # Initialize startup manager
    startup_manager = WorkerStartupManager(instance_count=instance_count)
    
    # Execute startup sequence
    success = await startup_manager.startup_sequence()
    
    if not success:
        logger.error("Worker startup failed. Exiting.")
        sys.exit(1)
    
    # Keep the service running
    try:
        while not startup_manager._shutdown.is_set():
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        logger.info("Worker service stopped")


if __name__ == "__main__":
    asyncio.run(main())
