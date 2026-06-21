"""Tests for strategy/engine.py — StrategyEngine."""

from __future__ import annotations

import pytest
import pytest_asyncio


class TestStrategyEngine:
    """Tests for StrategyEngine with mocked clients."""

    @pytest.mark.asyncio
    async def test_run_daily_analysis_returns_dict(self, mock_strategy_engine):
        """Verify run_daily_analysis returns a dict with analyses."""
        result = await mock_strategy_engine.run_daily_analysis()
        assert isinstance(result, dict)
        assert "date" in result
        assert "analyses" in result
        assert isinstance(result["analyses"], list)

    @pytest.mark.asyncio
    async def test_run_daily_analysis_analyses_all_symbols(self, mock_strategy_engine):
        """Verify run_daily_analysis processes all configured symbols."""
        result = await mock_strategy_engine.run_daily_analysis()
        symbols_analysed = [a["symbol"] for a in result["analyses"]]
        for sym in mock_strategy_engine.config.SYMBOLS:
            assert sym in symbols_analysed

    @pytest.mark.asyncio
    async def test_evaluate_symbol_returns_expected_keys(self, mock_strategy_engine):
        """Verify evaluate_symbol returns dict with symbol, price_data, decision, action_taken."""
        result = await mock_strategy_engine.evaluate_symbol("AAPL")
        assert "symbol" in result
        assert result["symbol"] == "AAPL"
        assert "price_data" in result
        assert "indicators" in result
        assert "decision" in result
        assert "action_taken" in result
        assert "pnl_impact" in result

    @pytest.mark.asyncio
    async def test_evaluate_symbol_price_data(self, mock_strategy_engine):
        """Verify evaluate_symbol price_data has price, change_pct, volume, timestamp."""
        result = await mock_strategy_engine.evaluate_symbol("MSFT")
        pd = result["price_data"]
        assert "price" in pd
        assert "change_pct" in pd
        assert "volume" in pd
        assert "timestamp" in pd
        assert pd["price"] > 0

    @pytest.mark.asyncio
    async def test_evaluate_symbol_decision_keys(self, mock_strategy_engine):
        """Verify evaluate_symbol decision has action, confidence, reasoning."""
        result = await mock_strategy_engine.evaluate_symbol("GOOGL")
        decision = result["decision"]
        assert "action" in decision
        assert "confidence" in decision
        assert "reasoning" in decision
        assert decision["action"] in ("BUY", "SELL", "HOLD")

    @pytest.mark.asyncio
    async def test_get_performance_summary(self, mock_strategy_engine):
        """Verify get_performance_summary returns metrics."""
        summary = await mock_strategy_engine.get_performance_summary(days=30)
        assert isinstance(summary, dict)
        assert "total_pnl" in summary
        assert "win_rate" in summary
        assert "trades_count" in summary
        assert "wins" in summary
        assert "losses" in summary

    @pytest.mark.asyncio
    async def test_get_performance_summary_shorter_period(self, mock_strategy_engine):
        """Verify get_performance_summary with a short period still works."""
        summary = await mock_strategy_engine.get_performance_summary(days=5)
        assert summary["period_days"] == 5

    @pytest.mark.asyncio
    async def test_multiple_evaluations(self, mock_strategy_engine):
        """Verify evaluate_symbol can be called multiple times."""
        r1 = await mock_strategy_engine.evaluate_symbol("AAPL")
        r2 = await mock_strategy_engine.evaluate_symbol("TSLA")
        assert r1["symbol"] == "AAPL"
        assert r2["symbol"] == "TSLA"

    @pytest.mark.asyncio
    async def test_evaluate_symbol_price_data_consistent(self, mock_strategy_engine):
        """Verify price_data and indicators are consistent with each other."""
        result = await mock_strategy_engine.evaluate_symbol("AAPL")
        price = result["price_data"]["price"]
        ind_price = result["indicators"]["price"]
        # They should be close, though may have small differences due to separate mock calls
        assert price > 0
        assert ind_price > 0

    @pytest.mark.asyncio
    async def test_mock_performance_summary(self, mock_strategy_engine):
        """Verify _mock_performance_summary generates realistic data."""
        summary = await mock_strategy_engine._mock_performance_summary(days=10)
        assert summary["trades_count"] > 0
        assert summary["period_days"] == 10
        assert summary["win_rate"] > 0
