import { useEffect, useRef, useMemo } from 'react';
import {
  AlertTriangle,
  Wrench,
  Rocket,
  Clock,
  Eye,
  Brain,
  Shield,
  Sparkles,
  CheckCircle2,
  ArrowRight,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';
import { Card } from '../ui/card';
import { Badge } from '../ui/badge';
import { Spinner } from '../ui/spinner';
import { useDashboard } from '../../hooks/use-dashboard';
import { useAuditLog } from '../../hooks/use-audit-log';
import { useSSE } from '../../hooks/use-sse';

const MODULE_COLORS: Record<string, string> = {
  WATCH: '#06b6d4',
  THINK: '#a855f7',
  HEAL: '#22c55e',
  VERIFY: '#3b82f6',
  EVOLVE: '#f59e0b',
};

const MODULE_ICONS: Record<string, typeof Eye> = {
  WATCH: Eye,
  THINK: Brain,
  HEAL: Wrench,
  VERIFY: Shield,
  EVOLVE: Sparkles,
};

const CATEGORY_COLORS: Record<string, string> = {
  database: '#ef4444',
  auth: '#f97316',
  api: '#eab308',
  integration: '#3b82f6',
  ai: '#a855f7',
  infrastructure: '#ec4899',
  ui: '#14b8a6',
  unknown: '#6b7280',
};

const SEVERITY_COLORS: Record<string, string> = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#3b82f6',
};

function getActionIcon(action: string) {
  if (action.includes('error') || action.includes('detect')) return AlertTriangle;
  if (action.includes('fix') || action.includes('heal')) return Wrench;
  if (action.includes('deploy') || action.includes('promote')) return Shield;
  if (action.includes('feature') || action.includes('evolve')) return Sparkles;
  return AlertTriangle;
}

function getActionBadgeVariant(action: string): 'critical' | 'high' | 'medium' | 'low' | 'success' | 'info' | 'default' {
  if (action.includes('error') || action.includes('detect')) return 'critical';
  if (action.includes('fix') || action.includes('generate')) return 'success';
  if (action.includes('deploy') || action.includes('approve')) return 'info';
  if (action.includes('feature')) return 'medium';
  return 'default';
}

