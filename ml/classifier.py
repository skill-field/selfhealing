"""Real ML error classifier using scikit-learn.

Trained on historical error data from Sentinel's database.
Deployed as a CML Model for real-time classification.
"""

import json
import logging
import os
import re
from typing import Optional

import joblib
import numpy as np

logger = logging.getLogger("sentinel.ml")

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "models")
CATEGORY_MODEL_PATH = os.path.join(MODEL_DIR, "category_classifier.joblib")
SEVERITY_MODEL_PATH = os.path.join(MODEL_DIR, "severity_classifier.joblib")

# Categories and severities (label encoding order)
CATEGORIES = ["database", "auth", "api", "ui", "integration", "ai", "infrastructure", "unknown"]
SEVERITIES = ["critical", "high", "medium", "low"]

# Error patterns for feature extraction
ERROR_PATTERNS = {
    "null_reference": re.compile(r"cannot read prop|undefined|null|is not a function|typeerror", re.I),
    "connection_failure": re.compile(r"econnrefused|econnreset|timeout|connection.*refused", re.I),
    "validation_error": re.compile(r"validation|invalid|required|constraint|schema|zod", re.I),
    "resource_exhaustion": re.compile(r"memory|heap|stack overflow|too many|limit|quota|enomem", re.I),
    "concurrency_issue": re.compile(r"deadlock|race condition|lock|concurrent|conflict", re.I),
    "configuration_error": re.compile(r"env|config|missing.*var|not found|undefined variable", re.I),
    "auth_failure": re.compile(r"unauthorized|forbidden|token.*expired|jwt|session.*expired", re.I),
    "database_error": re.compile(r"prisma|sql|query|migration|unique constraint|foreign key", re.I),
    "network_error": re.compile(r"network|dns|ssl|certificate|http.*error|cors", re.I),
    "file_system_error": re.compile(r"enoent|enospc|permission denied|file.*not found", re.I),
}

# Category keyword features
CATEGORY_KEYWORDS = {
    "database": ["prisma", "database", "sql", "query", "migration", "schema", "connection pool",
                  "transaction", "deadlock", "constraint", "p2022", "p2025"],
    "auth": ["auth", "token", "session", "permission", "unauthorized", "forbidden", "jwt",
             "oauth", "credentials", "login", "nextauth"],
    "api": ["api", "endpoint", "request", "response", "http", "rest", "graphql", "timeout",
            "rate limit", "cors", "validation", "zod"],
    "ui": ["render", "component", "react", "dom", "css", "layout", "hydration", "client",
           "browser", "window"],
    "integration": ["webhook", "third-party", "external", "service", "integration", "smtp",
                    "redis", "queue", "sendgrid", "hubspot"],
    "ai": ["openai", "anthropic", "claude", "model", "inference", "embedding", "token limit",
           "ai", "llm", "ollama"],
    "infrastructure": ["memory", "cpu", "disk", "network", "container", "docker", "deploy",
                       "env", "config", "port", "sigkill", "enomem"],
}


def extract_features(error_message: str, error_type: str = "", stack_trace: str = "") -> np.ndarray:
    """Extract feature vector from error text.

    Features:
    - 10 error pattern matches (binary)
    - 7 category keyword counts (normalized)
    - 5 text statistics (message length, has stack trace, etc.)
    = 22 features total
    """
    combined = f"{error_message} {error_type} {stack_trace}".lower()

    features = []

    # Error pattern features (10)
    for pattern in ERROR_PATTERNS.values():
        features.append(1.0 if pattern.search(combined) else 0.0)

    # Category keyword count features (7)
    for cat_keywords in CATEGORY_KEYWORDS.values():
        count = sum(1 for kw in cat_keywords if kw in combined)
        features.append(min(count / max(len(cat_keywords), 1), 1.0))

    # Text statistics (5)
    features.append(min(len(error_message) / 500.0, 1.0))  # normalized message length
    features.append(1.0 if stack_trace else 0.0)  # has stack trace
    features.append(min(stack_trace.count("\n") / 20.0, 1.0) if stack_trace else 0.0)  # stack depth
    features.append(1.0 if error_type else 0.0)  # has error type
    features.append(min(len(combined.split()) / 100.0, 1.0))  # word count

    return np.array(features, dtype=np.float64)


