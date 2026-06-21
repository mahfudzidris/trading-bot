"""Trend Following Strategy — based on SMA crossover analysis.

Signals:
- BUY when price > SMA(20) > SMA(50) (bullish alignment)
- SELL when price < SMA(20) < SMA(50) (bearish alignment)
- Confidence adjusted by gap magnitude between SMAs.
"""

from __future__ import annotations

from typing import Any

from .base import BaseStrategy, Signal


class TrendFollowingStrategy(BaseStrategy):
    """Trend following using SMA crossover detection."""

    @property
    def name(self) -> str:
        return "Trend Following"

    def analyze(self, indicators: dict[str, Any]) -> Signal:
        price = indicators.get("price", 0)
        sma_20 = indicators.get("sma_20", price)
        sma_50 = indicators.get("sma_50", price)

        if not price or not sma_20 or not sma_50:
            return Signal(self.name, "HOLD", 50, "Insufficient data for trend analysis")

        # Bullish: price > SMA(20) > SMA(50)
        if sma_20 > sma_50 and price > sma_20:
            gap_pct = abs(sma_20 - sma_50) / sma_50 * 100
            confidence = min(95, 65 + int(gap_pct * 2))
            return Signal(
                self.name, "BUY", confidence,
                f"Bullish trend: price ${price:.2f} above rising SMA(20) ${sma_20:.2f} and SMA(50) ${sma_50:.2f}",
            )

        # Bearish: price < SMA(20) < SMA(50)
        if sma_20 < sma_50 and price < sma_20:
            gap_pct = abs(sma_20 - sma_50) / sma_50 * 100
            confidence = min(95, 65 + int(gap_pct * 2))
            return Signal(
                self.name, "SELL", confidence,
                f"Bearish trend: price ${price:.2f} below falling SMA(20) ${sma_20:.2f} and SMA(50) ${sma_50:.2f}",
            )

        # Mixed / no clear trend
        if sma_20 > sma_50:
            return Signal(self.name, "BUY", 55, "SMA(20) above SMA(50) but price near SMA(20) — cautiously bullish")
        if sma_20 < sma_50:
            return Signal(self.name, "SELL", 55, "SMA(20) below SMA(50) but price near SMA(20) — cautiously bearish")

        return Signal(self.name, "HOLD", 50, "SMAs converging — no clear trend direction")
