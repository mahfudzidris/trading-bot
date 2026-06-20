'use client';

import { Zap, ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Analysis } from '@/types';

interface AiRecommendationProps {
  analysis: Analysis | null;
  loading?: boolean;
  onExecute?: () => void;
  executing?: boolean;
}

export default function AiRecommendation({
  analysis,
  loading,
  onExecute,
  executing,
}: AiRecommendationProps) {
  if (loading) {
    return (
      <div className="animate-pulse rounded-xl border border-slate-700/50 bg-slate-800/30 p-5">
        <div className="mb-3 h-5 w-36 rounded bg-slate-700/50" />
        <div className="mb-4 h-4 w-full rounded bg-slate-700/50" />
        <div className="mb-4 h-4 w-3/4 rounded bg-slate-700/50" />
        <div className="h-10 w-full rounded-lg bg-slate-700/50" />
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-slate-700/50 bg-slate-800/30 p-8">
        <Zap className="mb-2 h-8 w-8 text-slate-600" />
        <p className="text-sm text-slate-500">Select a symbol to analyze</p>
      </div>
    );
  }

  const actionConfig = {
    buy: { icon: ArrowUpRight, color: 'text-emerald-400', bg: 'bg-emerald-500/10', label: 'BUY' },
    sell: { icon: ArrowDownRight, color: 'text-red-400', bg: 'bg-red-500/10', label: 'SELL' },
    hold: { icon: Minus, color: 'text-yellow-400', bg: 'bg-yellow-500/10', label: 'HOLD' },
  };

  const action = actionConfig[analysis.action];
  const ActionIcon = action.icon;

  return (
    <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 p-5">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Zap className="h-5 w-5 text-purple-400" />
          <h3 className="text-sm font-semibold text-slate-200">AI Recommendation</h3>
        </div>
        <span className="text-xs text-slate-500">{analysis.symbol}</span>
      </div>

      {/* Action badge */}
      <div className="mb-4 flex items-center gap-3">
        <span
          className={cn(
            'inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-bold uppercase',
            action.bg,
            action.color
          )}
        >
          <ActionIcon className="h-4 w-4" />
          {action.label}
        </span>
        <span className="text-xs text-slate-500">
          Current: ${analysis.currentPrice.toLocaleString()}
        </span>
      </div>

      {/* Confidence bar */}
      <div className="mb-4">
        <div className="mb-1 flex items-center justify-between">
          <span className="text-xs text-slate-500">Confidence</span>
          <span className="text-xs font-semibold text-slate-300">
            {analysis.confidence.toFixed(0)}%
          </span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-slate-700/50">
          <div
            className={cn(
              'h-full rounded-full transition-all duration-700',
              analysis.confidence >= 80
                ? 'bg-emerald-500'
                : analysis.confidence >= 60
                ? 'bg-yellow-500'
                : 'bg-red-500'
            )}
            style={{ width: `${analysis.confidence}%` }}
          />
        </div>
      </div>

      {/* TP/SL */}
      <div className="mb-4 grid grid-cols-2 gap-3">
        <div className="rounded-lg bg-slate-800/50 p-2.5">
          <span className="text-[10px] uppercase tracking-wider text-slate-500">
            Take Profit
          </span>
          <p className="font-mono text-sm font-semibold text-emerald-400">
            ${analysis.takeProfit.toLocaleString()}
          </p>
        </div>
        <div className="rounded-lg bg-slate-800/50 p-2.5">
          <span className="text-[10px] uppercase tracking-wider text-slate-500">
            Stop Loss
          </span>
          <p className="font-mono text-sm font-semibold text-red-400">
            ${analysis.stopLoss.toLocaleString()}
          </p>
        </div>
      </div>

      {/* Reasoning */}
      <div className="mb-4 rounded-lg bg-slate-900/50 p-3">
        <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
          AI Reasoning
        </span>
        <p className="mt-1 text-xs leading-relaxed text-slate-400">
          {analysis.reasoning}
        </p>
      </div>

      {/* Execute button */}
      {onExecute && (
        <button
          onClick={onExecute}
          disabled={executing || analysis.action === 'hold'}
          className={cn(
            'w-full rounded-lg py-2.5 text-sm font-semibold transition-all',
            analysis.action === 'buy' &&
              'bg-emerald-600 text-white hover:bg-emerald-500 disabled:bg-slate-700 disabled:text-slate-500',
            analysis.action === 'sell' &&
              'bg-red-600 text-white hover:bg-red-500 disabled:bg-slate-700 disabled:text-slate-500',
            analysis.action === 'hold' &&
              'bg-slate-700 text-slate-500 cursor-not-allowed'
          )}
        >
          {executing
            ? 'Executing...'
            : analysis.action === 'hold'
            ? 'No Action Recommended'
            : `Execute ${action.label} ${analysis.symbol}`}
        </button>
      )}

      <div className="mt-3 text-center text-[10px] text-slate-600">
        Position size: {analysis.positionSizePct}% of portfolio
      </div>
    </div>
  );
}
