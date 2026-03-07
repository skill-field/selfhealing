import { useState, useMemo, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Wrench,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Clock,
  Rocket,
  ChevronDown,
  ChevronRight,
  ArrowLeft,
  Sparkles,
  Cpu,
  Shield,
  AlertTriangle,
  X,
} from 'lucide-react';
import { Card } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Spinner } from '../ui/spinner';
import { EmptyState } from '../ui/empty-state';
import { DiffViewer } from './diff-viewer';
import { useFixes } from '../../hooks/use-fixes';
import { approveFix, rejectFix, regenerateFix, generateFix } from '../../services/api';
import type { Fix } from '../../types';

type StatusFilter = 'all' | 'pending' | 'approved' | 'rejected' | 'deployed' | 'failed';

function getStatusBadgeVariant(status: string) {
  switch (status) {
    case 'pending':
      return 'medium' as const;
    case 'approved':
      return 'success' as const;
    case 'rejected':
      return 'critical' as const;
    case 'deployed':
      return 'info' as const;
    case 'failed':
      return 'high' as const;
    default:
      return 'default' as const;
  }
}

function getConfidenceColor(confidence: number | null): string {
  if (confidence === null) return 'text-gray-400';
  if (confidence > 80) return 'text-green-400';
  if (confidence >= 50) return 'text-yellow-400';
  return 'text-red-400';
}

function getConfidenceBarColor(confidence: number | null): string {
  if (confidence === null) return 'bg-gray-600';
  if (confidence > 80) return 'bg-green-500';
  if (confidence >= 50) return 'bg-yellow-500';
  return 'bg-red-500';
}

function getRiskLevel(confidence: number | null): { label: string; variant: 'success' | 'medium' | 'critical' } {
  if (confidence === null) return { label: 'Unknown', variant: 'medium' };
  if (confidence > 80) return { label: 'Low Risk', variant: 'success' };
  if (confidence >= 50) return { label: 'Medium Risk', variant: 'medium' };
  return { label: 'High Risk', variant: 'critical' };
}

function formatDate(ts?: string): string {
  if (!ts) return '--';
  try {
    const d = new Date(ts);
    return d.toLocaleDateString('en-AU', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    });
  } catch {
    return ts;
  }
}

function getModelBadge(model: string) {
  const lower = (model ?? '').toLowerCase();
  if (lower.includes('opus')) return { label: 'Opus', variant: 'info' as const };
  if (lower.includes('sonnet')) return { label: 'Sonnet', variant: 'success' as const };
  return { label: model || 'Unknown', variant: 'default' as const };
}

