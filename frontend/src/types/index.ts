export type Severity = 'critical' | 'high' | 'medium' | 'low';
export type FixStatus = 'pending' | 'approved' | 'rejected' | 'deployed' | 'failed';
export type DeploymentStatus = 'pending' | 'deploying' | 'deployed' | 'testing' | 'tests_passed' | 'promoted' | 'rolled_back' | 'failed';
export type FeatureStatus = 'submitted' | 'generating' | 'generated' | 'approved' | 'rejected' | 'deployed';
export type ErrorStatus = 'new' | 'acknowledged' | 'fix_generated' | 'resolved' | 'ignored';
export type ErrorCategory = 'database' | 'auth' | 'api' | 'integration' | 'ai' | 'infrastructure' | 'unknown';

export interface LogEntry {
  id: string;
  timestamp: string;
  level: string;
  message: string;
  source: string;
  environment?: string;
  metadata?: Record<string, unknown>;
  context?: Record<string, unknown>;
}

export interface Error {
  id: string;
  source?: string;
  environment?: string;
  raw_log?: string;
  error_message?: string;
  error_type?: string;
  stack_trace?: string;
  severity?: string;
  category?: string;
  root_cause?: string;
  affected_file?: string;
  affected_files?: string[];
  fingerprint?: string;
  occurrence_count: number;
  first_seen?: string;
  last_seen?: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ErrorStats {
  total_errors: number;
  by_severity: Record<string, number>;
  by_category: Record<string, number>;
  by_status: Record<string, number>;
  new_last_24h: number;
  resolved_last_24h: number;
}

export interface Fix {
  id: string;
  error_id: string;
  diff: string;
  explanation: string;
  files_changed: string | string[] | null;
  confidence: number | null;
  model_used: string;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  status: FixStatus;
  reviewer_notes: string | null;
  attempt_number: number;
  guidance: string | null;
  created_at: string;
  updated_at: string;
}

export interface Deployment {
  id: string;
  fix_id: string;
  environment: string;
  status: string;
  test_results: Array<{ name: string; status: string; duration_ms: number }> | null;
  pr_url: string | null;
  commit_sha: string | null;
  created_at: string;
  updated_at: string;
}

export interface FeatureRequest {
  id: string;
  title: string;
  description: string;
  priority: string;
  generated_code: Record<string, unknown> | string | null;
  generated_diff: string | null;
  explanation: string | null;
  model_used: string | null;
  status: string;
  reviewer_notes: string | null;
  pr_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface AuditEntry {
  id: string;
  action: string;
  entity_type?: string;
  entity_id?: string;
  details: Record<string, unknown> | string;
  actor?: string;
  created_at: string;
}

export interface DashboardSummary {
  total_errors: number;
  open_errors: number;
  fixes_generated: number;
  fixes_deployed: number;
  features_submitted: number;
  success_rate: number;
  error_stats: ErrorStats;
  recent_errors: Error[];
  recent_fixes: Fix[];
  errors_by_severity: Record<string, number>;
  errors_by_category: Record<string, number>;
  errors_by_status: Record<string, number>;
  total_fixes: number;
  fixes_by_status: Record<string, number>;
  total_deployments: number;
  total_features: number;
  mttr_minutes: number;
  system_health: Record<string, string>;
}

export interface TimelineEntry {
  hour: string;
  errors: number;
  fixes: number;
  deployments: number;
}

export interface DashboardTimeline {
  timeline: TimelineEntry[];
  hours: number;
}

export interface SystemConfig {
  watch_enabled: boolean;
  think_enabled: boolean;
  heal_enabled: boolean;
  verify_enabled: boolean;
  evolve_enabled: boolean;
  auto_deploy: boolean;
}

export interface SSEEvent {
  type: string;
  data: unknown;
  timestamp: string;
}
