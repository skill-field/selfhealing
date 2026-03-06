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
  // Legacy fields for compatibility
  timestamp?: string;
  message?: string;
  classification?: string;
  occurrences?: number;
}

export interface ErrorStats {
  total_errors: number;
  by_severity: Record<string, number>;
  by_category: Record<string, number>;
  by_status: Record<string, number>;
  new_last_24h: number;
  resolved_last_24h: number;
  // Legacy fields
  total?: number;
  by_source?: Record<string, number>;
  trend?: Array<{ date: string; count: number }>;
}

export interface Fix {
  id: string;
  error_id: string;
  diff: string;
  explanation: string;
  files_changed: string | null;
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
  // Legacy fields for compatibility
  timestamp?: string;
  description?: string;
  code_diff?: string;
  approved_by?: string;
  deployed_at?: string;
}

export interface Deployment {
  id: string;
  fix_id: string;
  environment: string;
  status: string;
  test_results: string | null;
  pr_url: string | null;
  commit_sha: string | null;
  created_at: string;
  updated_at: string;
  // Legacy fields for compatibility
  timestamp?: string;
  promoted_at?: string;
  rolled_back_at?: string;
}

export interface FeatureRequest {
  id: string;
  title: string;
  description: string;
  priority: string;
  generated_code: string | null;
  generated_diff: string | null;
  explanation: string | null;
  model_used: string | null;
  status: string;
  reviewer_notes: string | null;
  pr_url: string | null;
  created_at: string;
  updated_at: string;
  // Legacy fields for compatibility
  timestamp?: string;
  generated_spec?: string;
  approved_by?: string;
}

export interface AuditEntry {
  id: string;
  timestamp: string;
  module: string;
  action: string;
  details: string;
  actor: string;
}

export interface DashboardSummary {
  total_errors: number;
  fixes_generated: number;
  fixes_deployed: number;
  success_rate: number;
  module_status: Record<string, string>;
  recent_activity: AuditEntry[];
}

export interface DashboardTimeline {
  labels: string[];
  errors: number[];
  fixes: number[];
  deployments: number[];
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
