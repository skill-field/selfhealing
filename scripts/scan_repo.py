#!/usr/bin/env python3
"""CML Job — Scan monitored repos for issues using Claude via AWS Bedrock.

Uses Cloudera AI (CML) to orchestrate:
  CML Job -> GitHub API (fetch code) -> Claude via Bedrock (analyze) -> Sentinel DB

Iterates all active repos from the monitored_repos table.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import hashlib
from datetime import datetime, timezone
from uuid import uuid4

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

# Default scan targets for repos with no configured paths
DEFAULT_SCAN_PATHS = [
    "src/lib/services/metric/metric.service.ts",
    "src/lib/services/metric/metric-value.service.ts",
    "src/lib/services/scorecard/scorecard.service.ts",
    "src/lib/services/tenant/tenant.service.ts",
    "src/lib/auth/auth.config.ts",
    "prisma/schema.prisma",
    "src/app/api/v1/metrics/route.ts",
    "src/app/api/v1/scorecards/route.ts",
    "next.config.ts",
]

SCAN_PROMPT = """You are a senior software engineer performing a thorough code review of a production application.

Analyze the following source file for REAL issues — bugs, security vulnerabilities, performance problems, error handling gaps, and potential runtime errors.

**Repository:** {repo_slug}
**File:** {file_path}
**Content:**
```
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


async def scan_single_repo(repo_row: dict, llm: AnthropicClient) -> dict:
    """Scan a single repo. Returns stats dict."""
    repo_id = repo_row["id"]
    repo_slug = repo_row["repo_slug"]
    import crypto
    repo_token = crypto.decrypt(repo_row.get("github_token") or "") or settings.GITHUB_TOKEN

    scan_paths_raw = repo_row.get("scan_paths", "[]")
    try:
        scan_paths = json.loads(scan_paths_raw) if isinstance(scan_paths_raw, str) else scan_paths_raw
    except Exception:
        scan_paths = []

    if not scan_paths:
        scan_paths = DEFAULT_SCAN_PATHS

    github = GitHubClient(repo=repo_slug, token=repo_token)
    stats = {"files_scanned": 0, "total_issues": 0, "new_issues": 0}

    for file_path in scan_paths:
        print(f"  [{repo_slug}] Scanning {file_path}...", flush=True)

        content = await github.get_file_content(file_path)
        if content is None:
            print(f"    -> Not found, skipping", flush=True)
            continue

        stats["files_scanned"] += 1

        lines = content.split("\n")
        if len(lines) > 500:
            content = "\n".join(lines[:500]) + f"\n\n... (truncated, {len(lines)} total lines)"

        try:
            result = await llm.generate_json(
                system_prompt="You are a code analysis expert. Respond only with valid JSON.",
                user_prompt=SCAN_PROMPT.format(
                    repo_slug=repo_slug, file_path=file_path, content=content
                ),
                model="claude-sonnet-4-5",
            )
        except Exception as e:
            print(f"    -> LLM error: {e}", flush=True)
            continue

        issues = result["data"].get("issues", [])
        if not issues:
            print(f"    -> Clean", flush=True)
            continue

        print(f"    -> {len(issues)} issues found", flush=True)

        now = datetime.now(timezone.utc).isoformat()
        for issue in issues:
            stats["total_issues"] += 1
            error_message = issue.get("error_message", "")
            error_type = issue.get("error_type", "")

            fp_input = f"{error_type}|{error_message}|{file_path}|{repo_slug}".lower()
            fingerprint = hashlib.sha256(fp_input.encode()).hexdigest()[:32]

            existing = await fetch_one(
                "SELECT id FROM errors WHERE fingerprint = ? AND repo_id = ?",
                (fingerprint, repo_id),
            )
            if existing:
                await execute(
                    "UPDATE errors SET occurrence_count = occurrence_count + 1, last_seen = ?, updated_at = ? WHERE id = ?",
                    (now, now, existing["id"]),
                )
                continue

            stats["new_issues"] += 1
            error_id = uuid4().hex
            await execute(
                """INSERT INTO errors
                   (id, source, environment, raw_log, error_message, error_type,
                    stack_trace, severity, category, affected_file, fingerprint,
                    occurrence_count, first_seen, last_seen, status, repo_id, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, 'new', ?, ?, ?)""",
                (
                    error_id, repo_slug, "production",
                    issue.get("raw_log", f"[Scanner] {error_message}"),
                    error_message, error_type,
                    issue.get("stack_trace"), issue.get("severity", "medium"),
                    issue.get("category", "unknown"), file_path,
                    fingerprint, now, now, repo_id, now, now,
                ),
            )

            await execute(
                "INSERT INTO audit_log (id, action, entity_type, entity_id, details, actor, created_at) VALUES (?,?,?,?,?,?,?)",
                (uuid4().hex, "error_detected", "error", error_id,
                 json.dumps({"source": "cml_scanner", "repo": repo_slug, "file": file_path}),
                 "cml_scanner_job", now),
            )

    return stats


async def scan_all_repos():
    """Main entry — scan all active monitored repos."""
    print("[Sentinel Scanner] Starting multi-repo scan", flush=True)
    print(f"[Sentinel Scanner] Bedrock: {settings.USE_BEDROCK}, Region: {settings.AWS_REGION}", flush=True)

    await init_db()

    llm = AnthropicClient()
    if not llm.has_key:
        print("[Sentinel Scanner] ERROR: No AI credentials. Cannot scan.", flush=True)
        return

    repos = await fetch_all("SELECT * FROM monitored_repos WHERE is_active = 1")
    if not repos:
        print("[Sentinel Scanner] No active repos configured.", flush=True)
        return

    print(f"[Sentinel Scanner] Found {len(repos)} active repo(s)", flush=True)

    for repo in repos:
        print(f"\n[Sentinel Scanner] === {repo['display_name']} ({repo['repo_slug']}) ===", flush=True)
        stats = await scan_single_repo(repo, llm)
        print(f"  Files: {stats['files_scanned']}, Issues: {stats['total_issues']}, New: {stats['new_issues']}", flush=True)

    print("\n[Sentinel Scanner] All repos scanned.", flush=True)


if __name__ == "__main__":
    asyncio.run(scan_all_repos())