export function DashboardPage() {
  const { summary, timeline, loading, error: dashboardError } = useDashboard();
  const { entries: auditEntries } = useAuditLog();
  const { connected, events } = useSSE();
  const feedRef = useRef<HTMLDivElement>(null);

  // Combine SSE events with audit entries for the activity feed
  const activityFeed = useMemo(() => {
    const sseItems = events.map((e, i) => ({
      id: `sse-${i}`,
      timestamp: e.timestamp,
      action: e.type,
      details: typeof e.data === 'object' ? JSON.stringify(e.data) : String(e.data),
      module: e.type.split('.')[0] || 'system',
      actor: 'system',
    }));
    const auditItems = auditEntries.map((e) => ({
      id: e.id,
      timestamp: e.created_at,
      action: e.action,
      details: typeof e.details === 'object' ? JSON.stringify(e.details) : String(e.details),
      module: e.entity_type || 'system',
      actor: e.actor || 'sentinel',
    }));
    const combined = [...sseItems, ...auditItems];
    combined.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    return combined.slice(0, 20);
  }, [events, auditEntries]);

  // Auto-scroll feed
  useEffect(() => {
    if (feedRef.current) {
      feedRef.current.scrollTop = 0;
    }
  }, [activityFeed]);

  // Build timeline chart data from backend response
  const timelineData = useMemo(() => {
    if (!timeline?.timeline) return [];
    return timeline.timeline.map((entry) => ({
      time: new Date(entry.hour).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      errors: entry.errors,
      fixes: entry.fixes,
    }));
  }, [timeline]);

  // Build category chart data from summary
  const categoryData = useMemo(() => {
    if (!summary?.errors_by_category) return [];
    return Object.entries(summary.errors_by_category).map(([name, value]) => ({ name, value }));
  }, [summary]);

  // Pipeline flow counts
  const pipelineCounts = useMemo(() => {
    if (!summary) return { WATCH: 0, THINK: 0, HEAL: 0, VERIFY: 0, EVOLVE: 0 };
    const byStatus = summary.errors_by_status || {};
    return {
      WATCH: summary.total_errors,
      THINK: (byStatus['acknowledged'] || 0) + (byStatus['fix_generated'] || 0),
      HEAL: summary.fixes_generated,
      VERIFY: summary.total_deployments,
      EVOLVE: summary.total_features,
    };
  }, [summary]);

  const totalErrors = summary?.total_errors ?? 0;
  const fixesGenerated = summary?.fixes_generated ?? 0;
  const fixesDeployed = summary?.fixes_deployed ?? 0;
  const successRate = summary?.success_rate ?? 0;
  const mttrMinutes = summary?.mttr_minutes ?? 0;

  // Severity breakdown bar widths from actual data
  const severityBreakdown = useMemo(() => {
    if (!summary?.errors_by_severity || !totalErrors) return [];
    const sev = summary.errors_by_severity;
    return [
      { key: 'critical', pct: Math.round(((sev.critical || 0) / totalErrors) * 100), color: SEVERITY_COLORS.critical },
      { key: 'high', pct: Math.round(((sev.high || 0) / totalErrors) * 100), color: SEVERITY_COLORS.high },
      { key: 'medium', pct: Math.round(((sev.medium || 0) / totalErrors) * 100), color: SEVERITY_COLORS.medium },
      { key: 'low', pct: Math.round(((sev.low || 0) / totalErrors) * 100), color: SEVERITY_COLORS.low },
    ];
  }, [summary, totalErrors]);

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  if (dashboardError) {
    return (
      <div className="flex h-96 flex-col items-center justify-center gap-4">
        <AlertTriangle size={48} className="text-red-400" />
        <p className="text-sm text-red-400">Failed to load dashboard: {dashboardError}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold">Dashboard</h2>
        <p className="mt-1 text-sm text-gray-400">System overview and real-time metrics</p>
      </div>

      {/* Hero Stats Row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Total Errors */}
        <Card className="relative overflow-hidden">
          <div className="flex items-center gap-4">
            <div className="rounded-lg bg-red-500/10 p-3 text-red-400">
              <AlertTriangle size={22} />
            </div>
            <div className="flex-1">
              <p className="text-xs text-gray-400">Total Errors</p>
              <p className="text-2xl font-bold">{totalErrors}</p>
            </div>
          </div>
          {totalErrors > 0 && (
            <div className="mt-3 flex h-1.5 overflow-hidden rounded-full">
              {severityBreakdown.map((s) => (
                <div
                  key={s.key}
                  style={{ width: `${s.pct}%`, backgroundColor: s.color }}
                />
              ))}
            </div>
          )}
        </Card>

        {/* Fixes Generated */}
        <Card className="relative overflow-hidden">
          <div className="flex items-center gap-4">
            <div className="rounded-lg bg-green-500/10 p-3 text-green-400">
              <Wrench size={22} />
            </div>
            <div className="flex-1">
              <p className="text-xs text-gray-400">Fixes Generated</p>
              <p className="text-2xl font-bold">{fixesGenerated}</p>
            </div>
          </div>
          <div className="mt-2">
            <span className="text-xs text-gray-500">
              {successRate > 0 ? `${Math.round(successRate * 100)}% success rate` : 'No data yet'}
            </span>
          </div>
        </Card>

        {/* Fixes Deployed */}
        <Card className="relative overflow-hidden">
          <div className="flex items-center gap-4">
            <div className="rounded-lg bg-blue-500/10 p-3 text-blue-400">
              <Rocket size={22} />
            </div>
            <div className="flex-1">
              <p className="text-xs text-gray-400">Fixes Deployed</p>
              <div className="flex items-center gap-2">
                <p className="text-2xl font-bold">{fixesDeployed}</p>
                {fixesDeployed > 0 && <CheckCircle2 size={16} className="text-green-400" />}
              </div>
            </div>
          </div>
        </Card>

        {/* MTTR */}
        <Card className="relative overflow-hidden">
          <div className="flex items-center gap-4">
            <div className="rounded-lg bg-amber-500/10 p-3 text-amber-400">
              <Clock size={22} />
            </div>
            <div className="flex-1">
              <p className="text-xs text-gray-400">MTTR</p>
              <p className="text-2xl font-bold">
                {mttrMinutes > 0 ? `${Math.round(mttrMinutes)}m` : '--'}
              </p>
            </div>
          </div>
          <div className="mt-2">
            <span className="text-xs text-gray-500">Mean time to resolution</span>
          </div>
        </Card>
      </div>

      {/* Pipeline Flow Visualization */}
      <Card title="Pipeline Flow" description="Items currently at each stage">
        <div className="flex items-center justify-between gap-2 overflow-x-auto py-4 px-2">
          {(['WATCH', 'THINK', 'HEAL', 'VERIFY', 'EVOLVE'] as const).map((mod, i) => {
            const Icon = MODULE_ICONS[mod];
            const count = pipelineCounts[mod];
            return (
              <div key={mod} className="flex items-center gap-2">
                <div className="flex flex-col items-center gap-2">
                  <div
                    className="flex h-14 w-14 items-center justify-center rounded-full border-2"
                    style={{
                      borderColor: MODULE_COLORS[mod],
                      backgroundColor: `${MODULE_COLORS[mod]}15`,
                    }}
                  >
                    <Icon size={22} style={{ color: MODULE_COLORS[mod] }} />
                  </div>
                  <div className="text-center">
                    <p className="text-xs font-bold" style={{ color: MODULE_COLORS[mod] }}>
                      {mod}
                    </p>
                    <p className="text-lg font-bold text-gray-100">{count}</p>
                  </div>
                </div>
                {i < 4 && (
                  <ArrowRight size={20} className="mx-1 text-gray-600 flex-shrink-0" />
                )}
              </div>
            );
          })}
        </div>
      </Card>

      {/* Charts Row */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Error Trend Area Chart */}
        <Card title="Error Trend" description="Errors over the last 24 hours">
          <div className="h-64">
            {timelineData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={timelineData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="errorGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                  <XAxis
                    dataKey="time"
                    stroke="#4b5563"
                    tick={{ fill: '#6b7280', fontSize: 11 }}
                    tickLine={false}
                  />
                  <YAxis
                    stroke="#4b5563"
                    tick={{ fill: '#6b7280', fontSize: 11 }}
                    tickLine={false}
                    allowDecimals={false}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#111827',
                      border: '1px solid #374151',
                      borderRadius: '8px',
                      color: '#e5e7eb',
                      fontSize: '12px',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="errors"
                    stroke="#ef4444"
                    strokeWidth={2}
                    fill="url(#errorGradient)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center rounded-lg border border-dashed border-gray-800">
                <span className="text-sm text-gray-600">No timeline data available</span>
              </div>
            )}
          </div>
        </Card>

        {/* Category Breakdown Donut Chart */}
        <Card title="Category Breakdown" description="Errors by category">
          <div className="h-64">
            {categoryData.length > 0 && categoryData.some((d) => d.value > 0) ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={categoryData}
                    cx="50%"
                    cy="45%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={3}
                    dataKey="value"
                    nameKey="name"
                  >
                    {categoryData.map((entry) => (
                      <Cell
                        key={entry.name}
                        fill={CATEGORY_COLORS[entry.name] || CATEGORY_COLORS.unknown}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#111827',
                      border: '1px solid #374151',
                      borderRadius: '8px',
                      color: '#e5e7eb',
                      fontSize: '12px',
                    }}
                  />
                  <Legend
                    verticalAlign="bottom"
                    height={36}
                    formatter={(value: string) => (
                      <span className="text-xs text-gray-400">{value}</span>
                    )}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center rounded-lg border border-dashed border-gray-800">
                <span className="text-sm text-gray-600">No category data available</span>
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* Recent Activity Feed */}
      <Card title="Recent Activity" description="Real-time event feed">
        <div ref={feedRef} className="max-h-80 space-y-2 overflow-y-auto pr-1">
          {activityFeed.length > 0 ? (
            activityFeed.map((item) => {
              const Icon = getActionIcon(item.action);
              const variant = getActionBadgeVariant(item.action);
              return (
                <div
                  key={item.id}
                  className="flex items-start gap-3 rounded-lg border border-gray-800 bg-gray-950 p-3 transition-colors hover:border-gray-700"
                >
                  <Icon size={16} className="mt-0.5 flex-shrink-0 text-gray-400" />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <Badge variant={variant}>{item.action}</Badge>
                      <span className="text-xs text-gray-500">
                        {new Date(item.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="mt-1 truncate text-xs text-gray-400">{item.details}</p>
                  </div>
                  <Badge variant="default">{item.module}</Badge>
                </div>
              );
            })
          ) : (
            <div className="py-8 text-center text-sm text-gray-600">
              No activity yet. Events will appear here as the system processes errors.
            </div>
          )}
        </div>
      </Card>

      {/* System Status Bar */}
      <div className="flex flex-wrap items-center gap-6 rounded-xl border border-gray-800 bg-gray-900 px-5 py-3">
        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
          System Status
        </span>
        {[
          { name: 'Metrics App', key: 'metrics_app' },
          { name: 'GitHub API', key: 'github_api' },
          { name: 'Claude API', key: 'claude_api' },
        ].map((service) => {
          const health = summary?.system_health?.[service.key];
          const isConnected = health === 'connected' || connected;
          return (
            <div key={service.key} className="flex items-center gap-2">
              <div
                className={`h-2 w-2 rounded-full ${
                  isConnected ? 'bg-green-400 shadow-[0_0_6px_rgba(74,222,128,0.5)]' : 'bg-red-400'
                }`}
              />
              <span className="text-xs text-gray-300">{service.name}</span>
              <span className={`text-xs ${isConnected ? 'text-green-400' : 'text-red-400'}`}>
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          );
        })}
        <div className="ml-auto flex items-center gap-2">
          <Badge variant="info">v1.0.0</Badge>
          <span className="text-xs text-gray-500">Skillfield Sentinel</span>
        </div>
      </div>
    </div>
  );
}
