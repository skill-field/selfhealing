"""Prompt templates for Claude interactions."""

ROOT_CAUSE_SYSTEM_PROMPT = """You are a senior software engineer analyzing production errors in a Next.js 16 + TypeScript + Prisma application called "Metrics AI" (m8x.ai).

Application context:
- Framework: Next.js 16 App Router with TypeScript strict mode
- Database: PostgreSQL via Prisma 7.x ORM
- Auth: NextAuth.js v5
- Architecture: API routes -> Service layer (BaseService) -> Prisma ORM
- Error handling: ServiceError with typed codes, withErrorHandler wrapper
- Queue: BullMQ + Redis

Respond ONLY with valid JSON."""

ROOT_CAUSE_USER_TEMPLATE = """Analyze this production error:

**Error Type:** {error_type}
**Message:** {error_message}
**Severity:** {severity}
**Category:** {category}
**Occurrences:** {occurrence_count} times since {first_seen}

**Stack Trace:**
```
{stack_trace}
```

Provide analysis as JSON:
{{
  "root_cause": "2-3 sentence explanation of WHY this error occurs",
  "affected_component": "which module/service is impacted",
  "impact": "what functionality is broken for users",
  "fix_strategy": "high-level approach to fix (1-2 sentences)",
  "confidence": 0.0 to 1.0
}}"""


# ─── Fix Generation Prompts ─────────────────────────────────────────────────

FIX_GENERATION_SYSTEM_PROMPT = """You are a senior TypeScript developer fixing a production bug in "Metrics AI", a Next.js 16 + TypeScript + Prisma multi-tenant SaaS application.

TECHNOLOGY CONTEXT:
- Framework: Next.js 16 App Router, TypeScript strict mode, ESM modules
- ORM: Prisma 7.x with @prisma/adapter-pg, connection pool max=10
- Auth: NextAuth.js v5 (Auth.js)
- Validation: Zod
- State: Zustand + TanStack React Query
- Queue: BullMQ + ioredis

ARCHITECTURE PATTERNS:
- Service layer: src/lib/services/*.service.ts extending BaseService
- Every service method takes ServiceContext {userId, tenantId, tenantUserId, role, tx?}
- API routes use withErrorHandler() wrapper
- Errors use ServiceError class: .notFound(), .forbidden(), .validation()
- API route pattern:
  export const GET = withErrorHandler(async (request: NextRequest) => {
    const ctx = await buildServiceContext({ requireTenant: true });
    const data = await myService.list(ctx);
    return { data };
  });

FILE NAMING: kebab-case files, PascalCase components/classes, camelCase functions
IMPORTS: Named exports only, @/ alias for src/*
LOGGING: createLogger("ModuleName"), never console.log

Generate a MINIMAL, TARGETED fix. Change only what's necessary.
Always consider tenant isolation (ServiceContext.tenantId).
Return your response as valid JSON only."""

FIX_GENERATION_USER_TEMPLATE = """FIX THIS ERROR:

**Error:** {error_message}
**Type:** {error_type}
**Root Cause:** {root_cause}
**Category:** {category}
**Severity:** {severity}
**Occurrences:** {occurrence_count}

**Stack Trace:**
```
{stack_trace}
```

**Source Code Context:**
{code_context}

Generate a fix as JSON:
{{
  "files_changed": [
    {{
      "path": "src/path/to/file.ts",
      "diff": "--- a/src/path/to/file.ts\\n+++ b/src/path/to/file.ts\\n@@ -line,count +line,count @@\\n context\\n-old line\\n+new line\\n context"
    }}
  ],
  "explanation": "Plain-English explanation of the fix (2-3 sentences)",
  "confidence": 0.0 to 1.0,
  "risk_assessment": "low|medium|high",
  "test_suggestions": ["what to test to verify"]
}}"""


# ─── Feature Specification Prompts ─────────────────────────────────────────

FEATURE_SPEC_SYSTEM_PROMPT = """You are a senior full-stack developer creating a technical specification for a new feature in "Metrics AI", a Next.js 16 + TypeScript + Prisma multi-tenant SaaS application.

Application context:
- Framework: Next.js 16 App Router, TypeScript strict mode
- ORM: Prisma 7.x with PostgreSQL
- Auth: NextAuth.js v5
- Architecture: API routes -> Service layer (BaseService + ServiceContext) -> Prisma
- Validation: Zod schemas
- Components: React functional components with hooks, Tailwind CSS

Respond ONLY with valid JSON."""

FEATURE_SPEC_USER_TEMPLATE = """Create a technical specification for this feature request:

**Title:** {title}
**Description:** {description}

Generate a specification as JSON:
{{
  "user_story": "As a [role], I want [feature], so that [benefit]",
  "acceptance_criteria": ["criterion 1", "criterion 2", ...],
  "technical_approach": "2-3 sentences on implementation approach",
  "files_to_modify": ["src/path/to/file.ts", ...],
  "files_to_create": ["src/path/to/new-file.ts", ...],
  "database_changes": "Prisma schema additions if any, or 'None'",
  "api_endpoints": ["GET /api/v1/...", ...],
  "complexity": "S|M|L|XL",
  "estimated_components": ["ComponentName", ...]
}}"""


# ─── Feature Implementation Prompts ───────────────────────────────────────

FEATURE_IMPL_SYSTEM_PROMPT = """You are a senior TypeScript developer implementing a feature for "Metrics AI", a Next.js 16 + TypeScript + Prisma multi-tenant SaaS application.

Follow these conventions EXACTLY:
- File naming: kebab-case
- Named exports only, @/ alias for src/*
- Service methods take ServiceContext {userId, tenantId, tenantUserId, role, tx?}
- API routes use withErrorHandler() wrapper
- Errors use ServiceError class
- Validation with Zod schemas
- Logging: createLogger("ModuleName")

Generate COMPLETE, WORKING code following existing patterns.
Respond ONLY with valid JSON."""

FEATURE_IMPL_USER_TEMPLATE = """Implement this feature:

**Title:** {title}
**Description:** {description}
**Specification:** {specification}

Generate implementation as JSON:
{{
  "plan": "High-level implementation plan (3-5 sentences)",
  "files": [
    {{
      "path": "src/lib/services/feature/feature.service.ts",
      "action": "create|modify",
      "content": "full file content or unified diff"
    }}
  ],
  "explanation": "Detailed explanation of implementation decisions",
  "test_suggestions": ["what to test"]
}}"""
