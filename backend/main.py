"""FastAPI Trading Bot — main application entry point."""

from __future__ import annotations

import logging
import random
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any

from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from data.twelvedata_client import TwelveDataClient
from ai.deepseek_analyzer import DeepSeekAnalyzer
from broker.alpaca_client import AlpacaClient
from strategy.engine import StrategyEngine
from db.models import init_db, get_db
from db import crud
from scheduler.daily_run import run_daily

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Global service instances ──────────────────────────────────────────────
data_client: TwelveDataClient | None = None
ai_analyzer: DeepSeekAnalyzer | None = None
broker_client: AlpacaClient | None = None
strategy_engine: StrategyEngine | None = None


# ── Lifespan ───────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    global data_client, ai_analyzer, broker_client, strategy_engine

    logger.info("Starting up Trading Bot backend (mock_mode=%s)...", settings.MOCK_MODE)

    # Initialise database
    await init_db(settings.DB_PATH)
    logger.info("Database initialised at %s", settings.DB_PATH)

    # Initialise services
    data_client = TwelveDataClient(
        api_key=settings.TWELVEDATA_API_KEY,
        mock_mode=settings.MOCK_MODE,
    )
    ai_analyzer = DeepSeekAnalyzer(
        api_key=settings.DEEPSEEK_API_KEY,
        model=settings.DEEPSEEK_MODEL,
        mock_mode=settings.MOCK_MODE,
    )
    broker_client = AlpacaClient(
        api_key=settings.ALPACA_API_KEY,
        secret_key=settings.ALPACA_SECRET_KEY,
        paper=settings.ALPACA_PAPER,
        mock_mode=settings.MOCK_MODE,
    )
    strategy_engine = StrategyEngine(
        data_client=data_client,
        ai_analyzer=ai_analyzer,
        broker_client=broker_client,
        config=settings,
    )

    # Seed mock data if in mock mode
    if settings.MOCK_MODE:
        try:
            async for session in get_db():
                await _seed_mock_data(session)
                break
            logger.info("Mock data seeded successfully")
        except Exception as exc:
            logger.warning("Could not seed mock data: %s", exc)

    yield

    # Shutdown
    if data_client:
        await data_client.close()
    if ai_analyzer:
        await ai_analyzer.close()
    logger.info("Services shut down.")


app = FastAPI(
    title="Trading Bot API",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────────────────────────────────
# Helper: get current service instances
# ──────────────────────────────────────────────────────────────────────────

def _get_services() -> tuple[TwelveDataClient, DeepSeekAnalyzer, AlpacaClient, StrategyEngine]:
    """Return the four global service objects (raises if not ready)."""
    if any(x is None for x in (data_client, ai_analyzer, broker_client, strategy_engine)):
        raise HTTPException(status_code=503, detail="Services not initialised")
    return data_client, ai_analyzer, broker_client, strategy_engine  # type: ignore


# ──────────────────────────────────────────────────────────────────────────
# Mock data seeder
# ──────────────────────────────────────────────────────────────────────────

async def _seed_mock_data(db: AsyncSession) -> None:
    """Generate 30 days of historical trades and daily reports for the dashboard."""
    import numpy as np

    # Check if data already exists
    existing = await crud.get_trade_history(db, limit=1)
    if existing:
        logger.info("Mock data already exists, skipping seed")
        return

    np.random.seed(42)
    symbols = settings.SYMBOLS
    today = datetime.utcnow()
    balance = 100_000.0

    base_prices = {
        "AAPL": 180.0,
        "TSLA": 250.0,
        "MSFT": 380.0,
        "GOOGL": 140.0,
        "AMZN": 170.0,
    }

    for day_offset in range(29, -1, -1):
        day = today - timedelta(days=day_offset)
        date_str = day.strftime("%Y-%m-%d")
        day_start = datetime(day.year, day.month, day.day, 9, 30)
        day_end = datetime(day.year, day.month, day.day, 16, 0)

        day_pnl = 0.0
        day_wins = 0
        day_losses = 0
        day_trades = 0

        # 1-3 trades per day
        for _ in range(random.randint(1, 3)):
            symbol = random.choice(symbols)
            base = base_prices.get(symbol, 100.0)
            side = random.choice(["BUY", "SELL"])

            # Random walk from base
            entry_offset = np.random.normal(0, base * 0.02)
            entry_price = round(base + entry_offset, 2)

            # Trade is held 1-5 days
            hold_days = random.randint(1, 5)
            exit_day = day + timedelta(days=hold_days)
            exit_offset = np.random.normal(0, base * 0.025)
            exit_price = round(entry_price + exit_offset, 2)

            qty = random.randint(5, 50)
            is_buy = side == "BUY"
            pnl = round((exit_price - entry_price) * qty, 2) if is_buy else round((entry_price - exit_price) * qty, 2)
            pnl_pct = round((exit_price / entry_price - 1) * 100, 2)

            if pnl > 0:
                day_wins += 1
            else:
                day_losses += 1
            day_trades += 1
            day_pnl += pnl

            trade_data = {
                "symbol": symbol,
                "side": side,
                "qty": qty,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "entry_time": day_start + timedelta(hours=random.uniform(0, 6)),
                "exit_time": min(exit_day, today),
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "status": "CLOSED",
                "stop_loss": round(entry_price * 0.98, 2) if is_buy else round(entry_price * 1.02, 2),
                "take_profit": round(entry_price * 1.05, 2) if is_buy else round(entry_price * 0.95, 2),
                "strategy": "historical_mock",
                "ai_reasoning": f"Mock analysis for {symbol} on {date_str}: {'bullish' if pnl > 0 else 'bearish'} signals detected.",
                "ai_confidence": random.randint(60, 95),
            }

            trade_obj = await crud.create_trade(db, trade_data)

            # Update balance
            balance += pnl

        report_data = {
            "date": date_str,
            "total_pnl": round(day_pnl, 2),
            "win_count": day_wins,
            "loss_count": day_losses,
            "total_trades": day_trades,
            "win_rate": round(day_wins / day_trades * 100, 1) if day_trades > 0 else 0.0,
            "starting_balance": round(balance - day_pnl, 2),
            "ending_balance": round(balance, 2),
            "notes": f"Mock daily report for {date_str}",
        }
        await crud.create_daily_report(db, report_data)


# ──────────────────────────────────────────────────────────────────────────
# API Endpoints
# ──────────────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health_check() -> dict[str, Any]:
    """Simple health-check endpoint."""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "mock_mode": settings.MOCK_MODE,
        "version": "1.0.0",
    }


