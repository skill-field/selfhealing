#!/usr/bin/env python3
"""CML Job — Auto-Heal Pipeline.

Picks up all 'new' errors, runs Think (classification + root cause analysis)
then Heal (fix generation) for high/critical errors. Fully automated.

Uses Cloudera AI (Claude via AWS Bedrock) for analysis and fix generation.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from uuid import uuid4

try:
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    PROJECT_ROOT = os.getcwd()
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

import crypto
from config import settings
from database import init_db, execute, fetch_one, fetch_all
from llm.client import AnthropicClient
from llm.context_builder import ContextBuilder
from llm.prompts import (
    ROOT_CAUSE_SYSTEM_PROMPT,
    ROOT_CAUSE_USER_TEMPLATE,
    FIX_GENERATION_SYSTEM_PROMPT,
    FIX_GENERATION_USER_TEMPLATE,
)
from modules.github_client import GitHubClient


async def auto_heal():
    """Main entry — analyze and heal all new errors."""
    print("[Auto-Heal] Starting automated heal pipeline", flush=True)
    print(f"[Auto-Heal] Bedrock: {settings.USE_BEDROCK}, Region: {settings.AWS_REGION}", flush=True)

    await init_db()

    llm = AnthropicClient()
    if not llm.has_key:
        print("[Auto-Heal] ERROR: No AI credentials. Cannot heal.", flush=True)
        return

    # Get all new errors
    errors = await fetch_all(
        "SELECT e.*, mr.repo_slug, mr.github_token FROM errors e "
        "LEFT JOIN monitored_repos mr ON e.repo_id = mr.id "
        "WHERE e.status = 'new' ORDER BY "
        "CASE e.severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END"
    )

    if not errors:
        print("[Auto-Heal] No new errors to process.", flush=True)
        return

    print(f"[Auto-Heal] Found {len(errors)} new error(s) to process", flush=True)

    stats = {"analyzed": 0, "fixes_generated": 0, "skipped": 0}

    for error in errors:
        error_id = error["id"]
        severity = error.get("severity", "medium")
        repo_slug = error.get("repo_slug") or settings.GITHUB_REPO
        repo_token = crypto.decrypt(error.get("github_token") or "") or settings.GITHUB_TOKEN

        print(f"\n[Auto-Heal] Processing: {error.get('error_message', '')[:80]}...", flush=True)
        print(f"  Severity: {severity}, File: {error.get('affected_file', 'unknown')}", flush=True)

        now = datetime.now(timezone.utc).isoformat()

        # Step 1: Think — classify and analyze root cause
        try:
            category = error.get("category", "unknown")
            affected_file = error.get("affected_file", "")

            # Build context from source code
            github = GitHubClient(repo=repo_slug, token=repo_token)
            context_builder = ContextBuilder(github)
            code_ctx = await context_builder.build_fix_context(error)

            # Format code context for prompt
            if code_ctx["files"]:
                context_str = ""
                for f in code_ctx["files"]:
                    context_str += f"\n--- {f['path']} ({f['relevant_lines']}) ---\n"
                    context_str += f["content"]
                    context_str += "\n"
            else:
                context_str = "(No source code context available)"

            # Run root cause analysis via Claude
            rca_prompt = ROOT_CAUSE_USER_TEMPLATE.format(
                error_message=error.get("error_message", ""),
                error_type=error.get("error_type", ""),
                stack_trace=error.get("stack_trace", ""),
                category=category,
                severity=severity,
                occurrence_count=error.get("occurrence_count", 1),
                first_seen=error.get("first_seen", "unknown"),
            )

            rca_result = await llm.generate_json(
                system_prompt=ROOT_CAUSE_SYSTEM_PROMPT,
                user_prompt=rca_prompt,
                model="claude-sonnet-4-5",
            )

            rca_data = rca_result.get("data", {})
            root_cause = rca_data.get("root_cause", "Automated analysis pending")
            confidence = rca_data.get("confidence", 0.7)

            # Update error status to 'analyzed'
            await execute(
                "UPDATE errors SET status = 'analyzed', updated_at = ? WHERE id = ?",
                (now, error_id),
            )
            stats["analyzed"] += 1
            print(f"  Root cause: {root_cause[:100]}...", flush=True)

        except Exception as e:
            print(f"  Think failed: {e}", flush=True)
            stats["skipped"] += 1
            continue

        # Step 2: Heal — generate fix for high/critical errors
        if severity not in ("critical", "high"):
            print(f"  Skipping fix generation (severity: {severity})", flush=True)
            continue

        try:
            fix_prompt = FIX_GENERATION_USER_TEMPLATE.format(
                error_message=error.get("error_message", ""),
                error_type=error.get("error_type", ""),
                stack_trace=error.get("stack_trace", ""),
                root_cause=root_cause,
                category=category,
                severity=severity,
                occurrence_count=error.get("occurrence_count", 1),
                code_context=context_str,
            )

            fix_result = await llm.generate_json(
                system_prompt=FIX_GENERATION_SYSTEM_PROMPT,
                user_prompt=fix_prompt,
                model="claude-sonnet-4-5",
            )

            fix_data = fix_result.get("data", {})
            fix_id = uuid4().hex

            # Extract fields matching heal.py schema
            files_changed = fix_data.get("files_changed", [])
            diff_parts = []
            file_paths = []
            for fc in files_changed:
                file_paths.append(fc.get("path", "unknown"))
                diff_parts.append(fc.get("diff", ""))
            combined_diff = "\n".join(diff_parts)

            explanation = fix_data.get("explanation", root_cause)
            fix_confidence = fix_data.get("confidence", confidence)

            await execute(
                """INSERT INTO fixes
                   (id, error_id, diff, explanation, files_changed, confidence,
                    model_used, prompt_tokens, completion_tokens, status,
                    attempt_number, guidance, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', 1, ?, ?, ?)""",
                (
                    fix_id, error_id,
                    combined_diff,
                    explanation,
                    json.dumps(file_paths),
                    fix_confidence,
                    fix_result.get("model", "unknown"),
                    fix_result.get("prompt_tokens", 0),
                    fix_result.get("completion_tokens", 0),
                    None,
                    now, now,
                ),
            )

            # Update error status
            await execute(
                "UPDATE errors SET status = 'fix_available', updated_at = ? WHERE id = ?",
                (now, error_id),
            )

            # Audit log
            await execute(
                "INSERT INTO audit_log (id, action, entity_type, entity_id, details, actor, created_at) VALUES (?,?,?,?,?,?,?)",
                (uuid4().hex, "fix_generated", "fix", fix_id,
                 json.dumps({"error_id": error_id, "source": "auto_heal_pipeline", "confidence": confidence}),
                 "auto_heal_job", now),
            )

            stats["fixes_generated"] += 1
            print(f"  Fix generated: {fix_data.get('title', 'untitled')[:80]}", flush=True)

        except Exception as e:
            print(f"  Heal failed: {e}", flush=True)

    print(f"\n[Auto-Heal] Complete. Analyzed: {stats['analyzed']}, Fixes: {stats['fixes_generated']}, Skipped: {stats['skipped']}", flush=True)


if __name__ == "__main__":
    asyncio.run(auto_heal())
