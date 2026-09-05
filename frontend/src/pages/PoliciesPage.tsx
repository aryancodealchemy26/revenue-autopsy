import React from 'react';
import { ShieldCheck, ShieldAlert, Lock, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';

export const PoliciesPage: React.FC = () => {
  const policyRules = [
    {
      code: 'INPUT_INTEGRITY',
      name: 'Tenant Isolation & Format Integrity',
      type: 'Security Guard',
      desc: 'Enforces caller merchant_id matching incident tenant, non-negative amounts, and recovery <= revenue at risk. Fails closed immediately on violation.',
      status: 'Enforcing',
    },
    {
      code: 'ACTION_ALLOWLIST',
      name: 'Mitigation Action Allowlist',
      type: 'Permission Boundary',
      desc: 'Permits only verified domain action types (GATEWAY_REROUTE, RETRY_PAYMENT, MERCHANT_ALERT, WEBHOOK_RESYNC, RATE_LIMIT_ADJUSTMENT). Unknown types are strictly DENIED.',
      status: 'Enforcing',
    },
    {
      code: 'MONETARY_LIMIT',
      name: 'Financial Exposure Thresholds',
      type: 'Monetary Cap',
      desc: 'Auto-allow cap: <= ₹50,000.00. Amounts > ₹50k require human approval. Absolute cap: <= ₹500,000.00 (amounts above are strictly DENIED).',
      status: 'Enforcing',
    },
    {
      code: 'RISK_THRESHOLD',
      name: 'Operational Risk Evaluation',
      type: 'Operational Safety',
      desc: 'High-risk actions always require manual human approval. Medium risk actions with recovery > ₹25,000 require human authorization.',
      status: 'Enforcing',
    },
    {
      code: 'CONFIDENCE_THRESHOLD',
      name: 'Confidence Bounds',
      type: 'Safety Guard',
      desc: 'Confidence >= 0.70 auto-allowed. Confidence 0.40 - 0.70 requires human verification. Confidence < 0.40 is strictly DENIED.',
      status: 'Enforcing',
    },
    {
      code: 'DUPLICATE_PROTECTION',
      name: 'Idempotency & Duplicate Prevention',
      type: 'Concurrency Safety',
      desc: 'Rejects concurrent active action plans targeting identical gateways or payment rails to prevent conflicting intervention races.',
      status: 'Enforcing',
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Deterministic Policy Engine</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Strict deterministic authorization boundary ensuring AI may propose mitigations, but never authorizes execution.
          </p>
        </div>
      </div>

      {/* Safety Boundary Banner */}
      <div className="bg-purple-900 text-white rounded-xl p-6 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="space-y-2 max-w-2xl">
          <div className="flex items-center gap-2">
            <span className="h-6 w-6 rounded bg-purple-800 flex items-center justify-center text-purple-200">
              <Lock className="h-3.5 w-3.5" />
            </span>
            <span className="text-xs font-bold uppercase tracking-wider text-purple-200">Security Architecture Boundary</span>
          </div>
          <h2 className="text-lg font-bold">AI Proposes. Policy Engine Authorizes.</h2>
          <p className="text-xs text-purple-200 leading-relaxed font-normal">
            Every recovery plan emitted by the LangGraph agent is treated as untrusted input. The Deterministic Policy Engine evaluates mathematical caps, tenant boundaries, and risk parameters before any action can be dispatched.
          </p>
        </div>

        <div className="bg-purple-950/80 border border-purple-800 rounded-lg p-4 font-mono text-xs space-y-1.5 shrink-0 min-w-[220px]">
          <div className="text-[10px] text-purple-300 font-semibold uppercase">Engine Limits (v1.0.0)</div>
          <div className="flex justify-between text-purple-200">
            <span>Auto-Allow Cap:</span>
            <span className="font-bold text-white">₹50,000.00</span>
          </div>
          <div className="flex justify-between text-purple-200">
            <span>Absolute Cap:</span>
            <span className="font-bold text-white">₹500,000.00</span>
          </div>
          <div className="flex justify-between text-purple-200">
            <span>Min Confidence:</span>
            <span className="font-bold text-white">0.40</span>
          </div>
        </div>
      </div>

      {/* Policy Rules Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {policyRules.map((rule) => (
          <Card key={rule.code} title={rule.name} subtitle={`Rule Code: ${rule.code}`}>
            <div className="space-y-3 text-xs">
              <p className="text-slate-600 leading-relaxed">{rule.desc}</p>
              <div className="flex items-center justify-between pt-2 border-t border-slate-100">
                <span className="font-mono text-[10px] text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                  {rule.type}
                </span>
                <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 font-mono">
                  <CheckCircle2 className="h-3 w-3" /> {rule.status}
                </span>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};
