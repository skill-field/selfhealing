import { useState } from 'react';
import {
  Sparkles,
  Plus,
  X,
  ChevronDown,
  ChevronUp,
  Clock,
  CheckCircle2,
  XCircle,
  Send,
} from 'lucide-react';
import { Card } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Spinner } from '../ui/spinner';
import { EmptyState } from '../ui/empty-state';
import { DiffViewer } from '../fixes/diff-viewer';
import { useFeatures } from '../../hooks/use-features';
import {
  createFeature,
  generateFeature,
  approveFeature,
  rejectFeature,
} from '../../services/api';
import type { FeatureRequest } from '../../types';

const STATUS_CONFIG: Record<string, { label: string; badgeVariant: 'default' | 'medium' | 'low' | 'success' | 'critical' | 'info' | 'high' }> = {
  submitted: { label: 'Submitted', badgeVariant: 'default' },
  generating: { label: 'Generating', badgeVariant: 'medium' },
  generated: { label: 'Ready for Review', badgeVariant: 'low' },
  approved: { label: 'Approved', badgeVariant: 'success' },
  rejected: { label: 'Rejected', badgeVariant: 'critical' },
  deployed: { label: 'Deployed', badgeVariant: 'success' },
};

const PRIORITY_CONFIG: Record<string, { label: string; badgeVariant: 'default' | 'low' | 'medium' | 'high' | 'critical' }> = {
  low: { label: 'Low', badgeVariant: 'low' },
  medium: { label: 'Medium', badgeVariant: 'medium' },
  high: { label: 'High', badgeVariant: 'high' },
  critical: { label: 'Critical', badgeVariant: 'critical' },
};

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

function FeatureRequestForm({
  onSubmit,
  onClose,
}: {
  onSubmit: () => void;
  onClose: () => void;
}) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState('medium');
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !description.trim()) return;

    setSubmitting(true);
    setFormError(null);
    try {
      await createFeature(title.trim(), description.trim(), priority);
      setTitle('');
      setDescription('');
      setPriority('medium');
      onSubmit();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to create feature request');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Card className="border-amber-500/30">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="flex items-center gap-2 text-sm font-semibold text-gray-100">
            <Plus size={16} className="text-amber-400" />
            New Feature Request
          </h3>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-500 hover:text-gray-300 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        <div>
          <label htmlFor="feature-title" className="block text-xs font-medium text-gray-400 mb-1">
            Title <span className="text-red-400">*</span>
          </label>
          <input
            id="feature-title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            maxLength={100}
            placeholder="e.g., Add email notification for critical errors"
            className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500/50"
            required
          />
          <p className="mt-1 text-xs text-gray-600">{title.length}/100</p>
        </div>

        <div>
          <label htmlFor="feature-desc" className="block text-xs font-medium text-gray-400 mb-1">
            Description <span className="text-red-400">*</span>
          </label>
          <textarea
            id="feature-desc"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            maxLength={2000}
            rows={4}
            placeholder="Describe what you want the system to do..."
            className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 placeholder-gray-500 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500/50 resize-none"
            required
          />
          <p className="mt-1 text-xs text-gray-600">{description.length}/2000</p>
        </div>

        <div>
          <label htmlFor="feature-priority" className="block text-xs font-medium text-gray-400 mb-1">
            Priority
          </label>
          <select
            id="feature-priority"
            value={priority}
            onChange={(e) => setPriority(e.target.value)}
            className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500/50"
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </div>

        {formError && (
          <div className="flex items-center gap-2 rounded-lg bg-red-500/10 border border-red-500/20 px-3 py-2">
            <XCircle size={14} className="text-red-400 shrink-0" />
            <p className="text-xs text-red-400">{formError}</p>
          </div>
        )}

        <div className="flex justify-end">
          <Button type="submit" disabled={submitting || !title.trim() || !description.trim()}>
            {submitting ? <Spinner size="sm" /> : <Send size={14} />}
            Submit Feature Request
          </Button>
        </div>
      </form>
    </Card>
  );
}

function GeneratingOverlay() {
  return (
    <div className="flex flex-col items-center justify-center py-8 gap-3">
      <div className="relative">
        <Sparkles size={32} className="text-amber-400 animate-pulse" />
        <div className="absolute -inset-2 animate-ping opacity-20">
          <Sparkles size={48} className="text-amber-400" />
        </div>
      </div>
      <p className="text-sm text-amber-300 font-medium">Claude is designing your feature...</p>
      <p className="text-xs text-gray-500">This may take a minute</p>
    </div>
  );
}

