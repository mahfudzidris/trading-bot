export interface Trade {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  qty: number;
  entryPrice: number;
  exitPrice?: number;
  entryTime: string;
  exitTime?: string;
  pnl?: number;
  pnlPct?: number;
  status: 'open' | 'closed';
  stopLoss?: number;
  takeProfit?: number;
  strategy: string;
  aiReasoning?: string;
  aiConfidence?: number;
}

export interface DailyReport {
  id: string;
  date: string;
  totalPnl: number;
  winCount: number;
  lossCount: number;
  totalTrades: number;
  winRate: number;
  startingBalance: number;
  endingBalance: number;
}

export interface Position {
  symbol: string;
  qty: number;
  avgEntryPrice: number;
  currentPrice: number;
  unrealizedPnl: number;
}

export interface Account {
  balance: number;
  buyingPower: number;
  totalPnl: number;
  dayPnl: number;
}

export interface Analysis {
  symbol: string;
  action: 'buy' | 'sell' | 'hold';
  confidence: number;
  reasoning: string;
  takeProfit: number;
  stopLoss: number;
  positionSizePct: number;
  currentPrice: number;
  strategySignals?: any[];
  strategySummary?: any;
  marketSentiment?: {
    polymarket?: any[];
    fearGreed?: { score: number; label: string; previousClose: number };
    news?: { score: number; label: string; headlineCount: number; topHeadlines: string[] };
    compositeLabel: string;
    compositeBias: number;
  };
}

export interface Performance {
  totalPnl: number;
  winRate: number;
  tradesCount: number;
  bestTrade: Trade;
  worstTrade: Trade;
}

export interface TradeFilters {
  symbol?: string;
  startDate?: string;
  endDate?: string;
  side?: 'buy' | 'sell' | '';
  status?: 'open' | 'closed' | '';
  page?: number;
  limit?: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

// ── Backtest Types ────────────────────────────────────────────────────

export interface BacktestRequest {
  symbol: string;
  start_date: string;
  end_date?: string;
  initial_capital?: number;
  stop_loss_pct?: number;
  take_profit_pct?: number;
  max_position_size_pct?: number;
  commission_pct?: number;
  slippage_pct?: number;
  use_ai?: boolean;
}

export interface BacktestTrade {
  symbol: string;
  side: string;
  qty: number;
  entry_price: number;
  exit_price: number | null;
  entry_time: string;
  exit_time: string | null;
  pnl: number;
  pnl_pct: number;
  status: string;
  stop_loss: number;
  take_profit: number;
  strategy: string;
  ai_reasoning: string;
  ai_confidence: number;
  exit_reason: string;
}

export interface EquitySnapshot {
  date: string;
  cash: number;
  holdings_value: number;
  total_equity: number;
  daily_pnl: number;
}

export interface BacktestResult {
  id?: number;
  created_at?: string;
  symbol: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  days: number;
  total_pnl: number;
  total_pnl_pct: number;
  final_capital: number;
  total_trades: number;
  wins: number;
  losses: number;
  win_rate: number;
  avg_win: number;
  avg_loss: number;
  best_trade: number;
  worst_trade: number;
  avg_trade: number;
  profit_factor: number;
  expectancy: number;
  max_drawdown: number;
  max_drawdown_pct: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  calmar_ratio: number;
  cagr: number;
  volatility: number;
  avg_bars_held: number;
  max_consecutive_wins: number;
  max_consecutive_losses: number;
  trades?: BacktestTrade[];
  equity_curve?: EquitySnapshot[];
  monthly_returns?: Record<string, number>;
  errors?: string[];
}
