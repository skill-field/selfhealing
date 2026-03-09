"""Think routes — error analysis and classification."""

import json
from typing import Optional
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException, Query
from models import ErrorListResponse, ErrorResponse, ErrorStats
from database import execute, fetch_one, fetch_all
from modules.think import ThinkModule
from api.routes_events import broadcast_event

router = APIRouter(prefix="/errors", tags=["Think - Error Analysis"])

think_module = ThinkModule()


def _row_to_error_response(row: dict) -> ErrorResponse:
    """Convert a database row dict to an ErrorResponse model."""
    data = dict(row)
    # Parse affected_files JSON string
    if isinstance(data.get("affected_files"), str):
        try:
            data["affected_files"] = json.loads(data["affected_files"])
        except (json.JSONDecodeError, TypeError):
            data["affected_files"] = []
    return ErrorResponse(**data)


@router.get("", response_model=ErrorListResponse)
async def list_errors(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    category: Optional[str] = None,
):
    """List all errors with optional filtering and pagination."""
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 1
    if page_size > 100:
        page_size = 100

    # Build dynamic WHERE clause
    conditions = []
    params: list = []

    if status:
        conditions.append("status = ?")
        params.append(status)
    if severity:
        conditions.append("severity = ?")
        params.append(severity)
    if category:
        conditions.append("category = ?")
        params.append(category)

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    # Get total count
    count_row = await fetch_one(
        f"SELECT COUNT(*) as cnt FROM errors {where_clause}",
        tuple(params),
    )
    total = count_row["cnt"] if count_row else 0

    # Fetch page
    offset = (page - 1) * page_size
    rows = await fetch_all(
        f"SELECT * FROM errors {where_clause} ORDER BY last_seen DESC LIMIT ? OFFSET ?",
        tuple(params + [page_size, offset]),
    )

    errors = [_row_to_error_response(row) for row in rows]
    return ErrorListResponse(errors=errors, total=total, page=page, page_size=page_size)


@router.get("/stats", response_model=ErrorStats)
async def get_error_stats():
    """Get error statistics — counts by severity, category, status, and recent trends."""
    # Total
    total_row = await fetch_one("SELECT COUNT(*) as cnt FROM errors")
    total_errors = total_row["cnt"] if total_row else 0

    # By severity
    severity_rows = await fetch_all(
        "SELECT severity, COUNT(*) as cnt FROM errors WHERE severity IS NOT NULL GROUP BY severity"
    )
    by_severity = {row["severity"]: row["cnt"] for row in severity_rows}

    # By category
    category_rows = await fetch_all(
        "SELECT category, COUNT(*) as cnt FROM errors WHERE category IS NOT NULL GROUP BY category"
    )
    by_category = {row["category"]: row["cnt"] for row in category_rows}

    # By status
    status_rows = await fetch_all(
        "SELECT status, COUNT(*) as cnt FROM errors GROUP BY status"
    )
    by_status = {row["status"]: row["cnt"] for row in status_rows}

    # Last 24 hours
    now = datetime.now(timezone.utc)
    yesterday = (now - timedelta(hours=24)).isoformat()

    new_row = await fetch_one(
        "SELECT COUNT(*) as cnt FROM errors WHERE first_seen >= ?",
        (yesterday,),
    )
    new_last_24h = new_row["cnt"] if new_row else 0

    resolved_row = await fetch_one(
        "SELECT COUNT(*) as cnt FROM errors WHERE status = 'resolved' AND updated_at >= ?",
        (yesterday,),
    )
    resolved_last_24h = resolved_row["cnt"] if resolved_row else 0

    return ErrorStats(
        total_errors=total_errors,
        by_severity=by_severity,
        by_category=by_category,
        by_status=by_status,
        new_last_24h=new_last_24h,
        resolved_last_24h=resolved_last_24h,
    )


@router.get("/{error_id}", response_model=ErrorResponse)
async def get_error(error_id: str):
    """Get a single error by ID with full details."""
    row = await fetch_one("SELECT * FROM errors WHERE id = ?", (error_id,))
    if not row:
        raise HTTPException(status_code=404, detail=f"Error {error_id} not found")
    return _row_to_error_response(row)


@router.post("/{error_id}/classify")
async def classify_error(error_id: str):
    """Re-trigger classification and root cause analysis for an error."""
    # Verify error exists
    row = await fetch_one("SELECT * FROM errors WHERE id = ?", (error_id,))
    if not row:
        raise HTTPException(status_code=404, detail=f"Error {error_id} not found")

    result = await think_module.analyze_root_cause(error_id)

    if result.get("error") == "not_found":
        raise HTTPException(status_code=404, detail=result.get("message"))

    # Broadcast SSE event
    await broadcast_event("classification_done", {
        "error_id": error_id,
        "category": result.get("category"),
        "severity": result.get("severity"),
        "root_cause": result.get("root_cause"),
    })

    return result


@router.patch("/{error_id}/status")
async def update_error_status(error_id: str, status: str = Query(...)):
    """Update error status."""
    from constants import VALID_ERROR_STATUSES
    if status not in VALID_ERROR_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{status}'. Must be one of: {', '.join(sorted(VALID_ERROR_STATUSES))}",
        )

    row = await fetch_one("SELECT * FROM errors WHERE id = ?", (error_id,))
    if not row:
        raise HTTPException(status_code=404, detail=f"Error {error_id} not found")

    now = datetime.now(timezone.utc).isoformat()
    await execute(
        "UPDATE errors SET status = ?, updated_at = ? WHERE id = ?",
        (status, now, error_id),
    )

    updated = await fetch_one("SELECT * FROM errors WHERE id = ?", (error_id,))
    return _row_to_error_response(updated)
