import { useState, useMemo } from 'react';
import {
  Brain,
  ChevronDown,
  ChevronRight,
  ArrowUpDown,
  Eye,
  EyeOff,
  Wrench,
  FileCode,
  AlertCircle,
} from 'lucide-react';
import { Card } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Spinner } from '../ui/spinner';
import { EmptyState } from '../ui/empty-state';
import { useErrors } from '../../hooks/use-errors';
import type { Error as AppError } from '../../types';

type StatusFilter = 'all' | 'new' | 'acknowledged' | 'fix_generated' | 'resolved' | 'ignored';
type SeverityFilter = 'all' | 'critical' | 'high' | 'medium' | 'low';
type CategoryFilter = 'all' | 'database' | 'auth' | 'api' | 'integration' | 'ai' | 'infrastructure' | 'unknown';
type SortField = 'severity' | 'occurrence_count' | 'first_seen';
type SortDirection = 'asc' | 'desc';

const SEVERITY_ORDER: Record<string, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
};

function getSeverityVariant(severity?: string) {
  switch (severity) {
    case 'critical':
      return 'critical' as const;
    case 'high':
      return 'high' as const;
    case 'medium':
      return 'medium' as const;
    case 'low':
      return 'low' as const;
    default:
      return 'default' as const;
  }
}

const CATEGORY_COLORS: Record<string, string> = {
  database: 'bg-red-500/20 text-red-400 border-red-500/30',
  auth: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  api: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  integration: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  ai: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  infrastructure: 'bg-pink-500/20 text-pink-400 border-pink-500/30',
  unknown: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
};

const STATUS_LABELS: Record<string, string> = {
  new: 'New',
  acknowledged: 'Acknowledged',
  fix_generated: 'Fix Generated',
  resolved: 'Resolved',
  ignored: 'Ignored',
};

