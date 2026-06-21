"""Tests for db/crud.py — Async CRUD operations.

These tests use a real async SQLite database (created per test via test_db fixture).
"""

from __future__ import annotations

from datetime import date, datetime

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from db import crud


class TestCRUDTrades:
    """Tests for trade CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_trade(self, test_db: AsyncSession):
        """Verify create_trade creates a trade and returns its dict."""
        trade_data = {
            "symbol": "AAPL",
            "side": "BUY",
            "qty": 10,
            "entry_price": 150.0,
            "stop_loss": 147.0,
            "take_profit": 157.5,
            "strategy": "test",
            "ai_reasoning": "Test buy signal",
            "ai_confidence": 85,
        }
        trade = await crud.create_trade(test_db, trade_data)
        assert trade["symbol"] == "AAPL"
        assert trade["side"] == "BUY"
        assert trade["qty"] == 10
        assert trade["entry_price"] == 150.0
        assert trade["status"] == "OPEN"

    @pytest.mark.asyncio
    async def test_get_trade_history(self, test_db: AsyncSession):
        """Verify get_trade_history returns created trades."""
        await crud.create_trade(test_db, {"symbol": "AAPL", "side": "BUY", "qty": 10, "entry_price": 150.0})
        await crud.create_trade(test_db, {"symbol": "TSLA", "side": "SELL", "qty": 5, "entry_price": 250.0})
        trades = await crud.get_trade_history(test_db)
        assert len(trades) >= 2

    @pytest.mark.asyncio
    async def test_get_trade_history_with_filters(self, test_db: AsyncSession):
        """Verify get_trade_history filters by symbol."""
        await crud.create_trade(test_db, {"symbol": "AAPL", "side": "BUY", "qty": 10, "entry_price": 150.0})
        await crud.create_trade(test_db, {"symbol": "TSLA", "side": "SELL", "qty": 5, "entry_price": 250.0})
        trades = await crud.get_trade_history(test_db, symbol="AAPL")
        assert len(trades) == 1
        assert trades[0]["symbol"] == "AAPL"

    @pytest.mark.asyncio
    async def test_close_trade(self, test_db: AsyncSession):
        """Verify close_trade updates status to CLOSED with PnL."""
        trade = await crud.create_trade(test_db, {"symbol": "AAPL", "side": "BUY", "qty": 10, "entry_price": 150.0})
        closed = await crud.close_trade(test_db, trade["id"], exit_price=160.0)
        assert closed is not None
        assert closed["status"] == "CLOSED"
        assert closed["exit_price"] == 160.0
        # PnL = (160 - 150) * 10 = 100
        assert closed["pnl"] == 100.0

    @pytest.mark.asyncio
    async def test_close_trade_not_found(self, test_db: AsyncSession):
        """Verify close_trade returns None for non-existent trade."""
        result = await crud.close_trade(test_db, 99999, exit_price=100.0)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_open_trades(self, test_db: AsyncSession):
        """Verify get_open_trades returns only OPEN trades."""
        t1 = await crud.create_trade(test_db, {"symbol": "AAPL", "side": "BUY", "qty": 10, "entry_price": 150.0})
        await crud.create_trade(test_db, {"symbol": "TSLA", "side": "SELL", "qty": 5, "entry_price": 250.0})
        await crud.close_trade(test_db, t1["id"], exit_price=160.0)
        open_trades = await crud.get_open_trades(test_db)
        assert len(open_trades) == 1
        assert open_trades[0]["symbol"] == "TSLA"

    @pytest.mark.asyncio
    async def test_get_trades_by_date(self, test_db: AsyncSession):
        """Verify get_trades_by_date returns trades for a specific date."""
        trade = await crud.create_trade(test_db, {"symbol": "AAPL", "side": "BUY", "qty": 10, "entry_price": 150.0})
        entry_str = trade["entry_time"]
        trade_date = datetime.strptime(entry_str[:10], "%Y-%m-%d").date()
        trades = await crud.get_trades_by_date(test_db, trade_date)
        assert len(trades) >= 1


class TestCRUDDailyReports:
    """Tests for daily report CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_daily_report(self, test_db: AsyncSession):
        """Verify create_daily_report creates a report."""
        report = await crud.create_daily_report(test_db, {
            "date": "2025-01-15",
            "total_pnl": 500.0,
            "win_count": 3,
            "loss_count": 1,
            "total_trades": 4,
            "win_rate": 75.0,
        })
        assert report["date"] == "2025-01-15"
        assert report["total_pnl"] == 500.0
        assert report["win_rate"] == 75.0

    @pytest.mark.asyncio
    async def test_create_daily_report_update_existing(self, test_db: AsyncSession):
        """Verify create_daily_report updates an existing report for the same date."""
        await crud.create_daily_report(test_db, {"date": "2025-01-15", "total_pnl": 500.0, "win_count": 3})
        updated = await crud.create_daily_report(test_db, {"date": "2025-01-15", "total_pnl": 800.0, "win_count": 5})
        assert updated["total_pnl"] == 800.0
        assert updated["win_count"] == 5

    @pytest.mark.asyncio
    async def test_get_daily_reports(self, test_db: AsyncSession):
        """Verify get_daily_reports returns reports ordered by date desc."""
        await crud.create_daily_report(test_db, {"date": "2025-01-14", "total_pnl": 100.0, "win_count": 1})
        await crud.create_daily_report(test_db, {"date": "2025-01-15", "total_pnl": 200.0, "win_count": 2})
        reports = await crud.get_daily_reports(test_db)
        assert len(reports) == 2
        # Most recent first
        assert reports[0]["date"] > reports[1]["date"]


