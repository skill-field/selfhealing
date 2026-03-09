import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Eye,
  Brain,
  Wrench,
  Shield,
  Sparkles,
  Clock,
  DollarSign,
  Users,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  Zap,
  Globe,
  GitBranch,
  TestTube2,
  MessageSquare,
  Code2,
  BarChart3,
  Cpu,
  Server,
  Activity,
  CheckCircle2,
  AlertTriangle,
  FileCode,
  GitPullRequest,
  Rocket,
  TrendingUp,
  Layers,
  CloudCog,
  Timer,
  ExternalLink,
  X,
} from 'lucide-react';

/* ─── Logo Components (real brand logos) ─── */

function SkillfieldLogo({ size = 48 }: { size?: number }) {
  return (
    <img
      src="https://skillfield.com.au/wp-content/uploads/2022/05/LogoSkillfield-Logo-FULL120W.png"
      alt="Skillfield"
      width={size}
      height={size}
      style={{ objectFit: 'contain' }}
    />
  );
}

function ClouderaLogo({ size = 48 }: { size?: number }) {
  return (
    <img
      src="https://www.cloudera.com/content/dam/www/marketing/images/logos/cloudera/cloudera-new-logo.png"
      alt="Cloudera"
      width={size * 2.5}
      height={size}
      style={{ objectFit: 'contain' }}
    />
  );
}

const TOTAL_SLIDES = 13;

const MODULE_DATA = [
  { name: 'WATCH', icon: Eye, color: '#06b6d4', desc: 'Real-time monitoring' },
  { name: 'THINK', icon: Brain, color: '#a855f7', desc: 'AI classification' },
  { name: 'HEAL', icon: Wrench, color: '#22c55e', desc: 'Auto-fix generation' },
  { name: 'VERIFY', icon: Shield, color: '#3b82f6', desc: 'Safe deployment' },
  { name: 'EVOLVE', icon: Sparkles, color: '#f59e0b', desc: 'Feature generation' },
];

/* ---- Slide background gradients ---- */
const SLIDE_GRADIENTS: Record<number, string> = {
  0: 'radial-gradient(ellipse at 30% 20%, rgba(6,182,212,0.08) 0%, transparent 60%), radial-gradient(ellipse at 70% 80%, rgba(168,85,247,0.06) 0%, transparent 60%)',
  1: 'radial-gradient(ellipse at 50% 30%, rgba(239,68,68,0.06) 0%, transparent 60%)',
  2: 'radial-gradient(ellipse at 40% 50%, rgba(6,182,212,0.06) 0%, transparent 50%), radial-gradient(ellipse at 60% 50%, rgba(34,197,94,0.06) 0%, transparent 50%)',
  3: 'radial-gradient(ellipse at 50% 40%, rgba(59,130,246,0.06) 0%, transparent 60%)',
  4: 'radial-gradient(ellipse at 30% 30%, rgba(249,115,22,0.08) 0%, transparent 50%), radial-gradient(ellipse at 70% 70%, rgba(6,182,212,0.06) 0%, transparent 50%)',
  5: 'radial-gradient(ellipse at 50% 50%, rgba(168,85,247,0.06) 0%, transparent 60%)',
  6: 'radial-gradient(ellipse at 50% 40%, rgba(6,182,212,0.08) 0%, transparent 60%)',
  7: 'radial-gradient(ellipse at 50% 40%, rgba(168,85,247,0.08) 0%, transparent 60%)',
  8: 'radial-gradient(ellipse at 50% 40%, rgba(34,197,94,0.08) 0%, transparent 60%)',
  9: 'radial-gradient(ellipse at 50% 40%, rgba(59,130,246,0.08) 0%, transparent 60%)',
  10: 'radial-gradient(ellipse at 50% 40%, rgba(245,158,11,0.08) 0%, transparent 60%)',
  11: 'radial-gradient(ellipse at 40% 30%, rgba(6,182,212,0.08) 0%, transparent 50%), radial-gradient(ellipse at 60% 70%, rgba(34,197,94,0.06) 0%, transparent 50%)',
  12: 'radial-gradient(ellipse at 50% 50%, rgba(6,182,212,0.06) 0%, transparent 40%), radial-gradient(ellipse at 30% 80%, rgba(168,85,247,0.06) 0%, transparent 40%)',
};

/* ─── Slide 1: Title ─── */

