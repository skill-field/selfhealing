import { useState, useEffect, useCallback } from 'react';
import {
  Settings,
  Plus,
  Trash2,
  GitBranch,
  Power,
  PowerOff,
  Github,
  Shield,
  Container,
  Radio,
  Globe,
  Server,
  Clock,
  XCircle,
  Cloud,
} from 'lucide-react';
import { Card } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Spinner } from '../ui/spinner';
import { EmptyState } from '../ui/empty-state';

const BASE = '/api/v1';

type TabType = 'repos' | 'containers' | 'log_feeds';

interface MonitoredRepo {
  id: string;
  display_name: string;
  repo_slug: string;
  has_token: boolean;
  scan_paths: string[];
  is_active: boolean;
  source_type: string;
  created_at: string;
  updated_at: string;
}

interface LogSource {
  id: string;
  display_name: string;
  source_type: string;
  endpoint_url: string | null;
  container_id: string | null;
  container_image: string | null;
  environment: string;
  has_auth: boolean;
  poll_interval_seconds: number;
  is_active: boolean;
  last_polled_at: string | null;
  created_at: string;
  updated_at: string;
}

const TAB_CONFIG = [
  { key: 'repos' as TabType, label: 'GitHub Repos', icon: Github, color: 'text-cyan-400' },
  { key: 'containers' as TabType, label: 'Containers', icon: Container, color: 'text-purple-400' },
  { key: 'log_feeds' as TabType, label: 'Log Feeds', icon: Radio, color: 'text-green-400' },
];

