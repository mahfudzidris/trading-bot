"""Abstract base class for trading strategies.

Each strategy analyses technical indicators and returns a signal:
BUY, SELL, or HOLD with a confidence score and reasoning.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Signal:
    """A single strategy signal result."""

    def __init__(
        self,
        name: str,
        signal: str,  # "BUY" | "SELL" | "HOLD"
        confidence: int,  # 0-100
        reasoning: str,
    ) -> None:
        self.name = name
        self.signal = signal
        self.confidence = max(0, min(100, confidence))
        self.reasoning = reasoning

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "signal": self.signal,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
        }


class BaseStrategy(ABC):
    """Abstract strategy that analyses indicators and returns a Signal."""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def analyze(self, indicators: dict[str, Any]) -> Signal:
        """Analyse the given technical indicators and return a trading signal."""
        ...
