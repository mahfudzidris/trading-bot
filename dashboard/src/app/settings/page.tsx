'use client';

import { useState } from 'react';
import { Save, RefreshCw, AlertCircle } from 'lucide-react';

export default function SettingsPage() {
  const [apiUrl, setApiUrl] = useState(
    process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  );
  const [mockMode, setMockMode] = useState(
    process.env.NEXT_PUBLIC_MOCK_MODE === 'true'
  );
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    // Simulate save
    await new Promise((r) => setTimeout(r, 800));
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Settings</h1>
        <p className="mt-1 text-sm text-slate-500">
          Configure your trading dashboard and API connections
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
        </div>

        <button
          onClick={handleSave}
          disabled={saving}
          className="mt-6 inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-emerald-500 disabled:opacity-50"
        >
          {saving ? (
            <RefreshCw className="h-4 w-4 animate-spin" />
          ) : saved ? (
            <span className="text-emerald-200">✓ Saved</span>
          ) : (
            <>
              <Save className="h-4 w-4" />
              Save Settings
            </>
          )}
        </button>
      </div>

      {/* About */}
      <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 p-6">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-400">
          About
        </h2>
        <div className="space-y-2 text-sm text-slate-400">
          <p>
            <span className="font-medium text-slate-300">TradeBot Dashboard</span> v1.0.0
          </p>
          <p>Built with Next.js 14, TypeScript, Recharts, and Tailwind CSS</p>
          <p className="text-xs text-slate-600">
            Powered by AI analysis engine
          </p>
        </div>
      </div>
    </div>
  );
}