export function ReposPage() {
  const [activeTab, setActiveTab] = useState<TabType>('repos');
  const [repos, setRepos] = useState<MonitoredRepo[]>([]);
  const [sources, setSources] = useState<LogSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  const fetchRepos = useCallback(() => {
    fetch(`${BASE}/repos`)
      .then((r) => r.json())
      .then((d) => setRepos(d.repos ?? []))
      .catch((e) => setError(e.message));
  }, []);

  const fetchSources = useCallback(() => {
    fetch(`${BASE}/sources`)
      .then((r) => r.json())
      .then((d) => setSources(d.sources ?? []))
      .catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetch(`${BASE}/repos`).then((r) => r.json()).then((d) => setRepos(d.repos ?? [])),
      fetch(`${BASE}/sources`).then((r) => r.json()).then((d) => setSources(d.sources ?? [])),
    ])
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const handleDeleteRepo = async (id: string) => {
    if (!confirm('Remove this repository?')) return;
    try {
      await fetch(`${BASE}/repos/${id}`, { method: 'DELETE' });
      fetchRepos();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete');
    }
  };

  const handleToggleRepo = async (id: string, currentActive: boolean) => {
    try {
      await fetch(`${BASE}/repos/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: !currentActive }),
      });
      fetchRepos();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update');
    }
  };

  const handleDeleteSource = async (id: string) => {
    if (!confirm('Remove this source?')) return;
    try {
      await fetch(`${BASE}/sources/${id}`, { method: 'DELETE' });
      fetchSources();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete');
    }
  };

  const handleToggleSource = async (id: string, currentActive: boolean) => {
    try {
      await fetch(`${BASE}/sources/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: !currentActive }),
      });
      fetchSources();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update');
    }
  };

  const containers = sources.filter((s) => s.source_type === 'container');
  const logFeeds = sources.filter((s) => s.source_type !== 'container');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="flex items-center gap-3 text-2xl font-bold">
            <Settings className="text-gray-400" size={28} />
            <span>Monitored Applications</span>
          </h2>
          <p className="mt-1 text-sm text-gray-400">
            Configure GitHub repositories, containers, and log feeds for Sentinel to monitor
          </p>
        </div>
        <Button
          size="sm"
          variant="primary"
          onClick={() => setShowForm(!showForm)}
          className="border-cyan-500/30"
        >
          <Plus size={14} />
          Add Source
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 rounded-lg border border-gray-800 bg-gray-900 p-1">
        {TAB_CONFIG.map(({ key, label, icon: Icon, color }) => (
          <button
            key={key}
            onClick={() => { setActiveTab(key); setShowForm(false); }}
            className={`flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === key
                ? 'bg-gray-800 text-white'
                : 'text-gray-400 hover:bg-gray-800/50 hover:text-gray-200'
            }`}
          >
            <Icon size={16} className={activeTab === key ? color : 'text-gray-500'} />
            {label}
            <span className={`ml-1 rounded-full px-1.5 py-0.5 text-xs ${
              activeTab === key ? 'bg-gray-700 text-gray-200' : 'bg-gray-800 text-gray-500'
            }`}>
              {key === 'repos' ? repos.length : key === 'containers' ? containers.length : logFeeds.length}
            </span>
          </button>
        ))}
      </div>

      {/* Error */}
      {error && (
        <Card className="border-red-500/30">
          <div className="flex items-center justify-between">
            <p className="text-sm text-red-400">{error}</p>
            <button onClick={() => setError(null)} className="text-gray-500 hover:text-gray-300">
              <XCircle size={16} />
            </button>
          </div>
        </Card>
      )}

      {/* Add Forms */}
      {showForm && activeTab === 'repos' && (
        <RepoForm
          onSubmit={() => { fetchRepos(); setShowForm(false); }}
          onClose={() => setShowForm(false)}
          onError={setError}
        />
      )}
      {showForm && activeTab === 'containers' && (
        <ContainerForm
          onSubmit={() => { fetchSources(); setShowForm(false); }}
          onClose={() => setShowForm(false)}
          onError={setError}
        />
      )}
      {showForm && activeTab === 'log_feeds' && (
        <LogFeedForm
          onSubmit={() => { fetchSources(); setShowForm(false); }}
          onClose={() => setShowForm(false)}
          onError={setError}
        />
      )}

      {/* Loading */}
      {loading && (
        <div className="flex justify-center py-16">
          <Spinner size="lg" />
        </div>
      )}

      {/* Repos Tab */}
      {!loading && activeTab === 'repos' && (
        repos.length === 0 ? (
          <EmptyState
            icon={<GitBranch size={48} />}
            title="No repositories configured"
            description="Add a GitHub repository to start monitoring with Cloudera AI."
            action={
              <Button size="sm" variant="primary" onClick={() => setShowForm(true)}>
                <Plus size={14} />
                Add Your First Repo
              </Button>
            }
          />
        ) : (
          <div className="space-y-3">
            {repos.map((repo) => (
              <Card
                key={repo.id}
                className={`transition-colors ${repo.is_active ? 'border-gray-800' : 'border-gray-800/50 opacity-60'}`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${
                      repo.is_active ? 'bg-cyan-500/10' : 'bg-gray-800'
                    }`}>
                      <Github size={20} className={repo.is_active ? 'text-cyan-400' : 'text-gray-600'} />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-semibold text-gray-100">{repo.display_name}</h3>
                        <Badge variant={repo.is_active ? 'success' : 'default'}>
                          {repo.is_active ? 'Active' : 'Paused'}
                        </Badge>
                        {repo.has_token && (
                          <Badge variant="info"><Shield size={10} className="mr-0.5" />Token</Badge>
                        )}
                      </div>
                      <p className="mt-0.5 font-mono text-xs text-gray-500">{repo.repo_slug}</p>
                      {repo.scan_paths.length > 0 && (
                        <p className="mt-0.5 text-xs text-gray-600">
                          {repo.scan_paths.length} scan path{repo.scan_paths.length !== 1 ? 's' : ''}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button size="sm" variant="secondary" onClick={() => handleToggleRepo(repo.id, repo.is_active)}
                      title={repo.is_active ? 'Pause monitoring' : 'Resume monitoring'}>
                      {repo.is_active ? <PowerOff size={14} /> : <Power size={14} />}
                    </Button>
                    <Button size="sm" variant="secondary" onClick={() => handleDeleteRepo(repo.id)}
                      className="text-red-400 hover:bg-red-500/10" title="Remove repository">
                      <Trash2 size={14} />
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )
      )}

      {/* Containers Tab */}
      {!loading && activeTab === 'containers' && (
        containers.length === 0 ? (
          <EmptyState
            icon={<Container size={48} />}
            title="No containers configured"
            description="Add a Docker container or Kubernetes pod to monitor its logs."
            action={
              <Button size="sm" variant="primary" onClick={() => setShowForm(true)}>
                <Plus size={14} />
                Add Container
              </Button>
            }
          />
        ) : (
          <div className="space-y-3">
            {containers.map((source) => (
              <SourceCard
                key={source.id}
                source={source}
                icon={Container}
                iconColor="text-purple-400"
                bgColor="bg-purple-500/10"
                onToggle={handleToggleSource}
                onDelete={handleDeleteSource}
              />
            ))}
          </div>
        )
      )}

      {/* Log Feeds Tab */}
      {!loading && activeTab === 'log_feeds' && (
        logFeeds.length === 0 ? (
          <EmptyState
            icon={<Radio size={48} />}
            title="No log feeds configured"
            description="Add a log endpoint, syslog stream, or log file to monitor."
            action={
              <Button size="sm" variant="primary" onClick={() => setShowForm(true)}>
                <Plus size={14} />
                Add Log Feed
              </Button>
            }
          />
        ) : (
          <div className="space-y-3">
            {logFeeds.map((source) => (
              <SourceCard
                key={source.id}
                source={source}
                icon={source.source_type === 'syslog' ? Server : source.source_type === 'file' ? Globe : Radio}
                iconColor="text-green-400"
                bgColor="bg-green-500/10"
                onToggle={handleToggleSource}
                onDelete={handleDeleteSource}
              />
            ))}
          </div>
        )
      )}
    </div>
  );
}

/* ─── Source Card ─── */

function SourceCard({
  source,
  icon: Icon,
  iconColor,
  bgColor,
  onToggle,
  onDelete,
}: {
  source: LogSource;
  icon: typeof Container;
  iconColor: string;
  bgColor: string;
  onToggle: (id: string, active: boolean) => void;
  onDelete: (id: string) => void;
}) {
  const typeLabels: Record<string, string> = {
    container: 'Container',
    log_endpoint: 'HTTP Endpoint',
    syslog: 'Syslog',
    file: 'Log File',
  };

  return (
    <Card className={`transition-colors ${source.is_active ? 'border-gray-800' : 'border-gray-800/50 opacity-60'}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${
            source.is_active ? bgColor : 'bg-gray-800'
          }`}>
            <Icon size={20} className={source.is_active ? iconColor : 'text-gray-600'} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-gray-100">{source.display_name}</h3>
              <Badge variant={source.is_active ? 'success' : 'default'}>
                {source.is_active ? 'Active' : 'Paused'}
              </Badge>
              <Badge variant="info">{typeLabels[source.source_type] || source.source_type}</Badge>
              <Badge variant="default">{source.environment}</Badge>
            </div>
            {source.endpoint_url && (
              <p className="mt-0.5 font-mono text-xs text-gray-500">{source.endpoint_url}</p>
            )}
            {source.container_image && (
              <p className="mt-0.5 font-mono text-xs text-gray-500">{source.container_image}</p>
            )}
            {source.container_id && (
              <p className="mt-0.5 text-xs text-gray-600">ID: {source.container_id}</p>
            )}
            <div className="mt-0.5 flex items-center gap-3 text-xs text-gray-600">
              <span className="flex items-center gap-1">
                <Clock size={10} />
                Poll: {source.poll_interval_seconds}s
              </span>
              {source.has_auth && (
                <span className="flex items-center gap-1">
                  <Shield size={10} />
                  Auth
                </span>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button size="sm" variant="secondary" onClick={() => onToggle(source.id, source.is_active)}
            title={source.is_active ? 'Pause' : 'Resume'}>
            {source.is_active ? <PowerOff size={14} /> : <Power size={14} />}
          </Button>
          <Button size="sm" variant="secondary" onClick={() => onDelete(source.id)}
            className="text-red-400 hover:bg-red-500/10" title="Remove">
            <Trash2 size={14} />
          </Button>
        </div>
      </div>
    </Card>
  );
}

/* ─── Forms ─── */

function RepoForm({
  onSubmit,
  onClose,
  onError,
}: {
  onSubmit: () => void;
  onClose: () => void;
  onError: (msg: string) => void;
}) {
  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [token, setToken] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !slug.trim()) return;
    setSubmitting(true);
    try {
      const res = await fetch(`${BASE}/repos`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          display_name: name.trim(),
          repo_slug: slug.trim(),
          github_token: token.trim() || null,
          scan_paths: [],
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `HTTP ${res.status}`);
      }
      onSubmit();
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to add repo');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Card className="border-cyan-500/30">
      <form onSubmit={handleSubmit} className="space-y-4">
        <h3 className="flex items-center gap-2 text-sm font-semibold text-gray-200">
          <Github size={16} className="text-cyan-400" />
          Add GitHub Repository
        </h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-xs text-gray-400">Display Name</label>
            <input type="text" value={name} onChange={(e) => setName(e.target.value)}
              placeholder="My App" required
              className="w-full rounded-md border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-200 placeholder-gray-500 outline-none focus:border-cyan-500/50" />
          </div>
          <div>
            <label className="mb-1 block text-xs text-gray-400">
              GitHub Repo <span className="text-gray-600">(owner/repo)</span>
            </label>
            <input type="text" value={slug} onChange={(e) => setSlug(e.target.value)}
              placeholder="acme/my-app" required
              className="w-full rounded-md border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-200 placeholder-gray-500 outline-none focus:border-cyan-500/50" />
          </div>
        </div>
        <div>
          <label className="mb-1 block text-xs text-gray-400">
            GitHub Token <span className="text-gray-600">(optional — uses global token if empty)</span>
          </label>
          <input type="password" value={token} onChange={(e) => setToken(e.target.value)}
            placeholder="ghp_..."
            className="w-full rounded-md border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-200 placeholder-gray-500 outline-none focus:border-cyan-500/50" />
        </div>
        <FormActions submitting={submitting} onClose={onClose} label="Add Repository" />
      </form>
    </Card>
  );
}

const CLOUD_PRESETS = [
  { key: 'docker', label: 'Docker / K8s', icon: '🐳', fields: { endpoint_placeholder: '', needs_container_id: true } },
  { key: 'aws_ecs', label: 'AWS ECS / Fargate', icon: '☁️', fields: { endpoint_placeholder: 'arn:aws:ecs:us-east-1:123456:cluster/my-cluster', needs_container_id: false } },
  { key: 'aws_lambda', label: 'AWS Lambda', icon: '⚡', fields: { endpoint_placeholder: 'arn:aws:lambda:us-east-1:123456:function:my-fn', needs_container_id: false } },
  { key: 'azure_container', label: 'Azure Container Apps', icon: '🔷', fields: { endpoint_placeholder: '/subscriptions/.../containerApps/my-app', needs_container_id: false } },
  { key: 'gcp_run', label: 'GCP Cloud Run', icon: '🌐', fields: { endpoint_placeholder: 'projects/my-project/locations/us-central1/services/my-svc', needs_container_id: false } },
];

function ContainerForm({
  onSubmit,
  onClose,
  onError,
}: {
  onSubmit: () => void;
  onClose: () => void;
  onError: (msg: string) => void;
}) {
  const [name, setName] = useState('');
  const [preset, setPreset] = useState('docker');
  const [containerId, setContainerId] = useState('');
  const [image, setImage] = useState('');
  const [endpointUrl, setEndpointUrl] = useState('');
  const [authHeader, setAuthHeader] = useState('');
  const [env, setEnv] = useState('production');
  const [pollInterval, setPollInterval] = useState(60);
  const [submitting, setSubmitting] = useState(false);

  const activePreset = CLOUD_PRESETS.find((p) => p.key === preset) ?? CLOUD_PRESETS[0];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setSubmitting(true);
    try {
      const res = await fetch(`${BASE}/sources`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          display_name: name.trim(),
          source_type: 'container',
          container_id: containerId.trim() || null,
          container_image: image.trim() || (preset !== 'docker' ? preset : null),
          endpoint_url: endpointUrl.trim() || null,
          environment: env,
          auth_header: authHeader.trim() || null,
          poll_interval_seconds: pollInterval,
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `HTTP ${res.status}`);
      }
      onSubmit();
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to add container');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Card className="border-purple-500/30">
      <form onSubmit={handleSubmit} className="space-y-4">
        <h3 className="flex items-center gap-2 text-sm font-semibold text-gray-200">
          <Container size={16} className="text-purple-400" />
          Add Container / Cloud Service
        </h3>

        {/* Cloud provider presets */}
        <div>
          <label className="mb-2 block text-xs text-gray-400">Platform</label>
          <div className="flex flex-wrap gap-2">
            {CLOUD_PRESETS.map((p) => (
              <button
                key={p.key}
                type="button"
                onClick={() => setPreset(p.key)}
                className={`flex items-center gap-1.5 rounded-lg border px-3 py-2 text-xs font-medium transition-colors ${
                  preset === p.key
                    ? 'border-purple-500/50 bg-purple-500/15 text-purple-300'
                    : 'border-gray-700 bg-gray-800 text-gray-400 hover:border-gray-600 hover:text-gray-200'
                }`}
              >
                <span>{p.icon}</span>
                {p.label}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-xs text-gray-400">Display Name</label>
            <input type="text" value={name} onChange={(e) => setName(e.target.value)}
              placeholder="API Server" required
              className="w-full rounded-md border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-200 placeholder-gray-500 outline-none focus:border-purple-500/50" />
          </div>
          {activePreset.fields.needs_container_id ? (
            <div>
              <label className="mb-1 block text-xs text-gray-400">Container ID</label>
              <input type="text" value={containerId} onChange={(e) => setContainerId(e.target.value)}
                placeholder="abc123def456"
                className="w-full rounded-md border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-200 placeholder-gray-500 outline-none focus:border-purple-500/50" />
            </div>
          ) : (
            <div>
              <label className="mb-1 block text-xs text-gray-400">Resource ARN / ID</label>
              <input type="text" value={endpointUrl} onChange={(e) => setEndpointUrl(e.target.value)}
                placeholder={activePreset.fields.endpoint_placeholder}
                className="w-full rounded-md border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-200 placeholder-gray-500 outline-none focus:border-purple-500/50" />
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {preset === 'docker' && (
            <div>
              <label className="mb-1 block text-xs text-gray-400">Container Image</label>
              <input type="text" value={image} onChange={(e) => setImage(e.target.value)}
                placeholder="nginx:latest"
                className="w-full rounded-md border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-200 placeholder-gray-500 outline-none focus:border-purple-500/50" />
            </div>
          )}
          {preset !== 'docker' && (
            <div>
              <label className="mb-1 block text-xs text-gray-400">
                {preset.startsWith('aws') ? 'AWS Access Key / Role' : preset === 'azure_container' ? 'Azure Client ID' : 'GCP Service Account'}
              </label>
              <input type="password" value={authHeader} onChange={(e) => setAuthHeader(e.target.value)}
                placeholder="Credentials..."
                className="w-full rounded-md border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-200 placeholder-gray-500 outline-none focus:border-purple-500/50" />
            </div>
          )}
          <div>
            <label className="mb-1 block text-xs text-gray-400">Environment</label>
            <select value={env} onChange={(e) => setEnv(e.target.value)}
              className="w-full rounded-md border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-200 outline-none focus:border-purple-500/50">
              <option value="production">Production</option>
              <option value="staging">Staging</option>
              <option value="development">Development</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs text-gray-400">Poll Interval (seconds)</label>
            <input type="number" value={pollInterval} onChange={(e) => setPollInterval(Number(e.target.value))}
              min={10} max={3600}
              className="w-full rounded-md border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-200 outline-none focus:border-purple-500/50" />
          </div>
        </div>
        <FormActions submitting={submitting} onClose={onClose} label="Add Container" />
      </form>
    </Card>
  );
}

const LOG_FEED_PRESETS = [
  { key: 'log_endpoint', label: 'HTTP Endpoint', icon: '🔗', placeholder: 'https://api.example.com/logs' },
  { key: 'aws_cloudwatch', label: 'AWS CloudWatch', icon: '☁️', placeholder: 'arn:aws:logs:us-east-1:123456:log-group:/app/logs' },
  { key: 'azure_monitor', label: 'Azure Monitor', icon: '🔷', placeholder: '/subscriptions/.../providers/Microsoft.OperationalInsights/workspaces/...' },
  { key: 'gcp_logging', label: 'GCP Cloud Logging', icon: '🌐', placeholder: 'projects/my-project/logs/my-log' },
  { key: 'syslog', label: 'Syslog', icon: '📡', placeholder: 'udp://localhost:514' },
  { key: 'file', label: 'Log File', icon: '📄', placeholder: '/var/log/app/error.log' },
];

function LogFeedForm({
  onSubmit,
  onClose,
  onError,
}: {
  onSubmit: () => void;
  onClose: () => void;
  onError: (msg: string) => void;
}) {
  const [name, setName] = useState('');
  const [preset, setPreset] = useState('log_endpoint');
  const [url, setUrl] = useState('');
  const [authHeader, setAuthHeader] = useState('');
  const [env, setEnv] = useState('production');
  const [pollInterval, setPollInterval] = useState(60);
  const [submitting, setSubmitting] = useState(false);

  const activePreset = LOG_FEED_PRESETS.find((p) => p.key === preset) ?? LOG_FEED_PRESETS[0];
  const isCloudProvider = ['aws_cloudwatch', 'azure_monitor', 'gcp_logging'].includes(preset);
  const sourceType = isCloudProvider ? 'log_endpoint' : preset;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setSubmitting(true);
    try {
      const res = await fetch(`${BASE}/sources`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          display_name: name.trim(),
          source_type: sourceType,
          endpoint_url: url.trim() || null,
          container_image: isCloudProvider ? preset : null,
          environment: env,
          auth_header: authHeader.trim() || null,
          poll_interval_seconds: pollInterval,
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `HTTP ${res.status}`);
      }
      onSubmit();
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to add log feed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Card className="border-green-500/30">
      <form onSubmit={handleSubmit} className="space-y-4">
        <h3 className="flex items-center gap-2 text-sm font-semibold text-gray-200">
          <Radio size={16} className="text-green-400" />
          Add Log Feed
        </h3>

        {/* Source type presets */}
        <div>
          <label className="mb-2 block text-xs text-gray-400">Source</label>
          <div className="flex flex-wrap gap-2">
            {LOG_FEED_PRESETS.map((p) => (
              <button
                key={p.key}
                type="button"
                onClick={() => setPreset(p.key)}
                className={`flex items-center gap-1.5 rounded-lg border px-3 py-2 text-xs font-medium transition-colors ${
                  preset === p.key
                    ? 'border-green-500/50 bg-green-500/15 text-green-300'
                    : 'border-gray-700 bg-gray-800 text-gray-400 hover:border-gray-600 hover:text-gray-200'
                }`}
              >
                <span>{p.icon}</span>
                {p.label}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-xs text-gray-400">Display Name</label>
            <input type="text" value={name} onChange={(e) => setName(e.target.value)}
              placeholder="Payment Service Logs" required
              className="w-full rounded-md border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-200 placeholder-gray-500 outline-none focus:border-green-500/50" />
          </div>
          <div>
            <label className="mb-1 block text-xs text-gray-400">
              {preset === 'file' ? 'File Path' : isCloudProvider ? 'Resource ARN / ID' : preset === 'syslog' ? 'Syslog Address' : 'Endpoint URL'}
            </label>
            <input type="text" value={url} onChange={(e) => setUrl(e.target.value)}
              placeholder={activePreset.placeholder}
              className="w-full rounded-md border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-200 placeholder-gray-500 outline-none focus:border-green-500/50" />
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <label className="mb-1 block text-xs text-gray-400">
              {isCloudProvider
                ? preset === 'aws_cloudwatch' ? 'AWS Access Key / IAM Role ARN' : preset === 'azure_monitor' ? 'Azure Client ID / Key' : 'GCP Service Account JSON'
                : 'Auth Header'}
              <span className="text-gray-600"> (optional)</span>
            </label>
            <input type="password" value={authHeader} onChange={(e) => setAuthHeader(e.target.value)}
              placeholder={isCloudProvider ? 'Credentials...' : 'Bearer ...'}
              className="w-full rounded-md border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-200 placeholder-gray-500 outline-none focus:border-green-500/50" />
          </div>
          <div>
            <label className="mb-1 block text-xs text-gray-400">Environment</label>
            <select value={env} onChange={(e) => setEnv(e.target.value)}
              className="w-full rounded-md border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-200 outline-none focus:border-green-500/50">
              <option value="production">Production</option>
              <option value="staging">Staging</option>
              <option value="development">Development</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs text-gray-400">Poll Interval (seconds)</label>
            <input type="number" value={pollInterval} onChange={(e) => setPollInterval(Number(e.target.value))}
              min={10} max={3600}
              className="w-full rounded-md border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-200 outline-none focus:border-green-500/50" />
          </div>
        </div>

        {isCloudProvider && (
          <div className="flex items-start gap-2 rounded-lg border border-blue-500/20 bg-blue-500/5 p-3">
            <Cloud size={14} className="mt-0.5 shrink-0 text-blue-400" />
            <p className="text-xs text-blue-300">
              {preset === 'aws_cloudwatch' && 'Sentinel will use the AWS SDK to poll CloudWatch Logs. Provide an IAM role ARN or access key with logs:GetLogEvents permission.'}
              {preset === 'azure_monitor' && 'Sentinel will query Azure Monitor Logs via the REST API. Provide a service principal with Log Analytics Reader role.'}
              {preset === 'gcp_logging' && 'Sentinel will use the Cloud Logging API to read log entries. Provide a service account JSON key with logging.logEntries.list permission.'}
            </p>
          </div>
        )}

        <FormActions submitting={submitting} onClose={onClose} label="Add Log Feed" />
      </form>
    </Card>
  );
}

function FormActions({
  submitting,
  onClose,
  label,
}: {
  submitting: boolean;
  onClose: () => void;
  label: string;
}) {
  return (
    <div className="flex items-center gap-3">
      <Button type="submit" size="sm" variant="primary" disabled={submitting}>
        {submitting ? <Spinner size="sm" /> : <Plus size={14} />}
        {label}
      </Button>
      <Button type="button" size="sm" variant="secondary" onClick={onClose}>
        Cancel
      </Button>
    </div>
  );
}
