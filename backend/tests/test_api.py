"""Tests for main.py — FastAPI API routes.

Uses httpx.AsyncClient with ASGITransport to test all endpoints with mocked services.
"""

from __future__ import annotations

import pytest
import pytest_asyncio


class TestAPIHealth:
    """Tests for GET /api/health."""

    @pytest.mark.asyncio
    async def test_health_check(self, async_client):
        """Verify GET /api/health returns status ok."""
        resp = await async_client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "timestamp" in data
        assert "mock_mode" in data
        assert "version" in data


class TestAPIAccount:
    """Tests for GET /api/account."""

    @pytest.mark.asyncio
    async def test_get_account(self, async_client):
        """Verify GET /api/account returns account summary."""
        resp = await async_client.get("/api/account")
        assert resp.status_code == 200
        data = resp.json()
        assert "balance" in data
        assert "buying_power" in data
        assert "portfolio_value" in data
        assert "pnl" in data
        assert "status" in data


class TestAPIPositions:
    """Tests for GET /api/positions."""

    @pytest.mark.asyncio
    async def test_get_positions(self, async_client):
        """Verify GET /api/positions returns a list of positions."""
        resp = await async_client.get("/api/positions")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        if data:
            assert "symbol" in data[0]
            assert "qty" in data[0]


class TestAPITrades:
    """Tests for GET /api/trades."""

    @pytest.mark.asyncio
    async def test_get_trades(self, async_client):
        """Verify GET /api/trades returns a list of trades."""
        resp = await async_client.get("/api/trades")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_trades_with_limit(self, async_client):
        """Verify GET /api/trades accepts limit parameter."""
        resp = await async_client.get("/api/trades?limit=5")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_trades_today(self, async_client):
        """Verify GET /api/trades/today returns list."""
        resp = await async_client.get("/api/trades/today")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_trades_with_symbol_filter(self, async_client):
        """Verify GET /api/trades accepts symbol filter."""
        resp = await async_client.get("/api/trades?symbol=AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)


class TestAPIDailyReports:
    """Tests for GET /api/daily-reports."""

    @pytest.mark.asyncio
    async def test_get_daily_reports(self, async_client):
        """Verify GET /api/daily-reports returns a list of reports."""
        resp = await async_client.get("/api/daily-reports")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)


