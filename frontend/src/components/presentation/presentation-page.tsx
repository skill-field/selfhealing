import { useState, useEffect, useCallback } from 'react';
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
} from 'lucide-react';

const TOTAL_SLIDES = 10;

const MODULE_DATA = [
  { name: 'WATCH', icon: Eye, color: '#06b6d4', desc: 'Real-time monitoring' },
  { name: 'THINK', icon: Brain, color: '#a855f7', desc: 'AI classification' },
  { name: 'HEAL', icon: Wrench, color: '#22c55e', desc: 'Auto-fix generation' },
  { name: 'VERIFY', icon: Shield, color: '#3b82f6', desc: 'Safe deployment' },
  { name: 'EVOLVE', icon: Sparkles, color: '#f59e0b', desc: 'Feature generation' },
];

/* ─── Slide Components ─── */

function SlideTitle() {
  return (
    <div className="flex h-full flex-col items-center justify-center text-center">
      <div className="mb-8 flex items-center gap-3">
        <Shield size={40} className="text-cyan-400" />
        <Zap size={32} className="text-purple-400 animate-pulse" />
      </div>
      <h1 className="mb-4 text-6xl font-black tracking-tight md:text-7xl lg:text-8xl">
        <span className="bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-500 bg-clip-text text-transparent animate-pulse">
          Skillfield Sentinel
        </span>
      </h1>
      <p className="mb-6 text-xl text-gray-300 md:text-2xl">
        AI Self-Healing Software Platform
      </p>
      <div className="mb-12 h-px w-48 bg-gradient-to-r from-transparent via-gray-600 to-transparent" />
      <p className="text-lg text-gray-400">Cloudera Partner AI Hackathon 2026</p>
      <p className="mt-4 text-sm font-semibold tracking-widest text-gray-500 uppercase">
        Skillfield Pty Ltd
      </p>
    </div>
  );
}

