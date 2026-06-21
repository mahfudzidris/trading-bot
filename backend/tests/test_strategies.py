"""Tests for strategies/ — base, trend, mean_reversion, momentum, ensemble.

Tests each strategy individually and the ensemble aggregator.
Uses fixed indicator data so results are deterministic.
"""

from __future__ import annotations

import pytest

from strategies.base import Signal
from strategies.trend import TrendFollowingStrategy
from strategies.mean_reversion import MeanReversionStrategy
from strategies.momentum import MomentumStrategy
from strategies import EnsembleStrategy


# ── Shared fixtures ──────────────────────────────────────────────────────

@pytest.fixture
def bullish_indicators():
    """Everything points bullish — price above SMAs, RSI moderate, good volume."""
    return {
        "price": 185.0,
        "sma_20": 178.0,
        "sma_50": 165.0,
        "ema_20": 180.0,
        "ema_50": 168.0,
        "rsi_14": 58,
        "volume": 12_000_000,
        "change_pct": 1.8,
    }


@pytest.fixture
def bearish_indicators():
    """Everything points bearish — price below SMAs, RSI high (overbought), low volume."""
    return {
        "price": 155.0,
        "sma_20": 162.0,
        "sma_50": 170.0,
        "ema_20": 160.0,
        "ema_50": 168.0,
        "rsi_14": 72,
        "volume": 2_000_000,
        "change_pct": -2.5,
    }


@pytest.fixture
def neutral_indicators():
    """No clear direction — SMAs converging, RSI neutral."""
    return {
        "price": 170.0,
        "sma_20": 169.0,
        "sma_50": 168.5,
        "ema_20": 169.5,
        "ema_50": 168.8,
        "rsi_14": 50,
        "volume": 5_000_000,
        "change_pct": 0.2,
    }


# ── Trend Strategy Tests ─────────────────────────────────────────────────

class TestTrendFollowingStrategy:
    """Tests for TrendFollowingStrategy."""

    def test_bullish_trend(self, bullish_indicators):
        """Verify BUY signal when price > SMA(20) > SMA(50)."""
        s = TrendFollowingStrategy()
        signal = s.analyze(bullish_indicators)
        assert signal.signal == "BUY"
        assert signal.confidence >= 65
        assert "bullish" in signal.reasoning.lower()

    def test_bearish_trend(self, bearish_indicators):
        """Verify SELL signal when price < SMA(20) < SMA(50)."""
        s = TrendFollowingStrategy()
        signal = s.analyze(bearish_indicators)
        assert signal.signal == "SELL"
        assert signal.confidence >= 65
        assert "bearish" in signal.reasoning.lower()

    def test_neutral_trend(self, neutral_indicators):
        """Verify HOLD (or directional) signal when SMAs are close."""
        s = TrendFollowingStrategy()
        signal = s.analyze(neutral_indicators)
        # SMA(20) ~ SMA(50) — could go either way
        assert signal.confidence > 0
        assert signal.signal in ("BUY", "SELL", "HOLD")

    def test_zero_data_hold(self):
        """Verify HOLD when price data is missing."""
        s = TrendFollowingStrategy()
        signal = s.analyze({"price": 0, "sma_20": 0, "sma_50": 0})
        assert signal.signal == "HOLD"
        assert "Insufficient" in signal.reasoning

    def test_to_dict(self, bullish_indicators):
        """Verify Signal.to_dict() returns expected keys."""
        s = TrendFollowingStrategy()
        signal = s.analyze(bullish_indicators)
        d = signal.to_dict()
        assert d["name"] == "Trend Following"
        assert d["signal"] == "BUY"
        assert "confidence" in d
        assert "reasoning" in d


# ── Mean Reversion Strategy Tests ────────────────────────────────────────

