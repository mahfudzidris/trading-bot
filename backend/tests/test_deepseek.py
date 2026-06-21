"""Tests for ai/deepseek_analyzer.py — DeepSeekAnalyzer."""

from __future__ import annotations

import pytest
import pytest_asyncio


class TestDeepSeekAnalyzer:
    """Tests for DeepSeekAnalyzer in mock mode."""

    @pytest.mark.asyncio
    async def test_analyze_market_returns_decision(self, mock_deepseek_analyzer):
        """Verify analyze_market returns a dict with the expected keys."""
        price_data = {"price": 180.0, "change_pct": 1.5, "volume": 10_000_000, "timestamp": "2025-01-15T10:00:00"}
        indicators = {"price": 180.0, "sma_20": 178.0, "sma_50": 175.0, "ema_20": 179.0, "ema_50": 176.0, "rsi_14": 55, "volume": 10_000_000}
        decision = await mock_deepseek_analyzer.analyze_market("AAPL", price_data, indicators)
        assert isinstance(decision, dict)
        assert "action" in decision
        assert "confidence" in decision
        assert "reasoning" in decision
        assert "take_profit" in decision
        assert "stop_loss" in decision
        assert "position_size_pct" in decision

    @pytest.mark.asyncio
    async def test_analyze_market_action_types(self, mock_deepseek_analyzer):
        """Verify action is one of BUY, SELL, or HOLD."""
        price_data = {"price": 100.0, "change_pct": 0.0, "volume": 1_000_000, "timestamp": "2025-01-15T10:00:00"}
        indicators = {"price": 100.0, "sma_20": 100.0, "sma_50": 100.0, "ema_20": 100.0, "ema_50": 100.0, "rsi_14": 50, "volume": 1_000_000}
        decision = await mock_deepseek_analyzer.analyze_market("AAPL", price_data, indicators)
        assert decision["action"] in ("BUY", "SELL", "HOLD")

    @pytest.mark.asyncio
    async def test_analyze_market_confidence_range(self, mock_deepseek_analyzer):
        """Verify confidence is an integer between 0 and 100."""
        price_data = {"price": 150.0, "change_pct": -2.0, "volume": 5_000_000, "timestamp": "now"}
        indicators = {"price": 150.0, "sma_20": 148.0, "sma_50": 145.0, "ema_20": 149.0, "ema_50": 146.0, "rsi_14": 45, "volume": 5_000_000}
        decision = await mock_deepseek_analyzer.analyze_market("AAPL", price_data, indicators)
        assert isinstance(decision["confidence"], int)
        assert 0 <= decision["confidence"] <= 100

    @pytest.mark.asyncio
    async def test_analyze_market_rsi_oversold(self, mock_deepseek_analyzer):
        """Verify RSI < 30 triggers BUY signal."""
        price_data = {"price": 150.0, "change_pct": -3.0, "volume": 8_000_000, "timestamp": "now"}
        indicators = {"price": 150.0, "sma_20": 152.0, "sma_50": 155.0, "ema_20": 151.0, "ema_50": 154.0, "rsi_14": 25, "volume": 8_000_000}
        decision = await mock_deepseek_analyzer.analyze_market("AAPL", price_data, indicators)
        assert decision["action"] == "BUY"
        assert decision["stop_loss"] > 0
        assert decision["take_profit"] > 0
        assert decision["position_size_pct"] > 0

    @pytest.mark.asyncio
    async def test_analyze_market_rsi_overbought(self, mock_deepseek_analyzer):
        """Verify RSI > 70 triggers SELL signal."""
        price_data = {"price": 200.0, "change_pct": 5.0, "volume": 15_000_000, "timestamp": "now"}
        indicators = {"price": 200.0, "sma_20": 190.0, "sma_50": 185.0, "ema_20": 195.0, "ema_50": 188.0, "rsi_14": 75, "volume": 15_000_000}
        decision = await mock_deepseek_analyzer.analyze_market("AAPL", price_data, indicators)
        assert decision["action"] == "SELL"

    def test_build_prompt_contains_sections(self, mock_deepseek_analyzer):
        """Verify build_prompt contains expected sections."""
        price_data = {"price": 180.0, "change_pct": 1.2, "volume": 10_000_000, "timestamp": "2025-01-15"}
        indicators = {"price": 180.0, "sma_20": 178.0, "sma_50": 175.0, "ema_20": 179.0, "ema_50": 176.0, "rsi_14": 55, "volume": 10_000_000}
        prompt = mock_deepseek_analyzer.build_prompt("AAPL", price_data, indicators)
        assert "PRICE DATA" in prompt
        assert "TECHNICAL INDICATORS" in prompt
        assert "MARKET CONTEXT" in prompt
        assert "AAPL" in prompt
        assert "action" in prompt
        assert "confidence" in prompt
        assert "reasoning" in prompt

    def test_build_prompt_without_indicators(self, mock_deepseek_analyzer):
        """Verify build_prompt handles missing indicator keys gracefully."""
        price_data = {"price": 180.0, "change_pct": 0.0, "volume": 0, "timestamp": ""}
        indicators = {}
        prompt = mock_deepseek_analyzer.build_prompt("AAPL", price_data, indicators)
        assert "N/A" in prompt or "$" in prompt

    @pytest.mark.asyncio
    async def test_analyze_portfolio(self, mock_deepseek_analyzer):
        """Verify analyze_portfolio returns per-position decisions."""
        holdings = [
            {"symbol": "AAPL", "qty": 10, "unrealized_pl": 50.0},
            {"symbol": "TSLA", "qty": 5, "unrealized_pl": -20.0},
        ]
        market_data = {
            "AAPL": {"price": 180.0, "sma_20": 178.0, "sma_50": 175.0, "rsi_14": 55, "volume": 10_000_000},
            "TSLA": {"price": 250.0, "sma_20": 248.0, "sma_50": 245.0, "rsi_14": 60, "volume": 5_000_000},
        }
        results = await mock_deepseek_analyzer.analyze_portfolio(holdings, market_data)
        assert len(results) == 2
        for r in results:
            assert "symbol" in r
            assert "current_qty" in r
            assert "unrealized_pnl" in r
            assert "action" in r

    @pytest.mark.asyncio
    async def test_close(self, mock_deepseek_analyzer):
        """Verify close method works."""
        await mock_deepseek_analyzer.close()
