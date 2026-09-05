import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Flame,
  ArrowRight,
  ShieldCheck,
  Cpu,
  Lock,
  Play,
  Pause,
  RotateCcw,
  CheckCircle2,
  AlertOctagon,
  Clock,
  Layers,
  ChevronRight,
  TrendingUp,
} from 'lucide-react';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';

interface SimulationStage {
  id: string;
  stepNumber: string;
  phase: string;
  title: string;
  headline: string;
  description: string;
  status: 'active' | 'completed' | 'pending';
  badge: { text: string; variant: 'danger' | 'warning' | 'info' | 'purple' | 'success' | 'simulation' };
  metrics: Record<string, string>;
  actor: 'telemetry' | 'investigator' | 'policy' | 'executor' | 'verifier';
}

const LIFECYCLE_STAGES: SimulationStage[] = [
  {
    id: 'signal',
    stepNumber: '01',
    phase: 'OBSERVE',
    title: 'Signal Anomaly Detected',
    headline: 'High-frequency telemetry detects checkout conversion drop',
    description: 'Automated telemetry monitors observe HDFC Netbanking error rates spike from 0.12% baseline to 14.8% on mobile web.',
    status: 'completed',
    badge: { text: 'SIGNAL: ANOMALY', variant: 'danger' },
    metrics: { 'Route': 'HDFC_DIRECT', 'Error Rate': '14.8%', 'P99 Latency': '4,850 ms' },
    actor: 'telemetry',
  },
  {
    id: 'incident',
    stepNumber: '02',
    phase: 'PRIORITIZE',
    title: 'Revenue Incident Scoped',
    headline: 'Financial impact calculated deterministically at ₹45,000.00',
    description: 'Incident #inc_hdfc_drop_01 initialized. Immediate financial exposure scoped with 92% confidence based on hourly velocity.',
    status: 'completed',
    badge: { text: 'INCIDENT: HIGH SEVERITY', variant: 'danger' },
    metrics: { 'Revenue at Risk': '₹45,000.00', 'Confidence': '92%', 'Severity': 'HIGH' },
    actor: 'telemetry',
  },
  {
    id: 'investigate',
    stepNumber: '03',
    phase: 'INVESTIGATE & ATTRIBUTE',
    title: 'LangGraph Root Cause Analysis',
    headline: 'Multi-step agent workflow isolates upstream HTTP 504 timeout',
    description: 'Investigator agent ingests 3 telemetry traces, eliminating client-side bugs and attributing the failure to direct bank OTP gateway timeouts.',
    status: 'completed',
    badge: { text: 'AI INVESTIGATOR: CONCLUSIVE', variant: 'info' },
    metrics: { 'Root Cause': 'Bank OTP Gateway 504', 'Affected Cohort': 'HDFC_NETBANKING', 'Evidence Items': '3 Grounded' },
    actor: 'investigator',
  },
  {
    id: 'plan',
    stepNumber: '04',
    phase: 'DECIDE',
    title: 'Mitigation Plan Proposed',
    headline: 'Recovery Planner proposes secondary gateway traffic rerouting',
    description: 'Planner proposes GATEWAY_REROUTE targeting Axis secondary aggregation rail to recover an estimated ₹35,000.00 with low operational risk.',
    status: 'completed',
    badge: { text: 'PLAN: PROPOSED', variant: 'warning' },
    metrics: { 'Action Type': 'GATEWAY_REROUTE', 'Expected Recovery': '₹35,000.00', 'Risk Level': 'LOW' },
    actor: 'investigator',
  },
  {
    id: 'policy',
    stepNumber: '05',
    phase: 'GOVERN',
    title: 'Deterministic Policy Authorization',
    headline: 'Security boundary independently validates monetary & risk limits',
    description: 'CRITICAL TRUST BOUNDARY: AI proposes, but deterministic engine evaluates limits. Recovery ₹35k <= ₹50k auto-cap. Decision: ALLOW.',
    status: 'completed',
    badge: { text: 'POLICY: ALLOW', variant: 'purple' },
    metrics: { 'Policy Version': 'v1.0.0', 'Auto-Cap Limit': '₹50,000.00', 'Decision': 'ALLOW (6/6 Passed)' },
    actor: 'policy',
  },
  {
    id: 'execute',
    stepNumber: '06',
    phase: 'EXECUTE',
    title: 'Guarded Executor Dispatch',
    headline: 'ActionExecutor routes traffic through verified sandbox rail',
    description: 'State transitions safely from APPROVED → EXECUTING → COMPLETED. Idempotency key generated to prevent duplicate executions.',
    status: 'completed',
    badge: { text: 'EXECUTOR: COMPLETED', variant: 'simulation' },
    metrics: { 'Provider': 'simulation_adapter', 'Idempotency Key': 'exec_act_98a72b1', 'Status': 'SIMULATED' },
    actor: 'executor',
  },
  {
    id: 'verify',
    stepNumber: '07',
    phase: 'VERIFY & LEARN',
    title: 'Economic Outcome Verified',
    headline: 'Post-telemetry confirms route stabilization & protected revenue',
    description: 'Post-execution telemetry proves conversion recovery. Deterministic calculator computes ₹35,000.00 protected revenue (77.8% recovery rate).',
    status: 'completed',
    badge: { text: 'VERIFIED: ₹35,000 RECOVERED', variant: 'success' },
    metrics: { 'Protected Revenue': '₹35,000.00', 'Recovery Rate': '77.8%', 'Incident Status': 'RESOLVED' },
    actor: 'verifier',
  },
];

