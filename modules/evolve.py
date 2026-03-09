"""Evolve module — feature request generation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from llm.client import AnthropicClient
from llm.context_builder import ContextBuilder
from llm.prompts import (
    FEATURE_SPEC_SYSTEM_PROMPT,
    FEATURE_SPEC_USER_TEMPLATE,
    FEATURE_IMPL_SYSTEM_PROMPT,
    FEATURE_IMPL_USER_TEMPLATE,
)
from modules.github_client import GitHubClient
from api.routes_events import broadcast_event
import database as db


class EvolveModule:
    """Generate feature implementations from natural-language requests using Claude."""

    def __init__(self, anthropic_client: AnthropicClient, github_client: GitHubClient):
        self.llm = anthropic_client
        self.github = github_client
        self.context_builder = ContextBuilder(github_client)

    async def submit_feature(
        self, title: str, description: str, priority: str = "medium"
    ) -> dict:
        """Submit a new feature request."""
        now = datetime.now(timezone.utc).isoformat()
        feature_id = str(uuid4())

        # Insert into feature_requests table
        await db.execute(
            """INSERT INTO feature_requests
               (id, title, description, priority, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, 'submitted', ?, ?)""",
            (feature_id, title, description, priority, now, now),
        )

        # Create audit_log entry
        await db.execute(
            """INSERT INTO audit_log (id, action, entity_type, entity_id, details, actor, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                str(uuid4()),
                "feature.submitted",
                "feature",
                feature_id,
                json.dumps({
                    "title": title,
                    "priority": priority,
                }),
                "sentinel",
                now,
            ),
        )

        # Return feature record
        return await db.fetch_one(
            "SELECT * FROM feature_requests WHERE id = ?", (feature_id,)
        )

    async def generate_feature(self, feature_id: str) -> dict:
        """Generate implementation for a feature request using Claude."""
        now = datetime.now(timezone.utc).isoformat()

        # 1. Fetch feature from database
        feature = await db.fetch_one(
            "SELECT * FROM feature_requests WHERE id = ?", (feature_id,)
        )
        if feature is None:
            raise ValueError(f"Feature {feature_id} not found")

        # 2. Update status to 'generating'
        await db.execute(
            "UPDATE feature_requests SET status = 'generating', updated_at = ? WHERE id = ?",
            (now, feature_id),
        )

        # Broadcast status update
        await broadcast_event("feature_status", {
            "feature_id": feature_id,
            "status": "generating",
        })

        title = feature.get("title", "")
        description = feature.get("description", "")

        # 2b. Fetch repo context for better code generation
        code_context_str = "(No source files available)"
        try:
            context = await self.context_builder.build_feature_context(title, description)
            if context["files"]:
                parts = []
                for f in context["files"]:
                    parts.append(f"### {f['path']}\n```\n{f['content']}\n```")
                code_context_str = "\n\n".join(parts)
        except Exception as e:
            print(f"[Evolve] Warning: Could not fetch code context: {e}", flush=True)

        # 3. First call: Generate specification (Claude Sonnet)
        spec_user_prompt = FEATURE_SPEC_USER_TEMPLATE.format(
            title=title,
            description=description,
        )
        spec_result = await self.llm.generate_json(
            system_prompt=FEATURE_SPEC_SYSTEM_PROMPT,
            user_prompt=spec_user_prompt,
            model="claude-sonnet-4-5",
        )
        specification = spec_result["data"]

        # 4. Second call: Generate implementation (Claude Opus)
        impl_user_prompt = FEATURE_IMPL_USER_TEMPLATE.format(
            title=title,
            description=description,
            specification=json.dumps(specification, indent=2),
        )
        # Append source code context if available
        if code_context_str != "(No source files available)":
            impl_user_prompt += f"\n\n**Existing Source Code (for reference):**\n{code_context_str}"
        impl_result = await self.llm.generate_json(
            system_prompt=FEATURE_IMPL_SYSTEM_PROMPT,
            user_prompt=impl_user_prompt,
            model="claude-sonnet-4-5",
        )
        implementation = impl_result["data"]

        # 5. Extract fields from implementation
        plan = implementation.get("plan", "")
        files = implementation.get("files", [])
        explanation = implementation.get("explanation", "")
        test_suggestions = implementation.get("test_suggestions", [])

        # Build generated_code as structured data
        generated_code = {
            "specification": specification,
            "implementation": {
                "plan": plan,
                "files": files,
                "test_suggestions": test_suggestions,
            },
        }

        # Build a unified diff string from files
        diff_parts = []
        for f in files:
            path = f.get("path", "unknown")
            action = f.get("action", "create")
            content = f.get("content", "")
            diff_parts.append(f"--- {'a/' + path if action == 'modify' else '/dev/null'}")
            diff_parts.append(f"+++ b/{path}")
            diff_parts.append(content)
            diff_parts.append("")
        generated_diff = "\n".join(diff_parts)

        # Build full explanation
        full_explanation = explanation
        if test_suggestions:
            full_explanation += "\n\nTest Suggestions:\n" + "\n".join(
                f"  - {t}" for t in test_suggestions
            )

        model_used = impl_result.get("model", "unknown")

        # 6. Update feature record
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            """UPDATE feature_requests
               SET generated_code = ?, generated_diff = ?, explanation = ?,
                   model_used = ?, status = 'generated', updated_at = ?
               WHERE id = ?""",
            (
                json.dumps(generated_code),
                generated_diff,
                full_explanation,
                model_used,
                now,
                feature_id,
            ),
        )

        # 7. Create audit_log entry
        await db.execute(
            """INSERT INTO audit_log (id, action, entity_type, entity_id, details, actor, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                str(uuid4()),
                "feature.generated",
                "feature",
                feature_id,
                json.dumps({
                    "title": title,
                    "model": model_used,
                    "files_count": len(files),
                    "complexity": specification.get("complexity", "unknown"),
                    "spec_tokens": spec_result.get("prompt_tokens", 0)
                    + spec_result.get("completion_tokens", 0),
                    "impl_tokens": impl_result.get("prompt_tokens", 0)
                    + impl_result.get("completion_tokens", 0),
                }),
                "sentinel",
                now,
            ),
        )

        # 8. Broadcast SSE event (feature_generated)
        await broadcast_event("feature_generated", {
            "feature_id": feature_id,
            "title": title,
            "files_count": len(files),
            "complexity": specification.get("complexity", "unknown"),
        })

        # 9. Return updated feature
        return await db.fetch_one(
            "SELECT * FROM feature_requests WHERE id = ?", (feature_id,)
        )

    async def approve_feature(
        self, feature_id: str, reviewer_notes: str | None = None
    ) -> dict:
        """Approve a generated feature. Optionally create GitHub PR."""
        now = datetime.now(timezone.utc).isoformat()

        feature = await db.fetch_one(
            "SELECT * FROM feature_requests WHERE id = ?", (feature_id,)
        )
        if feature is None:
            raise ValueError(f"Feature {feature_id} not found")

        pr_url = None

        # If github token available, create PR
        if self.github.token:
            # Parse generated_code to get files
            generated_code_raw = feature.get("generated_code", "{}")
            if isinstance(generated_code_raw, str):
                try:
                    generated_code = json.loads(generated_code_raw)
                except (json.JSONDecodeError, TypeError):
                    generated_code = {}
            else:
                generated_code = generated_code_raw or {}

            impl = generated_code.get("implementation", {})
            files = impl.get("files", [])

            if files:
                pr_files = []
                for f in files:
                    pr_files.append({
                        "path": f.get("path", "unknown"),
                        "content": f.get("content", ""),
                    })

                branch_name = f"sentinel/feature-{feature_id[:8]}"
                title = f"[Sentinel] Feature: {feature.get('title', 'New Feature')[:80]}"
                body = (
                    f"## Sentinel Feature Generation\n\n"
                    f"**Feature ID:** {feature_id}\n"
                    f"**Title:** {feature.get('title', 'N/A')}\n"
                    f"**Priority:** {feature.get('priority', 'N/A')}\n\n"
                    f"### Description\n{feature.get('description', 'N/A')}\n\n"
                    f"### Explanation\n{feature.get('explanation', 'N/A')}\n\n"
                    f"### Files\n"
                    + "\n".join(f"- `{f.get('path', 'unknown')}`" for f in files)
                )

                if reviewer_notes:
                    body += f"\n\n### Reviewer Notes\n{reviewer_notes}"

                pr_result = await self.github.create_pull_request(
                    branch_name=branch_name,
                    title=title,
                    body=body,
                    files=pr_files,
                )
                pr_url = pr_result.get("pr_url")

        # Update status to 'approved'
        await db.execute(
            """UPDATE feature_requests
               SET status = 'approved', reviewer_notes = ?, pr_url = ?, updated_at = ?
               WHERE id = ?""",
            (reviewer_notes, pr_url, now, feature_id),
        )

        # Create audit_log entry
        await db.execute(
            """INSERT INTO audit_log (id, action, entity_type, entity_id, details, actor, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                str(uuid4()),
                "feature.approved",
                "feature",
                feature_id,
                json.dumps({
                    "title": feature.get("title"),
                    "reviewer_notes": reviewer_notes,
                    "pr_url": pr_url,
                }),
                "sentinel",
                now,
            ),
        )

        # Broadcast SSE event
        await broadcast_event("feature_approved", {
            "feature_id": feature_id,
            "title": feature.get("title"),
            "pr_url": pr_url,
        })

        return await db.fetch_one(
            "SELECT * FROM feature_requests WHERE id = ?", (feature_id,)
        )

    async def reject_feature(self, feature_id: str, reviewer_notes: str) -> dict:
        """Reject a feature."""
        now = datetime.now(timezone.utc).isoformat()

        feature = await db.fetch_one(
            "SELECT * FROM feature_requests WHERE id = ?", (feature_id,)
        )
        if feature is None:
            raise ValueError(f"Feature {feature_id} not found")

        # Update status to 'rejected'
        await db.execute(
            """UPDATE feature_requests
               SET status = 'rejected', reviewer_notes = ?, updated_at = ?
               WHERE id = ?""",
            (reviewer_notes, now, feature_id),
        )

        # Create audit_log entry
        await db.execute(
            """INSERT INTO audit_log (id, action, entity_type, entity_id, details, actor, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                str(uuid4()),
                "feature.rejected",
                "feature",
                feature_id,
                json.dumps({
                    "title": feature.get("title"),
                    "reviewer_notes": reviewer_notes,
                }),
                "sentinel",
                now,
            ),
        )

        # Broadcast SSE event
        await broadcast_event("feature_rejected", {
            "feature_id": feature_id,
            "title": feature.get("title"),
            "reviewer_notes": reviewer_notes,
        })

        return await db.fetch_one(
            "SELECT * FROM feature_requests WHERE id = ?", (feature_id,)
        )
