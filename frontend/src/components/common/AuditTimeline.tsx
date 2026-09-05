import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, Clock, ShieldAlert, Cpu, ArrowRight } from 'lucide-react';
import { FullIncidentContext } from '../../types/domain';

interface AuditTimelineProps {
  context: FullIncidentContext;
}

export const AuditTimeline: React.FC<AuditTimelineProps> = ({ context }) => {
  const { incident, evidences, investigation, proposed_action, policy_decision, execution_result, outcome } = context;

  const steps = [
    {
      id: 'detected',
      title: 'Incident Detected',
      status: 'completed',
      time: incident.detected_at,
      desc: `Anomaly type: ${incident.incident_type} (${incident.severity.toUpperCase()} severity)`,
      meta: `Exposure: ₹${parseFloat(incident.revenue_at_risk).toLocaleString('en-IN')}`,
    },
    {
      id: 'evidence',
      title: 'Diagnostic Evidence Grounded',
      status: evidences && evidences.length > 0 ? 'completed' : 'pending',
      desc: `${evidences?.length || 0} diagnostic evidence payloads collected from telemetry streams`,
      meta: evidences?.[0]?.source || 'telemetry_stream',
    },
    {
      id: 'investigation',
      title: 'LangGraph Root Cause Analysis',
      status: investigation ? 'completed' : incident.status === 'investigating' ? 'in_progress' : 'pending',
      desc: investigation ? investigation.primary_cause : 'Awaiting automated diagnostic investigation',
      meta: investigation ? `${Math.round(investigation.confidence * 100)}% Confidence` : undefined,
    },
    {
      id: 'plan',
      title: 'Mitigation Plan Proposed',
      status: proposed_action ? 'completed' : 'pending',
      desc: proposed_action ? `Action: ${proposed_action.action_type} on target [${proposed_action.target}]` : 'Awaiting mitigation plan proposal',
      meta: proposed_action ? `Expected: ₹${parseFloat(proposed_action.expected_recovery).toLocaleString('en-IN')}` : undefined,
    },
    {
      id: 'policy',
      title: 'Deterministic Policy Evaluation',
      status: policy_decision ? 'completed' : 'pending',
      desc: policy_decision
        ? `Policy decision: ${policy_decision.decision.toUpperCase()} (Version ${policy_decision.policy_version})`
        : 'Awaiting deterministic rule validation',
      meta: policy_decision ? `${policy_decision.rule_results.filter(r => r.passed).length}/${policy_decision.rule_results.length} Rules Passed` : undefined,
    },
    {
      id: 'execution',
      title: 'Guarded Execution',
      status: execution_result ? 'completed' : proposed_action?.status === 'executing' ? 'in_progress' : 'pending',
      desc: execution_result
        ? `Executed via ${execution_result.provider} (${execution_result.is_simulated ? 'SIMULATED SANDBOX' : 'RAZORPAY TEST MODE'})`
        : 'Awaiting authorized execution dispatch',
      meta: execution_result?.provider_reference || undefined,
    },
    {
      id: 'outcome',
      title: 'Economic Verification Outcome',
      status: outcome ? 'completed' : 'pending',
      desc: outcome
        ? `Verified impact: ₹${parseFloat(outcome.amount).toLocaleString('en-IN')} (${outcome.outcome_type.replace('_', ' ').toUpperCase()})`
        : 'Awaiting post-execution telemetry verification',
      meta: outcome?.reference_data?.recovery_rate ? `${(parseFloat(outcome.reference_data.recovery_rate) * 100).toFixed(1)}% Recovery Rate` : undefined,
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flow-root">
        <ul className="-mb-8">
          {steps.map((step, stepIdx) => (
            <li key={step.id}>
              <div className="relative pb-8">
                {stepIdx !== steps.length - 1 ? (
                  <span
                    className={`absolute top-4 left-4 -ml-px h-full w-0.5 ${
                      step.status === 'completed' ? 'bg-emerald-500' : 'bg-slate-200'
                    }`}
                    aria-hidden="true"
                  />
                ) : null}
                <div className="relative flex space-x-3 items-start">
                  <div>
                    {step.status === 'completed' ? (
                      <span className="h-8 w-8 rounded-full bg-emerald-100 flex items-center justify-center ring-4 ring-white">
                        <CheckCircle2 className="h-4 w-4 text-emerald-700" />
                      </span>
                    ) : step.status === 'in_progress' ? (
                      <span className="h-8 w-8 rounded-full bg-indigo-100 flex items-center justify-center ring-4 ring-white animate-pulse">
                        <Clock className="h-4 w-4 text-indigo-700" />
                      </span>
                    ) : (
                      <span className="h-8 w-8 rounded-full bg-slate-100 flex items-center justify-center ring-4 ring-white">
                        <div className="h-2 w-2 rounded-full bg-slate-400" />
                      </span>
                    )}
                  </div>
                  <div className="min-w-0 flex-1 pt-1 flex justify-between space-x-4">
                    <div>
                      <p className={`text-sm font-semibold ${step.status === 'completed' ? 'text-slate-900' : 'text-slate-500'}`}>
                        {step.title}
                      </p>
                      <p className="text-xs text-slate-600 mt-0.5">{step.desc}</p>
                    </div>
                    {step.meta && (
                      <div className="text-right text-xs whitespace-nowrap text-slate-500 font-mono">
                        {step.meta}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};
