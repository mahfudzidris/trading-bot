'use client';

import { cn } from '@/lib/utils';

interface StatusBadgeProps {
  status: 'open' | 'closed' | 'buy' | 'sell';
  className?: string;
}

export default function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = {
    open: { label: 'Open', bg: 'bg-yellow-500/15', text: 'text-yellow-400', dot: 'bg-yellow-400' },
    closed: { label: 'Closed', bg: 'bg-green-500/15', text: 'text-green-400', dot: 'bg-green-400' },
    buy: { label: 'Buy', bg: 'bg-emerald-500/15', text: 'text-emerald-400', dot: 'bg-emerald-400' },
    sell: { label: 'Sell', bg: 'bg-red-500/15', text: 'text-red-400', dot: 'bg-red-400' },
  } as const;

  const c = config[status.toLowerCase() as keyof typeof config];
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold',
        c.bg,
        c.text,
        className
      )}
    >
      <span className={cn('h-1.5 w-1.5 rounded-full', c.dot)} />
      {c.label}
    </span>
  );
}