class ErrorClassifier:
    """ML-based error classifier. Falls back to rule-based if no trained model exists."""

    def __init__(self):
        self.category_model = None
        self.severity_model = None
        self._load_models()

    def _load_models(self):
        """Load trained models from disk if available."""
        if os.path.exists(CATEGORY_MODEL_PATH):
            try:
                self.category_model = joblib.load(CATEGORY_MODEL_PATH)
                logger.info("Loaded category classifier from %s", CATEGORY_MODEL_PATH)
            except Exception as e:
                logger.warning("Failed to load category model: %s", e)

        if os.path.exists(SEVERITY_MODEL_PATH):
            try:
                self.severity_model = joblib.load(SEVERITY_MODEL_PATH)
                logger.info("Loaded severity classifier from %s", SEVERITY_MODEL_PATH)
            except Exception as e:
                logger.warning("Failed to load severity model: %s", e)

    @property
    def is_trained(self) -> bool:
        return self.category_model is not None

    def predict(self, error_message: str, error_type: str = "",
                stack_trace: str = "", occurrence_count: int = 1) -> dict:
        """Classify an error. Returns category, severity, confidence, and pattern."""
        features = extract_features(error_message, error_type, stack_trace)
        X = features.reshape(1, -1)

        # Category prediction
        if self.category_model is not None:
            cat_idx = self.category_model.predict(X)[0]
            category = CATEGORIES[cat_idx] if cat_idx < len(CATEGORIES) else "unknown"
            if hasattr(self.category_model, "predict_proba"):
                proba = self.category_model.predict_proba(X)[0]
                cat_confidence = float(max(proba))
            else:
                cat_confidence = 0.75
        else:
            category, cat_confidence = self._rule_based_category(error_message, error_type, stack_trace)

        # Severity prediction
        if self.severity_model is not None:
            sev_idx = self.severity_model.predict(X)[0]
            severity = SEVERITIES[sev_idx] if sev_idx < len(SEVERITIES) else "medium"
            if hasattr(self.severity_model, "predict_proba"):
                proba = self.severity_model.predict_proba(X)[0]
                sev_confidence = float(max(proba))
            else:
                sev_confidence = 0.70
        else:
            severity, sev_confidence = self._rule_based_severity(
                error_message, error_type, category, occurrence_count
            )

        # Detect error pattern
        pattern = self._detect_pattern(error_message, error_type, stack_trace)

        # Combined confidence
        confidence = round((cat_confidence + sev_confidence) / 2, 3)

        # Recommended action
        actions = {
            "null_reference": "Add null/undefined checks before property access",
            "connection_failure": "Implement retry logic with exponential backoff",
            "validation_error": "Add input validation at the boundary layer",
            "resource_exhaustion": "Review resource allocation and implement limits",
            "concurrency_issue": "Add proper locking or use optimistic concurrency",
            "configuration_error": "Verify environment variables and config files",
            "auth_failure": "Check token expiry, refresh logic, and session handling",
            "database_error": "Review query, check schema constraints and connections",
            "network_error": "Check network connectivity, DNS, and SSL certificates",
            "file_system_error": "Verify file paths, permissions, and disk space",
            "unknown": "Manual investigation recommended",
        }

        return {
            "category": category,
            "severity": severity,
            "pattern": pattern,
            "recommended_action": actions.get(pattern, actions["unknown"]),
            "confidence": confidence,
            "error_type": error_type or "Unknown",
            "model_type": "ml" if self.is_trained else "rule_based",
        }

    def _detect_pattern(self, error_message: str, error_type: str, stack_trace: str) -> str:
        """Detect the error pattern from text."""
        combined = f"{error_message} {error_type} {stack_trace}".lower()
        for pattern_name, regex in ERROR_PATTERNS.items():
            if regex.search(combined):
                return pattern_name
        return "unknown"

    def _rule_based_category(self, error_message: str, error_type: str,
                             stack_trace: str) -> tuple[str, float]:
        """Fallback rule-based category classification."""
        combined = f"{error_message} {error_type} {stack_trace}".lower()
        scores = {}
        for category, keywords in CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in combined)
            if score > 0:
                scores[category] = score
        if scores:
            best = max(scores, key=scores.get)
            total_keywords = len(CATEGORY_KEYWORDS[best])
            confidence = min(0.5 + (scores[best] / total_keywords) * 0.4, 0.90)
            return best, round(confidence, 3)
        return "unknown", 0.3

    def _rule_based_severity(self, error_message: str, error_type: str,
                             category: str, occurrence_count: int) -> tuple[str, float]:
        """Fallback rule-based severity classification."""
        combined = f"{error_type} {error_message}".upper()

        if any(kw in combined for kw in ["FATAL", "SIGKILL", "ENOMEM", "PANIC", "DATA LOSS", "CORRUPTION"]):
            return "critical", 0.90
        if category == "infrastructure":
            return "critical", 0.85
        if occurrence_count >= 100:
            return "critical", 0.80
        if occurrence_count >= 50:
            return "high", 0.75
        if any(kw in combined for kw in ["UNHANDLED", "UNCAUGHT", "CONNECTION REFUSED", "DEADLOCK"]):
            return "high", 0.80
        if category in ("database", "auth"):
            return "high", 0.70
        if any(kw in combined for kw in ["WARN", "WARNING", "DEPRECATED"]):
            return "low", 0.65
        return "medium", 0.50
