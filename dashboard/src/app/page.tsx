'use client';

import { useEffect, useState, useCallback } from 'react';
import { Play, RefreshCw, AlertCircle, Sparkles } from 'lucide-react';
import SummaryCards from '@/components/SummaryCards';
import PnLChart from '@/components/PnLChart';
import TradeTable from '@/components/TradeTable';
import PerformancePanel from '@/components/PerformancePanel';
import {
  fetchAccount,
  fetchDailyReports,
  fetchTrades,
  fetchPerformance,
  runAnalysis,
} from '@/lib/api';
import type {
  Account,
  DailyReport,
  Performance,
  Trade,
} from '@/types';

export default function DashboardPage() {
  const [account, setAccount] = useState<Account | null>(null);
  const [reports, setReports] = useState<DailyReport[]>([]);
  const [recentTrades, setRecentTrades] = useState<Trade[]>([]);
  const [performance, setPerformance] = useState<Performance | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [runningAnalysis, setRunningAnalysis] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<string | null>(null);

  const isMockMode = process.env.NEXT_PUBLIC_MOCK_MODE === 'true';

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [acc, rep, trades, perf] = await Promise.all([
        fetchAccount(),
        fetchDailyReports(),
        fetchTrades({ limit: 10, page: 1 }),
        fetchPerformance(),
      ]);
      setAccount(acc);
      setReports(rep);
      setRecentTrades(trades?.data ?? []);
      setPerformance(perf);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleRunAnalysis = async () => {
    setRunningAnalysis(true);
    setAnalysisResult(null);
    try {
      const result = await runAnalysis();
      setAnalysisResult(result.message);
      // Refresh data after analysis
      await fetchData();
    } catch (err) {
      setAnalysisResult(
        err instanceof Error ? `Error: ${err.message}` : 'Analysis failed'
      );
    } finally {
      setRunningAnalysis(false);
    }
  };

  // Build chart data from daily reports
  const chartData = reports
    .slice()
    .reverse()
    .map((r) => ({ date: r.date, pnl: r.totalPnl }));

  return (
    <div className="mx-auto max-w-7xl space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Dashboard</h1>
          <p className="mt-1 text-sm text-slate-500">
            Trading overview and performance metrics
          </p>
        </div>
        <div className="flex items-center gap-3">
          {isMockMode && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-yellow-500/10 px-3 py-1 text-xs font-medium text-yellow-400">
              <Sparkles className="h-3 w-3" />
              Mock Mode
            </span>
          )}
          <button
            onClick={fetchData}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800/50 px-3 py-2 text-xs font-medium text-slate-300 transition-colors hover:bg-slate-700/50 disabled:opacity-50"
          >
            <RefreshCw
              className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`}
            />
            Refresh
          </button>
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="flex items-center gap-3 rounded-xl border border-red-500/20 bg-red-500/10 p-4">
          <AlertCircle className="h-5 w-5 flex-shrink-0 text-red-400" />
          <div>
            <p className="text-sm font-medium text-red-400">Data Load Error</p>
            <p className="text-xs text-red-400/80">{error}</p>
          </div>
          <button
            onClick={fetchData}
            className="ml-auto rounded-lg bg-red-500/20 px-3 py-1.5 text-xs font-medium text-red-300 hover:bg-red-500/30"
          >
            Retry
          </button>
        </div>
      )}

      {/* Summary Cards */}
      <SummaryCards
        totalPnl={account?.totalPnl ?? 0}
        winRate={performance?.winRate ?? 0}
        openPositions={(recentTrades ?? []).filter((t) => (t.status ?? '').toLowerCase() === 'open').length}
        dayPnl={account?.dayPnl ?? 0}
      />

      {/* Main grid: Chart + Performance */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
        <div className="lg:col-span-3">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
              PnL Trend (30 Days)
            </h2>
            <span
              className={`text-xs font-semibold ${
                (account?.totalPnl ?? 0) >= 0
                  ? 'text-green-400'
                  : 'text-red-400'
              }`}
            >
              {account?.totalPnl != null
                ? `${account.totalPnl >= 0 ? '+' : ''}$${account.totalPnl.toFixed(2)}`
                : ''}
            </span>
          </div>
          <PnLChart data={chartData} height={280} />
        </div>
        <div className="lg:col-span-1">
          <PerformancePanel performance={performance} loading={loading} />
        </div>
      </div>

      {/* Recent Trades + Quick Actions */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
        <div className="lg:col-span-3">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
              Recent Trades
            </h2>
            <a
              href="/trades"
              className="text-xs font-medium text-emerald-400 hover:text-emerald-300"
            >
              View All →
            </a>
          </div>
          <TradeTable
            trades={recentTrades}
            loading={loading}
            compact
          />
        </div>
        <div className="lg:col-span-1">
          <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 p-4">
            <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-400">
              Quick Actions
            </h3>
            <button
              onClick={handleRunAnalysis}
              disabled={runningAnalysis}
              className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-emerald-600 to-emerald-500 px-4 py-2.5 text-sm font-semibold text-white transition-all hover:from-emerald-500 hover:to-emerald-400 disabled:opacity-50"
            >
              {runningAnalysis ? (
                <RefreshCw className="h-4 w-4 animate-spin" />
              ) : (
                <Play className="h-4 w-4" />
              )}
              {runningAnalysis ? 'Analyzing...' : 'Run Daily Analysis'}
            </button>
            {analysisResult && (
              <div className="mt-3 rounded-lg bg-slate-800/50 p-2.5">
                <p className="text-xs text-slate-400">{analysisResult}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
