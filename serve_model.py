"""CML Model endpoint — Real-time error classification and severity scoring.

Deployed as a CML Model, this exposes Sentinel's Think module as a REST API.
External systems can POST an error and get classification + severity + recommended action.

Example request:
{
    "error_message": "TypeError: Cannot read properties of undefined (reading 'id')",
    "error_type": "TypeError",
    "stack_trace": "at getUser (auth.ts:42:15)"
}

Example response:
{
    "category": "auth",
    "severity": "high",
    "pattern": "null_reference",
    "recommended_action": "Add null check before accessing property",
    "confidence": 0.85
}
"""
import os
import sys

try:
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
except NameError:
    PROJECT_ROOT = os.getcwd()
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

# Classification patterns (from Think module)
CATEGORY_PATTERNS = {
    "database": ["prisma", "database", "sql", "query", "migration", "schema", "connection", "pool", "transaction", "deadlock"],
    "auth": ["auth", "token", "session", "permission", "unauthorized", "forbidden", "jwt", "oauth", "credentials", "login"],
    "api": ["api", "endpoint", "request", "response", "http", "rest", "graphql", "timeout", "rate limit", "cors"],
    "ui": ["render", "component", "react", "dom", "css", "layout", "hydration", "client", "browser", "window"],
    "integration": ["webhook", "third-party", "external", "service", "integration", "smtp", "redis", "queue"],
    "ai": ["openai", "anthropic", "claude", "model", "inference", "embedding", "token limit", "ai", "llm"],
    "infrastructure": ["memory", "cpu", "disk", "network", "container", "docker", "deploy", "env", "config", "port"],
}

SEVERITY_KEYWORDS = {
    "critical": ["crash", "data loss", "security", "injection", "breach", "down", "outage", "corrupt", "fatal"],
    "high": ["error", "fail", "broken", "unauthorized", "timeout", "leak", "race condition", "deadlock"],
    "medium": ["warning", "deprecated", "slow", "retry", "fallback", "missing"],
    "low": ["info", "minor", "cosmetic", "typo", "style", "lint"],
}

ERROR_PATTERNS = {
    "null_reference": ["cannot read prop", "undefined", "null", "is not a function", "typeerror"],
    "connection_failure": ["econnrefused", "econnreset", "timeout", "connection", "network"],
    "validation_error": ["validation", "invalid", "required", "constraint", "schema"],
    "resource_exhaustion": ["memory", "heap", "stack overflow", "too many", "limit", "quota"],
    "concurrency_issue": ["deadlock", "race condition", "lock", "concurrent", "conflict"],
    "configuration_error": ["env", "config", "missing", "not found", "undefined variable"],
}


def classify_category(text: str) -> str:
    text_lower = text.lower()
    scores = {}
    for category, keywords in CATEGORY_PATTERNS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[category] = score
    if scores:
        return max(scores, key=scores.get)
    return "unknown"


def classify_severity(text: str, category: str, occurrence_count: int = 1) -> str:
    text_lower = text.lower()
    for severity, keywords in SEVERITY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return severity
    if category in ("auth", "database"):
        return "high"
    return "medium"


def detect_pattern(text: str) -> str:
    text_lower = text.lower()
    for pattern, keywords in ERROR_PATTERNS.items():
        if any(kw in text_lower for kw in keywords):
            return pattern
    return "unknown"


def predict(args):
    """CML Model predict function — classifies errors in real-time.

    This is the function deployed as a CML Model endpoint.
    Cloudera AI serves this as a REST API automatically.
    """
    error_message = args.get("error_message", "")
    error_type = args.get("error_type", "")
    stack_trace = args.get("stack_trace", "")

    combined_text = f"{error_message} {error_type} {stack_trace}"

    category = classify_category(combined_text)
    severity = classify_severity(combined_text, category)
    pattern = detect_pattern(combined_text)

    # Determine recommended action based on pattern
    actions = {
        "null_reference": "Add null/undefined checks before property access",
        "connection_failure": "Implement retry logic with exponential backoff",
        "validation_error": "Add input validation at the boundary layer",
        "resource_exhaustion": "Review resource allocation and implement limits",
        "concurrency_issue": "Add proper locking or use optimistic concurrency",
        "configuration_error": "Verify environment variables and config files",
        "unknown": "Manual investigation recommended",
    }

    # Confidence based on how many signals matched
    signals = sum([
        category != "unknown",
        severity != "medium",
        pattern != "unknown",
        len(error_message) > 20,
        bool(stack_trace),
    ])
    confidence = round(min(0.5 + (signals * 0.1), 0.95), 2)

    return {
        "category": category,
        "severity": severity,
        "pattern": pattern,
        "recommended_action": actions.get(pattern, actions["unknown"]),
        "confidence": confidence,
        "error_type": error_type or "Unknown",
    }
