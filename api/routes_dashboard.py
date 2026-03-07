"""Dashboard routes — summary, timeline, and audit log."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter

from database import fetch_all, fetch_one
from models import (
    AuditLogEntry,
    DashboardSummary,
    ErrorResponse,
    ErrorStats,
    FixResponse,
)

router = APIRouter(tags=["Dashboard"])


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _safe_json(value: str | None, default=None):
    """Parse a JSON string, returning *default* on failure."""
    if value is None:
        return default if default is not None else []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else []


def _row_to_error(row: dict) -> ErrorResponse:
    return ErrorResponse(
        id=row["id"],
        source=row.get("source"),
        environment=row.get("environment"),
        raw_log=row.get("raw_log"),
        error_message=row.get("error_message"),
        error_type=row.get("error_type"),
        stack_trace=row.get("stack_trace"),
        severity=row.get("severity"),
        category=row.get("category"),
        root_cause=row.get("root_cause"),
        affected_file=row.get("affected_file"),
        affected_files=_safe_json(row.get("affected_files"), []),
        fingerprint=row.get("fingerprint"),
        occurrence_count=row.get("occurrence_count", 1),
        first_seen=row.get("first_seen"),
        last_seen=row.get("last_seen"),
        status=row.get("status", "new"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_fix(row: dict) -> FixResponse:
    return FixResponse(
        id=row["id"],
        error_id=row["error_id"],
        diff=row.get("diff"),
        explanation=row.get("explanation"),
        files_changed=_safe_json(row.get("files_changed"), []),
        confidence=round(row["confidence"] * 100, 1) if row.get("confidence") is not None and row["confidence"] <= 1 else row.get("confidence"),
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


def _row_to_audit(row: dict) -> AuditLogEntry:
    return AuditLogEntry(
        id=row["id"],
        action=row["action"],
        entity_type=row.get("entity_type"),
        entity_id=row.get("entity_id"),
        details=_safe_json(row.get("details"), {}),
        actor=row.get("actor"),
        created_at=row["created_at"],
    )


# ─── GET /dashboard/summary ─────────────────────────────────────────────────

@router.get("/dashboard/summary", response_model=DashboardSummary)
async def get_dashboard_summary():
    """Get dashboard summary with key metrics from the database."""

    # ── Errors ────────────────────────────────────────────────────────────
    total_errors_row = await fetch_one("SELECT COUNT(*) AS cnt FROM errors")
    total_errors = total_errors_row["cnt"] if total_errors_row else 0

    open_statuses = ("new", "acknowledged", "fix_generated", "fix_approved")
    open_errors_row = await fetch_one(
        f"SELECT COUNT(*) AS cnt FROM errors WHERE status IN ({','.join('?' for _ in open_statuses)})",
        open_statuses,
    )
    open_errors = open_errors_row["cnt"] if open_errors_row else 0

    severity_rows = await fetch_all(
        "SELECT severity, COUNT(*) AS cnt FROM errors GROUP BY severity"
    )
    by_severity = {r["severity"]: r["cnt"] for r in severity_rows}

    category_rows = await fetch_all(
        "SELECT category, COUNT(*) AS cnt FROM errors GROUP BY category"
    )
    by_category = {r["category"]: r["cnt"] for r in category_rows}

    status_rows = await fetch_all(
        "SELECT status, COUNT(*) AS cnt FROM errors GROUP BY status"
    )
    by_status = {r["status"]: r["cnt"] for r in status_rows}

    # Last 24 h
    cutoff_24h = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    new_24_row = await fetch_one(
        "SELECT COUNT(*) AS cnt FROM errors WHERE created_at >= ?", (cutoff_24h,)
    )
    new_last_24h = new_24_row["cnt"] if new_24_row else 0

    resolved_24_row = await fetch_one(
        "SELECT COUNT(*) AS cnt FROM errors WHERE status = 'resolved' AND updated_at >= ?",
        (cutoff_24h,),
    )
    resolved_last_24h = resolved_24_row["cnt"] if resolved_24_row else 0

    # ── Fixes ─────────────────────────────────────────────────────────────
    total_fixes_row = await fetch_one("SELECT COUNT(*) AS cnt FROM fixes")
    total_fixes = total_fixes_row["cnt"] if total_fixes_row else 0

    fixes_deployed_row = await fetch_one(
        "SELECT COUNT(*) AS cnt FROM fixes WHERE status = 'deployed'"
    )
    fixes_deployed = fixes_deployed_row["cnt"] if fixes_deployed_row else 0

    fix_status_rows = await fetch_all(
        "SELECT status, COUNT(*) AS cnt FROM fixes GROUP BY status"
    )
    fixes_by_status = {r["status"]: r["cnt"] for r in fix_status_rows}

    # Success rate = deployed / total fixes (avoid div-by-zero)
    success_rate = round(fixes_deployed / total_fixes, 4) if total_fixes > 0 else 0.0

    # ── MTTR (mean time to resolve) ───────────────────────────────────────
    # Average minutes between error created_at and its fix being deployed
    mttr_row = await fetch_one(
        """
        SELECT AVG(
            (julianday(f.updated_at) - julianday(e.created_at)) * 24 * 60
        ) AS avg_minutes
        FROM fixes f
        JOIN errors e ON f.error_id = e.id
        WHERE f.status = 'deployed'
        """
    )
    mttr_minutes = round(mttr_row["avg_minutes"], 2) if mttr_row and mttr_row["avg_minutes"] else 0.0

    # ── Deployments ───────────────────────────────────────────────────────
    total_deployments_row = await fetch_one("SELECT COUNT(*) AS cnt FROM deployments")
    total_deployments = total_deployments_row["cnt"] if total_deployments_row else 0

    # ── Features ──────────────────────────────────────────────────────────
    total_features_row = await fetch_one("SELECT COUNT(*) AS cnt FROM feature_requests")
    total_features = total_features_row["cnt"] if total_features_row else 0

    # ── Recent items ──────────────────────────────────────────────────────
    recent_error_rows = await fetch_all(
        "SELECT * FROM errors ORDER BY created_at DESC LIMIT 10"
    )
    recent_errors = [_row_to_error(r) for r in recent_error_rows]

    recent_fix_rows = await fetch_all(
        "SELECT * FROM fixes ORDER BY created_at DESC LIMIT 10"
    )
    recent_fixes = [_row_to_fix(r) for r in recent_fix_rows]

    # ── System health (simple check: tables exist and are queryable) ─────
    system_health = {
        "metrics_app": "connected",
        "github_api": "connected",
        "claude_api": "connected",
    }

    return DashboardSummary(
        total_errors=total_errors,
        open_errors=open_errors,
        fixes_generated=total_fixes,
        fixes_deployed=fixes_deployed,
        features_submitted=total_features,
        success_rate=success_rate,
        error_stats=ErrorStats(
            total_errors=total_errors,
            by_severity=by_severity,
            by_category=by_category,
            by_status=by_status,
            new_last_24h=new_last_24h,
            resolved_last_24h=resolved_last_24h,
        ),
        recent_errors=recent_errors,
        recent_fixes=recent_fixes,
        # Extra fields the frontend can consume
        errors_by_severity=by_severity,
        errors_by_category=by_category,
        errors_by_status=by_status,
        total_fixes=total_fixes,
        fixes_by_status=fixes_by_status,
        total_deployments=total_deployments,
        total_features=total_features,
        mttr_minutes=mttr_minutes,
        system_health=system_health,
    )


# ─── GET /dashboard/timeline ────────────────────────────────────────────────

@router.get("/dashboard/timeline")
async def get_timeline(hours: int = 24):
    """Return error/fix/deployment counts grouped by hour for the last *hours* hours."""
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(hours=hours)).isoformat()

    # Errors by hour
    error_rows = await fetch_all(
        """
        SELECT strftime('%Y-%m-%dT%H:00:00Z', created_at) AS hour,
               COUNT(*) AS cnt
        FROM errors
        WHERE created_at >= ?
        GROUP BY hour
        ORDER BY hour
        """,
        (cutoff,),
    )
    error_map = {r["hour"]: r["cnt"] for r in error_rows}

    # Fixes by hour
    fix_rows = await fetch_all(
        """
        SELECT strftime('%Y-%m-%dT%H:00:00Z', created_at) AS hour,
               COUNT(*) AS cnt
        FROM fixes
        WHERE created_at >= ?
        GROUP BY hour
        ORDER BY hour
        """,
        (cutoff,),
    )
    fix_map = {r["hour"]: r["cnt"] for r in fix_rows}

    # Deployments by hour
    deploy_rows = await fetch_all(
        """
        SELECT strftime('%Y-%m-%dT%H:00:00Z', created_at) AS hour,
               COUNT(*) AS cnt
        FROM deployments
        WHERE created_at >= ?
        GROUP BY hour
        ORDER BY hour
        """,
        (cutoff,),
    )
    deploy_map = {r["hour"]: r["cnt"] for r in deploy_rows}

    # Build a continuous timeline covering every hour in the window
    timeline = []
    for i in range(hours):
        hour_dt = now - timedelta(hours=hours - 1 - i)
        hour_key = hour_dt.strftime("%Y-%m-%dT%H:00:00Z")
        timeline.append({
            "hour": hour_key,
            "errors": error_map.get(hour_key, 0),
            "fixes": fix_map.get(hour_key, 0),
            "deployments": deploy_map.get(hour_key, 0),
        })

    return {"timeline": timeline, "hours": hours}


# ─── GET /audit-log ─────────────────────────────────────────────────────────

@router.get("/audit-log")
async def get_audit_log(
    page: int = 1,
    page_size: int = 50,
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
):
    """Return paginated audit log entries, most recent first."""
    where_clauses: list[str] = []
    params: list[str] = []

    if entity_type:
        where_clauses.append("entity_type = ?")
        params.append(entity_type)
    if action:
        where_clauses.append("action = ?")
        params.append(action)

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    # Total count
    total_row = await fetch_one(
        f"SELECT COUNT(*) AS cnt FROM audit_log {where_sql}", tuple(params)
    )
    total = total_row["cnt"] if total_row else 0

    # Paginated results
    offset = (page - 1) * page_size
    rows = await fetch_all(
        f"SELECT * FROM audit_log {where_sql} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        tuple(params) + (page_size, offset),
    )

    entries = [_row_to_audit(r) for r in rows]

    return {
        "entries": [e.model_dump() for e in entries],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