function SlideTitle() {
  return (
    <div className="flex h-full flex-col items-center justify-center text-center">
      {/* Cloudera badge */}
      <div className="mb-6 flex items-center gap-2 rounded-full border border-orange-500/30 bg-orange-500/10 px-5 py-2">
        <CloudCog size={18} className="text-orange-400" />
        <span className="text-sm font-semibold tracking-wide text-orange-300">
          Built on Cloudera AI
        </span>
      </div>

      {/* Logo area */}
      <div className="mb-6 flex items-center gap-6">
        <SkillfieldLogo size={56} />
        <Zap size={28} className="text-purple-400 animate-pulse" />
        <ClouderaLogo size={56} />
      </div>

      <h1 className="mb-4 text-6xl font-black tracking-tight md:text-7xl lg:text-8xl">
        <span className="bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-500 bg-clip-text text-transparent">
          Skillfield Sentinel
        </span>
      </h1>

      <p className="mb-3 text-xl font-medium text-gray-200 md:text-2xl">
        AI Self-Healing Software Platform
      </p>
      <p className="mb-8 max-w-xl text-base text-gray-400">
        Detect errors. Classify with AI. Generate fixes. Deploy safely. Evolve autonomously.
      </p>

      <div className="mb-8 h-px w-64 bg-gradient-to-r from-transparent via-cyan-500/40 to-transparent" />

      <p className="text-lg font-semibold text-gray-300">
        Cloudera Partner AI Hackathon 2026
      </p>
      <p className="mt-3 text-sm font-bold tracking-[0.2em] text-gray-500 uppercase">
        Skillfield Pty Ltd
      </p>

      {/* Module pills at bottom */}
      <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
        {MODULE_DATA.map((mod) => (
          <div
            key={mod.name}
            className="flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold"
            style={{
              backgroundColor: `${mod.color}15`,
              color: mod.color,
              border: `1px solid ${mod.color}30`,
            }}
          >
            <mod.icon size={12} />
            {mod.name}
          </div>
        ))}
      </div>
    </div>
  );
}

/* ─── Slide 2: Problem ─── */

