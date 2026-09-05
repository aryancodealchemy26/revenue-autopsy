import React from 'react';
import { ShieldCheck, Bell, Terminal, RefreshCw, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';

export const TopBar: React.FC = () => {
  return (
    <header className="h-14 bg-white border-b border-slate-200 px-6 flex items-center justify-between sticky top-0 z-10">
      {/* Left: Environment & Breadcrumbs / Context */}
      <div className="flex items-center gap-3">
        <span className="text-xs font-semibold text-slate-800 uppercase tracking-wider bg-slate-100 border border-slate-200 px-2 py-0.5 rounded">
          MERCHANT ID: merch_acme_tech_01
        </span>
        <span className="text-slate-300">|</span>
        <div className="flex items-center gap-1.5 text-xs text-slate-500">
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
          <span className="font-mono text-[11px] text-slate-700 font-medium">Deterministic Policy Engine v1.0 Active</span>
        </div>
      </div>

      {/* Right: Actions, Public Link, Notifications */}
      <div className="flex items-center gap-3">
        <Link
          to="/"
          className="text-xs font-medium text-slate-600 hover:text-slate-900 flex items-center gap-1 bg-slate-50 border border-slate-200 px-2.5 py-1 rounded hover:bg-slate-100 transition-colors"
        >
          <span>Public Flow</span>
          <ExternalLink className="h-3 w-3 text-slate-400" />
        </Link>
        <div className="h-4 w-px bg-slate-200" />
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
            Operational (153 Tests Passing)
          </span>
        </div>
      </div>
    </header>
  );
};
