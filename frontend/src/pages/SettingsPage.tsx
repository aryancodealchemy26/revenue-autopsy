import React from 'react';
import { Card } from '../components/common/Card';

export const SettingsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Workspace Settings</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Merchant tenancy configurations and deterministic policy thresholds.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card title="Merchant Profile">
          <div className="space-y-3 text-xs">
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">Merchant Name:</span>
              <span className="font-semibold text-slate-900">Acme Digital Commerce Pvt Ltd</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">Tenant Merchant ID:</span>
              <span className="font-mono text-slate-900">merch_acme_tech_01</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">Base Currency:</span>
              <span className="font-mono font-bold text-slate-900">INR (₹)</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-slate-500">Timezone:</span>
              <span className="font-mono text-slate-900">Asia/Kolkata (UTC+5:30)</span>
            </div>
          </div>
        </Card>

        <Card title="Policy Engine Defaults">
          <div className="space-y-3 text-xs font-mono">
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">Auto-Allow Cap:</span>
              <span className="font-bold text-slate-900">₹50,000.00</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">Absolute Cap:</span>
              <span className="font-bold text-slate-900">₹500,000.00</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-100">
              <span className="text-slate-500">Min Confidence Auto-Allow:</span>
              <span className="font-bold text-slate-900">0.70</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-slate-500">Policy Version:</span>
              <span className="font-bold text-slate-900">1.0.0</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