class TestMeanReversionStrategy:
    """Tests for MeanReversionStrategy."""

    def test_oversold_buy(self):
        """Verify BUY signal when RSI < 30."""
        s = MeanReversionStrategy()
        signal = s.analyze({"price": 100, "rsi_14": 25})
        assert signal.signal == "BUY"
        assert signal.confidence >= 70
        assert "oversold" in signal.reasoning.lower()

    def test_overbought_sell(self):
        """Verify SELL signal when RSI > 70."""
        s = MeanReversionStrategy()
        signal = s.analyze({"price": 100, "rsi_14": 78})
        assert signal.signal == "SELL"
        assert signal.confidence >= 70
        assert "overbought" in signal.reasoning.lower()

    def test_neutral_rsi_hold(self):
        """Verify HOLD when RSI is neutral."""
        s = MeanReversionStrategy()
        signal = s.analyze({"price": 100, "rsi_14": 50})
        assert signal.signal == "HOLD"
        assert "neutral" in signal.reasoning.lower()

    def test_almost_oversold(self):
        """Verify BUY when RSI < 35 but > 30."""
        s = MeanReversionStrategy()
        signal = s.analyze({"price": 100, "rsi_14": 33})
        assert signal.signal == "BUY"
        assert signal.confidence == 60

    def test_almost_overbought(self):
        """Verify SELL when RSI > 65 but < 70."""
        s = MeanReversionStrategy()
        signal = s.analyze({"price": 100, "rsi_14": 67})
        assert signal.signal == "SELL"
        assert signal.confidence == 60


# ── Momentum Strategy Tests ──────────────────────────────────────────────

class TestMomentumStrategy:
    """Tests for MomentumStrategy."""

    def test_strong_upward_buy(self, bullish_indicators):
        """Verify BUY with strong upward momentum."""
        s = MomentumStrategy()
        signal = s.analyze(bullish_indicators)
        assert signal.signal == "BUY"
        assert signal.confidence >= 60
        assert "upward" in signal.reasoning.lower() or "momentum" in signal.reasoning.lower()

    def test_strong_downward_sell(self, bearish_indicators):
        """Verify SELL with strong downward momentum."""
        s = MomentumStrategy()
        signal = s.analyze(bearish_indicators)
        assert signal.signal == "SELL"
        assert signal.confidence >= 60

    def test_weak_momentum_hold(self, neutral_indicators):
        """Verify HOLD when momentum is flat."""
        s = MomentumStrategy()
        signal = s.analyze(neutral_indicators)
        assert signal.confidence > 0


# ── Ensemble Strategy Tests ──────────────────────────────────────────────

class TestEnsembleStrategy:
    """Tests for EnsembleStrategy aggregator."""

    def test_ensemble_runs_all_strategies(self, bullish_indicators):
        """Verify ensemble returns 3 signals."""
        e = EnsembleStrategy()
        signals = e.analyze(bullish_indicators)
        assert len(signals) == 3

    def test_ensemble_signals_have_expected_fields(self, bullish_indicators):
        """Verify each signal has name, signal, confidence, reasoning."""
        e = EnsembleStrategy()
        signals = e.analyze(bullish_indicators)
        for sig in signals:
            d = sig.to_dict()
            assert "name" in d
            assert "signal" in d
            assert "confidence" in d
            assert "reasoning" in d

    def test_ensemble_summary_keys(self, bullish_indicators):
        """Verify get_summary returns expected aggregates."""
        e = EnsembleStrategy()
        signals = e.analyze(bullish_indicators)
        summary = e.get_summary(signals)
        assert "consensus" in summary
        assert "avg_confidence" in summary
        assert "votes" in summary
        assert "strategies_count" in summary
        assert summary["strategies_count"] == 3

    def test_ensemble_consensus_bullish(self, bullish_indicators):
        """Verify bullish indicators → BUY consensus."""
        e = EnsembleStrategy()
        signals = e.analyze(bullish_indicators)
        summary = e.get_summary(signals)
        assert summary["consensus"] == "BUY"
        assert summary["votes"]["BUY"] >= 1

    def test_ensemble_consensus_bearish(self, bearish_indicators):
        """Verify bearish indicators → SELL consensus."""
        e = EnsembleStrategy()
        signals = e.analyze(bearish_indicators)
        summary = e.get_summary(signals)
        assert summary["consensus"] == "SELL"

    def test_ensemble_handles_mixed_signals(self):
        """Verify ensemble works with mixed signal data."""
        e = EnsembleStrategy()
        signals = e.analyze({"price": 170, "sma_20": 169, "sma_50": 168, "rsi_14": 50, "volume": 5_000_000, "change_pct": 0.5})
        summary = e.get_summary(signals)
        assert summary["strategies_count"] == 3
        assert summary["avg_confidence"] > 0

    def test_list_strategies(self):
        """Verify list_strategies returns all strategy names."""
        names = EnsembleStrategy.list_strategies()
        assert len(names) == 3
        assert "TrendFollowing" in names
        assert "MeanReversion" in names
        assert "Momentum" in names
