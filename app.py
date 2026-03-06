"""Skillfield Sentinel — AI Self-Healing Software Platform."""

import sys
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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


@app.get("/healthcheck")
async def cml_health_check():
    """CML health check endpoint."""
    return {"status": "ok"}


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


class SPAStaticFiles(StaticFiles):
    """Serves static files with correct MIME types, falls back to index.html for SPA routes."""

    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except Exception:
            # File not found — serve index.html for SPA client-side routing
            return await super().get_response("index.html", scope)


if os.path.isdir(static_dir):
    app.mount("/", SPAStaticFiles(directory=static_dir, html=True), name="spa")


# ─── Entry Point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=settings.CDSW_APP_PORT,
        reload=not settings.IS_CML,
    )
