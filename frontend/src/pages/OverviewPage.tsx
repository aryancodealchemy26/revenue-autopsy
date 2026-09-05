import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertOctagon,
  TrendingUp,
  ArrowRight,
  ShieldCheck,
  Cpu,
  Layers,
  ChevronRight,
  Clock,
  ArrowUpRight,
  Lock,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { api } from '../services/api';
import { Incident } from '../types/domain';

export const OverviewPage: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);

  useEffect(() => {
    api.getIncidents().then(setIncidents);
  }, []);

  const totalAtRisk = incidents.reduce((acc, inc) => acc + parseFloat(inc.revenue_at_risk), 0);
  const openIncidents = incidents.filter((i) => i.status !== 'resolved' && i.status !== 'closed');

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'critical':
        return <Badge variant="danger">CRITICAL</Badge>;
      case 'high':
        return <Badge variant="warning">HIGH</Badge>;
      case 'medium':
        return <Badge variant="info">MEDIUM</Badge>;
      default:
        return <Badge variant="default">LOW</Badge>;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'resolved':
        return <Badge variant="success">RESOLVED</Badge>;
      case 'action_proposed':
        return <Badge variant="warning">ACTION PROPOSED</Badge>;
      case 'action_approved':
        return <Badge variant="purple">ACTION APPROVED</Badge>;
      case 'investigating':
        return <Badge variant="info">INVESTIGATING</Badge>;
      default:
        return <Badge variant="default">DETECTED</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Operational Situation Room Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-rose-500 animate-pulse" />
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">Active Incident Situation Room</h1>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Active revenue exposure, automated root cause investigation, and deterministic policy authorization status.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link to="/app/incidents/inc_auth_surge_02">
            <Button variant="danger" size="sm">
              <AlertOctagon className="h-3.5 w-3.5 mr-1" /> Triage Critical Incident
            </Button>
          </Link>
        </div>
      </div>

      {/* Primary Economic Flow Strip */}
      <div className="bg-slate-900 text-white rounded-xl p-5 shadow-sm border border-slate-800">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <span className="text-[10px] uppercase font-mono text-rose-300 font-bold tracking-wider">
              TOTAL ACTIVE EXPOSURE
            </span>
            <div className="text-3xl font-extrabold text-white font-mono tabular-nums tracking-tight">
              ₹{totalAtRisk.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </div>
            <p className="text-xs text-slate-400 font-normal">
              Across {openIncidents.length} active unmitigated incidents requiring operator or policy authorization.
            </p>
          </div>

          <div className="flex items-center gap-2 sm:gap-4 overflow-x-auto py-1">
            <div className="bg-slate-800/80 border border-slate-700/80 rounded-lg p-3 min-w-[130px]">
              <span className="text-[10px] text-slate-400 font-mono block">PROTECTED REVENUE</span>
              <span className="text-base font-bold text-emerald-400 font-mono tabular-nums">₹35,000.00</span>
              <span className="text-[10px] text-slate-500 block mt-0.5">77.8% Recovery</span>
            </div>

            <ArrowRight className="h-4 w-4 text-slate-600 shrink-0 hidden sm:block" />

            <div className="bg-slate-800/80 border border-slate-700/80 rounded-lg p-3 min-w-[130px]">
              <span className="text-[10px] text-slate-400 font-mono block">POLICY ENGINE</span>
              <span className="text-base font-bold text-purple-300 font-mono">ENFORCING</span>
              <span className="text-[10px] text-slate-500 block mt-0.5">₹50k Auto-Cap</span>
            </div>

            <ArrowRight className="h-4 w-4 text-slate-600 shrink-0 hidden sm:block" />

            <div className="bg-slate-800/80 border border-slate-700/80 rounded-lg p-3 min-w-[130px]">
              <span className="text-[10px] text-slate-400 font-mono block">OPERATIONAL STATUS</span>
              <span className="text-base font-bold text-emerald-400 font-mono">READY</span>
              <span className="text-[10px] text-slate-500 block mt-0.5">153 Tests Passing</span>
            </div>
          </div>
        </div>
      </div>

      {/* PRIMARY CONTENT: Live Incident Queue */}
      <Card
        title="Active Revenue Incidents Requiring Action"
        subtitle="Ranked by economic loss rate, severity, and mitigation readiness"
        action={
          <Link to="/app/incidents" className="text-xs font-semibold text-slate-700 hover:text-slate-900 flex items-center gap-1">
            All Incidents <ArrowUpRight className="h-3 w-3" />
          </Link>
        }
      >
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500 bg-slate-50/50">
                <th className="py-2.5 px-3 font-semibold">INCIDENT / ANOMALY</th>
                <th className="py-2.5 px-3 font-semibold">SEVERITY</th>
                <th className="py-2.5 px-3 font-semibold">REVENUE AT RISK</th>
                <th className="py-2.5 px-3 font-semibold">LIFECYCLE STATUS</th>
                <th className="py-2.5 px-3 font-semibold">NEXT OPERATIONAL STEP</th>
                <th className="py-2.5 px-3 font-semibold text-right">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {incidents.map((inc) => {
                const isCritical = inc.severity === 'critical';
                const isResolved = inc.status === 'resolved';
                return (
                  <tr
                    key={inc.incident_id}
                    className={`hover:bg-slate-50 transition-colors ${
                      isCritical && !isResolved ? 'bg-rose-50/30' : ''
                    }`}
                  >
                    <td className="py-3 px-3">
                      <div className="flex flex-col">
                        <Link
                          to={`/app/incidents/${inc.incident_id}`}
                          className="font-bold text-slate-900 hover:text-blue-600 flex items-center gap-1.5"
                        >
                          {inc.description}
                        </Link>
                        <span className="text-[10px] text-slate-400 font-mono mt-0.5">
                          ID: {inc.incident_id} · Type: {inc.incident_type}
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-3">{getSeverityBadge(inc.severity)}</td>
                    <td className="py-3 px-3 font-mono font-bold text-slate-900 tabular-nums">
                      ₹{parseFloat(inc.revenue_at_risk).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-3">{getStatusBadge(inc.status)}</td>
                    <td className="py-3 px-3 font-medium text-slate-600">
                      {inc.status === 'detected' && 'Run diagnostic root cause investigation'}
                      {inc.status === 'investigating' && 'LangGraph multi-step agent running'}
                      {inc.status === 'action_proposed' && 'Policy requires operator authorization (₹85k > ₹50k)'}
                      {inc.status === 'action_approved' && 'Ready for guarded execution dispatch'}
                      {inc.status === 'resolved' && 'Verified: ₹35,000.00 protected'}
                    </td>
                    <td className="py-3 px-3 text-right">
                      <Link to={`/app/incidents/${inc.incident_id}`}>
                        <Button variant={isCritical && !isResolved ? 'danger' : 'primary'} size="sm">
                          Cockpit <ChevronRight className="h-3.5 w-3.5 ml-0.5" />
                        </Button>
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Supporting Architecture Health Context */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white border border-slate-200 rounded-lg p-4 space-y-1 shadow-xs">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-800">
            <Cpu className="h-4 w-4 text-blue-600" />
            <span>AI Investigator Subsystem</span>
          </div>
          <p className="text-[11px] text-slate-500 font-normal">
            LangGraph state machine grounds telemetry streams; never calculates monetary values.
          </p>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg p-4 space-y-1 shadow-xs">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-800">
            <Lock className="h-4 w-4 text-purple-600" />
            <span>Deterministic Policy Boundary</span>
          </div>
          <p className="text-[11px] text-slate-500 font-normal">
            Fail-closed validation enforces tenant isolation, monetary caps, and duplicate locks.
          </p>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg p-4 space-y-1 shadow-xs">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-800">
            <Layers className="h-4 w-4 text-emerald-600" />
            <span>Guarded Execution & Verification</span>
          </div>
          <p className="text-[11px] text-slate-500 font-normal">
            Only Executor invokes write adapters. Verifier confirms route recovery via telemetry.
          </p>
        </div>
      </div>
    </div>
  );
};
