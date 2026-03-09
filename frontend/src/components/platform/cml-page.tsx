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
  Brain,
  ArrowRight,
  Eye,
  Wrench,
  Shield,
  Sparkles,
  Database,
  GitBranch,
  BarChart3,
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
  type?: string;
}

interface CmlExperiment {
  id?: string;
  name: string;
  status: string;
  description?: string;
}

interface CmlApp {
  id?: string;
  name: string;
  subdomain?: string;
  status: string;
}

interface TrainingReport {
  category?: { accuracy?: number; f1_macro?: number; model_type?: string; samples?: number };
  severity?: { accuracy?: number; f1_macro?: number; model_type?: string };
  timestamp?: string;
  samples?: number;
}

interface MlStatus {
  classifier_trained: boolean;
  training_report: TrainingReport | null;
}

interface CmlStatus {
  is_cml: boolean;
  project_id: string | null;
  jobs: CmlJob[];
  models: CmlModel[];
  experiments: CmlExperiment[];
  applications: CmlApp[];
  ml_status?: MlStatus;
}

export function CmlPage() {
  const [data, setData] = useState<CmlStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [triggeringJob, setTriggeringJob] = useState<string | null>(null);
  const [training, setTraining] = useState(false);
  const [trainResult, setTrainResult] = useState<string | null>(null);

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

  const handleTrainClassifier = async () => {
    setTraining(true);
    setTrainResult(null);
    try {
      const res = await fetch(`${BASE}/cml/train-classifier`, { method: 'POST' });
      const result = await res.json();
      if (result.status === 'ok') {
        setTrainResult(`Trained on ${result.samples} samples. Category: ${(result.category_accuracy * 100).toFixed(1)}%, Severity: ${(result.severity_accuracy * 100).toFixed(1)}%`);
        fetchStatus();
      } else {
        setTrainResult(`Error: ${result.message}`);
      }
    } catch (e) {
      setTrainResult('Training failed');
    } finally {
      setTraining(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner size="lg" />
      </div>
    );
  }

  const report = data?.ml_status?.training_report;

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

      {/* Platform Architecture Diagram */}
      <Card title="Platform Architecture" description="How Cloudera AI services power the self-healing pipeline">
        <div className="relative overflow-x-auto">
          {/* Pipeline Flow */}
          <div className="flex items-center justify-between gap-1 py-4 px-2 min-w-[700px]">
            {[
              { name: 'Watch', icon: Eye, color: '#06b6d4', service: 'CML Jobs', detail: 'Scheduled scans' },
              { name: 'Think', icon: Brain, color: '#a855f7', service: 'CML Model', detail: 'ML classifier' },
              { name: 'Heal', icon: Wrench, color: '#22c55e', service: 'AWS Bedrock', detail: 'Claude Sonnet' },
              { name: 'Verify', icon: Shield, color: '#3b82f6', service: 'GitHub API', detail: 'PR creation' },
              { name: 'Evolve', icon: Sparkles, color: '#f59e0b', service: 'AWS Bedrock', detail: 'Claude Sonnet' },
            ].map((stage, i) => (
              <div key={stage.name} className="flex items-center gap-1">
                <div className="flex flex-col items-center gap-1.5">
                  <div
                    className="flex h-14 w-14 items-center justify-center rounded-xl border-2"
                    style={{ borderColor: stage.color, backgroundColor: `${stage.color}15` }}
                  >
                    <stage.icon size={24} style={{ color: stage.color }} />
                  </div>
                  <p className="text-xs font-bold" style={{ color: stage.color }}>{stage.name}</p>
                  <div className="rounded bg-gray-800 px-2 py-0.5 text-center">
                    <p className="text-[10px] font-medium text-gray-300">{stage.service}</p>
                    <p className="text-[9px] text-gray-500">{stage.detail}</p>
                  </div>
                </div>
                {i < 4 && <ArrowRight size={18} className="mx-1 text-gray-600 flex-shrink-0" />}
              </div>
            ))}
          </div>

          {/* Supporting Services */}
          <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {[
              { name: 'CML Experiments', icon: FlaskConical, color: 'text-green-400', bg: 'bg-green-500/10', desc: 'MLflow tracking' },
              { name: 'SQLite + WAL', icon: Database, color: 'text-blue-400', bg: 'bg-blue-500/10', desc: 'Persistent storage' },
              { name: 'GitHub API', icon: GitBranch, color: 'text-gray-400', bg: 'bg-gray-500/10', desc: 'Code & PRs' },
              { name: 'SSE Events', icon: BarChart3, color: 'text-amber-400', bg: 'bg-amber-500/10', desc: 'Real-time updates' },
            ].map((svc) => (
              <div key={svc.name} className="flex items-center gap-2 rounded-lg border border-gray-800 p-2">
                <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${svc.bg}`}>
                  <svc.icon size={14} className={svc.color} />
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-200">{svc.name}</p>
                  <p className="text-[10px] text-gray-500">{svc.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </Card>

      {/* ML Classifier Status */}
      <Card
        title="ML Error Classifier"
        description="Trained scikit-learn model for error classification"
        className={data?.ml_status?.classifier_trained ? 'border-green-500/20' : 'border-amber-500/20'}
      >
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${
                data?.ml_status?.classifier_trained ? 'bg-green-500/10' : 'bg-amber-500/10'
              }`}>
                <Brain size={20} className={data?.ml_status?.classifier_trained ? 'text-green-400' : 'text-amber-400'} />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-gray-100">
                  {data?.ml_status?.classifier_trained ? 'Classifier Active' : 'Classifier Not Trained'}
                </h3>
                <p className="text-xs text-gray-400">
                  {data?.ml_status?.classifier_trained
                    ? 'Using trained ML models for error classification'
                    : 'Using rule-based fallback. Train the model to enable ML classification.'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={data?.ml_status?.classifier_trained ? 'success' : 'medium'}>
                {data?.ml_status?.classifier_trained ? 'Trained' : 'Rule-based'}
              </Badge>
              <Button size="sm" variant="secondary" onClick={handleTrainClassifier} disabled={training}>
                {training ? <Spinner size="sm" /> : <Play size={12} />}
                {training ? 'Training...' : 'Train Now'}
              </Button>
            </div>
          </div>

          {trainResult && (
            <div className={`rounded-lg border p-3 text-xs ${
              trainResult.startsWith('Error') ? 'border-red-500/30 bg-red-500/5 text-red-300' : 'border-green-500/30 bg-green-500/5 text-green-300'
            }`}>
              {trainResult}
            </div>
          )}

          {report && (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <div className="rounded-lg bg-gray-800/50 p-3 text-center">
                <p className="text-[10px] uppercase text-gray-500">Category Accuracy</p>
                <p className="text-xl font-bold text-green-400">
                  {report.category?.accuracy ? `${(report.category.accuracy * 100).toFixed(1)}%` : '--'}
                </p>
              </div>
              <div className="rounded-lg bg-gray-800/50 p-3 text-center">
                <p className="text-[10px] uppercase text-gray-500">Severity Accuracy</p>
                <p className="text-xl font-bold text-blue-400">
                  {report.severity?.accuracy ? `${(report.severity.accuracy * 100).toFixed(1)}%` : '--'}
                </p>
              </div>
              <div className="rounded-lg bg-gray-800/50 p-3 text-center">
                <p className="text-[10px] uppercase text-gray-500">Training Samples</p>
                <p className="text-xl font-bold text-gray-200">
                  {report.samples || report.category?.samples || '--'}
                </p>
              </div>
              <div className="rounded-lg bg-gray-800/50 p-3 text-center">
                <p className="text-[10px] uppercase text-gray-500">Model Type</p>
                <p className="text-sm font-bold text-purple-400">
                  {report.category?.model_type?.replace('_', ' ') || '--'}
                </p>
              </div>
            </div>
          )}
        </div>
      </Card>

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
                    {model.type && (
                      <span className="mt-0.5 inline-block rounded bg-gray-800 px-1.5 py-0.5 text-[10px] text-gray-400">
                        {model.type}
                      </span>
                    )}
                  </div>
                </div>
                <Badge
                  variant={
                    model.status === 'deployed'
                      ? 'success'
                      : model.status === 'building'
                        ? 'info'
                        : model.status === 'not_trained'
                          ? 'medium'
                          : 'default'
                  }
                >
                  {model.status === 'not_trained' ? 'Not Trained' : model.status}
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
          CML Experiments (MLflow)
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
                    {exp.description && (
                      <p className="mt-0.5 text-xs text-gray-500">{exp.description}</p>
                    )}
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
      <Card title="Cloudera AI Integration Details" className="border-gray-800">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="rounded-lg bg-gray-800/50 p-3">
            <h4 className="text-xs font-semibold uppercase text-cyan-400">AI Engine</h4>
            <p className="mt-1 text-sm text-gray-200">Claude via AWS Bedrock</p>
            <p className="text-xs text-gray-500">claude-sonnet-4-5</p>
          </div>
          <div className="rounded-lg bg-gray-800/50 p-3">
            <h4 className="text-xs font-semibold uppercase text-purple-400">ML Models</h4>
            <p className="mt-1 text-sm text-gray-200">scikit-learn classifiers</p>
            <p className="text-xs text-gray-500">GBM / Random Forest / Logistic Regression</p>
          </div>
          <div className="rounded-lg bg-gray-800/50 p-3">
            <h4 className="text-xs font-semibold uppercase text-green-400">Experiments</h4>
            <p className="mt-1 text-sm text-gray-200">MLflow Tracking</p>
            <p className="text-xs text-gray-500">Model comparison + metric logging</p>
          </div>
        </div>
      </Card>
    </div>
  );
}
