import React from 'react';

interface MetricCardProps {
  label: string;
  value: string | number;
  subValue?: string;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  icon?: React.ReactNode;
  badge?: React.ReactNode;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  subValue,
  change,
  changeType = 'neutral',
  icon,
  badge,
}) => {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm hover:border-slate-300 transition-colors">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">{label}</span>
        {badge || (icon && <span className="text-slate-400">{icon}</span>)}
      </div>
      <div className="mt-2 flex items-baseline justify-between">
        <div className="text-2xl font-semibold text-slate-900 tabular-nums tracking-tight">{value}</div>
        {change && (
          <span
            className={`text-xs font-medium ${
              changeType === 'positive'
                ? 'text-emerald-700'
                : changeType === 'negative'
                ? 'text-rose-700'
                : 'text-slate-500'
            }`}
          >
            {change}
          </span>
        )}
      </div>
      {subValue && <p className="mt-1 text-xs text-slate-500 truncate">{subValue}</p>}
    </div>
  );
};
