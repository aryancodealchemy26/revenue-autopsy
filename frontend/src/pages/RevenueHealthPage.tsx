import React from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, AreaChart, Area } from 'recharts';
import { Activity, Clock, ShieldCheck, AlertOctagon } from 'lucide-react';
import { Card } from '../components/common/Card';
import { MetricCard } from '../components/common/MetricCard';

const TELEMETRY_FAILURE_DATA = [
  { time: '20:00', hdfc_error: 0.1, card_error: 0.2, webhook_lag_ms: 250 },
  { time: '20:10', hdfc_error: 0.2, card_error: 0.3, webhook_lag_ms: 320 },
  { time: '20:20', hdfc_error: 1.4, card_error: 0.4, webhook_lag_ms: 450 },
  { time: '20:30', hdfc_error: 8.9, card_error: 0.8, webhook_lag_ms: 820 },
  { time: '20:40', hdfc_error: 14.8, card_error: 1.2, webhook_lag_ms: 1400 }, // Incident peak
  { time: '20:50', hdfc_error: 2.1, card_error: 0.9, webhook_lag_ms: 1200 }, // Mitigation reroute executed
  { time: '21:00', hdfc_error: 0.3, card_error: 0.4, webhook_lag_ms: 380 }, // Stabilized
  { time: '21:10', hdfc_error: 0.1, card_error: 0.2, webhook_lag_ms: 280 },
];

export const RevenueHealthPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Revenue Telemetry & Health</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Diagnostic payment rail error rates, upstream gateway latencies, and conversion telemetry.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <MetricCard
          label="Overall Route Success Rate"
          value="98.8%"
          subValue="Stabilized post-intervention"
          change="+14.2% Post Reroute"
          changeType="positive"
          icon={<Activity className="h-4 w-4 text-emerald-600" />}
        />
        <MetricCard
          label="P99 Gateway Latency"
          value="480 ms"
          subValue="Target: <800 ms"
          change="Normal Range"
          changeType="positive"
          icon={<Clock className="h-4 w-4" />}
        />
        <MetricCard
          label="Active Payment Rail Anomalies"
          value="1 Rail"
          subValue="International 3DS under triage"
          change="1 Mitigated"
          changeType="neutral"
          icon={<AlertOctagon className="h-4 w-4 text-amber-600" />}
        />
      </div>

      {/* Gateway Failure Rate Spike Visualization */}
      <Card
        title="Gateway Route Error Rate (%) — Incident Telemetry Signature"
        subtitle="Displays baseline vs. spike on HDFC Direct rail and subsequent stabilization upon reroute"
      >
        <div className="h-72 w-full pt-4">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={TELEMETRY_FAILURE_DATA}>
              <defs>
                <linearGradient id="hdfcGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="time" stroke="#94a3b8" fontSize={11} />
              <YAxis stroke="#94a3b8" fontSize={11} unit="%" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#ffffff',
                  borderColor: '#e2e8f0',
                  borderRadius: '6px',
                  fontSize: '11px',
                  fontFamily: 'monospace',
                }}
              />
              <Area
                type="monotone"
                dataKey="hdfc_error"
                name="HDFC Direct Error Rate"
                stroke="#f43f5e"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#hdfcGradient)"
              />
              <Line
                type="monotone"
                dataKey="card_error"
                name="Card Baseline Error Rate"
                stroke="#64748b"
                strokeWidth={1.5}
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  );
};
