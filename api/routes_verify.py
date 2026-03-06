"""Verify routes — deployment and testing."""

from __future__ import annotations

import json
from typing import Optional, Union

from fastapi import APIRouter, HTTPException, Query

from models import DeploymentResponse
from modules.github_client import GitHubClient
from modules.verify import VerifyModule
import database as db

router = APIRouter(tags=["Verify - Deployments"])

# ─── Module instances (created once, reused across requests) ────────────────

_github_client = GitHubClient()
_verify = VerifyModule(_github_client)


def _row_to_deployment_response(row: dict) -> DeploymentResponse:
    """Convert a database row dict to a DeploymentResponse model."""
    test_results_raw = row.get("test_results", "[]")
    if isinstance(test_results_raw, str):
        try:
            test_results = json.loads(test_results_raw)
        except (json.JSONDecodeError, TypeError):
            test_results = []
    else:
        test_results = test_results_raw or []

    return DeploymentResponse(
        id=row["id"],
        fix_id=row["fix_id"],
        environment=row.get("environment"),
        status=row.get("status"),
        test_results=test_results,
        pr_url=row.get("pr_url"),
        commit_sha=row.get("commit_sha"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


# ─── Routes ─────────────────────────────────────────────────────────────────


@router.get("/deployments")
async def list_deployments(
    environment: Optional[str] = Query(default=None, description="Filter by environment"),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """List all deployments with optional filtering and pagination."""
    conditions: list[str] = []
    params: list = []

    if environment:
        conditions.append("environment = ?")
        params.append(environment)
    if status:
        conditions.append("status = ?")
        params.append(status)

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    # Total count
    count_row = await db.fetch_one(
        f"SELECT COUNT(*) as cnt FROM deployments {where_clause}", tuple(params)
    )
    total = count_row["cnt"] if count_row else 0

    # Paginated results
    offset = (page - 1) * page_size
    rows = await db.fetch_all(
        f"SELECT * FROM deployments {where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        tuple(params) + (page_size, offset),
    )

    deployments = [_row_to_deployment_response(r) for r in rows]
    return {"deployments": deployments, "total": total, "page": page, "page_size": page_size}


@router.get("/deployments/{deployment_id}")
async def get_deployment(deployment_id: str):
    """Get a single deployment by ID."""
    try:
        row = await _verify.get_deployment_status(deployment_id)
        return _row_to_deployment_response(row)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/fixes/{fix_id}/deploy-staging")
async def deploy_to_staging(fix_id: str):
    """Deploy an approved fix to staging by creating a GitHub PR."""
    try:
        deployment_row = await _verify.deploy_to_staging(fix_id)
        return _row_to_deployment_response(deployment_row)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Staging deployment failed: {exc}")


@router.post("/deployments/{deployment_id}/promote")
async def promote_deployment(deployment_id: str):
    """Promote a staging deployment to production."""
    try:
        deployment_row = await _verify.promote_to_production(deployment_id)
        return _row_to_deployment_response(deployment_row)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Promotion failed: {exc}")
