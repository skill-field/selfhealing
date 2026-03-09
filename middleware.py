"""Authentication middleware for Skillfield Sentinel."""

import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from config import settings

logger = logging.getLogger("sentinel.auth")

# Paths that don't require authentication
PUBLIC_PATHS = frozenset({
    "/healthcheck",
    "/api/v1/health",
    "/api/v1/events/stream",
})

# Path prefixes that are public (static assets, SPA)
PUBLIC_PREFIXES = ("/static/", "/assets/")


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Simple API key authentication middleware.

    Checks for X-API-Key header or api_key query parameter.
    Skipped when SENTINEL_API_KEY is not configured (dev/demo mode).
    """

    async def dispatch(self, request: Request, call_next):
        # Skip auth if no API key is configured (demo/dev mode)
        if not settings.SENTINEL_API_KEY:
            return await call_next(request)

        path = request.url.path

        # Allow public paths
        if path in PUBLIC_PATHS:
            return await call_next(request)

        # Allow static assets and SPA routes
        if any(path.startswith(p) for p in PUBLIC_PREFIXES):
            return await call_next(request)

        # Allow the SPA index
        if not path.startswith("/api/"):
            return await call_next(request)

        # Check API key
        api_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")

        if not api_key:
            logger.warning("Missing API key from %s", request.client.host if request.client else "unknown")
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing API key. Provide X-API-Key header."},
            )

        if api_key != settings.SENTINEL_API_KEY:
            logger.warning("Invalid API key from %s", request.client.host if request.client else "unknown")
            return JSONResponse(
                status_code=403,
                content={"detail": "Invalid API key."},
            )

        return await call_next(request)
