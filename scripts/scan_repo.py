#!/usr/bin/env python3
"""CML Job — Scan the real Metrics AI repo for issues and feed them into Sentinel.

Uses Claude via AWS Bedrock (Cloudera AI) to analyze the actual codebase,
detect potential bugs, security issues, and code quality problems,
then ingests them as real errors in Sentinel's Watch module.

This is the real Cloudera AI integration:
  CML Job -> GitHub API (fetch code) -> Claude via Bedrock (analyze) -> Sentinel DB
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import hashlib
from datetime import datetime, timezone
from uuid import uuid4

# Ensure project root is importable
try:
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    PROJECT_ROOT = os.getcwd()
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

from config import settings
from database import init_db, execute, fetch_one, fetch_all
from llm.client import AnthropicClient
from modules.github_client import GitHubClient

# ─── Configuration ────────────────────────────────────────────────────────────

# Key files to scan in the Metrics AI repo
SCAN_TARGETS = [
    # Core services
    "src/lib/services/metric/metric.service.ts",
    "src/lib/services/metric/metric-value.service.ts",
    "src/lib/services/scorecard/scorecard.service.ts",
    "src/lib/services/tenant/tenant.service.ts",
    "src/lib/services/user/user.service.ts",
    # Auth
    "src/lib/auth/auth.config.ts",
    "src/lib/auth/session.ts",
    # API routes
    "src/app/api/v1/metrics/route.ts",
    "src/app/api/v1/scorecards/route.ts",
    "src/app/api/v1/health/route.ts",
    # Database
    "prisma/schema.prisma",
    # Config
    "src/lib/config/index.ts",
    "next.config.ts",
    # Queue / background
    "src/lib/queue/worker.ts",
    "src/lib/queue/jobs.ts",
]

SCAN_PROMPT = """You are a senior software engineer performing a thorough code review of a production Next.js 16 + TypeScript + Prisma application called "Metrics AI".

Analyze the following source file for REAL issues — bugs, security vulnerabilities, performance problems, error handling gaps, and potential runtime errors.

**File:** {file_path}
**Content:**
```typescript
{content}
```

Find 1-3 REAL issues (not style/formatting). For each issue, provide:
- A realistic error message that would appear in production logs
- The error type (e.g., TypeError, PrismaClientKnownRequestError, etc.)
- Severity: critical, high, medium, or low
- A stack trace snippet pointing to the exact line
- Category: database, auth, api, ui, integration, ai, infrastructure

If the code is solid and has no real issues, return an empty array.

Respond ONLY with valid JSON:
{{
  "issues": [
    {{
      "error_message": "realistic production error message",
      "error_type": "ErrorClassName",
      "severity": "high",
      "category": "database",
      "stack_trace": "Error: message\\n    at FunctionName ({file_path}:LINE:COL)",
      "affected_file": "{file_path}",
      "raw_log": "[timestamp] ERROR [ModuleName] detailed log line",
      "explanation": "Why this is a real problem (1-2 sentences)"
    }}
  ]
}}"""


async def scan_repo():
    """Main scan function — fetch code, analyze with Claude, ingest errors."""
    print(f"[Sentinel Scanner] Starting repo scan of {settings.GITHUB_REPO}", flush=True)
    print(f"[Sentinel Scanner] Using Bedrock: {settings.USE_BEDROCK}, Region: {settings.AWS_REGION}", flush=True)

    await init_db()

    github = GitHubClient()
    llm = AnthropicClient()

    if not llm.has_key:
        print("[Sentinel Scanner] WARNING: No AI credentials configured. Cannot scan.", flush=True)
        return

    if not github.token:
        print("[Sentinel Scanner] WARNING: No GitHub token. Cannot fetch code.", flush=True)
        return

    total_issues = 0
    new_issues = 0
    files_scanned = 0

    for file_path in SCAN_TARGETS:
        print(f"[Sentinel Scanner] Scanning {file_path}...", flush=True)

        # Fetch file from GitHub
        content = await github.get_file_content(file_path)
        if content is None:
            print(f"  -> File not found, skipping", flush=True)
            continue

        files_scanned += 1

        # Truncate very large files
        lines = content.split("\n")
        if len(lines) > 500:
            content = "\n".join(lines[:500]) + f"\n\n... (truncated, {len(lines)} total lines)"

        # Analyze with Claude via Bedrock
        try:
            result = await llm.generate_json(
                system_prompt="You are a code analysis expert. Respond only with valid JSON.",
                user_prompt=SCAN_PROMPT.format(file_path=file_path, content=content),
                model="claude-sonnet-4-20250514",
            )
        except Exception as e:
            print(f"  -> LLM error: {e}", flush=True)
            continue

        issues = result["data"].get("issues", [])
        if not issues:
            print(f"  -> No issues found", flush=True)
            continue

        print(f"  -> Found {len(issues)} issues (model: {result.get('model', '?')}, tokens: {result.get('prompt_tokens', 0)}+{result.get('completion_tokens', 0)})", flush=True)

        # Ingest each issue into the database
        now = datetime.now(timezone.utc).isoformat()
        for issue in issues:
            total_issues += 1
            error_message = issue.get("error_message", "")
            error_type = issue.get("error_type", "")

            # Compute fingerprint for deduplication
            fp_input = f"{error_type}|{error_message}|{file_path}".lower()
            fingerprint = hashlib.sha256(fp_input.encode()).hexdigest()[:32]

            # Check if already exists
            existing = await fetch_one(
                "SELECT id, occurrence_count FROM errors WHERE fingerprint = ?",
                (fingerprint,),
            )
            if existing:
                await execute(
                    "UPDATE errors SET occurrence_count = occurrence_count + 1, last_seen = ?, updated_at = ? WHERE id = ?",
                    (now, now, existing["id"]),
                )
                print(f"    -> Duplicate (updated count): {error_message[:60]}", flush=True)
                continue

            # New error — insert
            new_issues += 1
            error_id = uuid4().hex
            await execute(
                """INSERT INTO errors
                   (id, source, environment, raw_log, error_message, error_type,
                    stack_trace, severity, category, affected_file, fingerprint,
                    occurrence_count, first_seen, last_seen, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, 'new', ?, ?)""",
                (
                    error_id, settings.GITHUB_REPO, "production",
                    issue.get("raw_log", f"[Scanner] {error_message}"),
                    error_message, error_type,
                    issue.get("stack_trace"), issue.get("severity", "medium"),
                    issue.get("category", "unknown"), file_path,
                    fingerprint, now, now, now, now,
                ),
            )

            # Audit log
            await execute(
                "INSERT INTO audit_log (id, action, entity_type, entity_id, details, actor, created_at) VALUES (?,?,?,?,?,?,?)",
                (
                    uuid4().hex, "error_detected", "error", error_id,
                    json.dumps({
                        "source": "cml_scanner",
                        "file": file_path,
                        "model": result.get("model", "unknown"),
                        "tokens": result.get("prompt_tokens", 0) + result.get("completion_tokens", 0),
                    }),
                    "cml_scanner_job", now,
                ),
            )
            print(f"    -> NEW: [{issue.get('severity', '?')}] {error_message[:60]}", flush=True)

    print(f"\n[Sentinel Scanner] Done.", flush=True)
    print(f"  Files scanned: {files_scanned}", flush=True)
    print(f"  Total issues: {total_issues}", flush=True)
    print(f"  New issues: {new_issues}", flush=True)
    print(f"  Duplicates: {total_issues - new_issues}", flush=True)


if __name__ == "__main__":
    asyncio.run(scan_repo())
