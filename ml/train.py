"""Train error classifier models on Sentinel's historical data.

This script:
1. Loads error data from the Sentinel SQLite database
2. Extracts features using the same feature extraction as the classifier
3. Trains scikit-learn models (category + severity)
4. Evaluates accuracy with cross-validation
5. Saves models to data/models/
6. Logs metrics to MLflow (CML Experiments) if available

Run as a CML Job for proper experiment tracking.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import cross_val_score, train_test_split

# Setup path
try:
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    PROJECT_ROOT = os.getcwd()
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

from ml.classifier import (
    CATEGORIES,
    CATEGORY_MODEL_PATH,
    MODEL_DIR,
    SEVERITIES,
    SEVERITY_MODEL_PATH,
    extract_features,
)

logger = logging.getLogger("sentinel.train")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")


async def load_training_data() -> list[dict]:
    """Load labeled error data from the database."""
    from database import init_db, fetch_all

    await init_db()
    rows = await fetch_all(
        "SELECT error_message, error_type, stack_trace, category, severity "
        "FROM errors WHERE category IS NOT NULL AND severity IS NOT NULL"
    )
    return rows


def prepare_dataset(rows: list[dict]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Convert error records to feature matrix and label vectors."""
    X_list = []
    y_cat = []
    y_sev = []

    cat_to_idx = {c: i for i, c in enumerate(CATEGORIES)}
    sev_to_idx = {s: i for i, s in enumerate(SEVERITIES)}

    for row in rows:
        category = row.get("category", "unknown")
        severity = row.get("severity", "medium")

        if category not in cat_to_idx or severity not in sev_to_idx:
            continue

        features = extract_features(
            error_message=row.get("error_message") or "",
            error_type=row.get("error_type") or "",
            stack_trace=row.get("stack_trace") or "",
        )
        X_list.append(features)
        y_cat.append(cat_to_idx[category])
        y_sev.append(sev_to_idx[severity])

    return np.array(X_list), np.array(y_cat), np.array(y_sev)


def train_and_evaluate(
    X: np.ndarray,
    y: np.ndarray,
    label_names: list[str],
    task_name: str,
) -> tuple[object, dict]:
    """Train multiple models, pick the best, return model + metrics."""
    logger.info("Training %s classifier on %d samples", task_name, len(X))

    if len(X) < 10:
        logger.warning("Too few samples (%d) for reliable training. Using simple model.", len(X))
        model = LogisticRegression(max_iter=1000, random_state=42)
        model.fit(X, y)
        y_pred = model.predict(X)
        return model, {
            "accuracy": float(accuracy_score(y, y_pred)),
            "f1_macro": float(f1_score(y, y_pred, average="macro", zero_division=0)),
            "model_type": "logistic_regression",
            "samples": len(X),
            "cv_folds": 0,
        }

    # Compare three classifiers
    candidates = {
        "gradient_boosting": GradientBoostingClassifier(
            n_estimators=100, max_depth=4, random_state=42
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=100, max_depth=6, random_state=42
        ),
        "logistic_regression": LogisticRegression(
            max_iter=1000, random_state=42
        ),
    }

    best_model = None
    best_score = -1.0
    best_name = ""
    all_results = {}

    cv_folds = min(5, len(X))
    if cv_folds < 2:
        cv_folds = 2

    for name, model in candidates.items():
        try:
            scores = cross_val_score(model, X, y, cv=cv_folds, scoring="f1_macro")
            mean_score = float(scores.mean())
            all_results[name] = {
                "cv_f1_mean": mean_score,
                "cv_f1_std": float(scores.std()),
            }
            logger.info("  %s: CV F1=%.3f (+/- %.3f)", name, mean_score, scores.std())

            if mean_score > best_score:
                best_score = mean_score
                best_name = name
                best_model = model
        except Exception as e:
            logger.warning("  %s failed: %s", name, e)

    if best_model is None:
        best_model = LogisticRegression(max_iter=1000, random_state=42)
        best_name = "logistic_regression"

    # Final training on full dataset
    best_model.fit(X, y)
    y_pred = best_model.predict(X)

    # Get unique labels that actually appear in y
    unique_labels = sorted(set(y))
    target_names = [label_names[i] for i in unique_labels if i < len(label_names)]

    report = classification_report(
        y, y_pred, labels=unique_labels, target_names=target_names, output_dict=True, zero_division=0
    )

    metrics = {
        "accuracy": float(accuracy_score(y, y_pred)),
        "f1_macro": float(f1_score(y, y_pred, average="macro", zero_division=0)),
        "model_type": best_name,
        "samples": len(X),
        "cv_folds": cv_folds,
        "cv_f1_mean": best_score,
        "candidates_compared": len(all_results),
        "classification_report": report,
    }

    logger.info("Best %s model: %s (F1=%.3f)", task_name, best_name, best_score)
    return best_model, metrics


