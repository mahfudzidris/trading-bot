"""
Shared pytest fixtures for the trading bot backend tests.

V2: Uses async SQLAlchemy with aiosqlite, httpx.AsyncClient with ASGITransport
for API tests. All fixtures use mock_mode=True so no real network calls are made.
"""

from __future__ import annotations

import os
import tempfile
from typing import AsyncGenerator

import httpx
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from config import Settings
from data.twelvedata_client import TwelveDataClient
from ai.deepseek_analyzer import DeepSeekAnalyzer
from broker.alpaca_client import AlpacaClient
from strategy.engine import StrategyEngine
from sentiment.polymarket_client import PolymarketClient
from sentiment.fear_greed_client import FearGreedClient
from sentiment.news_client import NewsClient
from sentiment.sentiment_aggregator import SentimentAggregator
from db.models import Base

# ── pytest plugins ──────────────────────────────────────────────────────────
pytest_plugins = ["pytest_asyncio"]

# ── Helpers ─────────────────────────────────────────────────────────────────


def _make_settings() -> Settings:
    """Return test Settings with MOCK_MODE=True and standard test values."""
    return Settings(
        TWELVEDATA_API_KEY="test_key",
        ALPACA_API_KEY="test_key",
        ALPACA_SECRET_KEY="test_secret",
        DEEPSEEK_API_KEY="test_key",
        MOCK_MODE=True,
        PORT=8000,
        SYMBOLS=["SPY"],
        TRADE_MAX_POSITION_SIZE=0.1,
        TRADE_STOP_LOSS_PCT=0.02,
        TRADE_TAKE_PROFIT_PCT=0.05,
        ALPACA_PAPER=True,
        DB_PATH=":memory:",
    )


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def mock_twelvedata_client() -> AsyncGenerator[TwelveDataClient, None]:
    """Return a TwelveDataClient in mock mode."""
    client = TwelveDataClient(api_key="test_key", mock_mode=True)
    yield client
    await client.close()


@pytest_asyncio.fixture
async def mock_deepseek_analyzer() -> AsyncGenerator[DeepSeekAnalyzer, None]:
    """Return a DeepSeekAnalyzer in mock mode."""
    analyzer = DeepSeekAnalyzer(api_key="test_key", model="deepseek-chat", mock_mode=True)
    yield analyzer
    await analyzer.close()


@pytest_asyncio.fixture
async def mock_alpaca_client() -> AsyncGenerator[AlpacaClient, None]:
    """Return an AlpacaClient in mock mode."""
    client = AlpacaClient(api_key="test_key", secret_key="test_secret", paper=True, mock_mode=True)
    yield client
    await client.close()


@pytest.fixture
def test_settings() -> Settings:
    """Return Settings with MOCK_MODE=True and test values."""
    return _make_settings()


@pytest_asyncio.fixture
async def mock_strategy_engine(
    mock_twelvedata_client: TwelveDataClient,
    mock_deepseek_analyzer: DeepSeekAnalyzer,
    mock_alpaca_client: AlpacaClient,
    test_settings: Settings,
) -> StrategyEngine:
    """Return a StrategyEngine with mocked clients."""
    return StrategyEngine(
        data_client=mock_twelvedata_client,
        ai_analyzer=mock_deepseek_analyzer,
        broker_client=mock_alpaca_client,
        config=test_settings,
    )


# ── Sentiment Fixtures ──────────────────────────────────────────────


@pytest_asyncio.fixture
async def mock_polymarket_client() -> PolymarketClient:
    """Return a PolymarketClient in mock mode."""
    return PolymarketClient(mock_mode=True)


@pytest_asyncio.fixture
async def mock_fear_greed_client() -> FearGreedClient:
    """Return a FearGreedClient in mock mode."""
    return FearGreedClient(mock_mode=True)


@pytest_asyncio.fixture
async def mock_news_client() -> NewsClient:
    """Return a NewsClient in mock mode."""
    return NewsClient(mock_mode=True)


@pytest_asyncio.fixture
async def mock_sentiment_aggregator() -> SentimentAggregator:
    """Return a SentimentAggregator with all sub-clients in mock mode."""
    return SentimentAggregator(mock_mode=True)


@pytest_asyncio.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh in-memory SQLite database for each test.

    Creates all tables, yields a session, then drops everything.
    """
    # Use a temporary file so aiosqlite works reliably
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp_path = tmp.name
    tmp.close()

    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with session_maker() as session:
        yield session

    await engine.dispose()
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


@pytest_asyncio.fixture
async def async_client(
    test_db: AsyncSession,
    mock_twelvedata_client: TwelveDataClient,
    mock_deepseek_analyzer: DeepSeekAnalyzer,
    mock_alpaca_client: AlpacaClient,
    mock_sentiment_aggregator: SentimentAggregator,
    test_settings: Settings,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Return an httpx.AsyncClient wired to the FastAPI app via ASGITransport.

    Sets the global service instances (data_client, ai_analyzer,
    broker_client, strategy_engine, sentiment_aggregator) and overrides
    the get_db dependency so the FastAPI code uses our test_db session.
    """
    from main import app, data_client, ai_analyzer, broker_client, strategy_engine, sentiment_aggregator
    from db.models import get_db

    # Patch globals in main
    globals_backup = {}

    # Store originals and override
    import main as main_module

    for name, val in [
        ("data_client", mock_twelvedata_client),
        ("ai_analyzer", mock_deepseek_analyzer),
        ("broker_client", mock_alpaca_client),
        ("sentiment_aggregator", mock_sentiment_aggregator),
    ]:
        globals_backup[name] = getattr(main_module, name)
        setattr(main_module, name, val)

    # Create StrategyEngine with mocked deps
    engine = StrategyEngine(
        data_client=mock_twelvedata_client,
        ai_analyzer=mock_deepseek_analyzer,
        broker_client=mock_alpaca_client,
        config=test_settings,
    )
    globals_backup["strategy_engine"] = getattr(main_module, "strategy_engine")
    setattr(main_module, "strategy_engine", engine)

    # Override the get_db dependency to use our test_db
    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_db

    app.dependency_overrides[get_db] = _override_get_db

    from httpx import ASGITransport

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Restore globals
    for name, old_val in globals_backup.items():
        setattr(main_module, name, old_val)
    app.dependency_overrides.clear()
