'use client';

import { TrendingUp, TrendingDown, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Performance } from '@/types';

interface PerformancePanelProps {
  performance: Performance | null;
  loading?: boolean;
}

function DonutChart({ winRate }: { winRate: number }) {
  const lossRate = 100 - winRate;
  const circumference = 2 * Math.PI * 36;
  const winOffset = circumference - (winRate / 100) * circumference;
  const lossOffset = circumference - (lossRate / 100) * circumference;

  return (
    <div className="relative flex items-center justify-center">
      <svg width="100" height="100" viewBox="0 0 100 100">
        <circle
          cx="50"
          cy="50"
          r="36"
          fill="none"
          stroke="#1e293b"
          strokeWidth="8"
        />
        <circle
          cx="50"
          cy="50"
          r="36"
          fill="none"
          stroke="#22c55e"
          strokeWidth="8"
          strokeDasharray={circumference}
          strokeDashoffset={winOffset}
          strokeLinecap="round"
          transform="rotate(-90 50 50)"
          className="transition-all duration-1000"
        />
        <circle
          cx="50"
          cy="50"
          r="36"
          fill="none"
          stroke="#ef4444"
          strokeWidth="8"
          strokeDasharray={circumference}
          strokeDashoffset={lossOffset}
          strokeLinecap="round"
          transform="rotate(${-90 + (winRate / 100) * 360} 50 50)"
          className="transition-all duration-1000"
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-lg font-bold text-slate-100">{winRate.toFixed(0)}%</span>
        <span className="text-[10px] text-slate-500">Win Rate</span>
      </div>
    </div>
  );
}

export default function PerformancePanel({
  performance,
  loading,
}: PerformancePanelProps) {
  if (loading) {
    return (
      <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 p-4">
        <div className="animate-pulse space-y-4">
          <div className="h-5 w-32 rounded bg-slate-700/50" />
          <div className="flex justify-center">
            <div className="h-[100px] w-[100px] rounded-full bg-slate-700/50" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="h-16 rounded bg-slate-700/50" />
            <div className="h-16 rounded bg-slate-700/50" />
          </div>
        </div>
      </div>
    );
  }

  if (!performance) {
    return (
      <div className="flex items-center justify-center rounded-xl border border-slate-700/50 bg-slate-800/30 p-8">
        <p className="text-sm text-slate-500">No performance data</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 p-4">
      <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-400">
        Performance
      </h3>

      <div className="flex justify-center">
        <DonutChart winRate={performance.winRate ?? 0} />
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3">
        <div className="rounded-lg bg-slate-800/50 p-3">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-green-400" />
            <span className="text-xs text-slate-500">Best Trade</span>
          </div>
          <p className="mt-1 text-sm font-semibold text-green-400">
            {performance.bestTrade?.pnl != null
              ? `+$${performance.bestTrade.pnl.toFixed(2)}`
              : '—'}
          </p>
          {performance.bestTrade && (
            <p className="text-[10px] text-slate-600">
              {performance.bestTrade.symbol} · {performance.bestTrade.strategy}
            </p>
          )}
        </div>
        <div className="rounded-lg bg-slate-800/50 p-3">
          <div className="flex items-center gap-2">
            <TrendingDown className="h-4 w-4 text-red-400" />
            <span className="text-xs text-slate-500">Worst Trade</span>
          </div>
          <p className="mt-1 text-sm font-semibold text-red-400">
            {performance.worstTrade?.pnl != null
              ? `-$${Math.abs(performance.worstTrade.pnl).toFixed(2)}`
              : '—'}
          </p>
          {performance.worstTrade && (
            <p className="text-[10px] text-slate-600">
              {performance.worstTrade.symbol} · {performance.worstTrade.strategy}
            </p>
          )}
        </div>
      </div>

      <div className="mt-3 flex items-center justify-between rounded-lg bg-slate-800/50 px-3 py-2">
        <span className="text-xs text-slate-500">Total Trades</span>
        <span className="text-sm font-semibold text-slate-200">
          {performance.tradesCount}
        </span>
      </div>
    </div>
  );
}
