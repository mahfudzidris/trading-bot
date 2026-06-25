'use client';

import { DollarSign, Wallet, Banknote, Activity } from 'lucide-react';
import { cn } from '@/lib/utils';

interface AccountSummaryProps {
  cash: number;
  portfolioValue: number;
  buyingPower: number;
  totalPnl: number;
  status: string;
  balance: number;
}

export default function AccountSummary({
  cash,
  portfolioValue,
  buyingPower,
  totalPnl,
  status,
  balance,
}: AccountSummaryProps) {
  const items = [
    {
      label: 'Cash Balance',
      value: cash,
      icon: <Wallet className="h-4 w-4" />,
      color: 'text-blue-400',
      bg: 'bg-blue-500/10',
    },
    {
      label: 'Equity / Portfolio',
      value: portfolioValue,
      icon: <Banknote className="h-4 w-4" />,
      color: 'text-violet-400',
      bg: 'bg-violet-500/10',
    },
    {
      label: 'Buying Power',
      value: buyingPower,
      icon: <DollarSign className="h-4 w-4" />,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10',
    },
    {
      label: 'Total PnL',
      value: totalPnl,
      icon: <Activity className="h-4 w-4" />,
      color: totalPnl >= 0 ? 'text-green-400' : 'text-red-400',
      bg: totalPnl >= 0 ? 'bg-green-500/10' : 'bg-red-500/10',
    },
  ];

  return (
    <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          Account Summary
        </h3>
        <span
          className={cn(
            'rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider',
            status === 'ACTIVE'
              ? 'bg-green-500/10 text-green-400'
              : 'bg-yellow-500/10 text-yellow-400'
          )}
        >
          {status || 'UNKNOWN'}
        </span>
      </div>
      <div className="space-y-2.5">
        {items.map((item) => (
          <div
            key={item.label}
            className="flex items-center justify-between rounded-lg bg-slate-800/50 px-3 py-2"
          >
            <div className="flex items-center gap-2">
              <span className={cn('rounded-md p-1', item.bg, item.color)}>
                {item.icon}
              </span>
              <span className="text-xs text-slate-400">{item.label}</span>
            </div>
            <span className={cn('text-sm font-semibold tabular-nums', item.color)}>
              ${Math.abs(item.value).toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
              {item.value < 0 && (
                <span className="ml-0.5 text-[10px] text-red-400">(Neg)</span>
              )}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
