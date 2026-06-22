"""Alpaca Broker client with full mock-mode simulation."""

from __future__ import annotations

import logging
import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)

try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, StopOrderRequest, TakeProfitRequest, StopLossRequest
    from alpaca.trading.enums import OrderSide, TimeInForce
    from alpaca.data import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False


class AlpacaClient:
    """Client for the Alpaca Markets brokerage API.

    In *mock_mode* all operations are simulated with realistic responses so
    the system can be developed and tested without a live account.
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        paper: bool = True,
        mock_mode: bool = True,
    ) -> None:
        self.api_key = api_key
        self.secret_key = secret_key
        self.paper = paper
        self.mock_mode = mock_mode

        # Internal state for mock mode
        self._mock_account: dict[str, Any] | None = None
        self._mock_positions: dict[str, dict[str, Any]] = {}
        self._mock_orders: list[dict[str, Any]] = []
        self._mock_base_prices: dict[str, float] = {
            "SPY": 570.0,
        }

        if not mock_mode and ALPACA_AVAILABLE:
            self._trade_client = TradingClient(api_key, secret_key, paper=paper)
            self._data_client = StockHistoricalDataClient(api_key, secret_key)
        else:
            self._trade_client = None
            self._data_client = None
            self._init_mock_state()

    # ──────────────────────────────────────────────────────────────────────
    # mock state initialisation
    # ──────────────────────────────────────────────────────────────────────

    def _init_mock_state(self) -> None:
        """Seed plausible mock account and positions."""
        self._mock_account = {
            "account_number": "MOCK123456",
            "status": "ACTIVE",
            "currency": "USD",
            "cash": 100_000.00,
            "portfolio_value": 150_000.00,
            "buying_power": 200_000.00,
            "long_market_value": 50_000.00,
            "short_market_value": 0.0,
            "equity": 150_000.00,
            "last_equity": 145_000.00,
            "multiplier": 2,
            "pattern_day_trader": False,
            "trading_blocked": False,
            "transfers_blocked": False,
            "account_blocked": False,
            "created_at": (datetime.utcnow() - timedelta(days=90)).isoformat(),
            "shorting_enabled": True,
            "day_trade_count": 0,
            "sma": 25_000.0,
        }
        # Seed a couple of positions
        for sym, price in self._mock_base_prices.items():
            if random.random() < 0.4:
                qty = random.randint(5, 50)
                entry = price * (1 - random.uniform(-0.05, 0.05))
                self._mock_positions[sym] = {
                    "symbol": sym,
                    "qty": qty,
                    "avg_entry_price": round(entry, 2),
                    "current_price": price,
                    "market_value": round(qty * price, 2),
                    "unrealized_pl": round(qty * (price - entry), 2),
                    "unrealized_pl_pct": round((price / entry - 1) * 100, 2),
                    "cost_basis": round(qty * entry, 2),
                }

    # ──────────────────────────────────────────────────────────────────────
    # get_account
    # ──────────────────────────────────────────────────────────────────────

    async def get_account(self) -> dict[str, Any]:
        if self.mock_mode:
            # Simulate small daily P&L changes
            if self._mock_account is None:
                self._init_mock_state()
            acct = self._mock_account  # type: ignore[union-attr]
            pnl = round(acct["equity"] - acct["last_equity"], 2)
            return {
                "balance": acct["equity"],
                "cash": acct["cash"],
                "buying_power": acct["buying_power"],
                "pnl": pnl,
                "portfolio_value": acct["portfolio_value"],
                "status": acct["status"],
            }
        try:
            acct = self._trade_client.get_account()
            return {
                "balance": float(acct.equity),
                "cash": float(acct.cash),
                "buying_power": float(acct.buying_power),
                "pnl": float(acct.equity) - float(acct.last_equity),
                "portfolio_value": float(acct.portfolio_value),
                "status": acct.status,
            }
        except Exception as exc:
            logger.error("get_account failed: %s", exc)
            return {"balance": 0, "cash": 0, "buying_power": 0, "pnl": 0, "portfolio_value": 0, "status": "ERROR"}

    # ──────────────────────────────────────────────────────────────────────
    # get_positions
    # ──────────────────────────────────────────────────────────────────────

    async def get_positions(self) -> list[dict[str, Any]]:
        if self.mock_mode:
            return list(self._mock_positions.values())
        try:
            positions = self._trade_client.get_all_positions()
            result = []
            for p in positions:
                result.append(
                    {
                        "symbol": p.symbol,
                        "qty": int(p.qty),
                        "market_value": float(p.market_value),
                        "unrealized_pl": float(p.unrealized_pl),
                        "unrealized_pl_pct": float(p.unrealized_plpc),
                        "avg_entry_price": float(p.avg_entry_price),
                        "cost_basis": float(p.cost_basis),
                        "current_price": float(p.current_price),
                    }
                )
            return result
        except Exception as exc:
            logger.error("get_positions failed: %s", exc)
            return []

    # ──────────────────────────────────────────────────────────────────────
    # place_market_order
    # ──────────────────────────────────────────────────────────────────────

    async def place_market_order(
        self, symbol: str, qty: int, side: str,
        take_profit: float | None = None,
        stop_loss: float | None = None,
    ) -> dict[str, Any]:
        if self.mock_mode:
            price = self._mock_base_prices.get(symbol.upper(), 100.0)
            order = {
                "id": f"mock-{random.randint(10000, 99999)}",
                "symbol": symbol.upper(),
                "qty": qty,
                "side": side,
                "type": "market",
                "status": "filled",
                "filled_avg_price": price,
                "filled_qty": qty,
                "created_at": datetime.utcnow().isoformat(),
                "filled_at": datetime.utcnow().isoformat(),
                "take_profit": take_profit,
                "stop_loss": stop_loss,
            }
            self._mock_orders.append(order)
            self._update_mock_position(symbol.upper(), qty, side, price)
            return order
        try:
            order_side = OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL
            req = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=order_side,
                time_in_force=TimeInForce.DAY,
            )
            # Attach bracket order (TP/SL) if prices provided
            if take_profit or stop_loss:
                req.order_class = "bracket"
            if take_profit:
                req.take_profit = TakeProfitRequest(limit_price=take_profit)
            if stop_loss:
                import alpaca.trading.requests as _atr
                req.stop_loss = StopLossRequest(stop_price=stop_loss)

            order = self._trade_client.submit_order(req)
            return {
                "id": order.id,
                "symbol": order.symbol,
                "qty": int(order.qty),
                "side": order.side.value,
                "type": order.type.value,
                "status": order.status,
                "filled_avg_price": float(order.filled_avg_price) if order.filled_avg_price else 0,
                "filled_qty": int(order.filled_qty) if order.filled_qty else 0,
                "created_at": str(order.created_at),
                "filled_at": str(order.filled_at) if order.filled_at else "",
                "take_profit": take_profit,
                "stop_loss": stop_loss,
            }
        except Exception as exc:
            logger.error("place_market_order(%s) failed: %s", symbol, exc)
            return {"status": "FAILED", "error": str(exc)}

    # ──────────────────────────────────────────────────────────────────────
    # place_limit_order
    # ──────────────────────────────────────────────────────────────────────

    async def place_limit_order(
        self, symbol: str, qty: int, side: str, limit_price: float
    ) -> dict[str, Any]:
        if self.mock_mode:
            order = {
                "id": f"mock-{random.randint(10000, 99999)}",
                "symbol": symbol.upper(),
                "qty": qty,
                "side": side,
                "type": "limit",
                "limit_price": limit_price,
                "status": "accepted",
                "filled_avg_price": 0.0,
                "filled_qty": 0,
                "created_at": datetime.utcnow().isoformat(),
                "filled_at": "",
            }
            self._mock_orders.append(order)
            return order
        try:
            order_side = OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL
            req = LimitOrderRequest(
                symbol=symbol,
                qty=qty,
                side=order_side,
                limit_price=round(limit_price, 2),
                time_in_force=TimeInForce.DAY,
            )
            order = self._trade_client.submit_order(req)
            return {
                "id": order.id,
                "symbol": order.symbol,
                "qty": int(order.qty),
                "side": order.side.value,
                "type": order.type.value,
                "limit_price": float(order.limit_price),
                "status": order.status,
                "filled_avg_price": float(order.filled_avg_price) if order.filled_avg_price else 0,
                "filled_qty": int(order.filled_qty) if order.filled_qty else 0,
                "created_at": str(order.created_at),
                "filled_at": str(order.filled_at) if order.filled_at else "",
            }
        except Exception as exc:
            logger.error("place_limit_order(%s) failed: %s", symbol, exc)
            return {"status": "FAILED", "error": str(exc)}

    # ──────────────────────────────────────────────────────────────────────
    # place_stop_order
    # ──────────────────────────────────────────────────────────────────────

    async def place_stop_order(
        self, symbol: str, qty: int, side: str, stop_price: float
    ) -> dict[str, Any]:
        if self.mock_mode:
            order = {
                "id": f"mock-{random.randint(10000, 99999)}",
                "symbol": symbol.upper(),
                "qty": qty,
                "side": side,
                "type": "stop",
                "stop_price": stop_price,
                "status": "accepted",
                "filled_avg_price": 0.0,
                "filled_qty": 0,
                "created_at": datetime.utcnow().isoformat(),
                "filled_at": "",
            }
            self._mock_orders.append(order)
            return order
        try:
            order_side = OrderSide.SELL if side.upper() == "BUY" else OrderSide.BUY
            req = StopOrderRequest(
                symbol=symbol,
                qty=qty,
                side=order_side,
                stop_price=round(stop_price, 2),
                time_in_force=TimeInForce.DAY,
            )
            order = self._trade_client.submit_order(req)
            return {
                "id": order.id,
                "symbol": order.symbol,
                "qty": int(order.qty),
                "side": order.side.value,
                "type": order.type.value,
                "stop_price": float(order.stop_price),
                "status": order.status,
                "filled_avg_price": float(order.filled_avg_price) if order.filled_avg_price else 0,
                "filled_qty": int(order.filled_qty) if order.filled_qty else 0,
                "created_at": str(order.created_at),
                "filled_at": str(order.filled_at) if order.filled_at else "",
            }
        except Exception as exc:
            logger.error("place_stop_order(%s) failed: %s", symbol, exc)
            return {"status": "FAILED", "error": str(exc)}

    # ──────────────────────────────────────────────────────────────────────
    # close_position
    # ──────────────────────────────────────────────────────────────────────

    async def close_position(self, symbol: str) -> dict[str, Any]:
        if self.mock_mode:
            pos = self._mock_positions.pop(symbol.upper(), None)
            if pos:
                return {
                    "symbol": symbol.upper(),
                    "qty": pos["qty"],
                    "status": "closed",
                    "pnl": pos["unrealized_pl"],
                }
            return {"symbol": symbol.upper(), "qty": 0, "status": "no_position"}
        try:
            resp = self._trade_client.close_position(symbol)
            return {"symbol": symbol, "qty": int(resp.qty), "status": "closed"}
        except Exception as exc:
            logger.error("close_position(%s) failed: %s", symbol, exc)
            return {"symbol": symbol, "qty": 0, "status": "FAILED", "error": str(exc)}

    # ──────────────────────────────────────────────────────────────────────
    # get_bars
    # ──────────────────────────────────────────────────────────────────────

    async def get_bars(
        self, symbol: str, timeframe: str = "1Day", limit: int = 100
    ) -> list[dict[str, Any]]:
        if self.mock_mode:
            import numpy as np

            base = self._mock_base_prices.get(symbol.upper(), 100.0)
            returns = np.random.normal(0.0003, 0.02, limit)
            prices = base * np.exp(np.cumsum(returns))
            bars: list[dict[str, Any]] = []
            now = datetime.utcnow()
            for i in range(limit):
                dt = now - timedelta(days=limit - i)
                c = round(float(prices[i]), 2)
                o = round(c * (1 + random.uniform(-0.01, 0.01)), 2)
                h = round(max(o, c) * (1 + random.uniform(0, 0.005)), 2)
                l_ = round(min(o, c) * (1 - random.uniform(0, 0.005)), 2)
                bars.append(
                    {
                        "timestamp": dt.isoformat(),
                        "open": o,
                        "high": h,
                        "low": l_,
                        "close": c,
                        "volume": random.randint(500_000, 20_000_000),
                    }
                )
            return bars
        try:
            tf = TimeFrame.Day if timeframe.lower() in ("1day", "1d", "day") else TimeFrame.Hour
            req = StockBarsRequest(symbol_or_symbols=symbol, timeframe=tf, limit=limit)
            bars = self._data_client.get_stock_bars(req)
            result = []
            if symbol in bars.data:
                for bar in bars.data[symbol]:
                    result.append({
                        "timestamp": str(bar.timestamp),
                        "open": float(bar.open),
                        "high": float(bar.high),
                        "low": float(bar.low),
                        "close": float(bar.close),
                        "volume": int(bar.volume),
                    })
            return result
        except Exception as exc:
            logger.error("get_bars(%s) failed: %s", symbol, exc)
            return []

    # ──────────────────────────────────────────────────────────────────────
    # get_clock
    # ──────────────────────────────────────────────────────────────────────

    async def get_clock(self) -> dict[str, Any]:
        if self.mock_mode:
            now = datetime.utcnow()
            is_open = 9 <= now.hour < 16 and now.weekday() < 5
            next_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
            next_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
            if now.hour >= 16:
                next_open = next_open + timedelta(days=1)
                next_close = next_close + timedelta(days=1)
            if now.weekday() >= 5:
                days_ahead = 7 - now.weekday()
                next_open = next_open + timedelta(days=days_ahead)
                next_close = next_close + timedelta(days=days_ahead)
            return {
                "is_open": is_open,
                "next_open": next_open.isoformat(),
                "next_close": next_close.isoformat(),
                "timestamp": now.isoformat(),
            }
        try:
            clock = self._trade_client.get_clock()
            return {
                "is_open": clock.is_open,
                "next_open": str(clock.next_open),
                "next_close": str(clock.next_close),
                "timestamp": str(clock.timestamp),
            }
        except Exception as exc:
            logger.error("get_clock failed: %s", exc)
            return {"is_open": False, "next_open": "", "next_close": "", "timestamp": ""}

    # ──────────────────────────────────────────────────────────────────────
    # internal helpers
    # ──────────────────────────────────────────────────────────────────────

    def _update_mock_position(
        self, symbol: str, qty: int, side: str, price: float
    ) -> None:
        if side.upper() == "BUY":
            existing = self._mock_positions.get(symbol)
            if existing:
                total_qty = existing["qty"] + qty
                total_cost = existing["cost_basis"] + qty * price
                existing["qty"] = total_qty
                existing["avg_entry_price"] = round(total_cost / total_qty, 2)
                existing["cost_basis"] = round(total_cost, 2)
                existing["market_value"] = round(total_qty * price, 2)
                existing["current_price"] = price
                existing["unrealized_pl"] = round(
                    existing["market_value"] - existing["cost_basis"], 2
                )
                existing["unrealized_pl_pct"] = round(
                    (price / existing["avg_entry_price"] - 1) * 100, 2
                )
            else:
                self._mock_positions[symbol] = {
                    "symbol": symbol,
                    "qty": qty,
                    "avg_entry_price": price,
                    "current_price": price,
                    "market_value": round(qty * price, 2),
                    "cost_basis": round(qty * price, 2),
                    "unrealized_pl": 0.0,
                    "unrealized_pl_pct": 0.0,
                }
        else:
            existing = self._mock_positions.get(symbol)
            if existing:
                existing["qty"] -= qty
                if existing["qty"] <= 0:
                    self._mock_positions.pop(symbol, None)
                else:
                    existing["market_value"] = round(existing["qty"] * price, 2)
                    existing["current_price"] = price
                    existing["unrealized_pl"] = round(
                        existing["market_value"] - existing["cost_basis"], 2
                    )
                    existing["unrealized_pl_pct"] = round(
                        (price / existing["avg_entry_price"] - 1) * 100, 2
                    )

    async def close(self) -> None:
        pass  # Alpaca SDK clients don't require explicit cleanup
