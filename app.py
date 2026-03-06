"""Skillfield Sentinel — AI Self-Healing Software Platform."""

import sys
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Ensure project root is on sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings
from database import init_db
from api.routes_watch import router as watch_router
from api.routes_think import router as think_router
from api.routes_heal import router as heal_router
from api.routes_verify import router as verify_router
from api.routes_evolve import router as evolve_router
from api.routes_dashboard import router as dashboard_router
from api.routes_events import router as events_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    # Startup: initialize the database
    await init_db()
    print(f"[Sentinel] Database initialized at {settings.DB_PATH}")
    print(f"[Sentinel] Running on port {settings.CDSW_APP_PORT}")
    if settings.IS_CML:
        print("[Sentinel] CML environment detected")
    yield
    # Shutdown
    print("[Sentinel] Shutting down")


app = FastAPI(
    title="Skillfield Sentinel",
    description="AI Self-Healing Software Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware (allow all for hackathon)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── API Routes ──────────────────────────────────────────────────────────────

API_PREFIX = "/api/v1"


@app.get(f"{API_PREFIX}/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Skillfield Sentinel",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": "cml" if settings.IS_CML else "local",
    }


# Include routers
app.include_router(watch_router, prefix=API_PREFIX)
app.include_router(think_router, prefix=API_PREFIX)
app.include_router(heal_router, prefix=API_PREFIX)
app.include_router(verify_router, prefix=API_PREFIX)
app.include_router(evolve_router, prefix=API_PREFIX)
app.include_router(dashboard_router, prefix=API_PREFIX)
app.include_router(events_router, prefix=API_PREFIX)

# ─── Static Files & SPA Catch-All ───────────────────────────────────────────

static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/{full_path:path}")
async def serve_spa(request: Request, full_path: str):
    """Catch-all route to serve index.html for SPA routing."""
    # Don't intercept API routes
    if full_path.startswith("api/"):
        return JSONResponse(status_code=404, content={"error": "not_found"})

    index_path = os.path.join(static_dir, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)

    return JSONResponse(
        status_code=404,
        content={"error": "Frontend not built. Place files in static/ directory."},
    )


# ─── Entry Point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=settings.CDSW_APP_PORT,
        reload=not settings.IS_CML,
    )
