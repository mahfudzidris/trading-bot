"""Tests for db/models.py — SQLAlchemy ORM models."""

from __future__ import annotations

from datetime import datetime

import pytest
import pytest_asyncio

from db.models import (
    BacktestResult,
    DailyReport,
    Position,
    Trade,
    TradeSide,
    TradeStatus,
)


class TestTrade:
    """Tests for the Trade model."""

    def test_trade_creation(self):
        """Verify a Trade can be constructed with minimal fields."""
        from datetime import datetime
        t = Trade(
            symbol="AAPL",
            side=TradeSide.BUY,
            qty=10,
            entry_price=150.0,
            entry_time=datetime.utcnow(),
            status=TradeStatus.OPEN,
        )
        assert t.symbol == "AAPL"
        assert t.side == TradeSide.BUY
        assert t.qty == 10
        assert t.entry_price == 150.0
        assert t.status == TradeStatus.OPEN
        assert t.entry_time is not None

    def test_trade_to_dict(self):
        """Verify to_dict returns the expected keys."""
        t = Trade(
            symbol="TSLA",
            side=TradeSide.SELL,
            qty=5,
            entry_price=250.0,
            entry_time=datetime(2025, 1, 1, 10, 0, 0),
            status=TradeStatus.OPEN,
        )
        d = t.to_dict()
        assert d["symbol"] == "TSLA"
        assert d["side"] == "SELL"
        assert d["qty"] == 5
        assert d["entry_price"] == 250.0
        assert d["status"] == "OPEN"
        assert d["exit_price"] is None
        assert "entry_time" in d

    def test_trade_to_dict_closed(self):
        """Verify to_dict reflects CLOSED status properly."""
        t = Trade(
            symbol="MSFT",
            side=TradeSide.BUY,
            qty=20,
            entry_price=380.0,
            exit_price=395.0,
            exit_time=datetime(2025, 1, 5, 16, 0, 0),
            pnl=300.0,
            pnl_pct=3.95,
            status=TradeStatus.CLOSED,
        )
        d = t.to_dict()
        assert d["status"] == "CLOSED"
        assert d["exit_price"] == 395.0
        assert d["pnl"] == 300.0
        assert d["pnl_pct"] == 3.95

    def test_trade_optional_fields(self):
        """Verify optional fields like stop_loss, take_profit, strategy work."""
        t = Trade(
            symbol="GOOGL",
            side=TradeSide.BUY,
            qty=15,
            entry_price=140.0,
            stop_loss=137.2,
            take_profit=147.0,
            strategy="ai_test",
            ai_reasoning="Bullish signal detected",
            ai_confidence=85,
        )
        d = t.to_dict()
        assert d["stop_loss"] == 137.2
        assert d["take_profit"] == 147.0
        assert d["strategy"] == "ai_test"
        assert d["ai_reasoning"] == "Bullish signal detected"
        assert d["ai_confidence"] == 85


class TestDailyReport:
    """Tests for the DailyReport model."""

    def test_daily_report_creation(self):
        """Verify a DailyReport can be constructed."""
        r = DailyReport(
            date="2025-01-15",
            total_pnl=1250.50,
            win_count=5,
            loss_count=2,
            total_trades=7,
            win_rate=71.4,
            starting_balance=100000.0,
            ending_balance=101250.50,
        )
        assert r.date == "2025-01-15"
        assert r.total_pnl == 1250.50
        assert r.win_rate == 71.4

    def test_daily_report_to_dict(self):
        """Verify to_dict returns expected keys."""
        r = DailyReport(
            date="2025-01-15",
            total_pnl=500.0,
            win_count=3,
            loss_count=1,
            total_trades=4,
            win_rate=75.0,
            starting_balance=100000.0,
            ending_balance=100500.0,
            notes="Good day",
        )
        d = r.to_dict()
        assert d["date"] == "2025-01-15"
        assert d["total_pnl"] == 500.0
        assert d["win_rate"] == 75.0
        assert d["notes"] == "Good day"
        assert "id" in d


class TestPosition:
    """Tests for the Position model."""

    def test_position_creation(self):
        """Verify a Position can be constructed."""
        p = Position(
            symbol="AAPL",
            qty=100,
            avg_entry_price=180.0,
            current_price=185.0,
            unrealized_pnl=500.0,
        )
        assert p.symbol == "AAPL"
        assert p.qty == 100
        assert p.avg_entry_price == 180.0
        assert p.current_price == 185.0
        assert p.unrealized_pnl == 500.0

    def test_position_to_dict(self):
        """Verify to_dict returns expected keys."""
        p = Position(
            symbol="TSLA",
            qty=50,
            avg_entry_price=250.0,
            current_price=260.0,
            unrealized_pnl=500.0,
        )
        d = p.to_dict()
        assert d["symbol"] == "TSLA"
        assert d["qty"] == 50
        assert d["unrealized_pnl"] == 500.0
        assert "updated_at" in d


class TestBacktestResult:
    """Tests for the BacktestResult model."""

    def test_backtest_result_creation(self):
        """Verify a BacktestResult can be constructed."""
        br = BacktestResult(
            symbol="AAPL",
            start_date="2025-01-01",
            end_date="2025-01-31",
            initial_capital=100000.0,
            days=21,
            total_pnl=5000.0,
            total_pnl_pct=5.0,
            final_capital=105000.0,
            total_trades=15,
            wins=10,
            losses=5,
            win_rate=66.7,
            sharpe_ratio=1.5,
            sortino_ratio=2.1,
            max_drawdown_pct=-8.5,
        )
        assert br.symbol == "AAPL"
        assert br.total_trades == 15
        assert br.win_rate == 66.7

    def test_backtest_result_to_dict(self):
        """Verify to_dict returns expected keys."""
        br = BacktestResult(
            symbol="TSLA",
            start_date="2025-01-01",
            end_date="2025-03-31",
            initial_capital=100000.0,
            days=63,
            total_pnl=12000.0,
            total_pnl_pct=12.0,
            final_capital=112000.0,
            total_trades=30,
            wins=18,
            losses=12,
            win_rate=60.0,
            max_drawdown_pct=-12.0,
            sharpe_ratio=1.2,
            sortino_ratio=1.8,
        )
        d = br.to_dict()
        assert d["symbol"] == "TSLA"
        assert d["total_trades"] == 30
        assert d["win_rate"] == 60.0
        assert d["sharpe_ratio"] == 1.2
        assert "created_at" in d