function SlideProblem() {
  const pains = [
    {
      icon: Clock,
      title: '4+ hours to resolve',
      desc: 'Average P0 incident takes 4+ hours to detect, diagnose, and fix',
    },
    {
      icon: DollarSign,
      title: '$15,000+ per hour',
      desc: 'Average cost per hour of production downtime',
    },
    {
      icon: Users,
      title: '40% reactive work',
      desc: 'Engineers spend 40% of their time firefighting production issues',
    },
  ];

  return (
    <div className="flex h-full flex-col items-center justify-center">
      <h2 className="mb-2 text-5xl font-black text-white md:text-6xl">
        Every Production Error
      </h2>
      <h2 className="mb-16 text-5xl font-black md:text-6xl">
        <span className="bg-gradient-to-r from-red-400 to-orange-400 bg-clip-text text-transparent">
          Costs Money
        </span>
      </h2>
      <div className="grid max-w-4xl grid-cols-1 gap-8 md:grid-cols-3">
        {pains.map(({ icon: Icon, title, desc }) => (
          <div key={title} className="flex flex-col items-center text-center">
            <div className="mb-4 flex h-20 w-20 items-center justify-center rounded-2xl border border-gray-700 bg-gray-800/50">
              <Icon size={36} className="text-red-400" />
            </div>
            <h3 className="mb-2 text-xl font-bold text-white">{title}</h3>
            <p className="text-sm text-gray-400">{desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function SlideSolution() {
  return (
    <div className="flex h-full flex-col items-center justify-center">
      <h2 className="mb-4 text-4xl font-black text-white md:text-5xl">
        What if your software could
      </h2>
      <h2 className="mb-16 text-5xl font-black md:text-6xl">
        <span className="bg-gradient-to-r from-cyan-400 to-green-400 bg-clip-text text-transparent">
          heal itself?
        </span>
      </h2>
      <div className="flex flex-wrap items-center justify-center gap-4">
        {MODULE_DATA.map((mod, i) => (
          <div key={mod.name} className="flex items-center gap-3">
            <div className="flex flex-col items-center gap-2">
              <div
                className="flex h-16 w-16 items-center justify-center rounded-full border-2"
                style={{
                  borderColor: mod.color,
                  backgroundColor: `${mod.color}15`,
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
              <ArrowRight size={24} className="text-gray-600" />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function SlideArchitecture() {
  const techs = [
    { name: 'Cloudera ML', icon: Cpu },
    { name: 'Claude AI', icon: Brain },
    { name: 'React', icon: Code2 },
    { name: 'Python', icon: Globe },
  ];

  return (
    <div className="flex h-full flex-col items-center justify-center">
      <h2 className="mb-12 text-4xl font-black text-white md:text-5xl">The Closed Loop</h2>

      {/* Circular flow diagram */}
      <div className="relative mb-12">
        <div className="flex items-center gap-3">
          {MODULE_DATA.map((mod, i) => (
            <div key={mod.name} className="flex items-center gap-3">
              <div className="flex flex-col items-center gap-1">
                <div
                  className="flex h-14 w-14 items-center justify-center rounded-xl border"
                  style={{ borderColor: mod.color, backgroundColor: `${mod.color}15` }}
                >
                  <mod.icon size={24} style={{ color: mod.color }} />
                </div>
                <span className="text-xs font-bold" style={{ color: mod.color }}>
                  {mod.name}
                </span>
              </div>
              {i < MODULE_DATA.length - 1 && (
                <ArrowRight size={20} className="text-gray-500" />
              )}
            </div>
          ))}
        </div>
        {/* Return arrow */}
        <div className="mt-4 flex justify-center">
          <div className="flex items-center gap-2 rounded-full border border-gray-700 bg-gray-800/50 px-4 py-1.5">
            <span className="text-xs text-gray-400">Full closed loop -- from detection to production</span>
          </div>
        </div>
      </div>

      <div className="flex gap-6">
        {techs.map(({ name, icon: Icon }) => (
          <div key={name} className="flex items-center gap-2 rounded-lg border border-gray-800 bg-gray-900 px-4 py-2">
            <Icon size={16} className="text-gray-400" />
            <span className="text-sm text-gray-300">{name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function SlideWatch() {
  const features = [
    'Structured log parsing from any application',
    'Intelligent deduplication (fingerprinting)',
    'Real-time streaming via SSE',
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

function SlideThink() {
  const features = [
    'Hybrid: Rule engine (instant) + Claude Sonnet (deep analysis)',
    '6 error categories, 4 severity levels',
    'Root cause analysis in plain English',
    'Pattern recognition across errors',
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

function SlideHeal() {
  const features = [
    'Fetches source code context from GitHub',
    'Generates minimal, targeted diffs',
    'Confidence scoring and risk assessment',
    'Human-in-the-loop approval (never auto-deploys)',
  ];

  return (
    <ModuleSlide
      module="HEAL"
      tagline="Fix Automatically"
      description="Claude generates targeted code fixes"
      features={features}
      icon={Wrench}
      color="#22c55e"
    />
  );
}

function SlideVerify() {
  const features = [
    'GitHub PR creation',
    'CI/CD pipeline integration',
    'Test result monitoring',
    'Production promotion gate',
  ];

  return (
    <ModuleSlide
      module="VERIFY"
      tagline="Deploy Safely"
      description="Automated staging deployment and testing"
      features={features}
      icon={Shield}
      color="#3b82f6"
      extraIcons={[GitBranch, TestTube2]}
    />
  );
}

function SlideEvolve() {
  const features = [
    'Natural language feature requests',
    'AI generates specification + implementation',
    'Human review and approval',
    'The system gets smarter over time',
  ];

  return (
    <div className="flex h-full flex-col items-center justify-center">
      <ModuleSlideInner
        module="EVOLVE"
        tagline="Build What Users Want"
        description="From user feedback to production features"
        features={features}
        icon={Sparkles}
        color="#f59e0b"
        extraIcons={[MessageSquare, Code2]}
      />
      <div className="mt-8 rounded-xl border border-amber-500/30 bg-amber-500/10 px-6 py-3">
        <span className="text-sm font-bold text-amber-400">
          UNIQUE -- no competitor does this
        </span>
      </div>
    </div>
  );
}

function SlideImpact() {
  const stats = [
    { before: '4 hours', after: '4 minutes', label: 'MTTR reduction' },
    { before: '', after: '85%', label: 'Fix success rate' },
    { before: '', after: '200+', label: 'Engineer-hours saved/month' },
  ];

  return (
    <div className="flex h-full flex-col items-center justify-center">
      <h2 className="mb-16 text-5xl font-black text-white md:text-6xl">The Numbers</h2>
      <div className="mb-12 grid max-w-4xl grid-cols-1 gap-8 md:grid-cols-3">
        {stats.map(({ before, after, label }) => (
          <div key={label} className="flex flex-col items-center text-center">
            {before && (
              <p className="mb-1 text-lg text-gray-500 line-through">{before}</p>
            )}
            <p className="mb-2 text-5xl font-black md:text-6xl">
              <span className="bg-gradient-to-r from-cyan-400 to-green-400 bg-clip-text text-transparent">
                {after}
              </span>
            </p>
            <p className="text-sm text-gray-400">{label}</p>
          </div>
        ))}
      </div>
      <p className="mb-8 text-gray-400">
        For a business running 50 client applications
      </p>
      <div className="flex items-center gap-3 rounded-xl border border-gray-700 bg-gray-800/50 px-6 py-3">
        <BarChart3 size={18} className="text-cyan-400" />
        <span className="text-sm text-gray-300">
          Built on <span className="font-bold text-cyan-400">Cloudera AI</span> | Powered by{' '}
          <span className="font-bold text-purple-400">Claude</span>
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
      <div
        className="mb-6 flex h-20 w-20 items-center justify-center rounded-2xl border-2"
        style={{ borderColor: color, backgroundColor: `${color}15` }}
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
              style={{ backgroundColor: color }}
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
  SlideTitle,
  SlideProblem,
  SlideSolution,
  SlideArchitecture,
  SlideWatch,
  SlideThink,
  SlideHeal,
  SlideVerify,
  SlideEvolve,
  SlideImpact,
];

export function PresentationPage() {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [fadeKey, setFadeKey] = useState(0);

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
      if (e.key === 'ArrowRight' || e.key === ' ') {
        e.preventDefault();
        goNext();
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault();
        goPrev();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [goNext, goPrev]);

  const SlideComponent = SLIDES[currentSlide];

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-gray-950">
      {/* Slide content */}
      <div className="flex-1 overflow-hidden px-8 py-6">
        <div
          key={fadeKey}
          className="h-full animate-[fadeIn_0.4s_ease-out]"
          style={{
            animation: 'fadeIn 0.4s ease-out',
          }}
        >
          <SlideComponent />
        </div>
      </div>

      {/* Bottom navigation bar */}
      <div className="flex items-center justify-between border-t border-gray-800 bg-gray-900/80 px-6 py-3 backdrop-blur">
        {/* Left arrow */}
        <button
          onClick={goPrev}
          disabled={currentSlide === 0}
          className="flex h-9 w-9 items-center justify-center rounded-lg text-gray-400 transition-colors hover:bg-gray-800 hover:text-white disabled:opacity-30 disabled:hover:bg-transparent"
        >
          <ChevronLeft size={20} />
        </button>

        {/* Dot indicators */}
        <div className="flex items-center gap-2">
          {SLIDES.map((_, i) => (
            <button
              key={i}
              onClick={() => goTo(i)}
              className={`h-2 rounded-full transition-all ${
                i === currentSlide
                  ? 'w-6 bg-cyan-400'
                  : 'w-2 bg-gray-600 hover:bg-gray-500'
              }`}
            />
          ))}
        </div>

        {/* Slide counter */}
        <div className="flex items-center gap-4">
          <span className="text-xs text-gray-500">
            {currentSlide + 1} / {TOTAL_SLIDES}
          </span>
          {/* Right arrow */}
          <button
            onClick={goNext}
            disabled={currentSlide === TOTAL_SLIDES - 1}
            className="flex h-9 w-9 items-center justify-center rounded-lg text-gray-400 transition-colors hover:bg-gray-800 hover:text-white disabled:opacity-30 disabled:hover:bg-transparent"
          >
            <ChevronRight size={20} />
          </button>
        </div>
      </div>

      {/* CSS for fade animation */}
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
