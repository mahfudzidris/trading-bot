"""
Polymarket prediction market client.

Fetches live macro-market probabilities that serve as a leading sentiment
indicator — the crowd's real-money conviction on Fed moves, SPX levels, etc.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

POLYMARKET_GAMMA = "https://gamma-api.polymarket.com"


class PolymarketClient:
    """Read-only client for Polymarket prediction markets.

    The client queries a fixed set of macro-relevant search terms and returns
    a structured list of (question, yes_probability, volume) tuples.
    """

    MACRO_SEARCHES = [
        "federal reserve interest rate 2026",
        "S&P 500 2026 close",
        "cpi inflation 2026",
        "US recession 2026",
        "nasdaq 100 2026",
    ]

    def __init__(self, mock_mode: bool = True) -> None:
        self.mock_mode = mock_mode
        self._http = httpx.AsyncClient(timeout=15)

    async def fetch_macro_sentiment(self) -> list[dict[str, Any]]:
        """Probe several macro topics and return structured predictions.

        Returns a list of dicts::
            [{"question": "Will…?", "probability": 0.65, "volume": 120000}, …]
        """
        if self.mock_mode:
            return self._mock_data()

        results: list[dict[str, Any]] = []
        for query in self.MACRO_SEARCHES:
            try:
                resp = await self._http.get(
                    f"{POLYMARKET_GAMMA}/public-search",
                    params={"q": query, "limit": 5},
                )
                resp.raise_for_status()
                data = resp.json()
                for event in data.get("events", []):
                    vol = float(event.get("volume", 0))
                    if vol < 5_000:  # skip illiquid
                        continue
                    for m in event.get("markets", []):
                        prices_raw = m.get("outcomePrices", "[]")
                        if isinstance(prices_raw, str):
                            prices = json.loads(prices_raw)
                        else:
                            prices = prices_raw
                        yes_prob = float(prices[0]) if len(prices) >= 1 else 0.0
                        results.append({
                            "question": m.get("question", "?"),
                            "probability": round(yes_prob, 4),
                            "volume": round(vol),
                        })
            except Exception as exc:
                logger.warning("Polymarket query '%s' failed: %s", query, exc)
        return results

    def _mock_data(self) -> list[dict[str, Any]]:
        """Synthetic macro data for testing / when API unreachable."""
        return [
            {"question": "Will the Fed hold rates steady at next FOMC meeting?",
             "probability": 0.72, "volume": 85000},
            {"question": "Will S&P 500 close above $7,500 in December 2026?",
             "probability": 0.28, "volume": 31000},
            {"question": "Will US CPI YoY be above 3.0% in next release?",
             "probability": 0.45, "volume": 22000},
            {"question": "Will the US enter a recession in 2026?",
             "probability": 0.18, "volume": 145000},
            {"question": "Will Nasdaq 100 close above $22,000 in December?",
             "probability": 0.35, "volume": 18000},
        ]

    async def close(self) -> None:
        await self._http.aclose()
