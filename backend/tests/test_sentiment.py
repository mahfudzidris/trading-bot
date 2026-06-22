"""Tests for sentiment package — PolymarketClient, FearGreedClient, NewsClient, SentimentAggregator."""

from __future__ import annotations

import pytest
import pytest_asyncio


class TestPolymarketClient:
    """Tests for sentiment/polymarket_client.py in mock mode."""

    @pytest.mark.asyncio
    async def test_fetch_macro_sentiment_returns_list(self, mock_polymarket_client):
        """Verify fetch_macro_sentiment returns a list of market dicts."""
        result = await mock_polymarket_client.fetch_macro_sentiment()
        assert isinstance(result, list)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_market_dict_structure(self, mock_polymarket_client):
        """Verify each market item has expected keys."""
        result = await mock_polymarket_client.fetch_macro_sentiment()
        for market in result:
            assert "question" in market
            assert "probability" in market
            assert "volume" in market
            assert 0 <= market["probability"] <= 1
            assert market["volume"] > 0

    @pytest.mark.asyncio
    async def test_close(self, mock_polymarket_client):
        """Verify close works without error."""
        await mock_polymarket_client.close()


class TestFearGreedClient:
    """Tests for sentiment/fear_greed_client.py in mock mode."""

    @pytest.mark.asyncio
    async def test_fetch_index_returns_dict(self, mock_fear_greed_client):
        """Verify fetch_index returns a dict with score, label, previous_close."""
        result = await mock_fear_greed_client.fetch_index()
        assert isinstance(result, dict)
        assert "score" in result
        assert "label" in result
        assert "previous_close" in result

    @pytest.mark.asyncio
    async def test_score_range(self, mock_fear_greed_client):
        """Verify score is between 0 and 100."""
        result = await mock_fear_greed_client.fetch_index()
        assert 0 <= result["score"] <= 100

    @pytest.mark.asyncio
    async def test_label_valid(self, mock_fear_greed_client):
        """Verify label is one of the known categories."""
        result = await mock_fear_greed_client.fetch_index()
        valid_labels = {"Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"}
        assert result["label"] in valid_labels

    @pytest.mark.asyncio
    async def test_close(self, mock_fear_greed_client):
        """Verify close works without error."""
        await mock_fear_greed_client.close()


class TestNewsClient:
    """Tests for sentiment/news_client.py in mock mode."""

    @pytest.mark.asyncio
    async def test_fetch_sentiment_returns_dict(self, mock_news_client):
        """Verify fetch_sentiment returns a dict with expected keys."""
        result = await mock_news_client.fetch_sentiment()
        assert isinstance(result, dict)
        assert "score" in result
        assert "label" in result
        assert "headline_count" in result
        assert "top_headlines" in result

    @pytest.mark.asyncio
    async def test_headlines_are_strings(self, mock_news_client):
        """Verify top_headlines contains strings."""
        result = await mock_news_client.fetch_sentiment()
        for h in result["top_headlines"]:
            assert isinstance(h, str)
            assert len(h) > 0

    @pytest.mark.asyncio
    async def test_headline_count_positive(self, mock_news_client):
        """Verify headline_count is positive."""
        result = await mock_news_client.fetch_sentiment()
        assert result["headline_count"] > 0

    @pytest.mark.asyncio
    async def test_close(self, mock_news_client):
        """Verify close works without error."""
        await mock_news_client.close()


class TestSentimentAggregator:
    """Tests for sentiment/sentiment_aggregator.py in mock mode."""

    @pytest.mark.asyncio
    async def test_aggregate_returns_all_sources(self, mock_sentiment_aggregator):
        """Verify aggregate() returns polymarket, fear_greed, news, and composite fields."""
        result = await mock_sentiment_aggregator.aggregate()
        assert "polymarket" in result
        assert "fear_greed" in result
        assert "news" in result
        assert "composite_label" in result
        assert "composite_bias" in result

    @pytest.mark.asyncio
    async def test_composite_bias_range(self, mock_sentiment_aggregator):
        """Verify composite_bias is between -1 and +1."""
        result = await mock_sentiment_aggregator.aggregate()
        assert -1.0 <= result["composite_bias"] <= 1.0

    @pytest.mark.asyncio
    async def test_composite_label_valid(self, mock_sentiment_aggregator):
        """Verify composite_label is a known category."""
        result = await mock_sentiment_aggregator.aggregate()
        valid = {"Very Bullish", "Bullish", "Neutral", "Bearish", "Very Bearish"}
        assert result["composite_label"] in valid

    @pytest.mark.asyncio
    async def test_close(self, mock_sentiment_aggregator):
        """Verify close works without error."""
        await mock_sentiment_aggregator.close()
