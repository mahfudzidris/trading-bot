'use client';

import { useState, useEffect } from 'react';
import { Save, RefreshCw, AlertCircle, Check, Activity } from 'lucide-react';

export default function SettingsPage() {
  const [apiUrl, setApiUrl] = useState(
    process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  );
  const [mockMode, setMockMode] = useState(false);
  const [autoTrade, setAutoTrade] = useState(false);
  const [marketAutoRun, setMarketAutoRun] = useState(false);
  const [marketWatchInterval, setMarketWatchInterval] = useState(30);
  const [watcherRunning, setWatcherRunning] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [restartRequired, setRestartRequired] = useState(false);

  // Fetch current settings on mount
  useEffect(() => {
    const init = async () => {
      try {
        const res = await fetch(`${apiUrl}/api/health`);
        const data = await res.json();
        setMockMode(data.mock_mode === true);
        setAutoTrade(data.auto_trade === true);
        setMarketAutoRun(data.market_auto_run === true);
        setMarketWatchInterval(data.market_watch_interval ?? 30);
        setWatcherRunning(data.market_watcher?.running === true);
      } catch {
        // keep defaults
      }
    };
    init();
  }, [apiUrl]);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSaved(false);
    setRestartRequired(false);
    try {
      const res = await fetch(`${apiUrl}/api/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mock_mode: mockMode,
          auto_trade: autoTrade,
          market_auto_run: marketAutoRun,
          market_watch_interval: marketWatchInterval,
        }),
      });
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      const data = await res.json();
      setSaved(true);
      setRestartRequired(data.restart_required === true);
      setTimeout(() => setSaved(false), 4000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Settings</h1>
        <p className="mt-1 text-sm text-slate-500">
          Configure your trading bot — modes, execution, and automation
        </p>
      </div>

      {/* API Configuration */}
      <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 p-6">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-400">
          API Configuration
        </h2>

        <div className="space-y-4">
          <div>
            <label className="mb-1.5 block text-xs font-medium text-slate-300">
              API Base URL
            </label>
            <input
              type="text"
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              placeholder="http://localhost:8000"
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-2.5 text-sm text-slate-200 outline-none transition-colors placeholder:text-slate-600 focus:border-emerald-500/50"
            />
            <p className="mt-1 text-[10px] text-slate-600">
              The backend API endpoint for trading data
            </p>
          </div>

          {/* ── Mock Mode ── */}
          <div className="flex items-center justify-between rounded-lg bg-slate-900/50 p-4">
            <div>
              <p className="text-sm font-medium text-slate-200">Mock Mode</p>
              <p className="text-xs text-slate-500">
                Use mock data instead of live API
              </p>
            </div>
            <button
              onClick={() => setMockMode(!mockMode)}
              className={`relative h-6 w-11 rounded-full transition-colors ${
                mockMode ? 'bg-emerald-600' : 'bg-slate-700'
              }`}
            >
              <span
                className={`absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white transition-transform ${
                  mockMode ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>

          {/* ── Auto Trade ── */}
          <div className="flex items-center justify-between rounded-lg bg-slate-900/50 p-4">
            <div>
              <p className="text-sm font-medium text-slate-200">Auto Trade</p>
              <p className="text-xs text-slate-500">
                Automatically execute BUY/SELL based on AI signals
              </p>
            </div>
            <button
              onClick={() => setAutoTrade(!autoTrade)}
              className={`relative h-6 w-11 rounded-full transition-colors ${
                autoTrade ? 'bg-emerald-600' : 'bg-slate-700'
              }`}
            >
              <span
                className={`absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white transition-transform ${
                  autoTrade ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>
        </div>
      </div>

      {/* ── 24/7 Market Watcher Section ── */}
      <div className="rounded-xl border border-cyan-700/50 bg-cyan-800/20 p-6">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-cyan-400 flex items-center gap-2">
          <Activity className="h-4 w-4" />
          24/7 Market Watcher
        </h2>

        <div className="space-y-4">
          {/* Watcher status indicator */}
          <div className="flex items-center gap-2 rounded-lg bg-slate-900/50 px-4 py-2">
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                watcherRunning && marketAutoRun
                  ? 'bg-emerald-400 animate-pulse'
                  : 'bg-slate-600'
              }`}
            />
            <span className="text-xs text-slate-300">
              {watcherRunning && marketAutoRun
                ? 'Watcher active — analysing every '
                : watcherRunning
                ? 'Watcher running (paused) — '
                : 'Watcher not started — '}
              {watcherRunning && marketAutoRun
                ? `${marketWatchInterval} min during market hours`
                : 'toggle ON to activate'}
            </span>
          </div>

          {/* Market Auto Run toggle */}
          <div className="flex items-center justify-between rounded-lg bg-slate-900/50 p-4">
            <div>
              <p className="text-sm font-medium text-slate-200">
                Market Auto Run
              </p>
              <p className="text-xs text-slate-500">
                Background loop runs strategy every N minutes during market
                hours (Mon–Fri, 9:30–16:00 ET). No manual action needed.
              </p>
            </div>
            <button
              onClick={() => setMarketAutoRun(!marketAutoRun)}
              className={`relative h-6 w-11 rounded-full transition-colors ${
                marketAutoRun ? 'bg-cyan-600' : 'bg-slate-700'
              }`}
            >
              <span
                className={`absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white transition-transform ${
                  marketAutoRun ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>

          {/* Watch Interval selector */}
          <div className="rounded-lg bg-slate-900/50 p-4">
            <label className="mb-1.5 block text-xs font-medium text-slate-300">
              Check Interval
            </label>
            <div className="flex items-center gap-3">
              <input
                type="range"
                min={5}
                max={120}
                step={5}
                value={marketWatchInterval}
                onChange={(e) =>
                  setMarketWatchInterval(Number(e.target.value))
                }
                className="flex-1 accent-cyan-500"
              />
              <span className="min-w-[4rem] text-right text-sm font-semibold text-cyan-400">
                {marketWatchInterval} min
              </span>
            </div>
            <div className="mt-1 flex justify-between text-[10px] text-slate-600">
              <span>5 min (aggressive)</span>
              <span>30 min (recommended)</span>
              <span>120 min (conservative)</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Save Button ── */}
      <div className="flex items-center gap-3">
        <button
          onClick={handleSave}
          disabled={saving}
          className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-emerald-500 disabled:opacity-50"
        >
          {saving ? (
            <>
              <RefreshCw className="h-4 w-4 animate-spin" />
              Saving...
            </>
          ) : saved ? (
            <>
              <Check className="h-4 w-4" />
              Saved ✓
            </>
          ) : (
            <>
              <Save className="h-4 w-4" />
              Save Settings
            </>
          )}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 rounded-lg bg-red-500/10 p-3">
          <AlertCircle className="h-4 w-4 flex-shrink-0 text-red-400" />
          <p className="text-xs text-red-400">{error}</p>
        </div>
      )}

      {/* Saved notes */}
      {saved && restartRequired && (
        <div className="rounded-lg bg-amber-500/10 p-3">
          <p className="text-xs text-amber-400">
            ⏳ Mock Mode / Auto Trade changes require a backend restart. Refresh
            dashboard in ~5s after restart.
          </p>
        </div>
      )}

      {saved && !restartRequired && (
        <div className="rounded-lg bg-emerald-500/10 p-3">
          <p className="text-xs text-emerald-400">
            ✅ Market Auto Run / Interval applied LIVE — no restart needed.
          </p>
        </div>
      )}

      <p className="text-[10px] text-slate-600 leading-relaxed">
        <strong>Mock Mode</strong> = guna data simulasi. <strong>Live</strong>{' '}
        = TwelveData + Alpaca (paper).<br />
        <strong>Auto Trade</strong> = execute BUY/SELL guna AI signals, bracket
        TP/SL automatik via Alpaca.<br />
        <strong>Market Auto Run</strong> = bot analyse & trade sendiri selama
        market hours. Tak perlu klik apa-apa.<br />
        <strong>Check Interval</strong> = berapa minit sekali bot semak market
        & laksana analysis.
      </p>
    </div>
  );
}
