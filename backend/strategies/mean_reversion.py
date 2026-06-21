"""Mean Reversion Strategy — based on RSI oversold/overbought levels.

Signals:
- BUY when RSI < 35 (oversold — price likely to bounce)
- SELL when RSI > 65 (overbought — price likely to drop)
- HOLD when RSI in neutral zone (35-65)
- Confidence increases the further RSI is from neutral.
"""

from __future__ import annotations

from typing import Any

from .base import BaseStrategy, Signal


class MeanReversionStrategy(BaseStrategy):
    """Mean reversion trading using RSI extremes."""

    @property
    def name(self) -> str:
        return "Mean Reversion"

    def analyze(self, indicators: dict[str, Any]) -> Signal:
        price = indicators.get("price", 0)
        rsi = indicators.get("rsi_14", 50)

        if not price or rsi is None:
            return Signal(self.name, "HOLD", 50, "Insufficient data for mean reversion analysis")

        # Oversold — potential bounce
        if rsi < 30:
            confidence = min(90, 70 + int((30 - rsi) * 2))
            return Signal(
                self.name, "BUY", confidence,
                f"Oversold: RSI at {rsi:.1f} — price may revert upward from ${price:.2f}",
            )

        if rsi < 35:
            return Signal(
                self.name, "BUY", 60,
                f"RSI at {rsi:.1f} approaching oversold zone — watch for bounce",
            )

        # Overbought — potential drop
        if rsi > 70:
            confidence = min(90, 70 + int((rsi - 70) * 2))
            return Signal(
                self.name, "SELL", confidence,
                f"Overbought: RSI at {rsi:.1f} — price may revert downward from ${price:.2f}",
            )

        if rsi > 65:
            return Signal(
                self.name, "SELL", 60,
                f"RSI at {rsi:.1f} approaching overbought zone — watch for drop",
            )

        # Neutral
        return Signal(self.name, "HOLD", 50, f"RSI at {rsi:.1f} in neutral zone — no reversal signal")
