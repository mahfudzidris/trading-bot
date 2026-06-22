"""DeepSeek AI-powered market analyzer with mock fallback."""

from __future__ import annotations

import logging
import random
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DEEPSEEK_API_BASE = "https://api.deepseek.com/v1"


class DeepSeekAnalyzer:
    """Analyzes market conditions using the DeepSeek LLM API.

    In mock mode the analyser returns rule-based synthetic decisions that
    mimic an AI's reasoning style.
    """

    def __init__(self, api_key: str, model: str = "deepseek-chat", mock_mode: bool = True) -> None:
        self.api_key = api_key
        self.model = model
        self.mock_mode = mock_mode
        self._http = httpx.AsyncClient(timeout=60)

    # ──────────────────────────────────────────────────────────────────────
    # analyze_market
    # ──────────────────────────────────────────────────────────────────────

    async def analyze_market(
        self,
        symbol: str,
        price_data: dict[str, Any],
        indicators: dict[str, Any],
        strategy_signals: list[dict[str, Any]] | None = None,
        market_sentiment: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run a full AI analysis on *symbol* and return a trade decision dict.

        Parameters
        ----------
        symbol : str
            Ticker symbol (e.g. "AAPL").
        price_data : dict
            Price, change_pct, volume, timestamp.
        indicators : dict
            Technical indicators (SMA, EMA, RSI, etc.).
        strategy_signals : list[dict] | None
            Optional pre-computed signals from EnsembleStrategy.
        market_sentiment : dict | None
            Optional aggregated market sentiment (Polymarket, Fear & Greed,
            News). Injected as an extra section in the prompt.

        Returns
        -------
        dict
            Keys: action, confidence, reasoning, take_profit, stop_loss,
            position_size_pct.
        """
        if self.mock_mode:
            return self._mock_decision(symbol, price_data, indicators, strategy_signals, market_sentiment)

        prompt = self.build_prompt(symbol, price_data, indicators, strategy_signals, market_sentiment)
        response_text = await self._call_deepseek(prompt)
        return self._parse_response(response_text, symbol, price_data, indicators)

    # ──────────────────────────────────────────────────────────────────────
    # analyze_portfolio
    # ──────────────────────────────────────────────────────────────────────

    async def analyze_portfolio(
        self,
        holdings: list[dict[str, Any]],
        market_data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Analyse each holding and return a list of per-position decisions."""
        results: list[dict[str, Any]] = []
        for h in holdings:
            sym = h.get("symbol", "")
            sym_data = market_data.get(sym, {})
            sym_indicators = {
                "price": sym_data.get("price", 0),
                "sma_20": sym_data.get("sma_20", 0),
                "sma_50": sym_data.get("sma_50", 0),
                "ema_20": sym_data.get("ema_20", 0),
                "ema_50": sym_data.get("ema_50", 0),
                "rsi_14": sym_data.get("rsi_14", 50),
                "volume": sym_data.get("volume", 0),
            }
            decision = await self.analyze_market(sym, sym_data, sym_indicators)
            decision["symbol"] = sym
            decision["current_qty"] = h.get("qty", 0)
            decision["unrealized_pnl"] = h.get("unrealized_pl", 0)
            results.append(decision)
        return results

    # ──────────────────────────────────────────────────────────────────────
    # build_prompt
    # ──────────────────────────────────────────────────────────────────────

    def build_prompt(
        self,
        symbol: str,
        price_data: dict[str, Any],
        indicators: dict[str, Any],
        strategy_signals: list[dict[str, Any]] | None = None,
        market_sentiment: dict[str, Any] | None = None,
    ) -> str:
        """Construct the detailed prompt sent to DeepSeek.

        If *strategy_signals* is provided (list of dicts from EnsembleStrategy),
        they are injected as extra context so the AI can weigh each strategy.

        If *market_sentiment* is provided (from SentimentAggregator), the macro
        sentiment data (Polymarket, Fear & Greed, News) is injected so the AI
        can factor in crowd sentiment and market narratives.
        """
        prompt = f"""You are an expert quantitative trader. Analyse the following data for {symbol} and decide whether to BUY, SELL, or HOLD.

=== PRICE DATA ===
Price: ${indicators.get('price', price_data.get('price', 'N/A'))}
Change: {price_data.get('change_pct', 0)}%
Volume: {price_data.get('volume', 0)}

=== TECHNICAL INDICATORS ===
SMA(20): {indicators.get('sma_20', 'N/A')}
SMA(50): {indicators.get('sma_50', 'N/A')}
EMA(20): {indicators.get('ema_20', 'N/A')}
EMA(50): {indicators.get('ema_50', 'N/A')}
RSI(14): {indicators.get('rsi_14', 'N/A')}

=== MARKET CONTEXT ===
Current time: {price_data.get('timestamp', 'now')}
"""

        if strategy_signals:
            prompt += "\n=== STRATEGY SIGNALS ===\n"
            for i, sig in enumerate(strategy_signals, 1):
                prompt += f"{i}. {sig.get('name', 'Strategy')}: {sig.get('signal', 'HOLD')} (conf: {sig.get('confidence', 0)}) — {sig.get('reasoning', '')}\n"

            prompt += f"""
These are individual strategy signals. Evaluate them critically:
- Some may agree, others may conflict — use your judgment.
- Consider market context (volume, volatility) to decide which signals are reliable.
- Do NOT simply follow the majority vote; reason from first principles.
"""

        # ── Market sentiment section ──
        if market_sentiment:
            prompt += "\n=== MARKET SENTIMENT ===\n"

            fg = market_sentiment.get("fear_greed", {})
            prompt += f"Fear & Greed Index: {fg.get('score', 'N/A')}/100 — {fg.get('label', 'N/A')}\n"

            news = market_sentiment.get("news", {})
            prompt += f"News Sentiment: {news.get('label', 'N/A')} (score: {news.get('score', 0)})\n"
            headlines = news.get("top_headlines", [])
            if headlines:
                prompt += "Top Headlines:\n"
                for h in headlines[:3]:
                    prompt += f"  • {h}\n"

            poly = market_sentiment.get("polymarket", [])
            if poly:
                prompt += "Prediction Markets (real-money probabilities):\n"
                for m in poly[:4]:
                    pct = m.get("probability", 0) * 100
                    prompt += f"  • {m.get('question', '?')}: {pct:.0f}% (${m.get('volume', 0):,} volume)\n"

            composite = market_sentiment.get("composite_label", "Neutral")
            bias = market_sentiment.get("composite_bias", 0)
            prompt += f"\nComposite Market Sentiment: {composite} (bias: {bias:+.2f})\n"

            prompt += """
These are external sentiment signals from prediction markets, the Fear & Greed
Index, and financial news. Use them as a macro overlay — they tell you whether
the broader market mood aligns with or contradicts your technical analysis.
A strongly bearish macro sentiment against bullish technicals may warrant caution.
"""

        prompt += """
Return your analysis as a JSON object with these fields:
- "action": "BUY" | "SELL" | "HOLD"
- "confidence": integer 0-100
- "reasoning": a brief explanation of your decision
- "take_profit": price target for profit taking (or 0 if HOLD)
- "stop_loss": stop-loss price (or 0 if HOLD)
- "position_size_pct": percentage of capital to deploy (0.0 - 0.1)

Output ONLY the JSON object, nothing else.
"""
        return prompt

    # ──────────────────────────────────────────────────────────────────────
    # internal: mock decisions
    # ──────────────────────────────────────────────────────────────────────

    def _mock_decision(
        self,
        symbol: str,
        price_data: dict[str, Any],
        indicators: dict[str, Any],
        strategy_signals: list[dict[str, Any]] | None = None,
        market_sentiment: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        price = indicators.get("price", price_data.get("price", 100.0))
        rsi = indicators.get("rsi_14", 50)
        sma_20 = indicators.get("sma_20", price)
        sma_50 = indicators.get("sma_50", price)
        volume = indicators.get("volume", price_data.get("volume", 1_000_000))

        # Simple rule-based logic that mimics AI reasoning
        action: str = "HOLD"
        confidence: int = 50
        reasoning_parts: list[str] = []

        # ── Market sentiment override ──
        sentiment_bias = 0.0
        if market_sentiment:
            sentiment_bias = market_sentiment.get("composite_bias", 0)
            composite = market_sentiment.get("composite_label", "Neutral")
            fg = market_sentiment.get("fear_greed", {})
            fg_label = fg.get("label", "N/A")
            reasoning_parts.append(f"Market sentiment: {composite} (Fear & Greed: {fg_label}, bias: {sentiment_bias:+.2f})")

        # If strategy signals are available, use them to inform the mock
        if strategy_signals:
            votes: dict[str, int] = {"BUY": 0, "SELL": 0, "HOLD": 0}
            total_conf = 0
            for sig in strategy_signals:
                votes[sig.get("signal", "HOLD")] = votes.get(sig.get("signal", "HOLD"), 0) + 1
                total_conf += sig.get("confidence", 0)
            avg_conf = total_conf // len(strategy_signals)

            # Consensus from strategies
            non_hold = {k: v for k, v in votes.items() if k != "HOLD"}
            if non_hold:
                max_vote = max(non_hold.values())
                leaders = [k for k, v in non_hold.items() if v == max_vote]
                if len(leaders) == 1:
                    action = leaders[0]
                    confidence = min(95, avg_conf + 5)
                    reasoning_parts.append(f"Ensemble consensus: {action} ({votes[action]}/{len(strategy_signals)} strategies)")

            reasoning_parts.append(f"Strategy votes: {dict(votes)}, avg conf: {avg_conf}%")

        # RSI-based signals (still used for refinement)
        if rsi < 30:
            action = "BUY"
            confidence = max(confidence, 70)
            reasoning_parts.append(f"RSI at {rsi:.1f} suggests oversold conditions")
        elif rsi > 70:
            if action != "BUY":  # don't override ensemble BUY
                action = "SELL"
            confidence = max(confidence, 70)
            reasoning_parts.append(f"RSI at {rsi:.1f} suggests overbought conditions")

        # Moving average crossover
        if sma_20 > sma_50 and price > sma_20:
            if action == "HOLD":
                action = "BUY"
            confidence += 10
            reasoning_parts.append("Price above rising SMA(20) and SMA(50) — bullish trend")
        elif sma_20 < sma_50 and price < sma_20:
            if action == "HOLD":
                action = "SELL"
            confidence += 10
            reasoning_parts.append("Price below falling SMA(20) and SMA(50) — bearish trend")

        # Volume confirmation
        avg_vol = 5_000_000
        if volume > avg_vol * 1.5:
            reasoning_parts.append("Above-average volume confirms momentum")
            confidence += 5
        elif volume < avg_vol * 0.5:
            reasoning_parts.append("Below-average volume suggests low conviction")
            confidence -= 5

        confidence = max(0, min(100, confidence))

        # Sentiment bias influences mock confidence (+/- 15 pts) and can nudge HOLD
        if sentiment_bias != 0.0 and action == "HOLD":
            if sentiment_bias > 0.3:
                action = "BUY"
                confidence = max(confidence, 55)
                reasoning_parts.append("Positive macro sentiment biases toward BUY")
            elif sentiment_bias < -0.3:
                action = "SELL"
                confidence = max(confidence, 55)
                reasoning_parts.append("Negative macro sentiment biases toward SELL")
        # Adjust confidence by sentiment magnitude
        confidence += int(sentiment_bias * 15)
        confidence = max(0, min(100, confidence))
        price_pct = 0.05 if action in ("BUY", "SELL") else 0.0

        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "No clear signals — holding position"

        return {
            "action": action,
            "confidence": confidence,
            "reasoning": reasoning,
            "take_profit": round(price * (1 + price_pct), 2) if action == "BUY" else 0.0,
            "stop_loss": round(price * (1 - 0.02), 2) if action != "HOLD" else 0.0,
            "position_size_pct": 0.1 if action != "HOLD" else 0.0,
        }

    # ──────────────────────────────────────────────────────────────────────
    # internal: real API call
    # ──────────────────────────────────────────────────────────────────────

    async def _call_deepseek(self, prompt: str) -> str:
        try:
            resp = await self._http.post(
                f"{DEEPSEEK_API_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 512,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as exc:
            logger.error("DeepSeek API call failed: %s", exc)
            raise

    def _parse_response(
        self,
        text: str,
        symbol: str,
        price_data: dict[str, Any],
        indicators: dict[str, Any],
    ) -> dict[str, Any]:
        """Parse the LLM's JSON response with fallback to mock logic."""
        import json
        import re

        try:
            # Try to extract JSON from the response
            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                return {
                    "action": parsed.get("action", "HOLD"),
                    "confidence": int(parsed.get("confidence", 50)),
                    "reasoning": parsed.get("reasoning", "No reasoning provided"),
                    "take_profit": float(parsed.get("take_profit", 0)),
                    "stop_loss": float(parsed.get("stop_loss", 0)),
                    "position_size_pct": float(parsed.get("position_size_pct", 0)),
                }
        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            logger.warning("Could not parse DeepSeek response: %s", exc)

        # Fallback to mock decision if parsing fails
        return self._mock_decision(symbol, price_data, indicators)

    async def close(self) -> None:
        await self._http.aclose()
