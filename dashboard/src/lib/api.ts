import type {
  Account,
  Analysis,
  DailyReport,
  Performance,
  Position,
  Trade,
  TradeFilters,
  PaginatedResponse,
  BacktestRequest,
  BacktestResult,
} from '@/types';

const BASE_URL = '';

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

// ── CamelCase converter for API snake_case responses ──────────────

function camelCase(str: string): string {
  return str.replace(/_([a-z])/g, (_, c) => c.toUpperCase());
}

function camelCaseKeys<T>(obj: unknown): T {
  if (Array.isArray(obj)) return obj.map(camelCaseKeys) as T;
  if (obj !== null && typeof obj === 'object') {
    const result: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(obj)) {
      result[camelCase(key)] = camelCaseKeys(value);
    }
    return result as T;
  }
  return obj as T;
}

async function request<T>(
  endpoint: string,
  options?: RequestInit,
  keepSnakeCase?: boolean
): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  try {
    const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json', ...options?.headers },
      signal: options?.signal,
      ...options,
    });
    if (!res.ok) {
      throw new ApiError(
        `API error: ${res.statusText} (${res.status})`,
        res.status
      );
    }
    const data = await res.json();
    // Backtest API returns snake_case — skip conversion for those endpoints
    if (keepSnakeCase || endpoint.startsWith('/api/backtest/')) {
      return data as T;
    }
    return camelCaseKeys(data) as T;
  } catch (err) {
    if (err instanceof ApiError) throw err;
    if (err instanceof TypeError && err.message === 'Failed to fetch') {
      console.warn(`API unavailable at ${url}, using mock data`);
      return getMockData<T>(endpoint, options);
    }
    throw new ApiError(`Network error: ${(err as Error).message}`, 0);
  }
}

// ── Mock Data Generation ──────────────────────────────────────────

function randomPnl(): number {
  return Math.round((Math.random() - 0.45) * 500 * 100) / 100;
}

function randomPrice(base = 100): number {
  return Math.round(base + (Math.random() - 0.5) * base * 0.2);
}

const SYMBOLS = ['BTC/USD', 'ETH/USD', 'SOL/USD', 'AVAX/USD', 'LINK/USD'];
const STRATEGIES = ['Momentum', 'Mean Reversion', 'Breakout', 'Grid', 'Scalping'];

function generateMockTrades(count: number): Trade[] {
  const trades: Trade[] = [];
  for (let i = 0; i < count; i++) {
    const daysAgo = Math.floor(Math.random() * 60);
    const entryTime = new Date(Date.now() - daysAgo * 86400000);
    const side = Math.random() > 0.5 ? 'buy' : 'sell';
    const entryPrice = randomPrice();
    const closed = Math.random() > 0.3;
    const exitPrice = closed ? randomPrice(entryPrice) : undefined;
    const qty = Math.round((Math.random() * 10 + 0.1) * 100) / 100;
    const pnl = closed && exitPrice
      ? Math.round((side === 'buy' ? exitPrice - entryPrice : entryPrice - exitPrice) * qty * 100) / 100
      : undefined;
    const pnlPct = closed && exitPrice
      ? Math.round((side === 'buy' ? (exitPrice - entryPrice) / entryPrice : (entryPrice - exitPrice) / entryPrice) * 10000) / 100
      : undefined;
    const exitTime = closed
      ? new Date(entryTime.getTime() + Math.random() * 7 * 86400000).toISOString()
      : undefined;

    trades.push({
      id: `trade-${i + 1}`,
      symbol: SYMBOLS[Math.floor(Math.random() * SYMBOLS.length)],
      side: side as 'buy' | 'sell',
      qty,
      entryPrice,
      exitPrice,
      entryTime: entryTime.toISOString(),
      exitTime,
      pnl,
      pnlPct,
      status: closed ? 'closed' : 'open',
      stopLoss: Math.round(entryPrice * 0.95 * 100) / 100,
      takeProfit: Math.round(entryPrice * 1.08 * 100) / 100,
      strategy: STRATEGIES[Math.floor(Math.random() * STRATEGIES.length)],
      aiReasoning: closed
        ? `AI analysis indicated ${side === 'buy' ? 'bullish' : 'bearish'} momentum based on RSI divergence and volume profile. Support/resistance levels confirmed.`
        : undefined,
      aiConfidence: closed ? Math.round((Math.random() * 40 + 60) * 100) / 100 : undefined,
    });
  }
  return trades;
}

