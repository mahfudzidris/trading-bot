"""Ensemble Strategy Runner — runs all strategies and aggregates signals.

Usage:
    ensemble = EnsembleStrategy()
    signals = ensemble.analyze(indicators)
    # → [Signal, Signal, Signal]

    summary = ensemble.get_summary(signals)
    # → {"votes": {"BUY": 2, "SELL": 0, "HOLD": 1},
    #     "avg_confidence": 74,
    #     "consensus": "BUY"}
"""

from __future__ import annotations

from typing import Any

from .base import BaseStrategy, Signal
from .trend import TrendFollowingStrategy
from .mean_reversion import MeanReversionStrategy
from .momentum import MomentumStrategy


# Registry of all strategies — add new ones here
_DEFAULT_STRATEGIES: list[type[BaseStrategy]] = [
    TrendFollowingStrategy,
    MeanReversionStrategy,
    MomentumStrategy,
]


class EnsembleStrategy:
    """Runs multiple strategies and produces an aggregated summary."""

    def __init__(self, strategies: list[BaseStrategy] | None = None) -> None:
        self.strategies: list[BaseStrategy] = strategies or [cls() for cls in _DEFAULT_STRATEGIES]

    def analyze(self, indicators: dict[str, Any]) -> list[Signal]:
        """Run all strategies and return a list of Signals."""
        return [s.analyze(indicators) for s in self.strategies]

    def get_summary(self, signals: list[Signal]) -> dict[str, Any]:
        """Aggregate signals into consensus summary."""
        votes: dict[str, int] = {"BUY": 0, "SELL": 0, "HOLD": 0}
        total_conf = 0
        details: list[dict[str, Any]] = []

        for sig in signals:
            votes[sig.signal] = votes.get(sig.signal, 0) + 1
            total_conf += sig.confidence
            details.append(sig.to_dict())

        avg_conf = total_conf // len(signals) if signals else 0

        # Determine consensus (exclude HOLD from tie-breaking)
        non_hold_votes = {k: v for k, v in votes.items() if k != "HOLD"}
        if non_hold_votes:
            max_vote = max(non_hold_votes.values())
            leaders = [k for k, v in non_hold_votes.items() if v == max_vote]
            consensus = leaders[0] if len(leaders) == 1 else "HOLD"
        else:
            consensus = "HOLD"

        return {
            "consensus": consensus,
            "avg_confidence": avg_conf,
            "votes": votes,
            "strategies_count": len(signals),
            "details": details,
        }

    @classmethod
    def list_strategies(cls) -> list[str]:
        """Return registered strategy names."""
        return [s.__name__.replace("Strategy", "") for s in _DEFAULT_STRATEGIES]
