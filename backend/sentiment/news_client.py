"""
Financial news headline sentiment client.

Fetches top business/finance headlines and runs a lightweight keyword-based
sentiment score to capture the prevailing narrative (bullish / bearish / neutral).
"""

from __future__ import annotations

import logging
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Fallback RSS feed for top financial news headlines (free, no auth)
NEWS_FEED_URL = "https://feeds.marketwatch.com/marketwatch/topstories"


class NewsClient:
    """Scrapes top financial headlines and computes a sentiment score."""

    def __init__(self, mock_mode: bool = True) -> None:
        self.mock_mode = mock_mode
        self._http = httpx.AsyncClient(timeout=10)

    # ── Bullish / Bearish keyword lexicons ──────────────────────────────
    BULLISH = {
        "rally", "surge", "soar", "bullish", "upgrade", "outperform",
        "breakout", "all-time high", "record", "growth", "positive",
        "optimism", "boom", "expansion", "beat estimates", "profit jump",
        "buyback", "dividend hike", "strong demand", "momentum",
    }
    BEARISH = {
        "plunge", "crash", "bearish", "downgrade", "underperform",
        "sell-off", "correction", "recession", "inflation", "slowdown",
        "decline", "loss", "debt", "default", "bankruptcy", "layoff",
        "uncertainty", "volatility", "fear", "panic", "miss estimates",
        "profit warning", "cut outlook", "tariff", "geopolitical risk",
    }

    async def fetch_sentiment(self) -> dict[str, Any]:
        """Fetch headlines and return aggregate sentiment.

        Returns::
            {"score": -0.12, "label": "Slightly Negative",
             "headline_count": 20, "top_headlines": ["…", …]}
        """
        if self.mock_mode:
            return self._mock_data()

        try:
            resp = await self._http.get(NEWS_FEED_URL)
            resp.raise_for_status()
            text = resp.text

            # Extract <title> tags from RSS XML
            titles = re.findall(r"<title>(.*?)</title>", text)[:25]

            # Score each title
            scores = [self._score_title(t) for t in titles]
            avg = sum(scores) / max(len(scores), 1)

            # Pick top 5 most interesting
            top = sorted(
                titles[:15],
                key=lambda t: abs(self._score_title(t)),
                reverse=True,
            )[:5]

            return {
                "score": round(avg, 4),
                "label": self._label(avg),
                "headline_count": len(scores),
                "top_headlines": top,
            }
        except Exception as exc:
            logger.warning("News sentiment fetch failed: %s", exc)
            return self._mock_data()

    def _score_title(self, title: str) -> float:
        """Score a single headline — positive = bullish, negative = bearish."""
        lower = title.lower()
        score = 0.0
        for word in self.BULLISH:
            if word in lower:
                score += 1.0
        for word in self.BEARISH:
            if word in lower:
                score -= 1.0
        return score

    def _label(self, score: float) -> str:
        if score >= 2.0:
            return "Very Bullish"
        if score >= 0.5:
            return "Bullish"
        if score > -0.5:
            return "Neutral"
        if score > -2.0:
            return "Bearish"
        return "Very Bearish"

    def _mock_data(self) -> dict[str, Any]:
        return {
            "score": -0.15,
            "label": "Neutral",
            "headline_count": 20,
            "top_headlines": [
                "Fed signals cautious approach to rate cuts",
                "Tech stocks rally on AI earnings optimism",
                "Treasury yields edge lower amid recession fears",
                "Oil prices slip on demand concerns",
                "S&P 500 hovers near record levels",
            ],
        }

    async def close(self) -> None:
        await self._http.aclose()
