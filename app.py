"""Skillfield Sentinel — AI Self-Healing Software Platform."""

import logging
import sys
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Ensure project root is on sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings, setup_logging
from database import init_db
from middleware import APIKeyMiddleware
from api.routes_watch import router as watch_router
from api.routes_think import router as think_router
from api.routes_heal import router as heal_router
from api.routes_verify import router as verify_router
from api.routes_evolve import router as evolve_router
from api.routes_dashboard import router as dashboard_router
from api.routes_events import router as events_router
from api.routes_repos import router as repos_router
from api.routes_cml import router as cml_router
from api.routes_sources import router as sources_router

setup_logging()
logger = logging.getLogger("sentinel.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    await init_db()
    logger.info("Database initialized at %s", settings.DB_PATH)
    logger.info("Running on port %d", settings.CDSW_APP_PORT)
    if settings.IS_CML:
        logger.info("CML environment detected")
    if settings.SENTINEL_API_KEY:
        logger.info("API key authentication enabled")
    else:
        logger.info("API key authentication disabled (set SENTINEL_API_KEY to enable)")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="Skillfield Sentinel",
    description="AI Self-Healing Software Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API key authentication middleware
app.add_middleware(APIKeyMiddleware)

# --- API Routes ---

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
        "auth_enabled": bool(settings.SENTINEL_API_KEY),
    }


# Include routers
app.include_router(watch_router, prefix=API_PREFIX)
app.include_router(think_router, prefix=API_PREFIX)
app.include_router(heal_router, prefix=API_PREFIX)
app.include_router(verify_router, prefix=API_PREFIX)
app.include_router(evolve_router, prefix=API_PREFIX)
app.include_router(dashboard_router, prefix=API_PREFIX)
app.include_router(events_router, prefix=API_PREFIX)
app.include_router(repos_router, prefix=API_PREFIX)
app.include_router(cml_router, prefix=API_PREFIX)
app.include_router(sources_router, prefix=API_PREFIX)

# --- Static Files & SPA Catch-All ---

static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


class SPAStaticFiles(StaticFiles):
    """Serves static files with correct MIME types, falls back to index.html for SPA routes."""

    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except Exception:
            return await super().get_response("index.html", scope)


if os.path.isdir(static_dir):
    app.mount("/", SPAStaticFiles(directory=static_dir, html=True), name="spa")


# --- Entry Point ---

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=settings.CDSW_APP_PORT,
        reload=not settings.IS_CML,
    )
