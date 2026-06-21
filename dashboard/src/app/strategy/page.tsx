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
  promptTemplate: string;
  indicators: Indicator[];
  decisionFields: Record<string, string>;
  mockFallbackLogic: string[];
  riskParameters: RiskParams;
  account: { buyingPower: number; cash: number };
  model: ModelInfo;
}

export default function StrategyPage() {
  const [data, setData] = useState<StrategyData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showPrompt, setShowPrompt] = useState(false);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchStrategy();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load strategy');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

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
            onClick={loadData}
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
        <button
          onClick={loadData}
          className="inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800/50 px-3 py-2 text-xs font-medium text-slate-300 transition-colors hover:bg-slate-700/50"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh
        </button>
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

      {/* AI Prompt */}
      <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 p-6">
        <button
          onClick={() => setShowPrompt(!showPrompt)}
          className="flex w-full items-center justify-between"
        >
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/10">
              <BookOpen className="h-4 w-4 text-indigo-400" />
            </div>
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
              AI Prompt Template
            </h2>
          </div>
          <span className="text-xs text-slate-500">{showPrompt ? 'Hide' : 'Show'} Full Prompt</span>
        </button>
        {showPrompt && (
          <pre className="mt-4 overflow-x-auto rounded-lg bg-slate-900/80 p-4 text-xs leading-relaxed text-slate-300">
            {data.promptTemplate}
          </pre>
        )}
        {!showPrompt && (
          <p className="mt-3 text-xs text-slate-500">
            Click to view the full system prompt sent to the DeepSeek model for every analysis.
          </p>
        )}
      </div>

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
