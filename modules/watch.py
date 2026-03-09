"""Watch module — log collection and ingestion."""
from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from uuid import uuid4

from database import execute, fetch_one, fetch_all

logger = logging.getLogger("sentinel.watch")


class WatchModule:
    """Handles log ingestion, error detection, and deduplication."""

    # Patterns to strip for fingerprint normalization
    _STRIP_PATTERNS = [
        # UUIDs
        (re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE), "<UUID>"),
        # Hex IDs (e.g., MongoDB ObjectIds, 24+ hex chars)
        (re.compile(r"\b[0-9a-f]{24,}\b", re.IGNORECASE), "<ID>"),
        # ISO timestamps
        (re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[.\dZ+:-]*"), "<TIMESTAMP>"),
        # Unix timestamps (10-13 digit numbers)
        (re.compile(r"\b\d{10,13}\b"), "<TS>"),
        # JWT-like tokens
        (re.compile(r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"), "<TOKEN>"),
        # IP addresses
        (re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"), "<IP>"),
        # Port numbers after colon
        (re.compile(r":\d{4,5}\b"), ":<PORT>"),
        # Generic numeric IDs in paths like /users/123
        (re.compile(r"/\d+(?=/|$)"), "/<NUM>"),
    ]

    # Stack trace patterns for Next.js/TypeScript
    _STACK_PATTERN = re.compile(
        r"at\s+(?:(?P<function>[^\s(]+)\s+)?\(?(?P<file>[^\s:)]+):(?P<line>\d+):(?P<col>\d+)\)?"
    )

    async def ingest_log(self, entry: dict) -> dict:
        """Process a single log entry, detect if it's an error, create error record if needed.

        Args:
            entry: Dict with keys matching LogEntry schema (source, environment,
                   raw_log, error_message, error_type, stack_trace, severity, timestamp).

        Returns:
            Dict with 'error' key (the error record dict or None) and 'is_new' bool.
        """
        now = datetime.now(timezone.utc).isoformat()
        source = entry.get("source", "unknown")
        environment = entry.get("environment", "production")
        raw_log = entry.get("raw_log", "")
        error_message = entry.get("error_message") or ""
        error_type = entry.get("error_type") or ""
        stack_trace = entry.get("stack_trace") or ""
        severity = entry.get("severity")

        # Determine if this is an error worth tracking
        is_error = self._is_error(raw_log, error_message, error_type, severity)
        if not is_error:
            return {"error": None, "is_new": False}

        # Parse stack trace for affected file info
        stack_info = self.parse_stack_trace(stack_trace) if stack_trace else {}
        affected_file = stack_info.get("file")

        # Compute fingerprint for deduplication
        fingerprint = self.compute_fingerprint(error_type, error_message or raw_log, affected_file)

        # Check if this fingerprint already exists
        existing = await fetch_one(
            "SELECT id, occurrence_count FROM errors WHERE fingerprint = ?",
            (fingerprint,),
        )

        if existing:
            # Increment occurrence count and update last_seen
            await execute(
                "UPDATE errors SET occurrence_count = occurrence_count + 1, last_seen = ?, updated_at = ? WHERE id = ?",
                (now, now, existing["id"]),
            )
            updated = await fetch_one("SELECT * FROM errors WHERE id = ?", (existing["id"],))
            return {"error": updated, "is_new": False}

        # New error — classify severity if not provided
        if not severity:
            severity = self._infer_severity(error_message or raw_log, error_type)

        # Create new error record
        error_id = uuid4().hex
        await execute(
            """INSERT INTO errors
               (id, source, environment, raw_log, error_message, error_type, stack_trace,
                severity, category, affected_file, fingerprint, occurrence_count,
                first_seen, last_seen, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, 'new', ?, ?)""",
            (
                error_id, source, environment, raw_log,
                error_message or None, error_type or None, stack_trace or None,
                severity, "unknown", affected_file,
                fingerprint, now, now, now, now,
            ),
        )

        # Create audit log entry
        audit_id = uuid4().hex
        await execute(
            "INSERT INTO audit_log (id, action, entity_type, entity_id, details, actor, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                audit_id, "error_detected", "error", error_id,
                json.dumps({"source": source, "environment": environment, "fingerprint": fingerprint}),
                "watch_module", now,
            ),
        )

        error_record = await fetch_one("SELECT * FROM errors WHERE id = ?", (error_id,))
        return {"error": error_record, "is_new": True}

    async def ingest_batch(self, entries: list[dict]) -> dict:
        """Process multiple log entries.

        Returns:
            Dict with 'processed', 'errors_detected', 'new_errors', and 'results' keys.
        """
        results = []
        errors_detected = 0
        new_errors = 0

        for entry in entries:
            result = await self.ingest_log(entry)
            results.append(result)
            if result["error"] is not None:
                errors_detected += 1
                if result["is_new"]:
                    new_errors += 1

        return {
            "processed": len(entries),
            "errors_detected": errors_detected,
            "new_errors": new_errors,
            "results": results,
        }

    def compute_fingerprint(self, error_type: str, message: str, affected_file: str | None) -> str:
        """Create dedup hash. Normalize by stripping IDs, timestamps, tokens."""
        normalized = message
        for pattern, replacement in self._STRIP_PATTERNS:
            normalized = pattern.sub(replacement, normalized)

        # Collapse whitespace
        normalized = re.sub(r"\s+", " ", normalized).strip().lower()

        parts = [
            (error_type or "").lower().strip(),
            normalized,
            (affected_file or "").lower().strip(),
        ]
        combined = "|".join(parts)
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()[:32]

    def parse_stack_trace(self, stack_trace: str) -> dict:
        """Extract affected_file, line number, function name from stack trace.

        Handles Next.js/TypeScript stack traces like:
        "at MetricService.calculateFormula (src/lib/services/metric/metric.service.ts:245:12)"

        Returns:
            {"file": str, "line": int, "function": str} or {} if no match.
        """
        if not stack_trace:
            return {}

        # Find the first meaningful frame (skip node_modules, internal frames)
        for line in stack_trace.splitlines():
            match = self._STACK_PATTERN.search(line)
            if match:
                file_path = match.group("file")
                # Skip internal/vendor frames
                if "node_modules" in file_path or file_path.startswith("node:"):
                    continue
                result = {
                    "file": file_path,
                    "line": int(match.group("line")),
                }
                func = match.group("function")
                if func:
                    result["function"] = func
                return result

        # If all frames were vendor, return the first match anyway
        for line in stack_trace.splitlines():
            match = self._STACK_PATTERN.search(line)
            if match:
                result = {
                    "file": match.group("file"),
                    "line": int(match.group("line")),
                }
                func = match.group("function")
                if func:
                    result["function"] = func
                return result

        return {}

    def _is_error(self, raw_log: str, error_message: str, error_type: str, severity: str | None) -> bool:
        """Determine whether a log entry represents an error worth tracking."""
        if severity and severity.lower() in ("critical", "high", "medium"):
            return True
        if error_type:
            return True
        if error_message:
            return True

        # Check raw log for error indicators
        raw_upper = raw_log.upper()
        error_keywords = ["ERROR", "FATAL", "CRITICAL", "EXCEPTION", "UNHANDLED", "PANIC", "SIGKILL", "ENOMEM"]
        for kw in error_keywords:
            if kw in raw_upper:
                return True

        # Also detect WARN level
        if "WARN" in raw_upper:
            return True

        return False

    def _infer_severity(self, message: str, error_type: str) -> str:
        """Infer severity from error signals when not explicitly provided."""
        combined = f"{error_type} {message}".upper()

        if any(kw in combined for kw in ["FATAL", "SIGKILL", "ENOMEM", "PANIC", "HEAP", "OUT OF MEMORY"]):
            return "critical"
        if any(kw in combined for kw in ["UNHANDLED", "UNCAUGHT", "CONNECTION REFUSED", "DEADLOCK"]):
            return "high"
        if any(kw in combined for kw in ["WARN", "WARNING", "DEPRECATED"]):
            return "low"
        return "medium"
