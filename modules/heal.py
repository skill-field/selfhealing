"""Heal module — AI-powered fix generation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from llm.client import AnthropicClient
from llm.context_builder import ContextBuilder
from llm.prompts import FIX_GENERATION_SYSTEM_PROMPT, FIX_GENERATION_USER_TEMPLATE
from modules.github_client import GitHubClient
from api.routes_events import broadcast_event
import database as db


class HealModule:
    """Generate, approve, and reject code fixes using Claude."""

    def __init__(
        self,
        anthropic_client: AnthropicClient,
        github_client: GitHubClient,
        context_builder: ContextBuilder,
    ):
        self.llm = anthropic_client
        self.github = github_client
        self.context = context_builder

    async def generate_fix(
        self, error_id: str, guidance: str | None = None
    ) -> dict:
        """Generate a code fix for an error using Claude Opus.

        Args:
            error_id: The ID of the error to fix.
            guidance: Optional human guidance (used during regeneration).

        Returns:
            The created fix record as a dict.
        """
        # 1. Fetch error from database
        error = await db.fetch_one("SELECT * FROM errors WHERE id = ?", (error_id,))
        if error is None:
            raise ValueError(f"Error {error_id} not found")

        # 2. Build code context via ContextBuilder
        code_ctx = await self.context.build_fix_context(error)

        # Format code context for prompt
        if code_ctx["files"]:
            code_context_str = ""
            for f in code_ctx["files"]:
                code_context_str += f"\n--- {f['path']} ({f['relevant_lines']}) ---\n"
                code_context_str += f["content"]
                code_context_str += "\n"
        else:
            code_context_str = "(No source code context available — GitHub token may not be configured.)"

        # 3. Format prompt using templates
        user_prompt = FIX_GENERATION_USER_TEMPLATE.format(
            error_message=error.get("error_message", "Unknown"),
            error_type=error.get("error_type", "Unknown"),
            root_cause=error.get("root_cause", "Not yet analysed"),
            category=error.get("category", "unknown"),
            severity=error.get("severity", "medium"),
            occurrence_count=error.get("occurrence_count", 1),
            stack_trace=error.get("stack_trace", "No stack trace available"),
            code_context=code_context_str,
        )

        # 4. If guidance provided (regeneration), append to user prompt
        if guidance:
            user_prompt += f"\n\n**ADDITIONAL GUIDANCE FROM REVIEWER:**\n{guidance}"

        # 5. Call Claude for fix generation
        llm_result = await self.llm.generate_json(
            system_prompt=FIX_GENERATION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            model="claude-sonnet-4-5",
        )

        parsed = llm_result["data"]

        # 6. Check for parse errors (e.g. truncated response)
        if parsed.get("parse_error"):
            raise ValueError(f"LLM response could not be parsed as JSON: {parsed.get('raw_response', '')[:200]}")

        # Extract fields from parsed response
        files_changed = parsed.get("files_changed", [])
        explanation = parsed.get("explanation", "")
        confidence = parsed.get("confidence", 0.0)
        risk_assessment = parsed.get("risk_assessment", "medium")
        test_suggestions = parsed.get("test_suggestions", [])

        # Build a unified diff string from files_changed
        diff_parts = []
        file_paths = []
        for fc in files_changed:
            file_paths.append(fc.get("path", "unknown"))
            diff_parts.append(fc.get("diff", ""))
        combined_diff = "\n".join(diff_parts)

        # Enrich explanation with risk and test info
        full_explanation = explanation
        if risk_assessment:
            full_explanation += f"\n\nRisk Assessment: {risk_assessment}"
        if test_suggestions:
            full_explanation += "\n\nTest Suggestions:\n" + "\n".join(
                f"  - {t}" for t in test_suggestions
            )

        # 7. Count attempt_number (query existing fixes for this error)
        existing = await db.fetch_all(
            "SELECT id FROM fixes WHERE error_id = ?", (error_id,)
        )
        attempt_number = len(existing) + 1

        # 8. Insert fix record into database
        now = datetime.now(timezone.utc).isoformat()
        fix_id = str(uuid4())

        await db.execute(
            """INSERT INTO fixes
               (id, error_id, diff, explanation, files_changed, confidence,
                model_used, prompt_tokens, completion_tokens, status,
                attempt_number, guidance, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?)""",
            (
                fix_id,
                error_id,
                combined_diff,
                full_explanation,
                json.dumps(file_paths),
                confidence,
                llm_result.get("model", "unknown"),
                llm_result.get("prompt_tokens", 0),
                llm_result.get("completion_tokens", 0),
                attempt_number,
                guidance,
                now,
                now,
            ),
        )

        # 9. Update error status to 'fix_generated'
        await db.execute(
            "UPDATE errors SET status = 'fix_generated', updated_at = ? WHERE id = ?",
            (now, error_id),
        )

        # 10. Create audit_log entry
        await db.execute(
            """INSERT INTO audit_log (id, action, entity_type, entity_id, details, actor, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                str(uuid4()),
                "fix.generated",
                "fix",
                fix_id,
                json.dumps({
                    "error_id": error_id,
                    "attempt_number": attempt_number,
                    "confidence": confidence,
                    "model": llm_result.get("model", "unknown"),
                    "files_changed": file_paths,
                    "has_guidance": bool(guidance),
                }),
                "sentinel",
                now,
            ),
        )

        # 11. Broadcast SSE event
        await broadcast_event("fix_generated", {
            "fix_id": fix_id,
            "error_id": error_id,
            "attempt_number": attempt_number,
            "confidence": confidence,
            "files_changed": file_paths,
        })

        # 12. Return fix record
        fix_record = await db.fetch_one("SELECT * FROM fixes WHERE id = ?", (fix_id,))
        return fix_record

    async def approve_fix(
        self, fix_id: str, reviewer_notes: str | None = None
    ) -> dict:
        """Approve a fix for deployment."""
        now = datetime.now(timezone.utc).isoformat()

        # Get fix to find error_id
        fix = await db.fetch_one("SELECT * FROM fixes WHERE id = ?", (fix_id,))
        if fix is None:
            raise ValueError(f"Fix {fix_id} not found")

        # Update fix status to 'approved'
        await db.execute(
            "UPDATE fixes SET status = 'approved', reviewer_notes = ?, updated_at = ? WHERE id = ?",
            (reviewer_notes, now, fix_id),
        )

        # Update error status to 'fix_approved'
        await db.execute(
            "UPDATE errors SET status = 'fix_approved', updated_at = ? WHERE id = ?",
            (now, fix["error_id"]),
        )

        # Create audit_log entry
        await db.execute(
            """INSERT INTO audit_log (id, action, entity_type, entity_id, details, actor, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                str(uuid4()),
                "fix.approved",
                "fix",
                fix_id,
                json.dumps({
                    "error_id": fix["error_id"],
                    "reviewer_notes": reviewer_notes,
                }),
                "sentinel",
                now,
            ),
        )

        # Broadcast SSE event
        await broadcast_event("fix_approved", {
            "fix_id": fix_id,
            "error_id": fix["error_id"],
        })

        return await db.fetch_one("SELECT * FROM fixes WHERE id = ?", (fix_id,))

    async def reject_fix(self, fix_id: str, reason: str) -> dict:
        """Reject a fix."""
        now = datetime.now(timezone.utc).isoformat()

        fix = await db.fetch_one("SELECT * FROM fixes WHERE id = ?", (fix_id,))
        if fix is None:
            raise ValueError(f"Fix {fix_id} not found")

        # Update fix status to 'rejected'
        await db.execute(
            "UPDATE fixes SET status = 'rejected', reviewer_notes = ?, updated_at = ? WHERE id = ?",
            (reason, now, fix_id),
        )

        # Create audit_log entry
        await db.execute(
            """INSERT INTO audit_log (id, action, entity_type, entity_id, details, actor, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                str(uuid4()),
                "fix.rejected",
                "fix",
                fix_id,
                json.dumps({
                    "error_id": fix["error_id"],
                    "reason": reason,
                }),
                "sentinel",
                now,
            ),
        )

        # Broadcast SSE event
        await broadcast_event("fix_rejected", {
            "fix_id": fix_id,
            "error_id": fix["error_id"],
            "reason": reason,
        })

        return await db.fetch_one("SELECT * FROM fixes WHERE id = ?", (fix_id,))
