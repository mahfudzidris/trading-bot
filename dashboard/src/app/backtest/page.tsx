'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  runBacktest,
  fetchBacktestResults,
} from '@/lib/api';
import type { BacktestResult, BacktestTrade, EquitySnapshot } from '@/types';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Activity,
  BarChart3,
  Target,
  PlayCircle,
  RotateCw,
  AlertCircle,
  CheckCircle2,
  History,
  Clock,
} from 'lucide-react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
} from 'recharts';

const SYMBOLS = ['AAPL', 'TSLA', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'SPY', 'QQQ'];

// ── Metric Card ───────────────────────────────────────────────────────

function MetricCard({
  label,
  value,
  icon: Icon,
  positive,
  negative,
  format = 'number',
}: {
  label: string;
  value: number | string;
  icon: React.ElementType;
  positive?: boolean;
  negative?: boolean;
  format?: 'number' | 'percent' | 'currency' | 'ratio';
}) {
  const numValue = typeof value === 'number' ? value : parseFloat(value as string);
  let display: string;

  if (typeof value === 'string' && isNaN(numValue)) {
    display = value;
  } else {
    switch (format) {
      case 'percent':
        display = `${numValue >= 0 ? '+' : ''}${numValue.toFixed(2)}%`;
        break;
      case 'currency':
        display = `$${numValue.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
        break;
      case 'ratio':
        display = numValue.toFixed(2);
        break;
      default:
        display = numValue.toLocaleString('en-US', { maximumFractionDigits: 2 });
    }
  }

  const isPositive = positive ?? (typeof value === 'number' ? value >= 0 : true);
  const isNegative = negative ?? (typeof value === 'number' ? value < 0 : false);

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4 backdrop-blur-sm transition-all hover:border-slate-700">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-wider text-slate-500">{label}</p>
        <Icon className={`h-4 w-4 ${isPositive ? 'text-emerald-400' : isNegative ? 'text-red-400' : 'text-slate-400'}`} />
      </div>
      <p
        className={`mt-2 text-2xl font-bold ${
          isPositive ? 'text-emerald-400' : isNegative ? 'text-red-400' : 'text-slate-100'
        }`}
      >
        {display}
      </p>
    </div>
  );
}

// ── Backtest Form ─────────────────────────────────────────────────────

function BacktestForm({
  onRun,
  loading,
}: {
  onRun: (data: any) => void;
  loading: boolean;
}) {
  const [symbol, setSymbol] = useState('AAPL');
  const [startDate, setStartDate] = useState('2025-06-01');
  const [endDate, setEndDate] = useState('');
  const [capital, setCapital] = useState('100000');
  const [sl, setSl] = useState('2');
  const [tp, setTp] = useState('5');
  const [positionSize, setPositionSize] = useState('10');
  const [useAi, setUseAi] = useState(true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onRun({
      symbol,
      start_date: startDate,
      end_date: endDate || undefined,
      initial_capital: parseFloat(capital),
      stop_loss_pct: parseFloat(sl) / 100,
      take_profit_pct: parseFloat(tp) / 100,
      max_position_size_pct: parseFloat(positionSize) / 100,
      use_ai: useAi,
      commission_pct: 0.001,
      slippage_pct: 0.001,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {/* Symbol */}
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-400">Symbol</label>
          <select
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-200 focus:border-emerald-500 focus:outline-none"
          >
            {SYMBOLS.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>

        {/* Start Date */}
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-400">Start Date</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-200 focus:border-emerald-500 focus:outline-none"
          />
        </div>

        {/* End Date */}
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-400">
            End Date <span className="text-slate-600">(empty = today)</span>
          </label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-200 focus:border-emerald-500 focus:outline-none"
          />
        </div>

        {/* Capital */}
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-400">Initial Capital ($)</label>
          <input
            type="number"
            value={capital}
            onChange={(e) => setCapital(e.target.value)}
            min="1000"
            step="1000"
            className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-200 focus:border-emerald-500 focus:outline-none"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {/* Stop Loss */}
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-400">Stop Loss (%)</label>
          <input
            type="number"
            value={sl}
            onChange={(e) => setSl(e.target.value)}
            min="0.5"
            max="20"
            step="0.5"
            className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-200 focus:border-emerald-500 focus:outline-none"
          />
        </div>

        {/* Take Profit */}
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-400">Take Profit (%)</label>
          <input
            type="number"
            value={tp}
            onChange={(e) => setTp(e.target.value)}
            min="1"
            max="50"
            step="0.5"
            className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-200 focus:border-emerald-500 focus:outline-none"
          />
        </div>

        {/* Position Size */}
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-400">Position Size (%)</label>
          <input
            type="number"
            value={positionSize}
            onChange={(e) => setPositionSize(e.target.value)}
            min="1"
            max="50"
            step="1"
            className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-200 focus:border-emerald-500 focus:outline-none"
          />
        </div>

        {/* AI Toggle */}
        <div className="flex items-end">
          <label className="flex cursor-pointer items-center gap-2">
            <div className="relative">
              <input
                type="checkbox"
                checked={useAi}
                onChange={(e) => setUseAi(e.target.checked)}
                className="sr-only peer"
              />
              <div className="h-6 w-11 rounded-full bg-slate-700 after:absolute after:start-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:bg-slate-400 after:transition-all peer-checked:bg-emerald-600 peer-checked:after:translate-x-full peer-checked:after:bg-white"></div>
            </div>
            <span className="text-xs font-medium text-slate-400">AI Analysis</span>
          </label>
        </div>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-emerald-600 to-emerald-500 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-emerald-500/20 transition-all hover:from-emerald-500 hover:to-emerald-400 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? (
          <>
            <RotateCw className="h-4 w-4 animate-spin" />
            Running Backtest...
          </>
        ) : (
          <>
            <PlayCircle className="h-4 w-4" />
            Run Backtest
          </>
        )}
      </button>
    </form>
  );
}

// ── Equity Curve Chart ────────────────────────────────────────────────

function EquityCurveChart({ data }: { data: EquitySnapshot[] }) {
  if (!data || data.length === 0) return null;

  const chartData = data.map((d) => ({
    date: d.date,
    equity: d.total_equity,
  }));

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
      <h3 className="mb-3 text-sm font-semibold text-slate-300">Equity Curve</h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis
              dataKey="date"
              tick={{ fill: '#64748b', fontSize: 10 }}
              tickLine={false}
              axisLine={false}
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{ fill: '#64748b', fontSize: 10 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
              domain={['auto', 'auto']}
            />
            <Tooltip
              contentStyle={{
                background: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
                fontSize: '12px',
              }}
              formatter={(v: any) => [`$${v?.toLocaleString() ?? 0}`, 'Equity']}
              labelFormatter={(l) => `Date: ${l}`}
            />
            <Area
              type="monotone"
              dataKey="equity"
              stroke="#22c55e"
              strokeWidth={2}
              fill="url(#equityGradient)"
              dot={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// ── Trade Table ───────────────────────────────────────────────────────

function TradeTable({ trades }: { trades: BacktestTrade[] }) {
  if (!trades || trades.length === 0) return null;

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-800">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-slate-800 bg-slate-900/80">
            <th className="px-4 py-3 font-medium text-slate-400">Date</th>
            <th className="px-4 py-3 font-medium text-slate-400">Side</th>
            <th className="px-4 py-3 font-medium text-slate-400">Entry</th>
            <th className="px-4 py-3 font-medium text-slate-400">Exit</th>
            <th className="px-4 py-3 font-medium text-slate-400">Qty</th>
            <th className="px-4 py-3 font-medium text-slate-400">PnL</th>
            <th className="px-4 py-3 font-medium text-slate-400">Return</th>
            <th className="px-4 py-3 font-medium text-slate-400">Exit Reason</th>
          </tr>
        </thead>
        <tbody>
          {trades.map((t, i) => (
            <tr
              key={i}
              className="border-b border-slate-800/50 transition-colors hover:bg-slate-800/30"
            >
              <td className="whitespace-nowrap px-4 py-2.5 text-slate-300">{t.entry_time}</td>
              <td className="px-4 py-2.5">
                <span
                  className={`inline-block rounded-md px-2 py-0.5 text-xs font-semibold ${
                    t.side === 'BUY'
                      ? 'bg-emerald-500/10 text-emerald-400'
                      : 'bg-red-500/10 text-red-400'
                  }`}
                >
                  {t.side}
                </span>
              </td>
              <td className="px-4 py-2.5 font-mono text-slate-300">${t.entry_price.toFixed(2)}</td>
              <td className="px-4 py-2.5 font-mono text-slate-300">
                ${t.exit_price?.toFixed(2) ?? '-'}
              </td>
              <td className="px-4 py-2.5 text-slate-300">{t.qty}</td>
              <td
                className={`px-4 py-2.5 font-mono font-medium ${
                  t.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'
                }`}
              >
                {t.pnl >= 0 ? '+' : ''}${t.pnl.toFixed(2)}
              </td>
              <td
                className={`px-4 py-2.5 font-mono ${
                  t.pnl_pct >= 0 ? 'text-emerald-400' : 'text-red-400'
                }`}
              >
                {t.pnl_pct >= 0 ? '+' : ''}{t.pnl_pct.toFixed(2)}%
              </td>
              <td className="px-4 py-2.5">
                <span
                  className={`inline-block rounded-md px-2 py-0.5 text-xs font-medium ${
                    t.exit_reason === 'TP_HIT'
                      ? 'bg-emerald-500/10 text-emerald-400'
                      : t.exit_reason === 'SL_HIT'
                      ? 'bg-red-500/10 text-red-400'
                      : t.exit_reason === 'SIGNAL'
                      ? 'bg-blue-500/10 text-blue-400'
                      : 'bg-slate-500/10 text-slate-400'
                  }`}
                >
                  {t.exit_reason || 'N/A'}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── Monthly Returns Bar Chart ─────────────────────────────────────────

function MonthlyReturnsChart({ data }: { data: Record<string, number> }) {
  if (!data || Object.keys(data).length === 0) return null;

  const chartData = Object.entries(data)
    .map(([month, ret]) => ({
      month: month.slice(5) + '/' + month.slice(2, 4),
      return: ret,
    }))
    .reverse();

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
      <h3 className="mb-3 text-sm font-semibold text-slate-300">Monthly Returns</h3>
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis
              dataKey="month"
              tick={{ fill: '#64748b', fontSize: 10 }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              tick={{ fill: '#64748b', fontSize: 10 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v) => `${v.toFixed(1)}%`}
            />
            <Tooltip
              contentStyle={{
                background: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
                fontSize: '12px',
              }}
              formatter={(v: any) => [`${v >= 0 ? '+' : ''}${v.toFixed(2)}%`, 'Return']}
            />
            <Bar dataKey="return" radius={[4, 4, 0, 0]}>
              {chartData.map((entry, i) => (
                <Cell
                  key={i}
                  fill={entry.return >= 0 ? '#22c55e' : '#ef4444'}
                  fillOpacity={0.8}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// ── Results Display ───────────────────────────────────────────────────

function ResultsDisplay({ result }: { result: BacktestResult }) {
  const [showTrades, setShowTrades] = useState(false);

  if (!result) return null;

  return (
    <div className="mt-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="h-5 w-5 text-emerald-400" />
          <h2 className="text-lg font-bold text-slate-100">
            {result.symbol} Backtest Complete
          </h2>
        </div>
        <span className="rounded-lg bg-slate-800 px-3 py-1 text-xs text-slate-400">
          {result.start_date} → {result.end_date} ({result.days} days)
        </span>
      </div>

      {/* PnL Banner */}
      <div
        className={`rounded-xl border p-4 ${
          result.total_pnl >= 0
            ? 'border-emerald-800/50 bg-emerald-500/5'
            : 'border-red-800/50 bg-red-500/5'
        }`}
      >
        <div className="flex items-center gap-3">
          {result.total_pnl >= 0 ? (
            <TrendingUp className="h-8 w-8 text-emerald-400" />
          ) : (
            <TrendingDown className="h-8 w-8 text-red-400" />
          )}
          <div>
            <p className="text-2xl font-bold text-slate-100">
              Total PnL: ${result.total_pnl.toLocaleString('en-US', { minimumFractionDigits: 2 })}
              <span
                className={`ml-2 text-lg font-semibold ${
                  result.total_pnl_pct >= 0 ? 'text-emerald-400' : 'text-red-400'
                }`}
              >
                ({result.total_pnl_pct >= 0 ? '+' : ''}{result.total_pnl_pct.toFixed(2)}%)
              </span>
            </p>
            <p className="text-sm text-slate-500">
              ${result.initial_capital.toLocaleString()} → $
              {result.final_capital.toLocaleString('en-US', { minimumFractionDigits: 2 })}
              {result.cagr > 0 && (
                <span className="ml-3">
                  CAGR: <span className="text-emerald-400">+{result.cagr.toFixed(2)}%</span>
                </span>
              )}
            </p>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4 lg:grid-cols-6">
        <MetricCard label="Total Trades" value={result.total_trades} icon={Activity} />
        <MetricCard
          label="Win Rate"
          value={`${result.win_rate.toFixed(1)}%`}
          icon={Target}
          positive={result.win_rate >= 50}
          negative={result.win_rate < 40}
          format="percent"
        />
        <MetricCard
          label="Profit Factor"
          value={result.profit_factor}
          icon={BarChart3}
          positive={result.profit_factor >= 1.5}
          negative={result.profit_factor < 1.0}
          format="ratio"
        />
        <MetricCard
          label="Sharpe Ratio"
          value={result.sharpe_ratio}
          icon={Activity}
          positive={result.sharpe_ratio >= 1.0}
          negative={result.sharpe_ratio < 0.5}
          format="ratio"
        />
        <MetricCard
          label="Max Drawdown"
          value={result.max_drawdown_pct}
          icon={TrendingDown}
          positive={false}
          negative={result.max_drawdown_pct < -20}
          format="percent"
        />
        <MetricCard
          label="Avg Trade"
          value={result.avg_trade}
          icon={DollarSign}
          positive={result.avg_trade >= 0}
          negative={result.avg_trade < 0}
          format="currency"
        />
      </div>

      {/* More Metrics */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <MetricCard
          label="Sortino Ratio"
          value={result.sortino_ratio}
          icon={Activity}
          positive={result.sortino_ratio >= 0.8}
          negative={result.sortino_ratio < 0.3}
          format="ratio"
        />
        <MetricCard
          label="Calmar Ratio"
          value={result.calmar_ratio}
          icon={Activity}
          positive={result.calmar_ratio >= 0.5}
          negative={result.calmar_ratio < 0}
          format="ratio"
        />
        <MetricCard
          label="Volatility"
          value={result.volatility}
          icon={Activity}
          positive={false}
          format="percent"
        />
        <MetricCard
          label="Avg Bars Held"
          value={result.avg_bars_held}
          icon={Clock}
          format="number"
        />
      </div>

      {/* Win/Loss Summary */}
      <div className="flex gap-3">
        <div className="flex-1 rounded-xl border border-slate-800 bg-slate-900/50 p-3">
          <p className="text-xs text-slate-500">Wins</p>
          <p className="text-xl font-bold text-emerald-400">{result.wins}</p>
        </div>
        <div className="flex-1 rounded-xl border border-slate-800 bg-slate-900/50 p-3">
          <p className="text-xs text-slate-500">Losses</p>
          <p className="text-xl font-bold text-red-400">{result.losses}</p>
        </div>
        <div className="flex-1 rounded-xl border border-slate-800 bg-slate-900/50 p-3">
          <p className="text-xs text-slate-500">Avg Win</p>
          <p className="text-lg font-bold text-emerald-400">
            ${result.avg_win.toFixed(2)}
          </p>
        </div>
        <div className="flex-1 rounded-xl border border-slate-800 bg-slate-900/50 p-3">
          <p className="text-xs text-slate-500">Avg Loss</p>
          <p className="text-lg font-bold text-red-400">
            ${result.avg_loss.toFixed(2)}
          </p>
        </div>
        <div className="flex-1 rounded-xl border border-slate-800 bg-slate-900/50 p-3">
          <p className="text-xs text-slate-500">Expectancy</p>
          <p
            className={`text-lg font-bold ${result.expectancy >= 0 ? 'text-emerald-400' : 'text-red-400'}`}
          >
            ${result.expectancy.toFixed(2)}
          </p>
        </div>
      </div>

      {/* Charts */}
      <div className="grid gap-6 lg:grid-cols-2">
        {result.equity_curve && result.equity_curve.length > 0 && (
          <EquityCurveChart data={result.equity_curve} />
        )}
        {result.monthly_returns && Object.keys(result.monthly_returns).length > 0 && (
          <MonthlyReturnsChart data={result.monthly_returns} />
        )}
      </div>

      {/* Trades Toggle */}
      {result.trades && result.trades.length > 0 && (
        <div>
          <button
            onClick={() => setShowTrades(!showTrades)}
            className="mb-3 flex items-center gap-2 text-sm font-medium text-slate-300 transition-colors hover:text-slate-100"
          >
            <History className="h-4 w-4" />
            {showTrades ? 'Hide' : 'Show'} All Trades ({result.trades.length})
          </button>
          {showTrades && <TradeTable trades={result.trades} />}
        </div>
      )}

      {/* Errors */}
      {result.errors && result.errors.length > 0 && (
        <div className="rounded-xl border border-amber-800/50 bg-amber-500/5 p-3">
          <div className="flex items-start gap-2">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-amber-400" />
            <div>
              <p className="text-xs font-semibold text-amber-300">
                {result.errors.length} Warning{result.errors.length > 1 ? 's' : ''}
              </p>
              {result.errors.slice(0, 3).map((err, i) => (
                <p key={i} className="mt-1 text-xs text-amber-400/70">
                  {err}
                </p>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── History Panel ─────────────────────────────────────────────────────

function HistoryPanel({
  results,
  onSelect,
  selectedId,
}: {
  results: BacktestResult[];
  onSelect: (r: BacktestResult) => void;
  selectedId?: number;
}) {
  if (!results || results.length === 0) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900/30 p-6 text-center">
        <History className="mx-auto h-8 w-8 text-slate-600" />
        <p className="mt-2 text-sm text-slate-500">No backtest history yet.</p>
        <p className="text-xs text-slate-600">Run your first backtest above!</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <h3 className="mb-2 text-sm font-semibold text-slate-400">
        <History className="mr-1 inline h-4 w-4" />
        History
      </h3>
      {results.map((r) => (
        <button
          key={r.id}
          onClick={() => onSelect(r)}
          className={`w-full rounded-lg border p-3 text-left transition-all ${
            selectedId === r.id
              ? 'border-emerald-600 bg-emerald-500/5'
              : 'border-slate-800 bg-slate-900/30 hover:border-slate-700'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-slate-200">{r.symbol}</span>
            <span
              className={`text-xs font-mono font-semibold ${
                r.total_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'
              }`}
            >
              {r.total_pnl >= 0 ? '+' : ''}${r.total_pnl.toFixed(0)}
            </span>
          </div>
          <div className="mt-1 flex items-center justify-between">
            <span className="text-[10px] text-slate-500">
              {r.start_date} → {r.end_date}
            </span>
            <span className="rounded-md bg-slate-800 px-2 py-0.5 text-[10px] text-slate-400">
              {r.total_trades} trades · {r.win_rate.toFixed(0)}%
            </span>
          </div>
        </button>
      ))}
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────

export default function BacktestPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [history, setHistory] = useState<BacktestResult[]>([]);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'run' | 'history'>('run');

  const loadHistory = useCallback(async () => {
    try {
      const res = await fetchBacktestResults(10);
      setHistory(res || []);
    } catch {
      // Silently fail — history is non-critical
    }
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const handleRun = async (data: any) => {
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const response = await runBacktest(data);
      setResult(response.result);
      await loadHistory();
    } catch (err: any) {
      setError(err.message || 'Backtest failed. Check backend connection.');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectHistory = (r: BacktestResult) => {
    setResult(r);
    setActiveTab('run');
  };

  return (
    <div className="animate-fade-in space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Backtest</h1>
        <p className="mt-1 text-sm text-slate-400">
          Simulate your AI trading strategy against historical market data.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
        {/* Main */}
        <div className="space-y-6">
          {/* Tabs */}
          <div className="flex gap-1 rounded-lg border border-slate-800 bg-slate-900/50 p-1">
            <button
              onClick={() => setActiveTab('run')}
              className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-all ${
                activeTab === 'run'
                  ? 'bg-emerald-500/10 text-emerald-400 shadow-sm'
                  : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              <PlayCircle className="mr-1.5 inline h-4 w-4" />
              Run Backtest
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-all ${
                activeTab === 'history'
                  ? 'bg-emerald-500/10 text-emerald-400 shadow-sm'
                  : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              <History className="mr-1.5 inline h-4 w-4" />
              History ({history.length})
            </button>
          </div>

          {activeTab === 'run' && (
            <>
              {/* Form */}
              <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
                <h2 className="mb-4 text-sm font-semibold text-slate-300">Configure Backtest</h2>
                <BacktestForm onRun={handleRun} loading={loading} />
              </div>

              {/* Error */}
              {error && (
                <div className="rounded-xl border border-red-800/50 bg-red-500/5 p-4">
                  <div className="flex items-center gap-2">
                    <AlertCircle className="h-5 w-5 shrink-0 text-red-400" />
                    <p className="text-sm text-red-300">{error}</p>
                  </div>
                </div>
              )}

              {/* Results */}
              {result && <ResultsDisplay result={result} />}
            </>
          )}

          {activeTab === 'history' && (
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
              <HistoryPanel
                results={history}
                onSelect={handleSelectHistory}
                selectedId={result?.id}
              />
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="hidden lg:block">
          <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
            <HistoryPanel
              results={history}
              onSelect={handleSelectHistory}
              selectedId={result?.id}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