@app.get("/api/account")
async def get_account() -> dict[str, Any]:
    """Return account summary: balance, buying_power, total PnL."""
    _, _, broker, _ = _get_services()
    account = await broker.get_account()
    return account


@app.get("/api/positions")
async def get_positions(
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return all current positions."""
    _, _, broker, _ = _get_services()
    positions = await broker.get_positions()

    # Also sync with DB
    for pos in positions:
        await crud.update_position(
            db,
            {
                "symbol": pos["symbol"],
                "qty": pos["qty"],
                "avg_entry_price": pos.get("avg_entry_price", 0),
                "current_price": pos.get("current_price", pos.get("market_value", 0) / max(pos["qty"], 1)),
                "unrealized_pnl": pos.get("unrealized_pl", 0),
            },
        )

    return positions


@app.get("/api/trades")
async def get_trades(
    limit: int = Query(50, ge=1, le=500),
    status: str | None = Query(None),
    symbol: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return trade history with optional filters."""
    trades = await crud.get_trade_history(db, limit=limit, status=status, symbol=symbol)
    return trades


@app.get("/api/trades/today")
async def get_trades_today(
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return all trades from today."""
    today = datetime.utcnow().date()
    trades = await crud.get_trades_by_date(db, today)
    return trades


@app.get("/api/daily-reports")
async def get_daily_reports(
    limit: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return the most recent daily PnL reports."""
    reports = await crud.get_daily_reports(db, limit=limit)
    return reports


@app.get("/api/analyze/{symbol}")
async def analyze_symbol(symbol: str) -> dict[str, Any]:
    """Run an AI analysis on a single symbol without executing a trade."""
    dc, ai, _, _ = _get_services()

    symbol = symbol.upper()
    quote = await dc.get_stock_quote(symbol)
    indicators = await dc.get_quote_with_indicators(symbol)

    price_data = {
        "price": quote.get("price", 0),
        "change_pct": quote.get("change_pct", 0),
        "volume": quote.get("volume", 0),
        "timestamp": quote.get("timestamp", ""),
    }

    decision = await ai.analyze_market(symbol, price_data, indicators)

    return {
        "symbol": symbol,
        "price_data": price_data,
        "indicators": {
            "price": indicators.get("price"),
            "sma_20": indicators.get("sma_20"),
            "sma_50": indicators.get("sma_50"),
            "ema_20": indicators.get("ema_20"),
            "ema_50": indicators.get("ema_50"),
            "rsi_14": indicators.get("rsi_14"),
            "volume": indicators.get("volume"),
        },
        "decision": decision,
    }


@app.post("/api/run-analysis")
async def trigger_daily_analysis(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Manually trigger the daily analysis run."""
    dc, ai, broker, engine = _get_services()
    try:
        result = await run_daily(
            data_client=dc,
            ai_analyzer=ai,
            broker_client=broker,
            strategy_engine=engine,
            db_session=db,
            config=settings,
        )
        return result
    except Exception as exc:
        logger.exception("Daily analysis run failed")
        raise HTTPException(status_code=500, detail=f"Analysis run failed: {str(exc)}") from exc


@app.get("/api/performance")
async def get_performance(
    days: int = Query(30, ge=1, le=365),
) -> dict[str, Any]:
    """Return aggregated performance summary."""
    _, _, _, engine = _get_services()
    summary = await engine.get_performance_summary(days=days)
    return summary
