import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  AlertOctagon,
  PlayCircle,
  TrendingUp,
  ShieldAlert,
  ScrollText,
  Plug,
  Settings,
  Flame,
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const navSections = [
    {
      title: 'OPERATE',
      items: [
        { name: 'Overview', path: '/app/overview', icon: LayoutDashboard },
        { name: 'Incidents', path: '/app/incidents', icon: AlertOctagon, badge: '2 Active' },
        { name: 'Actions', path: '/app/actions', icon: PlayCircle },
        { name: 'Outcomes', path: '/app/outcomes', icon: TrendingUp },
      ],
    },
    {
      title: 'CONTROL',
      items: [
        { name: 'Policies', path: '/app/policies', icon: ShieldAlert },
        { name: 'Audit Trail', path: '/app/audit-trail', icon: ScrollText },
      ],
    },
    {
      title: 'SYSTEM',
      items: [
        { name: 'Integrations', path: '/app/integrations', icon: Plug },
        { name: 'Settings', path: '/app/settings', icon: Settings },
      ],
    },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col border-r border-slate-800 shrink-0 h-screen sticky top-0">
      {/* Brand Header */}
      <div className="h-14 flex items-center px-5 border-b border-slate-800 gap-2.5">
        <div className="h-7 w-7 rounded-md bg-rose-500/20 border border-rose-500/30 flex items-center justify-center text-rose-400">
          <Flame className="h-4 w-4" />
        </div>
        <div className="flex flex-col">
          <span className="text-sm font-semibold tracking-tight text-white flex items-center gap-1.5">
            Revenue Autopsy
          </span>
          <span className="text-[10px] text-slate-400 font-mono tracking-wider">INCIDENT RESPONSE</span>
        </div>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 px-3 py-4 space-y-6 overflow-y-auto">
        {navSections.map((section) => (
          <div key={section.title} className="space-y-1">
            <h4 className="px-3 text-[10px] font-semibold text-slate-400 tracking-wider uppercase">
              {section.title}
            </h4>
            <div className="space-y-0.5 pt-1">
              {section.items.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={({ isActive }) =>
                      `flex items-center justify-between px-3 py-2 text-xs font-medium rounded-md transition-colors ${
                        isActive
                          ? 'bg-slate-800 text-white font-semibold'
                          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                      }`
                    }
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon className="h-4 w-4 shrink-0 text-slate-400" />
                      <span>{item.name}</span>
                    </div>
                    {item.badge && (
                      <span className="text-[10px] bg-rose-500/20 text-rose-300 border border-rose-500/30 px-1.5 py-0.2 rounded font-mono font-medium">
                        {item.badge}
                      </span>
                    )}
                  </NavLink>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Footer / Tenant Context */}
      <div className="p-3 border-t border-slate-800 bg-slate-950/40">
        <div className="flex items-center justify-between px-2 py-1.5 rounded-md bg-slate-800/60 border border-slate-700/50 text-xs">
          <div className="flex flex-col truncate">
            <span className="text-slate-200 font-medium truncate">Acme Digital Tech</span>
            <span className="text-[10px] text-emerald-400 font-mono flex items-center gap-1">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400"></span> Sandbox Operational
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
};