class TestCRUDPositions:
    """Tests for position CRUD operations."""

    @pytest.mark.asyncio
    async def test_update_position_create(self, test_db: AsyncSession):
        """Verify update_position creates a new position."""
        pos = await crud.update_position(test_db, {
            "symbol": "AAPL",
            "qty": 100,
            "avg_entry_price": 180.0,
            "current_price": 185.0,
            "unrealized_pnl": 500.0,
        })
        assert pos["symbol"] == "AAPL"
        assert pos["qty"] == 100

    @pytest.mark.asyncio
    async def test_update_position_update(self, test_db: AsyncSession):
        """Verify update_position updates an existing position."""
        await crud.update_position(test_db, {
            "symbol": "AAPL",
            "qty": 100,
            "avg_entry_price": 180.0,
            "current_price": 185.0,
            "unrealized_pnl": 500.0,
        })
        updated = await crud.update_position(test_db, {
            "symbol": "AAPL",
            "qty": 150,
            "current_price": 190.0,
            "unrealized_pnl": 1500.0,
        })
        assert updated["qty"] == 150
        assert updated["current_price"] == 190.0

    @pytest.mark.asyncio
    async def test_get_positions(self, test_db: AsyncSession):
        """Verify get_positions returns all positions."""
        await crud.update_position(test_db, {"symbol": "AAPL", "qty": 100, "avg_entry_price": 180.0, "current_price": 185.0})
        await crud.update_position(test_db, {"symbol": "TSLA", "qty": 50, "avg_entry_price": 250.0, "current_price": 260.0})
        positions = await crud.get_positions(test_db)
        assert len(positions) == 2

    @pytest.mark.asyncio
    async def test_delete_position(self, test_db: AsyncSession):
        """Verify delete_position removes a position."""
        await crud.update_position(test_db, {"symbol": "AAPL", "qty": 100, "avg_entry_price": 180.0, "current_price": 185.0})
        deleted = await crud.delete_position(test_db, "AAPL")
        assert deleted is True
        positions = await crud.get_positions(test_db)
        assert len(positions) == 0

    @pytest.mark.asyncio
    async def test_delete_position_not_found(self, test_db: AsyncSession):
        """Verify delete_position returns False for non-existent position."""
        result = await crud.delete_position(test_db, "NONEXISTENT")
        assert result is False


class TestCRUDBacktestResults:
    """Tests for backtest result CRUD operations."""

    @pytest.mark.asyncio
    async def test_save_backtest_result(self, test_db: AsyncSession):
        """Verify save_backtest_result stores a BacktestResult."""
        result_dict = {
            "symbol": "AAPL",
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
            "initial_capital": 100000.0,
            "days": 21,
            "total_pnl": 5000.0,
            "total_pnl_pct": 5.0,
            "final_capital": 105000.0,
            "total_trades": 15,
            "wins": 10,
            "losses": 5,
            "win_rate": 66.7,
            "trades": [],
            "equity_curve": [],
        }
        saved = await crud.save_backtest_result(test_db, result_dict)
        assert saved["symbol"] == "AAPL"
        assert saved["total_trades"] == 15

    @pytest.mark.asyncio
    async def test_get_backtest_results(self, test_db: AsyncSession):
        """Verify get_backtest_results returns stored results."""
        base = {
            "symbol": "AAPL", "start_date": "2025-01-01", "end_date": "2025-01-31",
            "initial_capital": 100000.0, "days": 21, "total_pnl": 5000.0,
            "total_pnl_pct": 5.0, "final_capital": 105000.0, "total_trades": 15,
            "wins": 10, "losses": 5, "win_rate": 66.7, "trades": [], "equity_curve": [],
        }
        await crud.save_backtest_result(test_db, base)
        base["symbol"] = "TSLA"
        await crud.save_backtest_result(test_db, base)
        results = await crud.get_backtest_results(test_db)
        assert len(results) >= 2

    @pytest.mark.asyncio
    async def test_get_backtest_by_id(self, test_db: AsyncSession):
        """Verify get_backtest_by_id returns a specific result."""
        base = {
            "symbol": "AAPL", "start_date": "2025-01-01", "end_date": "2025-01-31",
            "initial_capital": 100000.0, "days": 21, "total_pnl": 5000.0,
            "total_pnl_pct": 5.0, "final_capital": 105000.0, "total_trades": 15,
            "wins": 10, "losses": 5, "win_rate": 66.7, "trades": [], "equity_curve": [],
        }
        saved = await crud.save_backtest_result(test_db, base)
        fetched = await crud.get_backtest_by_id(test_db, saved["id"])
        assert fetched is not None
        assert fetched["symbol"] == "AAPL"

    @pytest.mark.asyncio
    async def test_get_backtest_by_id_not_found(self, test_db: AsyncSession):
        """Verify get_backtest_by_id returns None for non-existent ID."""
        result = await crud.get_backtest_by_id(test_db, 99999)
        assert result is None
