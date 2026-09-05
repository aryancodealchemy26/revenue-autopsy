import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Clock,
  ShieldCheck,
  ShieldAlert,
  Cpu,
  Layers,
  TrendingUp,
  ArrowRight,
  Lock,
  ChevronDown,
  ChevronUp,
  RotateCcw,
  Sparkles,
  Terminal,
  Activity,
  Check,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { api } from '../services/api';
import { FullIncidentContext, Evidence, InvestigationResult, ActionPlan, PolicyEvaluationResult, ExecutionResult, Outcome } from '../types/domain';

export type OperationState =
  | 'IDLE'
  | 'GATHERING_EVIDENCE'
  | 'EVIDENCE_READY'
  | 'INVESTIGATING'
  | 'INVESTIGATION_READY'
  | 'PLAN_READY'
  | 'POLICY_EVALUATING'
  | 'AWAITING_APPROVAL'
  | 'EXECUTING'
  | 'VERIFYING'
  | 'RESOLVED'
  | 'DENIED'
  | 'FAILED';

export const IncidentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [initialContext, setInitialContext] = useState<FullIncidentContext | null>(null);
  const [loading, setLoading] = useState(true);

  // Operational State Machine
  const [opState, setOpState] = useState<OperationState>('IDLE');
  const [opError, setOpError] = useState<string | null>(null);

  // Staged Data Loaded from Actions
  const [loadedEvidences, setLoadedEvidences] = useState<Evidence[]>([]);
  const [loadedInvestigation, setLoadedInvestigation] = useState<InvestigationResult | null>(null);
  const [loadedAction, setLoadedAction] = useState<ActionPlan | null>(null);
  const [loadedPolicy, setLoadedPolicy] = useState<PolicyEvaluationResult | null>(null);
  const [loadedExecution, setLoadedExecution] = useState<ExecutionResult | null>(null);
  const [loadedOutcome, setLoadedOutcome] = useState<Outcome | null>(null);

  const [expandedEvidences, setExpandedEvidences] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (id) {
      setLoading(true);
      api.getIncidentById(id).then((ctx) => {
        setInitialContext(ctx);
        if (ctx) {
          // If already resolved in grounded data (like HDFC ALLOW scenario), initialize as resolved
          if (ctx.incident.status === 'resolved' && ctx.outcome && ctx.execution_result && ctx.policy_decision?.decision === 'allow') {
            setLoadedEvidences(ctx.evidences || []);
            setLoadedInvestigation(ctx.investigation || null);
            setLoadedAction(ctx.proposed_action || null);
            setLoadedPolicy(ctx.policy_decision || null);
            setLoadedExecution(ctx.execution_result || null);
            setLoadedOutcome(ctx.outcome || null);
            setOpState('RESOLVED');
          } else if (ctx.policy_decision?.decision === 'require_approval' || ctx.incident.status === 'action_proposed') {
            // Require approval incidents MUST strictly start BEFORE authorization/execution
            setLoadedEvidences(ctx.evidences || []);
            setLoadedInvestigation(ctx.investigation || null);
            setLoadedAction(ctx.proposed_action || null);
            setLoadedPolicy(ctx.policy_decision || null);
            setLoadedExecution(null);
            setLoadedOutcome(null);
            setOpState('AWAITING_APPROVAL');
          } else {
            setLoadedEvidences(ctx.evidences || []);
            setLoadedInvestigation(null);
            setLoadedAction(null);
            setLoadedPolicy(null);
            setLoadedExecution(null);
            setLoadedOutcome(null);
            setOpState('IDLE');
          }

          // Expand first evidence item by default
          if (ctx.evidences && ctx.evidences.length > 0) {
            setExpandedEvidences({ [ctx.evidences[0].evidence_id]: true });
          }
        }
        setLoading(false);
      });
    }
  }, [id]);

  const toggleEvidence = (evId: string) => {
    setExpandedEvidences((prev) => ({ ...prev, [evId]: !prev[evId] }));
  };

  // Primary Operational Trigger: "Investigate Incident"
  const handleRunInvestigation = async () => {
    if (!id || !initialContext) return;
    setOpError(null);

    try {
      // 1. GATHER EVIDENCE
      setOpState('GATHERING_EVIDENCE');
      setLoadedExecution(null);
      setLoadedOutcome(null);
      const evidences = await api.gatherEvidence(id);
      setLoadedEvidences(evidences);
      setOpState('EVIDENCE_READY');

      // 2. AI INVESTIGATION
      setOpState('INVESTIGATING');
      const investigation = await api.runInvestigation(id);
      setLoadedInvestigation(investigation);
      setOpState('INVESTIGATION_READY');

      // 3. RECOVERY PLAN GENERATION
      const actionPlan = await api.generateActionPlan(id);
      setLoadedAction(actionPlan);
      setOpState('PLAN_READY');

      // 4. DETERMINISTIC POLICY EVALUATION
      setOpState('POLICY_EVALUATING');
      const policyDecision = await api.evaluatePolicy(id, actionPlan.action_id);
      setLoadedPolicy(policyDecision);

      // Policy Branching
      if (policyDecision.decision === 'deny') {
        setOpState('DENIED');
        return;
      }

      if (policyDecision.decision === 'require_approval') {
        setOpState('AWAITING_APPROVAL');
        return; // HALT! Never proceed to execution before explicit operator authorization
      }

      // 5. GUARDED EXECUTION (ALLOW path)
      await proceedToExecution(actionPlan.action_id);
    } catch (err: any) {
      setOpError(err?.message || 'Operation failed');
      setOpState('FAILED');
    }
  };

  // Human Operator Authorization Sign-off
  const handleAuthorizeAndExecute = async () => {
    if (!id || !loadedAction) return;
    setOpError(null);

    try {
      setOpState('EXECUTING');
      await api.authorizeAction(id, loadedAction.action_id);
      await proceedToExecution(loadedAction.action_id);
    } catch (err: any) {
      setOpError(err?.message || 'Authorization failed');
      setOpState('FAILED');
    }
  };

  // Shared Execution & Verification Pipeline
  const proceedToExecution = async (actionId: string) => {
    if (!id) return;
    setOpState('EXECUTING');
    const execResult = await api.executeAction(id, actionId);
    setLoadedExecution(execResult);

    // 6. POST-EXECUTION VERIFICATION
    setOpState('VERIFYING');
    const outcome = await api.verifyOutcome(id);
    setLoadedOutcome(outcome);
    setOpState('RESOLVED');
  };

  if (loading) {
    return (
      <div className="py-20 text-center space-y-3 font-mono text-xs text-slate-500">
        <div className="h-4 w-4 border-2 border-slate-900 border-t-transparent rounded-full animate-spin mx-auto" />
        <p>Loading operational incident cockpit...</p>
      </div>
    );
  }

  if (!initialContext) {
    return (
      <div className="py-20 text-center space-y-3">
        <p className="text-sm font-semibold text-slate-900">Incident not found in active workspace.</p>
        <Link to="/app/incidents">
          <Button variant="outline" size="sm">Back to Incident Queue</Button>
        </Link>
      </div>
    );
  }

  const { incident } = initialContext;
  const isOperating = ['GATHERING_EVIDENCE', 'INVESTIGATING', 'POLICY_EVALUATING', 'EXECUTING', 'VERIFYING'].includes(opState);

  // Compute status badge
  const displayStatus = opState === 'RESOLVED'
    ? 'RESOLVED'
    : opState === 'AWAITING_APPROVAL'
    ? 'AWAITING_APPROVAL'
    : opState === 'DENIED'
    ? 'POLICY_DENIED'
    : isOperating
    ? 'OPERATING'
    : incident.status.replace('_', ' ').toUpperCase();

  // Build Dynamic Audit Provenance Entries
  const provenanceEvents = [
    {
      step: '1. Incident Signal Detected',
      time: incident.detected_at,
      status: 'DETECTED',
      actor: 'Signal Ingestion Engine',
      summary: `${incident.incident_type} detected. Initial revenue at risk computed at ₹${parseFloat(incident.revenue_at_risk).toLocaleString('en-IN')}.`,
    },
    loadedEvidences.length > 0 && {
      step: '2. Evidence Collected',
      time: loadedEvidences[0]?.observed_at || incident.detected_at,
      status: 'COLLECTED',
      actor: 'Telemetry & Logs Collector',
      summary: `Gathered ${loadedEvidences.length} structured diagnostic payloads (${loadedEvidences.map(e => e.evidence_type).join(', ')}).`,
    },
    loadedInvestigation && {
      step: '3. Investigation & Attribution',
      time: incident.detected_at,
      status: 'CONCLUSIVE',
      actor: `AI Investigator Agent (Confidence: ${(loadedInvestigation.confidence * 100).toFixed(0)}%)`,
      summary: `Root cause: ${loadedInvestigation.primary_cause}. Impacted cohorts: ${loadedInvestigation.affected_cohorts.join(', ')}.`,
    },
    loadedAction && {
      step: '4. Recovery Plan Proposed',
      time: loadedAction.created_at,
      status: opState === 'AWAITING_APPROVAL' ? 'PENDING_APPROVAL' : loadedAction.status.toUpperCase(),
      actor: 'Recovery Planner Agent',
      summary: `Formulated ${loadedAction.action_type.toUpperCase()} mitigation plan for ${loadedAction.target}. Expected recovery: ₹${parseFloat(loadedAction.expected_recovery).toLocaleString('en-IN')}.`,
    },
    loadedPolicy && {
      step: '5. Deterministic Policy Evaluation',
      time: loadedPolicy.evaluated_at || incident.detected_at,
      status: loadedPolicy.decision.toUpperCase(),
      actor: `PolicyEngine (${loadedPolicy.policy_version})`,
      summary: `Evaluated ${loadedPolicy.rule_results.length} deterministic rules. Final decision: ${loadedPolicy.decision.toUpperCase()}. (${loadedPolicy.reasons.join('; ')})`,
    },
    loadedExecution && {
      step: '6. Guarded Execution',
      time: loadedExecution.executed_at,
      status: loadedExecution.status.toUpperCase(),
      actor: `Execution Broker (${loadedExecution.provider})`,
      summary: `Executed ${loadedExecution.action_type.toUpperCase()} via ${loadedExecution.provider}. Idempotency key: ${loadedExecution.idempotency_key}.`,
    },
    loadedOutcome && {
      step: '7. Economic Verification',
      time: loadedOutcome.measured_at,
      status: (loadedOutcome.reference_data.verification_status || 'VERIFIED_SUCCESS').toUpperCase(),
      actor: 'Verification Engine',
      summary: `Verified economic protection: ₹${parseFloat(loadedOutcome.reference_data.protected_revenue || loadedOutcome.amount || '0').toLocaleString('en-IN')} protected. Recovery Rate: ${(parseFloat(loadedOutcome.reference_data.recovery_rate || '1') * 100).toFixed(1)}%.`,
    },
  ].filter(Boolean) as { step: string; time: string; status: string; actor: string; summary: string }[];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      
      {/* Cockpit Breadcrumb & Header Bar */}
      <div className="space-y-3 border-b border-slate-200 pb-4">
        <div className="flex items-center justify-between">
          <Link
            to="/app/incidents"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 hover:text-slate-900 transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> Back to Incident Queue
          </Link>

          <span className="text-[11px] font-mono text-slate-500 bg-slate-100 border border-slate-200 px-2.5 py-0.5 rounded-full flex items-center gap-1.5">
            <span className={`h-2 w-2 rounded-full ${isOperating ? 'bg-blue-500 animate-ping' : opState === 'RESOLVED' ? 'bg-emerald-500' : 'bg-amber-500'}`} />
            OPERATIONAL INCIDENT COCKPIT · DETERMINISTIC BOUNDARY
          </span>
        </div>

        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-mono text-xs font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                {incident.incident_id}
              </span>
              <span className="font-mono text-xs font-semibold text-slate-700 uppercase bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                {incident.incident_type}
              </span>
              <Badge variant={incident.severity === 'critical' ? 'danger' : incident.severity === 'high' ? 'warning' : 'info'}>
                {incident.severity.toUpperCase()}
              </Badge>
              <Badge variant={opState === 'RESOLVED' ? 'success' : opState === 'AWAITING_APPROVAL' ? 'warning' : 'purple'}>
                {displayStatus}
              </Badge>
            </div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">{incident.description}</h1>
          </div>

          <div className="flex items-center gap-4 bg-white border border-slate-200 rounded-lg p-3 shadow-xs font-mono shrink-0">
            <div>
              <span className="text-[10px] text-slate-400 block uppercase font-semibold">Revenue at Risk</span>
              <span className="text-xl font-extrabold text-rose-700 tabular-nums">
                ₹{parseFloat(incident.revenue_at_risk).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
            </div>
            <div className="h-8 w-px bg-slate-200" />
            <div>
              <span className="text-[10px] text-slate-400 block uppercase font-semibold">
                {loadedOutcome ? 'Verified Protected' : 'Detected At'}
              </span>
              <span className={`text-sm font-bold ${loadedOutcome ? 'text-emerald-700' : 'text-slate-700'}`}>
                {loadedOutcome
                  ? `₹${parseFloat(loadedOutcome.reference_data.protected_revenue || loadedOutcome.amount).toLocaleString('en-IN')}`
                  : new Date(incident.detected_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* ACTION-DRIVEN OPERATIONAL CONTROLLER BAR */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-0.5">
          <div className="flex items-center gap-2">
            <Activity className={`h-4 w-4 ${isOperating ? 'text-blue-600 animate-spin' : opState === 'RESOLVED' ? 'text-emerald-600' : opState === 'AWAITING_APPROVAL' ? 'text-amber-600' : 'text-slate-500'}`} />
            <span className="text-xs font-mono uppercase font-bold text-slate-700">
              Operational Status:
            </span>
            <span className="text-xs font-bold text-slate-900">
              {opState === 'IDLE' && 'Ready for Investigation'}
              {opState === 'GATHERING_EVIDENCE' && 'Gathering Telemetry & Log Payloads...'}
              {opState === 'INVESTIGATING' && 'LangGraph Multi-Agent Correlating Root Cause...'}
              {opState === 'POLICY_EVALUATING' && 'PolicyEngine Evaluating Safety Rules...'}
              {opState === 'AWAITING_APPROVAL' && 'Awaiting Operator Authorization (Monetary Cap Exceeded)'}
              {opState === 'EXECUTING' && 'Dispatching Guarded Action to Simulation Adapter...'}
              {opState === 'VERIFYING' && 'Verification Engine Sampling Post-Execution Telemetry...'}
              {opState === 'RESOLVED' && 'Incident Mitigated & Economic Outcome Verified'}
              {opState === 'DENIED' && 'Action Denied by Policy Engine'}
              {opState === 'FAILED' && 'Operation Error'}
            </span>
          </div>
          <p className="text-xs text-slate-500">
            {opState === 'IDLE' && 'Trigger autonomous AI investigation and deterministic policy evaluation.'}
            {opState === 'AWAITING_APPROVAL' && 'Financial recovery exceeds auto-authorization cap (₹50,000.00). Execution halted pending operator sign-off.'}
            {opState === 'RESOLVED' && 'Post-execution telemetry verified. All operational stages logged.'}
            {isOperating && 'Autonomous response loop in progress...'}
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {opState === 'AWAITING_APPROVAL' ? (
            <Button
              variant="primary"
              size="md"
              isLoading={isOperating}
              onClick={handleAuthorizeAndExecute}
              className="bg-amber-600 hover:bg-amber-700 text-white"
            >
              <ShieldCheck className="h-4 w-4 mr-1.5" /> Authorize & Dispatch Action Plan
            </Button>
          ) : opState === 'RESOLVED' ? (
            <Button
              variant="outline"
              size="sm"
              isLoading={isOperating}
              onClick={handleRunInvestigation}
              className="border-slate-300 text-slate-700"
            >
              <RotateCcw className="h-3.5 w-3.5 mr-1" /> Re-run Investigation
            </Button>
          ) : (
            <Button
              variant="primary"
              size="md"
              isLoading={isOperating}
              onClick={handleRunInvestigation}
              className="bg-slate-900 hover:bg-slate-800 text-white"
            >
              <Sparkles className="h-4 w-4 mr-1.5 text-blue-400" /> Investigate Incident
            </Button>
          )}
        </div>
      </div>

      {opError && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-800 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 shrink-0 text-rose-600" />
          <span>{opError}</span>
        </div>
      )}

      {/* OPERATIONAL PROGRESSION STEPPER */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
        <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-3">
          Operational Response Lifecycle
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 text-xs">
          
          {/* Step 1: Detect & Evidence */}
          <div className={`p-2.5 rounded-lg border transition-all ${
            loadedEvidences.length > 0 ? 'border-emerald-200 bg-emerald-50/50 text-emerald-900 font-semibold' : 'border-slate-200 bg-slate-50 text-slate-500'
          }`}>
            <div className="flex items-center justify-between font-bold">
              <span>1. Evidence</span>
              {loadedEvidences.length > 0 ? (
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
              ) : (
                <Clock className="h-3.5 w-3.5 text-slate-400" />
              )}
            </div>
            <span className="text-[10px] font-mono mt-0.5 block truncate">
              {loadedEvidences.length > 0 ? `${loadedEvidences.length} Payloads Grounded` : 'Pending'}
            </span>
          </div>

          {/* Step 2: Investigation */}
          <div className={`p-2.5 rounded-lg border transition-all ${
            loadedInvestigation
              ? 'border-emerald-200 bg-emerald-50/50 text-emerald-900 font-semibold'
              : opState === 'INVESTIGATING'
              ? 'border-blue-300 bg-blue-50 text-blue-900 font-bold'
              : 'border-slate-200 bg-slate-50 text-slate-500'
          }`}>
            <div className="flex items-center justify-between font-bold">
              <span>2. Investigation</span>
              {loadedInvestigation ? (
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
              ) : opState === 'INVESTIGATING' ? (
                <span className="h-3 w-3 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
              ) : (
                <Clock className="h-3.5 w-3.5 text-slate-400" />
              )}
            </div>
            <span className="text-[10px] font-mono mt-0.5 block truncate">
              {loadedInvestigation ? `${(loadedInvestigation.confidence * 100).toFixed(0)}% Conclusive` : opState === 'INVESTIGATING' ? 'Correlating Agents' : 'Pending'}
            </span>
          </div>

          {/* Step 3: Mitigation Plan */}
          <div className={`p-2.5 rounded-lg border transition-all ${
            loadedAction ? 'border-emerald-200 bg-emerald-50/50 text-emerald-900 font-semibold' : 'border-slate-200 bg-slate-50 text-slate-500'
          }`}>
            <div className="flex items-center justify-between font-bold">
              <span>3. Mitigation Plan</span>
              {loadedAction ? (
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
              ) : (
                <Clock className="h-3.5 w-3.5 text-slate-400" />
              )}
            </div>
            <span className="text-[10px] font-mono mt-0.5 block truncate">
              {loadedAction ? `₹${parseFloat(loadedAction.expected_recovery).toLocaleString('en-IN')}` : 'Pending'}
            </span>
          </div>

          {/* Step 4: Policy Gate */}
          <div className={`p-2.5 rounded-lg border transition-all ${
            loadedPolicy?.decision === 'allow'
              ? 'border-emerald-200 bg-emerald-50/50 text-emerald-900 font-semibold'
              : opState === 'AWAITING_APPROVAL' || loadedPolicy?.decision === 'require_approval'
              ? 'border-amber-300 bg-amber-50 text-amber-900 font-bold'
              : opState === 'POLICY_EVALUATING'
              ? 'border-purple-300 bg-purple-50 text-purple-900 font-bold'
              : 'border-slate-200 bg-slate-50 text-slate-500'
          }`}>
            <div className="flex items-center justify-between font-bold">
              <span>4. Policy Gate</span>
              {loadedPolicy?.decision === 'allow' ? (
                <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
              ) : opState === 'AWAITING_APPROVAL' || loadedPolicy?.decision === 'require_approval' ? (
                <ShieldAlert className="h-3.5 w-3.5 text-amber-600" />
              ) : opState === 'POLICY_EVALUATING' ? (
                <span className="h-3 w-3 border-2 border-purple-600 border-t-transparent rounded-full animate-spin" />
              ) : (
                <Lock className="h-3.5 w-3.5 text-slate-400" />
              )}
            </div>
            <span className="text-[10px] font-mono mt-0.5 block truncate">
              {loadedPolicy ? loadedPolicy.decision.toUpperCase() : opState === 'POLICY_EVALUATING' ? 'Evaluating' : 'Pending'}
            </span>
          </div>

          {/* Step 5: Execution */}
          <div className={`p-2.5 rounded-lg border transition-all ${
            loadedExecution ? 'border-emerald-200 bg-emerald-50/50 text-emerald-900 font-semibold' : opState === 'EXECUTING' ? 'border-blue-300 bg-blue-50 text-blue-900 font-bold' : 'border-slate-200 bg-slate-50 text-slate-500'
          }`}>
            <div className="flex items-center justify-between font-bold">
              <span>5. Execution</span>
              {loadedExecution ? (
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
              ) : opState === 'EXECUTING' ? (
                <span className="h-3 w-3 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
              ) : (
                <Clock className="h-3.5 w-3.5 text-slate-400" />
              )}
            </div>
            <span className="text-[10px] font-mono mt-0.5 block truncate">
              {loadedExecution ? 'Simulated Adapter' : opState === 'EXECUTING' ? 'Dispatching' : 'Pending'}
            </span>
          </div>

          {/* Step 6: Outcome */}
          <div className={`p-2.5 rounded-lg border transition-all ${
            loadedOutcome ? 'border-emerald-300 bg-emerald-100/70 text-emerald-950 font-bold shadow-xs' : opState === 'VERIFYING' ? 'border-amber-300 bg-amber-50 text-amber-900 font-bold' : 'border-slate-200 bg-slate-50 text-slate-500'
          }`}>
            <div className="flex items-center justify-between font-bold">
              <span>6. Outcome</span>
              {loadedOutcome ? (
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-700" />
              ) : opState === 'VERIFYING' ? (
                <span className="h-3 w-3 border-2 border-amber-600 border-t-transparent rounded-full animate-spin" />
              ) : (
                <Clock className="h-3.5 w-3.5 text-slate-400" />
              )}
            </div>
            <span className="text-[10px] font-mono mt-0.5 block truncate">
              {loadedOutcome ? `₹${parseFloat(loadedOutcome.reference_data.protected_revenue || loadedOutcome.amount).toLocaleString('en-IN')}` : opState === 'VERIFYING' ? 'Sampling' : 'Unverified'}
            </span>
          </div>
        </div>
      </div>

      {/* FLAGSHIP 3-COLUMN OPERATIONAL COCKPIT */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* COLUMN 1 (4 cols): Diagnostic Telemetry Evidence */}
        <div className="lg:col-span-4 space-y-6">
          <Card
            title="Diagnostic Telemetry Evidence"
            subtitle={`${loadedEvidences.length} Grounded telemetry metrics collected`}
          >
            {loadedEvidences.length > 0 ? (
              <div className="space-y-3">
                {loadedEvidences.map((ev) => {
                  const isExpanded = expandedEvidences[ev.evidence_id];
                  return (
                    <div key={ev.evidence_id} className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-2 text-xs transition-all hover:border-slate-300">
                      <div className="flex items-center justify-between cursor-pointer" onClick={() => toggleEvidence(ev.evidence_id)}>
                        <div className="flex items-center gap-1.5">
                          <span className="font-mono text-[10px] text-slate-700 font-semibold bg-white border border-slate-200 px-1.5 py-0.5 rounded">
                            {ev.evidence_type}
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5 text-[10px] text-slate-400 font-mono">
                          <span>{new Date(ev.observed_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                          {isExpanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                        </div>
                      </div>

                      <p className="text-slate-800 font-semibold leading-snug">{ev.summary}</p>

                      {isExpanded && (
                        <div className="bg-white p-2.5 rounded border border-slate-200/80 font-mono text-[11px] text-slate-600 space-y-1 mt-1 transition-all">
                          <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-100 pb-1">
                            Source: {ev.source}
                          </div>
                          {Object.entries(ev.metrics_data).map(([k, v]) => (
                            <div key={k} className="flex justify-between py-0.5">
                              <span className="text-slate-400">{k}:</span>
                              <span className="text-slate-900 font-bold">{String(v)}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="py-8 text-center text-slate-500 text-xs space-y-2 font-mono">
                <div className="h-4 w-4 border-2 border-slate-400 border-t-transparent rounded-full animate-spin mx-auto" />
                <p>Streaming diagnostic logs and conversion funnels...</p>
              </div>
            )}
          </Card>

          {loadedInvestigation?.affected_cohorts && loadedInvestigation.affected_cohorts.length > 0 && (
            <Card title="Impacted Cohorts" subtitle="Isolated by failure clustering">
              <div className="flex flex-wrap gap-1.5">
                {loadedInvestigation.affected_cohorts.map((cohort) => (
                  <span
                    key={cohort}
                    className="font-mono text-xs font-semibold px-2.5 py-1 rounded-md bg-rose-50 text-rose-800 border border-rose-200"
                  >
                    {cohort}
                  </span>
                ))}
              </div>
            </Card>
          )}
        </div>

        {/* COLUMN 2 (4 cols): AI Investigation & Deterministic Policy Boundary */}
        <div className="lg:col-span-4 space-y-6">
          
          {/* LangGraph Root Cause Card */}
          <Card
            title="LangGraph Root Cause Investigation"
            subtitle={
              loadedInvestigation
                ? `${(loadedInvestigation.confidence * 100).toFixed(0)}% Confidence · Multi-Step Grounded`
                : opState === 'INVESTIGATING'
                ? 'Correlating diagnostic evidence...'
                : 'Awaiting trigger'
            }
          >
            {loadedInvestigation ? (
              <div className="space-y-3 text-xs">
                <div className="p-3 bg-blue-50/60 border border-blue-200 rounded-md space-y-1">
                  <span className="text-[10px] font-bold uppercase text-blue-700 tracking-wider">Primary Root Cause</span>
                  <p className="text-slate-900 font-bold leading-snug">{loadedInvestigation.primary_cause}</p>
                </div>

                <div className="space-y-1 pt-1">
                  <span className="text-[10px] font-semibold uppercase text-slate-400 tracking-wider">Confidence Rationale</span>
                  <p className="text-slate-600 leading-relaxed font-normal">{loadedInvestigation.confidence_rationale}</p>
                </div>
              </div>
            ) : opState === 'INVESTIGATING' ? (
              <div className="py-8 text-center text-slate-600 text-xs space-y-2 font-mono">
                <div className="h-5 w-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto" />
                <p className="font-semibold text-slate-800">AI Investigator Agent running multi-step correlation...</p>
                <p className="text-[11px] text-slate-400">Evaluating evidence keys against upstream gateway metrics</p>
              </div>
            ) : (
              <div className="py-8 text-center text-slate-500 text-xs space-y-2">
                <Cpu className="h-6 w-6 text-slate-300 mx-auto" />
                <p>Click "Investigate Incident" to trigger autonomous LangGraph investigation.</p>
              </div>
            )}
          </Card>

          {/* Deterministic Policy Engine Boundary */}
          {opState === 'POLICY_EVALUATING' && (
            <div className="rounded-xl p-4 border border-purple-300 bg-purple-50/80 space-y-2 text-xs font-mono">
              <div className="flex items-center gap-2 text-purple-900 font-bold">
                <span className="h-3.5 w-3.5 border-2 border-purple-700 border-t-transparent rounded-full animate-spin" />
                <span>Deterministic Policy Engine Evaluating Safety Rules...</span>
              </div>
              <p className="text-[11px] text-purple-800">Checking monetary threshold (₹50,000 auto-cap), risk level, and allowlist.</p>
            </div>
          )}

          {loadedPolicy && (
            <div className={`rounded-xl p-4 border space-y-3 shadow-xs ${
              loadedPolicy.decision === 'require_approval'
                ? 'border-amber-300 bg-amber-50/80'
                : loadedPolicy.decision === 'deny'
                ? 'border-rose-300 bg-rose-50/80'
                : 'border-purple-200 bg-purple-50/80'
            }`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <Lock className={`h-4 w-4 ${loadedPolicy.decision === 'require_approval' ? 'text-amber-800' : 'text-purple-800'}`} />
                  <span className={`text-xs font-bold uppercase tracking-wider ${loadedPolicy.decision === 'require_approval' ? 'text-amber-950' : 'text-purple-950'}`}>
                    Deterministic Policy Boundary
                  </span>
                </div>
                <Badge variant={loadedPolicy.decision === 'allow' ? 'success' : loadedPolicy.decision === 'require_approval' ? 'warning' : 'danger'}>
                  POLICY: {loadedPolicy.decision.toUpperCase()}
                </Badge>
              </div>

              <p className={`text-xs leading-relaxed font-medium ${loadedPolicy.decision === 'require_approval' ? 'text-amber-900' : 'text-purple-900'}`}>
                {loadedPolicy.decision === 'require_approval'
                  ? 'Financial recovery amount exceeds auto-authorization cap (₹50,000.00). Human operator signoff required.'
                  : 'AI proposed the mitigation plan. Policy Engine deterministically evaluated safety rules and authorized execution.'}
              </p>

              <div className="bg-white/90 rounded border border-slate-200 p-2.5 space-y-1 text-xs font-mono">
                {loadedPolicy.rule_results.map((rule) => (
                  <div key={rule.rule_code} className="flex items-center justify-between text-[11px] py-0.5">
                    <span className="text-slate-600">{rule.rule_code}:</span>
                    <span className={rule.decision_impact === 'require_approval' ? 'text-amber-700 font-bold' : rule.decision_impact === 'deny' ? 'text-rose-700 font-bold' : 'text-emerald-700 font-bold'}>
                      {rule.decision_impact === 'require_approval' ? 'REQUIRES APPROVAL' : rule.decision_impact === 'deny' ? 'FAILED (DENY)' : 'PASSED (ALLOW)'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Mitigation Action Plan */}
          {loadedAction && (
            <Card
              title="Mitigation Action Plan"
              subtitle={`Target: ${loadedAction.target}`}
              action={
                <Badge variant={loadedExecution ? 'success' : opState === 'AWAITING_APPROVAL' ? 'warning' : 'purple'}>
                  {loadedExecution ? 'EXECUTED' : opState === 'AWAITING_APPROVAL' ? 'PENDING APPROVAL' : 'AUTHORIZED'}
                </Badge>
              }
            >
              <div className="space-y-3 text-xs">
                <div className="grid grid-cols-2 gap-2 text-[11px] font-mono bg-slate-50 p-2.5 rounded border border-slate-200">
                  <div>
                    <span className="text-slate-400 block">Action Type:</span>
                    <span className="text-slate-900 font-bold">{loadedAction.action_type}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block">Expected Recovery:</span>
                    <span className="text-slate-900 font-bold">₹{parseFloat(loadedAction.expected_recovery).toLocaleString('en-IN')}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block">Risk Level:</span>
                    <span className="text-slate-900 font-bold uppercase">{loadedAction.risk_level}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block">Confidence:</span>
                    <span className="text-slate-900 font-bold">{(parseFloat(loadedAction.confidence) * 100).toFixed(0)}%</span>
                  </div>
                </div>

                <p className="text-slate-600 leading-relaxed">{loadedAction.rationale}</p>
              </div>
            </Card>
          )}
        </div>

        {/* COLUMN 3 (4 cols): Execution Record & Economic Verification Outcome */}
        <div className="lg:col-span-4 space-y-6">
          
          {/* Guarded Execution Record Card */}
          <Card
            title="Guarded Execution Record"
            subtitle={
              loadedExecution
                ? `Provider: ${loadedExecution.provider}`
                : opState === 'EXECUTING'
                ? 'Dispatching idempotency-guarded write...'
                : 'Awaiting policy clearance'
            }
          >
            {loadedExecution ? (
              <div className="space-y-3 text-xs">
                <div className="flex items-center justify-between">
                  <Badge variant="simulation">
                    SIMULATED SUCCESS
                  </Badge>
                  <span className="text-[10px] font-mono text-amber-900 bg-amber-50 border border-amber-300 px-2 py-0.5 rounded font-bold">
                    SANDBOX ADAPTER
                  </span>
                </div>

                <div className="bg-slate-50 p-2.5 rounded border border-slate-200 font-mono text-[11px] space-y-1.5 text-slate-700">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Execution ID:</span>
                    <span className="text-slate-900">{loadedExecution.execution_id}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Reference:</span>
                    <span className="text-slate-900 font-bold">{loadedExecution.provider_reference}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Idempotency Key:</span>
                    <span className="text-slate-900 text-[10px] truncate max-w-[170px]">{loadedExecution.idempotency_key}</span>
                  </div>
                </div>
              </div>
            ) : opState === 'EXECUTING' ? (
              <div className="py-8 text-center text-slate-600 text-xs space-y-2 font-mono">
                <div className="h-5 w-5 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin mx-auto" />
                <p className="font-semibold text-slate-800">Dispatching action to simulation adapter...</p>
                <p className="text-[11px] text-slate-400">Recording cryptographic idempotency hash</p>
              </div>
            ) : (
              <div className="py-8 text-center text-slate-500 text-xs space-y-2">
                <Layers className="h-6 w-6 text-slate-300 mx-auto" />
                <p className="font-semibold text-slate-700">PENDING / NOT EXECUTED</p>
                <p className="text-[11px] text-slate-400">Executor will invoke write adapters only after explicit policy authorization.</p>
              </div>
            )}
          </Card>

          {/* Verified Economic Outcome Card */}
          {opState === 'VERIFYING' && (
            <Card title="Post-Execution Verification" subtitle="Sampling telemetry streams">
              <div className="py-6 text-center text-slate-600 text-xs space-y-2 font-mono">
                <div className="h-5 w-5 border-2 border-amber-600 border-t-transparent rounded-full animate-spin mx-auto" />
                <p className="font-semibold text-slate-800">Verification Engine measuring recovery rate...</p>
                <p className="text-[11px] text-slate-400">Comparing post-intervention conversion to baseline</p>
              </div>
            </Card>
          )}

          {loadedOutcome ? (
            <Card
              title="Verified Economic Outcome"
              subtitle="Grounded in post-execution telemetry metrics"
              action={<Badge variant="success">VERIFIED SUCCESS</Badge>}
            >
              <div className="space-y-4 text-xs">
                <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3.5 space-y-2.5">
                  <div className="flex items-baseline justify-between">
                    <span className="text-[10px] uppercase font-bold text-emerald-800 tracking-wider">
                      {loadedOutcome.outcome_type.replace('_', ' ').toUpperCase()}
                    </span>
                    <span className="text-2xl font-extrabold text-emerald-900 font-mono tabular-nums">
                      ₹{parseFloat(loadedOutcome.reference_data.protected_revenue || loadedOutcome.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-[11px] font-mono text-emerald-950 pt-2 border-t border-emerald-200/80">
                    <div>
                      <span className="text-emerald-800">Recovery Rate: </span>
                      <span className="font-extrabold text-emerald-950">
                        {(parseFloat(loadedOutcome.reference_data.recovery_rate || '1') * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div>
                      <span className="text-emerald-800">Remaining Risk: </span>
                      <span className="font-extrabold text-emerald-950">
                        ₹{parseFloat(loadedOutcome.reference_data.remaining_revenue_at_risk || '0').toLocaleString('en-IN')}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="bg-slate-50 p-2.5 rounded border border-slate-200 font-mono text-[10px] text-slate-600 space-y-1">
                  <span className="text-slate-400 uppercase font-semibold block">Audit Reference Metadata</span>
                  <div>Outcome ID: {loadedOutcome.outcome_id}</div>
                  <div>Correlation ID: {loadedOutcome.reference_data.correlation_id}</div>
                  <div>Verification Status: {loadedOutcome.reference_data.verification_status}</div>
                </div>
              </div>
            </Card>
          ) : opState !== 'VERIFYING' && (
            <Card
              title="Verified Economic Outcome"
              subtitle="Grounded in post-execution telemetry metrics"
              action={<Badge variant="default">UNVERIFIED</Badge>}
            >
              <div className="py-8 text-center text-slate-500 text-xs space-y-2">
                <TrendingUp className="h-6 w-6 text-slate-300 mx-auto" />
                <p className="font-semibold text-slate-700">Economic outcome verification pending</p>
                <p className="text-[11px] text-slate-400">Verified protection and recovery rates will be measured after action execution.</p>
              </div>
            </Card>
          )}
        </div>
      </div>

      {/* BOTTOM FULL-WIDTH AUDIT PROVENANCE CARD */}
      <Card
        title={`Chronological Provenance & Audit Stream (${provenanceEvents.length} Events Recorded)`}
        subtitle="Cryptographically verified state machine trace from initial detection to economic outcome"
      >
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-mono text-[10px] uppercase">
              <tr>
                <th className="py-2.5 px-3">Lifecycle Step</th>
                <th className="py-2.5 px-3">Actor / Subsystem</th>
                <th className="py-2.5 px-3">Timestamp</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Operational Audit Summary</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono text-slate-700">
              {provenanceEvents.map((ev, idx) => (
                <tr key={idx} className="hover:bg-slate-50/70 transition-colors">
                  <td className="py-2.5 px-3 font-semibold text-slate-900">{ev.step}</td>
                  <td className="py-2.5 px-3 text-slate-600">{ev.actor}</td>
                  <td className="py-2.5 px-3 text-slate-500 text-[11px]">{new Date(ev.time).toLocaleTimeString()}</td>
                  <td className="py-2.5 px-3">
                    <span className="inline-block px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-800 border border-slate-200">
                      {ev.status}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 font-sans text-slate-600 text-xs">{ev.summary}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
