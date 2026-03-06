import { useState } from 'react';
import {
  FileText,
  ChevronDown,
  ChevronRight,
  AlertTriangle,
  Wrench,
  Shield,
  Sparkles,
  CheckCircle2,
} from 'lucide-react';
import { Card } from '../ui/card';
import { Badge } from '../ui/badge';
import { Spinner } from '../ui/spinner';
import { Button } from '../ui/button';
import { useAuditLog } from '../../hooks/use-audit-log';

type FilterType = 'all' | 'error' | 'fix' | 'deployment' | 'feature';

function getActionBadgeVariant(action: string): 'critical' | 'high' | 'medium' | 'low' | 'success' | 'info' | 'default' {
  if (action.includes('error') || action.includes('detected')) return 'critical';
  if (action.includes('fix') || action.includes('generated')) return 'success';
  if (action.includes('approved') || action.includes('approve')) return 'info';
  if (action.includes('deploy') || action.includes('promote')) return 'high';
  if (action.includes('feature')) return 'medium';
  return 'default';
}

function getActionIcon(action: string) {
  if (action.includes('error') || action.includes('detect')) return AlertTriangle;
  if (action.includes('fix') || action.includes('generate')) return Wrench;
  if (action.includes('deploy') || action.includes('approve')) return Shield;
  if (action.includes('feature')) return Sparkles;
  return CheckCircle2;
}

const ITEMS_PER_PAGE = 15;

export function AuditPage() {
  const { entries, loading, error } = useAuditLog();
  const [filter, setFilter] = useState<FilterType>('all');
  const [page, setPage] = useState(1);
  const [expandedRow, setExpandedRow] = useState<string | null>(null);

  const filteredEntries = entries.filter((entry) => {
    if (filter === 'all') return true;
    const action = entry.action.toLowerCase();
    const module = entry.module.toLowerCase();
    switch (filter) {
      case 'error':
        return action.includes('error') || module.includes('watch') || module.includes('think');
      case 'fix':
        return action.includes('fix') || module.includes('heal');
      case 'deployment':
        return action.includes('deploy') || module.includes('verify');
      case 'feature':
        return action.includes('feature') || module.includes('evolve');
      default:
        return true;
    }
  });

  const totalPages = Math.max(1, Math.ceil(filteredEntries.length / ITEMS_PER_PAGE));
  const currentPage = Math.min(page, totalPages);
  const pagedEntries = filteredEntries.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE,
  );

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <FileText size={28} className="text-gray-400" />
        <div>
          <h2 className="text-2xl font-bold">Audit Log</h2>
          <p className="mt-1 text-sm text-gray-400">
            Complete history of all system actions and decisions
          </p>
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div className="rounded-lg border border-red-800 bg-red-900/20 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-2">
        {(['all', 'error', 'fix', 'deployment', 'feature'] as FilterType[]).map((f) => (
          <Button
            key={f}
            variant={filter === f ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => {
              setFilter(f);
              setPage(1);
            }}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </Button>
        ))}
        <span className="ml-auto text-xs text-gray-500">
          {filteredEntries.length} entries
        </span>
      </div>

      {/* Table */}
      <Card className="overflow-hidden p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 bg-gray-950">
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Timestamp
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Action
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Module
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  ID
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Actor
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Details
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {pagedEntries.length > 0 ? (
                pagedEntries.map((entry) => {
                  const Icon = getActionIcon(entry.action);
                  const variant = getActionBadgeVariant(entry.action);
                  const isExpanded = expandedRow === entry.id;
                  let parsedDetails: Record<string, unknown> | null = null;
                  try {
                    const parsed = JSON.parse(entry.details);
                    if (typeof parsed === 'object' && parsed !== null) {
                      parsedDetails = parsed as Record<string, unknown>;
                    }
                  } catch {
                    parsedDetails = null;
                  }

                  return (
                    <tr
                      key={entry.id}
                      className="transition-colors hover:bg-gray-800/50 cursor-pointer"
                      onClick={() => setExpandedRow(isExpanded ? null : entry.id)}
                    >
                      <td className="whitespace-nowrap px-4 py-3 text-xs text-gray-300">
                        {new Date(entry.timestamp).toLocaleString()}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <Icon size={14} className="text-gray-500" />
                          <Badge variant={variant}>{entry.action}</Badge>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant="default">{entry.module}</Badge>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-gray-400">
                        {entry.id.slice(0, 8)}...
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-300">{entry.actor}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          {isExpanded ? (
                            <ChevronDown size={14} className="text-gray-500" />
                          ) : (
                            <ChevronRight size={14} className="text-gray-500" />
                          )}
                          {!isExpanded && (
                            <span className="max-w-xs truncate text-xs text-gray-400">
                              {entry.details}
                            </span>
                          )}
                          {isExpanded && parsedDetails && (
                            <pre className="mt-1 max-w-md overflow-x-auto rounded bg-gray-950 p-2 text-xs text-gray-300">
                              {JSON.stringify(parsedDetails, null, 2)}
                            </pre>
                          )}
                          {isExpanded && !parsedDetails && (
                            <span className="text-xs text-gray-400">{entry.details}</span>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-sm text-gray-600">
                    No audit entries found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-500">
            Page {currentPage} of {totalPages}
          </span>
          <div className="flex gap-2">
            <Button
              variant="secondary"
              size="sm"
              disabled={currentPage <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Previous
            </Button>
            <Button
              variant="secondary"
              size="sm"
              disabled={currentPage >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
