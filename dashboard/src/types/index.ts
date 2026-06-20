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