function getMockData<T>(endpoint: string, _options?: RequestInit): T {
  const mockTrades = generateMockTrades(100);
  const mockPositions: Position[] = SYMBOLS.slice(0, 3).map((sym, i) => ({
    symbol: sym,
    qty: Math.round((Math.random() * 5 + 0.5) * 100) / 100,
    avgEntryPrice: randomPrice(),
    currentPrice: randomPrice(),
    unrealizedPnl: randomPnl(),
  }));

  const mockReports: DailyReport[] = Array.from({ length: 30 }, (_, i) => {
    const date = new Date(Date.now() - i * 86400000);
    const pnl = randomPnl();
    const winCount = Math.floor(Math.random() * 8);
    const lossCount = Math.floor(Math.random() * 5);
    return {
      id: `report-${i + 1}`,
      date: date.toISOString().split('T')[0],
      totalPnl: pnl,
      winCount,
      lossCount,
      totalTrades: winCount + lossCount,
      winRate: winCount + lossCount > 0
        ? Math.round((winCount / (winCount + lossCount)) * 10000) / 100
        : 0,
      startingBalance: 10000 + (i > 0 ? Math.random() * 2000 - 1000 : 0),
      endingBalance: 10000 + (Math.random() * 3000 - 500),
    };
  });

  const totalPnl = mockReports.reduce((sum, r) => sum + r.totalPnl, 0);
  const winCount = mockReports.reduce((sum, r) => sum + r.winCount, 0);
  const lossCount = mockReports.reduce((sum, r) => sum + r.lossCount, 0);

  if (endpoint === '/api/account') {
    return {
      balance: 10000 + totalPnl,
      buyingPower: 5000 + totalPnl * 0.5,
      totalPnl,
      dayPnl: mockReports[0]?.totalPnl ?? 0,
    } as T;
  }
  if (endpoint.startsWith('/api/positions')) {
    return mockPositions as T;
  }
  if (endpoint.startsWith('/api/trades')) {
    const url = new URL(endpoint, 'http://x');
    const page = parseInt(url.searchParams.get('page') || '1');
    const limit = parseInt(url.searchParams.get('limit') || '10');
    const symbol = url.searchParams.get('symbol');
    const side = url.searchParams.get('side');
    const status = url.searchParams.get('status');

    let filtered = [...mockTrades];
    if (symbol) filtered = filtered.filter((t) => t.symbol === symbol);
    if (side) filtered = filtered.filter((t) => t.side === side);
    if (status) filtered = filtered.filter((t) => t.status === status);

    const start = (page - 1) * limit;
    const paginated = filtered.slice(start, start + limit);
    return {
      data: paginated,
      total: filtered.length,
      page,
      limit,
      totalPages: Math.ceil(filtered.length / limit),
    } as T;
  }
  if (endpoint.startsWith('/api/daily-reports')) {
    return mockReports as T;
  }
  if (endpoint.startsWith('/api/performance')) {
    const sortedTrades = [...mockTrades].sort((a, b) => (b.pnl ?? 0) - (a.pnl ?? 0));
    return {
      totalPnl,
      winRate: winCount + lossCount > 0
        ? Math.round((winCount / (winCount + lossCount)) * 10000) / 100
        : 0,
      tradesCount: mockTrades.length,
      bestTrade: sortedTrades[0] || mockTrades[0],
      worstTrade: sortedTrades[sortedTrades.length - 1] || mockTrades[mockTrades.length - 1],
    } as T;
  }
  if (endpoint.startsWith('/api/analyze')) {
    const sym = endpoint.split('/').pop() || 'BTC/USD';
    return {
      symbol: sym,
      action: Math.random() > 0.6 ? 'buy' : Math.random() > 0.3 ? 'sell' : 'hold',
      confidence: Math.round((Math.random() * 40 + 60) * 100) / 100,
      reasoning: `Analysis for ${sym} shows strong bullish momentum on the 4H timeframe. RSI is at 62 (neutral-bullish), MACD is crossing above signal line, and volume is increasing. Key resistance at $52,400. Support levels holding at $48,900. Market structure suggests continued uptrend with potential pullback to $50,200 before next leg up.`,
      takeProfit: randomPrice(50000),
      stopLoss: randomPrice(48000),
      positionSizePct: Math.round((Math.random() * 20 + 5) * 100) / 100,
      currentPrice: randomPrice(50000),
    } as T;
  }
  if (endpoint === '/api/run-analysis') {
    return { success: true, message: 'Daily analysis completed successfully. 3 trade signals generated.' } as T;
  }

  return {} as T;
}

// ── Exported API Functions ────────────────────────────────────────

