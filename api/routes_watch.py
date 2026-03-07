"""Watch routes — log ingestion and retrieval."""

import json
from fastapi import APIRouter, HTTPException
from models import LogEntry, LogBatchRequest, ErrorResponse
from modules.watch import WatchModule
from database import fetch_all
from api.routes_events import broadcast_event

router = APIRouter(prefix="/logs", tags=["Watch - Log Ingestion"])

watch_module = WatchModule()


def _error_row_to_response(row: dict) -> dict:
    """Convert a database row to an ErrorResponse-compatible dict."""
    result = dict(row)
    # Parse affected_files JSON string to list
    if isinstance(result.get("affected_files"), str):
        try:
            result["affected_files"] = json.loads(result["affected_files"])
        except (json.JSONDecodeError, TypeError):
            result["affected_files"] = []
    return result


@router.post("/ingest")
async def ingest_log(entry: LogEntry):
    """Ingest a single log entry and detect errors."""
    result = await watch_module.ingest_log(entry.model_dump())

    if result["error"] is None:
        return {"status": "accepted", "error_detected": False}

    error_data = _error_row_to_response(result["error"])

    # Broadcast SSE event if new error
    if result["is_new"]:
        await broadcast_event("error_detected", {
            "error_id": error_data["id"],
            "error_message": error_data.get("error_message"),
            "severity": error_data.get("severity"),
            "source": error_data.get("source"),
        })

    return {
        "status": "accepted",
        "error_detected": True,
        "is_new": result["is_new"],
        "error": error_data,
    }


@router.post("/ingest/batch")
async def ingest_batch(batch: LogBatchRequest):
    """Ingest a batch of log entries."""
    entries = [e.model_dump() for e in batch.entries]
    result = await watch_module.ingest_batch(entries)

    # Broadcast SSE events for new errors
    for r in result["results"]:
        if r["error"] is not None and r["is_new"]:
            error_data = r["error"]
            await broadcast_event("error_detected", {
                "error_id": error_data["id"],
                "error_message": error_data.get("error_message"),
                "severity": error_data.get("severity"),
                "source": error_data.get("source"),
            })

    return {
        "status": "accepted",
        "processed": result["processed"],
        "errors_detected": result["errors_detected"],
        "new_errors": result["new_errors"],
    }


@router.get("/recent")
async def get_recent_logs(limit: int = 50):
    """Get recent error entries as log entries for the Watch UI."""
    if limit < 1:
        limit = 1
    if limit > 200:
        limit = 200

    rows = await fetch_all(
        "SELECT * FROM errors ORDER BY last_seen DESC LIMIT ?",
        (limit,),
    )

    # Map error records to LogEntry shape expected by frontend
    logs = []
    for row in rows:
        r = _error_row_to_response(row)
        logs.append({
            "id": r["id"],
            "timestamp": r.get("last_seen") or r.get("created_at", ""),
            "level": {"critical": "ERROR", "high": "ERROR", "medium": "WARN", "low": "INFO"}.get(r.get("severity", "medium"), "WARN"),
            "message": r.get("error_message") or r.get("raw_log") or "",
            "source": r.get("source") or "unknown",
            "environment": r.get("environment"),
            # Include extra fields for detail views
            "error_type": r.get("error_type"),
            "stack_trace": r.get("stack_trace"),
            "status": r.get("status"),
            "occurrence_count": r.get("occurrence_count", 1),
            "fingerprint": r.get("fingerprint"),
        })

    return {"logs": logs, "total": len(logs)}
