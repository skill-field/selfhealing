"""Log source management routes — containers, endpoints, syslog feeds."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import database as db
import crypto

router = APIRouter(tags=["Sources"])


class SourceCreateRequest(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=100)
    source_type: str = Field(..., pattern="^(container|log_endpoint|syslog|file)$")
    endpoint_url: Optional[str] = None
    container_id: Optional[str] = None
    container_image: Optional[str] = None
    environment: str = "production"
    auth_header: Optional[str] = None
    poll_interval_seconds: int = 60


class SourceUpdateRequest(BaseModel):
    is_active: Optional[bool] = None
    display_name: Optional[str] = None
    endpoint_url: Optional[str] = None
    poll_interval_seconds: Optional[int] = None


def _row_to_response(row: dict) -> dict:
    return {
        "id": row["id"],
        "display_name": row["display_name"],
        "source_type": row["source_type"],
        "endpoint_url": row.get("endpoint_url"),
        "container_id": row.get("container_id"),
        "container_image": row.get("container_image"),
        "environment": row.get("environment", "production"),
        "has_auth": bool(row.get("auth_header")),
        "poll_interval_seconds": row.get("poll_interval_seconds", 60),
        "is_active": bool(row.get("is_active", 1)),
        "last_polled_at": row.get("last_polled_at"),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


@router.get("/sources")
async def list_sources():
    """List all log sources (containers, endpoints, etc.)."""
    rows = await db.fetch_all("SELECT * FROM log_sources ORDER BY created_at DESC")
    return {"sources": [_row_to_response(r) for r in rows]}


@router.post("/sources", status_code=201)
async def add_source(req: SourceCreateRequest):
    """Add a new log source."""
    now = datetime.now(timezone.utc).isoformat()
    source_id = uuid4().hex[:12]
    await db.execute(
        """INSERT INTO log_sources
           (id, display_name, source_type, endpoint_url, container_id, container_image,
            environment, auth_header, poll_interval_seconds, is_active, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)""",
        (source_id, req.display_name, req.source_type, req.endpoint_url,
         req.container_id, req.container_image, req.environment,
         crypto.encrypt(req.auth_header) if req.auth_header else None,
         req.poll_interval_seconds, now, now),
    )

    await db.execute(
        "INSERT INTO audit_log (id, action, entity_type, entity_id, details, actor, created_at) VALUES (?,?,?,?,?,?,?)",
        (uuid4().hex, "source_added", "log_source", source_id,
         json.dumps({"display_name": req.display_name, "source_type": req.source_type}),
         "user", now),
    )

    row = await db.fetch_one("SELECT * FROM log_sources WHERE id = ?", (source_id,))
    return _row_to_response(row)


@router.patch("/sources/{source_id}")
async def update_source(source_id: str, req: SourceUpdateRequest):
    """Update a log source."""
    existing = await db.fetch_one("SELECT * FROM log_sources WHERE id = ?", (source_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Source not found")

    now = datetime.now(timezone.utc).isoformat()
    updates = []
    params = []

    if req.is_active is not None:
        updates.append("is_active = ?")
        params.append(int(req.is_active))
    if req.display_name is not None:
        updates.append("display_name = ?")
        params.append(req.display_name)
    if req.endpoint_url is not None:
        updates.append("endpoint_url = ?")
        params.append(req.endpoint_url)
    if req.poll_interval_seconds is not None:
        updates.append("poll_interval_seconds = ?")
        params.append(req.poll_interval_seconds)

    if updates:
        updates.append("updated_at = ?")
        params.append(now)
        params.append(source_id)
        await db.execute(
            f"UPDATE log_sources SET {', '.join(updates)} WHERE id = ?",
            tuple(params),
        )

    row = await db.fetch_one("SELECT * FROM log_sources WHERE id = ?", (source_id,))
    return _row_to_response(row)


@router.delete("/sources/{source_id}")
async def remove_source(source_id: str):
    """Remove a log source."""
    existing = await db.fetch_one("SELECT id FROM log_sources WHERE id = ?", (source_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Source not found")
    await db.execute("DELETE FROM log_sources WHERE id = ?", (source_id,))
    return {"status": "deleted", "id": source_id}