export async function fetchAccount(signal?: AbortSignal): Promise<Account> {
  const raw = await request<Record<string, unknown>>('/api/account', { signal });
  return {
    balance: (raw.balance as number) ?? 0,
    buyingPower: (raw.buyingPower as number) ?? (raw.buying_power as number) ?? 0,
    totalPnl: (raw.pnl as number) ?? (raw.totalPnl as number) ?? 0,
    dayPnl: (raw.dayPnl as number) ?? 0,
    cash: (raw.cash as number) ?? 0,
    portfolioValue: (raw.portfolioValue as number) ?? (raw.portfolio_value as number) ?? 0,
    status: (raw.status as string) ?? '',
  };
}

export async function fetchPositions(signal?: AbortSignal): Promise<Position[]> {
  return request<Position[]>('/api/positions', { signal });
}

export async function fetchTrades(
  filters?: TradeFilters,
  signal?: AbortSignal
): Promise<PaginatedResponse<Trade>> {
  const params = new URLSearchParams();
  if (filters?.symbol) params.set('symbol', filters.symbol);
  if (filters?.startDate) params.set('startDate', filters.startDate);
  if (filters?.endDate) params.set('endDate', filters.endDate);
  if (filters?.side) params.set('side', filters.side);
  if (filters?.status) params.set('status', filters.status);
  if (filters?.page) params.set('page', String(filters.page));
  if (filters?.limit) params.set('limit', String(filters.limit));
  const qs = params.toString();
  const res = await request<Trade[] | PaginatedResponse<Trade>>(`/api/trades${qs ? `?${qs}` : ''}`, { signal });
  // API returns array directly; wrap it in PaginatedResponse
  if (Array.isArray(res)) {
    return { data: res, total: res.length, page: 1, limit: res.length, totalPages: 1 };
  }
  return res;
}

export async function fetchDailyReports(signal?: AbortSignal): Promise<DailyReport[]> {
  return request<DailyReport[]>('/api/daily-reports', { signal });
}

export async function executeTrade(data: {
  symbol: string;
  side: string;
  qty: number;
  ai_reasoning?: string;
  ai_confidence?: number;
  stop_loss?: number;
  take_profit?: number;
}): Promise<{ ok: boolean; order: any; trade: any }> {
  return request('/api/trade/execute', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function fetchStrategy(symbol?: string): Promise<any> {
  const qs = symbol ? `?symbol=${symbol}` : '';
  return request(`/api/strategy${qs}`);
}

export async function fetchPerformance(signal?: AbortSignal): Promise<Performance> {
  return request<Performance>('/api/performance', { signal });
}

export async function analyzeSymbol(symbol: string): Promise<Analysis> {
  const raw = await request<Record<string, unknown>>(`/api/analyze/${symbol}`);
  const dec = (raw.decision as Record<string, unknown>) ?? {};
  const price = (raw.priceData as Record<string, unknown>) ?? {};
  return {
    symbol: symbol,
    action: ((dec.action as string) ?? 'hold').toLowerCase() as 'buy' | 'sell' | 'hold',
    confidence: (dec.confidence as number) ?? 0,
    reasoning: (dec.reasoning as string) ?? '',
    takeProfit: (dec.takeProfit as number) ?? (dec.take_profit as number) ?? 0,
    stopLoss: (dec.stopLoss as number) ?? (dec.stop_loss as number) ?? 0,
    positionSizePct: (dec.positionSizePct as number) ?? (dec.position_size_pct as number) ?? 0,
    currentPrice: (price.price as number) ?? 0,
    strategySignals: (raw.strategySignals as any[]) ?? (raw.strategy_signals as any[]) ?? [],
    strategySummary: (raw.strategySummary as any) ?? (raw.strategy_summary as any) ?? null,
    marketSentiment: (raw.marketSentiment as any) ?? (raw.market_sentiment as any) ?? undefined,
  };
}

export async function runAnalysis(): Promise<{ success: boolean; message: string }> {
  const raw = await request<Record<string, unknown>>('/api/run-analysis', {
    method: 'POST',
  });
  const pnl = (raw.totalPnl ?? 0) as number;
  const trades = (raw.tradesExecuted ?? 0) as number;
  return {
    success: true,
    message: `Daily analysis completed. ${trades} trade(s) executed, PnL: $${pnl.toFixed(2)}`,
  };
}

// ── Backtest API Functions ────────────────────────────────────────────────

export async function runBacktest(req: BacktestRequest): Promise<{ ok: boolean; result: BacktestResult }> {
  return request<{ ok: boolean; result: BacktestResult }>('/api/backtest/run', {
    method: 'POST',
    body: JSON.stringify(req),
  });
}

export async function fetchBacktestResults(limit = 10): Promise<BacktestResult[]> {
  return request<BacktestResult[]>(`/api/backtest/results?limit=${limit}`);
}

export async function fetchBacktestDetail(id: number): Promise<BacktestResult> {
  return request<BacktestResult>(`/api/backtest/results/${id}`);
}
