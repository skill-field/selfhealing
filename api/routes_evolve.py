"""Evolve routes — feature request generation."""

from __future__ import annotations

import json
from typing import Optional, Union

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from models import FeatureRequest, FeatureResponse
from llm.client import AnthropicClient
from modules.github_client import GitHubClient
from modules.evolve import EvolveModule
import database as db

router = APIRouter(prefix="/features", tags=["Evolve - Feature Generation"])

# ─── Module instances (created once, reused across requests) ────────────────

_github_client = GitHubClient()
_anthropic_client = AnthropicClient()
_evolve = EvolveModule(_anthropic_client, _github_client)


# ─── Request models for approve/reject ─────────────────────────────────────

class FeatureApproveRequest(BaseModel):
    """Request to approve a feature."""
    reviewer_notes: Optional[str] = Field(default=None, description="Optional reviewer notes")


class FeatureRejectRequest(BaseModel):
    """Request to reject a feature."""
    reviewer_notes: str = Field(..., min_length=1, description="Reason for rejection")


# ─── Helpers ────────────────────────────────────────────────────────────────

def _row_to_feature_response(row: dict) -> FeatureResponse:
    """Convert a database row dict to a FeatureResponse model."""
    generated_code_raw = row.get("generated_code", "{}")
    if isinstance(generated_code_raw, str):
        try:
            generated_code = json.loads(generated_code_raw)
        except (json.JSONDecodeError, TypeError):
            generated_code = None
    else:
        generated_code = generated_code_raw

    return FeatureResponse(
        id=row["id"],
        title=row["title"],
        description=row.get("description"),
        priority=row.get("priority"),
        generated_code=generated_code,
        generated_diff=row.get("generated_diff"),
        explanation=row.get("explanation"),
        model_used=row.get("model_used"),
        status=row.get("status", "submitted"),
        reviewer_notes=row.get("reviewer_notes"),
        pr_url=row.get("pr_url"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


# ─── Routes ─────────────────────────────────────────────────────────────────


@router.post("", response_model=Union[FeatureResponse, dict])
async def create_feature(request: FeatureRequest):
    """Submit a new feature request."""
    try:
        feature_row = await _evolve.submit_feature(
            title=request.title,
            description=request.description,
            priority=request.priority or "medium",
        )
        return _row_to_feature_response(feature_row)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Feature submission failed: {exc}")


@router.get("")
async def list_features(
    status: Optional[str] = Query(default=None, description="Filter by status"),
    priority: Optional[str] = Query(default=None, description="Filter by priority"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """List all feature requests with optional filtering and pagination."""
    conditions: list[str] = []
    params: list = []

    if status:
        conditions.append("status = ?")
        params.append(status)
    if priority:
        conditions.append("priority = ?")
        params.append(priority)

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    # Total count
    count_row = await db.fetch_one(
        f"SELECT COUNT(*) as cnt FROM feature_requests {where_clause}", tuple(params)
    )
    total = count_row["cnt"] if count_row else 0

    # Paginated results
    offset = (page - 1) * page_size
    rows = await db.fetch_all(
        f"SELECT * FROM feature_requests {where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        tuple(params) + (page_size, offset),
    )

    features = [_row_to_feature_response(r) for r in rows]
    return {"features": features, "total": total, "page": page, "page_size": page_size}


@router.get("/{feature_id}")
async def get_feature(feature_id: str):
    """Get a single feature request by ID."""
    row = await db.fetch_one(
        "SELECT * FROM feature_requests WHERE id = ?", (feature_id,)
    )
    if row is None:
        raise HTTPException(status_code=404, detail=f"Feature {feature_id} not found")
    return _row_to_feature_response(row)


@router.post("/{feature_id}/generate")
async def generate_feature_code(feature_id: str):
    """Generate code for a feature request using AI."""
    try:
        feature_row = await _evolve.generate_feature(feature_id)
        return _row_to_feature_response(feature_row)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Feature generation failed: {exc}")


@router.post("/{feature_id}/approve")
async def approve_feature(feature_id: str, request: Optional[FeatureApproveRequest] = None):
    """Approve a generated feature and optionally create a GitHub PR."""
    reviewer_notes = request.reviewer_notes if request else None
    try:
        feature_row = await _evolve.approve_feature(feature_id, reviewer_notes=reviewer_notes)
        return _row_to_feature_response(feature_row)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Feature approval failed: {exc}")


@router.post("/{feature_id}/reject")
async def reject_feature(feature_id: str, request: FeatureRejectRequest):
    """Reject a feature request."""
    try:
        feature_row = await _evolve.reject_feature(feature_id, reviewer_notes=request.reviewer_notes)
        return _row_to_feature_response(feature_row)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Feature rejection failed: {exc}")
