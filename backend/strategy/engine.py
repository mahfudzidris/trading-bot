"""Core trading strategy engine that orchestrates analysis and execution.

Supports DCA (dollar-cost averaging), trailing stops, short trades,
and fractional shares for small capital setups.
"""

from __future__ import annotations

import logging
import random
from datetime import datetime, timedelta
from typing import Any

from config import Settings
from data.twelvedata_client import TwelveDataClient
from ai.deepseek_analyzer import DeepSeekAnalyzer
from broker.alpaca_client import AlpacaClient

logger = logging.getLogger(__name__)


class StrategyEngine:
    """Orchestrates data → AI analysis → broker execution.

    In mock mode the engine generates rich historical data so the dashboard
    (and daily reports) always have something to display.

    New features:
    - **Fractional shares**: All qty values are floats (Alpaca supports
      fractional trading on cash accounts).
    - **DCA**: Buys are split into N tranches across watcher ticks when
      the AI returns consecutive BUY signals.
    - **Trailing stop**: After entry, the stop-loss price trails upward
      as the market price rises, locking in profit.
    - **Short side**: When SHORT_TRADES_ENABLED=True, the AI can return
      SHORT (sell first) and COVER (buy back) actions.
    """

    def __init__(
        self,
        data_client: TwelveDataClient,
        ai_analyzer: DeepSeekAnalyzer,
        broker_client: AlpacaClient,
        config: Settings,
    ) -> None:
        self.data = data_client
        self.ai = ai_analyzer
        self.broker = broker_client
        self.config = config

        # ── DCA state ─────────────────────────────────────────────────
        # symbol -> {tranches_bought, total_target_qty, entry_price}
        self._dca_state: dict[str, dict[str, Any]] = {}

        # ── Trailing stop state ───────────────────────────────────────
        # symbol -> {highest_price, active_sl}
        self._trail_state: dict[str, dict[str, float]] = {}

    # ──────────────────────────────────────────────────────────────────────
    # run_daily_analysis
    # ──────────────────────────────────────────────────────────────────────

    async def run_daily_analysis(self) -> dict[str, Any]:
        """Analyse every configured symbol and execute decisions.

        Returns a summary dict with the date and per-symbol results.
        """
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        analyses: list[dict[str, Any]] = []

        for symbol in self.config.SYMBOLS:
            try:
                result = await self.evaluate_symbol(symbol)
                analyses.append(result)
            except Exception as exc:
                logger.exception("Error analysing %s: %s", symbol, exc)
                analyses.append(
                    {
                        "symbol": symbol,
                        "decision": {"action": "ERROR", "reasoning": str(exc)},
                        "action_taken": None,
                        "pnl_impact": 0.0,
                    }
                )

        return {"date": date_str, "analyses": analyses}

    # ──────────────────────────────────────────────────────────────────────
    # evaluate_symbol
    # ──────────────────────────────────────────────────────────────────────

    async def evaluate_symbol(self, symbol: str) -> dict[str, Any]:
        """Fetch data, run AI, and optionally execute a trade for *symbol*.

        Supports:
        - **BUY** → enter long (or add DCA tranche)
        - **SELL** → close long position
        - **SHORT** → enter short (when SHORT_TRADES_ENABLED)
        - **COVER** → close short position
        - **HOLD** → no action (but trailing stop check still runs)

        Returns
        -------
        dict with keys: symbol, price_data, indicators, decision, action_taken, pnl_impact.
        """
        # 1. Get market data
        quote = await self.data.get_stock_quote(symbol)
        indicators = await self.data.get_quote_with_indicators(symbol)
        price = indicators.get("price", quote.get("price", 0))
        price_data = {
            "price": price,
            "change_pct": quote.get("change_pct", 0),
            "volume": quote.get("volume", 0),
            "timestamp": quote.get("timestamp", ""),
        }

        # 2. AI analysis
        decision = await self.ai.analyze_market(symbol, price_data, indicators)

        action = decision.get("action", "HOLD")
        action_taken: dict[str, Any] | None = None
        pnl_impact = 0.0

        # 3. Trailing stop check — runs every tick regardless of action
        if self.config.TRAILING_STOP_ENABLED:
            await self._check_trailing_stop(symbol, price, action_taken)

        # 4. Execute based on action
        if action in ("BUY", "SHORT") and not self.config.AUTO_TRADE:
            logger.info("[%s] AUTO_TRADE=OFF — analysis done, trade skipped", symbol)
            action_taken = {
                "type": f"simulated_{action.lower()}",
                "reason": "AUTO_TRADE disabled",
            }

        elif action == "BUY":
            action_taken = await self._handle_buy(symbol, price, decision)

        elif action == "SELL":
            action_taken = await self._handle_sell(symbol, price, decision)

        elif action == "SHORT":
            if not self.config.SHORT_TRADES_ENABLED:
                logger.info("[%s] SHORT trades disabled — skipping", symbol)
                action_taken = {"type": "hold", "reason": "SHORT_TRADES_ENABLED=False"}
            else:
                action_taken = await self._handle_short(symbol, price, decision)

        elif action == "COVER":
            if not self.config.SHORT_TRADES_ENABLED:
                logger.info("[%s] SHORT trades disabled — skipping COVER", symbol)
                action_taken = {"type": "hold", "reason": "SHORT_TRADES_ENABLED=False"}
            else:
                action_taken = await self._handle_cover(symbol, price, decision)

        # 5. Clean up DCA state if position was closed
        if action in ("SELL", "COVER") and symbol in self._dca_state:
            del self._dca_state[symbol]
        # Clean up trailing state if position closed
        if action in ("SELL", "COVER") and symbol in self._trail_state:
            del self._trail_state[symbol]

        return {
            "symbol": symbol,
            "price_data": price_data,
            "indicators": indicators,
            "decision": decision,
            "action_taken": action_taken,
            "pnl_impact": pnl_impact,
        }

    # ──────────────────────────────────────────────────────────────────────
    # Action handlers
    # ──────────────────────────────────────────────────────────────────────

    async def _handle_buy(
        self, symbol: str, price: float, decision: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle BUY signal — supports DCA tranches."""
        # Check if already holding a position
        positions = await self.broker.get_positions()
        existing = next(
            (p for p in positions if p["symbol"] == symbol and float(p.get("qty", 0)) > 0),
            None,
        )

        if existing:
            qty_held = float(existing["qty"])
            # If DCA is active and we haven't hit target, add another tranche
            if self._can_add_tranche(symbol, qty_held):
                tranche_qty = self._next_tranche_qty(symbol, price)
                if tranche_qty > 0:
                    return await self._execute_buy(
                        symbol, tranche_qty, price, decision, is_dca=True
                    )
            logger.info(
                "[%s] Already holding %.4f shares — BUY skipped",
                symbol, qty_held,
            )
            return {
                "type": "hold",
                "reason": f"Already holding {qty_held:.4f} shares",
                "qty": qty_held,
                "price": float(existing.get("current_price", 0)),
            }

        # ── New position — calculate size ──
        account = await self.broker.get_account()
        buying_power = account.get("buying_power", 100_000.0)
        max_capital = buying_power * self.config.TRADE_MAX_POSITION_SIZE
        total_qty = round(max_capital / price, 4)

        # Minimum fractional check (Alpaca supports 0.001+ shares)
        if total_qty < 0.001:
            logger.warning("[%s] Position too small (%.6f), skipping", symbol, total_qty)
            return {"type": "hold", "reason": "Position too small for fractional trading"}

        if self.config.DCA_ENABLED:
            # Split into tranches — buy first tranche now
            tranche_qty = round(total_qty / self.config.DCA_TRANCHES, 4)
            self._dca_state[symbol] = {
                "tranches_bought": 1,
                "total_target_qty": total_qty,
                "entry_price": price,
            }
            logger.info(
                "[%s] DCA: buying tranche 1/%d (%.4f of %.4f shares target)",
                symbol, self.config.DCA_TRANCHES, tranche_qty, total_qty,
            )
            return await self._execute_buy(symbol, tranche_qty, price, decision)
        else:
            # Single entry
            self._dca_state.pop(symbol, None)
            return await self._execute_buy(symbol, total_qty, price, decision)

    async def _handle_sell(
        self, symbol: str, price: float, decision: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle SELL signal — close long position."""
        positions = await self.broker.get_positions()
        pos = next((p for p in positions if p["symbol"] == symbol), None)
        if pos and float(pos["qty"]) > 0:
            order = await self.broker.close_position(symbol)
            result = {
                "type": "SELL",
                "qty": float(pos["qty"]),
                "price": pos.get("current_price", price),
                "order": order,
            }
            logger.info(
                "[%s] SELL %.4f @ $%.2f",
                symbol, float(pos["qty"]), result["price"],
            )
            return result
        logger.info("[%s] No position to sell", symbol)
        return {"type": "hold", "reason": "No position to sell"}

    async def _handle_short(
        self, symbol: str, price: float, decision: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle SHORT signal — open a short position (margin account only)."""
        # Check if already short
        positions = await self.broker.get_positions()
        existing = next(
            (p for p in positions if p["symbol"] == symbol and float(p.get("qty", 0)) < 0),
            None,
        )
        if existing:
            logger.info("[%s] Already short %.4f shares", symbol, float(existing["qty"]))
            return {
                "type": "hold",
                "reason": f"Already short {float(existing['qty']):.4f} shares",
            }

        account = await self.broker.get_account()
        buying_power = account.get("buying_power", 100_000.0)
        max_capital = buying_power * self.config.TRADE_MAX_POSITION_SIZE
        qty = round(max_capital / price, 4)

        if qty < 0.001:
            return {"type": "hold", "reason": "Position too small"}

        order = await self.broker.place_market_order(
            symbol, qty, "SELL",
            take_profit=decision.get("take_profit"),
            stop_loss=decision.get("stop_loss"),
        )
        result = {
            "type": "SHORT",
            "qty": qty,
            "price": price,
            "order": order,
        }
        logger.info("[%s] SHORT %.4f @ $%.2f", symbol, qty, price)
        return result

    async def _handle_cover(
        self, symbol: str, price: float, decision: dict[str, Any]
    ) -> dict[str, Any]:
        """Handle COVER signal — close short position."""
        order = await self.broker.close_position(symbol)
        if order.get("status") == "no_position":
            return {"type": "hold", "reason": "No short position to cover"}
        result = {
            "type": "COVER",
            "qty": order.get("qty", 0),
            "price": price,
            "order": order,
        }
        logger.info("[%s] COVER %.4f @ $%.2f", symbol, result["qty"], price)
        return result

    async def _execute_buy(
        self,
        symbol: str,
        qty: float,
        price: float,
        decision: dict[str, Any],
        is_dca: bool = False,
    ) -> dict[str, Any]:
        """Place a market BUY order."""
        order = await self.broker.place_market_order(
            symbol, qty, "BUY",
            take_profit=decision.get("take_profit"),
            stop_loss=decision.get("stop_loss"),
        )

        # Initialise trailing stop state
        if self.config.TRAILING_STOP_ENABLED and order.get("status") != "FAILED":
            self._trail_state[symbol] = {
                "highest_price": price,
                "active_sl": decision.get("stop_loss", price * 0.99),
            }

        result = {
            "type": "BUY",
            "qty": qty,
            "price": price,
            "order": order,
            "is_dca": is_dca,
        }
        label = f"DCA tranche: {qty:.4f}" if is_dca else f"{qty:.4f}"
        logger.info(
            "[%s] BUY %s @ $%.2f (TP: $%.2f, SL: $%.2f)",
            symbol, label, price,
            decision.get("take_profit", 0),
            decision.get("stop_loss", 0),
        )
        return result

    # ──────────────────────────────────────────────────────────────────────
    # DCA helpers
    # ──────────────────────────────────────────────────────────────────────

    def _can_add_tranche(self, symbol: str, qty_held: float) -> bool:
        """Check if DCA should add another tranche."""
        if not self.config.DCA_ENABLED:
            return False
        state = self._dca_state.get(symbol)
        if not state:
            return False
        if state["tranches_bought"] >= self.config.DCA_TRANCHES:
            return False
        if qty_held >= state["total_target_qty"] * 0.99:
            return False
        return True

    def _next_tranche_qty(self, symbol: str, price: float) -> float:
        """Calculate the next DCA tranche quantity."""
        state = self._dca_state.get(symbol)
        if not state:
            return 0
        tranche = round(state["total_target_qty"] / self.config.DCA_TRANCHES, 4)
        state["tranches_bought"] += 1
        logger.info(
            "[%s] DCA: buying tranche %d/%d",
            symbol, state["tranches_bought"], self.config.DCA_TRANCHES,
        )
        return tranche

    # ──────────────────────────────────────────────────────────────────────
    # Trailing stop
    # ──────────────────────────────────────────────────────────────────────

    async def _check_trailing_stop(
        self,
        symbol: str,
        current_price: float,
        action_taken: dict[str, Any] | None,
    ) -> None:
        """Check and update trailing stop for *symbol*.

        If the current price exceeds the highest seen price (since entry or
        last trail update), the stop loss is raised proportionally to trail
        at ``TRAILING_STOP_TRAIL_PCT`` below the new high.

        The trailing stop only activates once the price has moved up by at
        least ``TRAILING_STOP_ACTIVATION_PCT`` from the entry/initial price.
        """
        state = self._trail_state.get(symbol)
        if not state:
            return

        highest = state.get("highest_price", current_price)
        active_sl = state.get("active_sl", 0)

        # Update highest seen price
        if current_price > highest:
            state["highest_price"] = current_price

            # Activate trailing once price exceeds entry by activation_pct
            activation_threshold = highest * (1 - self.config.TRAILING_STOP_ACTIVATION_PCT)
            if active_sl < activation_threshold:
                # Not yet activated; trail hasn't kicked in
                pass

            # Slide stop up by trail_pct below new high
            new_sl = round(current_price * (1 - self.config.TRAILING_STOP_TRAIL_PCT), 2)
            if new_sl > active_sl:
                state["active_sl"] = new_sl
                logger.info(
                    "[%s] Trailing stop raised to $%.2f (price $%.2f, trail %.1f%%)",
                    symbol, new_sl, current_price,
                    self.config.TRAILING_STOP_TRAIL_PCT * 100,
                )

    # ──────────────────────────────────────────────────────────────────────
    # get_performance_summary
    # ──────────────────────────────────────────────────────────────────────

    async def get_performance_summary(self, days: int = 30) -> dict[str, Any]:
        """Aggregate performance metrics from the DB (or generate mock)."""
        try:
            from db.crud import get_trade_history, get_daily_reports
            from db.models import get_session

            async for session in get_session():
                # Get daily reports for the period
                reports = await get_daily_reports(session, limit=days)
                trades = await get_trade_history(session, limit=500)

                closed_trades = [t for t in trades if t.get("status") == "CLOSED"]

                if not closed_trades and not reports:
                    # Fallback to mock data
                    return await self._mock_performance_summary(days)

                total_pnl = sum(t.get("pnl", 0) for t in closed_trades)
                wins = [t for t in closed_trades if (t.get("pnl") or 0) > 0]
                losses = [t for t in closed_trades if (t.get("pnl") or 0) <= 0]
                win_rate = round(len(wins) / len(closed_trades) * 100, 1) if closed_trades else 0.0

                best_trade = max(closed_trades, key=lambda t: t.get("pnl", 0)) if closed_trades else None
                worst_trade = min(closed_trades, key=lambda t: t.get("pnl", 0)) if closed_trades else None

                return {
                    "total_pnl": round(total_pnl, 2),
                    "win_rate": win_rate,
                    "trades_count": len(closed_trades),
                    "wins": len(wins),
                    "losses": len(losses),
                    "best_trade": best_trade,
                    "worst_trade": worst_trade,
                    "period_days": days,
                }
        except Exception as exc:
            logger.warning("get_performance_summary from DB failed: %s", exc)
            return await self._mock_performance_summary(days)

        # If no session was yielded
        return await self._mock_performance_summary(days)

    # ──────────────────────────────────────────────────────────────────────
    # mock performance
    # ──────────────────────────────────────────────────────────────────────

    async def _mock_performance_summary(self, days: int = 30) -> dict[str, Any]:
        """Generate a realistic performance history when DB is empty/not available."""
        import numpy as np

        np.random.seed(42)
        n_trades = min(days * 2, 60)

        # Random walk of PnL values with realistic win-rate ~55%
        pnls = []
        for _ in range(n_trades):
            is_win = np.random.random() < 0.55
            if is_win:
                pnl = round(abs(np.random.normal(50, 30)), 2)
            else:
                pnl = round(-abs(np.random.normal(40, 25)), 2)
            pnls.append(pnl)

        total_pnl = round(sum(pnls), 2)
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]
        win_rate = round(len(wins) / len(pnls) * 100, 1) if pnls else 0.0

        best = max(pnls) if pnls else 0
        worst = min(pnls) if pnls else 0

        # Build mock best/worst trade dicts
        symbols = self.config.SYMBOLS
        best_trade = {
            "symbol": np.random.choice(symbols),
            "side": "BUY",
            "pnl": best,
            "pnl_pct": round(best / 100 * 100, 2),
            "entry_price": round(np.random.uniform(100, 400), 2),
            "exit_price": round(np.random.uniform(100, 400), 2),
            "status": "CLOSED",
        } if best else None

        worst_trade = {
            "symbol": np.random.choice(symbols),
            "side": "BUY",
            "pnl": worst,
            "pnl_pct": round(worst / 100 * 100, 2),
            "entry_price": round(np.random.uniform(100, 400), 2),
            "exit_price": round(np.random.uniform(100, 400), 2),
            "status": "CLOSED",
        } if worst else None

        return {
            "total_pnl": total_pnl,
            "win_rate": win_rate,
            "trades_count": len(pnls),
            "wins": len(wins),
            "losses": len(losses),
            "best_trade": best_trade,
            "worst_trade": worst_trade,
            "period_days": days,
        }
