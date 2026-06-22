"""
Aggregates all three market sentiment sources into a single structured payload
that gets injected into the DeepSeek meta-analyzer prompt.
"""

from __future__ import annotations

import logging
from typing import Any

from .polymarket_client import PolymarketClient
from .fear_greed_client import FearGreedClient
from .news_client import NewsClient

logger = logging.getLogger(__name__)


class SentimentAggregator:
    """Combines Polymarket, Fear & Greed, and News sentiment."""

    def __init__(
        self,
        mock_mode: bool = True,
        polymarket_client: PolymarketClient | None = None,
        fear_greed_client: FearGreedClient | None = None,
        news_client: NewsClient | None = None,
    ) -> None:
        self.mock_mode = mock_mode
        self.polymarket = polymarket_client or PolymarketClient(mock_mode=mock_mode)
        self.fear_greed = fear_greed_client or FearGreedClient(mock_mode=mock_mode)
        self.news = news_client or NewsClient(mock_mode=mock_mode)

    async def aggregate(self) -> dict[str, Any]:
        """Fetch all three sources in parallel and return combined sentiment.

        Returns::
            {
              "polymarket": [ ... markets ... ],
              "fear_greed": { "score": 42, "label": "Fear", ... },
              "news": { "score": -0.15, "label": "Neutral", ... },
              "composite_label": "Cautious",
              "composite_bias": -0.15,   # -1 (bearish) to +1 (bullish)
            }
        """
        import asyncio

        poly_task = self.polymarket.fetch_macro_sentiment()
        fg_task = self.fear_greed.fetch_index()
        news_task = self.news.fetch_sentiment()

        poly, fg, news = await asyncio.gather(poly_task, fg_task, news_task)

        # Normalise to a composite bias in [-1, +1]
        biases: list[float] = []

        # Fear & Greed → bias: 0=Extreme Fear → -1, 100=Extreme Greed → +1
        fg_score = fg.get("score", 50)
        biases.append((fg_score - 50) / 50.0)

        # News sentiment score → clamp to [-3, +3] then normalise
        ns = news.get("score", 0)
        ns_clamped = max(-3.0, min(3.0, float(ns)))
        biases.append(ns_clamped / 3.0)

        # Polymarket bias: average of probabilities for bullish markets minus
        # bearish ones (rough heuristic)
        poly_score = 0.0
        count = 0
        for m in poly:
            q = m.get("question", "").lower()
            p = m.get("probability", 0.5)
            # Markets phrased as "Will X happen?" — higher Yes = more likely
            # We approximate: higher prob on typically bullish questions = bullish
            if any(w in q for w in ("above", "rally", "raise", "increase", "grow", "bull")):
                poly_score += p
            elif any(w in q for w in ("below", "crash", "recession", "cut", "decrease")):
                poly_score += (1 - p)  # inverted = bearish
            else:
                poly_score += p  # neutral
            count += 1
        if count:
            poly_bias = (poly_score / count - 0.5) * 2  # [0,1] → [-1,+1]
        else:
            poly_bias = 0.0
        biases.append(poly_bias)

        composite_bias = round(sum(biases) / len(biases), 4)

        return {
            "polymarket": poly,
            "fear_greed": fg,
            "news": news,
            "composite_label": self._composite_label(composite_bias),
            "composite_bias": composite_bias,
        }

    def _composite_label(self, bias: float) -> str:
        if bias >= 0.5:
            return "Very Bullish"
        if bias >= 0.15:
            return "Bullish"
        if bias > -0.15:
            return "Neutral"
        if bias > -0.5:
            return "Bearish"
        return "Very Bearish"

    async def close(self) -> None:
        await self.polymarket.close()
        await self.fear_greed.close()
        await self.news.close()
