"""
CNN Fear & Greed Index client.

Fetches the Fear & Greed Index — a composite market sentiment gauge (0–100)
that blends 7 indicators: stock price breadth, put/call ratio, market volatility,
safe-haven demand, junk-bond demand, and momentum.
"""

from __future__ import annotations

import logging
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)

FEAR_GREED_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"


class FearGreedClient:
    """Fetches the CNN Fear & Greed Index value."""

    def __init__(self, mock_mode: bool = True) -> None:
        self.mock_mode = mock_mode
        self._http = httpx.AsyncClient(timeout=10)

    async def fetch_index(self) -> dict[str, Any]:
        """Return the current Fear & Greed index.
        Returns {"score": 42, "label": "Fear", "previous_close": 38}
        """
        if self.mock_mode:
            return self._mock_data()

        try:
            resp = await self._http.get(FEAR_GREED_URL)
            resp.raise_for_status()
            data = resp.json()
            fg = data.get("fear_and_greed", {})
            score_raw = fg.get("score", "")
            # score might be a string like "42" or an object...
            score = 50
            if isinstance(score_raw, str):
                # extract numeric via regex in case it's wrapped
                m = re.search(r"(\d+)", score_raw)
                if m:
                    score = int(m.group(1))
            elif isinstance(score_raw, (int, float)):
                score = int(score_raw)

            prev = fg.get("previous_close", "")
            prev_score = 50
            if isinstance(prev, str):
                m = re.search(r"(\d+)", prev)
                if m:
                    prev_score = int(m.group(1))
            elif isinstance(prev, (int, float)):
                prev_score = int(prev)

            return {
                "score": max(0, min(100, score)),
                "label": self._label(score),
                "previous_close": max(0, min(100, prev_score)),
            }
        except Exception as exc:
            logger.warning("Fear & Greed fetch failed: %s", exc)
            return self._mock_data()

    def _label(self, score: int) -> str:
        if score <= 25:
            return "Extreme Fear"
        if score <= 45:
            return "Fear"
        if score <= 55:
            return "Neutral"
        if score <= 75:
            return "Greed"
        return "Extreme Greed"

    def _mock_data(self) -> dict[str, Any]:
        return {"score": 42, "label": "Fear", "previous_close": 38}

    async def close(self) -> None:
        await self._http.aclose()
