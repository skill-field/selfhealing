"""Verify module — deployment and testing."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from modules.github_client import GitHubClient
from api.routes_events import broadcast_event
import database as db


class VerifyModule:
    """Manage deployments: create staging PRs, promote to production."""

    def __init__(self, github_client: GitHubClient):
        self.github = github_client

    async def deploy_to_staging(self, fix_id: str) -> dict:
        """Create a GitHub PR for the fix and track deployment."""
        now = datetime.now(timezone.utc).isoformat()

        # 1. Fetch fix from database (with error details)
        fix = await db.fetch_one("SELECT * FROM fixes WHERE id = ?", (fix_id,))
        if fix is None:
            raise ValueError(f"Fix {fix_id} not found")

        error = await db.fetch_one(
            "SELECT * FROM errors WHERE id = ?", (fix["error_id"],)
        )

        # 2. Parse files_changed from fix
        files_changed_raw = fix.get("files_changed", "[]")
        if isinstance(files_changed_raw, str):
            try:
                files_changed = json.loads(files_changed_raw)
            except (json.JSONDecodeError, TypeError):
                files_changed = []
        else:
            files_changed = files_changed_raw or []

        # Build file list for PR (use diff content as placeholder since we have diffs)
        pr_files = []
        for file_path in files_changed:
            pr_files.append({
                "path": file_path,
                "content": f"// Fix applied by Sentinel for fix {fix_id}\n"
                           f"// Diff:\n{fix.get('diff', 'No diff available')}",
            })

        # 3. Create GitHub PR via github_client.create_pull_request()
        error_message = error.get("error_message", "Unknown error") if error else "Unknown error"
        branch_name = f"sentinel/fix-{fix_id[:8]}"
        title = f"[Sentinel] Fix: {error_message[:80]}"
        body = (
            f"## Sentinel Auto-Fix\n\n"
            f"**Fix ID:** {fix_id}\n"
            f"**Error ID:** {fix.get('error_id', 'N/A')}\n"
            f"**Confidence:** {fix.get('confidence', 'N/A')}\n\n"
            f"### Explanation\n{fix.get('explanation', 'No explanation available')}\n\n"
            f"### Files Changed\n"
            + "\n".join(f"- `{f}`" for f in files_changed)
        )

        pr_result = await self.github.create_pull_request(
            branch_name=branch_name,
            title=title,
            body=body,
            files=pr_files,
        )

        # 4. Insert deployment record (status='deploying', environment='staging')
        deployment_id = str(uuid4())
        await db.execute(
            """INSERT INTO deployments
               (id, fix_id, environment, status, test_results, pr_url, commit_sha, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                deployment_id,
                fix_id,
                "staging",
                "deploying",
                json.dumps([]),
                pr_result.get("pr_url"),
                None,
                now,
                now,
            ),
        )

        # 5. Update deployment status to 'deployed' (with pr_url)
        await db.execute(
            "UPDATE deployments SET status = 'deployed', pr_url = ?, updated_at = ? WHERE id = ?",
            (pr_result.get("pr_url"), now, deployment_id),
        )

        # 6. Update fix status to 'deployed'
        await db.execute(
            "UPDATE fixes SET status = 'deployed', updated_at = ? WHERE id = ?",
            (now, fix_id),
        )

        # Update error status to 'fix_deployed'
        if error:
            await db.execute(
                "UPDATE errors SET status = 'fix_deployed', updated_at = ? WHERE id = ?",
                (now, fix["error_id"]),
            )

        # 7. Create audit_log entry
        await db.execute(
            """INSERT INTO audit_log (id, action, entity_type, entity_id, details, actor, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                str(uuid4()),
                "deployment.staging",
                "deployment",
                deployment_id,
                json.dumps({
                    "fix_id": fix_id,
                    "error_id": fix.get("error_id"),
                    "environment": "staging",
                    "pr_url": pr_result.get("pr_url"),
                    "pr_number": pr_result.get("pr_number"),
                }),
                "sentinel",
                now,
            ),
        )

        # 8. Broadcast SSE event (deployment_status)
        await broadcast_event("deployment_status", {
            "deployment_id": deployment_id,
            "fix_id": fix_id,
            "environment": "staging",
            "status": "deployed",
            "pr_url": pr_result.get("pr_url"),
        })

        # 9. Return deployment record
        deployment = await db.fetch_one(
            "SELECT * FROM deployments WHERE id = ?", (deployment_id,)
        )
        return deployment

    async def promote_to_production(self, deployment_id: str) -> dict:
        """Promote a staging deployment to production."""
        now = datetime.now(timezone.utc).isoformat()

        # 1. Fetch deployment
        deployment = await db.fetch_one(
            "SELECT * FROM deployments WHERE id = ?", (deployment_id,)
        )
        if deployment is None:
            raise ValueError(f"Deployment {deployment_id} not found")

        # 2. Verify status is 'deployed' or 'tests_passed'
        valid_statuses = ("deployed", "tests_passed")
        if deployment["status"] not in valid_statuses:
            raise ValueError(
                f"Deployment {deployment_id} has status '{deployment['status']}' — "
                f"must be one of {valid_statuses} to promote"
            )

        # 3. Update deployment: environment='production', status='promoted'
        await db.execute(
            "UPDATE deployments SET environment = 'production', status = 'promoted', updated_at = ? WHERE id = ?",
            (now, deployment_id),
        )

        # 4. Create audit_log entry
        await db.execute(
            """INSERT INTO audit_log (id, action, entity_type, entity_id, details, actor, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                str(uuid4()),
                "deployment.promoted",
                "deployment",
                deployment_id,
                json.dumps({
                    "fix_id": deployment["fix_id"],
                    "from_environment": deployment["environment"],
                    "to_environment": "production",
                    "pr_url": deployment.get("pr_url"),
                }),
                "sentinel",
                now,
            ),
        )

        # 5. Broadcast SSE event
        await broadcast_event("deployment_status", {
            "deployment_id": deployment_id,
            "fix_id": deployment["fix_id"],
            "environment": "production",
            "status": "promoted",
        })

        # 6. Return updated deployment
        return await db.fetch_one(
            "SELECT * FROM deployments WHERE id = ?", (deployment_id,)
        )

    async def get_deployment_status(self, deployment_id: str) -> dict:
        """Get deployment details."""
        deployment = await db.fetch_one(
            "SELECT * FROM deployments WHERE id = ?", (deployment_id,)
        )
        if deployment is None:
            raise ValueError(f"Deployment {deployment_id} not found")
        return deployment
