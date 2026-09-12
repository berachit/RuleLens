import React from 'react';
import { RegulationStatus } from '../types';
import { CheckCircle2, HelpCircle, AlertTriangle } from 'lucide-react';

interface StatusBadgeProps {
  status: RegulationStatus;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const isSm = size === 'sm';

  switch (status) {
    case 'ANSWERED':
      return (
        <span
          className={`inline-flex items-center gap-1.5 font-medium rounded-full bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20 ${
            isSm ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-xs tracking-wide uppercase'
          }`}
        >
          <CheckCircle2 className={isSm ? 'w-3 h-3' : 'w-3.5 h-3.5'} />
          <span>Official Rule Found</span>
        </span>
      );

    case 'NOT_COVERED':
      return (
        <span
          className={`inline-flex items-center gap-1.5 font-medium rounded-full bg-slate-500/10 text-slate-700 dark:text-slate-300 border border-slate-500/20 ${
            isSm ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-xs tracking-wide uppercase'
          }`}
        >
          <HelpCircle className={isSm ? 'w-3 h-3' : 'w-3.5 h-3.5'} />
          <span>Not In Rules</span>
        </span>
      );

    case 'CONFLICT':
      return (
        <span
          className={`inline-flex items-center gap-1.5 font-medium rounded-full bg-rose-500/10 text-rose-700 dark:text-rose-400 border border-rose-500/20 ${
            isSm ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-xs tracking-wide uppercase'
          }`}
        >
          <AlertTriangle className={isSm ? 'w-3 h-3' : 'w-3.5 h-3.5'} />
          <span>Rule Contradiction</span>
        </span>
      );

    default:
      return null;
  }
};
