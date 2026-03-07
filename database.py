"""Database module using aiosqlite for Skillfield Sentinel."""
from __future__ import annotations

import os
import json
from typing import Optional, List, Dict, Any
import aiosqlite
from datetime import datetime, timezone
from uuid import uuid4
from config import settings

DB_PATH = settings.DB_PATH


async def get_db() -> aiosqlite.Connection:
    """Get a database connection with WAL mode and row factory enabled."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    db = await aiosqlite.connect(DB_PATH)
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    db.row_factory = aiosqlite.Row
    return db


async def execute(sql: str, params: tuple = ()) -> None:
    """Execute a single SQL statement."""
    db = await get_db()
    try:
        await db.execute(sql, params)
        await db.commit()
    finally:
        await db.close()


async def fetch_one(sql: str, params: tuple = ()) -> dict | None:
    """Fetch a single row and return as dict."""
    db = await get_db()
    try:
        cursor = await db.execute(sql, params)
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)
    finally:
        await db.close()


async def fetch_all(sql: str, params: tuple = ()) -> list[dict]:
    """Fetch all rows and return as list of dicts."""
    db = await get_db()
    try:
        cursor = await db.execute(sql, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def init_db() -> None:
    """Create all tables and seed default configuration."""
    db = await get_db()
    try:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS errors (
                id TEXT PRIMARY KEY,
                source TEXT,
                environment TEXT,
                raw_log TEXT,
                error_message TEXT,
                error_type TEXT,
                stack_trace TEXT,
                severity TEXT CHECK(severity IN ('critical', 'high', 'medium', 'low')),
                category TEXT CHECK(category IN ('database', 'auth', 'api', 'ui', 'integration', 'ai', 'infrastructure', 'unknown')),
                root_cause TEXT,
                affected_file TEXT,
                affected_files TEXT DEFAULT '[]',
                fingerprint TEXT,
                occurrence_count INTEGER DEFAULT 1,
                first_seen TEXT,
                last_seen TEXT,
                status TEXT DEFAULT 'new' CHECK(status IN ('new', 'acknowledged', 'fix_generated', 'fix_approved', 'fix_deployed', 'resolved', 'ignored')),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS fixes (
                id TEXT PRIMARY KEY,
                error_id TEXT NOT NULL,
                diff TEXT,
                explanation TEXT,
                files_changed TEXT DEFAULT '[]',
                confidence REAL,
                model_used TEXT,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected', 'deployed', 'failed')),
                reviewer_notes TEXT,
                attempt_number INTEGER DEFAULT 1,
                guidance TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (error_id) REFERENCES errors(id)
            );

            CREATE TABLE IF NOT EXISTS deployments (
                id TEXT PRIMARY KEY,
                fix_id TEXT NOT NULL,
                environment TEXT,
                status TEXT,
                test_results TEXT DEFAULT '[]',
                pr_url TEXT,
                commit_sha TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (fix_id) REFERENCES fixes(id)
            );

            CREATE TABLE IF NOT EXISTS feature_requests (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                priority TEXT,
                generated_code TEXT DEFAULT '{}',
                generated_diff TEXT,
                explanation TEXT,
                model_used TEXT,
                status TEXT DEFAULT 'submitted' CHECK(status IN ('submitted', 'generating', 'generated', 'approved', 'rejected', 'deployed')),
                reviewer_notes TEXT,
                pr_url TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id TEXT PRIMARY KEY,
                action TEXT NOT NULL,
                entity_type TEXT,
                entity_id TEXT,
                details TEXT DEFAULT '{}',
                actor TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS system_config (
                key TEXT PRIMARY KEY,
                value TEXT DEFAULT '{}',
                description TEXT,
                updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_errors_status ON errors(status);
            CREATE INDEX IF NOT EXISTS idx_errors_severity ON errors(severity);
            CREATE INDEX IF NOT EXISTS idx_errors_fingerprint ON errors(fingerprint);
            CREATE INDEX IF NOT EXISTS idx_fixes_error_id ON fixes(error_id);
            CREATE INDEX IF NOT EXISTS idx_fixes_status ON fixes(status);
            CREATE INDEX IF NOT EXISTS idx_deployments_fix_id ON deployments(fix_id);
            CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id);

            CREATE TABLE IF NOT EXISTS monitored_repos (
                id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                repo_slug TEXT NOT NULL UNIQUE,
                github_token TEXT,
                scan_paths TEXT DEFAULT '[]',
                is_active INTEGER DEFAULT 1,
                source_type TEXT DEFAULT 'github',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS log_sources (
                id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                source_type TEXT NOT NULL CHECK(source_type IN ('container', 'log_endpoint', 'syslog', 'file')),
                endpoint_url TEXT,
                container_id TEXT,
                container_image TEXT,
                environment TEXT DEFAULT 'production',
                auth_header TEXT,
                poll_interval_seconds INTEGER DEFAULT 60,
                is_active INTEGER DEFAULT 1,
                last_polled_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)

        # Add repo_id column to existing tables (safe migration)
        for table in ["errors", "fixes", "feature_requests", "deployments"]:
            try:
                await db.execute(f"ALTER TABLE {table} ADD COLUMN repo_id TEXT REFERENCES monitored_repos(id)")
            except Exception:
                pass  # column already exists

        await db.execute("CREATE INDEX IF NOT EXISTS idx_errors_repo_id ON errors(repo_id)")

        # Seed default monitored repo
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            """INSERT OR IGNORE INTO monitored_repos
               (id, display_name, repo_slug, scan_paths, is_active, source_type, created_at, updated_at)
               VALUES (?, ?, ?, ?, 1, 'github', ?, ?)""",
            ("default", "Metrics AI", settings.GITHUB_REPO,
             json.dumps([
                 "src/lib/services/metric/metric.service.ts",
                 "src/lib/services/metric/metric-value.service.ts",
                 "src/lib/services/scorecard/scorecard.service.ts",
                 "src/lib/services/tenant/tenant.service.ts",
                 "src/lib/auth/auth.config.ts",
                 "prisma/schema.prisma",
                 "src/app/api/v1/metrics/route.ts",
                 "src/app/api/v1/scorecards/route.ts",
                 "next.config.ts",
             ]), now, now),
        )
        # Backfill existing errors with default repo_id
        await db.execute("UPDATE errors SET repo_id = 'default' WHERE repo_id IS NULL")

        # Seed default system_config values
        defaults = [
            ("auto_fix_enabled", json.dumps(False), "Automatically generate fixes for new errors", now),
            ("auto_deploy_enabled", json.dumps(False), "Automatically deploy approved fixes", now),
            ("max_fix_attempts", json.dumps(3), "Maximum fix generation attempts per error", now),
            ("min_confidence_threshold", json.dumps(0.7), "Minimum confidence score to auto-approve fixes", now),
            ("watched_severities", json.dumps(["critical", "high"]), "Severities that trigger automatic fix generation", now),
            ("target_environments", json.dumps(["staging", "production"]), "Environments to monitor", now),
            ("model_preference", json.dumps("claude-sonnet-4-20250514"), "Preferred Claude model for fix generation", now),
            ("github_repo", json.dumps(settings.GITHUB_REPO), "Target GitHub repository", now),
        ]
        for key, value, description, updated_at in defaults:
            await db.execute(
                "INSERT OR IGNORE INTO system_config (key, value, description, updated_at) VALUES (?, ?, ?, ?)",
                (key, value, description, updated_at),
            )

        await db.commit()
    finally:
        await db.close()
