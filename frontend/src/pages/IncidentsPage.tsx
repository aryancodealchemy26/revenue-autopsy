import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, Filter, AlertOctagon, ArrowRight, ShieldCheck, ChevronRight } from 'lucide-react';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { api } from '../services/api';
import { Incident } from '../types/domain';

export const IncidentsPage: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSeverity, setSelectedSeverity] = useState('ALL');
  const [selectedStatus, setSelectedStatus] = useState('ALL');

  useEffect(() => {
    api.getIncidents().then(setIncidents);
  }, []);

  const filteredIncidents = incidents.filter((inc) => {
    const matchesSearch =
      inc.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inc.incident_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inc.incident_type.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesSeverity = selectedSeverity === 'ALL' || inc.severity.toUpperCase() === selectedSeverity;
    const matchesStatus = selectedStatus === 'ALL' || inc.status.toUpperCase() === selectedStatus;

    return matchesSearch && matchesSeverity && matchesStatus;
  });

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
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Revenue Incidents Queue</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Real-time telemetry-scoped payment drops, authorization anomalies, and settlement failures.
          </p>
        </div>
      </div>

      {/* Search & Filter Bar */}
      <div className="bg-white border border-slate-200 rounded-lg p-3.5 shadow-sm flex flex-col md:flex-row items-center gap-3">
        <div className="relative flex-1 w-full">
          <Search className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search by incident ID, cause, or gateway target..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-slate-900"
          />
        </div>

        <div className="flex items-center gap-2 w-full md:w-auto">
          <select
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value)}
            className="text-xs bg-slate-50 border border-slate-200 rounded-md px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-slate-900"
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>

          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="text-xs bg-slate-50 border border-slate-200 rounded-md px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-slate-900"
          >
            <option value="ALL">All Statuses</option>
            <option value="DETECTED">Detected</option>
            <option value="INVESTIGATING">Investigating</option>
            <option value="ACTION_PROPOSED">Action Proposed</option>
            <option value="ACTION_APPROVED">Action Approved</option>
            <option value="RESOLVED">Resolved</option>
          </select>
        </div>
      </div>

      {/* Incidents List Table */}
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500 bg-slate-50/50">
                <th className="py-2.5 px-3 font-semibold">INCIDENT</th>
                <th className="py-2.5 px-3 font-semibold">TYPE</th>
                <th className="py-2.5 px-3 font-semibold">SEVERITY</th>
                <th className="py-2.5 px-3 font-semibold">REVENUE AT RISK</th>
                <th className="py-2.5 px-3 font-semibold">STATUS</th>
                <th className="py-2.5 px-3 font-semibold">CONFIDENCE</th>
                <th className="py-2.5 px-3 font-semibold text-right">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredIncidents.length > 0 ? (
                filteredIncidents.map((inc) => (
                  <tr key={inc.incident_id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-3 px-3">
                      <div className="flex flex-col">
                        <Link
                          to={`/app/incidents/${inc.incident_id}`}
                          className="font-semibold text-slate-900 hover:text-blue-600"
                        >
                          {inc.description}
                        </Link>
                        <span className="text-[10px] text-slate-400 font-mono mt-0.5">
                          ID: {inc.incident_id} · Detected {new Date(inc.detected_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-3">
                      <span className="font-mono text-[11px] text-slate-700 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200">
                        {inc.incident_type}
                      </span>
                    </td>
                    <td className="py-3 px-3">{getSeverityBadge(inc.severity)}</td>
                    <td className="py-3 px-3 font-mono font-semibold text-slate-900 tabular-nums">
                      ₹{parseFloat(inc.revenue_at_risk).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-3">{getStatusBadge(inc.status)}</td>
                    <td className="py-3 px-3 font-mono text-slate-600 tabular-nums">
                      {(parseFloat(inc.confidence) * 100).toFixed(0)}%
                    </td>
                    <td className="py-3 px-3 text-right">
                      <Link to={`/app/incidents/${inc.incident_id}`}>
                        <Button variant="primary" size="sm">
                          Inspect <ChevronRight className="h-3.5 w-3.5 ml-0.5" />
                        </Button>
                      </Link>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    No incidents matching filter criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
