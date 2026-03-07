import { useState, useEffect } from 'react';
import {
  Cpu,
  Play,
  Clock,
  Box,
  FlaskConical,
  AppWindow,
  Zap,
  RefreshCw,
} from 'lucide-react';
import { Card } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Spinner } from '../ui/spinner';

const BASE = '/api/v1';

interface CmlJob {
  id?: string;
  name: string;
  script: string;
  schedule: string;
  status: string;
}

interface CmlModel {
  id?: string;
  name: string;
  description?: string;
  status: string;
  endpoint?: string;
  function?: string;
}

interface CmlExperiment {
  id?: string;
  name: string;
  status: string;
}

interface CmlApp {
  id?: string;
  name: string;
  subdomain?: string;
  status: string;
}

interface CmlStatus {
  is_cml: boolean;
  project_id: string | null;
  jobs: CmlJob[];
  models: CmlModel[];
  experiments: CmlExperiment[];
  applications: CmlApp[];
}

export function CmlPage() {
  const [data, setData] = useState<CmlStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [triggeringJob, setTriggeringJob] = useState<string | null>(null);

  const fetchStatus = () => {
    setLoading(true);
    fetch(`${BASE}/cml/status`)
      .then((r) => r.json())
      .then((d) => setData(d))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleTriggerJob = async (jobId: string) => {
    setTriggeringJob(jobId);
    try {
      await fetch(`${BASE}/cml/jobs/${jobId}/run`, { method: 'POST' });
    } catch {
      // silently fail
    } finally {
      setTriggeringJob(null);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="flex items-center gap-3 text-2xl font-bold">
            <Cpu className="text-cyan-400" size={28} />
            <span>Cloudera AI Platform</span>
          </h2>
          <p className="mt-1 text-sm text-gray-400">
            CML capabilities powering Sentinel — Jobs, Models, Experiments & Applications
          </p>
        </div>
        <Button size="sm" variant="secondary" onClick={fetchStatus}>
          <RefreshCw size={14} />
          Refresh
        </Button>
      </div>

      {/* Platform Status */}
      <Card className="border-cyan-500/20">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-cyan-500/10">
            <Zap size={20} className="text-cyan-400" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-100">Platform Status</h3>
            <p className="text-xs text-gray-400">
              {data?.is_cml ? (
                <>
                  Running on Cloudera Machine Learning
                  {data.project_id && (
                    <span className="ml-2 font-mono text-gray-500">
                      Project: {data.project_id}
                    </span>
                  )}
                </>
              ) : (
                'Cloudera AI capabilities configured (static mode)'
              )}
            </p>
          </div>
          <Badge variant={data?.is_cml ? 'success' : 'info'} className="ml-auto">
            {data?.is_cml ? 'Connected' : 'Configured'}
          </Badge>
        </div>
      </Card>

      {/* Jobs */}
      <div>
        <h3 className="mb-3 flex items-center gap-2 text-lg font-semibold text-gray-200">
          <Clock size={18} className="text-amber-400" />
          CML Jobs
          <Badge variant="default">{data?.jobs?.length || 0}</Badge>
        </h3>
        <div className="space-y-2">
          {data?.jobs?.map((job, i) => (
            <Card key={job.id || i} className="border-gray-800">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-500/10">
                    <Play size={16} className="text-amber-400" />
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-100">{job.name}</h4>
                    <div className="mt-0.5 flex items-center gap-3 text-xs text-gray-500">
                      <span className="font-mono">{job.script}</span>
                      <span>
                        {job.schedule === 'manual' ? 'Manual trigger' : `Cron: ${job.schedule}`}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={job.schedule !== 'manual' ? 'success' : 'default'}>
                    {job.schedule !== 'manual' ? 'Scheduled' : 'Manual'}
                  </Badge>
                  {job.id && (
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => handleTriggerJob(job.id!)}
                      disabled={triggeringJob === job.id}
                      title="Run now"
                    >
                      {triggeringJob === job.id ? (
                        <Spinner size="sm" />
                      ) : (
                        <Play size={12} />
                      )}
                    </Button>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* Models */}
      <div>
        <h3 className="mb-3 flex items-center gap-2 text-lg font-semibold text-gray-200">
          <Box size={18} className="text-purple-400" />
          CML Models
          <Badge variant="default">{data?.models?.length || 0}</Badge>
        </h3>
        <div className="space-y-2">
          {data?.models?.map((model, i) => (
            <Card key={model.id || i} className="border-gray-800">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-purple-500/10">
                    <Box size={16} className="text-purple-400" />
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-100">{model.name}</h4>
                    {model.description && (
                      <p className="mt-0.5 text-xs text-gray-500">{model.description}</p>
                    )}
                  </div>
                </div>
                <Badge
                  variant={
                    model.status === 'deployed'
                      ? 'success'
                      : model.status === 'building'
                        ? 'info'
                        : 'default'
                  }
                >
                  {model.status}
                </Badge>
              </div>
            </Card>
          ))}
          {(!data?.models || data.models.length === 0) && (
            <p className="text-sm text-gray-500">No models deployed</p>
          )}
        </div>
      </div>

      {/* Experiments */}
      <div>
        <h3 className="mb-3 flex items-center gap-2 text-lg font-semibold text-gray-200">
          <FlaskConical size={18} className="text-green-400" />
          CML Experiments
          <Badge variant="default">{data?.experiments?.length || 0}</Badge>
        </h3>
        <div className="space-y-2">
          {data?.experiments?.map((exp, i) => (
            <Card key={exp.id || i} className="border-gray-800">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-green-500/10">
                    <FlaskConical size={16} className="text-green-400" />
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-100">{exp.name}</h4>
                  </div>
                </div>
                <Badge variant="success">{exp.status}</Badge>
              </div>
            </Card>
          ))}
          {(!data?.experiments || data.experiments.length === 0) && (
            <p className="text-sm text-gray-500">No experiments configured</p>
          )}
        </div>
      </div>

      {/* Applications */}
      {data?.applications && data.applications.length > 0 && (
        <div>
          <h3 className="mb-3 flex items-center gap-2 text-lg font-semibold text-gray-200">
            <AppWindow size={18} className="text-cyan-400" />
            CML Applications
            <Badge variant="default">{data.applications.length}</Badge>
          </h3>
          <div className="space-y-2">
            {data.applications.map((app, i) => (
              <Card key={app.id || i} className="border-gray-800">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-500/10">
                      <AppWindow size={16} className="text-cyan-400" />
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-gray-100">{app.name}</h4>
                      {app.subdomain && (
                        <p className="mt-0.5 font-mono text-xs text-gray-500">{app.subdomain}</p>
                      )}
                    </div>
                  </div>
                  <Badge
                    variant={app.status === 'APPLICATION_RUNNING' ? 'success' : 'default'}
                  >
                    {app.status === 'APPLICATION_RUNNING' ? 'Running' : app.status}
                  </Badge>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Architecture Info */}
      <Card title="Cloudera AI Architecture" className="border-gray-800">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="rounded-lg bg-gray-800/50 p-3">
            <h4 className="text-xs font-semibold uppercase text-cyan-400">AI Engine</h4>
            <p className="mt-1 text-sm text-gray-200">Claude via AWS Bedrock</p>
            <p className="text-xs text-gray-500">claude-sonnet-4-20250514</p>
          </div>
          <div className="rounded-lg bg-gray-800/50 p-3">
            <h4 className="text-xs font-semibold uppercase text-purple-400">Runtime</h4>
            <p className="mt-1 text-sm text-gray-200">Python 3.11 PBJ</p>
            <p className="text-xs text-gray-500">CML Workbench Standard</p>
          </div>
          <div className="rounded-lg bg-gray-800/50 p-3">
            <h4 className="text-xs font-semibold uppercase text-green-400">Pipeline</h4>
            <p className="mt-1 text-sm text-gray-200">Watch &rarr; Think &rarr; Heal &rarr; Verify</p>
            <p className="text-xs text-gray-500">Automated self-healing loop</p>
          </div>
        </div>
      </Card>
    </div>
  );
}
