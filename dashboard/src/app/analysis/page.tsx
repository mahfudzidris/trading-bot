'use client';

import { useEffect, useState, useCallback } from 'react';
import {
  RefreshCw,
  AlertCircle,
  BarChart3,
  TrendingUp,
  DollarSign,
  Activity,
  Clock,
  TrendingUp as TrendingUpIcon,
  TrendingDown,
  Minus,
  Layers,
  Globe,
  Newspaper,
  BrainCircuit,
  Gauge,
  ExternalLink,
} from 'lucide-react';
import AiRecommendation from '@/components/AiRecommendation';
import StatusBadge from '@/components/StatusBadge';
import { analyzeSymbol, fetchTrades, fetchAccount, executeTrade } from '@/lib/api';
import type { Analysis, Trade } from '@/types';
import { cn } from '@/lib/utils';

const SYMBOLS = ['AAPL', 'TSLA', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'SPY', 'QQQ'];

export default function AnalysisPage() {
  const [selectedSymbol, setSelectedSymbol] = useState('AAPL');
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [recentTrades, setRecentTrades] = useState<Trade[]>([]);
  const [strategySignals, setStrategySignals] = useState<any[]>([]);
  const [strategySummary, setStrategySummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async (symbol: string) => {
    setLoading(true);
    setError(null);
    try {
      const [analysisData, tradesData] = await Promise.all([
        analyzeSymbol(symbol),
        fetchTrades({ symbol, limit: 5, page: 1 }),
      ]);
      setAnalysis(analysisData);
      setStrategySignals(analysisData.strategySignals ?? []);
      setStrategySummary(analysisData.strategySummary ?? null);
      setRecentTrades(tradesData?.data ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analysis');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData(selectedSymbol);
  }, [loadData, selectedSymbol]);

  const handleRefresh = () => {
    setAnalyzing(true);
    loadData(selectedSymbol).finally(() => setAnalyzing(false));
  };

  const handleExecute = async () => {
    if (!analysis || analysis.action === 'hold') return;
    setExecuting(true);
    setError(null);
    try {
      // Calculate position size based on AI recommendation
      const account = await fetchAccount();
      const positionValue = (analysis.positionSizePct / 100) * account.buyingPower;
      const qty = Math.max(1, Math.floor(positionValue / analysis.currentPrice));

      await executeTrade({
        symbol: selectedSymbol,
        side: analysis.action.toUpperCase(),
        qty,
        ai_reasoning: analysis.reasoning,
        ai_confidence: analysis.confidence,
        stop_loss: analysis.stopLoss,
        take_profit: analysis.takeProfit,
      });

      handleRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to execute trade');
    } finally {
      setExecuting(false);
    }
  };

  const marketIndicators = analysis
    ? [
        { label: 'Current Price', value: `$${analysis.currentPrice.toLocaleString()}`, icon: DollarSign, color: 'text-blue-400' },
        { label: 'Take Profit', value: `$${analysis.takeProfit.toLocaleString()}`, icon: TrendingUp, color: 'text-emerald-400' },
        { label: 'Stop Loss', value: `$${analysis.stopLoss.toLocaleString()}`, icon: TrendingUp, color: 'text-red-400' },
        { label: 'Position Size', value: `${analysis.positionSizePct}%`, icon: Activity, color: 'text-purple-400' },
      ]
    : [];

  return (
    <div className="mx-auto max-w-7xl space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Market Analysis</h1>
          <p className="mt-1 text-sm text-slate-500">
            AI-powered trading signals and recommendations
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Symbol selector */}
          <div className="relative">
            <select
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
              className="appearance-none rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 pr-8 text-sm font-medium text-slate-200 outline-none focus:border-emerald-500/50"
            >
              {SYMBOLS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
            <BarChart3 className="pointer-events-none absolute right-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          </div>
          <button
            onClick={handleRefresh}
            disabled={analyzing}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800/50 px-3 py-2 text-xs font-medium text-slate-300 transition-colors hover:bg-slate-700/50 disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${analyzing ? 'animate-spin' : ''}`} />
            {analyzing ? 'Analyzing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
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
      )}

      {/* Main grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left column: Indicators */}
        <div className="space-y-4 lg:col-span-2">
          {/* Market Indicators */}
          <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 p-4">
            <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-400">
              Market Indicators — {selectedSymbol}
            </h2>
            {loading ? (
              <div className="grid grid-cols-2 gap-3">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="animate-pulse rounded-lg bg-slate-800/50 p-3">
                    <div className="mb-2 h-3 w-16 rounded bg-slate-700/50" />
                    <div className="h-5 w-24 rounded bg-slate-700/50" />
                  </div>
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-3">
                {marketIndicators.map((indicator) => {
                  const Icon = indicator.icon;
                  return (
                    <div
                      key={indicator.label}
                      className="rounded-lg bg-slate-800/50 p-3"
                    >
                      <div className="flex items-center gap-2">
                        <Icon className={cn('h-4 w-4', indicator.color)} />
                        <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500">
                          {indicator.label}
                        </span>
                      </div>
                      <p className="mt-1 font-mono text-lg font-bold text-slate-100">
                        {indicator.value}
                      </p>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Strategy Signals (Ensemble) */}
          {!loading && strategySignals.length > 0 && (
            <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 p-4">
              <div className="mb-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Layers className="h-4 w-4 text-indigo-400" />
                  <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
                    Strategy Signals
                  </h2>
                </div>
                {strategySummary && (
                  <span className={cn(
                    'rounded-full px-2 py-0.5 text-[10px] font-bold',
                    strategySummary.consensus === 'BUY' ? 'bg-green-500/20 text-green-400' :
                    strategySummary.consensus === 'SELL' ? 'bg-red-500/20 text-red-400' :
                    'bg-slate-500/20 text-slate-400'
                  )}>
                    Consensus: {strategySummary.consensus} ({strategySummary.avgConfidence}%)
                  </span>
                )}
              </div>
              <div className="space-y-2">
                {strategySignals.map((sig: any, idx: number) => {
                  const isBuy = sig.signal === 'BUY';
                  const isSell = sig.signal === 'SELL';
                  return (
                    <div key={idx} className="flex items-start gap-3 rounded-lg bg-slate-800/50 p-3">
                      <div className={cn(
                        'flex h-7 w-7 items-center justify-center rounded-full',
                        isBuy ? 'bg-green-500/20' : isSell ? 'bg-red-500/20' : 'bg-slate-500/20'
                      )}>
                        {isBuy ? <TrendingUpIcon className="h-3.5 w-3.5 text-green-400" /> :
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
                          )}>
                            {sig.signal}
                          </span>
                          <span className="text-[10px] text-slate-500">{sig.confidence}%</span>
                        </div>
                        <p className="mt-0.5 text-[11px] leading-relaxed text-slate-500 line-clamp-2">
                          {sig.reasoning}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Market Sentiment (Polymarket, Fear & Greed, News) */}
          {!loading && analysis?.marketSentiment && (
            <div className="rounded-xl border border-amber-500/30 bg-amber-950/20 p-4">
              <div className="mb-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Globe className="h-4 w-4 text-amber-400" />
                  <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
                    Market Sentiment
                  </h2>
                </div>
                {analysis.marketSentiment.compositeLabel && (
                  <span className={cn(
                    'rounded-full px-2 py-0.5 text-[10px] font-bold',
                    analysis.marketSentiment.compositeLabel.includes('Bullish') ? 'bg-green-500/20 text-green-400' :
                    analysis.marketSentiment.compositeLabel.includes('Bearish') ? 'bg-red-500/20 text-red-400' :
                    'bg-slate-500/20 text-slate-400'
                  )}>
                    {analysis.marketSentiment.compositeLabel}
                  </span>
                )}
              </div>
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                {/* Fear & Greed */}
                <div className="rounded-lg bg-slate-800/50 p-3">
                  <div className="flex items-center gap-1.5 mb-1.5">
                    <Gauge className="h-3 w-3 text-amber-400" />
                    <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500">Fear & Greed</span>
                  </div>
                  <p className="font-mono text-sm font-bold text-slate-100">
                    {analysis.marketSentiment.fearGreed?.score ?? '—'}
                    <span className="ml-1 text-[10px] font-normal text-slate-400">
                      ({analysis.marketSentiment.fearGreed?.label ?? 'N/A'})
                    </span>
                  </p>
                </div>

                {/* News Sentiment */}
                <div className="rounded-lg bg-slate-800/50 p-3">
                  <div className="flex items-center gap-1.5 mb-1.5">
                    <Newspaper className="h-3 w-3 text-blue-400" />
                    <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500">News</span>
                  </div>
                  <p className="font-mono text-sm font-bold text-slate-100">
                    {analysis.marketSentiment.news?.label ?? '—'}
                  </p>
                  {analysis.marketSentiment.news?.topHeadlines && (
                    <div className="mt-1.5 space-y-0.5">
                      {analysis.marketSentiment.news.topHeadlines.slice(0, 2).map((h: string, i: number) => (
                        <p key={i} className="text-[10px] text-slate-500 truncate">• {h}</p>
                      ))}
                    </div>
                  )}
                </div>

                {/* Polymarket */}
                <div className="rounded-lg bg-slate-800/50 p-3">
                  <div className="flex items-center gap-1.5 mb-1.5">
                    <BrainCircuit className="h-3 w-3 text-purple-400" />
                    <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500">Prediction Mkts</span>
                  </div>
                  {analysis.marketSentiment.polymarket && analysis.marketSentiment.polymarket.length > 0 ? (
                    <div className="space-y-0.5">
                      {(analysis.marketSentiment.polymarket as Array<{question: string; probability: number; volume: number}>).slice(0, 2).map((m: any, i: number) => {
                        const pct = Math.round((m.probability ?? 0) * 100);
                        return (
                          <p key={i} className="text-[10px] text-slate-500 truncate">
                            • {m.question?.slice(0, 35) ?? '?'}: <span className="text-amber-400">{pct}%</span>
                          </p>
                        );
                      })}
                    </div>
                  ) : (
                    <p className="text-[10px] text-slate-500">No data</p>
                  )}
                </div>
              </div>
              {/* Composite bias bar */}
              {analysis.marketSentiment.compositeBias !== undefined && (
                <div className="mt-3">
                  <div className="flex items-center justify-between text-[10px] text-slate-500 mb-1">
                    <span>Bearish</span>
                    <span>Bias: {(analysis.marketSentiment.compositeBias * 100).toFixed(0)}%</span>
                    <span>Bullish</span>
                  </div>
                  <div className="h-1.5 w-full rounded-full bg-slate-700/50 overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{
                        width: `${((analysis.marketSentiment.compositeBias + 1) / 2) * 100}%`,
                        background: analysis.marketSentiment.compositeBias >= 0
                          ? 'linear-gradient(90deg, #22c55e, #16a34a)'
                          : 'linear-gradient(90deg, #ef4444, #dc2626)',
                      }}
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Recent recommendations / trades for this symbol */}
          <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 p-4">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
                Recent {selectedSymbol} Trades
              </h2>
              <Clock className="h-4 w-4 text-slate-500" />
            </div>
            {loading ? (
              <div className="space-y-2">
                {Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="animate-pulse flex gap-3 rounded-lg bg-slate-800/50 p-3">
                    <div className="h-4 w-20 rounded bg-slate-700/50" />
                    <div className="h-4 w-16 rounded bg-slate-700/50" />
                    <div className="ml-auto h-4 w-16 rounded bg-slate-700/50" />
                  </div>
                ))}
              </div>
            ) : recentTrades.length === 0 ? (
              <p className="py-6 text-center text-sm text-slate-500">
                No recent trades for {selectedSymbol}
              </p>
            ) : (
              <div className="divide-y divide-slate-700/30">
                {recentTrades.map((trade) => (
                  <div
                    key={trade.id}
                    className="flex items-center gap-3 py-2.5"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <StatusBadge status={trade.side} />
                        <span className="text-xs text-slate-400">
                          {trade.qty} @ ${trade.entryPrice.toLocaleString()}
                        </span>
                      </div>
                    </div>
                    <div className="text-right">
                      <span
                        className={cn(
                          'text-xs font-semibold',
                          (trade.pnl ?? 0) >= 0 ? 'text-green-400' : 'text-red-400'
                        )}
                      >
                        {trade.pnl != null
                          ? `${trade.pnl >= 0 ? '+' : ''}$${trade.pnl.toFixed(2)}`
                          : '—'}
                      </span>
                      <p className="text-[10px] text-slate-600">
                        {new Date(trade.entryTime).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right column: AI Recommendation */}
        <div className="lg:col-span-1">
          <AiRecommendation
            analysis={analysis}
            loading={loading}
            onExecute={handleExecute}
            executing={executing}
          />
        </div>
      </div>
    </div>
  );
}