export const LandingPage: React.FC = () => {
  const [currentStageIdx, setCurrentStageIdx] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(true);

  // Auto-progression timer for interactive animation
  useEffect(() => {
    if (!isPlaying) return;
    const interval = setInterval(() => {
      setCurrentStageIdx((prev) => (prev + 1) % LIFECYCLE_STAGES.length);
    }, 4500);
    return () => clearInterval(interval);
  }, [isPlaying]);

  const currentStage = LIFECYCLE_STAGES[currentStageIdx];

  return (
    <div className="min-h-screen bg-[#FAFAFA] text-slate-900 flex flex-col font-sans selection:bg-slate-200">
      {/* Top Header */}
      <header className="border-b border-slate-200 bg-white/90 backdrop-blur-md sticky top-0 z-40 px-6 py-3.5">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-lg bg-slate-900 flex items-center justify-center text-white shadow-sm">
              <Flame className="h-4 w-4 text-rose-400" />
            </div>
            <div>
              <span className="font-bold tracking-tight text-slate-900 text-base">Revenue Autopsy</span>
              <span className="text-[10px] text-slate-500 font-mono ml-2 border border-slate-200 px-1.5 py-0.5 rounded bg-slate-50">
                INCIDENT RESPONSE
              </span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/app/overview">
              <Button variant="primary" size="sm">
                Enter Console <ArrowRight className="h-3.5 w-3.5 ml-1" />
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="pt-16 pb-12 px-6 max-w-5xl mx-auto text-center space-y-5">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-100 border border-slate-200 text-xs font-medium text-slate-700">
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-700" />
          <span>Operational Revenue Incident Response & Autonomous Mitigation</span>
        </div>

        <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight text-slate-900 leading-[1.12]">
          When revenue drops, find out why. <br />
          <span className="text-slate-900">Then recover it.</span>
        </h1>

        <p className="max-w-2xl mx-auto text-base sm:text-lg text-slate-600 leading-relaxed font-normal">
          Enterprise revenue incidents happen silently. Revenue Autopsy investigates checkout anomalies, attributes root causes with grounded telemetry, applies strict deterministic financial safety policies, and verifies recovered revenue.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
          <Link to="/app/incidents/inc_hdfc_drop_01">
            <Button variant="primary" size="lg">
              Live Incident Cockpit <ArrowRight className="h-4 w-4 ml-1.5" />
            </Button>
          </Link>
          <Link to="/app/overview">
            <Button variant="outline" size="lg">
              Operational Situation Room
            </Button>
          </Link>
        </div>
      </section>

      {/* Flagship Interactive Lifecycle Workflow Player */}
      <section className="py-8 px-6 max-w-6xl mx-auto w-full">
        <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
          {/* Player Controls Bar */}
          <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/70 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
                  The Revenue Autopsy Operational Loop
                </h2>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Watch an active high-severity incident progress through investigation, policy validation, execution, and verification.
              </p>
            </div>

            <div className="flex items-center gap-2 font-mono text-xs">
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-white border border-slate-200 text-slate-700 hover:bg-slate-100 text-xs font-semibold shadow-xs"
              >
                {isPlaying ? <Pause className="h-3 w-3" /> : <Play className="h-3 w-3" />}
                <span>{isPlaying ? 'Pause Loop' : 'Play Loop'}</span>
              </button>
              <button
                onClick={() => setCurrentStageIdx(0)}
                className="inline-flex items-center gap-1.5 px-2 py-1 rounded bg-white border border-slate-200 text-slate-500 hover:text-slate-900 hover:bg-slate-100 text-xs"
                title="Reset to beginning"
              >
                <RotateCcw className="h-3 w-3" />
              </button>
            </div>
          </div>

          {/* Stepper Progress Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 border-b border-slate-100 bg-white divide-x divide-slate-100">
            {LIFECYCLE_STAGES.map((st, idx) => {
              const isCurrent = idx === currentStageIdx;
              const isPast = idx < currentStageIdx;
              return (
                <button
                  key={st.id}
                  onClick={() => {
                    setCurrentStageIdx(idx);
                    setIsPlaying(false);
                  }}
                  className={`p-3 text-left transition-all relative ${
                    isCurrent ? 'bg-slate-900 text-white' : 'hover:bg-slate-50 text-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className={`text-[10px] font-mono font-bold ${isCurrent ? 'text-slate-400' : 'text-slate-400'}`}>
                      {st.stepNumber}
                    </span>
                    {isPast ? (
                      <CheckCircle2 className="h-3 w-3 text-emerald-500" />
                    ) : isCurrent ? (
                      <span className="h-1.5 w-1.5 rounded-full bg-rose-400 animate-ping" />
                    ) : null}
                  </div>
                  <span className={`text-[10px] uppercase tracking-wider block font-semibold ${isCurrent ? 'text-rose-300' : 'text-slate-400'}`}>
                    {st.phase}
                  </span>
                  <span className={`text-xs font-semibold block truncate mt-0.5 ${isCurrent ? 'text-white' : 'text-slate-800'}`}>
                    {st.title}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Detailed Stage Execution Terminal Panel */}
          <div className="p-6 md:p-8 bg-slate-50/50">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
              {/* Narrative Explainer */}
              <div className="lg:col-span-7 space-y-4">
                <div className="flex items-center gap-2">
                  <Badge variant={currentStage.badge.variant}>
                    {currentStage.badge.text}
                  </Badge>
                  <span className="text-xs font-mono text-slate-400 uppercase font-semibold">
                    Stage {currentStage.stepNumber} of 07
                  </span>
                </div>

                <h3 className="text-xl font-bold text-slate-900 tracking-tight">
                  {currentStage.headline}
                </h3>

                <p className="text-sm text-slate-600 leading-relaxed font-normal">
                  {currentStage.description}
                </p>

                <div className="pt-2 flex items-center gap-3">
                  <Link to="/app/incidents/inc_hdfc_drop_01">
                    <Button variant="primary" size="sm">
                      Inspect Incident Cockpit <ArrowRight className="h-3.5 w-3.5 ml-1" />
                    </Button>
                  </Link>
                  <span className="text-xs text-slate-400 font-mono">
                    Incident ID: inc_hdfc_drop_01
                  </span>
                </div>
              </div>

              {/* Live Stage Audit Data Card */}
              <div className="lg:col-span-5 bg-white border border-slate-200 rounded-lg p-4 shadow-sm font-mono text-xs space-y-3">
                <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                  <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">
                    Stage State Payload
                  </span>
                  <span className="text-[10px] text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200 font-bold">
                    VERIFIED INVARIANT
                  </span>
                </div>

                <div className="space-y-2 text-[11px]">
                  {Object.entries(currentStage.metrics).map(([key, val]) => (
                    <div key={key} className="flex items-center justify-between py-1 border-b border-slate-50 last:border-0">
                      <span className="text-slate-400">{key}:</span>
                      <span className="font-semibold text-slate-900">{val}</span>
                    </div>
                  ))}
                </div>

                <div className="pt-1 text-[10px] text-slate-400 border-t border-slate-100 flex items-center justify-between">
                  <span>Actor Boundary:</span>
                  <span className="text-slate-700 uppercase font-bold">{currentStage.actor}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Core Operational Guarantees */}
      <section className="py-12 px-6 max-w-6xl mx-auto w-full grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white border border-slate-200 rounded-lg p-6 space-y-2.5 shadow-sm">
          <div className="h-8 w-8 rounded-md bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-700">
            <Cpu className="h-4 w-4" />
          </div>
          <h3 className="text-sm font-bold text-slate-900">LangGraph Diagnostic Investigator</h3>
          <p className="text-xs text-slate-600 leading-relaxed font-normal">
            Multi-node state machine grounds telemetry streams and calculates root causes. Structured Pydantic outputs with zero chain-of-thought hallucination.
          </p>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg p-6 space-y-2.5 shadow-sm">
          <div className="h-8 w-8 rounded-md bg-purple-50 border border-purple-200 flex items-center justify-center text-purple-700">
            <Lock className="h-4 w-4" />
          </div>
          <h3 className="text-sm font-bold text-slate-900">Deterministic Policy Engine</h3>
          <p className="text-xs text-slate-600 leading-relaxed font-normal">
            Strict fail-closed authorization. AI proposes mitigation, but deterministic engine validates ₹50k auto-caps, risk limits, and tenant boundaries.
          </p>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg p-6 space-y-2.5 shadow-sm">
          <div className="h-8 w-8 rounded-md bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700">
            <TrendingUp className="h-4 w-4" />
          </div>
          <h3 className="text-sm font-bold text-slate-900">Verified Economic Outcomes</h3>
          <p className="text-xs text-slate-600 leading-relaxed font-normal">
            Execution does not assume recovery. Post-execution telemetry confirms route health restoration and calculates exact decimal revenue protected.
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto border-t border-slate-200 bg-white py-6 px-6 text-center text-xs text-slate-500">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Flame className="h-4 w-4 text-slate-700" />
            <span className="font-semibold text-slate-800">Revenue Autopsy</span>
            <span>— Enterprise Incident Orchestration</span>
          </div>
          <div className="flex items-center gap-3 text-slate-500 font-mono text-[11px]">
            <span>FastAPI Backend</span>
            <span>·</span>
            <span>Deterministic Policy Engine v1.0</span>
            <span>·</span>
            <span>153 Passing Tests</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
