"""
Minimal backend runner for demonstration - runs without database dependency
"""

from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Sorce API - Minimal", version="0.4.0")

@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Backend is running without database"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Sorce API is running", "status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
