"""Tests for config.py — Settings validation."""

from __future__ import annotations

from config import Settings


class TestSettings:
    """Test the Settings class from config.py."""

    def test_default_values(self, monkeypatch):
        """Verify default values are set correctly (isolated from .env)."""
        # Clear any env vars that might be set
        monkeypatch.delenv("MOCK_MODE", raising=False)
        monkeypatch.delenv("PORT", raising=False)
        s = Settings(_env_file=None)  # Don't read .env
        assert s.MOCK_MODE is True
        assert s.PORT == 8000
        assert "AAPL" in s.SYMBOLS
        assert s.TRADE_MAX_POSITION_SIZE == 0.1
        assert s.ALPACA_PAPER is True
        assert s.TRADE_STOP_LOSS_PCT == 0.02
        assert s.TRADE_TAKE_PROFIT_PCT == 0.05

    def test_env_override(self, monkeypatch):
        """Verify environment variables override defaults."""
        monkeypatch.setenv("MOCK_MODE", "false")
        monkeypatch.setenv("PORT", "9000")
        monkeypatch.setenv("SYMBOLS", '["SPY", "QQQ"]')
        s = Settings()
        assert s.MOCK_MODE is False
        assert s.PORT == 9000

    def test_symbols_list(self):
        """Verify SYMBOLS is a list of strings with at least 5 entries."""
        s = Settings()
        assert len(s.SYMBOLS) >= 5
        assert all(isinstance(sym, str) for sym in s.SYMBOLS)

    def test_model_config(self):
        """Verify model_config has env_file set."""
        s = Settings()
        assert s.model_config.get("env_file") == ".env"

    def test_trading_params_types(self):
        """Verify trading parameters have correct types."""
        s = Settings()
        assert isinstance(s.TRADE_MAX_POSITION_SIZE, float)
        assert isinstance(s.TRADE_STOP_LOSS_PCT, float)
        assert isinstance(s.TRADE_TAKE_PROFIT_PCT, float)
        assert isinstance(s.PORT, int)
        assert isinstance(s.ALPACA_PAPER, bool)
        assert isinstance(s.MOCK_MODE, bool)
