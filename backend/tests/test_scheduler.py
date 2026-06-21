"""Tests for scheduler/daily_run.py — run_daily function."""

from __future__ import annotations

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch


class TestRunDaily:
    """Tests for the run_daily scheduler function."""

    @pytest.mark.asyncio
    async def test_run_daily_returns_summary(
        self, test_db, mock_twelvedata_client, mock_deepseek_analyzer, mock_alpaca_client, test_settings
    ):
        """Verify run_daily returns a dict with date, market_open, total_pnl, trades_executed."""
        from scheduler.daily_run import run_daily
        from strategy.engine import StrategyEngine

        engine = StrategyEngine(
            data_client=mock_twelvedata_client,
            ai_analyzer=mock_deepseek_analyzer,
            broker_client=mock_alpaca_client,
            config=test_settings,
        )

        summary = await run_daily(
            data_client=mock_twelvedata_client,
            ai_analyzer=mock_deepseek_analyzer,
            broker_client=mock_alpaca_client,
            strategy_engine=engine,
            db_session=test_db,
            config=test_settings,
        )
        assert isinstance(summary, dict)
        assert "date" in summary
        assert "market_open" in summary
        assert "total_pnl" in summary
        assert "trades_executed" in summary
        assert "analyses" in summary

    @pytest.mark.asyncio
    async def test_run_daily_in_mock_mode_always_runs(
        self, test_db, mock_twelvedata_client, mock_deepseek_analyzer, mock_alpaca_client, test_settings
    ):
        """Verify run_daily executes analysis even when markets are closed in mock mode."""
        from scheduler.daily_run import run_daily
        from strategy.engine import StrategyEngine

        engine = StrategyEngine(
            data_client=mock_twelvedata_client,
            ai_analyzer=mock_deepseek_analyzer,
            broker_client=mock_alpaca_client,
            config=test_settings,
        )

        summary = await run_daily(
            data_client=mock_twelvedata_client,
            ai_analyzer=mock_deepseek_analyzer,
            broker_client=mock_alpaca_client,
            strategy_engine=engine,
            db_session=test_db,
            config=test_settings,
        )
        # Should have analyses even if markets are closed (mock mode)
        assert len(summary["analyses"]) > 0

    @pytest.mark.asyncio
    async def test_run_daily_persists_report(
        self, test_db, mock_twelvedata_client, mock_deepseek_analyzer, mock_alpaca_client, test_settings
    ):
        """Verify run_daily creates a daily report in the database."""
        from scheduler.daily_run import run_daily
        from strategy.engine import StrategyEngine
        from db import crud

        engine = StrategyEngine(
            data_client=mock_twelvedata_client,
            ai_analyzer=mock_deepseek_analyzer,
            broker_client=mock_alpaca_client,
            config=test_settings,
        )

        await run_daily(
            data_client=mock_twelvedata_client,
            ai_analyzer=mock_deepseek_analyzer,
            broker_client=mock_alpaca_client,
            strategy_engine=engine,
            db_session=test_db,
            config=test_settings,
        )

        # Check the report was saved
        reports = await crud.get_daily_reports(test_db, limit=5)
        assert len(reports) >= 1

    @pytest.mark.asyncio
    async def test_run_daily_analyses_expected_keys(
        self, test_db, mock_twelvedata_client, mock_deepseek_analyzer, mock_alpaca_client, test_settings
    ):
        """Verify each analysis result has the required keys."""
        from scheduler.daily_run import run_daily
        from strategy.engine import StrategyEngine

        engine = StrategyEngine(
            data_client=mock_twelvedata_client,
            ai_analyzer=mock_deepseek_analyzer,
            broker_client=mock_alpaca_client,
            config=test_settings,
        )

        summary = await run_daily(
            data_client=mock_twelvedata_client,
            ai_analyzer=mock_deepseek_analyzer,
            broker_client=mock_alpaca_client,
            strategy_engine=engine,
            db_session=test_db,
            config=test_settings,
        )

        for analysis in summary["analyses"]:
            assert "symbol" in analysis
            assert "decision" in analysis
            assert "action_taken" in analysis
            assert "pnl_impact" in analysis
