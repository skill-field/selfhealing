"""CML Platform Integration routes — expose Cloudera AI capabilities in the UI."""

from __future__ import annotations

import os
import httpx
from fastapi import APIRouter

router = APIRouter(tags=["cml"])

CML_BASE = os.environ.get("CDSW_API_URL", "").rstrip("/") or None
CML_API_KEY = os.environ.get("CDSW_APIV2_KEY") or os.environ.get("CDSW_API_KEY") or None
PROJECT_ID = os.environ.get("CDSW_PROJECT_ID") or None


def _headers():
    if CML_API_KEY:
        return {"Authorization": f"Bearer {CML_API_KEY}"}
    return {}


@router.get("/cml/status")
async def cml_status():
    """Return CML platform integration status and available capabilities."""
    is_cml = bool(os.environ.get("CDSW_PROJECT_ID"))

    capabilities = {
        "is_cml": is_cml,
        "project_id": PROJECT_ID,
        "jobs": [],
        "models": [],
        "experiments": [],
        "applications": [],
    }

    if not is_cml or not CML_BASE or not CML_API_KEY:
        # Return static info when not running on CML or no API access
        capabilities["jobs"] = [
            {"name": "Scheduled AI Scan (30min)", "schedule": "*/30 * * * *", "status": "active", "script": "cml_scan.py"},
            {"name": "Auto-Heal Pipeline (hourly)", "schedule": "15 * * * *", "status": "active", "script": "cml_auto_heal.py"},
            {"name": "Reset + Real Scan", "schedule": "manual", "status": "active", "script": "cml_reset_scan.py"},
        ]
        capabilities["models"] = [
            {"name": "Sentinel Error Classifier", "status": "deployed", "endpoint": "REST API", "function": "predict"},
        ]
        capabilities["experiments"] = [
            {"name": "Sentinel Performance Tracking", "status": "active"},
        ]
        return capabilities

    # Live CML API queries
    api_base = f"{CML_BASE}/api/v2"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Jobs
            resp = await client.get(f"{api_base}/projects/{PROJECT_ID}/jobs", headers=_headers())
            if resp.status_code == 200:
                jobs_data = resp.json().get("jobs", [])
                capabilities["jobs"] = [
                    {
                        "id": j.get("id"),
                        "name": j.get("name"),
                        "script": j.get("script"),
                        "schedule": j.get("schedule") or "manual",
                        "status": "scheduled" if j.get("schedule") else "manual",
                    }
                    for j in jobs_data
                ]

            # Models
            resp = await client.get(f"{api_base}/projects/{PROJECT_ID}/models", headers=_headers())
            if resp.status_code == 200:
                models_data = resp.json().get("models", [])
                capabilities["models"] = [
                    {
                        "id": m.get("id"),
                        "name": m.get("name"),
                        "description": m.get("description"),
                        "status": m.get("status", "unknown"),
                    }
                    for m in models_data
                ]

            # Experiments
            resp = await client.get(f"{api_base}/projects/{PROJECT_ID}/experiments", headers=_headers())
            if resp.status_code == 200:
                exps_data = resp.json().get("experiments", [])
                capabilities["experiments"] = [
                    {
                        "id": e.get("id"),
                        "name": e.get("name"),
                        "status": e.get("status", "active"),
                    }
                    for e in exps_data
                ]

            # Applications
            resp = await client.get(f"{api_base}/projects/{PROJECT_ID}/applications", headers=_headers())
            if resp.status_code == 200:
                apps_data = resp.json().get("applications", [])
                capabilities["applications"] = [
                    {
                        "id": a.get("id"),
                        "name": a.get("name"),
                        "subdomain": a.get("subdomain"),
                        "status": a.get("status"),
                    }
                    for a in apps_data
                ]
    except Exception:
        pass

    return capabilities


@router.post("/cml/jobs/{job_id}/run")
async def trigger_job(job_id: str):
    """Trigger a CML job run from the UI."""
    if not CML_BASE or not CML_API_KEY or not PROJECT_ID:
        return {"status": "error", "message": "CML API not available"}

    api_base = f"{CML_BASE}/api/v2"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{api_base}/projects/{PROJECT_ID}/jobs/{job_id}/runs",
                headers={**_headers(), "Content-Type": "application/json"},
                json={},
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                return {"status": "ok", "run_id": data.get("id"), "job_status": data.get("status")}
            return {"status": "error", "message": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
