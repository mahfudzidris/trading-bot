"""Tests for data/twelvedata_client.py — TwelveDataClient."""

from __future__ import annotations

import numpy as np
import pytest
import pytest_asyncio


class TestTwelveDataClient:
    """Tests for TwelveDataClient in mock mode."""

    @pytest.mark.asyncio
    async def test_get_stock_quote(self, mock_twelvedata_client):
        """Verify get_stock_quote returns expected keys in mock mode."""
        quote = await mock_twelvedata_client.get_stock_quote("AAPL")
        assert quote["symbol"] == "AAPL"
        assert "price" in quote
        assert "change" in quote
        assert "change_pct" in quote
        assert "volume" in quote
        assert "timestamp" in quote
        assert isinstance(quote["price"], float)
        assert quote["price"] > 0

    @pytest.mark.asyncio
    async def test_get_stock_quote_unknown_symbol(self, mock_twelvedata_client):
        """Verify fallback base price for unknown symbols."""
        quote = await mock_twelvedata_client.get_stock_quote("UNKN")
        assert quote["symbol"] == "UNKN"
        assert quote["price"] > 0  # Should use default 100.0

    @pytest.mark.asyncio
    async def test_get_time_series(self, mock_twelvedata_client):
        """Verify get_time_series returns a list of OHLCV bars."""
        series = await mock_twelvedata_client.get_time_series("AAPL", outputsize=10)
        assert len(series) == 10
        for bar in series:
            assert "datetime" in bar
            assert "open" in bar
            assert "high" in bar
            assert "low" in bar
            assert "close" in bar
            assert "volume" in bar

    @pytest.mark.asyncio
    async def test_get_quote_with_indicators(self, mock_twelvedata_client):
        """Verify get_quote_with_indicators returns indicators with expected keys."""
        ind = await mock_twelvedata_client.get_quote_with_indicators("MSFT")
        assert ind["symbol"] == "MSFT"
        assert "price" in ind
        assert "sma_20" in ind
        assert "sma_50" in ind
        assert "ema_20" in ind
        assert "ema_50" in ind
        assert "rsi_14" in ind
        assert "volume" in ind
        assert ind["sma_20"] > 0
        assert ind["rsi_14"] >= 0

    @pytest.mark.asyncio
    async def test_mock_time_series_different_symbols(self, mock_twelvedata_client):
        """Verify different symbols produce different price series."""
        aapl = await mock_twelvedata_client.get_time_series("AAPL", outputsize=5)
        tsla = await mock_twelvedata_client.get_time_series("TSLA", outputsize=5)
        assert len(aapl) == 5
        assert len(tsla) == 5
        # Prices should differ (different base prices)
        assert aapl[-1]["close"] != tsla[-1]["close"]

    @pytest.mark.asyncio
    async def test_empty_symbol(self, mock_twelvedata_client):
        """Verify empty symbol returns a fallback quote."""
        quote = await mock_twelvedata_client.get_stock_quote("")
        assert quote["price"] > 0

    def test_static_rsi(self):
        """Test _rsi static method with known values."""
        prices = np.array([100, 101, 102, 103, 102, 101, 100, 99, 100, 101,
                           102, 103, 104, 103, 105], dtype=float)
        from data.twelvedata_client import TwelveDataClient
        rsi = TwelveDataClient._rsi(prices, period=14)
        assert isinstance(rsi, float)
        assert 0 <= rsi <= 100

    def test_static_sma(self):
        """Test _sma static method."""
        prices = np.array([10, 20, 30, 40, 50], dtype=float)
        from data.twelvedata_client import TwelveDataClient
        sma = TwelveDataClient._sma(prices, period=3)
        # Last 3 values: 30, 40, 50 => avg 40
        assert sma == 40.0

    def test_static_ema(self):
        """Test _ema static method."""
        prices = np.array([10, 20, 30, 40, 50], dtype=float)
        from data.twelvedata_client import TwelveDataClient
        ema = TwelveDataClient._ema(prices, period=3)
        assert isinstance(ema, float)
        assert ema > 0

    def test_static_mock_price(self):
        """Test _mock_price static method produces reasonable values."""
        from data.twelvedata_client import TwelveDataClient
        price = TwelveDataClient._mock_price(150.0)
        assert isinstance(price, float)
        # Should be within reasonable range of base
        assert 130 < price < 170

    def test_static_random_walk(self):
        """Test _random_walk static method with seed."""
        from data.twelvedata_client import TwelveDataClient
        walk1 = TwelveDataClient._random_walk(10, start=100.0, seed=42)
        walk2 = TwelveDataClient._random_walk(10, start=100.0, seed=42)
        assert len(walk1) == 10
        assert np.array_equal(walk1, walk2)  # Deterministic with same seed

    def test_static_random_walk_no_seed(self):
        """Test _random_walk without seed produces different results."""
        from data.twelvedata_client import TwelveDataClient
        walk1 = TwelveDataClient._random_walk(10, start=100.0)
        walk2 = TwelveDataClient._random_walk(10, start=100.0)
        # Without seed, they should differ (very high probability)
        assert not np.array_equal(walk1, walk2)

    @pytest.mark.asyncio
    async def test_close(self, mock_twelvedata_client):
        """Verify close method works."""
        await mock_twelvedata_client.close()
        # No exception means success
