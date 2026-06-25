'use client';

import { useEffect, useState, useCallback } from 'react';
import {
  Search,
  Download,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  AlertCircle,
  Filter,
} from 'lucide-react';
import TradeTable from '@/components/TradeTable';
import { fetchTrades } from '@/lib/api';
import type { Trade, PaginatedResponse } from '@/types';
import { cn } from '@/lib/utils';

const SYMBOLS = ['', 'AAPL', 'TSLA', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'SPY', 'QQQ'];

export default function TradesPage() {
  const [tradesData, setTradesData] = useState<PaginatedResponse<Trade> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [symbol, setSymbol] = useState('');
  const [side, setSide] = useState<'buy' | 'sell' | ''>('');
  const [status, setStatus] = useState<'open' | 'closed' | ''>('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [page, setPage] = useState(1);
  const limit = 15;

  const loadTrades = useCallback(async (p: number) => {
    setLoading(true);
    setError(null);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);

    try {
      const data = await fetchTrades(
        {
          symbol: symbol || undefined,
          side: side || undefined,
          status: status || undefined,
          startDate: startDate || undefined,
          endDate: endDate || undefined,
          page: p,
          limit,
        },
        controller.signal
      );
      setTradesData(data);
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        setError('Request timed out. Please try again.');
      } else {
        setError(err instanceof Error ? err.message : 'Failed to load trades');
      }
    } finally {
      clearTimeout(timeoutId);
      setLoading(false);
    }
  }, [symbol, side, status, startDate, endDate]);

  useEffect(() => {
    loadTrades(page);
  }, [loadTrades, page]);

  const handleSearch = () => {
    setPage(1);
    loadTrades(1);
  };

  const handleExport = () => {
    if (!tradesData?.data) return;
    const csv = [
      ['Date', 'Symbol', 'Side', 'Qty', 'Entry', 'Exit', 'PnL', 'PnL%', 'Status'].join(','),
      ...tradesData.data.map((t) =>
        [
          new Date(t.entryTime).toISOString(),
          t.symbol,
          t.side,
          t.qty,
          t.entryPrice,
          t.exitPrice || '',
          t.pnl || '',
          t.pnlPct || '',
          t.status,
        ].join(',')
      ),
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `trades-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="mx-auto max-w-7xl space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Trade History</h1>
          <p className="mt-1 text-sm text-slate-500">
            View and filter all executed trades
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleExport}
            disabled={!tradesData?.data.length}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800/50 px-3 py-2 text-xs font-medium text-slate-300 transition-colors hover:bg-slate-700/50 disabled:opacity-50"
          >
            <Download className="h-3.5 w-3.5" />
            Export CSV
          </button>
          <button
            onClick={() => loadTrades(page)}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800/50 px-3 py-2 text-xs font-medium text-slate-300 transition-colors hover:bg-slate-700/50 disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-end gap-3 rounded-xl border border-slate-700/50 bg-slate-800/30 p-4">
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <Filter className="h-3.5 w-3.5" />
          Filters
        </div>

        <div className="flex flex-1 flex-wrap items-center gap-3">
          {/* Symbol */}
          <div>
            <label className="mb-1 block text-[10px] font-medium uppercase tracking-wider text-slate-500">
              Symbol
            </label>
            <select
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs text-slate-200 outline-none focus:border-emerald-500/50"
            >
              <option value="">All</option>
              {SYMBOLS.filter(Boolean).map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          {/* Side */}
          <div>
            <label className="mb-1 block text-[10px] font-medium uppercase tracking-wider text-slate-500">
              Side
            </label>
            <select
              value={side}
              onChange={(e) => setSide(e.target.value as 'buy' | 'sell' | '')}
              className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs text-slate-200 outline-none focus:border-emerald-500/50"
            >
              <option value="">All</option>
              <option value="buy">Buy</option>
              <option value="sell">Sell</option>
            </select>
          </div>

          {/* Status */}
          <div>
            <label className="mb-1 block text-[10px] font-medium uppercase tracking-wider text-slate-500">
              Status
            </label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as 'open' | 'closed' | '')}
              className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs text-slate-200 outline-none focus:border-emerald-500/50"
            >
              <option value="">All</option>
              <option value="open">Open</option>
              <option value="closed">Closed</option>
            </select>
          </div>

          {/* Date range */}
          <div>
            <label className="mb-1 block text-[10px] font-medium uppercase tracking-wider text-slate-500">
              From
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs text-slate-200 outline-none focus:border-emerald-500/50"
            />
          </div>
          <div>
            <label className="mb-1 block text-[10px] font-medium uppercase tracking-wider text-slate-500">
              To
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs text-slate-200 outline-none focus:border-emerald-500/50"
            />
          </div>
        </div>

        <button
          onClick={handleSearch}
          className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white transition-colors hover:bg-emerald-500"
        >
          <Search className="h-3.5 w-3.5" />
          Search
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-3 rounded-xl border border-red-500/20 bg-red-500/10 p-4">
          <AlertCircle className="h-5 w-5 flex-shrink-0 text-red-400" />
          <p className="text-sm text-red-400">{error}</p>
          <button
            onClick={() => loadTrades(page)}
            className="ml-auto rounded-lg bg-red-500/20 px-3 py-1.5 text-xs font-medium text-red-300 hover:bg-red-500/30"
          >
            Retry
          </button>
        </div>
      )}

      {/* Table */}
      <TradeTable
        trades={tradesData?.data ?? []}
        loading={loading}
      />

      {/* Pagination */}
      {tradesData && tradesData.totalPages > 1 && (
        <div className="flex items-center justify-between rounded-xl border border-slate-700/50 bg-slate-800/30 px-4 py-3">
          <p className="text-xs text-slate-500">
            Showing {tradesData.data.length} of {tradesData.total} trades
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="rounded-lg border border-slate-700 p-1.5 text-slate-400 transition-colors hover:bg-slate-700/50 disabled:opacity-50"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            {Array.from(
              { length: Math.min(5, tradesData.totalPages) },
              (_, i) => {
                const start = Math.max(
                  1,
                  Math.min(
                    page - 2,
                    tradesData.totalPages - 4
                  )
                );
                const p = start + i;
                if (p > tradesData.totalPages) return null;
                return (
                  <button
                    key={p}
                    onClick={() => setPage(p)}
                    className={cn(
                      'h-8 w-8 rounded-lg text-xs font-medium transition-colors',
                      p === page
                        ? 'bg-emerald-600 text-white'
                        : 'text-slate-400 hover:bg-slate-700/50'
                    )}
                  >
                    {p}
                  </button>
                );
              }
            )}
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={page >= (tradesData?.totalPages ?? 1)}
              className="rounded-lg border border-slate-700 p-1.5 text-slate-400 transition-colors hover:bg-slate-700/50 disabled:opacity-50"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
