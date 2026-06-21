"""Momentum Strategy — based on price rate of change (ROC).

Signals:
- BUY when price change % is strong positive (>1.5%)
- SELL when price change % is strong negative (<-1.5%)
- HOLD when momentum is weak / flat
- Confidence proportional to momentum strength.
"""

from __future__ import annotations

from typing import Any

from .base import BaseStrategy, Signal


class MomentumStrategy(BaseStrategy):
    """Momentum trading using price rate of change."""

    @property
    def name(self) -> str:
        return "Momentum"

    def analyze(self, indicators: dict[str, Any]) -> Signal:
        price = indicators.get("price", 0)
        change_pct = indicators.get("change_pct", 0)
        volume = indicators.get("volume", 0)

        if not price:
            return Signal(self.name, "HOLD", 50, "Insufficient price data for momentum analysis")

        # Use both change_pct and SMA gap as momentum indicators
        sma_20 = indicators.get("sma_20", price)
        sma_gap_pct = ((price / sma_20) - 1) * 100 if sma_20 and sma_20 > 0 else 0

        momentum_score = change_pct + sma_gap_pct  # rough composite momentum

        # Volume confirmation
        avg_vol = 5_000_000
        volume_boost = 0
        if volume > avg_vol * 1.5:
            volume_boost = 10
        elif volume < avg_vol * 0.5:
            volume_boost = -5

        # Strong positive momentum
        if momentum_score > 2.0:
            confidence = min(90, 65 + int(abs(momentum_score) * 3) + volume_boost)
            return Signal(
                self.name, "BUY", confidence,
                f"Strong upward momentum: +{change_pct:.2f}% today, "
                f"{sma_gap_pct:+.2f}% above SMA(20). "
                f"{'Volume confirms' if volume_boost > 0 else 'Volume moderate'}. "
                f"Composite momentum score: {momentum_score:.1f}",
            )

        if momentum_score > 0.8:
            confidence = 55 + volume_boost
            return Signal(
                self.name, "BUY", confidence,
                f"Mild upward momentum: +{change_pct:.2f}% today, "
                f"{sma_gap_pct:+.2f}% vs SMA(20). Waiting for confirmation.",
            )

        # Strong negative momentum
        if momentum_score < -2.0:
            confidence = min(90, 65 + int(abs(momentum_score) * 3) + volume_boost)
            return Signal(
                self.name, "SELL", confidence,
                f"Strong downward momentum: {change_pct:.2f}% today, "
                f"{sma_gap_pct:+.2f}% below SMA(20). "
                f"{'Volume confirms' if volume_boost > 0 else 'Volume moderate'}. "
                f"Composite momentum score: {momentum_score:.1f}",
            )

        if momentum_score < -0.8:
            confidence = 55 + volume_boost
            return Signal(
                self.name, "SELL", confidence,
                f"Mild downward momentum: {change_pct:.2f}% today, "
                f"{sma_gap_pct:+.2f}% vs SMA(20). Waiting for confirmation.",
            )

        # Weak / flat
        direction = "slightly bullish" if momentum_score > 0 else "slightly bearish" if momentum_score < 0 else "flat"
        return Signal(
            self.name, "HOLD", 50,
            f"Momentum {direction}: {change_pct:+.2f}% daily change, "
            f"{sma_gap_pct:+.2f}% vs SMA(20). Score: {momentum_score:.1f}",
        )
