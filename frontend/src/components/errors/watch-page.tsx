import { useState, useEffect, useRef, useMemo } from 'react';
import { Eye, Send, Wifi, WifiOff, Search, AlertTriangle, Clock, Activity } from 'lucide-react';
import { Card } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Spinner } from '../ui/spinner';
import { EmptyState } from '../ui/empty-state';
import { useSSE } from '../../hooks/use-sse';
import { useLogs } from '../../hooks/use-logs';
import { ingestLog } from '../../services/api';
import type { LogEntry } from '../../types';

type LevelFilter = 'all' | 'ERROR' | 'WARN' | 'INFO';
type TimeRange = '1h' | '24h' | '7d' | 'all';

function getLevelBadgeVariant(level: string) {
  switch (level.toUpperCase()) {
    case 'ERROR':
      return 'critical' as const;
    case 'WARN':
    case 'WARNING':
      return 'medium' as const;
    case 'INFO':
      return 'info' as const;
    default:
      return 'default' as const;
  }
}

function formatDate(ts: string): string {
  try {
    const d = new Date(ts);
    return d.toLocaleDateString('en-AU', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  } catch {
    return ts;
  }
}

export function WatchPage() {
  const { connected, events } = useSSE();
  const { logs: apiLogs, loading, error: fetchError, total } = useLogs();
  const [levelFilter, setLevelFilter] = useState<LevelFilter>('all');
  const [timeRange, setTimeRange] = useState<TimeRange>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [ingesting, setIngesting] = useState(false);
  const [ingestFeedback, setIngestFeedback] = useState<string | null>(null);
  const feedRef = useRef<HTMLDivElement>(null);

  // Combine SSE events (type=log) with API logs
  const sseLogs = useMemo(() => {
    return events
      .filter((e) => e.type === 'log' || e.type === 'new_log')
      .map((e) => {
        const data = e.data as Record<string, unknown>;
        return {
          id: (data.id as string) || `sse-${e.timestamp}`,
          timestamp: (data.timestamp as string) || e.timestamp,
          level: (data.level as string) || 'INFO',
          message: (data.message as string) || (data.raw_log as string) || '',
          source: (data.source as string) || 'unknown',
          environment: data.environment as string,
        } satisfies LogEntry;
      });
  }, [events]);

  // Merge and deduplicate logs
  const allLogs = useMemo(() => {
    const map = new Map<string, LogEntry>();
    for (const log of apiLogs) {
      map.set(log.id, log);
    }
    for (const log of sseLogs) {
      if (!map.has(log.id)) {
        map.set(log.id, log);
      }
    }
    return Array.from(map.values()).sort(
      (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
    );
  }, [apiLogs, sseLogs]);

  // Apply filters
  const filteredLogs = useMemo(() => {
    let result = allLogs;

    if (levelFilter !== 'all') {
      result = result.filter((l) => l.level.toUpperCase() === levelFilter);
    }

    if (timeRange !== 'all') {
      const now = Date.now();
      const rangeMs: Record<string, number> = {
        '1h': 3600000,
        '24h': 86400000,
        '7d': 604800000,
      };
      const cutoff = now - (rangeMs[timeRange] ?? 0);
      result = result.filter((l) => new Date(l.timestamp).getTime() >= cutoff);
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (l) =>
          l.message.toLowerCase().includes(q) ||
          l.source.toLowerCase().includes(q),
      );
    }

    return result.slice(0, 100);
  }, [allLogs, levelFilter, timeRange, searchQuery]);

  // Stats
  const errorCount = allLogs.filter((l) => l.level.toUpperCase() === 'ERROR').length;
  const errorsLastHour = allLogs.filter((l) => {
    if (l.level.toUpperCase() !== 'ERROR') return false;
    return Date.now() - new Date(l.timestamp).getTime() < 3600000;
  }).length;

  // Auto-scroll
  useEffect(() => {
    if (feedRef.current) {
      feedRef.current.scrollTop = 0;
    }
  }, [filteredLogs.length]);

  const handleIngestTestLog = async () => {
    setIngesting(true);
    setIngestFeedback(null);
    try {
      await ingestLog({
        timestamp: new Date().toISOString(),
        source: 'metrics-app',
        environment: 'production',
        raw_log: '[MetricService] Failed to calculate formula for metric',
        error_message: '[MetricService] Failed to calculate formula for metric',
        error_type: 'FormulaError',
        stack_trace:
          'Error: Failed to calculate formula\n    at MetricService.calculateFormula (src/lib/services/metric/metric.service.ts:245:12)\n    at async MetricValueService.createMetricValue (src/lib/services/metric/metric-value.service.ts:89:20)',
        severity: 'high',
      });
      setIngestFeedback('Log ingested successfully');
      setTimeout(() => setIngestFeedback(null), 3000);
    } catch (err) {
      setIngestFeedback(
        `Failed: ${err instanceof Error ? err.message : 'Unknown error'}`,
      );
    } finally {
      setIngesting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="flex items-center gap-3 text-2xl font-bold">
            <Eye className="text-cyan-500" size={28} />
            <span>
              <span className="text-cyan-500">WATCH</span> — Log Monitoring
            </span>
          </h2>
          <p className="mt-1 flex items-center gap-3 text-sm text-gray-400">
            <span>{total} total logs ingested</span>
            <span className="flex items-center gap-1">
              {connected ? (
                <>
                  <Wifi size={14} className="text-green-400" />
                  <span className="text-green-400">Connected</span>
                </>
              ) : (
                <>
                  <WifiOff size={14} className="text-red-400" />
                  <span className="text-red-400">Disconnected</span>
                </>
              )}
            </span>
          </p>
        </div>
        <div className="flex items-center gap-3">
          {ingestFeedback && (
            <span
              className={`text-xs ${ingestFeedback.startsWith('Failed') ? 'text-red-400' : 'text-green-400'}`}
            >
              {ingestFeedback}
            </span>
          )}
          <Button
            size="sm"
            variant="secondary"
            onClick={handleIngestTestLog}
            disabled={ingesting}
            className="border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/10"
          >
            {ingesting ? <Spinner size="sm" /> : <Send size={14} />}
            Ingest Test Log
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card className="border-cyan-500/20">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-red-500/10">
              <AlertTriangle size={20} className="text-red-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-100">{errorCount}</p>
              <p className="text-xs text-gray-400">Total Errors</p>
            </div>
          </div>
        </Card>
        <Card className="border-cyan-500/20">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-orange-500/10">
              <Clock size={20} className="text-orange-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-100">{errorsLastHour}</p>
              <p className="text-xs text-gray-400">Errors (Last Hour)</p>
            </div>
          </div>
        </Card>
        <Card className="border-cyan-500/20">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-cyan-500/10">
              <Activity size={20} className="text-cyan-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-100">
                {allLogs.length > 0
                  ? `${((errorCount / allLogs.length) * 100).toFixed(1)}%`
                  : '0%'}
              </p>
              <p className="text-xs text-gray-400">Error Rate</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Filters Bar */}
      <div className="flex flex-wrap items-center gap-3 rounded-lg border border-gray-800 bg-gray-900 p-3">
        {/* Level filter */}
        <div className="flex items-center gap-1">
          <span className="mr-1 text-xs text-gray-500">Level:</span>
          {(['all', 'ERROR', 'WARN', 'INFO'] as LevelFilter[]).map((level) => (
            <button
              key={level}
              onClick={() => setLevelFilter(level)}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                levelFilter === level
                  ? 'bg-cyan-500/20 text-cyan-400'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
              }`}
            >
              {level === 'all' ? 'All' : level}
            </button>
          ))}
        </div>

        <div className="h-5 w-px bg-gray-700" />

        {/* Time range */}
        <div className="flex items-center gap-1">
          <span className="mr-1 text-xs text-gray-500">Time:</span>
          {(
            [
              ['1h', 'Last Hour'],
              ['24h', 'Last 24h'],
              ['7d', 'Last 7d'],
              ['all', 'All Time'],
            ] as [TimeRange, string][]
          ).map(([value, label]) => (
            <button
              key={value}
              onClick={() => setTimeRange(value)}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                timeRange === value
                  ? 'bg-cyan-500/20 text-cyan-400'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="h-5 w-px bg-gray-700" />

        {/* Search */}
        <div className="relative flex-1">
          <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search log messages..."
            className="w-full rounded-md border border-gray-700 bg-gray-800 py-1.5 pl-8 pr-3 text-xs text-gray-200 placeholder-gray-500 outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/25"
          />
        </div>
      </div>

      {/* Log Feed */}
      {loading && allLogs.length === 0 ? (
        <div className="flex items-center justify-center py-16">
          <Spinner size="lg" className="text-cyan-500" />
        </div>
      ) : fetchError && allLogs.length === 0 ? (
        <Card className="border-red-500/20">
          <p className="text-sm text-red-400">Failed to load logs: {fetchError}</p>
        </Card>
      ) : filteredLogs.length === 0 ? (
        <EmptyState
          icon={<Eye size={48} />}
          title="No logs ingested yet"
          description="Connect your application or click 'Ingest Test Log' to start monitoring. Logs will stream in real-time."
          action={
            <Button
              size="sm"
              variant="secondary"
              onClick={handleIngestTestLog}
              disabled={ingesting}
              className="border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/10"
            >
              <Send size={14} />
              Ingest Test Log
            </Button>
          }
        />
      ) : (
        <div className="rounded-lg border border-gray-800 bg-gray-900">
          <div className="border-b border-gray-800 px-4 py-2.5">
            <span className="text-xs font-medium text-gray-400">
              Showing {filteredLogs.length} of {allLogs.length} log entries
            </span>
          </div>
          <div
            ref={feedRef}
            className="max-h-[560px] overflow-y-auto"
          >
            {filteredLogs.map((log, idx) => (
              <div
                key={log.id || idx}
                className="flex items-start gap-3 border-b border-gray-800/50 px-4 py-2.5 transition-colors hover:bg-gray-800/40 last:border-b-0"
              >
                {/* Timestamp */}
                <span className="shrink-0 pt-0.5 font-mono text-xs text-gray-500">
                  {formatDate(log.timestamp)}
                </span>

                {/* Level badge */}
                <Badge
                  variant={getLevelBadgeVariant(log.level)}
                  className="shrink-0 font-mono text-[10px] uppercase"
                >
                  {log.level.toUpperCase().slice(0, 5).padEnd(5)}
                </Badge>

                {/* Source */}
                <span className="shrink-0 rounded bg-gray-800 px-1.5 py-0.5 font-mono text-[10px] text-gray-400">
                  {log.source}
                </span>

                {/* Message */}
                <span className="min-w-0 flex-1 truncate font-mono text-xs text-gray-200">
                  {log.message}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
