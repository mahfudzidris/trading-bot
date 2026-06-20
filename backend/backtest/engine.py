"""Comprehensive backtesting engine that simulates strategy performance.

Supports:
- Historical OHLCV data (mock or real TwelveData)
- AI-powered decision making via DeepSeek (or mock logic)
- TP/SL simulation
- Detailed performance metrics: CAGR, Sharpe, Sortino, Max DD, Calmar, Profit Factor
- Full trade log with every entry/exit
- Equity curve snapshots
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import random
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, date as date_type
from typing import Any, Callable

import numpy as np

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Data Structures
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class BacktestTrade:
    """A single simulated trade during a backtest."""

    symbol: str
    side: str  # BUY / SELL
    qty: int
    entry_price: float
    entry_time: str
    exit_price: float | None = None
    exit_time: str | None = None
    pnl: float = 0.0
    pnl_pct: float = 0.0
    status: str = "OPEN"
    stop_loss: float = 0.0
    take_profit: float = 0.0
    strategy: str = ""
    ai_reasoning: str = ""
    ai_confidence: int = 0
    exit_reason: str = ""  # TP_HIT / SL_HIT / SIGNAL / MANUAL


@dataclass
class EquitySnapshot:
    """Portfolio equity value at a point in time."""

    date: str
    cash: float
    holdings_value: float
    total_equity: float
    daily_pnl: float = 0.0


@dataclass
class BacktestResult:
    """Full backtest result with metrics and history."""

    # Parameters
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float
    days: int

    # Performance Metrics
    total_pnl: float = 0.0
    total_pnl_pct: float = 0.0
    final_capital: float = 0.0
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    best_trade: float = 0.0
    worst_trade: float = 0.0
    avg_trade: float = 0.0
    profit_factor: float = 0.0
    expectancy: float = 0.0

    # Risk Metrics
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    cagr: float = 0.0
    volatility: float = 0.0
    return_std: float = 0.0

    # Trade Distribution
    avg_bars_held: float = 0.0
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0

    # Detailed Data
    trades: list[dict[str, Any]] = field(default_factory=list)
    equity_curve: list[dict[str, Any]] = field(default_factory=list)
    monthly_returns: dict[str, float] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def summary_table(self) -> dict[str, Any]:
        """Return a compact summary for display."""
        return {
            "symbol": self.symbol,
            "period": f"{self.start_date} → {self.end_date} ({self.days} days)",
            "initial_capital": self.initial_capital,
            "final_capital": round(self.final_capital, 2),
            "total_pnl": round(self.total_pnl, 2),
            "total_pnl_pct": round(self.total_pnl_pct, 2),
            "total_trades": self.total_trades,
            "win_rate": round(self.win_rate, 1),
            "profit_factor": round(self.profit_factor, 2),
            "max_drawdown_pct": round(self.max_drawdown_pct, 2),
            "sharpe_ratio": round(self.sharpe_ratio, 2),
            "sortino_ratio": round(self.sortino_ratio, 2),
            "cagr": round(self.cagr, 2),
            "calmar_ratio": round(self.calmar_ratio, 2),
            "avg_trade": round(self.avg_trade, 2),
            "best_trade": round(self.best_trade, 2),
            "worst_trade": round(self.worst_trade, 2),
        }


# ─────────────────────────────────────────────────────────────────────────────
# BacktestEngine
# ─────────────────────────────────────────────────────────────────────────────


class BacktestEngine:
    """Simulates trading a strategy over historical price data.

    Parameters
    ----------
    data_client : TwelveDataClient
        Used to fetch historical time-series data.
    ai_analyzer : DeepSeekAnalyzer
        Provides AI-driven BUY/SELL/HOLD decisions.
    initial_capital : float
        Starting account balance (default 100_000).
    commission_pct : float
        Per-trade commission as a fraction (default 0.001 = 0.1%).
    slippage_pct : float
        Slippage on entry/exit price as a fraction (default 0.001).
    """

    def __init__(
        self,
        data_client: Any,
        ai_analyzer: Any,
        initial_capital: float = 100_000.0,
        commission_pct: float = 0.001,
        slippage_pct: float = 0.001,
    ) -> None:
        self.data = data_client
        self.ai = ai_analyzer
        self.initial_capital = initial_capital
        self.commission_pct = commission_pct
        self.slippage_pct = slippage_pct

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    async def run(
        self,
        symbol: str,
        start_date: str,
        end_date: str | None = None,
        strategy_params: dict[str, Any] | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> BacktestResult:
        """Run a full backtest for *symbol* over the date range.

        Parameters
        ----------
        symbol : str
            Ticker symbol (e.g. "AAPL").
        start_date : str
            Start date in "YYYY-MM-DD" format.
        end_date : str | None
            End date in "YYYY-MM-DD" format. Defaults to today.
        strategy_params : dict | None
            Override default strategy parameters.
        progress_callback : callable | None
            Called with (current_day, total_days) for progress tracking.

        Returns
        -------
        BacktestResult with all performance metrics and trade history.
        """
        symbol = symbol.upper()
        end_date = end_date or datetime.utcnow().strftime("%Y-%m-%d")

        params = {
            "stop_loss_pct": 0.02,
            "take_profit_pct": 0.05,
            "max_position_size_pct": 0.1,
            "min_rsi_buy": 35,
            "max_rsi_sell": 65,
            "use_ai": True,
        }
        if strategy_params:
            params.update(strategy_params)

        # 1. Fetch historical data
        bars = await self._fetch_historical_data(symbol, start_date, end_date)
        if not bars:
            return BacktestResult(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                initial_capital=self.initial_capital,
                days=0,
                errors=["No historical data available for backtest"],
            )

        # 2. Convert bars to numpy arrays for vectorised computation
        closes = np.array([b["close"] for b in bars], dtype=np.float64)
        highs = np.array([b["high"] for b in bars], dtype=np.float64)
        lows = np.array([b["low"] for b in bars], dtype=np.float64)
        opens = np.array([b["open"] for b in bars], dtype=np.float64)
        volumes = np.array([b["volume"] for b in bars], dtype=np.float64)
        dates = [b["datetime"] for b in bars]

        n = len(bars)
        days_traded = n

        # 3. Compute rolling indicators
        sma_20 = self._rolling_mean(closes, 20)
        sma_50 = self._rolling_mean(closes, 50)
        ema_12 = self._ema(closes, 12)
        ema_26 = self._ema(closes, 26)
        rsi_values = self._rsi_array(closes, 14)

        # 4. Simulate walking through time
        cash = self.initial_capital
        position_qty = 0
        position_entry_price = 0.0
        position_entry_day = 0
        position_side = ""  # BUY or SELL
        entry_reasoning = ""
        entry_confidence = 0

        trades: list[BacktestTrade] = []
        equity_curve: list[EquitySnapshot] = []
        consecutive_wins = 0
        consecutive_losses = 0
        max_cons_wins = 0
        max_cons_losses = 0
        monthly_pnls: dict[str, list[float]] = {}
        daily_returns: list[float] = []
        errors: list[str] = []

        total_days = n
        prev_equity = self.initial_capital

        for i in range(n):
            if progress_callback:
                progress_callback(i + 1, total_days)

            current_price = closes[i]
            current_high = highs[i]
            current_low = lows[i]
            current_date = dates[i]

            # --- Check for stop-loss / take-profit on open position ---
            if position_qty != 0:
                exit_reason, exit_price = self._check_exit_conditions(
                    position_side=position_side,
                    entry_price=position_entry_price,
                    current_high=current_high,
                    current_low=current_low,
                    current_close=current_price,
                    stop_loss_pct=params["stop_loss_pct"],
                    take_profit_pct=params["take_profit_pct"],
                )
                if exit_reason:
                    # Close position
                    slippage = exit_price * self.slippage_pct
                    fill_price = exit_price - slippage if position_side == "BUY" else exit_price + slippage
                    commission = fill_price * position_qty * self.commission_pct

                    if position_side == "BUY":
                        pnl = (fill_price - position_entry_price) * position_qty - commission
                    else:
                        pnl = (position_entry_price - fill_price) * position_qty - commission

                    pnl_pct = (
                        (fill_price / position_entry_price - 1) * 100
                        if position_entry_price > 0
                        else 0.0
                    )

                    trade = BacktestTrade(
                        symbol=symbol,
                        side=position_side,
                        qty=position_qty,
                        entry_price=position_entry_price,
                        entry_time=dates[position_entry_day],
                        exit_price=fill_price,
                        exit_time=current_date,
                        pnl=round(pnl, 2),
                        pnl_pct=round(pnl_pct, 2),
                        status="CLOSED",
                        stop_loss=round(position_entry_price * (1 - params["stop_loss_pct"]), 2)
                        if position_side == "BUY"
                        else round(position_entry_price * (1 + params["stop_loss_pct"]), 2),
                        take_profit=round(position_entry_price * (1 + params["take_profit_pct"]), 2)
                        if position_side == "BUY"
                        else round(position_entry_price * (1 - params["take_profit_pct"]), 2),
                        strategy=f"AI_backtest_{'TP' if 'TP' in exit_reason else 'SL' if 'SL' in exit_reason else 'signal'}",
                        ai_reasoning=entry_reasoning,
                        ai_confidence=entry_confidence,
                        exit_reason=exit_reason,
                    )
                    trades.append(trade)
                    cash += pnl + (position_qty * fill_price - commission)

                    if pnl > 0:
                        consecutive_wins += 1
                        consecutive_losses = 0
                        max_cons_wins = max(max_cons_wins, consecutive_wins)
                    else:
                        consecutive_losses += 1
                        consecutive_wins = 0
                        max_cons_losses = max(max_cons_losses, consecutive_losses)

                    position_qty = 0
                    position_entry_price = 0.0
                    position_side = ""
                    entry_reasoning = ""
                    entry_confidence = 0

            # --- Generate trading signal for today ---
            if i < 20:  # Need warmup for indicators
                holdings_value = position_qty * current_price
                total_equity = cash + holdings_value
                daily_return = (total_equity / prev_equity - 1) if prev_equity > 0 else 0
                prev_equity = total_equity
                if i > 0:
                    daily_returns.append(daily_return)

                equity_curve.append(
                    EquitySnapshot(
                        date=current_date,
                        cash=round(cash, 2),
                        holdings_value=round(holdings_value, 2),
                        total_equity=round(total_equity, 2),
                        daily_pnl=round(holdings_value * 0, 2),
                    )
                )
                continue

            # Build indicators dict for the AI
            indicators = {
                "price": current_price,
                "sma_20": float(sma_20[i]) if not np.isnan(sma_20[i]) else current_price,
                "sma_50": float(sma_50[i]) if not np.isnan(sma_50[i]) else current_price,
                "ema_12": float(ema_12[i]) if not np.isnan(ema_12[i]) else current_price,
                "ema_26": float(ema_26[i]) if not np.isnan(ema_26[i]) else current_price,
                "rsi_14": float(rsi_values[i]) if not np.isnan(rsi_values[i]) else 50.0,
                "volume": int(volumes[i]) if not np.isnan(volumes[i]) else 0,
            }

            price_data = {
                "price": current_price,
                "change_pct": round((closes[i] / closes[i - 1] - 1) * 100, 2) if i > 0 else 0.0,
                "volume": int(volumes[i]),
                "timestamp": current_date,
            }

            # Get AI decision
            try:
                if params["use_ai"]:
                    decision = await self.ai.analyze_market(symbol, price_data, indicators)
                else:
                    decision = self._rule_based_decision(indicators, params)

                action = decision.get("action", "HOLD")
                confidence = decision.get("confidence", 50)
                reasoning = decision.get("reasoning", "")
                tp_price = decision.get("take_profit", 0)
                sl_price = decision.get("stop_loss", 0)

            except Exception as exc:
                logger.warning("AI decision failed for %s on %s: %s", symbol, current_date, exc)
                errors.append(f"AI error on {current_date}: {exc}")
                action = "HOLD"
                confidence = 0
                reasoning = "AI error fallback"
                tp_price = 0
                sl_price = 0

            # --- Execute signals ---
            if action == "BUY" and position_qty == 0 and cash > current_price:
                # Calculate position size
                max_capital = cash * params["max_position_size_pct"]
                qty = max(1, int(max_capital / current_price))
                if qty > 0:
                    slippage = current_price * self.slippage_pct
                    fill_price = current_price + slippage
                    commission = fill_price * qty * self.commission_pct
                    cost = fill_price * qty + commission

                    if cost <= cash:
                        position_qty = qty
                        position_entry_price = fill_price
                        position_entry_day = i
                        position_side = "BUY"
                        entry_reasoning = reasoning
                        entry_confidence = confidence
                        cash -= cost

            elif action == "SELL" and position_qty > 0:
                # Close via signal
                slippage = current_price * self.slippage_pct
                fill_price = current_price - slippage
                commission = fill_price * position_qty * self.commission_pct

                pnl = (fill_price - position_entry_price) * position_qty - commission
                pnl_pct = round((fill_price / position_entry_price - 1) * 100, 2)

                trade = BacktestTrade(
                    symbol=symbol,
                    side=position_side,
                    qty=position_qty,
                    entry_price=position_entry_price,
                    entry_time=dates[position_entry_day],
                    exit_price=fill_price,
                    exit_time=current_date,
                    pnl=round(pnl, 2),
                    pnl_pct=pnl_pct,
                    status="CLOSED",
                    stop_loss=round(position_entry_price * (1 - params["stop_loss_pct"]), 2),
                    take_profit=round(position_entry_price * (1 + params["take_profit_pct"]), 2),
                    strategy=f"AI_backtest_signal",
                    ai_reasoning=reasoning,
                    ai_confidence=confidence,
                    exit_reason="SIGNAL",
                )
                trades.append(trade)
                cash += pnl + (position_qty * fill_price - commission)

                if pnl > 0:
                    consecutive_wins += 1
                    consecutive_losses = 0
                    max_cons_wins = max(max_cons_wins, consecutive_wins)
                else:
                    consecutive_losses += 1
                    consecutive_wins = 0
                    max_cons_losses = max(max_cons_losses, consecutive_losses)

                position_qty = 0
                position_entry_price = 0.0
                position_side = ""
                entry_reasoning = ""
                entry_confidence = 0

            # --- Record equity snapshot ---
            holdings_value = position_qty * current_price
            total_equity = cash + holdings_value
            daily_return = (total_equity / prev_equity - 1) if prev_equity > 0 else 0
            prev_equity = total_equity
            daily_returns.append(daily_return)

            # Track monthly PnL
            month_key = current_date[:7]  # "YYYY-MM"
            if month_key not in monthly_pnls:
                monthly_pnls[month_key] = []
            monthly_pnls[month_key].append(daily_return)

            equity_curve.append(
                EquitySnapshot(
                    date=current_date,
                    cash=round(cash, 2),
                    holdings_value=round(holdings_value, 2),
                    total_equity=round(total_equity, 2),
                    daily_pnl=round(total_equity - (equity_curve[-1].total_equity if equity_curve else self.initial_capital), 2),
                )
            )

        # --- Close any open position at the end ---
        if position_qty != 0 and closes.size > 0:
            final_price = closes[-1]
            slippage = final_price * self.slippage_pct
            fill_price = final_price - slippage if position_side == "BUY" else final_price + slippage
            commission = fill_price * position_qty * self.commission_pct

            if position_side == "BUY":
                pnl = (fill_price - position_entry_price) * position_qty - commission
            else:
                pnl = (position_entry_price - fill_price) * position_qty - commission

            trade = BacktestTrade(
                symbol=symbol,
                side=position_side,
                qty=position_qty,
                entry_price=position_entry_price,
                entry_time=dates[position_entry_day],
                exit_price=fill_price,
                exit_time=dates[-1],
                pnl=round(pnl, 2),
                pnl_pct=round((fill_price / position_entry_price - 1) * 100, 2),
                status="CLOSED",
                stop_loss=round(position_entry_price * (1 - 0.02), 2),
                take_profit=round(position_entry_price * (1 + 0.05), 2),
                strategy="AI_backtest_end",
                ai_reasoning="Position closed at end of backtest period",
                ai_confidence=0,
                exit_reason="END_OF_PERIOD",
            )
            trades.append(trade)
            cash += pnl + (position_qty * fill_price - commission)
            position_qty = 0

        # ──────────────────────────────────────────────────────────────────────
        # Compute performance metrics
        # ──────────────────────────────────────────────────────────────────────
        final_capital = cash
        result = BacktestResult(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            days=days_traded,
            final_capital=round(final_capital, 2),
            total_pnl=round(final_capital - self.initial_capital, 2),
            total_pnl_pct=round(
                (final_capital / self.initial_capital - 1) * 100, 2
            ),
            total_trades=len(trades),
            max_consecutive_wins=max_cons_wins,
            max_consecutive_losses=max_cons_losses,
            errors=errors,
        )

        if not trades:
            return result

        # Win/Loss analysis
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl <= 0]
        result.wins = len(winning_trades)
        result.losses = len(losing_trades)
        result.win_rate = (result.wins / result.total_trades * 100) if result.total_trades > 0 else 0.0

        result.avg_win = float(np.mean([t.pnl for t in winning_trades])) if winning_trades else 0.0
        result.avg_loss = float(np.mean([t.pnl for t in losing_trades])) if losing_trades else 0.0
        result.best_trade = max(t.pnl for t in trades)
        result.worst_trade = min(t.pnl for t in trades)
        result.avg_trade = float(np.mean([t.pnl for t in trades]))

        # Profit Factor
        gross_profit = sum(t.pnl for t in winning_trades)
        gross_loss = abs(sum(t.pnl for t in losing_trades))
        result.profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else float("inf")

        # Expectancy
        result.expectancy = round(
            (result.win_rate / 100 * result.avg_win)
            - ((1 - result.win_rate / 100) * abs(result.avg_loss)),
            2,
        )

        # Avg bars held
        if trades:
            held_days = []
            for t in trades:
                try:
                    e_dt = datetime.strptime(t.entry_time, "%Y-%m-%d")
                    x_dt = datetime.strptime(t.exit_time or end_date, "%Y-%m-%d")
                    held_days.append((x_dt - e_dt).days)
                except (ValueError, TypeError):
                    pass
            result.avg_bars_held = round(float(np.mean(held_days)), 1) if held_days else 0.0

        # Compute from equity curve
        equity_values = np.array([e.total_equity for e in equity_curve], dtype=np.float64)
        daily_ret_array = np.array(daily_returns, dtype=np.float64)

        # Max Drawdown
        if len(equity_values) > 0:
            peak = np.maximum.accumulate(equity_values)
            drawdown = equity_values - peak
            drawdown_pct = drawdown / peak * 100
            result.max_drawdown = round(float(np.min(drawdown)), 2)
            result.max_drawdown_pct = round(float(np.min(drawdown_pct)), 2)

        # CAGR
        if len(equity_values) > 1 and days_traded > 0:
            years = days_traded / 365.0
            if years > 0 and equity_values[0] > 0:
                cagr = (equity_values[-1] / equity_values[0]) ** (1 / years) - 1
                result.cagr = round(cagr * 100, 2)

        # Volatility (annualised)
        if len(daily_ret_array) > 1:
            result.volatility = round(float(np.std(daily_ret_array) * np.sqrt(252) * 100), 2)

        # Sharpe Ratio (risk-free = 2% annual / 252)
        if len(daily_ret_array) > 1 and np.std(daily_ret_array) > 0:
            excess_returns = daily_ret_array - 0.02 / 252
            sharpe = np.mean(excess_returns) / np.std(daily_ret_array) * np.sqrt(252)
            result.sharpe_ratio = round(float(sharpe), 2)

        # Sortino Ratio (downside deviation)
        if len(daily_ret_array) > 1:
            downside = daily_ret_array[daily_ret_array < 0]
            if len(downside) > 0 and np.std(downside) > 0:
                sortino = (np.mean(daily_ret_array) - 0.02 / 252) / np.std(downside) * np.sqrt(252)
                result.sortino_ratio = round(float(sortino), 2)

        # Calmar Ratio
        if result.max_drawdown_pct != 0:
            result.calmar_ratio = round(result.cagr / abs(result.max_drawdown_pct), 2) if abs(result.max_drawdown_pct) > 0 else 0.0

        # Monthly returns
        monthly_agg = {}
        for month, rets in monthly_pnls.items():
            compound_return = 1.0
            for r in rets:
                compound_return *= 1 + r if not np.isnan(r) else 1.0
            monthly_agg[month] = round((compound_return - 1) * 100, 2)
        result.monthly_returns = monthly_agg

        # Serialise trade & equity data
        result.trades = [asdict(t) for t in trades]
        result.equity_curve = [asdict(e) for e in equity_curve]

        return result

    # ──────────────────────────────────────────────────────────────────────────
    # Internal Helpers
    # ──────────────────────────────────────────────────────────────────────────

    async def _fetch_historical_data(
        self, symbol: str, start_date: str, end_date: str
    ) -> list[dict[str, Any]]:
        """Fetch OHLCV bars from the data client."""
        try:
            # Parse dates, compute days needed from the start
            s_dt = datetime.strptime(start_date, "%Y-%m-%d")
            e_dt = datetime.strptime(end_date, "%Y-%m-%d")
            today = datetime.utcnow()

            # We need enough bars to cover start_date to today
            # (mock mode generates recent bars)
            days_from_start = (today - s_dt).days + 60  # buffer
            outputsize = max(days_from_start, 100)

            series = await self.data.get_time_series(
                symbol, interval="1day", outputsize=outputsize
            )

            if not series:
                logger.warning("No time series data for %s", symbol)
                return []

            # Filter to requested range
            filtered = []
            for bar in series:
                bar_date = bar.get("datetime", "")
                if start_date <= bar_date <= end_date:
                    filtered.append(bar)

            # If still empty in mock mode, generate bars for the exact range
            if not filtered and self.data.mock_mode:
                filtered = self._generate_bars_for_range(symbol, s_dt, e_dt)

            return filtered

        except Exception as exc:
            logger.error("Failed to fetch historical data: %s", exc)
            return []

    def _generate_bars_for_range(
        self, symbol: str, s_dt: datetime, e_dt: datetime
    ) -> list[dict[str, Any]]:
        """Generate mock OHLCV bars for the exact date range (mock-mode fallback)."""
        days = (e_dt - s_dt).days
        if days < 1:
            return []

        base = self.data._base_price(symbol)
        np.random.seed(hash(symbol + str(s_dt)) % (2**31))
        volatility = 0.02
        drift = 0.0003
        returns = np.random.normal(drift, volatility, days)
        prices = base * np.exp(np.cumsum(returns))

        bars = []
        for i in range(days):
            dt = s_dt + timedelta(days=i)
            # Skip weekends
            if dt.weekday() >= 5:
                continue
            c = float(prices[i])
            daily_range = c * 0.02
            o = round(c - daily_range + random.uniform(0, daily_range * 2), 2)
            h = round(max(o, c) + random.uniform(0, daily_range * 0.5), 2)
            l_ = round(min(o, c) - random.uniform(0, daily_range * 0.5), 2)
            bars.append({
                "datetime": dt.strftime("%Y-%m-%d"),
                "open": o,
                "high": h,
                "low": l_,
                "close": c,
                "volume": random.randint(500_000, 25_000_000),
            })
        return bars

    @staticmethod
    def _rolling_mean(arr: np.ndarray, period: int) -> np.ndarray:
        """Compute rolling (simple) mean, returning NaN for incomplete windows."""
        result = np.full_like(arr, np.nan, dtype=np.float64)
        if len(arr) < period:
            return result
        cumsum = np.cumsum(arr, dtype=np.float64)
        result[period - 1:] = (cumsum[period - 1:] - np.concatenate([[0], cumsum[:-period]])) / period
        return result

    @staticmethod
    def _ema(arr: np.ndarray, period: int) -> np.ndarray:
        """Exponential Moving Average."""
        result = np.full_like(arr, np.nan, dtype=np.float64)
        if len(arr) < period:
            return result
        alpha = 2.0 / (period + 1)
        result[period - 1] = float(np.mean(arr[:period]))
        for i in range(period, len(arr)):
            result[i] = alpha * arr[i] + (1 - alpha) * result[i - 1]
        return result

    @staticmethod
    def _rsi_array(prices: np.ndarray, period: int = 14) -> np.ndarray:
        """Compute RSI for each point in the price array."""
        result = np.full_like(prices, np.nan, dtype=np.float64)
        if len(prices) < period + 1:
            return result

        deltas = np.diff(prices)
        for i in range(period, len(prices)):
            window = deltas[i - period : i]
            gains = window[window > 0].sum() if window[window > 0].size > 0 else 0
            losses = -window[window < 0].sum() if window[window < 0].size > 0 else 0
            avg_gain = gains / period
            avg_loss = losses / period
            if avg_loss == 0:
                result[i] = 100.0
            else:
                rs = avg_gain / avg_loss
                result[i] = 100.0 - 100.0 / (1.0 + rs)
        return result

    @staticmethod
    def _check_exit_conditions(
        position_side: str,
        entry_price: float,
        current_high: float,
        current_low: float,
        current_close: float,
        stop_loss_pct: float,
        take_profit_pct: float,
    ) -> tuple[str, float]:
        """Check whether TP or SL has been hit.

        Returns (exit_reason, fill_price) or ("", 0.0) if no exit.
        """
        if position_side == "BUY":
            tp_price = entry_price * (1 + take_profit_pct)
            sl_price = entry_price * (1 - stop_loss_pct)
            if current_high >= tp_price:
                return "TP_HIT", tp_price
            if current_low <= sl_price:
                return "SL_HIT", sl_price
        else:  # SELL
            tp_price = entry_price * (1 - take_profit_pct)
            sl_price = entry_price * (1 + stop_loss_pct)
            if current_low <= tp_price:
                return "TP_HIT", tp_price
            if current_high >= sl_price:
                return "SL_HIT", sl_price
        return ("", 0.0)

    @staticmethod
    def _rule_based_decision(
        indicators: dict[str, Any], params: dict[str, Any]
    ) -> dict[str, Any]:
        """Simple rule-based fallback when AI is disabled."""
        price = indicators.get("price", 100)
        rsi = indicators.get("rsi_14", 50)
        sma_20 = indicators.get("sma_20", price)
        sma_50 = indicators.get("sma_50", price)
        ema_12 = indicators.get("ema_12", price)
        ema_26 = indicators.get("ema_26", price)

        action = "HOLD"
        confidence = 50
        reasoning_parts = []

        # RSI oversold
        if rsi < params.get("min_rsi_buy", 35):
            action = "BUY"
            confidence = 70
            reasoning_parts.append(f"RSI {rsi:.1f} oversold")
        elif rsi > params.get("max_rsi_sell", 65):
            action = "SELL"
            confidence = 70
            reasoning_parts.append(f"RSI {rsi:.1f} overbought")

        # MA cross
        if ema_12 > ema_26 and price > sma_20 and action != "HOLD":
            confidence += 10
            reasoning_parts.append("Bullish MA alignment")
        elif ema_12 < ema_26 and price < sma_20 and action != "HOLD":
            confidence += 10
            reasoning_parts.append("Bearish MA alignment")

        # Golden cross
        if sma_20 > sma_50 and action != "SELL":
            if action == "HOLD":
                action = "BUY"
                confidence = 65
            reasoning_parts.append("Golden cross (20>50 SMA)")

        # Death cross
        if sma_20 < sma_50 and action != "BUY":
            if action == "HOLD":
                action = "SELL"
                confidence = 65
            reasoning_parts.append("Death cross (20<50 SMA)")

        confidence = max(0, min(100, confidence))
        price_pct = params.get("take_profit_pct", 0.05)

        return {
            "action": action,
            "confidence": confidence,
            "reasoning": "; ".join(reasoning_parts) if reasoning_parts else "No clear signals",
            "take_profit": round(price * (1 + price_pct), 2) if action == "BUY" else 0.0,
            "stop_loss": round(price * (1 - 0.02), 2) if action != "HOLD" else 0.0,
            "position_size_pct": params.get("max_position_size_pct", 0.1) if action != "HOLD" else 0.0,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Convenience wrapper
# ─────────────────────────────────────────────────────────────────────────────


async def run_backtest(
    data_client: Any,
    ai_analyzer: Any,
    symbol: str,
    start_date: str,
    end_date: str | None = None,
    initial_capital: float = 100_000.0,
    strategy_params: dict[str, Any] | None = None,
    commission_pct: float = 0.001,
    slippage_pct: float = 0.001,
) -> BacktestResult:
    """One-shot convenience function to run a backtest."""
    engine = BacktestEngine(
        data_client=data_client,
        ai_analyzer=ai_analyzer,
        initial_capital=initial_capital,
        commission_pct=commission_pct,
        slippage_pct=slippage_pct,
    )
    result = await engine.run(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        strategy_params=strategy_params,
    )
    return result
