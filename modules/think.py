"""Think module — error analysis and classification."""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from uuid import uuid4

from database import execute, fetch_one
from llm.client import AnthropicClient
from llm.prompts import ROOT_CAUSE_SYSTEM_PROMPT, ROOT_CAUSE_USER_TEMPLATE
from ml.classifier import ErrorClassifier

logger = logging.getLogger("sentinel.think")


class ThinkModule:
    """Handles error classification and root cause analysis."""

    def __init__(self, anthropic_client: AnthropicClient | None = None):
        self.anthropic_client = anthropic_client or AnthropicClient()
        self.ml_classifier = ErrorClassifier()
        self.rules = self._load_classification_rules()
        if self.ml_classifier.is_trained:
            logger.info("ML classifier loaded — using trained models for classification")
        else:
            logger.info("No trained ML model found — using rule-based classification")

    def _load_classification_rules(self) -> list[dict]:
        """Return rule-based classification patterns for the Metrics app.

        Each rule has: category, patterns (compiled regex list), severity_hint.
        """
        return [
            {
                "category": "database",
                "patterns": [
                    re.compile(r"PrismaClient\w*Error", re.IGNORECASE),
                    re.compile(r"connection\s*.*refused", re.IGNORECASE),
                    re.compile(r"\bP20\d{2}\b"),
                    re.compile(r"\bP2022\b"),
                    re.compile(r"\bP2025\b"),
                    re.compile(r"deadlock", re.IGNORECASE),
                    re.compile(r"connection\s*pool", re.IGNORECASE),
                    re.compile(r"prisma", re.IGNORECASE),
                    re.compile(r"database.*error", re.IGNORECASE),
                    re.compile(r"unique\s*constraint", re.IGNORECASE),
                ],
                "severity_hint": "high",
            },
            {
                "category": "auth",
                "patterns": [
                    re.compile(r"UNAUTHORIZED", re.IGNORECASE),
                    re.compile(r"FORBIDDEN", re.IGNORECASE),
                    re.compile(r"session\s*.*expired", re.IGNORECASE),
                    re.compile(r"NEXTAUTH", re.IGNORECASE),
                    re.compile(r"JWT\s*.*invalid", re.IGNORECASE),
                    re.compile(r"token\s*.*expired", re.IGNORECASE),
                    re.compile(r"auth.*error", re.IGNORECASE),
                    re.compile(r"unauthenticated", re.IGNORECASE),
                ],
                "severity_hint": "high",
            },
            {
                "category": "api",
                "patterns": [
                    re.compile(r"ServiceError", re.IGNORECASE),
                    re.compile(r"ValidationError", re.IGNORECASE),
                    re.compile(r"ZodError", re.IGNORECASE),
                    re.compile(r"VALIDATION_ERROR", re.IGNORECASE),
                    re.compile(r"RATE_LIMITED", re.IGNORECASE),
                    re.compile(r"rate\s*limit", re.IGNORECASE),
                    re.compile(r"bad\s*request", re.IGNORECASE),
                    re.compile(r"404\s*not\s*found", re.IGNORECASE),
                ],
                "severity_hint": "medium",
            },
            {
                "category": "integration",
                "patterns": [
                    re.compile(r"Google\s*Sheets", re.IGNORECASE),
                    re.compile(r"HubSpot", re.IGNORECASE),
                    re.compile(r"SendGrid", re.IGNORECASE),
                    re.compile(r"OAuth\s*.*error", re.IGNORECASE),
                    re.compile(r"webhook\s*.*failed", re.IGNORECASE),
                    re.compile(r"integration.*error", re.IGNORECASE),
                    re.compile(r"third.party", re.IGNORECASE),
                ],
                "severity_hint": "medium",
            },
            {
                "category": "ai",
                "patterns": [
                    re.compile(r"OpenAI", re.IGNORECASE),
                    re.compile(r"Anthropic", re.IGNORECASE),
                    re.compile(r"CircuitBreakerError", re.IGNORECASE),
                    re.compile(r"rate_limit", re.IGNORECASE),
                    re.compile(r"token\s*.*budget", re.IGNORECASE),
                    re.compile(r"model.*overloaded", re.IGNORECASE),
                    re.compile(r"ollama", re.IGNORECASE),
                ],
                "severity_hint": "medium",
            },
            {
                "category": "infrastructure",
                "patterns": [
                    re.compile(r"ENOMEM", re.IGNORECASE),
                    re.compile(r"SIGKILL", re.IGNORECASE),
                    re.compile(r"health\s*.*check\s*.*fail", re.IGNORECASE),
                    re.compile(r"\b503\b"),
                    re.compile(r"heap\s*.*out\s*.*memory", re.IGNORECASE),
                    re.compile(r"out\s*of\s*memory", re.IGNORECASE),
                    re.compile(r"container.*restart", re.IGNORECASE),
                    re.compile(r"ENOSPC", re.IGNORECASE),
                    re.compile(r"disk.*full", re.IGNORECASE),
                ],
                "severity_hint": "critical",
            },
        ]

    def classify(
        self, error_message: str, error_type: str | None = None, stack_trace: str | None = None
    ) -> dict:
        """Classify an error using ML model (preferred) or rule-based fallback.

        Returns:
            {"category": str, "severity": str, "confidence": float, "model_type": str}
        """
        # Try ML classifier first
        ml_result = self.ml_classifier.predict(
            error_message=error_message or "",
            error_type=error_type or "",
            stack_trace=stack_trace or "",
        )
        logger.debug(
            "Classification result (%s): category=%s severity=%s confidence=%.2f",
            ml_result.get("model_type", "unknown"),
            ml_result["category"],
            ml_result["severity"],
            ml_result["confidence"],
        )
        return {
            "category": ml_result["category"],
            "severity": ml_result["severity"],
            "confidence": ml_result["confidence"],
            "model_type": ml_result.get("model_type", "rule_based"),
        }

    def determine_severity(self, error_message: str, category: str, occurrence_count: int) -> str:
        """Compute severity: critical/high/medium/low based on signals."""
        msg_upper = error_message.upper()

        # Critical signals
        if any(kw in msg_upper for kw in [
            "FATAL", "SIGKILL", "ENOMEM", "PANIC", "OUT OF MEMORY", "HEAP",
            "DATA LOSS", "CORRUPTION",
        ]):
            return "critical"

        # Infrastructure issues are usually critical
        if category == "infrastructure":
            return "critical"

        # High occurrence count escalates severity
        if occurrence_count >= 100:
            return "critical"
        if occurrence_count >= 50:
            return "high"

        # High signals
        if any(kw in msg_upper for kw in [
            "UNHANDLED", "UNCAUGHT", "CONNECTION REFUSED", "DEADLOCK",
            "UNAUTHORIZED", "FORBIDDEN",
        ]):
            return "high"

        # Database and auth errors default to high
        if category in ("database", "auth"):
            return "high"

        # Low signals
        if any(kw in msg_upper for kw in ["WARN", "WARNING", "DEPRECATED", "NOTICE"]):
            return "low"

        return "medium"

    async def analyze_root_cause(self, error_id: str) -> dict:
        """Use Claude Sonnet to analyze root cause.

        Fetches error from DB, calls LLM, updates error record.

        Returns:
            Analysis result dict with root_cause, affected_component, impact, fix_strategy, confidence.
        """
        now = datetime.now(timezone.utc).isoformat()

        # Fetch error from database
        error = await fetch_one("SELECT * FROM errors WHERE id = ?", (error_id,))
        if not error:
            return {"error": "not_found", "message": f"Error {error_id} not found"}

        # First do rule-based classification
        classification = self.classify(
            error.get("error_message") or "",
            error.get("error_type"),
            error.get("stack_trace"),
        )
        category = classification["category"]
        severity = self.determine_severity(
            error.get("error_message") or "",
            category,
            error.get("occurrence_count", 1),
        )

        # Build prompt
        user_prompt = ROOT_CAUSE_USER_TEMPLATE.format(
            error_type=error.get("error_type") or "Unknown",
            error_message=error.get("error_message") or error.get("raw_log", "No message"),
            severity=severity,
            category=category,
            occurrence_count=error.get("occurrence_count", 1),
            first_seen=error.get("first_seen") or "unknown",
            stack_trace=error.get("stack_trace") or "No stack trace available",
        )

        # Call Claude
        llm_result = await self.anthropic_client.generate_json(
            system_prompt=ROOT_CAUSE_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        analysis = llm_result["data"]
        root_cause = analysis.get("root_cause", "Analysis unavailable")

        # Update error record
        await execute(
            """UPDATE errors
               SET root_cause = ?, category = ?, severity = ?,
                   updated_at = ?
               WHERE id = ?""",
            (root_cause, category, severity, now, error_id),
        )

        # Create audit log entry
        audit_id = uuid4().hex
        await execute(
            "INSERT INTO audit_log (id, action, entity_type, entity_id, details, actor, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                audit_id, "error_classified", "error", error_id,
                json.dumps({
                    "category": category,
                    "severity": severity,
                    "confidence": classification["confidence"],
                    "model": llm_result.get("model", "unknown"),
                    "prompt_tokens": llm_result.get("prompt_tokens", 0),
                    "completion_tokens": llm_result.get("completion_tokens", 0),
                }),
                "think_module", now,
            ),
        )

        return {
            "error_id": error_id,
            "category": category,
            "severity": severity,
            "classification_confidence": classification["confidence"],
            "root_cause": root_cause,
            "affected_component": analysis.get("affected_component", "unknown"),
            "impact": analysis.get("impact", "unknown"),
            "fix_strategy": analysis.get("fix_strategy", "unknown"),
            "analysis_confidence": analysis.get("confidence", 0.0),
            "model": llm_result.get("model", "unknown"),
            "prompt_tokens": llm_result.get("prompt_tokens", 0),
            "completion_tokens": llm_result.get("completion_tokens", 0),
        }