function formatDate(ts?: string): string {
  if (!ts) return '—';
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

function getErrorMessage(err: AppError): string {
  return err.error_message || err.raw_log || '(no message)';
}

export function ThinkPage() {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>('all');
  const [categoryFilter, setCategoryFilter] = useState<CategoryFilter>('all');
  const [sortField, setSortField] = useState<SortField>('first_seen');
  const [sortDir, setSortDir] = useState<SortDirection>('desc');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const filterParams = useMemo(() => {
    const p: Record<string, string> = {};
    if (statusFilter !== 'all') p.status = statusFilter;
    if (severityFilter !== 'all') p.severity = severityFilter;
    if (categoryFilter !== 'all') p.category = categoryFilter;
    return p;
  }, [statusFilter, severityFilter, categoryFilter]);

  const { errors, loading, error: fetchError, stats, statsLoading } = useErrors(filterParams);

  // Sort
  const sortedErrors = useMemo(() => {
    const sorted = [...errors];
    sorted.sort((a, b) => {
      let cmp = 0;
      switch (sortField) {
        case 'severity':
          cmp =
            (SEVERITY_ORDER[a.severity ?? 'low'] ?? 4) -
            (SEVERITY_ORDER[b.severity ?? 'low'] ?? 4);
          break;
        case 'occurrence_count':
          cmp = (a.occurrence_count ?? 0) - (b.occurrence_count ?? 0);
          break;
        case 'first_seen':
          cmp =
            new Date(a.first_seen ?? a.created_at).getTime() -
            new Date(b.first_seen ?? b.created_at).getTime();
          break;
      }
      return sortDir === 'desc' ? -cmp : cmp;
    });
    return sorted;
  }, [errors, sortField, sortDir]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDir('desc');
    }
  };

  const toggleExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  // Stats counts
  const totalErrors = stats?.total_errors ?? errors.length;
  const unclassified = stats?.by_category?.['unknown'] ?? 0;
  const criticalCount = stats?.by_severity?.['critical'] ?? 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="flex items-center gap-3 text-2xl font-bold">
          <Brain className="text-purple-500" size={28} />
          <span>
            <span className="text-purple-500">THINK</span> — Error Analysis
          </span>
        </h2>
        <p className="mt-1 text-sm text-gray-400">
          AI-powered error classification and root cause analysis
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card className="border-purple-500/20">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-500/10">
              <AlertCircle size={20} className="text-purple-400" />
            </div>
            <div>
              {statsLoading && !stats ? (
                <Spinner size="sm" className="text-purple-400" />
              ) : (
                <>
                  <p className="text-2xl font-bold text-gray-100">{totalErrors}</p>
                  <p className="text-xs text-gray-400">Total Errors</p>
                </>
              )}
            </div>
          </div>
        </Card>
        <Card className="border-purple-500/20">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-500/10">
              <Brain size={20} className="text-gray-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-100">{unclassified}</p>
              <p className="text-xs text-gray-400">Unclassified</p>
            </div>
          </div>
        </Card>
        <Card className="border-purple-500/20">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-red-500/10">
              <AlertCircle size={20} className="text-red-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-100">{criticalCount}</p>
              <p className="text-xs text-gray-400">Critical</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 rounded-lg border border-gray-800 bg-gray-900 p-3">
        {/* Status */}
        <div className="flex items-center gap-1">
          <span className="mr-1 text-xs text-gray-500">Status:</span>
          {(['all', 'new', 'acknowledged', 'fix_generated', 'resolved', 'ignored'] as StatusFilter[]).map(
            (s) => (
              <button
                key={s}
                onClick={() => setStatusFilter(s)}
                className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                  statusFilter === s
                    ? 'bg-purple-500/20 text-purple-400'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
                }`}
              >
                {s === 'all' ? 'All' : STATUS_LABELS[s] ?? s}
              </button>
            ),
          )}
        </div>

        <div className="h-5 w-px bg-gray-700" />

        {/* Severity */}
        <div className="flex items-center gap-1">
          <span className="mr-1 text-xs text-gray-500">Severity:</span>
          {(['all', 'critical', 'high', 'medium', 'low'] as SeverityFilter[]).map((s) => (
            <button
              key={s}
              onClick={() => setSeverityFilter(s)}
              className={`rounded-md px-2.5 py-1 text-xs font-medium capitalize transition-colors ${
                severityFilter === s
                  ? 'bg-purple-500/20 text-purple-400'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
              }`}
            >
              {s === 'all' ? 'All' : s}
            </button>
          ))}
        </div>

        <div className="h-5 w-px bg-gray-700" />

        {/* Category */}
        <div className="flex items-center gap-1">
          <span className="mr-1 text-xs text-gray-500">Category:</span>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value as CategoryFilter)}
            className="rounded-md border border-gray-700 bg-gray-800 px-2.5 py-1 text-xs text-gray-300 outline-none focus:border-purple-500/50"
          >
            <option value="all">All</option>
            <option value="database">Database</option>
            <option value="auth">Auth</option>
            <option value="api">API</option>
            <option value="integration">Integration</option>
            <option value="ai">AI</option>
            <option value="infrastructure">Infrastructure</option>
            <option value="unknown">Unknown</option>
          </select>
        </div>
      </div>

      {/* Error Table / Content */}
      {loading && errors.length === 0 ? (
        <div className="flex items-center justify-center py-16">
          <Spinner size="lg" className="text-purple-500" />
        </div>
      ) : fetchError && errors.length === 0 ? (
        <Card className="border-red-500/20">
          <p className="text-sm text-red-400">Failed to load errors: {fetchError}</p>
        </Card>
      ) : sortedErrors.length === 0 ? (
        <EmptyState
          icon={<Brain size={48} />}
          title="No errors detected yet"
          description="Ingest logs from the Watch module to get started. Errors will be automatically analyzed and classified here."
        />
      ) : (
        <div className="overflow-hidden rounded-lg border border-gray-800 bg-gray-900">
          {/* Table Header */}
          <div className="grid grid-cols-[80px_100px_1fr_90px_110px_100px_80px] items-center gap-2 border-b border-gray-800 bg-gray-900/80 px-4 py-2.5 text-xs font-semibold uppercase text-gray-500">
            <SortableHeader
              label="Severity"
              field="severity"
              current={sortField}
              dir={sortDir}
              onSort={handleSort}
            />
            <span>Category</span>
            <span>Message</span>
            <SortableHeader
              label="Count"
              field="occurrence_count"
              current={sortField}
              dir={sortDir}
              onSort={handleSort}
            />
            <SortableHeader
              label="First Seen"
              field="first_seen"
              current={sortField}
              dir={sortDir}
              onSort={handleSort}
            />
            <span>Status</span>
            <span>Actions</span>
          </div>

          {/* Rows */}
          <div className="max-h-[520px] overflow-y-auto">
            {sortedErrors.map((err) => (
              <ErrorRow
                key={err.id}
                error={err}
                expanded={expandedId === err.id}
                onToggle={() => toggleExpand(err.id)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ─── Sub-components ──────────────────────────────────────────────────────── */

function SortableHeader({
  label,
  field,
  current,
  dir,
  onSort,
}: {
  label: string;
  field: SortField;
  current: SortField;
  dir: SortDirection;
  onSort: (f: SortField) => void;
}) {
  return (
    <button
      className="flex items-center gap-1 text-left text-xs font-semibold uppercase text-gray-500 hover:text-gray-300"
      onClick={() => onSort(field)}
    >
      {label}
      <ArrowUpDown
        size={12}
        className={current === field ? 'text-purple-400' : 'text-gray-600'}
      />
      {current === field && (
        <span className="text-[10px] text-purple-400">{dir === 'asc' ? 'asc' : 'desc'}</span>
      )}
    </button>
  );
}

function ErrorRow({
  error,
  expanded,
  onToggle,
}: {
  error: AppError;
  expanded: boolean;
  onToggle: () => void;
}) {
  const message = getErrorMessage(error);
  const statusLabel = STATUS_LABELS[error.status] ?? error.status;
  const categoryStyle =
    CATEGORY_COLORS[error.category ?? 'unknown'] ?? CATEGORY_COLORS.unknown;

  return (
    <>
      {/* Row */}
      <div
        className="grid cursor-pointer grid-cols-[80px_100px_1fr_90px_110px_100px_80px] items-center gap-2 border-b border-gray-800/50 px-4 py-2.5 transition-colors hover:bg-gray-800/40"
        onClick={onToggle}
      >
        <Badge variant={getSeverityVariant(error.severity)} className="justify-center text-[10px]">
          {(error.severity ?? 'low').toUpperCase()}
        </Badge>

        <span
          className={`inline-flex items-center justify-center truncate rounded-full border px-2 py-0.5 text-[10px] font-medium ${categoryStyle}`}
        >
          {error.category ?? 'unknown'}
        </span>

        <span className="flex items-center gap-1.5 truncate font-mono text-xs text-gray-200">
          {expanded ? <ChevronDown size={14} className="shrink-0 text-gray-500" /> : <ChevronRight size={14} className="shrink-0 text-gray-500" />}
          {message}
        </span>

        <span className="text-center font-mono text-xs text-gray-300">
          {error.occurrence_count ?? 1}
        </span>

        <span className="text-xs text-gray-400">
          {formatDate(error.first_seen ?? error.created_at)}
        </span>

        <span className="text-xs text-gray-400">{statusLabel}</span>

        <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
          <button
            title="Acknowledge"
            className="rounded p-1 text-gray-500 transition-colors hover:bg-gray-700 hover:text-gray-300"
          >
            <Eye size={14} />
          </button>
          <button
            title="Ignore"
            className="rounded p-1 text-gray-500 transition-colors hover:bg-gray-700 hover:text-gray-300"
          >
            <EyeOff size={14} />
          </button>
        </div>
      </div>

      {/* Expanded Detail Panel */}
      {expanded && <ErrorDetailPanel error={error} />}
    </>
  );
}

function ErrorDetailPanel({ error }: { error: AppError }) {
  const message = getErrorMessage(error);
  const affectedFiles = error.affected_files?.length
    ? error.affected_files
    : error.affected_file
      ? [error.affected_file]
      : [];

  return (
    <div className="border-b border-gray-800 bg-gray-950/60 px-6 py-5">
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Left column */}
        <div className="space-y-4">
          {/* Full message */}
          <div>
            <h4 className="mb-1.5 text-xs font-semibold uppercase text-gray-500">Error Message</h4>
            <p className="rounded-md bg-gray-900 p-3 font-mono text-xs leading-relaxed text-gray-200">
              {message}
            </p>
          </div>

          {/* Stack trace */}
          {error.stack_trace && (
            <div>
              <h4 className="mb-1.5 text-xs font-semibold uppercase text-gray-500">Stack Trace</h4>
              <pre className="max-h-48 overflow-auto rounded-md bg-gray-900 p-3 font-mono text-[11px] leading-relaxed text-gray-300">
                {error.stack_trace}
              </pre>
            </div>
          )}

          {/* Root cause */}
          <div>
            <h4 className="mb-1.5 text-xs font-semibold uppercase text-gray-500">
              Root Cause Analysis
            </h4>
            {error.root_cause ? (
              <p className="rounded-md bg-gray-900 p-3 text-xs leading-relaxed text-gray-300">
                {error.root_cause}
              </p>
            ) : (
              <div className="flex items-center gap-2 rounded-md bg-gray-900 p-3">
                <Brain size={14} className="text-purple-400" />
                <span className="text-xs text-gray-500">
                  Root cause not yet analyzed. Analysis will be performed automatically.
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Right column */}
        <div className="space-y-4">
          {/* Classification */}
          <div>
            <h4 className="mb-1.5 text-xs font-semibold uppercase text-gray-500">Classification</h4>
            <div className="flex items-center gap-2">
              <Badge variant={getSeverityVariant(error.severity)}>
                {(error.severity ?? 'low').toUpperCase()}
              </Badge>
              <span
                className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${
                  CATEGORY_COLORS[error.category ?? 'unknown'] ?? CATEGORY_COLORS.unknown
                }`}
              >
                {error.category ?? 'unknown'}
              </span>
              {error.error_type && (
                <span className="rounded bg-gray-800 px-2 py-0.5 font-mono text-[10px] text-gray-400">
                  {error.error_type}
                </span>
              )}
            </div>
          </div>

          {/* Occurrence timeline */}
          <div>
            <h4 className="mb-1.5 text-xs font-semibold uppercase text-gray-500">
              Occurrence Timeline
            </h4>
            <div className="space-y-1.5 rounded-md bg-gray-900 p-3">
              <div className="flex justify-between text-xs">
                <span className="text-gray-500">First Seen</span>
                <span className="text-gray-300">{formatDate(error.first_seen ?? error.created_at)}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-gray-500">Last Seen</span>
                <span className="text-gray-300">{formatDate(error.last_seen ?? error.updated_at)}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-gray-500">Occurrences</span>
                <span className="font-mono text-gray-300">{error.occurrence_count ?? 1}</span>
              </div>
            </div>
          </div>

          {/* Affected files */}
          {affectedFiles.length > 0 && (
            <div>
              <h4 className="mb-1.5 text-xs font-semibold uppercase text-gray-500">
                Affected Files
              </h4>
              <div className="space-y-1">
                {affectedFiles.map((f, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-2 rounded-md bg-gray-900 px-3 py-1.5"
                  >
                    <FileCode size={12} className="shrink-0 text-gray-500" />
                    <span className="truncate font-mono text-[11px] text-gray-300">{f}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div>
            <h4 className="mb-1.5 text-xs font-semibold uppercase text-gray-500">Actions</h4>
            <div className="flex flex-wrap gap-2">
              <Button size="sm" variant="primary" className="bg-green-600 hover:bg-green-500">
                <Wrench size={14} />
                Generate Fix
              </Button>
              <Button size="sm" variant="secondary">
                <Eye size={14} />
                Acknowledge
              </Button>
              <Button size="sm" variant="ghost">
                <EyeOff size={14} />
                Ignore
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
