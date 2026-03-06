import { useState } from 'react';
import {
  ShieldCheck,
  ExternalLink,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowRight,
  Rocket,
  TestTube2,
  Server,
  Globe,
} from 'lucide-react';
import { Card } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Spinner } from '../ui/spinner';
import { EmptyState } from '../ui/empty-state';
import { useDeployments } from '../../hooks/use-deployments';
import { promoteDeployment } from '../../services/api';
import type { Deployment } from '../../types';

const STATUS_CONFIG: Record<string, { label: string; color: string; badgeVariant: 'default' | 'medium' | 'low' | 'info' | 'success' | 'critical' | 'high' }> = {
  pending: { label: 'Pending', color: 'text-gray-400', badgeVariant: 'default' },
  deploying: { label: 'Deploying', color: 'text-yellow-400', badgeVariant: 'medium' },
  deployed: { label: 'Deployed to Staging', color: 'text-blue-400', badgeVariant: 'low' },
  testing: { label: 'Testing', color: 'text-purple-400', badgeVariant: 'info' },
  tests_passed: { label: 'Tests Passed', color: 'text-green-400', badgeVariant: 'success' },
  promoted: { label: 'Live in Production', color: 'text-emerald-400', badgeVariant: 'success' },
  failed: { label: 'Failed', color: 'text-red-400', badgeVariant: 'critical' },
  rolled_back: { label: 'Rolled Back', color: 'text-orange-400', badgeVariant: 'high' },
};

const PIPELINE_STAGES = [
  { key: 'pending', label: 'Fix Approved', icon: CheckCircle2, color: 'bg-gray-600' },
  { key: 'deploying', label: 'Deploy to Staging', icon: Server, color: 'bg-yellow-600' },
  { key: 'testing', label: 'Testing', icon: TestTube2, color: 'bg-purple-600' },
  { key: 'tests_passed', label: 'Tests Passed', icon: CheckCircle2, color: 'bg-green-600' },
  { key: 'promoted', label: 'Production', icon: Globe, color: 'bg-emerald-600' },
];

function getStageIndex(status: string): number {
  const map: Record<string, number> = {
    pending: 0,
    deploying: 1,
    deployed: 1,
    testing: 2,
    tests_passed: 3,
    promoted: 4,
    failed: -1,
    rolled_back: -1,
  };
  return map[status] ?? -1;
}

function formatTimestamp(ts: string | null | undefined): string {
  if (!ts) return '--';
  const d = new Date(ts);
  return d.toLocaleString('en-AU', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });
}

