#!/usr/bin/env python3
"""Seed the Sentinel database with realistic demo data for the hackathon.

Usage:
    python scripts/seed_demo_data.py           # append data
    python scripts/seed_demo_data.py --clear   # clear existing data first

Idempotent: running multiple times with --clear gives a fresh, consistent dataset.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from uuid import uuid4

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db, init_db  # noqa: E402

# ─── Timestamp helpers ───────────────────────────────────────────────────────

NOW = datetime.now(timezone.utc)


def _hours_ago(h: float) -> str:
    """Return an ISO timestamp *h* hours before NOW."""
    return (NOW - timedelta(hours=h)).isoformat()


def _rand_hours_ago(min_h: float, max_h: float) -> str:
    """Return a random ISO timestamp between min_h and max_h hours ago."""
    h = random.uniform(min_h, max_h)
    return (NOW - timedelta(hours=h)).isoformat()


def _uid() -> str:
    return uuid4().hex


# ─── Demo errors ─────────────────────────────────────────────────────────────

DEMO_ERRORS: list[dict] = [
    # ── Database ──────────────────────────────────────────────────────────
    {
        "error_message": "[PrismaClientKnownRequestError] Unique constraint violated on field: scorecard_id_name",
        "error_type": "PrismaClientKnownRequestError",
        "category": "database",
        "severity": "medium",
        "stack_trace": "PrismaClientKnownRequestError: Unique constraint failed on the constraint: `metrics_scorecard_id_name_key`\n    at PrismaService.create (src/lib/prisma.ts:45:12)\n    at MetricService.create (src/lib/services/metric/metric.service.ts:67:20)",
        "status": "new",
        "affected_file": "src/lib/services/metric/metric.service.ts",
    },
    {
        "error_message": "[PrismaClientKnownRequestError] Connection pool exhausted — no available connections (P2024)",
        "error_type": "PrismaClientKnownRequestError",
        "category": "database",
        "severity": "critical",
        "stack_trace": "PrismaClientKnownRequestError: Timed out fetching a new connection from the connection pool. (P2024)\n    at PrismaService.connect (src/lib/prisma.ts:22:10)\n    at ScorecardService.findMany (src/lib/services/scorecard/scorecard.service.ts:34:18)",
        "status": "fix_generated",
        "affected_file": "src/lib/prisma.ts",
    },
    {
        "error_message": "[PrismaClientKnownRequestError] Record not found (P2025) — scorecard.findUniqueOrThrow",
        "error_type": "PrismaClientKnownRequestError",
        "category": "database",
        "severity": "medium",
        "stack_trace": "PrismaClientKnownRequestError: An operation failed because it depends on one or more records that were required but not found. (P2025)\n    at ScorecardService.getById (src/lib/services/scorecard/scorecard.service.ts:58:12)",
        "status": "acknowledged",
        "affected_file": "src/lib/services/scorecard/scorecard.service.ts",
    },
    {
        "error_message": "[PrismaError] Prisma migration drift detected — database schema does not match migration history",
        "error_type": "PrismaMigrationError",
        "category": "database",
        "severity": "high",
        "stack_trace": "PrismaMigrationError: The database schema is not in sync with the migration history.\n    at PrismaService.ensureMigrations (src/lib/prisma.ts:78:8)",
        "status": "fix_generated",
        "affected_file": "prisma/schema.prisma",
    },
    {
        "error_message": "[PrismaClientKnownRequestError] Foreign key constraint failed on field: organization_id",
        "error_type": "PrismaClientKnownRequestError",
        "category": "database",
        "severity": "high",
        "stack_trace": "PrismaClientKnownRequestError: Foreign key constraint failed on the field: `organization_id`\n    at UserService.create (src/lib/services/user/user.service.ts:42:14)\n    at InviteService.acceptInvite (src/lib/services/invite/invite.service.ts:88:16)",
        "status": "new",
        "affected_file": "src/lib/services/user/user.service.ts",
    },
    {
        "error_message": "[DatabaseError] Deadlock detected during concurrent metric value inserts",
        "error_type": "DatabaseDeadlockError",
        "category": "database",
        "severity": "critical",
        "stack_trace": "DatabaseDeadlockError: Deadlock detected\n    at MetricValueService.batchInsert (src/lib/services/metric/metric-value.service.ts:112:10)\n    at BulkImportService.importValues (src/lib/services/import/bulk-import.service.ts:67:14)",
        "status": "fix_approved",
        "affected_file": "src/lib/services/metric/metric-value.service.ts",
    },
    # ── Auth ──────────────────────────────────────────────────────────────
    {
        "error_message": "[AuthError] Session expired for user csso_hani",
        "error_type": "SessionExpiredError",
        "category": "auth",
        "severity": "low",
        "stack_trace": "SessionExpiredError: JWT token expired\n    at validateSession (src/lib/auth/session.ts:34:8)\n    at middleware (src/middleware.ts:22:12)",
        "status": "resolved",
        "affected_file": "src/lib/auth/session.ts",
    },
    {
        "error_message": "[NextAuthError] OAuth callback error — invalid state parameter",
        "error_type": "OAuthCallbackError",
        "category": "auth",
        "severity": "high",
        "stack_trace": "OAuthCallbackError: State mismatch in OAuth callback\n    at handleCallback (src/app/api/auth/[...nextauth]/route.ts:45:10)\n    at NextAuth.handler (node_modules/next-auth/src/index.ts:230:14)",
        "status": "fix_generated",
        "affected_file": "src/app/api/auth/[...nextauth]/route.ts",
    },
    {
        "error_message": "[AuthError] Tenant isolation violation — user attempting cross-org data access",
        "error_type": "TenantIsolationError",
        "category": "auth",
        "severity": "critical",
        "stack_trace": "TenantIsolationError: User org_abc tried to access resource owned by org_xyz\n    at TenantGuard.validate (src/lib/auth/tenant-guard.ts:28:12)\n    at ScorecardController.get (src/app/api/v1/scorecards/[id]/route.ts:18:8)",
        "status": "fix_generated",
        "affected_file": "src/lib/auth/tenant-guard.ts",
    },
    {
        "error_message": "[AuthError] CSRF token mismatch on POST /api/v1/scorecards",
        "error_type": "CSRFError",
        "category": "auth",
        "severity": "medium",
        "stack_trace": "CSRFError: CSRF token validation failed\n    at csrfMiddleware (src/lib/middleware/csrf.ts:19:10)\n    at middleware (src/middleware.ts:35:8)",
        "status": "acknowledged",
        "affected_file": "src/lib/middleware/csrf.ts",
    },
    # ── API ───────────────────────────────────────────────────────────────
    {
        "error_message": "[MetricService] Failed to calculate formula for metric clx_abc123",
        "error_type": "FormulaError",
        "category": "api",
        "severity": "high",
        "stack_trace": "Error: Failed to calculate formula\n    at MetricService.calculateFormula (src/lib/services/metric/metric.service.ts:245:12)\n    at async MetricValueService.createMetricValue (src/lib/services/metric/metric-value.service.ts:89:20)",
        "status": "fix_generated",
        "affected_file": "src/lib/services/metric/metric.service.ts",
    },
    {
        "error_message": "[ZodError] Validation failed on POST /api/v1/metrics — invalid 'target' field type",
        "error_type": "ZodError",
        "category": "api",
        "severity": "medium",
        "stack_trace": "ZodError: [\n  {\n    \"code\": \"invalid_type\",\n    \"expected\": \"number\",\n    \"received\": \"string\",\n    \"path\": [\"target\"]\n  }\n]\n    at MetricSchema.parse (src/lib/schemas/metric.schema.ts:34:10)\n    at MetricController.create (src/app/api/v1/metrics/route.ts:22:14)",
        "status": "resolved",
        "affected_file": "src/lib/schemas/metric.schema.ts",
    },
    {
        "error_message": "[ServiceError] Rate limit exceeded for tenant org_acme — 100 requests/min",
        "error_type": "RateLimitError",
        "category": "api",
        "severity": "medium",
        "stack_trace": "RateLimitError: Rate limit exceeded\n    at RateLimiter.check (src/lib/middleware/rate-limiter.ts:45:12)\n    at middleware (src/middleware.ts:48:8)",
        "status": "acknowledged",
        "affected_file": "src/lib/middleware/rate-limiter.ts",
    },
    {
        "error_message": "[ServiceError] Scorecard export failed — PDF generation timeout after 30s",
        "error_type": "ExportTimeoutError",
        "category": "api",
        "severity": "medium",
        "stack_trace": "ExportTimeoutError: PDF generation timed out\n    at ExportService.generatePDF (src/lib/services/export/export.service.ts:89:14)\n    at ScorecardController.export (src/app/api/v1/scorecards/[id]/export/route.ts:28:10)",
        "status": "new",
        "affected_file": "src/lib/services/export/export.service.ts",
    },
    {
        "error_message": "[CORSError] Blocked cross-origin request from https://staging.m8x.ai to https://api.m8x.ai",
        "error_type": "CORSError",
        "category": "api",
        "severity": "low",
        "stack_trace": "CORSError: Origin https://staging.m8x.ai not allowed\n    at corsMiddleware (src/lib/middleware/cors.ts:22:10)",
        "status": "resolved",
        "affected_file": "src/lib/middleware/cors.ts",
    },
    {
        "error_message": "[ValidationError] Invalid metric formula expression: SUM(revenue / )",
        "error_type": "FormulaValidationError",
        "category": "api",
        "severity": "low",
        "stack_trace": "FormulaValidationError: Unexpected end of expression\n    at FormulaParser.parse (src/lib/formula/parser.ts:134:16)\n    at MetricService.validateFormula (src/lib/services/metric/metric.service.ts:198:12)",
        "status": "new",
        "affected_file": "src/lib/formula/parser.ts",
    },
    {
        "error_message": "[ServiceError] Bulk metric value import failed — CSV row 847 has invalid date format",
        "error_type": "ImportParseError",
        "category": "api",
        "severity": "low",
        "stack_trace": "ImportParseError: Invalid date format at row 847: '13/32/2025'\n    at CSVParser.parseRow (src/lib/services/import/csv-parser.ts:67:14)\n    at BulkImportService.importCSV (src/lib/services/import/bulk-import.service.ts:45:10)",
        "status": "ignored",
        "affected_file": "src/lib/services/import/csv-parser.ts",
    },
    # ── Integration ───────────────────────────────────────────────────────
    {
        "error_message": "[IntegrationService] Google Sheets API rate limit exceeded",
        "error_type": "RateLimitError",
        "category": "integration",
        "severity": "medium",
        "stack_trace": "RateLimitError: 429 Too Many Requests\n    at GoogleSheetsConnector.syncData (src/lib/services/integration/google-sheets.service.ts:156:14)",
        "status": "acknowledged",
        "affected_file": "src/lib/services/integration/google-sheets.service.ts",
    },
    {
        "error_message": "[IntegrationService] HubSpot webhook delivery failed — 502 Bad Gateway",
        "error_type": "WebhookDeliveryError",
        "category": "integration",
        "severity": "medium",
        "stack_trace": "WebhookDeliveryError: Webhook POST to https://api.hubspot.com/webhooks/v3/... returned 502\n    at WebhookService.deliver (src/lib/services/webhook/webhook.service.ts:78:12)\n    at IntegrationService.notify (src/lib/services/integration/integration.service.ts:112:8)",
        "status": "new",
        "affected_file": "src/lib/services/webhook/webhook.service.ts",
    },
    {
        "error_message": "[IntegrationService] SendGrid email delivery bounced — invalid recipient domain",
        "error_type": "EmailBounceError",
        "category": "integration",
        "severity": "low",
        "stack_trace": "EmailBounceError: Hard bounce for recipient: user@nonexistent-domain.xyz\n    at EmailService.handleBounce (src/lib/services/email/email.service.ts:134:10)\n    at SendGridWebhook.process (src/lib/services/integration/sendgrid.service.ts:89:8)",
        "status": "ignored",
        "affected_file": "src/lib/services/email/email.service.ts",
    },
    {
        "error_message": "[IntegrationService] Slack notification failed — channel not found #metrics-alerts",
        "error_type": "SlackAPIError",
        "category": "integration",
        "severity": "medium",
        "stack_trace": "SlackAPIError: channel_not_found\n    at SlackService.postMessage (src/lib/services/notification/slack.service.ts:56:12)\n    at NotificationService.send (src/lib/services/notification/notification.service.ts:34:8)",
        "status": "fix_generated",
        "affected_file": "src/lib/services/notification/slack.service.ts",
    },
    # ── AI ────────────────────────────────────────────────────────────────
    {
        "error_message": "[CircuitBreakerError] AI provider circuit open after 5 consecutive failures",
        "error_type": "CircuitBreakerError",
        "category": "ai",
        "severity": "high",
        "stack_trace": "CircuitBreakerError: Circuit breaker is open\n    at AIProvider.generate (src/lib/ai-provider.ts:89:10)\n    at InsightService.generateInsight (src/lib/services/insight/insight.service.ts:45:18)",
        "status": "fix_generated",
        "affected_file": "src/lib/ai-provider.ts",
    },
    {
        "error_message": "[OpenAIError] Token budget exceeded for insight generation — 128k context limit reached",
        "error_type": "TokenBudgetError",
        "category": "ai",
        "severity": "medium",
        "stack_trace": "TokenBudgetError: Request exceeds model context window (128000 tokens)\n    at OpenAIClient.chat (src/lib/ai/openai-client.ts:67:10)\n    at InsightService.generateInsight (src/lib/services/insight/insight.service.ts:52:14)",
        "status": "acknowledged",
        "affected_file": "src/lib/ai/openai-client.ts",
    },
    {
        "error_message": "[OllamaError] Local model server unresponsive — connection refused on port 11434",
        "error_type": "OllamaConnectionError",
        "category": "ai",
        "severity": "medium",
        "stack_trace": "OllamaConnectionError: ECONNREFUSED 127.0.0.1:11434\n    at OllamaClient.generate (src/lib/ai/ollama-client.ts:34:10)\n    at AIProvider.fallbackGenerate (src/lib/ai-provider.ts:112:14)",
        "status": "new",
        "affected_file": "src/lib/ai/ollama-client.ts",
    },
    # ── Infrastructure ────────────────────────────────────────────────────
    {
        "error_message": "[InfraError] Container OOMKilled — memory limit 512Mi exceeded (RSS: 623Mi)",
        "error_type": "OOMKilledError",
        "category": "infrastructure",
        "severity": "critical",
        "stack_trace": "OOMKilledError: Container metrics-app killed: OOMKilled (exit code 137)\n    at HealthMonitor.checkContainer (src/lib/infra/health-monitor.ts:45:8)",
        "status": "fix_approved",
        "affected_file": "docker/Dockerfile",
    },
    {
        "error_message": "[InfraError] Redis connection timeout — BullMQ worker unable to fetch jobs",
        "error_type": "RedisTimeoutError",
        "category": "infrastructure",
        "severity": "high",
        "stack_trace": "RedisTimeoutError: Connection to Redis at redis://redis:6379 timed out after 5000ms\n    at BullMQWorker.connect (src/lib/queue/worker.ts:28:10)\n    at QueueService.init (src/lib/services/queue/queue.service.ts:18:8)",
        "status": "resolved",
        "affected_file": "src/lib/queue/worker.ts",
    },
    {
        "error_message": "[InfraError] BullMQ worker crashed — unhandled job failure in metrics-sync queue",
        "error_type": "WorkerCrashError",
        "category": "infrastructure",
        "severity": "high",
        "stack_trace": "WorkerCrashError: Worker process exited unexpectedly\n    at MetricsSyncWorker.process (src/lib/queue/metrics-sync.worker.ts:56:12)\n    at BullMQWorker.run (src/lib/queue/worker.ts:45:8)",
        "status": "fix_generated",
        "affected_file": "src/lib/queue/metrics-sync.worker.ts",
    },
    {
        "error_message": "[InfraError] Health check failed for /api/v1/health — 3 consecutive failures",
        "error_type": "HealthCheckError",
        "category": "infrastructure",
        "severity": "high",
        "stack_trace": "HealthCheckError: Health check returned non-200: 503\n    at HealthMonitor.probe (src/lib/infra/health-monitor.ts:67:10)",
        "status": "resolved",
        "affected_file": "src/lib/infra/health-monitor.ts",
    },
    {
        "error_message": "[InfraError] Disk usage at 94% on /data volume — approaching ENOSPC",
        "error_type": "DiskSpaceWarning",
        "category": "infrastructure",
        "severity": "high",
        "stack_trace": "DiskSpaceWarning: Volume /data is 94% full (47.2G / 50G)\n    at DiskMonitor.check (src/lib/infra/disk-monitor.ts:23:8)",
        "status": "acknowledged",
        "affected_file": "src/lib/infra/disk-monitor.ts",
    },
]

# ─── Demo fixes ──────────────────────────────────────────────────────────────

DEMO_FIXES: list[dict] = [
    {
        "error_index": 1,  # Connection pool exhausted
        "diff": "--- a/src/lib/prisma.ts\n+++ b/src/lib/prisma.ts\n@@ -8,7 +8,12 @@\n const prisma = new PrismaClient({\n-  datasources: { db: { url: process.env.DATABASE_URL } },\n+  datasources: { db: { url: process.env.DATABASE_URL } },\n+  // Increase pool size and add timeout handling\n+  connection_limit: 20,\n+  pool_timeout: 10,\n+  connect_timeout: 10,\n });\n+\n+// Add connection pool monitoring\n+prisma.$on('query', (e) => {\n+  if (e.duration > 2000) logger.warn(`Slow query: ${e.query} (${e.duration}ms)`);\n+});",
        "explanation": "The connection pool was set to the default size of 5, which is insufficient under load. Increased to 20 connections with explicit timeout handling and added slow query monitoring.",
        "confidence": 0.91,
        "model_used": "claude-opus-4-20250514",
        "status": "approved",
    },
    {
        "error_index": 3,  # Migration drift
        "diff": "--- a/prisma/schema.prisma\n+++ b/prisma/schema.prisma\n@@ -45,6 +45,8 @@\n model Metric {\n   id          String   @id @default(cuid())\n   name        String\n+  formula     String?  @db.Text\n+  formulaType String?  @map(\"formula_type\")\n   scorecardId String   @map(\"scorecard_id\")\n   scorecard   Scorecard @relation(fields: [scorecardId], references: [id])\n   @@unique([scorecardId, name])\n }",
        "explanation": "The schema.prisma file was missing the formula and formulaType columns that were added in a migration. Synced the schema to match the actual database state.",
        "confidence": 0.88,
        "model_used": "claude-opus-4-20250514",
        "status": "deployed",
    },
    {
        "error_index": 5,  # Deadlock
        "diff": "--- a/src/lib/services/metric/metric-value.service.ts\n+++ b/src/lib/services/metric/metric-value.service.ts\n@@ -110,8 +110,14 @@\n   async batchInsert(ctx: ServiceContext, values: MetricValueInput[]) {\n-    await Promise.all(\n-      values.map(v => this.prisma.metricValue.create({ data: v }))\n-    );\n+    // Process in sequential batches of 50 to avoid deadlocks\n+    const BATCH_SIZE = 50;\n+    for (let i = 0; i < values.length; i += BATCH_SIZE) {\n+      const batch = values.slice(i, i + BATCH_SIZE);\n+      await this.prisma.$transaction(\n+        batch.map(v => this.prisma.metricValue.create({ data: v })),\n+        { isolationLevel: 'Serializable' }\n+      );\n+    }",
        "explanation": "Replaced parallel Promise.all with sequential batched transactions using Serializable isolation to prevent deadlocks during concurrent metric value inserts.",
        "confidence": 0.94,
        "model_used": "claude-opus-4-20250514",
        "status": "approved",
    },
    {
        "error_index": 6,  # Session expired
        "diff": "--- a/src/lib/auth/session.ts\n+++ b/src/lib/auth/session.ts\n@@ -32,6 +32,12 @@\n   const token = request.headers.get('authorization')?.replace('Bearer ', '');\n-  const decoded = jwt.verify(token, process.env.NEXTAUTH_SECRET!);\n+  try {\n+    const decoded = jwt.verify(token, process.env.NEXTAUTH_SECRET!);\n+    return decoded;\n+  } catch (error) {\n+    if (error.name === 'TokenExpiredError') {\n+      // Attempt silent refresh using refresh token\n+      return await refreshSession(request);\n+    }\n+    throw new AuthError('Invalid session');\n+  }",
        "explanation": "Added automatic silent session refresh when JWT expires, instead of immediately failing. Uses the refresh token stored in the HTTP-only cookie.",
        "confidence": 0.89,
        "model_used": "claude-sonnet-4-20250514",
        "status": "deployed",
    },
    {
        "error_index": 7,  # OAuth callback
        "diff": "--- a/src/app/api/auth/[...nextauth]/route.ts\n+++ b/src/app/api/auth/[...nextauth]/route.ts\n@@ -43,7 +43,12 @@\n   callbacks: {\n     async signIn({ account }) {\n-      if (account?.state !== cookies.get('oauth_state')) throw new Error('State mismatch');\n+      const cookieState = cookies.get('oauth_state')?.value;\n+      const paramState = account?.state;\n+      if (!cookieState || !paramState || cookieState !== paramState) {\n+        logger.warn('OAuth state mismatch', { cookieState: !!cookieState, paramState: !!paramState });\n+        return '/auth/error?error=OAuthStateMismatch';\n+      }\n       return true;\n     },\n   }",
        "explanation": "Fixed OAuth state validation to properly extract cookie value and handle missing states gracefully. Now redirects to error page instead of throwing.",
        "confidence": 0.87,
        "model_used": "claude-opus-4-20250514",
        "status": "pending",
    },
    {
        "error_index": 8,  # Tenant isolation
        "diff": "--- a/src/lib/auth/tenant-guard.ts\n+++ b/src/lib/auth/tenant-guard.ts\n@@ -26,8 +26,15 @@\n   async validate(userId: string, resourceOrgId: string) {\n-    const user = await this.getUser(userId);\n-    if (user.orgId !== resourceOrgId) throw new TenantIsolationError(...);\n+    const user = await this.getUser(userId);\n+    if (user.orgId !== resourceOrgId) {\n+      // Log security event before throwing\n+      await this.auditService.logSecurityEvent({\n+        type: 'tenant_isolation_violation',\n+        userId,\n+        attemptedOrgId: resourceOrgId,\n+        actualOrgId: user.orgId,\n+        severity: 'critical',\n+      });\n+      throw new TenantIsolationError(`User ${userId} (org: ${user.orgId}) attempted access to org: ${resourceOrgId}`);\n+    }",
        "explanation": "Added security audit logging before throwing the tenant isolation error. This ensures cross-org access attempts are tracked for security review.",
        "confidence": 0.95,
        "model_used": "claude-opus-4-20250514",
        "status": "approved",
    },
    {
        "error_index": 10,  # Formula error
        "diff": "--- a/src/lib/services/metric/metric.service.ts\n+++ b/src/lib/services/metric/metric.service.ts\n@@ -243,7 +243,12 @@\n   async calculateFormula(ctx: ServiceContext, metricId: string) {\n-    const formula = await this.getFormula(ctx, metricId);\n-    return eval(formula.expression);\n+    const formula = await this.getFormula(ctx, metricId);\n+    try {\n+      const result = this.safeEvaluate(formula.expression, ctx);\n+      return result;\n+    } catch (error) {\n+      throw ServiceError.validation(`Invalid formula expression: ${formula.expression}`);\n+    }",
        "explanation": "The formula calculation was using unsafe eval() which throws on malformed expressions. Replaced with a safe evaluator that validates the expression first and throws a proper ServiceError on failure.",
        "confidence": 0.92,
        "model_used": "claude-opus-4-20250514",
        "status": "deployed",
    },
    {
        "error_index": 11,  # Zod validation
        "diff": "--- a/src/lib/schemas/metric.schema.ts\n+++ b/src/lib/schemas/metric.schema.ts\n@@ -32,7 +32,9 @@\n export const MetricSchema = z.object({\n   name: z.string().min(1).max(100),\n-  target: z.number(),\n+  target: z.union([\n+    z.number(),\n+    z.string().transform((val) => {\n+      const num = Number(val);\n+      if (isNaN(num)) throw new Error('target must be a valid number');\n+      return num;\n+    }),\n+  ]),\n   unit: z.string().optional(),\n });",
        "explanation": "Added a union type that accepts both numbers and numeric strings for the 'target' field, with automatic string-to-number coercion. This handles form submissions that send numbers as strings.",
        "confidence": 0.96,
        "model_used": "claude-sonnet-4-20250514",
        "status": "deployed",
    },
    {
        "error_index": 20,  # Slack notification
        "diff": "--- a/src/lib/services/notification/slack.service.ts\n+++ b/src/lib/services/notification/slack.service.ts\n@@ -54,7 +54,16 @@\n   async postMessage(channel: string, text: string) {\n-    const response = await this.client.chat.postMessage({ channel, text });\n+    try {\n+      const response = await this.client.chat.postMessage({ channel, text });\n+      return response;\n+    } catch (error) {\n+      if (error.data?.error === 'channel_not_found') {\n+        // Attempt to find channel by name lookup\n+        const channels = await this.client.conversations.list({ types: 'public_channel,private_channel' });\n+        const match = channels.channels?.find(c => c.name === channel.replace('#', ''));\n+        if (match) return await this.client.chat.postMessage({ channel: match.id, text });\n+      }\n+      throw error;\n+    }",
        "explanation": "Added fallback logic: when a channel name lookup fails, the service now queries the Slack API for a matching channel by name and retries with the channel ID.",
        "confidence": 0.85,
        "model_used": "claude-sonnet-4-20250514",
        "status": "pending",
    },
    {
        "error_index": 21,  # Circuit breaker
        "diff": "--- a/src/lib/ai-provider.ts\n+++ b/src/lib/ai-provider.ts\n@@ -87,8 +87,18 @@\n   async generate(prompt: string) {\n-    if (this.circuitBreaker.isOpen) throw new CircuitBreakerError('Circuit is open');\n+    if (this.circuitBreaker.isOpen) {\n+      // Check if half-open period has elapsed\n+      if (this.circuitBreaker.canRetry()) {\n+        this.circuitBreaker.halfOpen();\n+      } else {\n+        // Fallback to secondary provider\n+        return this.fallbackProvider.generate(prompt);\n+      }\n+    }\n+    try {\n+      const result = await this.primaryProvider.generate(prompt);\n+      this.circuitBreaker.success();\n+      return result;\n+    } catch (error) {\n+      this.circuitBreaker.failure();\n+      return this.fallbackProvider.generate(prompt);\n+    }",
        "explanation": "Implemented proper circuit breaker half-open state with automatic fallback to secondary AI provider instead of immediately throwing. The circuit resets after a configurable cooldown period.",
        "confidence": 0.90,
        "model_used": "claude-opus-4-20250514",
        "status": "approved",
    },
    {
        "error_index": 24,  # OOMKilled
        "diff": "--- a/docker/Dockerfile\n+++ b/docker/Dockerfile\n@@ -18,6 +18,8 @@\n-CMD [\"node\", \"server.js\"]\n+# Increase memory limit and add heap monitoring\n+ENV NODE_OPTIONS=\"--max-old-space-size=450 --expose-gc\"\n+HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:3000/api/v1/health || exit 1\n+CMD [\"node\", \"--max-old-space-size=450\", \"server.js\"]",
        "explanation": "Set explicit Node.js heap limit to 450MB (under the 512Mi container limit) to enable graceful GC instead of OOMKill. Added container healthcheck.",
        "confidence": 0.88,
        "model_used": "claude-opus-4-20250514",
        "status": "approved",
    },
    {
        "error_index": 25,  # Redis timeout
        "diff": "--- a/src/lib/queue/worker.ts\n+++ b/src/lib/queue/worker.ts\n@@ -26,7 +26,15 @@\n   constructor(queueName: string) {\n-    this.connection = new Redis(process.env.REDIS_URL);\n+    this.connection = new Redis(process.env.REDIS_URL, {\n+      maxRetriesPerRequest: 3,\n+      retryStrategy(times) {\n+        const delay = Math.min(times * 200, 5000);\n+        return delay;\n+      },\n+      reconnectOnError(err) {\n+        return err.message.includes('READONLY') || err.message.includes('ETIMEDOUT');\n+      },\n+      connectTimeout: 10000,\n+      lazyConnect: true,\n+    });",
        "explanation": "Added Redis connection resilience with exponential backoff retry strategy, automatic reconnection on timeout/readonly errors, and lazy connect to avoid blocking startup.",
        "confidence": 0.93,
        "model_used": "claude-opus-4-20250514",
        "status": "deployed",
    },
    {
        "error_index": 26,  # BullMQ worker crash
        "diff": "--- a/src/lib/queue/metrics-sync.worker.ts\n+++ b/src/lib/queue/metrics-sync.worker.ts\n@@ -54,7 +54,18 @@\n   async process(job: Job) {\n-    const result = await this.metricService.syncAll(job.data);\n-    return result;\n+    try {\n+      const result = await this.metricService.syncAll(job.data);\n+      return result;\n+    } catch (error) {\n+      // Categorize failure for retry strategy\n+      if (isTransientError(error)) {\n+        throw new UnrecoverableError(`Transient failure, will retry: ${error.message}`);\n+      }\n+      // Log permanent failures and move to dead letter queue\n+      logger.error('Permanent sync failure', { jobId: job.id, error });\n+      await this.deadLetterQueue.add('failed-sync', { ...job.data, error: error.message });\n+      return { status: 'failed', error: error.message };\n+    }",
        "explanation": "Added proper error classification in the worker: transient errors trigger automatic retries while permanent failures are routed to a dead letter queue for investigation.",
        "confidence": 0.87,
        "model_used": "claude-sonnet-4-20250514",
        "status": "pending",
    },
    {
        "error_index": 17,  # Google Sheets rate limit
        "diff": "--- a/src/lib/services/integration/google-sheets.service.ts\n+++ b/src/lib/services/integration/google-sheets.service.ts\n@@ -154,7 +154,16 @@\n   async syncData(sheetId: string) {\n-    const data = await this.sheetsApi.spreadsheets.values.get(...);\n+    // Implement exponential backoff with jitter for rate limits\n+    const data = await retry(\n+      () => this.sheetsApi.spreadsheets.values.get(...),\n+      {\n+        retries: 3,\n+        factor: 2,\n+        minTimeout: 1000,\n+        maxTimeout: 10000,\n+        randomize: true,\n+        onRetry: (err, attempt) => logger.warn(`Sheets API retry ${attempt}`, { err }),\n+      }\n+    );",
        "explanation": "Added exponential backoff with jitter for Google Sheets API calls to gracefully handle 429 rate limit responses instead of failing immediately.",
        "confidence": 0.91,
        "model_used": "claude-sonnet-4-20250514",
        "status": "deployed",
    },
    {
        "error_index": 4,  # Foreign key constraint
        "diff": "--- a/src/lib/services/user/user.service.ts\n+++ b/src/lib/services/user/user.service.ts\n@@ -40,7 +40,14 @@\n   async create(data: CreateUserInput) {\n-    return this.prisma.user.create({ data });\n+    // Verify organization exists before creating user\n+    const org = await this.prisma.organization.findUnique({\n+      where: { id: data.organizationId },\n+    });\n+    if (!org) {\n+      throw ServiceError.notFound(`Organization ${data.organizationId} not found`);\n+    }\n+    return this.prisma.user.create({ data });",
        "explanation": "Added explicit organization existence check before user creation to provide a clear error message instead of a cryptic foreign key constraint violation.",
        "confidence": 0.93,
        "model_used": "claude-sonnet-4-20250514",
        "status": "pending",
    },
]

# ─── Demo feature requests ───────────────────────────────────────────────────

DEMO_FEATURES: list[dict] = [
    {
        "title": "Add CSV export for scorecard metrics",
        "description": "Users should be able to export all metrics for a scorecard as a CSV file, including historical values and trend data.",
        "priority": "medium",
        "status": "generated",
        "explanation": "Implementation adds a new API endpoint GET /api/v1/scorecards/:id/export/csv and a download button in the scorecard detail view. Uses the 'fast-csv' library for streaming CSV generation.",
        "generated_diff": "--- /dev/null\n+++ b/src/app/api/v1/scorecards/[id]/export/csv/route.ts\n+import { NextResponse } from 'next/server';\n+import { stringify } from 'csv-stringify/sync';\n+...",
    },
    {
        "title": "Slack notification on metric threshold breach",
        "description": "When a metric value crosses a defined threshold, automatically send a Slack notification to the configured channel.",
        "priority": "high",
        "status": "submitted",
        "explanation": None,
        "generated_diff": None,
    },
    {
        "title": "Implement scorecard comparison view",
        "description": "Allow users to compare two scorecards side by side, showing metric deltas and trend differences across time periods.",
        "priority": "medium",
        "status": "generated",
        "explanation": "New ComparisonView component using a split-pane layout. API endpoint returns normalized metric data for two scorecards with calculated deltas.",
        "generated_diff": "--- /dev/null\n+++ b/src/components/comparison/comparison-view.tsx\n+import { useScorecardComparison } from '@/hooks/use-scorecard-comparison';\n+...",
    },
    {
        "title": "AI-powered anomaly detection for metric values",
        "description": "Automatically detect anomalous metric values using statistical methods and flag them for review. Should support z-score, IQR, and isolation forest methods.",
        "priority": "high",
        "status": "generating",
        "explanation": None,
        "generated_diff": None,
    },
    {
        "title": "Multi-language support (i18n) for the dashboard",
        "description": "Add internationalization support starting with English, Japanese, and Spanish. Use next-intl for type-safe translations.",
        "priority": "low",
        "status": "submitted",
        "explanation": None,
        "generated_diff": None,
    },
]

# ─── Audit log action templates ──────────────────────────────────────────────

AUDIT_ACTIONS: list[dict] = [
    {"action": "error_detected", "entity_type": "error", "actor": "watch_module"},
    {"action": "error_classified", "entity_type": "error", "actor": "think_module"},
    {"action": "fix_generated", "entity_type": "fix", "actor": "heal_module"},
    {"action": "fix_approved", "entity_type": "fix", "actor": "admin"},
    {"action": "fix_rejected", "entity_type": "fix", "actor": "admin"},
    {"action": "fix_deployed", "entity_type": "deployment", "actor": "verify_module"},
    {"action": "deployment_created", "entity_type": "deployment", "actor": "heal_module"},
    {"action": "deployment_succeeded", "entity_type": "deployment", "actor": "verify_module"},
    {"action": "deployment_failed", "entity_type": "deployment", "actor": "verify_module"},
    {"action": "feature_submitted", "entity_type": "feature", "actor": "admin"},
    {"action": "feature_generated", "entity_type": "feature", "actor": "evolve_module"},
    {"action": "config_updated", "entity_type": "config", "actor": "admin"},
    {"action": "system_health_check", "entity_type": "system", "actor": "sentinel"},
    {"action": "log_batch_ingested", "entity_type": "log", "actor": "watch_module"},
]


# ─── Seeder ──────────────────────────────────────────────────────────────────

async def seed(clear: bool = False) -> None:
    """Populate the database with demo data."""
    await init_db()
    db = await get_db()
    try:
        if clear:
            print("[seed] Clearing existing data...")
            for table in ("audit_log", "deployments", "fixes", "errors", "feature_requests"):
                await db.execute(f"DELETE FROM {table}")
            await db.commit()
            print("[seed] Tables cleared.")

        # ── 1. Insert errors ──────────────────────────────────────────────
        error_ids: list[str] = []
        for i, err in enumerate(DEMO_ERRORS):
            eid = _uid()
            error_ids.append(eid)
            # Spread timestamps across the last 48 hours
            created = _rand_hours_ago(1, 47)
            await db.execute(
                """INSERT INTO errors
                   (id, source, environment, raw_log, error_message, error_type,
                    stack_trace, severity, category, affected_file, fingerprint,
                    occurrence_count, first_seen, last_seen, status, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    eid,
                    "nextjs-app",
                    random.choice(["production", "staging", "production", "production"]),
                    err.get("stack_trace", err["error_message"]),
                    err["error_message"],
                    err["error_type"],
                    err.get("stack_trace"),
                    err["severity"],
                    err["category"],
                    err.get("affected_file"),
                    _uid()[:32],  # fake fingerprint
                    random.randint(1, 25),
                    created,
                    _rand_hours_ago(0, 2),
                    err["status"],
                    created,
                    _rand_hours_ago(0, 5),
                ),
            )
        await db.commit()
        print(f"[seed] Inserted {len(error_ids)} errors.")

        # ── 2. Insert fixes ───────────────────────────────────────────────
        fix_ids: list[str] = []
        fix_error_map: dict[str, str] = {}  # fix_id -> error_id
        for fix in DEMO_FIXES:
            fid = _uid()
            fix_ids.append(fid)
            error_idx = fix["error_index"]
            error_id = error_ids[error_idx]
            fix_error_map[fid] = error_id

            created = _rand_hours_ago(0.5, 40)
            files_changed = [DEMO_ERRORS[error_idx].get("affected_file", "unknown")]

            await db.execute(
                """INSERT INTO fixes
                   (id, error_id, diff, explanation, files_changed, confidence,
                    model_used, prompt_tokens, completion_tokens, status,
                    reviewer_notes, attempt_number, guidance, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    fid,
                    error_id,
                    fix["diff"],
                    fix["explanation"],
                    json.dumps(files_changed),
                    fix["confidence"],
                    fix["model_used"],
                    random.randint(1200, 4500),
                    random.randint(400, 2000),
                    fix["status"],
                    "Looks good" if fix["status"] in ("approved", "deployed") else None,
                    1,
                    None,
                    created,
                    _rand_hours_ago(0, 6) if fix["status"] in ("deployed", "approved") else created,
                ),
            )
        await db.commit()
        print(f"[seed] Inserted {len(fix_ids)} fixes.")

        # ── 3. Insert deployments ─────────────────────────────────────────
        deployment_ids: list[str] = []
        deployed_fixes = [fid for fid, _ in zip(fix_ids, DEMO_FIXES) if DEMO_FIXES[fix_ids.index(fid)]["status"] == "deployed"]
        # Also add a couple extra deployments for approved fixes
        for fid in fix_ids:
            idx = fix_ids.index(fid)
            fix_status = DEMO_FIXES[idx]["status"]
            if fix_status not in ("deployed", "approved"):
                continue
            did = _uid()
            deployment_ids.append(did)
            deploy_status = "success" if fix_status == "deployed" else "pending"
            created = _rand_hours_ago(0, 20)
            pr_number = random.randint(100, 350)
            await db.execute(
                """INSERT INTO deployments
                   (id, fix_id, environment, status, test_results, pr_url,
                    commit_sha, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (
                    did,
                    fid,
                    random.choice(["production", "staging"]),
                    deploy_status,
                    json.dumps([
                        {"name": "unit-tests", "status": "passed", "duration_ms": random.randint(8000, 25000)},
                        {"name": "integration-tests", "status": "passed", "duration_ms": random.randint(15000, 45000)},
                        {"name": "e2e-tests", "status": "passed" if deploy_status == "success" else "running", "duration_ms": random.randint(30000, 90000)},
                    ]),
                    f"https://github.com/koshaji/metrics/pull/{pr_number}",
                    f"{_uid()[:7]}",
                    created,
                    _rand_hours_ago(0, 3) if deploy_status == "success" else created,
                ),
            )
        await db.commit()
        print(f"[seed] Inserted {len(deployment_ids)} deployments.")

        # ── 4. Insert feature requests ────────────────────────────────────
        feature_ids: list[str] = []
        for feat in DEMO_FEATURES:
            frid = _uid()
            feature_ids.append(frid)
            created = _rand_hours_ago(2, 46)
            await db.execute(
                """INSERT INTO feature_requests
                   (id, title, description, priority, generated_code, generated_diff,
                    explanation, model_used, status, reviewer_notes, pr_url,
                    created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    frid,
                    feat["title"],
                    feat["description"],
                    feat["priority"],
                    json.dumps({}),
                    feat.get("generated_diff"),
                    feat.get("explanation"),
                    "claude-opus-4-20250514" if feat.get("explanation") else None,
                    feat["status"],
                    None,
                    None,
                    created,
                    _rand_hours_ago(0, 10),
                ),
            )
        await db.commit()
        print(f"[seed] Inserted {len(feature_ids)} feature requests.")

        # ── 5. Insert audit log entries ───────────────────────────────────
        all_entity_ids = error_ids + fix_ids + deployment_ids + feature_ids
        audit_count = 0
        # Create structured audit trail for each error
        for i, eid in enumerate(error_ids):
            ts = _rand_hours_ago(2, 47)
            await db.execute(
                "INSERT INTO audit_log (id, action, entity_type, entity_id, details, actor, created_at) VALUES (?,?,?,?,?,?,?)",
                (_uid(), "error_detected", "error", eid,
                 json.dumps({"source": "nextjs-app", "severity": DEMO_ERRORS[i]["severity"]}),
                 "watch_module", ts),
            )
            audit_count += 1

            # Classified
            if DEMO_ERRORS[i]["status"] not in ("new",):
                await db.execute(
                    "INSERT INTO audit_log (id, action, entity_type, entity_id, details, actor, created_at) VALUES (?,?,?,?,?,?,?)",
                    (_uid(), "error_classified", "error", eid,
                     json.dumps({"category": DEMO_ERRORS[i]["category"], "severity": DEMO_ERRORS[i]["severity"]}),
                     "think_module", _rand_hours_ago(1, 40)),
                )
                audit_count += 1

        # Fix-related audit entries
        for i, fid in enumerate(fix_ids):
            await db.execute(
                "INSERT INTO audit_log (id, action, entity_type, entity_id, details, actor, created_at) VALUES (?,?,?,?,?,?,?)",
                (_uid(), "fix_generated", "fix", fid,
                 json.dumps({"model": DEMO_FIXES[i]["model_used"], "confidence": DEMO_FIXES[i]["confidence"]}),
                 "heal_module", _rand_hours_ago(1, 38)),
            )
            audit_count += 1

            if DEMO_FIXES[i]["status"] in ("approved", "deployed"):
                await db.execute(
                    "INSERT INTO audit_log (id, action, entity_type, entity_id, details, actor, created_at) VALUES (?,?,?,?,?,?,?)",
                    (_uid(), "fix_approved", "fix", fid,
                     json.dumps({"reviewer": "admin"}),
                     "admin", _rand_hours_ago(0.5, 30)),
                )
                audit_count += 1

            if DEMO_FIXES[i]["status"] == "deployed":
                await db.execute(
                    "INSERT INTO audit_log (id, action, entity_type, entity_id, details, actor, created_at) VALUES (?,?,?,?,?,?,?)",
                    (_uid(), "fix_deployed", "deployment", fid,
                     json.dumps({"environment": "production"}),
                     "verify_module", _rand_hours_ago(0.2, 20)),
                )
                audit_count += 1

        # Feature audit entries
        for i, frid in enumerate(feature_ids):
            await db.execute(
                "INSERT INTO audit_log (id, action, entity_type, entity_id, details, actor, created_at) VALUES (?,?,?,?,?,?,?)",
                (_uid(), "feature_submitted", "feature", frid,
                 json.dumps({"title": DEMO_FEATURES[i]["title"], "priority": DEMO_FEATURES[i]["priority"]}),
                 "admin", _rand_hours_ago(2, 45)),
            )
            audit_count += 1

        # System health / config audit entries
        for j in range(8):
            await db.execute(
                "INSERT INTO audit_log (id, action, entity_type, entity_id, details, actor, created_at) VALUES (?,?,?,?,?,?,?)",
                (_uid(), "system_health_check", "system", None,
                 json.dumps({"status": "healthy", "uptime_seconds": random.randint(3600, 172800)}),
                 "sentinel", _rand_hours_ago(j * 6, j * 6 + 1)),
            )
            audit_count += 1

        for key, val in [
            ("auto_fix_enabled", True),
            ("min_confidence_threshold", 0.75),
            ("model_preference", "claude-opus-4-20250514"),
        ]:
            await db.execute(
                "INSERT INTO audit_log (id, action, entity_type, entity_id, details, actor, created_at) VALUES (?,?,?,?,?,?,?)",
                (_uid(), "config_updated", "config", key,
                 json.dumps({"key": key, "new_value": val}),
                 "admin", _rand_hours_ago(10, 46)),
            )
            audit_count += 1

        await db.commit()
        print(f"[seed] Inserted {audit_count} audit log entries.")

        # ── Summary ───────────────────────────────────────────────────────
        print("\n[seed] Demo data seeding complete!")
        print(f"  Errors:           {len(error_ids)}")
        print(f"  Fixes:            {len(fix_ids)}")
        print(f"  Deployments:      {len(deployment_ids)}")
        print(f"  Feature requests: {len(feature_ids)}")
        print(f"  Audit log:        {audit_count}")

    finally:
        await db.close()


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Seed Sentinel DB with demo data")
    parser.add_argument("--clear", action="store_true", help="Clear existing data before seeding")
    args = parser.parse_args()
    asyncio.run(seed(clear=args.clear))


if __name__ == "__main__":
    main()
