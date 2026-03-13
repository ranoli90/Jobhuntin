"""Worker health check endpoint for monitoring and diagnostics."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from shared.config import get_settings
from shared.logging_config import get_logger

logger = get_logger("sorce.worker.health")

app = FastAPI(title="Worker Health Check")

# Module-level singleton for browser pool - persists across health check requests
_browser_pool: Any = None
_browser_pool_lock: asyncio.Lock = asyncio.Lock()


async def get_browser_pool() -> Any:
    """Get or create the shared browser pool singleton.
    
    This avoids creating/destroying a browser on every health check request.
    The browser pool is created once and reused for all subsequent requests.
    """
    global _browser_pool
    
    if _browser_pool is not None:
        return _browser_pool
    
    async with _browser_pool_lock:
        # Double-check after acquiring lock
        if _browser_pool is not None:
            return _browser_pool
            
        from .scaling import BrowserPoolManager
        _browser_pool = BrowserPoolManager()
        await _browser_pool.start()
        logger.info("Browser pool initialized for health checks")
        
    return _browser_pool


async def shutdown_browser_pool() -> None:
    """Shutdown the browser pool gracefully."""
    global _browser_pool
    
    if _browser_pool is not None:
        try:
            await _browser_pool.shutdown()
        except Exception as e:
            logger.warning("Error shutting down browser pool: %s", e)
        finally:
            _browser_pool = None
            logger.info("Browser pool shut down")


@app.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint for worker service."""
    try:
        s = get_settings()
        
        # Basic service health
        health_data = {
            "status": "healthy",
            "service": "auto-apply-worker",
            "version": "1.0.0",
            "timestamp": asyncio.get_event_loop().time(),
            "checks": {},
        }
        
        # Check database connectivity
        try:
            from shared.db import get_db_pool
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            health_data["checks"]["database"] = {"status": "healthy", "message": "Database connection successful"}
        except Exception as e:
            health_data["checks"]["database"] = {"status": "unhealthy", "message": f"Database connection failed: {e}"}
            health_data["status"] = "unhealthy"
        
        # Check browser pool - use shared singleton instead of creating new one
        try:
            browser_pool = await get_browser_pool()
            browser_health = await browser_pool.health_check()
            
            health_data["checks"]["browser"] = browser_health
            if not browser_health["healthy"]:
                health_data["status"] = "unhealthy"
                
        except Exception as e:
            health_data["checks"]["browser"] = {"status": "unhealthy", "message": f"Browser health check failed: {e}"}
            health_data["status"] = "unhealthy"
        
        # Check configuration
        try:
            config_checks = {
                "llm_configured": bool(s.llm_api_key and s.llm_api_base),
                "database_configured": bool(s.database_url),
                "agent_enabled": s.agent_enabled,
            }
            health_data["checks"]["configuration"] = config_checks
            
            if not all(config_checks.values()):
                health_data["status"] = "degraded"
                
        except Exception as e:
            health_data["checks"]["configuration"] = {"status": "error", "message": f"Configuration check failed: {e}"}
        
        # Return appropriate HTTP status
        status_code = 200 if health_data["status"] == "healthy" else 503
        
        return JSONResponse(
            content=health_data,
            status_code=status_code,
        )
        
    except Exception as e:
        logger.error("Health check failed: %s", e)
        return JSONResponse(
            content={
                "status": "error",
                "service": "auto-apply-worker",
                "message": f"Health check failed: {e}",
                "timestamp": asyncio.get_event_loop().time(),
            },
            status_code=500,
        )


@app.get("/health/ready")
async def readiness_check() -> JSONResponse:
    """Readiness check - service is ready to accept traffic."""
    try:
        # Use shared browser pool instead of creating new one
        browser_pool = await get_browser_pool()
        browser_health = await browser_pool.health_check()
        
        if browser_health["healthy"]:
            return JSONResponse(
                content={
                    "status": "ready",
                    "service": "auto-apply-worker",
                    "message": "Service is ready to accept traffic",
                },
                status_code=200,
            )
        else:
            return JSONResponse(
                content={
                    "status": "not_ready",
                    "service": "auto-apply-worker",
                    "message": f"Browser not ready: {browser_health.get('browser_status', 'unknown')}",
                },
                status_code=503,
            )
        
    except Exception as e:
        logger.error("Readiness check failed: %s", e)
        return JSONResponse(
            content={
                "status": "not_ready",
                "service": "auto-apply-worker",
                "message": f"Service not ready: {e}",
            },
            status_code=503,
        )


@app.get("/health/live")
async def liveness_check() -> JSONResponse:
    """Liveness check - service is alive."""
    return JSONResponse(
        content={
            "status": "alive",
            "service": "auto-apply-worker",
            "message": "Service is alive",
        },
        status_code=200,
    )


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting worker health check service...")
    uvicorn.run(
        "health:app",
        host="0.0.0.0",
        port=8001,
        log_level="info",
    )
