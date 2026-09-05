import React from 'react';
import { ScrollText, ShieldCheck, ArrowRight, ExternalLink } from 'lucide-react';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { MOCK_INCIDENTS_CONTEXT } from '../services/mockData';
import { Link } from 'react-router-dom';

export const AuditTrailPage: React.FC = () => {
  const auditEntries = [
    {
      id: 'aud_101',
      timestamp: new Date(Date.now() - 20 * 60 * 1000).toISOString(),
      type: 'VERIFICATION_OUTCOME',
      incident_id: 'inc_hdfc_drop_01',
      action_id: 'act_reroute_01',
      correlation_id: 'corr-hdfc-01',
      summary: 'Verified economic protection of ₹35,000.00 (Recovery Rate: 77.8%). Incident transitioned to RESOLVED.',
      status: 'VERIFIED_SUCCESS',
    },
    {
      id: 'aud_102',
      timestamp: new Date(Date.now() - 25 * 60 * 1000).toISOString(),
      type: 'ACTION_EXECUTION',
      incident_id: 'inc_hdfc_drop_01',
      action_id: 'act_reroute_01',
      correlation_id: 'corr-hdfc-01',
      summary: 'Action plan dispatched to simulation adapter. Idempotency key exec_act_reroute_01_1725540000 recorded.',
      status: 'SIMULATED',
    },
    {
      id: 'aud_103',
      timestamp: new Date(Date.now() - 28 * 60 * 1000).toISOString(),
      type: 'POLICY_EVALUATION',
      incident_id: 'inc_hdfc_drop_01',
      action_id: 'act_reroute_01',
      correlation_id: 'corr-hdfc-01',
      summary: 'Deterministic Policy Engine evaluated 6 rules: ALLOW decision recorded under Policy v1.0.0.',
      status: 'ALLOW',
    },
    {
      id: 'aud_104',
      timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
      type: 'PLANNER_PROPOSAL',
      incident_id: 'inc_hdfc_drop_01',
      action_id: 'act_reroute_01',
      correlation_id: 'corr-hdfc-01',
      summary: 'Recovery Planner agent proposed GATEWAY_REROUTE to secondary Axis aggregation rail.',
      status: 'PROPOSED',
    },
    {
      id: 'aud_105',
      timestamp: new Date(Date.now() - 42 * 60 * 1000).toISOString(),
      type: 'INCIDENT_DETECTION',
      incident_id: 'inc_hdfc_drop_01',
      action_id: '-',
      correlation_id: 'corr-hdfc-01',
      summary: 'Payment drop spike detected on HDFC Netbanking. Revenue at risk scoped to ₹45,000.00.',
      status: 'DETECTED',
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Audit Trail & Provenance</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Immutable log tracing every state transition from telemetry detection to economic recovery verification.
          </p>
        </div>
      </div>

      <Card title="Operational Audit Ledger">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500 bg-slate-50/50">
                <th className="py-2.5 px-3 font-semibold">EVENT & TIMESTAMP</th>
                <th className="py-2.5 px-3 font-semibold">STAGE</th>
                <th className="py-2.5 px-3 font-semibold">INCIDENT / CORRELATION ID</th>
                <th className="py-2.5 px-3 font-semibold">EVENT SUMMARY</th>
                <th className="py-2.5 px-3 font-semibold">OUTCOME</th>
                <th className="py-2.5 px-3 font-semibold text-right">VIEW</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {auditEntries.map((aud) => (
                <tr key={aud.id} className="hover:bg-slate-50 transition-colors">
                  <td className="py-3 px-3 font-mono">
                    <span className="font-semibold text-slate-900">{aud.id}</span>
                    <span className="text-[10px] text-slate-400 block mt-0.5">
                      {new Date(aud.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </span>
                  </td>
                  <td className="py-3 px-3">
                    <span className="font-mono text-[10px] text-slate-700 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200">
                      {aud.type}
                    </span>
                  </td>
                  <td className="py-3 px-3 font-mono text-[11px] text-slate-600">
                    <div>{aud.incident_id}</div>
                    <div className="text-[10px] text-slate-400">{aud.correlation_id}</div>
                  </td>
                  <td className="py-3 px-3 text-slate-700 max-w-sm">{aud.summary}</td>
                  <td className="py-3 px-3">
                    <Badge variant={aud.status === 'VERIFIED_SUCCESS' || aud.status === 'ALLOW' ? 'success' : 'default'}>
                      {aud.status}
                    </Badge>
                  </td>
                  <td className="py-3 px-3 text-right">
                    <Link to={`/app/incidents/${aud.incident_id}`}>
                      <ExternalLink className="h-3.5 w-3.5 text-slate-400 hover:text-slate-900 inline" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
