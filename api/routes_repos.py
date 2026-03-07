"""Repo management routes — add, list, remove monitored repositories."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import database as db
import crypto

router = APIRouter(tags=["Repos"])


class RepoCreateRequest(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=100)
    repo_slug: str = Field(..., min_length=3, max_length=200)
    github_token: Optional[str] = None
    scan_paths: list[str] = Field(default_factory=list)


class RepoUpdateRequest(BaseModel):
    is_active: Optional[bool] = None
    display_name: Optional[str] = None
    scan_paths: Optional[list[str]] = None


def _row_to_response(row: dict) -> dict:
    scan_paths_raw = row.get("scan_paths", "[]")
    try:
        scan_paths = json.loads(scan_paths_raw) if isinstance(scan_paths_raw, str) else scan_paths_raw
    except Exception:
        scan_paths = []
    return {
        "id": row["id"],
        "display_name": row["display_name"],
        "repo_slug": row["repo_slug"],
        "has_token": bool(row.get("github_token")),
        "scan_paths": scan_paths,
        "is_active": bool(row.get("is_active", 1)),
        "source_type": row.get("source_type", "github"),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


@router.get("/repos")
async def list_repos():
    """List all monitored repositories."""
    rows = await db.fetch_all("SELECT * FROM monitored_repos ORDER BY created_at DESC")
    return {"repos": [_row_to_response(r) for r in rows]}


@router.post("/repos", status_code=201)
async def add_repo(req: RepoCreateRequest):
    """Add a new repository to monitor."""
    now = datetime.now(timezone.utc).isoformat()
    repo_id = uuid4().hex[:12]
    try:
        await db.execute(
            """INSERT INTO monitored_repos
               (id, display_name, repo_slug, github_token, scan_paths, is_active, source_type, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, 1, 'github', ?, ?)""",
            (repo_id, req.display_name, req.repo_slug,
             crypto.encrypt(req.github_token) if req.github_token else None,
             json.dumps(req.scan_paths), now, now),
        )
    except Exception:
        raise HTTPException(status_code=409, detail="Repository already exists")

    # Audit log
    await db.execute(
        "INSERT INTO audit_log (id, action, entity_type, entity_id, details, actor, created_at) VALUES (?,?,?,?,?,?,?)",
        (uuid4().hex, "repo_added", "repo", repo_id,
         json.dumps({"repo_slug": req.repo_slug, "display_name": req.display_name}),
         "user", now),
    )

    row = await db.fetch_one("SELECT * FROM monitored_repos WHERE id = ?", (repo_id,))
    return _row_to_response(row)


@router.patch("/repos/{repo_id}")
async def update_repo(repo_id: str, req: RepoUpdateRequest):
    """Update a monitored repository (toggle active, rename, update scan paths)."""
    existing = await db.fetch_one("SELECT * FROM monitored_repos WHERE id = ?", (repo_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Repo not found")

    now = datetime.now(timezone.utc).isoformat()
    updates = []
    params = []

    if req.is_active is not None:
        updates.append("is_active = ?")
        params.append(int(req.is_active))
    if req.display_name is not None:
        updates.append("display_name = ?")
        params.append(req.display_name)
    if req.scan_paths is not None:
        updates.append("scan_paths = ?")
        params.append(json.dumps(req.scan_paths))

    if updates:
        updates.append("updated_at = ?")
        params.append(now)
        params.append(repo_id)
        await db.execute(
            f"UPDATE monitored_repos SET {', '.join(updates)} WHERE id = ?",
            tuple(params),
        )

    row = await db.fetch_one("SELECT * FROM monitored_repos WHERE id = ?", (repo_id,))
    return _row_to_response(row)


@router.delete("/repos/{repo_id}")
async def remove_repo(repo_id: str):
    """Remove a monitored repository."""
    existing = await db.fetch_one("SELECT id FROM monitored_repos WHERE id = ?", (repo_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Repo not found")
    await db.execute("DELETE FROM monitored_repos WHERE id = ?", (repo_id,))
    return {"status": "deleted", "id": repo_id}
