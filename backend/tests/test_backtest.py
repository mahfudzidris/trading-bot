"""Tests for backtest/engine.py — BacktestEngine."""

from __future__ import annotations

import pytest
import pytest_asyncio


class TestBacktestEngine:
    """Tests for BacktestEngine with mocked data and AI clients."""

    @pytest.mark.asyncio
    async def test_run_returns_backtest_result(self, mock_twelvedata_client, mock_deepseek_analyzer):
        """Verify run() returns a BacktestResult with expected metrics."""
        from backtest.engine import BacktestEngine

        engine = BacktestEngine(
            data_client=mock_twelvedata_client,
            ai_analyzer=mock_deepseek_analyzer,
            initial_capital=100_000.0,
        )
        result = await engine.run(
            symbol="AAPL",
            start_date="2025-01-01",
            end_date="2025-01-31",
        )
        assert result.symbol == "AAPL"
        assert result.initial_capital == 100_000.0
        assert isinstance(result.total_trades, int)
        assert result.days > 0

    @pytest.mark.asyncio
    async def test_run_contains_trades(self, mock_twelvedata_client, mock_deepseek_analyzer):
        """Verify run() returns a result with trade history.
        
        Note: With mock data and short ranges, trades may or may not occur
        depending on random signals. We verify the structure regardless.
        """
        from backtest.engine import BacktestEngine

        engine = BacktestEngine(
            data_client=mock_twelvedata_client,
            ai_analyzer=mock_deepseek_analyzer,
            initial_capital=100_000.0,
        )
        result = await engine.run(
            symbol="AAPL",
            start_date="2025-02-01",
            end_date="2025-02-28",
        )
        assert isinstance(result.trades, list)
        assert isinstance(result.total_trades, int)
        assert result.total_trades >= 0

    @pytest.mark.asyncio
    async def test_run_metrics(self, mock_twelvedata_client, mock_deepseek_analyzer):
        """Verify run() computes win_rate, max_drawdown, sharpe, sortino."""
        from backtest.engine import BacktestEngine

        engine = BacktestEngine(
            data_client=mock_twelvedata_client,
            ai_analyzer=mock_deepseek_analyzer,
            initial_capital=100_000.0,
        )
        result = await engine.run(
            symbol="AAPL",
            start_date="2025-03-01",
            end_date="2025-03-31",
        )
        assert result.win_rate >= 0.0
        assert result.win_rate <= 100.0
        assert result.max_drawdown <= 0
        if result.total_trades > 0:
            assert result.sharpe_ratio != 0.0 or result.volatility > 0
            # sortino may be 0 if no downside deviation; check that it was computed
            assert isinstance(result.sortino_ratio, float)

    @pytest.mark.asyncio
    async def test_run_with_different_symbol(self, mock_twelvedata_client, mock_deepseek_analyzer):
        """Verify run works with different symbols."""
        from backtest.engine import BacktestEngine

        engine = BacktestEngine(
            data_client=mock_twelvedata_client,
            ai_analyzer=mock_deepseek_analyzer,
        )
        result = await engine.run(
            symbol="TSLA",
            start_date="2025-01-01",
            end_date="2025-01-15",
        )
        assert result.symbol == "TSLA"
        assert result.days > 0

    @pytest.mark.asyncio
    async def test_run_with_strategy_params(self, mock_twelvedata_client, mock_deepseek_analyzer):
        """Verify run accepts and uses strategy_params override."""
        from backtest.engine import BacktestEngine

        engine = BacktestEngine(
            data_client=mock_twelvedata_client,
            ai_analyzer=mock_deepseek_analyzer,
            initial_capital=50_000.0,
        )
        params = {
            "stop_loss_pct": 0.03,
            "take_profit_pct": 0.08,
            "max_position_size_pct": 0.2,
            "use_ai": True,
        }
        result = await engine.run(
            symbol="AAPL",
            start_date="2025-04-01",
            end_date="2025-04-15",
            strategy_params=params,
        )
        assert result.initial_capital == 50_000.0
        assert result.total_trades >= 0

    @pytest.mark.asyncio
    async def test_to_dict(self, mock_twelvedata_client, mock_deepseek_analyzer):
        """Verify BacktestResult.to_dict returns a flat dict."""
        from backtest.engine import BacktestEngine

        engine = BacktestEngine(
            data_client=mock_twelvedata_client,
            ai_analyzer=mock_deepseek_analyzer,
        )
        result = await engine.run(
            symbol="AAPL",
            start_date="2025-01-01",
            end_date="2025-01-10",
        )
        d = result.to_dict()
        assert isinstance(d, dict)
        assert d["symbol"] == "AAPL"
        assert "total_trades" in d
        assert "sharpe_ratio" in d
        assert "trades" in d
        assert "equity_curve" in d

    @pytest.mark.asyncio
    async def test_summary_table(self, mock_twelvedata_client, mock_deepseek_analyzer):
        """Verify summary_table returns a compact dict."""
        from backtest.engine import BacktestEngine

        engine = BacktestEngine(
            data_client=mock_twelvedata_client,
            ai_analyzer=mock_deepseek_analyzer,
        )
        result = await engine.run(
            symbol="AAPL",
            start_date="2025-01-01",
            end_date="2025-01-10",
        )
        s = result.summary_table()
        assert "symbol" in s
        assert "period" in s
        assert "initial_capital" in s
        assert "total_pnl" in s

    @pytest.mark.asyncio
    async def test_convenience_run_backtest(self, mock_twelvedata_client, mock_deepseek_analyzer):
        """Verify the convenience wrapper run_backtest() works."""
        from backtest.engine import run_backtest

        result = await run_backtest(
            data_client=mock_twelvedata_client,
            ai_analyzer=mock_deepseek_analyzer,
            symbol="AAPL",
            start_date="2025-01-01",
            end_date="2025-01-10",
            initial_capital=100_000.0,
        )
        assert result is not None
        assert result.total_trades >= 0
