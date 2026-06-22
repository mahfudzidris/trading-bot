'use client';

import { useEffect, useState } from 'react';
import {
  Brain,
  AlertCircle,
  RefreshCw,
  TrendingUp,
  Activity,
  BarChart3,
  DollarSign,
  Shield,
  Zap,
  BookOpen,
  Cpu,
  Layers,
  TrendingDown,
  Minus,
} from 'lucide-react';
import { fetchStrategy } from '@/lib/api';
import { cn } from '@/lib/utils';

interface Indicator {
  name: string;
  description: string;
}

interface RiskParams {
  maxPositionSizePct: number;
  stopLossPct: number;
  takeProfitPct: number;
  symbolsTracked: string[];
  mockMode: boolean;
}

interface ModelInfo {
  provider: string;
  modelName: string;
  temperature: number;
  maxTokens: number;
}

interface StrategyData {
  name: string;
  description: string;
  indicators: Indicator[];
  decisionFields: Record<string, string>;
  ensembleStrategies?: { name: string; inputs: string[]; logic: string }[];
  mockFallbackLogic: string[];
  riskParameters: RiskParams;
  account: { buyingPower: number; cash: number };
  model: ModelInfo;
  liveData?: LiveData | null;
}

interface LiveData {
  symbol: string;
  prompt: string | null;
  error?: string;
  priceData?: { price: number; changePct: number; volume: number; timestamp: string };
  indicators?: Record<string, number>;
  strategySignals?: { name: string; signal: string; confidence: number; reasoning: string }[];
  strategySummary?: { consensus: string; avgConfidence: number; votes: Record<string, number> };
}