class TestAPIAnalyze:
    """Tests for GET /api/analyze/{symbol}."""

    @pytest.mark.asyncio
    async def test_analyze_symbol(self, async_client):
        """Verify GET /api/analyze/{symbol} returns analysis data."""
        resp = await async_client.get("/api/analyze/AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert data["symbol"] == "AAPL"
        assert "price_data" in data
        assert "indicators" in data
        assert "decision" in data

    @pytest.mark.asyncio
    async def test_analyze_symbol_decision_keys(self, async_client):
        """Verify analyze response contains decision with action, confidence, reasoning."""
        resp = await async_client.get("/api/analyze/TSLA")
        data = resp.json()
        decision = data["decision"]
        assert "action" in decision
        assert "confidence" in decision
        assert "reasoning" in decision

    @pytest.mark.asyncio
    async def test_analyze_symbol_indicators_keys(self, async_client):
        """Verify analyze response indicators has expected fields."""
        resp = await async_client.get("/api/analyze/MSFT")
        data = resp.json()
        ind = data["indicators"]
        assert "price" in ind
        assert "sma_20" in ind
        assert "sma_50" in ind
        assert "rsi_14" in ind


class TestAPIRunAnalysis:
    """Tests for POST /api/run-analysis."""

    @pytest.mark.asyncio
    async def test_run_analysis(self, async_client):
        """Verify POST /api/run-analysis triggers analysis and returns summary."""
        resp = await async_client.post("/api/run-analysis")
        assert resp.status_code == 200
        data = resp.json()
        assert "date" in data
        assert "total_pnl" in data
        assert "trades_executed" in data
        assert "analyses" in data

    @pytest.mark.asyncio
    async def test_run_analysis_analyses_all_symbols(self, async_client):
        """Verify run-analysis returns analyses for all configured symbols."""
        resp = await async_client.post("/api/run-analysis")
        data = resp.json()
        symbols_returned = {a["symbol"] for a in data["analyses"]}
        expected = {"AAPL", "TSLA", "MSFT", "GOOGL", "AMZN"}
        assert symbols_returned == expected


class TestAPIPerformance:
    """Tests for GET /api/performance."""

    @pytest.mark.asyncio
    async def test_get_performance(self, async_client):
        """Verify GET /api/performance returns aggregated metrics."""
        resp = await async_client.get("/api/performance")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_pnl" in data
        assert "win_rate" in data
        assert "trades_count" in data
        assert "wins" in data
        assert "losses" in data

    @pytest.mark.asyncio
    async def test_get_performance_with_days(self, async_client):
        """Verify GET /api/performance accepts days parameter."""
        resp = await async_client.get("/api/performance?days=10")
        assert resp.status_code == 200
        data = resp.json()
        assert data["period_days"] == 10


class TestAPIStrategy:
    """Tests for GET /api/strategy."""

    @pytest.mark.asyncio
    async def test_get_strategy(self, async_client):
        """Verify GET /api/strategy returns strategy configuration."""
        resp = await async_client.get("/api/strategy")
        assert resp.status_code == 200
        data = resp.json()
        assert "Ensemble Signals" in data["name"]
        assert "prompt_template" in data
        assert "indicators" in data
        assert "decision_fields" in data
        assert "risk_parameters" in data
        assert "model" in data

    @pytest.mark.asyncio
    async def test_strategy_indicators(self, async_client):
        """Verify strategy returns all 6 expected technical indicators."""
        resp = await async_client.get("/api/strategy")
        data = resp.json()
        indicators = data["indicators"]
        assert len(indicators) == 6
        names = [i["name"] for i in indicators]
        assert "SMA(20)" in names
        assert "SMA(50)" in names
        assert "EMA(20)" in names
        assert "EMA(50)" in names
        assert "RSI(14)" in names
        assert "Volume" in names

    @pytest.mark.asyncio
    async def test_strategy_risk_parameters(self, async_client):
        """Verify strategy returns risk parameters with expected keys."""
        resp = await async_client.get("/api/strategy")
        data = resp.json()
        risk = data["risk_parameters"]
        assert "max_position_size_pct" in risk
        assert "stop_loss_pct" in risk
        assert "take_profit_pct" in risk
        assert "symbols_tracked" in risk
        assert "mock_mode" in risk
        assert isinstance(risk["symbols_tracked"], list)
        assert len(risk["symbols_tracked"]) > 0

    @pytest.mark.asyncio
    async def test_strategy_decision_fields(self, async_client):
        """Verify strategy returns decision fields for BUY/SELL/HOLD."""
        resp = await async_client.get("/api/strategy")
        data = resp.json()
        fields = data["decision_fields"]
        assert "action" in fields
        assert "confidence" in fields
        assert "reasoning" in fields
        assert "take_profit" in fields
        assert "stop_loss" in fields
        assert "position_size_pct" in fields

    @pytest.mark.asyncio
    async def test_strategy_model_info(self, async_client):
        """Verify strategy returns model configuration."""
        resp = await async_client.get("/api/strategy")
        data = resp.json()
        model = data["model"]
        assert model["provider"] == "DeepSeek"
        assert "model_name" in model
        assert "temperature" in model
        assert "max_tokens" in model

    @pytest.mark.asyncio
    async def test_strategy_prompt_template(self, async_client):
        """Verify prompt template contains expected indicator placeholders."""
        resp = await async_client.get("/api/strategy")
        data = resp.json()
        prompt = data["prompt_template"]
        assert "SMA(20)" in prompt
        assert "RSI(14)" in prompt
        assert "BUY" in prompt
        assert "SELL" in prompt
        assert "HOLD" in prompt
        assert "position_size_pct" in prompt

    @pytest.mark.asyncio
    async def test_strategy_mock_fallback(self, async_client):
        """Verify mock fallback logic is present when in mock mode."""
        resp = await async_client.get("/api/strategy")
        data = resp.json()
        fallback = data["mock_fallback_logic"]
        assert isinstance(fallback, list)
        assert len(fallback) > 0
        assert any("RSI" in rule for rule in fallback)


class TestAPIBacktest:
    """Tests for backtest endpoints."""

    @pytest.mark.asyncio
    async def test_run_backtest(self, async_client):
        """Verify POST /api/backtest/run returns a backtest result."""
        payload = {
            "symbol": "AAPL",
            "start_date": "2025-01-01",
            "end_date": "2025-01-10",
            "initial_capital": 100_000.0,
        }
        resp = await async_client.post("/api/backtest/run", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        result = data["result"]
        assert result["symbol"] == "AAPL"
        assert "total_trades" in result
        assert "sharpe_ratio" in result

    @pytest.mark.asyncio
    async def test_get_backtest_results(self, async_client):
        """Verify GET /api/backtest/results returns a list."""
        resp = await async_client.get("/api/backtest/results")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