export function HealPage() {
  const [searchParams] = useSearchParams();
  const errorIdParam = searchParams.get('error_id');

  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [selectedFixId, setSelectedFixId] = useState<string | null>(null);
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Generate fix state
  const [generating, setGenerating] = useState(false);
  const [generatedFix, setGeneratedFix] = useState<Fix | null>(null);
  const [generateError, setGenerateError] = useState<string | null>(null);

  const filterParams = useMemo(() => {
    const p: Record<string, string> = {};
    if (statusFilter !== 'all') p.status = statusFilter;
    return p;
  }, [statusFilter]);

  const { fixes, loading, error: fetchError, refetch } = useFixes(filterParams);

  // Stats
  const stats = useMemo(() => {
    const all = fixes;
    return {
      total: all.length,
      pending: all.filter((f) => f.status === 'pending').length,
      approved: all.filter((f) => f.status === 'approved').length,
      deployed: all.filter((f) => f.status === 'deployed').length,
    };
  }, [fixes]);

  const selectedFix = useMemo(() => {
    if (generatedFix && selectedFixId === generatedFix.id) return generatedFix;
    return fixes.find((f) => f.id === selectedFixId) ?? null;
  }, [fixes, selectedFixId, generatedFix]);

  const showNotification = useCallback((type: 'success' | 'error', message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 4000);
  }, []);

  // Generate fix from error
  const handleGenerateFix = async () => {
    if (!errorIdParam) return;
    setGenerating(true);
    setGenerateError(null);
    try {
      const fix = await generateFix(errorIdParam);
      setGeneratedFix(fix);
      setSelectedFixId(fix.id);
      showNotification('success', 'Fix generated successfully');
      refetch();
    } catch (err) {
      setGenerateError(err instanceof Error ? err.message : 'Failed to generate fix');
      showNotification('error', 'Failed to generate fix');
    } finally {
      setGenerating(false);
    }
  };

  // If showing detail view
  if (selectedFix) {
    return (
      <div className="space-y-6">
        <FixDetailView
          fix={selectedFix}
          onBack={() => {
            setSelectedFixId(null);
            setGeneratedFix(null);
          }}
          onNotification={showNotification}
          onRefetch={refetch}
        />
        {notification && <Notification type={notification.type} message={notification.message} onDismiss={() => setNotification(null)} />}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Notification */}
      {notification && <Notification type={notification.type} message={notification.message} onDismiss={() => setNotification(null)} />}

      {/* Header */}
      <div>
        <h2 className="flex items-center gap-3 text-2xl font-bold">
          <Wrench className="text-green-500" size={28} />
          <span>
            <span className="text-green-500">HEAL</span> -- Fix Generation
          </span>
        </h2>
        <p className="mt-1 text-sm text-gray-400">
          AI-generated code fixes with diff preview and approval workflow
        </p>
      </div>

      {/* Generate Fix from Error */}
      {errorIdParam && (
        <Card className="border-green-500/20">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-500/10">
                <Sparkles size={20} className="text-green-400" />
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-100">Generate Fix for Error</p>
                <p className="text-xs text-gray-400">
                  Error ID: <span className="font-mono text-green-400">{errorIdParam}</span>
                </p>
              </div>
            </div>
            <Button
              size="md"
              className="bg-green-600 hover:bg-green-500"
              onClick={handleGenerateFix}
              disabled={generating}
            >
              {generating ? (
                <>
                  <Spinner size="sm" className="text-white" />
                  Claude is analyzing the code...
                </>
              ) : (
                <>
                  <Wrench size={16} />
                  Generate Fix
                </>
              )}
            </Button>
          </div>
          {generating && (
            <div className="mt-4 flex items-center gap-3 rounded-lg bg-green-500/5 p-3">
              <Spinner size="sm" className="text-green-400" />
              <p className="text-xs text-green-400">
                Claude is analyzing the code and generating a fix. This may take 10-30 seconds...
              </p>
            </div>
          )}
          {generateError && (
            <div className="mt-4 rounded-lg bg-red-500/10 p-3">
              <p className="text-xs text-red-400">{generateError}</p>
            </div>
          )}
        </Card>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
        <StatCard
          icon={<Wrench size={20} className="text-green-400" />}
          value={stats.total}
          label="Total Fixes"
          borderColor="border-green-500/20"
          bgColor="bg-green-500/10"
          loading={loading && fixes.length === 0}
        />
        <StatCard
          icon={<Clock size={20} className="text-yellow-400" />}
          value={stats.pending}
          label="Pending Review"
          borderColor="border-yellow-500/20"
          bgColor="bg-yellow-500/10"
          loading={loading && fixes.length === 0}
        />
        <StatCard
          icon={<CheckCircle2 size={20} className="text-green-400" />}
          value={stats.approved}
          label="Approved"
          borderColor="border-green-500/20"
          bgColor="bg-green-500/10"
          loading={loading && fixes.length === 0}
        />
        <StatCard
          icon={<Rocket size={20} className="text-blue-400" />}
          value={stats.deployed}
          label="Deployed"
          borderColor="border-blue-500/20"
          bgColor="bg-blue-500/10"
          loading={loading && fixes.length === 0}
        />
      </div>

      {/* Status Filter */}
      <div className="flex flex-wrap items-center gap-3 rounded-lg border border-gray-800 bg-gray-900 p-3">
        <span className="mr-1 text-xs text-gray-500">Status:</span>
        {(['all', 'pending', 'approved', 'rejected', 'deployed', 'failed'] as StatusFilter[]).map(
          (s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`rounded-md px-2.5 py-1 text-xs font-medium capitalize transition-colors ${
                statusFilter === s
                  ? 'bg-green-500/20 text-green-400'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
              }`}
            >
              {s === 'all' ? 'All' : s}
            </button>
          ),
        )}
      </div>

      {/* Fix List */}
      {loading && fixes.length === 0 ? (
        <div className="flex items-center justify-center py-16">
          <Spinner size="lg" className="text-green-500" />
        </div>
      ) : fetchError && fixes.length === 0 ? (
        <Card className="border-red-500/20">
          <p className="text-sm text-red-400">Failed to load fixes: {fetchError}</p>
        </Card>
      ) : fixes.length === 0 ? (
        <EmptyState
          icon={<Wrench size={48} />}
          title="No fixes generated yet"
          description="Select an error from the Think module to generate a fix."
        />
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-800 bg-gray-900">
          {/* Table Header */}
          <div className="grid min-w-[700px] grid-cols-[90px_1fr_100px_90px_120px_120px] items-center gap-2 border-b border-gray-800 bg-gray-900/80 px-4 py-2.5 text-xs font-semibold uppercase text-gray-500">
            <span>Status</span>
            <span>Error Message</span>
            <span>Confidence</span>
            <span>Model</span>
            <span>Created</span>
            <span>Actions</span>
          </div>

          {/* Rows */}
          <div className="max-h-[520px] overflow-y-auto">
            {fixes.map((fix) => (
              <FixRow
                key={fix.id}
                fix={fix}
                onClick={() => setSelectedFixId(fix.id)}
                onNotification={showNotification}
                onRefetch={refetch}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ---- Sub-components ---- */

function Notification({
  type,
  message,
  onDismiss,
}: {
  type: 'success' | 'error';
  message: string;
  onDismiss: () => void;
}) {
  return (
    <div
      className={`fixed right-6 top-6 z-50 flex items-center gap-3 rounded-lg border px-4 py-3 shadow-lg ${
        type === 'success'
          ? 'border-green-500/30 bg-green-500/10 text-green-400'
          : 'border-red-500/30 bg-red-500/10 text-red-400'
      }`}
    >
      {type === 'success' ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
      <span className="text-sm">{message}</span>
      <button onClick={onDismiss} className="ml-2 rounded p-0.5 transition-colors hover:bg-gray-800">
        <X size={14} />
      </button>
    </div>
  );
}

function StatCard({
  icon,
  value,
  label,
  borderColor,
  bgColor,
  loading,
}: {
  icon: React.ReactNode;
  value: number;
  label: string;
  borderColor: string;
  bgColor: string;
  loading: boolean;
}) {
  return (
    <Card className={borderColor}>
      <div className="flex items-center gap-3">
        <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${bgColor}`}>
          {icon}
        </div>
        <div>
          {loading ? (
            <Spinner size="sm" className="text-green-400" />
          ) : (
            <>
              <p className="text-2xl font-bold text-gray-100">{value}</p>
              <p className="text-xs text-gray-400">{label}</p>
            </>
          )}
        </div>
      </div>
    </Card>
  );
}

function FixRow({ fix, onClick, onNotification, onRefetch }: { fix: Fix; onClick: () => void; onNotification: (type: 'success' | 'error', message: string) => void; onRefetch: () => void }) {
  const errorMsg = fix.explanation
    ? fix.explanation.substring(0, 80) + (fix.explanation.length > 80 ? '...' : '')
    : '(no description)';
  const confidence = fix.confidence;
  const model = getModelBadge(fix.model_used);

  return (
    <div
      className="grid min-w-[700px] cursor-pointer grid-cols-[90px_1fr_100px_90px_120px_120px] items-center gap-2 border-b border-gray-800/50 px-4 py-2.5 transition-colors hover:bg-gray-800/40"
      onClick={onClick}
    >
      <Badge variant={getStatusBadgeVariant(fix.status)} className="justify-center text-[10px]">
        {fix.status.toUpperCase()}
      </Badge>

      <span className="flex items-center gap-1.5 truncate font-mono text-xs text-gray-200">
        <ChevronRight size={14} className="shrink-0 text-gray-500" />
        {errorMsg}
      </span>

      <div className="flex items-center gap-2">
        <span className={`font-mono text-xs font-semibold ${getConfidenceColor(confidence)}`}>
          {confidence !== null ? `${Math.round(confidence)}%` : '--'}
        </span>
        <div className="h-1.5 w-12 overflow-hidden rounded-full bg-gray-700">
          <div
            className={`h-full rounded-full transition-all ${getConfidenceBarColor(confidence)}`}
            style={{ width: `${confidence ?? 0}%` }}
          />
        </div>
      </div>

      <Badge variant={model.variant} className="text-[10px]">
        {model.label}
      </Badge>

      <span className="text-xs text-gray-400">
        {formatDate(fix.created_at)}
      </span>

      <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
        {fix.status === 'pending' && (
          <>
            <button
              title="Approve"
              className="rounded p-1 text-green-500/60 transition-colors hover:bg-green-500/10 hover:text-green-400"
              onClick={async () => {
                try {
                  await approveFix(fix.id);
                  onNotification('success', 'Fix approved');
                  onRefetch();
                } catch (err) {
                  onNotification('error', err instanceof Error ? err.message : 'Failed to approve');
                }
              }}
            >
              <CheckCircle2 size={14} />
            </button>
            <button
              title="Reject"
              className="rounded p-1 text-red-500/60 transition-colors hover:bg-red-500/10 hover:text-red-400"
              onClick={async () => {
                try {
                  await rejectFix(fix.id, 'Rejected from list view');
                  onNotification('success', 'Fix rejected');
                  onRefetch();
                } catch (err) {
                  onNotification('error', err instanceof Error ? err.message : 'Failed to reject');
                }
              }}
            >
              <XCircle size={14} />
            </button>
          </>
        )}
        <button
          title="View Details"
          className="rounded p-1 text-gray-500 transition-colors hover:bg-gray-700 hover:text-gray-300"
          onClick={onClick}
        >
          <ChevronDown size={14} />
        </button>
      </div>
    </div>
  );
}

function FixDetailView({
  fix,
  onBack,
  onNotification,
  onRefetch,
}: {
  fix: Fix;
  onBack: () => void;
  onNotification: (type: 'success' | 'error', message: string) => void;
  onRefetch: () => void;
}) {
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [showRejectForm, setShowRejectForm] = useState(false);
  const [showRegenerateForm, setShowRegenerateForm] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [regenerateGuidance, setRegenerateGuidance] = useState('');

  const risk = getRiskLevel(fix.confidence);
  const model = getModelBadge(fix.model_used);

  const handleApprove = async () => {
    setActionLoading('approve');
    try {
      await approveFix(fix.id);
      onNotification('success', 'Fix approved successfully');
      onRefetch();
    } catch (err) {
      onNotification('error', err instanceof Error ? err.message : 'Failed to approve fix');
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async () => {
    if (!rejectReason.trim()) return;
    setActionLoading('reject');
    try {
      await rejectFix(fix.id, rejectReason);
      onNotification('success', 'Fix rejected');
      setShowRejectForm(false);
      setRejectReason('');
      onRefetch();
    } catch (err) {
      onNotification('error', err instanceof Error ? err.message : 'Failed to reject fix');
    } finally {
      setActionLoading(null);
    }
  };

  const handleRegenerate = async () => {
    if (!regenerateGuidance.trim()) return;
    setActionLoading('regenerate');
    try {
      await regenerateFix(fix.id, regenerateGuidance);
      onNotification('success', 'Fix regeneration requested');
      setShowRegenerateForm(false);
      setRegenerateGuidance('');
      onRefetch();
    } catch (err) {
      onNotification('error', err instanceof Error ? err.message : 'Failed to regenerate fix');
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Back button + header */}
      <div>
        <button
          onClick={onBack}
          className="mb-3 flex items-center gap-1.5 text-sm text-gray-400 transition-colors hover:text-gray-200"
        >
          <ArrowLeft size={16} />
          Back to Fix List
        </button>
        <h2 className="flex items-center gap-3 text-2xl font-bold">
          <Wrench className="text-green-500" size={28} />
          <span>
            <span className="text-green-500">HEAL</span> -- Fix Detail
          </span>
        </h2>
        <div className="mt-2 flex items-center gap-3">
          <Badge variant={getStatusBadgeVariant(fix.status)}>
            {fix.status.toUpperCase()}
          </Badge>
          <span className="text-xs text-gray-500">
            Attempt #{fix.attempt_number ?? 1}
          </span>
          <span className="text-xs text-gray-500">
            {formatDate(fix.created_at)}
          </span>
        </div>
      </div>

      {/* Code Diff Viewer - CENTERPIECE */}
      <div>
        <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-200">
          <span className="flex h-6 w-6 items-center justify-center rounded bg-green-500/10">
            <Wrench size={14} className="text-green-400" />
          </span>
          Code Changes
        </h3>
        <DiffViewer
          diff={fix.diff ?? ''}
          filesChanged={Array.isArray(fix.files_changed) ? JSON.stringify(fix.files_changed) : fix.files_changed}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Explanation Panel */}
        <Card className="border-green-500/20">
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Sparkles size={16} className="text-green-400" />
              <h4 className="text-sm font-semibold text-gray-100">Fix Explanation</h4>
            </div>
            <div className="rounded-md bg-gray-950/60 p-4">
              <p className="whitespace-pre-wrap text-xs leading-relaxed text-gray-300">
                {fix.explanation ?? '(No explanation available)'}
              </p>
            </div>

            {/* Confidence meter */}
            <div>
              <div className="mb-1.5 flex items-center justify-between">
                <span className="text-xs text-gray-500">Confidence</span>
                <span className={`font-mono text-sm font-bold ${getConfidenceColor(fix.confidence)}`}>
                  {fix.confidence !== null ? `${Math.round(fix.confidence)}%` : '--'}
                </span>
              </div>
              <div className="h-2.5 w-full overflow-hidden rounded-full bg-gray-700">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${getConfidenceBarColor(fix.confidence)}`}
                  style={{ width: `${fix.confidence ?? 0}%` }}
                />
              </div>
            </div>

            {/* Risk assessment */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Shield size={14} className="text-gray-500" />
                <span className="text-xs text-gray-500">Risk Assessment</span>
              </div>
              <Badge variant={risk.variant}>{risk.label}</Badge>
            </div>
          </div>
        </Card>

        {/* Model Info + Actions */}
        <div className="space-y-4">
          {/* Model & token info */}
          <Card className="border-gray-700">
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Cpu size={16} className="text-gray-400" />
                <h4 className="text-sm font-semibold text-gray-100">Model Details</h4>
              </div>
              <div className="space-y-2 rounded-md bg-gray-950/60 p-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">Model</span>
                  <Badge variant={model.variant}>{model.label}</Badge>
                </div>
                {fix.prompt_tokens !== null && (
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500">Prompt Tokens</span>
                    <span className="font-mono text-xs text-gray-300">
                      {fix.prompt_tokens?.toLocaleString() ?? '--'}
                    </span>
                  </div>
                )}
                {fix.completion_tokens !== null && (
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500">Completion Tokens</span>
                    <span className="font-mono text-xs text-gray-300">
                      {fix.completion_tokens?.toLocaleString() ?? '--'}
                    </span>
                  </div>
                )}
                {(fix.prompt_tokens !== null && fix.completion_tokens !== null) && (
                  <div className="flex items-center justify-between border-t border-gray-800 pt-2">
                    <span className="text-xs text-gray-500">Total Tokens</span>
                    <span className="font-mono text-xs font-semibold text-gray-200">
                      {((fix.prompt_tokens ?? 0) + (fix.completion_tokens ?? 0)).toLocaleString()}
                    </span>
                  </div>
                )}
              </div>

              {fix.guidance && (
                <div className="rounded-md bg-gray-950/60 p-3">
                  <span className="text-xs text-gray-500">Guidance provided:</span>
                  <p className="mt-1 text-xs text-gray-400">{fix.guidance}</p>
                </div>
              )}

              {fix.reviewer_notes && (
                <div className="rounded-md bg-gray-950/60 p-3">
                  <span className="text-xs text-gray-500">Reviewer notes:</span>
                  <p className="mt-1 text-xs text-gray-400">{fix.reviewer_notes}</p>
                </div>
              )}
            </div>
          </Card>

          {/* Action Buttons */}
          <Card className="border-green-500/20">
            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-gray-100">Actions</h4>

              <div className="flex flex-wrap gap-2">
                {(fix.status === 'pending' || fix.status === 'failed') && (
                  <>
                    <Button
                      size="sm"
                      className="bg-green-600 hover:bg-green-500"
                      onClick={handleApprove}
                      disabled={actionLoading !== null}
                    >
                      {actionLoading === 'approve' ? (
                        <Spinner size="sm" className="text-white" />
                      ) : (
                        <CheckCircle2 size={14} />
                      )}
                      Approve
                    </Button>
                    <Button
                      size="sm"
                      variant="danger"
                      onClick={() => {
                        setShowRejectForm(!showRejectForm);
                        setShowRegenerateForm(false);
                      }}
                      disabled={actionLoading !== null}
                    >
                      <XCircle size={14} />
                      Reject
                    </Button>
                    <Button
                      size="sm"
                      className="bg-yellow-600 hover:bg-yellow-500"
                      onClick={() => {
                        setShowRegenerateForm(!showRegenerateForm);
                        setShowRejectForm(false);
                      }}
                      disabled={actionLoading !== null}
                    >
                      <RefreshCw size={14} />
                      Regenerate
                    </Button>
                  </>
                )}

                {fix.status === 'approved' && (
                  <div className="flex items-center gap-2 text-xs text-green-400">
                    <CheckCircle2 size={14} />
                    This fix has been approved and is ready for deployment.
                  </div>
                )}

                {fix.status === 'rejected' && (
                  <div className="flex items-center gap-2 text-xs text-red-400">
                    <XCircle size={14} />
                    This fix was rejected.
                    <Button
                      size="sm"
                      className="ml-2 bg-yellow-600 hover:bg-yellow-500"
                      onClick={() => {
                        setShowRegenerateForm(!showRegenerateForm);
                      }}
                      disabled={actionLoading !== null}
                    >
                      <RefreshCw size={14} />
                      Regenerate
                    </Button>
                  </div>
                )}

                {fix.status === 'deployed' && (
                  <div className="flex items-center gap-2 text-xs text-blue-400">
                    <Rocket size={14} />
                    This fix has been deployed.
                  </div>
                )}
              </div>

              {/* Reject form */}
              {showRejectForm && (
                <div className="space-y-2 rounded-lg border border-red-500/20 bg-red-500/5 p-3">
                  <div className="flex items-center gap-2">
                    <AlertTriangle size={14} className="text-red-400" />
                    <span className="text-xs font-semibold text-red-400">Rejection Reason</span>
                  </div>
                  <textarea
                    value={rejectReason}
                    onChange={(e) => setRejectReason(e.target.value)}
                    placeholder="Explain why this fix should be rejected..."
                    className="w-full rounded-md border border-gray-700 bg-gray-900 px-3 py-2 font-mono text-xs text-gray-200 placeholder-gray-600 outline-none focus:border-red-500/50"
                    rows={3}
                  />
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="danger"
                      onClick={handleReject}
                      disabled={!rejectReason.trim() || actionLoading !== null}
                    >
                      {actionLoading === 'reject' ? (
                        <Spinner size="sm" className="text-white" />
                      ) : (
                        'Confirm Rejection'
                      )}
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        setShowRejectForm(false);
                        setRejectReason('');
                      }}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              )}

              {/* Regenerate form */}
              {showRegenerateForm && (
                <div className="space-y-2 rounded-lg border border-yellow-500/20 bg-yellow-500/5 p-3">
                  <div className="flex items-center gap-2">
                    <RefreshCw size={14} className="text-yellow-400" />
                    <span className="text-xs font-semibold text-yellow-400">Regeneration Guidance</span>
                  </div>
                  <textarea
                    value={regenerateGuidance}
                    onChange={(e) => setRegenerateGuidance(e.target.value)}
                    placeholder="Provide guidance for regenerating the fix (e.g., 'use a different approach', 'handle edge case X')..."
                    className="w-full rounded-md border border-gray-700 bg-gray-900 px-3 py-2 font-mono text-xs text-gray-200 placeholder-gray-600 outline-none focus:border-yellow-500/50"
                    rows={3}
                  />
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      className="bg-yellow-600 hover:bg-yellow-500"
                      onClick={handleRegenerate}
                      disabled={!regenerateGuidance.trim() || actionLoading !== null}
                    >
                      {actionLoading === 'regenerate' ? (
                        <Spinner size="sm" className="text-white" />
                      ) : (
                        'Confirm Regeneration'
                      )}
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        setShowRegenerateForm(false);
                        setRegenerateGuidance('');
                      }}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
