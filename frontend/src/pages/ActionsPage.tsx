import React from 'react';
import { Link } from 'react-router-dom';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { MOCK_INCIDENTS_CONTEXT } from '../services/mockData';

export const ActionsPage: React.FC = () => {
  const actionsList = Object.values(MOCK_INCIDENTS_CONTEXT)
    .filter((ctx) => ctx.proposed_action)
    .map((ctx) => ({
      ...ctx.proposed_action!,
      incidentDescription: ctx.incident.description,
      incidentSeverity: ctx.incident.severity,
    }));

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Mitigation Actions Queue</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Proposed, authorized, executing, and completed mitigation action plans.
          </p>
        </div>
      </div>

      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500 bg-slate-50/50">
                <th className="py-2.5 px-3 font-semibold">ACTION ID & TARGET</th>
                <th className="py-2.5 px-3 font-semibold">TYPE</th>
                <th className="py-2.5 px-3 font-semibold">INCIDENT CONTEXT</th>
                <th className="py-2.5 px-3 font-semibold">EXPECTED RECOVERY</th>
                <th className="py-2.5 px-3 font-semibold">RISK LEVEL</th>
                <th className="py-2.5 px-3 font-semibold">STATUS</th>
                <th className="py-2.5 px-3 font-semibold text-right">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {actionsList.map((act) => (
                <tr key={act.action_id} className="hover:bg-slate-50 transition-colors">
                  <td className="py-3 px-3">
                    <div className="flex flex-col">
                      <span className="font-semibold text-slate-900 font-mono">{act.target}</span>
                      <span className="text-[10px] text-slate-400 font-mono mt-0.5">{act.action_id}</span>
                    </div>
                  </td>
                  <td className="py-3 px-3">
                    <span className="font-mono text-[11px] text-slate-700 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200">
                      {act.action_type}
                    </span>
                  </td>
                  <td className="py-3 px-3">
                    <span className="text-slate-600 truncate max-w-[200px] block">{act.incidentDescription}</span>
                  </td>
                  <td className="py-3 px-3 font-mono font-semibold text-slate-900 tabular-nums">
                    ₹{parseFloat(act.expected_recovery).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="py-3 px-3">
                    <Badge variant={act.risk_level === 'low' ? 'success' : act.risk_level === 'medium' ? 'warning' : 'danger'}>
                      {act.risk_level.toUpperCase()}
                    </Badge>
                  </td>
                  <td className="py-3 px-3">
                    <Badge
                      variant={
                        act.status === 'completed'
                          ? 'success'
                          : act.status === 'executing'
                          ? 'info'
                          : act.status === 'approved'
                          ? 'purple'
                          : 'warning'
                      }
                    >
                      {act.status.toUpperCase()}
                    </Badge>
                  </td>
                  <td className="py-3 px-3 text-right">
                    <Link to={`/app/incidents/${act.incident_id}`}>
                      <Button variant="outline" size="sm">
                        View in Cockpit
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
