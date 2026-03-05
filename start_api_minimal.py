#!/usr/bin/env python3
"""Minimal API startup for local development without database dependencies."""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment variables for minimal startup
os.environ["ENV"] = "local"
os.environ["LOG_JSON"] = "false"
os.environ["LOG_LEVEL"] = "DEBUG"


# Mock database dependencies
class MockPool:
    async def acquire(self):
        return MockConn()


class MockConn:
    async def fetch(self, *args):
        return []

    async def fetchrow(self, *args):
        return None

    async def execute(self, *args):
        return None


# Create a minimal FastAPI app
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="JobHuntin API - Minimal Mode")


@app.get("/health")
async def health_check():
    """Health check endpoint that doesn't require database."""
    return JSONResponse({"status": "healthy", "mode": "minimal", "database": "mocked"})


@app.get("/")
async def root():
    """Root endpoint."""
    return JSONResponse(
        {
            "message": "JobHuntin API - Minimal Mode",
            "docs": "/docs",
            "health": "/health",
        }
    )


if __name__ == "__main__":
    import uvicorn

    print("Starting JobHuntin API in minimal mode (no database)")
    print("Health check: http://localhost:8000/health")
    print("API docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