function SlideProblem() {
  const pains = [
    {
      icon: Clock,
      title: '4+ hours to resolve',
      desc: 'Average P0 incident takes 4+ hours to detect, diagnose, and fix',
      stat: '4h+',
    },
    {
      icon: DollarSign,
      title: '$15,000+ per hour',
      desc: 'Average cost per hour of production downtime',
      stat: '$15K',
    },
    {
      icon: Users,
      title: '40% reactive work',
      desc: 'Engineers spend 40% of their time firefighting production issues',
      stat: '40%',
    },
  ];

  return (
    <div className="flex h-full flex-col items-center justify-center">
      <div className="mb-4 flex items-center gap-2 rounded-full border border-red-500/20 bg-red-500/10 px-4 py-1.5">
        <AlertTriangle size={14} className="text-red-400" />
        <span className="text-xs font-semibold tracking-wide text-red-400 uppercase">
          The Problem
        </span>
      </div>
      <h2 className="mb-2 text-5xl font-black text-white md:text-6xl">
        Every Production Error
      </h2>
      <h2 className="mb-4 text-5xl font-black md:text-6xl">
        <span className="bg-gradient-to-r from-red-400 to-orange-400 bg-clip-text text-transparent">
          Costs Money
        </span>
      </h2>
      <p className="mb-14 max-w-lg text-center text-gray-400">
        Traditional incident response is slow, expensive, and burns out your best engineers.
      </p>
      <div className="grid max-w-4xl grid-cols-1 gap-10 md:grid-cols-3">
        {pains.map(({ icon: Icon, title, desc, stat }) => (
          <div key={title} className="flex flex-col items-center text-center">
            <div className="mb-4 flex h-20 w-20 items-center justify-center rounded-2xl border border-red-500/20 bg-gradient-to-br from-red-500/10 to-orange-500/10">
              <Icon size={36} className="text-red-400" />
            </div>
            <p className="mb-1 text-3xl font-black text-red-400">{stat}</p>
            <h3 className="mb-2 text-lg font-bold text-white">{title}</h3>
            <p className="text-sm text-gray-400">{desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ─── Slide 3: Solution ─── */

function SlideSolution() {
  return (
    <div className="flex h-full flex-col items-center justify-center">
      <div className="mb-4 flex items-center gap-2 rounded-full border border-cyan-500/20 bg-cyan-500/10 px-4 py-1.5">
        <Sparkles size={14} className="text-cyan-400" />
        <span className="text-xs font-semibold tracking-wide text-cyan-400 uppercase">
          Our Answer
        </span>
      </div>
      <h2 className="mb-4 text-4xl font-black text-white md:text-5xl">
        What if your software could
      </h2>
      <h2 className="mb-6 text-5xl font-black md:text-6xl">
        <span className="bg-gradient-to-r from-cyan-400 to-green-400 bg-clip-text text-transparent">
          heal itself?
        </span>
      </h2>
      <p className="mb-14 max-w-xl text-center text-lg text-gray-400">
        A closed-loop AI platform that reduces MTTR from hours to minutes -- autonomously.
      </p>
      <div className="flex flex-wrap items-center justify-center gap-4">
        {MODULE_DATA.map((mod, i) => (
          <div key={mod.name} className="flex items-center gap-4">
            <div className="flex flex-col items-center gap-2">
              <div
                className="flex h-16 w-16 items-center justify-center rounded-full border-2 transition-transform hover:scale-110"
                style={{
                  borderColor: mod.color,
                  backgroundColor: `${mod.color}15`,
                  boxShadow: `0 0 20px ${mod.color}20`,
                }}
              >
                <mod.icon size={28} style={{ color: mod.color }} />
              </div>
              <span className="text-xs font-bold" style={{ color: mod.color }}>
                {mod.name}
              </span>
              <span className="text-xs text-gray-500">{mod.desc}</span>
            </div>
            {i < MODULE_DATA.length - 1 && (
              <ArrowRight size={22} className="text-gray-600" />
            )}
          </div>
        ))}
      </div>
      {/* Loop-back indicator */}
      <div className="mt-8 flex items-center gap-2 rounded-full border border-gray-700 bg-gray-800/50 px-5 py-2">
        <Activity size={14} className="text-cyan-400" />
        <span className="text-xs text-gray-400">
          Continuous closed loop -- every fix makes the system smarter
        </span>
      </div>
    </div>
  );
}

/* ─── Slide 4: Architecture / The Closed Loop ─── */

function SlideArchitecture() {
  const layers = [
    { label: 'Frontend', items: ['React + TypeScript', 'Real-time Dashboard', 'SSE Streaming'], color: '#06b6d4', icon: Globe },
    { label: 'Backend', items: ['Python FastAPI', 'REST API', 'Background Workers'], color: '#a855f7', icon: Server },
    { label: 'AI Layer', items: ['AWS Bedrock / Claude', 'scikit-learn ML Classifier', 'Code Generation'], color: '#22c55e', icon: Brain },
    { label: 'Infrastructure', items: ['Cloudera ML', 'SQLite + MLflow', 'GitHub Integration'], color: '#3b82f6', icon: Layers },
  ];

  return (
    <div className="flex h-full flex-col items-center justify-center">
      <div className="mb-4 flex items-center gap-2 rounded-full border border-blue-500/20 bg-blue-500/10 px-4 py-1.5">
        <Layers size={14} className="text-blue-400" />
        <span className="text-xs font-semibold tracking-wide text-blue-400 uppercase">
          Architecture
        </span>
      </div>
      <h2 className="mb-10 text-4xl font-black text-white md:text-5xl">The Closed Loop</h2>

      {/* Flow diagram */}
      <div className="mb-10 flex items-center gap-3">
        {MODULE_DATA.map((mod, i) => (
          <div key={mod.name} className="flex items-center gap-3">
            <div className="flex flex-col items-center gap-1.5">
              <div
                className="flex h-12 w-12 items-center justify-center rounded-xl border"
                style={{ borderColor: mod.color, backgroundColor: `${mod.color}15`, boxShadow: `0 0 12px ${mod.color}15` }}
              >
                <mod.icon size={22} style={{ color: mod.color }} />
              </div>
              <span className="text-[10px] font-bold tracking-wider" style={{ color: mod.color }}>
                {mod.name}
              </span>
            </div>
            {i < MODULE_DATA.length - 1 && (
              <ArrowRight size={18} className="text-gray-500" />
            )}
          </div>
        ))}
      </div>

      {/* Architecture layers */}
      <div className="grid max-w-5xl grid-cols-2 gap-4 md:grid-cols-4">
        {layers.map(({ label, items, color, icon: Icon }) => (
          <div
            key={label}
            className="rounded-xl border p-4"
            style={{ borderColor: `${color}30`, backgroundColor: `${color}08` }}
          >
            <div className="mb-3 flex items-center gap-2">
              <Icon size={16} style={{ color }} />
              <span className="text-sm font-bold" style={{ color }}>{label}</span>
            </div>
            <div className="space-y-1.5">
              {items.map((item) => (
                <p key={item} className="text-xs text-gray-400">{item}</p>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ─── Slide 5: Cloudera AI Platform (NEW) ─── */

function SlideCloudera() {
  const capabilities = [
    {
      title: 'CML Applications',
      desc: 'Hosts the full Sentinel platform -- React frontend + FastAPI backend running as persistent CML Applications',
      icon: Globe,
      color: '#06b6d4',
    },
    {
      title: 'CML Jobs',
      desc: 'Scheduled error scanning every 30 min and auto-heal pipeline every hour via CML Jobs',
      icon: Timer,
      color: '#a855f7',
    },
    {
      title: 'CML Models',
      desc: 'scikit-learn ML classifier (GradientBoosting + cross-validation) deployed as real-time REST endpoint for error classification',
      icon: Brain,
      color: '#22c55e',
    },
    {
      title: 'CML Experiments',
      desc: 'MLflow tracking of model accuracy, fix success rates, MTTR, and token usage -- full experiment history versioned',
      icon: BarChart3,
      color: '#f59e0b',
    },
    {
      title: 'AWS Bedrock via CML',
      desc: 'Claude AI integration through CML\'s AWS Bedrock gateway for deep error analysis and code generation',
      icon: Cpu,
      color: '#ec4899',
    },
    {
      title: 'PBJ Runtime',
      desc: 'Python 3.11 PBJ Workbench Runtime with all ML/AI dependencies pre-configured',
      icon: Server,
      color: '#3b82f6',
    },
  ];

  return (
    <div className="flex h-full flex-col items-center justify-center">
      <div className="mb-4 flex items-center gap-2 rounded-full border border-orange-500/30 bg-orange-500/10 px-5 py-2">
        <CloudCog size={16} className="text-orange-400" />
        <span className="text-xs font-semibold tracking-wide text-orange-300 uppercase">
          Platform
        </span>
      </div>
      <h2 className="mb-3 text-4xl font-black text-white md:text-5xl">
        Powered by{' '}
        <span className="bg-gradient-to-r from-orange-400 to-amber-400 bg-clip-text text-transparent">
          Cloudera AI
        </span>
      </h2>
      <p className="mb-10 max-w-xl text-center text-gray-400">
        Every CML capability working together to deliver autonomous self-healing
      </p>

      <div className="grid max-w-5xl grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {capabilities.map(({ title, desc, icon: Icon, color }) => (
          <div
            key={title}
            className="group rounded-xl border p-5 transition-all hover:scale-[1.02]"
            style={{ borderColor: `${color}25`, backgroundColor: `${color}08` }}
          >
            <div className="mb-3 flex items-center gap-3">
              <div
                className="flex h-10 w-10 items-center justify-center rounded-lg border"
                style={{ borderColor: `${color}40`, backgroundColor: `${color}15` }}
              >
                <Icon size={20} style={{ color }} />
              </div>
              <h3 className="text-sm font-bold text-white">{title}</h3>
            </div>
            <p className="text-xs leading-relaxed text-gray-400">{desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ─── Slide 6: How It Works (NEW) ─── */

function SlideHowItWorks() {
  const steps = [
    {
      step: '1',
      title: 'Error Detected',
      desc: 'CML Job scans logs, finds a NullPointerException in production',
      icon: AlertTriangle,
      color: '#ef4444',
      detail: 'WATCH module ingests structured logs',
    },
    {
      step: '2',
      title: 'AI Classifies',
      desc: 'CML Model endpoint classifies as "Critical / Database Error"',
      icon: Brain,
      color: '#a855f7',
      detail: 'THINK module uses ML classifier + Claude',
    },
    {
      step: '3',
      title: 'Fix Generated',
      desc: 'Claude via AWS Bedrock generates a targeted 3-line code fix',
      icon: FileCode,
      color: '#22c55e',
      detail: 'HEAL module fetches context from GitHub',
    },
    {
      step: '4',
      title: 'PR Created',
      desc: 'Automated pull request with fix, tests, and confidence score',
      icon: GitPullRequest,
      color: '#3b82f6',
      detail: 'VERIFY module manages deployment gate',
    },
    {
      step: '5',
      title: 'Deployed & Learned',
      desc: 'Fix merged, deployed, and metrics logged to MLflow',
      icon: Rocket,
      color: '#f59e0b',
      detail: 'EVOLVE module tracks patterns for future',
    },
  ];

  return (
    <div className="flex h-full flex-col items-center justify-center">
      <div className="mb-4 flex items-center gap-2 rounded-full border border-purple-500/20 bg-purple-500/10 px-4 py-1.5">
        <Activity size={14} className="text-purple-400" />
        <span className="text-xs font-semibold tracking-wide text-purple-400 uppercase">
          Real Scenario
        </span>
      </div>
      <h2 className="mb-3 text-4xl font-black text-white md:text-5xl">How It Works</h2>
      <p className="mb-10 text-gray-400">From error to fix in under 4 minutes</p>

      <div className="flex max-w-5xl flex-wrap items-start justify-center gap-3">
        {steps.map(({ step, title, desc, icon: Icon, color, detail }, i) => (
          <div key={step} className="flex items-start gap-3">
            <div className="flex flex-col items-center" style={{ width: '160px' }}>
              {/* Step number circle */}
              <div
                className="mb-3 flex h-12 w-12 items-center justify-center rounded-full border-2 text-lg font-black"
                style={{ borderColor: color, color, backgroundColor: `${color}15`, boxShadow: `0 0 20px ${color}20` }}
              >
                <Icon size={22} />
              </div>
              <h4 className="mb-1 text-sm font-bold text-white">{title}</h4>
              <p className="mb-2 text-center text-xs text-gray-400">{desc}</p>
              <div
                className="rounded-md px-2 py-1 text-center"
                style={{ backgroundColor: `${color}10`, border: `1px solid ${color}20` }}
              >
                <span className="text-[10px] font-semibold" style={{ color }}>{detail}</span>
              </div>
            </div>
            {i < steps.length - 1 && (
              <ArrowRight size={18} className="mt-4 flex-shrink-0 text-gray-600" />
            )}
          </div>
        ))}
      </div>

      <div className="mt-8 flex items-center gap-3 rounded-xl border border-green-500/20 bg-green-500/10 px-5 py-2.5">
        <Timer size={16} className="text-green-400" />
        <span className="text-sm font-bold text-green-400">
          Total time: ~4 minutes
        </span>
        <span className="text-sm text-gray-400">
          (vs. 4+ hours manual)
        </span>
      </div>
    </div>
  );
}

/* ─── Slide 7: WATCH ─── */

function SlideWatch() {
  const features = [
    'Structured log parsing from any application',
    'Intelligent deduplication (fingerprinting)',
    'Real-time streaming via SSE',
    'CML Job: Scheduled scan every 30 minutes',
    'Currently monitoring: Metrics AI (m8x.ai)',
  ];

  return (
    <ModuleSlide
      module="WATCH"
      tagline="See Everything"
      description="Real-time log ingestion and anomaly detection"
      features={features}
      icon={Eye}
      color="#06b6d4"
    />
  );
}

/* ─── Slide 8: THINK ─── */

function SlideThink() {
  const features = [
    'Hybrid: ML Classifier (scikit-learn) + Claude Sonnet (deep analysis)',
    'CML Model: Real-time classification REST endpoint',
    '8 error categories, 4 severity levels, trained with cross-validation',
    'Root cause analysis in plain English',
    'Pattern recognition across error history',
  ];

  return (
    <ModuleSlide
      module="THINK"
      tagline="Understand Why"
      description="AI-powered error classification and root cause analysis"
      features={features}
      icon={Brain}
      color="#a855f7"
    />
  );
}

/* ─── Slide 9: HEAL ─── */

function SlideHeal() {
  const features = [
    'Fetches source code context from GitHub',
    'Claude via AWS Bedrock generates targeted diffs',
    'Confidence scoring and risk assessment',
    'CML Job: Auto-heal pipeline runs hourly',
    'Human-in-the-loop approval (never auto-deploys)',
  ];

  return (
    <ModuleSlide
      module="HEAL"
      tagline="Fix Automatically"
      description="Claude generates targeted code fixes with context"
      features={features}
      icon={Wrench}
      color="#22c55e"
    />
  );
}

/* ─── Slide 10: VERIFY ─── */

function SlideVerify() {
  const features = [
    'Automated GitHub PR creation with AI-generated diffs',
    'CI/CD pipeline integration and test monitoring',
    'CML Experiments: MLflow tracks heal success metrics',
    'Production promotion gate with confidence thresholds',
  ];

  return (
    <ModuleSlide
      module="VERIFY"
      tagline="Deploy Safely"
      description="Automated staging deployment, testing, and promotion"
      features={features}
      icon={Shield}
      color="#3b82f6"
      extraIcons={[GitBranch, TestTube2]}
    />
  );
}

/* ─── Slide 11: EVOLVE ─── */

function SlideEvolve() {
  const features = [
    'Natural language feature requests from user feedback',
    'AI generates specification + implementation plan',
    'Human review and approval workflow',
    'The system gets smarter with every heal cycle',
  ];

  return (
    <div className="flex h-full flex-col items-center justify-center">
      <ModuleSlideInner
        module="EVOLVE"
        tagline="Build What Users Want"
        description="From user feedback to production features -- autonomously"
        features={features}
        icon={Sparkles}
        color="#f59e0b"
        extraIcons={[MessageSquare, Code2]}
      />
      <div className="mt-8 rounded-xl border border-amber-500/30 bg-gradient-to-r from-amber-500/10 to-orange-500/10 px-6 py-3">
        <span className="text-sm font-bold text-amber-400">
          UNIQUE DIFFERENTIATOR -- no competitor does this
        </span>
      </div>
    </div>
  );
}

/* ─── Slide 12: Impact ─── */

function SlideImpact() {
  const stats = [
    { before: '4 hours', after: '4 min', label: 'MTTR', sublabel: 'Mean Time To Recovery', icon: Timer },
    { before: '', after: '85%', label: 'Fix Rate', sublabel: 'AI-generated fixes that work', icon: CheckCircle2 },
    { before: '', after: '200+', label: 'Hours Saved', sublabel: 'Engineer-hours per month', icon: TrendingUp },
  ];

  return (
    <div className="flex h-full flex-col items-center justify-center">
      <div className="mb-4 flex items-center gap-2 rounded-full border border-green-500/20 bg-green-500/10 px-4 py-1.5">
        <TrendingUp size={14} className="text-green-400" />
        <span className="text-xs font-semibold tracking-wide text-green-400 uppercase">
          Impact
        </span>
      </div>
      <h2 className="mb-12 text-5xl font-black text-white md:text-6xl">The Numbers</h2>

      <div className="mb-10 grid max-w-4xl grid-cols-1 gap-10 md:grid-cols-3">
        {stats.map(({ before, after, label, sublabel, icon: Icon }) => (
          <div key={label} className="flex flex-col items-center text-center">
            <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-xl border border-cyan-500/20 bg-cyan-500/10">
              <Icon size={24} className="text-cyan-400" />
            </div>
            {before && (
              <p className="mb-1 text-lg text-gray-500 line-through">{before}</p>
            )}
            <p className="mb-1 text-5xl font-black md:text-6xl">
              <span className="bg-gradient-to-r from-cyan-400 to-green-400 bg-clip-text text-transparent">
                {after}
              </span>
            </p>
            <p className="text-lg font-bold text-white">{label}</p>
            <p className="text-sm text-gray-500">{sublabel}</p>
          </div>
        ))}
      </div>

      <p className="mb-6 text-gray-400">
        Projected impact for a business running 50 client applications
      </p>

      <div className="flex flex-wrap items-center justify-center gap-4">
        <div className="flex items-center gap-2 rounded-xl border border-gray-700 bg-gray-800/50 px-5 py-2.5">
          <CloudCog size={16} className="text-orange-400" />
          <span className="text-sm text-gray-300">
            Built on <span className="font-bold text-orange-400">Cloudera AI</span>
          </span>
        </div>
        <div className="flex items-center gap-2 rounded-xl border border-gray-700 bg-gray-800/50 px-5 py-2.5">
          <Brain size={16} className="text-purple-400" />
          <span className="text-sm text-gray-300">
            Powered by <span className="font-bold text-purple-400">Claude AI</span>
          </span>
        </div>
      </div>
    </div>
  );
}

/* ─── Slide 13: Closing / CTA (NEW) ─── */

function SlideClosing() {
  const takeaways = [
    { text: 'Fully autonomous detect-to-deploy pipeline', icon: Activity, color: '#06b6d4' },
    { text: 'Reduces MTTR from hours to minutes', icon: Timer, color: '#22c55e' },
    { text: 'Leverages 6 Cloudera ML capabilities', icon: CloudCog, color: '#f59e0b' },
    { text: 'Self-evolving -- learns and grows from every fix', icon: Sparkles, color: '#a855f7' },
  ];

  return (
    <div className="flex h-full flex-col items-center justify-center text-center">
      {/* Logos */}
      <div className="mb-6 flex items-center gap-5">
        <SkillfieldLogo size={48} />
        <ClouderaLogo size={48} />
      </div>

      <h2 className="mb-3 text-4xl font-black text-white md:text-5xl">
        <span className="bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-500 bg-clip-text text-transparent">
          Skillfield Sentinel
        </span>
      </h2>
      <p className="mb-10 text-lg text-gray-400">
        Software that heals itself. Built on Cloudera AI.
      </p>

      {/* Key takeaways */}
      <div className="mb-10 grid max-w-2xl grid-cols-1 gap-3 md:grid-cols-2">
        {takeaways.map(({ text, icon: Icon, color }) => (
          <div
            key={text}
            className="flex items-center gap-3 rounded-xl border px-4 py-3 text-left"
            style={{ borderColor: `${color}25`, backgroundColor: `${color}08` }}
          >
            <Icon size={18} style={{ color }} className="flex-shrink-0" />
            <span className="text-sm text-gray-300">{text}</span>
          </div>
        ))}
      </div>

      <div className="mb-8 h-px w-48 bg-gradient-to-r from-transparent via-gray-600 to-transparent" />

      {/* Demo & Contact */}
      <div className="mb-6 flex flex-wrap items-center justify-center gap-4">
        <div className="flex items-center gap-2 rounded-xl border border-cyan-500/30 bg-cyan-500/10 px-5 py-2.5">
          <ExternalLink size={16} className="text-cyan-400" />
          <span className="text-sm font-semibold text-cyan-400">Live Demo Available</span>
        </div>
        <div className="flex items-center gap-2 rounded-xl border border-gray-700 bg-gray-800/50 px-5 py-2.5">
          <Globe size={16} className="text-gray-400" />
          <span className="text-sm text-gray-300">skillfield.com.au</span>
        </div>
      </div>

      <div className="flex flex-col items-center gap-1">
        <p className="text-sm font-bold tracking-[0.15em] text-gray-400 uppercase">
          Skillfield Pty Ltd
        </p>
        <p className="text-xs text-gray-500">
          Cloudera Partner AI Hackathon 2026
        </p>
      </div>

      {/* Cloudera badge */}
      <div className="mt-6 flex items-center gap-2 rounded-full border border-orange-500/30 bg-orange-500/10 px-5 py-2">
        <CloudCog size={16} className="text-orange-400" />
        <span className="text-sm font-semibold text-orange-300">
          Built on Cloudera AI
        </span>
      </div>
    </div>
  );
}

/* ─── Shared Module Slide Layout ─── */

interface ModuleSlideProps {
  module: string;
  tagline: string;
  description: string;
  features: string[];
  icon: typeof Eye;
  color: string;
  extraIcons?: (typeof Eye)[];
}

function ModuleSlide(props: ModuleSlideProps) {
  return (
    <div className="flex h-full flex-col items-center justify-center">
      <ModuleSlideInner {...props} />
    </div>
  );
}

function ModuleSlideInner({
  module,
  tagline,
  description,
  features,
  icon: Icon,
  color,
}: ModuleSlideProps) {
  return (
    <>
      {/* Module badge */}
      <div
        className="mb-6 flex items-center gap-2 rounded-full px-4 py-1.5"
        style={{ backgroundColor: `${color}15`, border: `1px solid ${color}30` }}
      >
        <span className="text-xs font-semibold tracking-wide uppercase" style={{ color }}>
          Module
        </span>
      </div>

      <div
        className="mb-6 flex h-20 w-20 items-center justify-center rounded-2xl border-2"
        style={{ borderColor: color, backgroundColor: `${color}15`, boxShadow: `0 0 30px ${color}15` }}
      >
        <Icon size={40} style={{ color }} />
      </div>
      <h2 className="mb-2 text-4xl font-black md:text-5xl" style={{ color }}>
        {module}
      </h2>
      <h3 className="mb-2 text-2xl font-bold text-white md:text-3xl">{tagline}</h3>
      <p className="mb-10 text-gray-400">{description}</p>
      <div className="max-w-lg space-y-4">
        {features.map((f, i) => (
          <div key={i} className="flex items-start gap-3">
            <div
              className="mt-1.5 h-2 w-2 flex-shrink-0 rounded-full"
              style={{ backgroundColor: color, boxShadow: `0 0 6px ${color}40` }}
            />
            <span className="text-lg text-gray-300">{f}</span>
          </div>
        ))}
      </div>
    </>
  );
}

/* ─── Main Presentation Component ─── */

const SLIDES = [
  SlideTitle,       // 1
  SlideProblem,     // 2
  SlideSolution,    // 3
  SlideArchitecture,// 4
  SlideCloudera,    // 5 (NEW)
  SlideHowItWorks,  // 6 (NEW)
  SlideWatch,       // 7
  SlideThink,       // 8
  SlideHeal,        // 9
  SlideVerify,      // 10
  SlideEvolve,      // 11
  SlideImpact,      // 12
  SlideClosing,     // 13 (NEW)
];

export function PresentationPage() {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [fadeKey, setFadeKey] = useState(0);
  const navigate = useNavigate();

  const goTo = useCallback(
    (index: number) => {
      if (index >= 0 && index < TOTAL_SLIDES && index !== currentSlide) {
        setCurrentSlide(index);
        setFadeKey((k) => k + 1);
      }
    },
    [currentSlide],
  );

  const goNext = useCallback(() => goTo(currentSlide + 1), [currentSlide, goTo]);
  const goPrev = useCallback(() => goTo(currentSlide - 1), [currentSlide, goTo]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        navigate('/');
      } else if (e.key === 'ArrowRight' || e.key === ' ') {
        e.preventDefault();
        goNext();
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault();
        goPrev();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [goNext, goPrev, navigate]);

  const SlideComponent = SLIDES[currentSlide];
  const bgGradient = SLIDE_GRADIENTS[currentSlide] || '';

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-gray-950">
      {/* Background gradient layer */}
      <div
        className="pointer-events-none absolute inset-0 transition-opacity duration-700"
        style={{ backgroundImage: bgGradient }}
      />

      {/* Subtle grid pattern overlay */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: 'linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)',
          backgroundSize: '60px 60px',
        }}
      />

      {/* Exit button */}
      <button
        onClick={() => navigate('/')}
        className="absolute right-4 top-4 z-10 flex h-9 w-9 items-center justify-center rounded-lg border border-gray-700/50 bg-gray-900/80 text-gray-400 backdrop-blur transition-all hover:border-gray-600 hover:bg-gray-800 hover:text-white"
        title="Exit presentation (Esc)"
      >
        <X size={18} />
      </button>

      {/* Slide content */}
      <div className="relative flex-1 overflow-hidden px-8 py-6">
        <div
          key={fadeKey}
          className="h-full"
          style={{ animation: 'slideIn 0.45s cubic-bezier(0.16, 1, 0.3, 1)' }}
        >
          <SlideComponent />
        </div>
      </div>

      {/* Bottom navigation bar */}
      <div className="relative flex items-center justify-between border-t border-gray-800/60 bg-gray-900/60 px-6 py-3 backdrop-blur-md">
        {/* Left arrow */}
        <button
          onClick={goPrev}
          disabled={currentSlide === 0}
          className="flex h-9 w-9 items-center justify-center rounded-lg text-gray-400 transition-all hover:bg-gray-800 hover:text-white disabled:opacity-20 disabled:hover:bg-transparent"
        >
          <ChevronLeft size={20} />
        </button>

        {/* Dot indicators */}
        <div className="flex items-center gap-1.5">
          {SLIDES.map((_, i) => (
            <button
              key={i}
              onClick={() => goTo(i)}
              className={`h-1.5 rounded-full transition-all duration-300 ${
                i === currentSlide
                  ? 'w-6 bg-cyan-400 shadow-[0_0_8px_rgba(6,182,212,0.4)]'
                  : 'w-1.5 bg-gray-600 hover:bg-gray-500'
              }`}
            />
          ))}
        </div>

        {/* Slide counter + Right arrow */}
        <div className="flex items-center gap-4">
          <span className="text-xs font-medium tabular-nums text-gray-500">
            {currentSlide + 1} / {TOTAL_SLIDES}
          </span>
          <button
            onClick={goNext}
            disabled={currentSlide === TOTAL_SLIDES - 1}
            className="flex h-9 w-9 items-center justify-center rounded-lg text-gray-400 transition-all hover:bg-gray-800 hover:text-white disabled:opacity-20 disabled:hover:bg-transparent"
          >
            <ChevronRight size={20} />
          </button>
        </div>
      </div>

      {/* CSS for animations */}
      <style>{`
        @keyframes slideIn {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
