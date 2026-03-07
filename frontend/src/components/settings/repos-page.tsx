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
} from 'lucide-react';
import { Card } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Spinner } from '../ui/spinner';
import { EmptyState } from '../ui/empty-state';

const BASE = '/api/v1';

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

export function ReposPage() {
  const [repos, setRepos] = useState<MonitoredRepo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Form state
  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [token, setToken] = useState('');

  const fetchRepos = useCallback(() => {
    setLoading(true);
    fetch(`${BASE}/repos`)
      .then((r) => r.json())
      .then((d) => setRepos(d.repos ?? []))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchRepos();
  }, [fetchRepos]);

  const handleAdd = async (e: React.FormEvent) => {
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
      setName('');
      setSlug('');
      setToken('');
      setShowForm(false);
      fetchRepos();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add repo');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Remove this repository?')) return;
    await fetch(`${BASE}/repos/${id}`, { method: 'DELETE' });
    fetchRepos();
  };

  const handleToggle = async (id: string, currentActive: boolean) => {
    await fetch(`${BASE}/repos/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_active: !currentActive }),
    });
    fetchRepos();
  };

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
            Add GitHub repositories for Sentinel to scan and monitor using Cloudera AI
          </p>
        </div>
        <Button
          size="sm"
          variant="primary"
          onClick={() => setShowForm(!showForm)}
          className="border-cyan-500/30"
        >
          <Plus size={14} />
          Add App
        </Button>
      </div>

      {/* Add Form */}
      {showForm && (
        <Card className="border-cyan-500/30">
          <form onSubmit={handleAdd} className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-200">Add New Repository</h3>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-xs text-gray-400">Display Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="My App"
                  required
                  className="w-full rounded-md border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-200 placeholder-gray-500 outline-none focus:border-cyan-500/50"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs text-gray-400">
                  GitHub Repo <span className="text-gray-600">(owner/repo)</span>
                </label>
                <input
                  type="text"
                  value={slug}
                  onChange={(e) => setSlug(e.target.value)}
                  placeholder="acme/my-app"
                  required
                  className="w-full rounded-md border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-200 placeholder-gray-500 outline-none focus:border-cyan-500/50"
                />
              </div>
            </div>
            <div>
              <label className="mb-1 block text-xs text-gray-400">
                GitHub Token <span className="text-gray-600">(optional — uses global token if empty)</span>
              </label>
              <input
                type="password"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="ghp_..."
                className="w-full rounded-md border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-200 placeholder-gray-500 outline-none focus:border-cyan-500/50"
              />
            </div>
            <div className="flex items-center gap-3">
              <Button type="submit" size="sm" variant="primary" disabled={submitting}>
                {submitting ? <Spinner size="sm" /> : <Plus size={14} />}
                Add Repository
              </Button>
              <Button
                type="button"
                size="sm"
                variant="secondary"
                onClick={() => setShowForm(false)}
              >
                Cancel
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* Error */}
      {error && (
        <Card className="border-red-500/30">
          <p className="text-sm text-red-400">{error}</p>
        </Card>
      )}

      {/* Loading */}
      {loading && repos.length === 0 && (
        <div className="flex justify-center py-16">
          <Spinner size="lg" />
        </div>
      )}

      {/* Empty */}
      {!loading && repos.length === 0 && (
        <EmptyState
          icon={<GitBranch size={48} />}
          title="No repositories configured"
          description="Add a GitHub repository to start monitoring with Cloudera AI."
          action={
            <Button size="sm" variant="primary" onClick={() => setShowForm(true)}>
              <Plus size={14} />
              Add Your First App
            </Button>
          }
        />
      )}

      {/* Repo Cards */}
      <div className="space-y-3">
        {repos.map((repo) => (
          <Card
            key={repo.id}
            className={`transition-colors ${repo.is_active ? 'border-gray-800' : 'border-gray-800/50 opacity-60'}`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-lg ${
                    repo.is_active ? 'bg-cyan-500/10' : 'bg-gray-800'
                  }`}
                >
                  <Github size={20} className={repo.is_active ? 'text-cyan-400' : 'text-gray-600'} />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-semibold text-gray-100">{repo.display_name}</h3>
                    <Badge variant={repo.is_active ? 'success' : 'default'}>
                      {repo.is_active ? 'Active' : 'Paused'}
                    </Badge>
                    {repo.has_token && (
                      <Badge variant="info">
                        <Shield size={10} className="mr-0.5" />
                        Token
                      </Badge>
                    )}
                  </div>
                  <p className="mt-0.5 font-mono text-xs text-gray-500">{repo.repo_slug}</p>
                  {repo.scan_paths.length > 0 && (
                    <p className="mt-0.5 text-xs text-gray-600">
                      {repo.scan_paths.length} scan path{repo.scan_paths.length !== 1 ? 's' : ''} configured
                    </p>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => handleToggle(repo.id, repo.is_active)}
                  title={repo.is_active ? 'Pause monitoring' : 'Resume monitoring'}
                >
                  {repo.is_active ? <PowerOff size={14} /> : <Power size={14} />}
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => handleDelete(repo.id)}
                  className="text-red-400 hover:bg-red-500/10"
                  title="Remove repository"
                >
                  <Trash2 size={14} />
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
