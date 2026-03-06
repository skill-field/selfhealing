"""Pydantic models for Skillfield Sentinel API request/response schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Union, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import uuid4


# ─── Log Ingestion ───────────────────────────────────────────────────────────

class LogEntry(BaseModel):
    """A single log entry for ingestion."""
    source: str = Field(..., description="Source of the log (e.g., 'nextjs', 'vercel', 'docker')")
    environment: str = Field(default="production", description="Environment (production, staging, development)")
    raw_log: str = Field(..., description="Raw log text")
    error_message: Optional[str] = Field(default=None, description="Extracted error message")
    error_type: Optional[str] = Field(default=None, description="Error type/class")
    stack_trace: Optional[str] = Field(default=None, description="Stack trace if available")
    severity: Optional[str] = Field(default=None, description="Severity: critical, high, medium, low")
    timestamp: Optional[str] = Field(default=None, description="Original log timestamp")


class LogBatchRequest(BaseModel):
    """Batch of log entries for ingestion."""
    entries: list[LogEntry] = Field(..., min_length=1, max_length=100)


# ─── Errors ──────────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    """Response schema for a single error."""
    id: str
    source: Optional[str] = None
    environment: Optional[str] = None
    raw_log: Optional[str] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    stack_trace: Optional[str] = None
    severity: Optional[str] = None
    category: Optional[str] = None
    root_cause: Optional[str] = None
    affected_file: Optional[str] = None
    affected_files: list[str] = Field(default_factory=list)
    fingerprint: Optional[str] = None
    occurrence_count: int = 1
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    status: str = "new"
    created_at: str
    updated_at: str


class ErrorListResponse(BaseModel):
    """Paginated list of errors."""
    errors: list[ErrorResponse] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20


class ErrorStats(BaseModel):
    """Error statistics for the dashboard."""
    total_errors: int = 0
    by_severity: dict[str, int] = Field(default_factory=dict)
    by_category: dict[str, int] = Field(default_factory=dict)
    by_status: dict[str, int] = Field(default_factory=dict)
    new_last_24h: int = 0
    resolved_last_24h: int = 0


# ─── Fixes ───────────────────────────────────────────────────────────────────

class FixGenerateRequest(BaseModel):
    """Request to generate a fix for an error."""
    guidance: Optional[str] = Field(default=None, description="Optional human guidance for fix generation")
    model: Optional[str] = Field(default=None, description="Override model to use")


class FixApproveRequest(BaseModel):
    """Request to approve a fix."""
    reviewer_notes: Optional[str] = Field(default=None, description="Optional reviewer notes")


class FixRejectRequest(BaseModel):
    """Request to reject a fix."""
    reason: str = Field(..., min_length=1, description="Reason for rejection")


class FixResponse(BaseModel):
    """Response schema for a single fix."""
    id: str
    error_id: str
    diff: Optional[str] = None
    explanation: Optional[str] = None
    files_changed: list[str] = Field(default_factory=list)
    confidence: Optional[float] = None
    model_used: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    status: str = "pending"
    reviewer_notes: Optional[str] = None
    attempt_number: int = 1
    guidance: Optional[str] = None
    created_at: str
    updated_at: str


class FixListResponse(BaseModel):
    """Paginated list of fixes."""
    fixes: list[FixResponse] = Field(default_factory=list)
    total: int = 0


# ─── Deployments ─────────────────────────────────────────────────────────────

class DeploymentResponse(BaseModel):
    """Response schema for a deployment."""
    id: str
    fix_id: str
    environment: Optional[str] = None
    status: Optional[str] = None
    test_results: list[dict] = Field(default_factory=list)
    pr_url: Optional[str] = None
    commit_sha: Optional[str] = None
    created_at: str
    updated_at: str


class DeploymentListResponse(BaseModel):
    """Paginated list of deployments."""
    deployments: list[DeploymentResponse] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20


# ─── Feature Requests ────────────────────────────────────────────────────────

class FeatureSubmitRequest(BaseModel):
    """Request to submit a new feature (alias)."""
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10)
    priority: Optional[str] = Field(default="medium", description="Priority: low, medium, high, critical")


class FeatureRequest(BaseModel):
    """Request to create a new feature."""
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10)
    priority: Optional[str] = Field(default="medium", description="Priority: low, medium, high, critical")


class FeatureApproveRequest(BaseModel):
    """Request to approve a feature."""
    reviewer_notes: Optional[str] = Field(default=None, description="Optional reviewer notes")


class FeatureRejectRequest(BaseModel):
    """Request to reject a feature."""
    reviewer_notes: str = Field(..., min_length=1, description="Reason for rejection")


class FeatureResponse(BaseModel):
    """Response schema for a feature request."""
    id: str
    title: str
    description: Optional[str] = None
    priority: Optional[str] = None
    generated_code: Optional[dict] = None
    generated_diff: Optional[str] = None
    explanation: Optional[str] = None
    model_used: Optional[str] = None
    status: str = "submitted"
    reviewer_notes: Optional[str] = None
    pr_url: Optional[str] = None
    created_at: str
    updated_at: str


# ─── Audit Log ───────────────────────────────────────────────────────────────

class AuditLogEntry(BaseModel):
    """A single audit log entry."""
    id: str
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    details: Optional[dict] = None
    actor: Optional[str] = None
    created_at: str


# ─── Dashboard ───────────────────────────────────────────────────────────────

class DashboardSummary(BaseModel):
    """Summary data for the main dashboard."""
    total_errors: int = 0
    open_errors: int = 0
    fixes_generated: int = 0
    fixes_deployed: int = 0
    features_submitted: int = 0
    success_rate: float = 0.0
    error_stats: ErrorStats = Field(default_factory=ErrorStats)
    recent_errors: list[ErrorResponse] = Field(default_factory=list)
    recent_fixes: list[FixResponse] = Field(default_factory=list)
    # Extended summary fields
    errors_by_severity: dict[str, int] = Field(default_factory=dict)
    errors_by_category: dict[str, int] = Field(default_factory=dict)
    errors_by_status: dict[str, int] = Field(default_factory=dict)
    total_fixes: int = 0
    fixes_by_status: dict[str, int] = Field(default_factory=dict)
    total_deployments: int = 0
    total_features: int = 0
    mttr_minutes: float = 0.0
    system_health: dict[str, str] = Field(default_factory=dict)


# ─── System Config ───────────────────────────────────────────────────────────

class SystemConfig(BaseModel):
    """System configuration key-value pair."""
    key: str
    value: Optional[Union[str, int, float, bool, list, dict]] = None
    description: Optional[str] = None
    updated_at: Optional[str] = None