function FeatureCard({
  feature,
  onGenerate,
  onApprove,
  onReject,
  actionLoading,
}: {
  feature: FeatureRequest;
  onGenerate: (id: string) => void;
  onApprove: (id: string, notes?: string) => void;
  onReject: (id: string, notes: string) => void;
  actionLoading: string | null;
}) {
  const [expanded, setExpanded] = useState(false);
  const [reviewNotes, setReviewNotes] = useState('');
  const config = STATUS_CONFIG[feature.status] ?? STATUS_CONFIG.submitted;
  const priorityConfig = PRIORITY_CONFIG[feature.priority] ?? PRIORITY_CONFIG.medium;
  const isLoading = actionLoading === feature.id;
  const isGenerating = feature.status === 'generating';

  const truncatedDesc =
    feature.description.length > 150
      ? feature.description.substring(0, 150) + '...'
      : feature.description;

  return (
    <Card className="hover:border-gray-700 transition-colors">
      {/* Card header */}
      <div
        className="cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 space-y-2">
            <div className="flex items-center gap-2 flex-wrap">
              <Badge variant={config.badgeVariant}>{config.label}</Badge>
              <Badge variant={priorityConfig.badgeVariant}>{priorityConfig.label}</Badge>
              {feature.model_used && (
                <span className="text-xs text-gray-600">{feature.model_used}</span>
              )}
            </div>
            <h4 className="text-sm font-semibold text-gray-100">{feature.title}</h4>
            {!expanded && (
              <p className="text-xs text-gray-400">{truncatedDesc}</p>
            )}
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <Clock size={12} />
              {formatTimestamp(feature.created_at)}
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {/* Inline action buttons (non-expanded) */}
            {!expanded && feature.status === 'submitted' && (
              <Button
                variant="secondary"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  onGenerate(feature.id);
                }}
                disabled={isLoading}
              >
                {isLoading ? <Spinner size="sm" /> : <Sparkles size={14} />}
                Generate
              </Button>
            )}
            {!expanded && feature.status === 'generated' && (
              <Button
                variant="secondary"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  setExpanded(true);
                }}
              >
                Review Code
              </Button>
            )}
            {expanded ? (
              <ChevronUp size={16} className="text-gray-500" />
            ) : (
              <ChevronDown size={16} className="text-gray-500" />
            )}
          </div>
        </div>
      </div>

      {/* Expanded detail view */}
      {expanded && (
        <div className="mt-4 space-y-4 border-t border-gray-800 pt-4">
          {/* Full description */}
          <div>
            <h5 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
              Description
            </h5>
            <p className="text-sm text-gray-300 whitespace-pre-wrap">{feature.description}</p>
          </div>

          {/* Generating state */}
          {isGenerating && <GeneratingOverlay />}

          {/* AI Explanation */}
          {feature.explanation && (
            <div>
              <h5 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                AI Explanation
              </h5>
              <div className="rounded-lg border border-gray-800 bg-gray-800/50 p-3">
                <p className="text-sm text-gray-300 whitespace-pre-wrap">{feature.explanation}</p>
              </div>
            </div>
          )}

          {/* Generated code diff */}
          {feature.generated_diff && (
            <div>
              <h5 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                Generated Code
              </h5>
              <DiffViewer diff={feature.generated_diff} />
            </div>
          )}

          {/* Generated code (if no diff, show raw code) */}
          {!feature.generated_diff && feature.generated_code && (
            <div>
              <h5 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                Generated Code
              </h5>
              <div className="rounded-lg border border-gray-800 bg-[#1a1a2e] p-4 overflow-x-auto">
                <pre className="text-xs text-gray-300 font-mono whitespace-pre-wrap">
                  {feature.generated_code}
                </pre>
              </div>
            </div>
          )}

          {/* Reviewer notes (if already reviewed) */}
          {feature.reviewer_notes && (
            <div>
              <h5 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                Reviewer Notes
              </h5>
              <p className="text-sm text-gray-400 italic">{feature.reviewer_notes}</p>
            </div>
          )}

          {/* PR link */}
          {feature.pr_url && (
            <a
              href={feature.pr_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300"
            >
              View Pull Request
              <span className="text-blue-500">&#x2197;</span>
            </a>
          )}

          {/* Actions */}
          <div className="flex items-end gap-3 flex-wrap">
            {feature.status === 'submitted' && (
              <Button
                variant="primary"
                size="sm"
                onClick={() => onGenerate(feature.id)}
                disabled={isLoading}
              >
                {isLoading ? <Spinner size="sm" /> : <Sparkles size={14} />}
                Generate Implementation
              </Button>
            )}

            {feature.status === 'generated' && (
              <>
                <div className="flex-1 min-w-[200px]">
                  <label className="block text-xs text-gray-500 mb-1">Notes (optional for approve, required for reject)</label>
                  <input
                    type="text"
                    value={reviewNotes}
                    onChange={(e) => setReviewNotes(e.target.value)}
                    placeholder="Add review notes..."
                    className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-1.5 text-xs text-gray-100 placeholder-gray-500 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500/50"
                    onClick={(e) => e.stopPropagation()}
                  />
                </div>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => {
                    onApprove(feature.id, reviewNotes || undefined);
                    setReviewNotes('');
                  }}
                  disabled={isLoading}
                  className="bg-green-600 hover:bg-green-500"
                >
                  {isLoading ? <Spinner size="sm" /> : <CheckCircle2 size={14} />}
                  Approve
                </Button>
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => {
                    if (!reviewNotes.trim()) {
                      alert('Please add notes explaining why this is rejected.');
                      return;
                    }
                    onReject(feature.id, reviewNotes);
                    setReviewNotes('');
                  }}
                  disabled={isLoading}
                >
                  {isLoading ? <Spinner size="sm" /> : <XCircle size={14} />}
                  Reject
                </Button>
              </>
            )}
          </div>
        </div>
      )}
    </Card>
  );
}