export default function StrategyPage() {
  const SYMBOLS = ['SPY'];
  const [selectedSymbol, setSelectedSymbol] = useState('SPY');
  const [data, setData] = useState<StrategyData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showPrompt, setShowPrompt] = useState(false);

  const loadData = async (symbol: string) => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchStrategy(symbol);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load strategy');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(selectedSymbol);
  }, [selectedSymbol]);

  if (loading) {
    return (
      <div className="mx-auto max-w-7xl space-y-6 animate-fade-in">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-100">Strategy</h1>
            <p className="mt-1 text-sm text-slate-500">Loading strategy configuration...</p>
          </div>
        </div>
        <div className="space-y-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="animate-pulse rounded-xl border border-slate-700/50 bg-slate-800/30 p-6">
              <div className="mb-3 h-5 w-48 rounded bg-slate-700/50" />
              <div className="h-4 w-full rounded bg-slate-700/50" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-7xl space-y-6 animate-fade-in">
        <div className="flex items-center gap-3 rounded-xl border border-red-500/20 bg-red-500/10 p-4">
          <AlertCircle className="h-5 w-5 flex-shrink-0 text-red-400" />
          <p className="text-sm text-red-400">{error}</p>
          <button
            onClick={() => loadData(selectedSymbol)}
            className="ml-auto rounded-lg bg-red-500/20 px-3 py-1.5 text-xs font-medium text-red-300 hover:bg-red-500/30"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="mx-auto max-w-7xl space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Strategy</h1>
          <p className="mt-1 text-sm text-slate-500">
            How the AI analyses the market and generates trading signals
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <select
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
              className="appearance-none rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 pr-8 text-sm font-medium text-slate-200 outline-none focus:border-emerald-500/50"
            >
              {SYMBOLS.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            <BarChart3 className="pointer-events-none absolute right-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          </div>
          <button
            onClick={() => loadData(selectedSymbol)}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800/50 px-3 py-2 text-xs font-medium text-slate-300 transition-colors hover:bg-slate-700/50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Strategy Overview */}
      <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-500 to-emerald-600">
            <Brain className="h-4 w-4 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-100">{data.name}</h2>
            <p className="text-xs text-slate-500">Strategy Configuration</p>
          </div>
        </div>
        <p className="text-sm leading-relaxed text-slate-400">{data.description}</p>

        {/* Quick Stats */}
        <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="rounded-lg bg-slate-800/50 p-3">
            <div className="flex items-center gap-2">
              <Activity className="h-3.5 w-3.5 text-emerald-400" />
              <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500">Mode</span>
            </div>
            <p className="mt-1 text-sm font-bold text-slate-100">
              {data.riskParameters.mockMode ? 'Mock' : 'Live'}
            </p>
          </div>
          <div className="rounded-lg bg-slate-800/50 p-3">
            <div className="flex items-center gap-2">
              <BarChart3 className="h-3.5 w-3.5 text-blue-400" />
              <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500">Symbols</span>
            </div>
            <p className="mt-1 text-sm font-bold text-slate-100">{data.riskParameters.symbolsTracked.length}</p>
          </div>
          <div className="rounded-lg bg-slate-800/50 p-3">
            <div className="flex items-center gap-2">
              <Cpu className="h-3.5 w-3.5 text-purple-400" />
              <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500">Model</span>
            </div>
            <p className="mt-1 text-sm font-bold text-slate-100">{data.model.modelName}</p>
          </div>
          <div className="rounded-lg bg-slate-800/50 p-3">
            <div className="flex items-center gap-2">
              <DollarSign className="h-3.5 w-3.5 text-green-400" />
              <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500">Buying Power</span>
            </div>
            <p className="mt-1 text-sm font-bold text-slate-100">
              ${data.account.buyingPower.toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      {/* ── Live Preview (prompt + signals + indicators) ── */}
      {data.liveData && data.liveData.error && (
        <div className="flex items-center gap-3 rounded-xl border border-amber-500/20 bg-amber-500/5 p-4">
          <AlertCircle className="h-4 w-4 text-amber-400" />
          <p className="text-xs text-amber-400">Could not fetch live data: {data.liveData.error}</p>
        </div>
      )}

      {data.liveData && data.liveData.prompt && (
        <>
          {/* Live Indicators */}
          {data.liveData.indicators && (
            <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-blue-400" />
                  <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
                    Live Indicators — {data.liveData.symbol}
                  </h2>
                </div>
                <span className="text-[10px] text-slate-500">
                  {data.liveData.priceData?.timestamp ?? ''}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                {[
                  { label: 'Price', value: data.liveData.priceData?.price, fmt: 'currency' },
                  { label: 'Change', value: data.liveData.priceData?.changePct, fmt: 'percent' },
                  { label: 'SMA(20)', value: data.liveData.indicators?.sma_20, fmt: 'currency' },
                  { label: 'SMA(50)', value: data.liveData.indicators?.sma_50, fmt: 'currency' },
                  { label: 'EMA(20)', value: data.liveData.indicators?.ema_20, fmt: 'currency' },
                  { label: 'EMA(50)', value: data.liveData.indicators?.ema_50, fmt: 'currency' },
                  { label: 'RSI(14)', value: data.liveData.indicators?.rsi_14, fmt: 'number' },
                  { label: 'Volume', value: data.liveData.indicators?.volume, fmt: 'compact' },
                ].map((item) => (
                  <div key={item.label} className="rounded-lg bg-slate-800/50 p-2.5">
                    <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500">{item.label}</span>
                    <p className="mt-0.5 font-mono text-sm font-bold text-slate-100">
                      {item.value != null
                        ? item.fmt === 'currency'
                          ? `$${Number(item.value).toFixed(2)}`
                          : item.fmt === 'percent'
                            ? `${Number(item.value) >= 0 ? '+' : ''}${Number(item.value).toFixed(2)}%`
                            : item.fmt === 'compact'
                              ? Number(item.value) >= 1_000_000
                                ? `${(Number(item.value) / 1_000_000).toFixed(1)}M`
                                : Number(item.value).toLocaleString()
                              : Number(item.value).toFixed(1)
                        : '—'}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Live Strategy Signals */}
          {data.liveData.strategySignals && data.liveData.strategySignals.length > 0 && (
            <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 p-4">
              <div className="mb-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Layers className="h-4 w-4 text-indigo-400" />
                  <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
                    Live Strategy Signals — {data.liveData.symbol}
                  </h2>
                </div>
                {data.liveData.strategySummary && (
                  <span className={cn(
                    'rounded-full px-2 py-0.5 text-[10px] font-bold',
                    data.liveData.strategySummary.consensus === 'BUY' ? 'bg-green-500/20 text-green-400' :
                    data.liveData.strategySummary.consensus === 'SELL' ? 'bg-red-500/20 text-red-400' :
                    'bg-slate-500/20 text-slate-400'
                  )}>
                    Consensus: {data.liveData.strategySummary.consensus} ({data.liveData.strategySummary.avgConfidence}%)
                  </span>
                )}
              </div>
              <div className="space-y-2">
                {data.liveData.strategySignals.map((sig, idx) => {
                  const isBuy = sig.signal === 'BUY';
                  const isSell = sig.signal === 'SELL';
                  return (
                    <div key={idx} className="flex items-start gap-3 rounded-lg bg-slate-800/50 p-3">
                      <div className={cn(
                        'flex h-7 w-7 items-center justify-center rounded-full',
                        isBuy ? 'bg-green-500/20' : isSell ? 'bg-red-500/20' : 'bg-slate-500/20'
                      )}>
                        {isBuy ? <TrendingUp className="h-3.5 w-3.5 text-green-400" /> :
                         isSell ? <TrendingDown className="h-3.5 w-3.5 text-red-400" /> :
                         <Minus className="h-3.5 w-3.5 text-slate-400" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-slate-200">{sig.name}</span>
                          <span className={cn(
                            'rounded px-1.5 py-0.5 text-[10px] font-bold',
                            isBuy ? 'bg-green-500/15 text-green-400' :
                            isSell ? 'bg-red-500/15 text-red-400' :
                            'bg-slate-500/15 text-slate-400'
                          )}>{sig.signal}</span>
                          <span className="text-[10px] text-slate-500">{sig.confidence}%</span>
                        </div>
                        <p className="mt-0.5 text-[11px] leading-relaxed text-slate-500 line-clamp-2">{sig.reasoning}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Live Prompt — exact same as what DeepSeek receives */}
          <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-6">
            <button
              onClick={() => setShowPrompt(!showPrompt)}
              className="flex w-full items-center justify-between"
            >
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10">
                  <BookOpen className="h-4 w-4 text-emerald-400" />
                </div>
                <div>
                  <h2 className="text-sm font-semibold uppercase tracking-wider text-emerald-400">
                    Live AI Prompt — {data.liveData.symbol}
                  </h2>
                  <p className="text-[10px] text-emerald-500/70">Exact prompt sent to DeepSeek</p>
                </div>
              </div>
              <span className="text-xs text-emerald-500/70">{showPrompt ? 'Hide' : 'Show'} Full Prompt</span>
            </button>
            {showPrompt && (
              <pre className="mt-4 overflow-x-auto rounded-lg bg-slate-900/80 p-4 text-xs leading-relaxed text-slate-300 whitespace-pre-wrap">
                {data.liveData.prompt}
              </pre>
            )}
            {!showPrompt && (
              <p className="mt-3 text-xs text-emerald-500/50">
                Click to view the exact prompt being sent to DeepSeek for {data.liveData.symbol}, including live indicators and ensemble strategy signals.
              </p>
            )}
          </div>
        </>
      )}

      {!data.liveData && (
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 p-6">
          <div className="flex items-center gap-3">
            <BarChart3 className="h-5 w-5 text-slate-400" />
            <p className="text-sm text-slate-400">
              Select a symbol above to see live indicators, strategy signals, and the exact prompt sent to DeepSeek.
            </p>
          </div>
        </div>
      )}

      {/* Technical Indicators */}
      <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/10">
            <TrendingUp className="h-4 w-4 text-blue-400" />
          </div>
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
            Technical Indicators
          </h2>
        </div>
        <p className="mb-4 text-xs text-slate-500">
          These indicators are fetched from TwelveData and passed to the AI model for decision-making.
        </p>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {data.indicators.map((indicator) => (
            <div key={indicator.name} className="rounded-lg border border-slate-700/30 bg-slate-800/50 p-4">
              <span className="font-mono text-sm font-bold text-emerald-400">{indicator.name}</span>
              <p className="mt-1.5 text-xs leading-relaxed text-slate-400">{indicator.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Decision Output Fields */}
      <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-500/10">
            <Zap className="h-4 w-4 text-purple-400" />
          </div>
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
            AI Decision Output
          </h2>
        </div>
        <p className="mb-4 text-xs text-slate-500">
          The AI model returns a JSON object with these fields for every symbol analysed.
        </p>
        <div className="overflow-hidden rounded-lg border border-slate-700/30">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-700/30 bg-slate-800/50">
                <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-400">Field</th>
                <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-400">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/30">
              {Object.entries(data.decisionFields).map(([field, desc]) => (
                <tr key={field} className="hover:bg-slate-800/30">
                  <td className="px-4 py-3">
                    <code className="rounded bg-slate-700/50 px-1.5 py-0.5 font-mono text-xs text-emerald-300">
                      {field}
                    </code>
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-400">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Ensemble Strategies */}
      {data.ensembleStrategies && data.ensembleStrategies.length > 0 && (
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/10">
              <Layers className="h-4 w-4 text-indigo-400" />
            </div>
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
              Ensemble Strategies
            </h2>
          </div>
          <p className="mb-4 text-xs text-slate-500">
            3 algorithmic strategies run in parallel. Each produces an independent signal. The AI acts as a meta-analyzer, weighing all signals alongside raw data to produce the final decision.
          </p>
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            {data.ensembleStrategies.map((strat) => (
              <div key={strat.name} className="rounded-lg border border-slate-700/30 bg-slate-800/50 p-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className={cn(
                    'flex h-6 w-6 items-center justify-center rounded-full',
                    strat.name === 'Trend Following' ? 'bg-blue-500/20' :
                    strat.name === 'Mean Reversion' ? 'bg-amber-500/20' :
                    'bg-purple-500/20'
                  )}>
                    <span className={cn(
                      'text-[10px] font-bold',
                      strat.name === 'Trend Following' ? 'text-blue-400' :
                      strat.name === 'Mean Reversion' ? 'text-amber-400' :
                      'text-purple-400'
                    )}>
                      {strat.name === 'Trend Following' ? 'TF' : strat.name === 'Mean Reversion' ? 'MR' : 'MO'}
                    </span>
                  </div>
                  <span className="text-sm font-bold text-slate-200">{strat.name}</span>
                </div>
                <div className="mb-2 flex flex-wrap gap-1">
                  {strat.inputs.map((input: string) => (
                    <span key={input} className="rounded bg-slate-700/50 px-1.5 py-0.5 text-[10px] font-mono text-slate-400">
                      {input}
                    </span>
                  ))}
                </div>
                <p className="text-[11px] leading-relaxed text-slate-500">{strat.logic}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Mock Fallback Logic */}
      {data.riskParameters.mockMode && (
        <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/10">
              <Cpu className="h-4 w-4 text-amber-400" />
            </div>
            <h2 className="text-sm font-semibold uppercase tracking-wider text-amber-400">
              Mock Mode: Rule-Based Fallback
            </h2>
          </div>
          <p className="mb-4 text-xs text-amber-500/70">
            Since the bot is running in mock mode, AI decisions use this rule-based logic instead of DeepSeek API calls.
          </p>
          <div className="space-y-2">
            {data.mockFallbackLogic.map((rule, i) => (
              <div key={i} className="flex items-start gap-3 rounded-lg bg-slate-800/50 p-3">
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-amber-500/20 text-[10px] font-bold text-amber-400">
                  {i + 1}
                </span>
                <p className="text-xs text-slate-300">{rule}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Risk Parameters & Model Info */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Risk Parameters */}
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-red-500/10">
              <Shield className="h-4 w-4 text-red-400" />
            </div>
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
              Risk Parameters
            </h2>
          </div>
          <div className="overflow-hidden rounded-lg border border-slate-700/30">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-700/30 bg-slate-800/50">
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-400">Parameter</th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-400">Value</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/30">
                <tr className="hover:bg-slate-800/30">
                  <td className="px-4 py-3 text-xs text-slate-400">Max Position Size</td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-200">{(data.riskParameters.maxPositionSizePct * 100).toFixed(1)}%</td>
                </tr>
                <tr className="hover:bg-slate-800/30">
                  <td className="px-4 py-3 text-xs text-slate-400">Stop Loss</td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-200">{(data.riskParameters.stopLossPct * 100).toFixed(1)}%</td>
                </tr>
                <tr className="hover:bg-slate-800/30">
                  <td className="px-4 py-3 text-xs text-slate-400">Take Profit</td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-200">{(data.riskParameters.takeProfitPct * 100).toFixed(1)}%</td>
                </tr>
                <tr className="hover:bg-slate-800/30">
                  <td className="px-4 py-3 text-xs text-slate-400">Symbols Tracked</td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-200">
                    {data.riskParameters.symbolsTracked.join(', ')}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Model Info */}
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-500/10">
              <Cpu className="h-4 w-4 text-purple-400" />
            </div>
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
              AI Model Configuration
            </h2>
          </div>
          <div className="overflow-hidden rounded-lg border border-slate-700/30">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-700/30 bg-slate-800/50">
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-400">Setting</th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-400">Value</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/30">
                <tr className="hover:bg-slate-800/30">
                  <td className="px-4 py-3 text-xs text-slate-400">Provider</td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-200">{data.model.provider}</td>
                </tr>
                <tr className="hover:bg-slate-800/30">
                  <td className="px-4 py-3 text-xs text-slate-400">Model</td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-200">{data.model.modelName}</td>
                </tr>
                <tr className="hover:bg-slate-800/30">
                  <td className="px-4 py-3 text-xs text-slate-400">Temperature</td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-200">{data.model.temperature}</td>
                </tr>
                <tr className="hover:bg-slate-800/30">
                  <td className="px-4 py-3 text-xs text-slate-400">Max Tokens</td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-200">{data.model.maxTokens.toLocaleString()}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
