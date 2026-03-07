#!/usr/bin/env python3
"""CML Experiment Tracking — Log scan and heal metrics to MLflow.

Tracks Sentinel's AI performance over time:
- Scan accuracy and issue distribution
- Fix quality and confidence scores
- Token usage and response times
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timezone

try:
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    PROJECT_ROOT = os.getcwd()
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

from database import init_db, fetch_all, fetch_one


async def log_experiment_metrics():
    """Query current DB state and log metrics."""
    await init_db()

    # Try MLflow first (available in CML), fall back to printing
    try:
        import mlflow
        use_mlflow = True
    except ImportError:
        use_mlflow = False
        print("[Experiments] MLflow not available, printing metrics only", flush=True)

    now = datetime.now(timezone.utc).isoformat()

    # Gather metrics
    total_errors = await fetch_one("SELECT COUNT(*) as cnt FROM errors")
    by_severity = await fetch_all(
        "SELECT severity, COUNT(*) as cnt FROM errors GROUP BY severity"
    )
    by_category = await fetch_all(
        "SELECT category, COUNT(*) as cnt FROM errors GROUP BY category"
    )
    by_status = await fetch_all(
        "SELECT status, COUNT(*) as cnt FROM errors GROUP BY status"
    )
    total_fixes = await fetch_one("SELECT COUNT(*) as cnt FROM fixes")
    avg_confidence = await fetch_one(
        "SELECT AVG(confidence) as avg_conf FROM fixes WHERE confidence IS NOT NULL"
    )
    fix_by_status = await fetch_all(
        "SELECT status, COUNT(*) as cnt FROM fixes GROUP BY status"
    )
    active_repos = await fetch_one(
        "SELECT COUNT(*) as cnt FROM monitored_repos WHERE is_active = 1"
    )

    metrics = {
        "total_errors": total_errors["cnt"] if total_errors else 0,
        "total_fixes": total_fixes["cnt"] if total_fixes else 0,
        "avg_fix_confidence": round(avg_confidence["avg_conf"] or 0, 3) if avg_confidence else 0,
        "active_repos": active_repos["cnt"] if active_repos else 0,
    }

    # Add severity breakdown
    for row in (by_severity or []):
        metrics[f"errors_{row['severity']}"] = row["cnt"]

    # Add category breakdown
    for row in (by_category or []):
        metrics[f"category_{row['category']}"] = row["cnt"]

    # Add status breakdown
    for row in (by_status or []):
        metrics[f"status_{row['status']}"] = row["cnt"]

    # Add fix status breakdown
    for row in (fix_by_status or []):
        metrics[f"fix_{row['status']}"] = row["cnt"]

    if use_mlflow:
        mlflow.set_experiment("Sentinel Performance")
        with mlflow.start_run(run_name=f"metrics-{now[:10]}"):
            mlflow.log_param("timestamp", now)
            mlflow.log_param("platform", "cloudera_cml")
            mlflow.log_param("model", "claude-sonnet-4-20250514")
            for k, v in metrics.items():
                mlflow.log_metric(k, v)
        print(f"[Experiments] Logged {len(metrics)} metrics to MLflow", flush=True)
    else:
        print(f"[Experiments] Metrics snapshot at {now}:", flush=True)
        for k, v in sorted(metrics.items()):
            print(f"  {k}: {v}", flush=True)

    return metrics


if __name__ == "__main__":
    asyncio.run(log_experiment_metrics())
