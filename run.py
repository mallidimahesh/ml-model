"""EcoSim Unified Application Runner.

Runs the FastAPI backend and serves the compiled React production frontend
across any cloud platform (Render, Railway, Fly.io, Docker, or locally).
"""
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run("backend.main:app", host=host, port=port)
