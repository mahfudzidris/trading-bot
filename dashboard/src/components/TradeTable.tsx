'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, ArrowUpDown, BarChart3 } from 'lucide-react';
import StatusBadge from './StatusBadge';
import { cn } from '@/lib/utils';
import type { Trade } from '@/types';

interface TradeTableProps {
  trades: Trade[];
  loading?: boolean;
  compact?: boolean;
}

type SortKey = 'entryTime' | 'symbol' | 'side' | 'pnl' | 'status' | 'entryPrice';
type SortDir = 'asc' | 'desc';

export default function TradeTable({ trades, loading, compact }: TradeTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>('entryTime');
  const [sortDir, setSortDir] = useState<SortDir>('desc');

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('desc');
    }
  };

  const sorted = [...trades].sort((a, b) => {
    let cmp = 0;
    switch (sortKey) {
      case 'entryTime':
        cmp = new Date(a.entryTime).getTime() - new Date(b.entryTime).getTime();
        break;
      case 'symbol':
        cmp = a.symbol.localeCompare(b.symbol);
        break;
      case 'side':
        cmp = a.side.localeCompare(b.side);
        break;
      case 'pnl':
        cmp = (a.pnl ?? 0) - (b.pnl ?? 0);
        break;
      case 'status':
        cmp = a.status.localeCompare(b.status);
        break;
      case 'entryPrice':
        cmp = a.entryPrice - b.entryPrice;
        break;
    }
    return sortDir === 'asc' ? cmp : -cmp;
  });

  const columns = compact
    ? [
        { key: 'entryTime' as SortKey, label: 'Date', sortable: true },
        { key: 'symbol' as SortKey, label: 'Symbol', sortable: true },
        { key: 'side' as SortKey, label: 'Side', sortable: true },
        { key: 'pnl' as SortKey, label: 'PnL', sortable: true },
        { key: 'status' as SortKey, label: 'Status', sortable: true },
      ]
    : [
        { key: 'entryTime' as SortKey, label: 'Date', sortable: true },
        { key: 'symbol' as SortKey, label: 'Symbol', sortable: true },
        { key: 'side' as SortKey, label: 'Side', sortable: true },
        { key: '' as SortKey, label: 'Qty', sortable: false },
        { key: 'entryPrice' as SortKey, label: 'Entry', sortable: true },
        { key: '' as SortKey, label: 'Exit', sortable: false },
        { key: 'pnl' as SortKey, label: 'PnL', sortable: true },
        { key: '' as SortKey, label: 'PnL%', sortable: false },
        { key: 'status' as SortKey, label: 'Status', sortable: true },
      ];

  const SortIcon = ({ columnKey }: { columnKey: SortKey }) => {
    if (sortKey !== columnKey) return <ArrowUpDown className="ml-1 h-3 w-3 text-slate-600" />;
    return sortDir === 'asc' ? (
      <ChevronUp className="ml-1 h-3 w-3" />
    ) : (
      <ChevronDown className="ml-1 h-3 w-3" />
    );
  };

  if (loading) {
    return (
      <div className="overflow-hidden rounded-xl border border-slate-700/50">
        <div className="divide-y divide-slate-700/30">
          {Array.from({ length: compact ? 5 : 4 }).map((_, i) => (
            <div key={i} className="flex animate-pulse gap-4 p-4">
              {Array.from({ length: compact ? 5 : 9 }).map((_, j) => (
                <div key={j} className="h-4 flex-1 rounded bg-slate-700/50" />
              ))}
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (trades.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-slate-700/50 py-12">
        <BarChart3 className="mb-2 h-8 w-8 text-slate-600" />
        <p className="text-sm text-slate-500">No trades found</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-700/50">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-slate-700/50 bg-slate-800/30">
            {columns.map((col) => (
              <th
                key={col.label}
                className={cn(
                  'px-3 py-3 text-xs font-semibold uppercase tracking-wider text-slate-400',
                  col.sortable && 'cursor-pointer select-none hover:text-slate-200'
                )}
                onClick={() => col.sortable && col.key && handleSort(col.key)}
              >
                <span className="inline-flex items-center">
                  {col.label}
                  {col.sortable && col.key && <SortIcon columnKey={col.key} />}
                </span>
              </th>
            ))}
            {!compact && <th className="px-3 py-3 text-xs font-semibold uppercase tracking-wider text-slate-400">AI</th>}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-700/30">
          {sorted.map((trade) => (
            <tr
              key={trade.id}
              className="transition-colors hover:bg-slate-700/20"
            >
              <td className="whitespace-nowrap px-3 py-3 text-slate-300">
                {new Date(trade.entryTime).toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric',
                })}
              </td>
              <td className="whitespace-nowrap px-3 py-3 font-medium text-slate-100">
                {trade.symbol}
              </td>
              <td className="px-3 py-3">
                <StatusBadge status={trade.side} />
              </td>
              {!compact && (
                <>
                  <td className="whitespace-nowrap px-3 py-3 font-mono text-slate-300">{trade.qty.toFixed(4).replace(/\.?0+$/, '')}</td>
                  <td className="whitespace-nowrap px-3 py-3 font-mono text-slate-300">
                    ${trade.entryPrice.toLocaleString()}
                  </td>
                  <td className="whitespace-nowrap px-3 py-3 font-mono text-slate-300">
                    {trade.exitPrice ? `$${trade.exitPrice.toLocaleString()}` : '—'}
                  </td>
                </>
              )}
              <td
                className={cn(
                  'whitespace-nowrap px-3 py-3 font-mono font-semibold',
                  (trade.pnl ?? 0) >= 0 ? 'text-green-400' : 'text-red-400'
                )}
              >
                {trade.pnl != null ? `$${trade.pnl.toFixed(2)}` : '—'}
              </td>
              {!compact && (
                <td
                  className={cn(
                    'whitespace-nowrap px-3 py-3 font-mono text-sm',
                    (trade.pnlPct ?? 0) >= 0 ? 'text-green-400' : 'text-red-400'
                  )}
                >
                  {trade.pnlPct != null ? `${trade.pnlPct >= 0 ? '+' : ''}${trade.pnlPct.toFixed(2)}%` : '—'}
                </td>
              )}
              <td className="px-3 py-3">
                <StatusBadge status={trade.status} />
              </td>
              {!compact && (
                <td className="max-w-[200px] truncate px-3 py-3 text-xs text-slate-500">
                  {trade.aiReasoning || '—'}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
