import React from 'react';
import { Link } from 'react-router-dom';
import { TrendingUp, CheckCircle2, ShieldCheck, ArrowRight } from 'lucide-react';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { MetricCard } from '../components/common/MetricCard';
import { MOCK_INCIDENTS_CONTEXT } from '../services/mockData';

export const OutcomesPage: React.FC = () => {
  const outcomesList = Object.values(MOCK_INCIDENTS_CONTEXT)
    .filter((ctx) => ctx.outcome)
    .map((ctx) => ({
      ...ctx.outcome!,
      incidentDescription: ctx.incident.description,
    }));

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Verified Economic Outcomes</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Cryptographically auditable ledger of protected and recovered revenue resulting from verified mitigations.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <MetricCard
          label="Total Verified Economic Impact"
          value="₹35,000.00"
          subValue="1 Incident Verified"
          change="₹35,000 Protected"
          changeType="positive"
          icon={<TrendingUp className="h-4 w-4 text-emerald-600" />}
        />
        <MetricCard
          label="Average Recovery Rate"
          value="77.8%"
          subValue="Across executed mitigations"
          changeType="neutral"
          icon={<ShieldCheck className="h-4 w-4" />}
        />
        <MetricCard
          label="Verification Method"
          value="Deterministic"
          subValue="Grounded post-telemetry metrics"
          change="Zero AI Arithmetic"
          changeType="positive"
        />
      </div>

      <Card title="Economic Outcomes Ledger">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500 bg-slate-50/50">
                <th className="py-2.5 px-3 font-semibold">OUTCOME ID</th>
                <th className="py-2.5 px-3 font-semibold">TYPE</th>
                <th className="py-2.5 px-3 font-semibold">TOTAL IMPACT</th>
                <th className="py-2.5 px-3 font-semibold">RECOVERY RATE</th>
                <th className="py-2.5 px-3 font-semibold">STATUS</th>
                <th className="py-2.5 px-3 font-semibold">MEASURED AT</th>
                <th className="py-2.5 px-3 font-semibold text-right">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {outcomesList.map((out) => (
                <tr key={out.outcome_id} className="hover:bg-slate-50 transition-colors">
                  <td className="py-3 px-3">
                    <div className="flex flex-col font-mono">
                      <span className="font-semibold text-slate-900">{out.outcome_id}</span>
                      <span className="text-[10px] text-slate-400 mt-0.5">Incident: {out.incident_id}</span>
                    </div>
                  </td>
                  <td className="py-3 px-3">
                    <span className="font-mono text-[11px] text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 font-semibold">
                      {out.outcome_type.replace('_', ' ').toUpperCase()}
                    </span>
                  </td>
                  <td className="py-3 px-3 font-mono font-bold text-slate-900 tabular-nums">
                    ₹{parseFloat(out.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="py-3 px-3 font-mono text-slate-700 font-semibold tabular-nums">
                    {(parseFloat(out.reference_data.recovery_rate || '0') * 100).toFixed(1)}%
                  </td>
                  <td className="py-3 px-3">
                    <Badge variant="success">VERIFIED</Badge>
                  </td>
                  <td className="py-3 px-3 text-slate-500 font-mono text-[11px]">
                    {new Date(out.measured_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </td>
                  <td className="py-3 px-3 text-right">
                    <Link to={`/app/incidents/${out.incident_id}`}>
                      <Button variant="outline" size="sm">
                        Inspect Cockpit
                      </Button>
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