function PipelineVisualization({ activeDeployment }: { activeDeployment?: Deployment }) {
  const activeStage = activeDeployment ? getStageIndex(activeDeployment.status) : -1;
  const isFailed = activeDeployment?.status === 'failed' || activeDeployment?.status === 'rolled_back';

  return (
    <Card className="overflow-hidden">
      <div className="mb-3 flex items-center gap-2">
        <Rocket size={16} className="text-blue-400" />
        <h3 className="text-sm font-semibold text-gray-100">Deployment Pipeline</h3>
      </div>
      <div className="flex items-center justify-between gap-1 px-2 py-4">
        {PIPELINE_STAGES.map((stage, index) => {
          const Icon = stage.icon;
          const isCompleted = activeStage > index;
          const isActive = activeStage === index;
          const isUpcoming = activeStage < index;

          let nodeColor = 'bg-gray-700/50 border-gray-600';
          let textColor = 'text-gray-500';
          let iconColor = 'text-gray-500';

          if (isFailed && activeStage === index) {
            nodeColor = 'bg-red-500/20 border-red-500 shadow-red-500/30 shadow-lg';
            textColor = 'text-red-400';
            iconColor = 'text-red-400';
          } else if (isCompleted) {
            nodeColor = 'bg-green-500/20 border-green-500/50';
            textColor = 'text-green-400';
            iconColor = 'text-green-400';
          } else if (isActive) {
            nodeColor = `${stage.color}/20 border-blue-400 shadow-blue-500/30 shadow-lg`;
            textColor = 'text-blue-300';
            iconColor = 'text-blue-400';
          }

          return (
            <div key={stage.key} className="flex items-center gap-1 flex-1">
              <div className="flex flex-col items-center gap-2 flex-1">
                <div
                  className={`flex h-12 w-12 items-center justify-center rounded-full border-2 transition-all duration-500 ${nodeColor} ${
                    isActive && !isFailed ? 'animate-pulse' : ''
                  }`}
                >
                  {isCompleted ? (
                    <CheckCircle2 size={20} className="text-green-400" />
                  ) : (
                    <Icon size={20} className={iconColor} />
                  )}
                </div>
                <span className={`text-xs font-medium text-center leading-tight ${textColor}`}>
                  {stage.label}
                </span>
              </div>
              {index < PIPELINE_STAGES.length - 1 && (
                <div className="flex items-center self-start mt-5 -mx-1">
                  <div
                    className={`h-0.5 w-6 transition-colors duration-500 ${
                      isCompleted || (isActive && !isUpcoming) ? 'bg-green-500/50' : 'bg-gray-700'
                    }`}
                  />
                  <ArrowRight
                    size={14}
                    className={`shrink-0 transition-colors duration-500 ${
                      isCompleted ? 'text-green-500/50' : 'text-gray-700'
                    }`}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
      {!activeDeployment && (
        <p className="text-center text-xs text-gray-500 pb-2">
          No active deployment. Approve a fix to start the pipeline.
        </p>
      )}
      {isFailed && activeDeployment && (
        <p className="text-center text-xs text-red-400 pb-2">
          Deployment {activeDeployment.status === 'failed' ? 'failed' : 'rolled back'} at stage:{' '}
          {PIPELINE_STAGES[activeStage]?.label ?? activeDeployment.status}
        </p>
      )}
    </Card>
  );
}

function DeploymentCard({
  deployment,
  onPromote,
  promoting,
}: {
  deployment: Deployment;
  onPromote: (id: string) => void;
  promoting: boolean;
}) {
  const config = STATUS_CONFIG[deployment.status] ?? STATUS_CONFIG.pending;
  const canPromote = deployment.status === 'deployed' || deployment.status === 'tests_passed';

  return (
    <Card className="hover:border-gray-700 transition-colors">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex-1 space-y-2">
          <div className="flex items-center gap-3 flex-wrap">
            <Badge variant={config.badgeVariant}>{config.label}</Badge>
            <Badge variant={deployment.environment === 'production' ? 'success' : 'info'}>
              {deployment.environment}
            </Badge>
          </div>

          <div className="space-y-1 text-sm">
            <p className="text-gray-300">
              <span className="text-gray-500">Fix ID:</span>{' '}
              <span className="font-mono text-xs">{deployment.fix_id}</span>
            </p>
            {deployment.commit_sha && (
              <p className="text-gray-300">
                <span className="text-gray-500">Commit:</span>{' '}
                <span className="font-mono text-xs">{deployment.commit_sha.substring(0, 8)}</span>
              </p>
            )}
            <div className="flex items-center gap-4 text-xs text-gray-500">
              <span className="flex items-center gap-1">
                <Clock size={12} />
                Created: {formatTimestamp(deployment.created_at)}
              </span>
              {deployment.promoted_at && (
                <span className="flex items-center gap-1">
                  <Globe size={12} />
                  Promoted: {formatTimestamp(deployment.promoted_at)}
                </span>
              )}
            </div>
          </div>

          {deployment.test_results && (
            <div className="mt-2">
              <p className="text-xs text-gray-500">Test Results:</p>
              <p className="text-xs text-gray-400 font-mono mt-0.5 whitespace-pre-wrap">
                {typeof deployment.test_results === 'string'
                  ? deployment.test_results
                  : JSON.stringify(deployment.test_results, null, 2)}
              </p>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {deployment.pr_url && (
            <a
              href={deployment.pr_url}
              target="_blank"
              rel="noopener noreferrer"
            >
              <Button variant="secondary" size="sm">
                <ExternalLink size={14} />
                View PR
              </Button>
            </a>
          )}
          {canPromote && (
            <Button
              variant="primary"
              size="sm"
              onClick={() => onPromote(deployment.id)}
              disabled={promoting}
            >
              {promoting ? <Spinner size="sm" /> : <Rocket size={14} />}
              Promote to Production
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
}

export function VerifyPage() {
  const { deployments, loading, error, refetch } = useDeployments();
  const [promotingId, setPromotingId] = useState<string | null>(null);

  const handlePromote = async (deploymentId: string) => {
    setPromotingId(deploymentId);
    try {
      await promoteDeployment(deploymentId);
      refetch();
    } catch (err) {
      console.error('Failed to promote deployment:', err);
    } finally {
      setPromotingId(null);
    }
  };

  // Stats
  const total = deployments.length;
  const active = deployments.filter(
    (d) => d.status === 'deploying' || d.status === 'testing',
  ).length;
  const successful = deployments.filter(
    (d) => d.status === 'promoted' || d.status === 'tests_passed',
  ).length;
  const failed = deployments.filter((d) => d.status === 'failed').length;

  // Find the most recent active deployment for the pipeline visualization
  const activeDeployment = deployments.find(
    (d) =>
      d.status === 'deploying' ||
      d.status === 'deployed' ||
      d.status === 'testing' ||
      d.status === 'tests_passed',
  ) ?? deployments[0];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3">
          <ShieldCheck size={28} className="text-blue-500" />
          <div>
            <h2 className="text-2xl font-bold text-gray-100">Deployment Verification</h2>
            <p className="mt-0.5 text-sm text-gray-400">
              Automated staging deployment, testing, and promotion pipeline
            </p>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Card className="text-center">
          <p className="text-2xl font-bold text-gray-100">{total}</p>
          <p className="text-xs text-gray-500 mt-1">Total Deployments</p>
        </Card>
        <Card className="text-center">
          <p className="text-2xl font-bold text-yellow-400">{active}</p>
          <p className="text-xs text-gray-500 mt-1">Active</p>
        </Card>
        <Card className="text-center">
          <p className="text-2xl font-bold text-green-400">{successful}</p>
          <p className="text-xs text-gray-500 mt-1">Successful</p>
        </Card>
        <Card className="text-center">
          <p className="text-2xl font-bold text-red-400">{failed}</p>
          <p className="text-xs text-gray-500 mt-1">Failed</p>
        </Card>
      </div>

      {/* Pipeline Visualization */}
      <PipelineVisualization activeDeployment={activeDeployment} />

      {/* Loading / Error states */}
      {loading && deployments.length === 0 && (
        <div className="flex items-center justify-center py-16">
          <Spinner size="lg" className="text-blue-500" />
        </div>
      )}

      {error && (
        <Card className="border-red-500/30">
          <div className="flex items-center gap-2 text-red-400">
            <XCircle size={16} />
            <p className="text-sm">{error}</p>
          </div>
        </Card>
      )}

      {/* Deployment List */}
      {!loading && deployments.length === 0 && !error && (
        <EmptyState
          icon={<ShieldCheck size={48} />}
          title="No deployments yet"
          description="Approve a fix from the Heal module to start deploying."
        />
      )}

      {deployments.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-gray-300">All Deployments</h3>
          {deployments.map((deployment) => (
            <DeploymentCard
              key={deployment.id}
              deployment={deployment}
              onPromote={handlePromote}
              promoting={promotingId === deployment.id}
            />
          ))}
        </div>
      )}
    </div>
  );
}
