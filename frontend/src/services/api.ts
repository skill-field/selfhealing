import type {
  LogEntry,
  Error as AppError,
  ErrorStats,
  Fix,
  Deployment,
  FeatureRequest,
  AuditEntry,
  DashboardSummary,
  DashboardTimeline,
} from '../types';

const BASE = '/api/v1';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json();
}

// Health
export const health = () => request<{ status: string }>('/health');

// Logs (WATCH)
export const getLogs = (params?: Record<string, string>) => {
  const qs = params ? '?' + new URLSearchParams(params).toString() : '';
  return request<{ logs: LogEntry[]; total: number }>(`/logs/recent${qs}`);
};

export const ingestLog = (log: Record<string, unknown>) =>
  request<{ status: string; message: string }>('/logs/ingest', {
    method: 'POST',
    body: JSON.stringify(log),
  });

// Errors (THINK)
export const getErrors = (params?: Record<string, string>) => {
  const qs = params ? '?' + new URLSearchParams(params).toString() : '';
  return request<{ errors: AppError[]; total: number; page: number; page_size: number }>(
    `/errors${qs}`,
  );
};
export const getError = (id: string) => request<AppError>(`/errors/${id}`);
export const getErrorStats = () => request<ErrorStats>('/errors/stats');

// Fixes (HEAL)
export const getFixes = (filters?: Record<string, string>) => {
  const qs = filters ? '?' + new URLSearchParams(filters).toString() : '';
  return request<{ fixes: Fix[]; total: number }>(`/fixes${qs}`);
};
export const getFix = (id: string) => request<Fix>(`/fixes/${id}`);
export const generateFix = (errorId: string, guidance?: string) =>
  request<Fix>(`/errors/${errorId}/generate-fix`, {
    method: 'POST',
    body: JSON.stringify({ guidance }),
  });
export const approveFix = (id: string, notes?: string) =>
  request<Fix>(`/fixes/${id}/approve`, {
    method: 'POST',
    body: JSON.stringify({ notes }),
  });
export const rejectFix = (id: string, reason?: string) =>
  request<Fix>(`/fixes/${id}/reject`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  });
export const regenerateFix = (id: string, guidance: string) =>
  request<Fix>(`/fixes/${id}/regenerate`, {
    method: 'POST',
    body: JSON.stringify({ guidance }),
  });

// Deployments (VERIFY)
export const getDeployments = () =>
  request<Deployment[] | { deployments: Deployment[]; total: number }>('/deployments');
export const getDeployment = (id: string) => request<Deployment>(`/deployments/${id}`);
export const deployToStaging = (fixId: string) =>
  request<Deployment>(`/fixes/${fixId}/deploy-staging`, { method: 'POST' });
export const promoteDeployment = (deploymentId: string) =>
  request<Deployment>(`/deployments/${deploymentId}/promote`, { method: 'POST' });

// Features (EVOLVE)
export const getFeatures = (filters?: Record<string, string>) => {
  const qs = filters ? '?' + new URLSearchParams(filters).toString() : '';
  return request<FeatureRequest[] | { features: FeatureRequest[]; total: number }>(`/features${qs}`);
};
export const getFeature = (id: string) => request<FeatureRequest>(`/features/${id}`);
export const createFeature = (title: string, description: string, priority: string) =>
  request<FeatureRequest>('/features', {
    method: 'POST',
    body: JSON.stringify({ title, description, priority }),
  });
export const generateFeature = (featureId: string) =>
  request<FeatureRequest>(`/features/${featureId}/generate`, { method: 'POST' });
export const approveFeature = (featureId: string, notes?: string) =>
  request<FeatureRequest>(`/features/${featureId}/approve`, {
    method: 'POST',
    body: JSON.stringify({ notes }),
  });
export const rejectFeature = (featureId: string, notes: string) =>
  request<FeatureRequest>(`/features/${featureId}/reject`, {
    method: 'POST',
    body: JSON.stringify({ notes }),
  });

// Dashboard
export const getDashboardSummary = () => request<DashboardSummary>('/dashboard/summary');
export const getDashboardTimeline = () => request<DashboardTimeline>('/dashboard/timeline');

// Audit
export const getAuditLog = () => request<AuditEntry[]>('/audit');
