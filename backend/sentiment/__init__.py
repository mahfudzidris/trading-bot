"""
Market sentiment package.

Provides three external sentiment sources that feed into the AI Meta-Analyzer:
  1. PolymarketClient  — Prediction market probabilities (Fed, SPX, macro)
  2. FearGreedClient   — CNN Fear & Greed Index (0–100)
  3. NewsClient        — Top financial headline sentiment

The SentimentAggregator unionises all three into a single dict injected into the
DeepSeek prompt under === MARKET SENTIMENT ===.
"""

from __future__ import annotations

from .polymarket_client import PolymarketClient
from .fear_greed_client import FearGreedClient
from .news_client import NewsClient
from .sentiment_aggregator import SentimentAggregator

__all__ = [
    "PolymarketClient",
    "FearGreedClient",
    "NewsClient",
    "SentimentAggregator",
]