async def train_classifier():
    """Main training pipeline."""
    logger.info("=== Sentinel ML Training Pipeline ===")

    # Load data
    rows = await load_training_data()
    logger.info("Loaded %d labeled errors from database", len(rows))

    if len(rows) < 5:
        logger.warning("Insufficient training data (%d rows). Need at least 5. Skipping.", len(rows))
        return None

    # Prepare features
    X, y_cat, y_sev = prepare_dataset(rows)
    logger.info("Feature matrix: %s, Categories: %d unique, Severities: %d unique",
                X.shape, len(set(y_cat)), len(set(y_sev)))

    # Train category classifier
    cat_model, cat_metrics = train_and_evaluate(X, y_cat, CATEGORIES, "category")

    # Train severity classifier
    sev_model, sev_metrics = train_and_evaluate(X, y_sev, SEVERITIES, "severity")

    # Save models
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(cat_model, CATEGORY_MODEL_PATH)
    joblib.dump(sev_model, SEVERITY_MODEL_PATH)
    logger.info("Models saved to %s", MODEL_DIR)

    # Always save training report
    report_path = os.path.join(MODEL_DIR, "training_report.json")
    with open(report_path, "w") as f:
        json.dump({
            "category": cat_metrics,
            "severity": sev_metrics,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "samples": len(X),
        }, f, indent=2, default=str)
    logger.info("Training report saved to %s", report_path)

    # Log to MLflow if available (CML Experiments)
    try:
        import mlflow

        experiment_name = "Sentinel Error Classifier"
        mlflow.set_experiment(experiment_name)

        with mlflow.start_run(run_name=f"train-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}"):
            # Parameters
            mlflow.log_param("training_samples", len(X))
            mlflow.log_param("feature_count", X.shape[1])
            mlflow.log_param("category_model_type", cat_metrics["model_type"])
            mlflow.log_param("severity_model_type", sev_metrics["model_type"])
            mlflow.log_param("cv_folds", cat_metrics.get("cv_folds", 0))

            # Category metrics
            mlflow.log_metric("category_accuracy", cat_metrics["accuracy"])
            mlflow.log_metric("category_f1_macro", cat_metrics["f1_macro"])
            mlflow.log_metric("category_cv_f1", cat_metrics.get("cv_f1_mean", 0))

            # Severity metrics
            mlflow.log_metric("severity_accuracy", sev_metrics["accuracy"])
            mlflow.log_metric("severity_f1_macro", sev_metrics["f1_macro"])
            mlflow.log_metric("severity_cv_f1", sev_metrics.get("cv_f1_mean", 0))

            # Log model artifacts
            mlflow.log_artifact(CATEGORY_MODEL_PATH)
            mlflow.log_artifact(SEVERITY_MODEL_PATH)

            # Log training report as artifact
            mlflow.log_artifact(report_path)

        logger.info("Training metrics logged to MLflow experiment: %s", experiment_name)

    except ImportError:
        logger.info("MLflow not available — metrics printed only (install mlflow for CML Experiments)")
    except Exception as e:
        logger.warning("MLflow logging failed: %s", e)

    return {
        "category": cat_metrics,
        "severity": sev_metrics,
        "samples": len(X),
    }


if __name__ == "__main__":
    result = asyncio.run(train_classifier())
    if result:
        print(f"\nTraining complete:")
        print(f"  Category accuracy: {result['category']['accuracy']:.1%}")
        print(f"  Severity accuracy: {result['severity']['accuracy']:.1%}")
        print(f"  Samples used: {result['samples']}")