export function EvolvePage() {
  const { features, loading, error, refetch } = useFeatures();
  const [showForm, setShowForm] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const handleGenerate = async (featureId: string) => {
    setActionLoading(featureId);
    try {
      await generateFeature(featureId);
      refetch();
    } catch (err) {
      console.error('Failed to generate feature:', err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleApprove = async (featureId: string, notes?: string) => {
    setActionLoading(featureId);
    try {
      await approveFeature(featureId, notes);
      refetch();
    } catch (err) {
      console.error('Failed to approve feature:', err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (featureId: string, notes: string) => {
    setActionLoading(featureId);
    try {
      await rejectFeature(featureId, notes);
      refetch();
    } catch (err) {
      console.error('Failed to reject feature:', err);
    } finally {
      setActionLoading(null);
    }
  };

  // Stats
  const total = features.length;
  const generating = features.filter((f) => f.status === 'generating').length;
  const readyForReview = features.filter((f) => f.status === 'generated').length;
  const deployed = features.filter((f) => f.status === 'deployed').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <Sparkles size={28} className="text-amber-500" />
          <div>
            <h2 className="text-2xl font-bold text-gray-100">Feature Evolution</h2>
            <p className="mt-0.5 text-sm text-gray-400">
              AI-driven feature request analysis and code generation
            </p>
          </div>
        </div>
        {!showForm && (
          <Button onClick={() => setShowForm(true)}>
            <Plus size={16} />
            New Request
          </Button>
        )}
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Card className="text-center">
          <p className="text-2xl font-bold text-gray-100">{total}</p>
          <p className="text-xs text-gray-500 mt-1">Total Requests</p>
        </Card>
        <Card className="text-center">
          <p className="text-2xl font-bold text-yellow-400">{generating}</p>
          <p className="text-xs text-gray-500 mt-1">Generating</p>
        </Card>
        <Card className="text-center">
          <p className="text-2xl font-bold text-blue-400">{readyForReview}</p>
          <p className="text-xs text-gray-500 mt-1">Ready for Review</p>
        </Card>
        <Card className="text-center">
          <p className="text-2xl font-bold text-emerald-400">{deployed}</p>
          <p className="text-xs text-gray-500 mt-1">Deployed</p>
        </Card>
      </div>

      {/* Feature Request Form */}
      {showForm && (
        <FeatureRequestForm
          onSubmit={() => {
            refetch();
            setShowForm(false);
          }}
          onClose={() => setShowForm(false)}
        />
      )}

      {/* Loading / Error states */}
      {loading && features.length === 0 && (
        <div className="flex items-center justify-center py-16">
          <Spinner size="lg" className="text-amber-500" />
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

      {/* Feature List */}
      {!loading && features.length === 0 && !error && (
        <EmptyState
          icon={<Sparkles size={48} />}
          title="No feature requests yet"
          description="Submit an idea to let AI build it for you."
          action={
            !showForm ? (
              <Button onClick={() => setShowForm(true)}>
                <Plus size={16} />
                Submit a Feature Request
              </Button>
            ) : undefined
          }
        />
      )}

      {features.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-gray-300">All Feature Requests</h3>
          {features.map((feature) => (
            <FeatureCard
              key={feature.id}
              feature={feature}
              onGenerate={handleGenerate}
              onApprove={handleApprove}
              onReject={handleReject}
              actionLoading={actionLoading}
            />
          ))}
        </div>
      )}
    </div>
  );
}
