import React from 'react';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';

export const IntegrationsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Provider Integrations</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Configured payment gateways, telemetry streams, and webhook delivery endpoints.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Razorpay Integration Card */}
        <Card
          title="Razorpay Gateway Adapter"
          subtitle="Test Mode API connection for payment retry and status checks"
          action={<Badge variant="success">CONNECTED · TEST MODE</Badge>}
        >
          <div className="space-y-4 text-xs">
            <div className="bg-slate-50 p-3 rounded-md border border-slate-200 font-mono space-y-1.5 text-[11px]">
              <div className="flex justify-between">
                <span className="text-slate-400">Environment:</span>
                <span className="text-emerald-700 font-bold">TEST MODE (rzp_test_*)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Key ID:</span>
                <span className="text-slate-900">rzp_test_mockkey123</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Key Secret:</span>
                <span className="text-slate-900">••••••••••••••••</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Live Money Guard:</span>
                <span className="text-emerald-700 font-semibold">ENFORCED (rzp_live_* blocked)</span>
              </div>
            </div>

            <p className="text-slate-600 leading-relaxed">
              Configured via backend environment settings (<code className="bg-slate-100 px-1 py-0.5 rounded font-mono">RAZORPAY_KEY_ID</code>). Only permits documented Orders and Payment verification endpoints.
            </p>
          </div>
        </Card>

        {/* Sandbox Simulation Adapter */}
        <Card
          title="Simulation Capability Adapter"
          subtitle="Truthfully simulates actions without direct Razorpay write endpoints"
          action={<Badge variant="simulation">ACTIVE SANDBOX</Badge>}
        >
          <div className="space-y-4 text-xs">
            <div className="bg-slate-50 p-3 rounded-md border border-slate-200 font-mono space-y-1.5 text-[11px]">
              <div className="flex justify-between">
                <span className="text-slate-400">Capabilities:</span>
                <span className="text-slate-900">GATEWAY_REROUTE, RATE_LIMIT</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Telemetry Mocking:</span>
                <span className="text-slate-900">Deterministic</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Simulated Tag:</span>
                <span className="text-amber-800 font-semibold">is_simulated = true</span>
              </div>
            </div>

            <p className="text-slate-600 leading-relaxed">
              Explicitly tags all simulated interventions to guarantee that simulated recovery is never misrepresented as a real financial provider write.
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
};
