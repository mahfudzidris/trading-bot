"""Tests for broker/alpaca_client.py — AlpacaClient."""

from __future__ import annotations

import pytest
import pytest_asyncio


class TestAlpacaClient:
    """Tests for AlpacaClient in mock mode."""

    @pytest.mark.asyncio
    async def test_get_account(self, mock_alpaca_client):
        """Verify get_account returns balance, buying_power, pnl, portfolio_value, status."""
        account = await mock_alpaca_client.get_account()
        assert "balance" in account
        assert "cash" in account
        assert "buying_power" in account
        assert "pnl" in account
        assert "portfolio_value" in account
        assert "status" in account
        assert account["balance"] > 0
        assert account["buying_power"] > 0
        assert account["status"] == "ACTIVE"

    @pytest.mark.asyncio
    async def test_get_positions(self, mock_alpaca_client):
        """Verify get_positions returns a list of positions with expected keys."""
        positions = await mock_alpaca_client.get_positions()
        assert isinstance(positions, list)
        for pos in positions:
            assert "symbol" in pos
            assert "qty" in pos
            assert "avg_entry_price" in pos
            assert "current_price" in pos
            assert "market_value" in pos
            assert "unrealized_pl" in pos

    @pytest.mark.asyncio
    async def test_place_market_order_buy(self, mock_alpaca_client):
        """Verify place_market_order returns order with id, symbol, qty, side, status."""
        order = await mock_alpaca_client.place_market_order("AAPL", 10, "BUY")
        assert "id" in order
        assert order["symbol"] == "AAPL"
        assert order["qty"] == 10
        assert order["side"] == "BUY"
        assert order["status"] == "filled"
        assert "filled_avg_price" in order

    @pytest.mark.asyncio
    async def test_place_market_order_sell(self, mock_alpaca_client):
        """Verify place_market_order with SELL side."""
        order = await mock_alpaca_client.place_market_order("TSLA", 5, "SELL")
        assert order["symbol"] == "TSLA"
        assert order["qty"] == 5
        assert order["side"] == "SELL"
        assert order["status"] == "filled"

    @pytest.mark.asyncio
    async def test_get_clock(self, mock_alpaca_client):
        """Verify get_clock returns is_open, next_open, next_close."""
        clock = await mock_alpaca_client.get_clock()
        assert "is_open" in clock
        assert "next_open" in clock
        assert "next_close" in clock
        assert "timestamp" in clock
        assert isinstance(clock["is_open"], bool)

    @pytest.mark.asyncio
    async def test_close_position(self, mock_alpaca_client):
        """Verify close_position returns status dict."""
        # First, ensure we have a position (may be seeded)
        result = await mock_alpaca_client.close_position("AAPL")
        assert "symbol" in result
        assert "qty" in result
        assert "status" in result

    @pytest.mark.asyncio
    async def test_close_position_no_position(self, mock_alpaca_client):
        """Verify close_position on non-existent symbol returns no_position status."""
        result = await mock_alpaca_client.close_position("NONEXISTENT")
        assert result["status"] in ("no_position", "closed")

    @pytest.mark.asyncio
    async def test_place_limit_order(self, mock_alpaca_client):
        """Verify place_limit_order returns order with limit price."""
        order = await mock_alpaca_client.place_limit_order("MSFT", 10, "BUY", 380.0)
        assert order["type"] == "limit"
        assert order["limit_price"] == 380.0
        assert order["status"] == "accepted"

    @pytest.mark.asyncio
    async def test_place_stop_order(self, mock_alpaca_client):
        """Verify place_stop_order returns order with stop price."""
        order = await mock_alpaca_client.place_stop_order("AAPL", 10, "SELL", 170.0)
        assert order["type"] == "stop"
        assert order["stop_price"] == 170.0
        assert order["status"] == "accepted"

    @pytest.mark.asyncio
    async def test_get_bars(self, mock_alpaca_client):
        """Verify get_bars returns a list of OHLCV bars."""
        bars = await mock_alpaca_client.get_bars("AAPL", timeframe="1Day", limit=5)
        assert len(bars) == 5
        for bar in bars:
            assert "timestamp" in bar
            assert "open" in bar
            assert "high" in bar
            assert "low" in bar
            assert "close" in bar
            assert "volume" in bar

    @pytest.mark.asyncio
    async def test_order_updates_mock_position(self, mock_alpaca_client):
        """Verify placing a buy order adds to mock positions."""
        # Place a buy order for a symbol we don't already hold
        await mock_alpaca_client.place_market_order("META", 20, "BUY")
        positions = await mock_alpaca_client.get_positions()
        meta_pos = [p for p in positions if p["symbol"] == "META"]
        assert len(meta_pos) > 0
        assert meta_pos[0]["qty"] == 20

    @pytest.mark.asyncio
    async def test_close(self, mock_alpaca_client):
        """Verify close method works."""
        await mock_alpaca_client.close()
