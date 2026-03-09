"""Heal routes — fix generation and management."""

from __future__ import annotations

import json
from typing import Optional, Union

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from models import (
    FixGenerateRequest,
    FixApproveRequest,
    FixRejectRequest,
    FixResponse,
    FixListResponse,
)
from llm.client import AnthropicClient
from llm.context_builder import ContextBuilder
from modules.github_client import GitHubClient
from modules.heal import HealModule
import database as db

router = APIRouter(tags=["Heal - Fix Generation"])

# ─── Module instances (created once, reused across requests) ────────────────

_github_client = GitHubClient()
_anthropic_client = AnthropicClient()
_context_builder = ContextBuilder(_github_client)
_heal = HealModule(_anthropic_client, _github_client, _context_builder)


def _row_to_fix_response(row: dict) -> FixResponse:
    """Convert a database row dict to a FixResponse model."""
    files_changed_raw = row.get("files_changed", "[]")
    if isinstance(files_changed_raw, str):
        try:
            files_changed = json.loads(files_changed_raw)
        except (json.JSONDecodeError, TypeError):
            files_changed = []
    else:
        files_changed = files_changed_raw or []

    return FixResponse(
        id=row["id"],
        error_id=row["error_id"],
        diff=row.get("diff"),
        explanation=row.get("explanation"),
        files_changed=files_changed,
        confidence=round(row["confidence"] * 100, 1) if row.get("confidence") is not None and 0 < row["confidence"] <= 1 else row.get("confidence"),
        model_used=row.get("model_used"),
        prompt_tokens=row.get("prompt_tokens"),
        completion_tokens=row.get("completion_tokens"),
        status=row.get("status", "pending"),
        reviewer_notes=row.get("reviewer_notes"),
        attempt_number=row.get("attempt_number", 1),
        guidance=row.get("guidance"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


# ─── Routes ─────────────────────────────────────────────────────────────────


@router.post("/errors/{error_id}/generate-fix")
async def generate_fix(error_id: str, request: Optional[FixGenerateRequest] = None):
    """Generate an AI fix for a specific error."""
    guidance = request.guidance if request else None
    try:
        fix_row = await _heal.generate_fix(error_id, guidance=guidance)
        return _row_to_fix_response(fix_row)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Fix generation failed: {exc}")


@router.get("/fixes", response_model=FixListResponse)
async def list_fixes(
    status: Optional[str] = Query(default=None, description="Filter by status"),
    error_id: Optional[str] = Query(default=None, description="Filter by error ID"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """List all fixes with optional status/error filtering and pagination."""
    conditions: list[str] = []
    params: list = []

    if status:
        conditions.append("status = ?")
        params.append(status)
    if error_id:
        conditions.append("error_id = ?")
        params.append(error_id)

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    # Total count
    count_row = await db.fetch_one(
        f"SELECT COUNT(*) as cnt FROM fixes {where_clause}", tuple(params)
    )
    total = count_row["cnt"] if count_row else 0

    # Paginated results
    offset = (page - 1) * page_size
    rows = await db.fetch_all(
        f"SELECT * FROM fixes {where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        tuple(params) + (page_size, offset),
    )

    fixes = [_row_to_fix_response(r) for r in rows]
    return FixListResponse(fixes=fixes, total=total)


@router.get("/fixes/{fix_id}", response_model=Union[FixResponse, dict])
async def get_fix(fix_id: str):
    """Get a single fix by ID."""
    row = await db.fetch_one("SELECT * FROM fixes WHERE id = ?", (fix_id,))
    if row is None:
        raise HTTPException(status_code=404, detail=f"Fix {fix_id} not found")
    return _row_to_fix_response(row)


@router.post("/fixes/{fix_id}/approve")
async def approve_fix(fix_id: str, request: Optional[FixApproveRequest] = None):
    """Approve a generated fix."""
    reviewer_notes = request.reviewer_notes if request else None
    try:
        fix_row = await _heal.approve_fix(fix_id, reviewer_notes=reviewer_notes)
        return _row_to_fix_response(fix_row)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Fix approval failed: {exc}")


@router.post("/fixes/{fix_id}/reject")
async def reject_fix(fix_id: str, request: FixRejectRequest):
    """Reject a generated fix."""
    try:
        fix_row = await _heal.reject_fix(fix_id, reason=request.reason)
        return _row_to_fix_response(fix_row)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Fix rejection failed: {exc}")


@router.post("/fixes/{fix_id}/regenerate")
async def regenerate_fix(fix_id: str, request: Optional[FixGenerateRequest] = None):
    """Regenerate a fix with optional guidance.

    Looks up the original error_id from the fix, then calls generate_fix again.
    """
    fix_row = await db.fetch_one("SELECT * FROM fixes WHERE id = ?", (fix_id,))
    if fix_row is None:
        raise HTTPException(status_code=404, detail=f"Fix {fix_id} not found")

    guidance = request.guidance if request else None
    try:
        new_fix_row = await _heal.generate_fix(fix_row["error_id"], guidance=guidance)
        return _row_to_fix_response(new_fix_row)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Fix regeneration failed: {exc}")
