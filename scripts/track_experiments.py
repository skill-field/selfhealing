#!/usr/bin/env python3
"""CML Experiment Tracking — Log scan, heal, and ML classifier metrics to MLflow.

Tracks Sentinel's performance over time using CML Experiments (MLflow):
- Error classification accuracy and distribution
- Fix quality: confidence scores, approval rates, deployment rates
- ML model performance: category/severity prediction accuracy
- Token usage and cost tracking
- Pipeline throughput: errors/hour, fixes/hour, MTTR
"""
from __future__ import annotations

import asyncio
import json
import logging
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

logger = logging.getLogger("sentinel.experiments")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")


async def gather_metrics() -> dict:
    """Query database for comprehensive metrics."""
    await init_db()

    metrics = {}

    # --- Error Metrics ---
    total_errors = await fetch_one("SELECT COUNT(*) as cnt FROM errors")
    metrics["total_errors"] = total_errors["cnt"] if total_errors else 0

    by_severity = await fetch_all(
        "SELECT severity, COUNT(*) as cnt FROM errors GROUP BY severity"
    )
    for row in (by_severity or []):
        metrics[f"errors_severity_{row['severity']}"] = row["cnt"]

    by_category = await fetch_all(
        "SELECT category, COUNT(*) as cnt FROM errors GROUP BY category"
    )
    for row in (by_category or []):
        metrics[f"errors_category_{row['category']}"] = row["cnt"]

    by_status = await fetch_all(
        "SELECT status, COUNT(*) as cnt FROM errors GROUP BY status"
    )
    for row in (by_status or []):
        metrics[f"errors_status_{row['status']}"] = row["cnt"]

    # --- Fix Metrics ---
    total_fixes = await fetch_one("SELECT COUNT(*) as cnt FROM fixes")
    metrics["total_fixes"] = total_fixes["cnt"] if total_fixes else 0

    avg_confidence = await fetch_one(
        "SELECT AVG(confidence) as avg_conf, MIN(confidence) as min_conf, "
        "MAX(confidence) as max_conf FROM fixes WHERE confidence IS NOT NULL"
    )
    if avg_confidence:
        metrics["fix_avg_confidence"] = round(avg_confidence["avg_conf"] or 0, 4)
        metrics["fix_min_confidence"] = round(avg_confidence["min_conf"] or 0, 4)
        metrics["fix_max_confidence"] = round(avg_confidence["max_conf"] or 0, 4)

    fix_by_status = await fetch_all(
        "SELECT status, COUNT(*) as cnt FROM fixes GROUP BY status"
    )
    for row in (fix_by_status or []):
        metrics[f"fix_status_{row['status']}"] = row["cnt"]

    # Fix approval rate
    approved = sum(r["cnt"] for r in (fix_by_status or []) if r["status"] in ("approved", "deployed"))
    total = metrics["total_fixes"]
    metrics["fix_approval_rate"] = round(approved / total, 4) if total > 0 else 0

    # Fix deployment rate
    deployed = sum(r["cnt"] for r in (fix_by_status or []) if r["status"] == "deployed")
    metrics["fix_deployment_rate"] = round(deployed / total, 4) if total > 0 else 0

    # --- Token Usage ---
    token_stats = await fetch_one(
        "SELECT SUM(prompt_tokens) as total_prompt, SUM(completion_tokens) as total_completion "
        "FROM fixes WHERE prompt_tokens IS NOT NULL"
    )
    if token_stats:
        metrics["total_prompt_tokens"] = token_stats["total_prompt"] or 0
        metrics["total_completion_tokens"] = token_stats["total_completion"] or 0
        metrics["total_tokens"] = (token_stats["total_prompt"] or 0) + (token_stats["total_completion"] or 0)

    # --- MTTR ---
    mttr_row = await fetch_one(
        """SELECT AVG(
            (julianday(f.updated_at) - julianday(e.created_at)) * 24 * 60
        ) AS avg_minutes
        FROM fixes f
        JOIN errors e ON f.error_id = e.id
        WHERE f.status = 'deployed'"""
    )
    metrics["mttr_minutes"] = round(mttr_row["avg_minutes"], 2) if mttr_row and mttr_row["avg_minutes"] else 0

    # --- Deployment Metrics ---
    total_deployments = await fetch_one("SELECT COUNT(*) as cnt FROM deployments")
    metrics["total_deployments"] = total_deployments["cnt"] if total_deployments else 0

    # --- Feature Metrics ---
    total_features = await fetch_one("SELECT COUNT(*) as cnt FROM feature_requests")
    metrics["total_features"] = total_features["cnt"] if total_features else 0

    feat_by_status = await fetch_all(
        "SELECT status, COUNT(*) as cnt FROM feature_requests GROUP BY status"
    )
    for row in (feat_by_status or []):
        metrics[f"feature_status_{row['status']}"] = row["cnt"]

    # --- Repository Metrics ---
    active_repos = await fetch_one(
        "SELECT COUNT(*) as cnt FROM monitored_repos WHERE is_active = 1"
    )
    metrics["active_repos"] = active_repos["cnt"] if active_repos else 0

    # --- ML Model Metrics ---
    model_report_path = os.path.join(PROJECT_ROOT, "data", "models", "training_report.json")
    if os.path.exists(model_report_path):
        try:
            with open(model_report_path) as f:
                report = json.load(f)
            if "category" in report:
                metrics["ml_category_accuracy"] = report["category"].get("accuracy", 0)
                metrics["ml_category_f1"] = report["category"].get("f1_macro", 0)
                metrics["ml_category_model"] = report["category"].get("model_type", "unknown")
            if "severity" in report:
                metrics["ml_severity_accuracy"] = report["severity"].get("accuracy", 0)
                metrics["ml_severity_f1"] = report["severity"].get("f1_macro", 0)
            metrics["ml_training_samples"] = report.get("samples", 0)
        except Exception as e:
            logger.warning("Could not load ML training report: %s", e)

    return metrics


async def log_experiment_metrics():
    """Gather metrics and log to MLflow (CML Experiments)."""
    metrics = await gather_metrics()
    now = datetime.now(timezone.utc).isoformat()

    # Try MLflow first (available in CML)
    try:
        import mlflow
        use_mlflow = True
    except ImportError:
        use_mlflow = False
        logger.info("MLflow not available, printing metrics only")

    if use_mlflow:
        mlflow.set_experiment("Sentinel Performance")
        with mlflow.start_run(run_name=f"metrics-{now[:16]}"):
            # Parameters
            mlflow.log_param("timestamp", now)
            mlflow.log_param("platform", "cloudera_cml")
            mlflow.log_param("model", "claude-sonnet-4-5")

            # Log all numeric metrics
            for k, v in metrics.items():
                if isinstance(v, (int, float)):
                    mlflow.log_metric(k, v)

            # Log string values as params
            for k, v in metrics.items():
                if isinstance(v, str):
                    mlflow.log_param(k, v)

        logger.info("Logged %d metrics to MLflow experiment 'Sentinel Performance'", len(metrics))
    else:
        logger.info("Metrics snapshot at %s:", now)
        for k, v in sorted(metrics.items()):
            logger.info("  %s: %s", k, v)

    return metrics


if __name__ == "__main__":
    asyncio.run(log_experiment_metrics())
