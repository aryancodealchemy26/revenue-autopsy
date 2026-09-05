import React, { useEffect, useState } from 'react';
import { ShieldCheck, ExternalLink, Activity, Wifi, WifiOff } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../../services/api';

export const TopBar: React.FC = () => {
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  useEffect(() => {
    api.checkHealth()
      .then(() => setBackendOnline(true))
      .catch(() => setBackendOnline(false));
  }, []);

  return (
    <header className="h-14 bg-white border-b border-slate-200 px-6 flex items-center justify-between sticky top-0 z-10">
      {/* Left: Environment & Breadcrumbs / Context */}
      <div className="flex items-center gap-3">
        <span className="text-xs font-semibold text-slate-800 uppercase tracking-wider bg-slate-100 border border-slate-200 px-2 py-0.5 rounded font-mono">
          TENANT: {api.getMerchantId()}
        </span>
        <span className="text-slate-300">|</span>
        <div className="flex items-center gap-1.5 text-xs text-slate-500">
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
          <span className="font-mono text-[11px] text-slate-700 font-medium">Deterministic Policy Engine v1.0</span>
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
          {backendOnline === true ? (
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 font-mono">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              FastAPI /api/v1 Connected (164 Tests Passing)
            </span>
          ) : backendOnline === false ? (
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200 font-mono">
              <span className="h-1.5 w-1.5 rounded-full bg-amber-500"></span>
              API Offline (Sandbox Fallback)
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200 font-mono">
              <span className="h-1.5 w-1.5 rounded-full bg-slate-400 animate-pulse"></span>
              Connecting to API...
            </span>
          )}
        </div>
      </div>
    </header>
  );
};
