"""FastAPI Trading Bot — main application entry point."""

from __future__ import annotations

import logging
import random
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, date as date_type
from typing import Any
from enum import Enum

import traceback
from fastapi import FastAPI, Depends, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from data.twelvedata_client import TwelveDataClient
from ai.deepseek_analyzer import DeepSeekAnalyzer
from broker.alpaca_client import AlpacaClient
from strategy.engine import StrategyEngine
from db.models import init_db, get_db
from db import crud
from scheduler.daily_run import run_daily
from backtest.engine import BacktestEngine
from pydantic import BaseModel
from sentiment.sentiment_aggregator import SentimentAggregator

# ── Request models ─────────────────────────────────────────────────────────


class ExecuteTradeRequest(BaseModel):
    symbol: str
    side: str  # "BUY" or "SELL"
    qty: int
    ai_reasoning: str | None = None
    ai_confidence: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    strategy: str = "manual"


class BacktestRequest(BaseModel):
    symbol: str = "AAPL"
    start_date: str = "2025-01-01"
    end_date: str | None = None
    initial_capital: float = 100_000.0
    stop_loss_pct: float = 0.02
    take_profit_pct: float = 0.05
    max_position_size_pct: float = 0.1
    commission_pct: float = 0.001
    slippage_pct: float = 0.001
    use_ai: bool = True


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
sentiment_aggregator: SentimentAggregator | None = None


# ── Lifespan ───────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    global data_client, ai_analyzer, broker_client, strategy_engine, sentiment_aggregator

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
    sentiment_aggregator = SentimentAggregator(
        mock_mode=settings.MOCK_MODE,
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
    if sentiment_aggregator:
        await sentiment_aggregator.close()
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
        "http://100.108.97.116:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global exception handler to log tracebacks ─────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"},
    )


# ──────────────────────────────────────────────────────────────────────────
# Helper: get current service instances
# ──────────────────────────────────────────────────────────────────────────

def _get_services() -> tuple[TwelveDataClient, DeepSeekAnalyzer, AlpacaClient, StrategyEngine]:
    """Return the four global service objects (raises if not ready)."""
    if any(x is None for x in (data_client, ai_analyzer, broker_client, strategy_engine)):
        raise HTTPException(status_code=503, detail="Services not initialised")
    return data_client, ai_analyzer, broker_client, strategy_engine  # type: ignore


def _get_sentiment() -> SentimentAggregator:
    """Return the global SentimentAggregator (raises if not ready)."""
    if sentiment_aggregator is None:
        raise HTTPException(status_code=503, detail="Sentiment services not initialised")
    return sentiment_aggregator


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


# ══════════════════════════════════════════════════════════════════════════
# Strategy Endpoints
# ══════════════════════════════════════════════════════════════════════════


@app.get("/api/strategy")
async def get_strategy(
    symbol: str | None = Query(None, description="Symbol to fetch live data for. If omitted, static strategy info is returned without live prompt/data."),
) -> dict[str, Any]:
    """Return the AI analysis strategy configuration, prompt, and indicators used.

    When ?symbol=AAPL is provided, fetches live market data and generates the
    *exact* prompt that would be sent to DeepSeek in /api/analyze/{symbol},
    including real ensemble strategy signals.
    """
    from ai.deepseek_analyzer import DeepSeekAnalyzer
    from strategies import EnsembleStrategy

    dc, ai, broker, _ = _get_services()

    # ── Build the static strategy info first ──
    info = {
        "name": "AI-Powered Technical Analysis Strategy with Ensemble Signals",
        "description": "Combines 3 algorithmic strategies (Trend Following, Mean Reversion, Momentum) with DeepSeek LLM reasoning. Each strategy independently analyses indicators and produces a signal. The AI then acts as a meta-analyzer, weighing all strategy signals alongside raw market data to produce the final decision. In mock mode, the ensemble consensus primarily drives the decision with RSI/MA refinement.",
        "indicators": [
            {"name": "SMA(20)", "description": "20-period Simple Moving Average — short-term trend direction"},
            {"name": "SMA(50)", "description": "50-period Simple Moving Average — medium-term trend direction"},
            {"name": "EMA(20)", "description": "20-period Exponential Moving Average — fast, price-sensitive trend"},
            {"name": "EMA(50)", "description": "50-period Exponential Moving Average — slower, smoother trend"},
            {"name": "RSI(14)", "description": "14-period Relative Strength Index — overbought (>70) / oversold (<30) oscillator"},
            {"name": "Volume", "description": "Trading volume — confirms momentum strength"},
        ],
        "decision_fields": {
            "action": "BUY | SELL | HOLD",
            "confidence": "0-100 — how confident the AI is",
            "reasoning": "Natural language explanation of the decision",
            "take_profit": "Price target for profit taking",
            "stop_loss": "Stop-loss price to limit downside",
            "position_size_pct": "Percentage of capital to deploy (0.0 - 0.1 = 10%)",
        },
        "ensemble_strategies": [
            {
                "name": "Trend Following",
                "inputs": ["SMA(20)", "SMA(50)", "Price"],
                "logic": "BUY if price > SMA(20) > SMA(50); SELL if price < SMA(20) < SMA(50); confidence scales with SMA gap",
            },
            {
                "name": "Mean Reversion",
                "inputs": ["RSI(14)"],
                "logic": "BUY when RSI < 35 (oversold bounce); SELL when RSI > 65 (overbought drop); confidence scales with distance from neutral (50)",
            },
            {
                "name": "Momentum",
                "inputs": ["Price Change %", "SMA(20) gap", "Volume"],
                "logic": "Composite momentum score combining daily change % and price vs SMA(20). BUY/SELL when momentum exceeds 2.0σ; volume confirms confidence",
            },
        ],
        "mock_fallback_logic": [
            "Ensemble consensus determines primary action (majority vote of 3 strategies)",
            "RSI extremes refine the action if ensemble is split",
            "MA crossover confirms trend direction",
            "Above-average volume adjusts confidence ±5-10",
        ],
    }

    # ── Fetch live account info ──
    try:
        account = await broker.get_account()
        buying_power = account.get("buying_power", 0)
        cash = account.get("cash", 0)
    except Exception:
        buying_power = 0
        cash = 0

    result: dict[str, Any] = {
        **info,
        "risk_parameters": {
            "max_position_size_pct": settings.TRADE_MAX_POSITION_SIZE,
            "stop_loss_pct": settings.TRADE_STOP_LOSS_PCT,
            "take_profit_pct": settings.TRADE_TAKE_PROFIT_PCT,
            "symbols_tracked": settings.SYMBOLS,
            "mock_mode": settings.MOCK_MODE,
        },
        "account": {"buying_power": buying_power, "cash": cash},
        "model": {
            "provider": "DeepSeek",
            "model_name": settings.DEEPSEEK_MODEL,
            "temperature": 0.3,
            "max_tokens": 512,
        },
    }

    # ── If symbol is provided, fetch live data and generate real prompt ──
    selected_symbol = (symbol or "AAPL").upper()
    live_data = None

    if symbol:
        try:
            quote = await dc.get_stock_quote(selected_symbol)
            indicators = await dc.get_quote_with_indicators(selected_symbol)

            price_data = {
                "price": quote.get("price", 0),
                "change_pct": quote.get("change_pct", 0),
                "volume": quote.get("volume", 0),
                "timestamp": quote.get("timestamp", ""),
            }

            # Run ensemble strategies
            ensemble = EnsembleStrategy()
            signals = ensemble.analyze(indicators)
            strategy_summary = ensemble.get_summary(signals)
            signals_dicts = [s.to_dict() for s in signals]

            # Generate real prompt with live data + signals
            real_prompt = ai.build_prompt(selected_symbol, price_data, indicators, signals_dicts)

            live_data = {
                "symbol": selected_symbol,
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
                "strategy_signals": signals_dicts,
                "strategy_summary": strategy_summary,
                "prompt": real_prompt,
            }
        except Exception as exc:
            logger.warning("Could not fetch live data for %s: %s", selected_symbol, exc)
            live_data = {
                "symbol": selected_symbol,
                "error": str(exc),
                "prompt": None,
            }

    result["live_data"] = live_data
    return result


@app.get("/api/analyze/{symbol}")
async def analyze_symbol(symbol: str) -> dict[str, Any]:
    """Run an AI analysis on a single symbol without executing a trade.

    Now uses ensemble strategy signals (Trend, Mean Reversion, Momentum)
    AND aggregated market sentiment (Polymarket, Fear & Greed, News)
    as extra context for the DeepSeek AI model.
    """
    from strategies import EnsembleStrategy

    dc, ai, _, _ = _get_services()
    sentiment = _get_sentiment()

    symbol = symbol.upper()
    quote = await dc.get_stock_quote(symbol)
    indicators = await dc.get_quote_with_indicators(symbol)

    price_data = {
        "price": quote.get("price", 0),
        "change_pct": quote.get("change_pct", 0),
        "volume": quote.get("volume", 0),
        "timestamp": quote.get("timestamp", ""),
    }

    # ── Run ensemble strategy signals ──
    ensemble = EnsembleStrategy()
    signals = ensemble.analyze(indicators)
    strategy_summary = ensemble.get_summary(signals)
    signals_dicts = [s.to_dict() for s in signals]

    # ── Fetch market sentiment (Polymarket, Fear & Greed, News) ──
    market_sentiment = await sentiment.aggregate()

    decision = await ai.analyze_market(
        symbol, price_data, indicators, signals_dicts, market_sentiment,
    )

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
        "strategy_signals": signals_dicts,
        "strategy_summary": strategy_summary,
        "market_sentiment": market_sentiment,
    }


@app.post("/api/trade/execute")
async def execute_trade(
    req: ExecuteTradeRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Execute a manual buy/sell trade on Alpaca based on AI recommendation."""
    _, _, broker, _ = _get_services()

    # ── Place order on Alpaca ──
    order = await broker.place_market_order(req.symbol.upper(), req.qty, req.side.upper())

    if order.get("status") == "FAILED":
        raise HTTPException(status_code=500, detail=order.get("error", "Order execution failed"))

    # ── Save trade to local DB ──
    trade_data = {
        "symbol": req.symbol.upper(),
        "side": req.side.upper(),
        "qty": req.qty,
        "entry_price": order.get("filled_avg_price", 0),
        "stop_loss": req.stop_loss,
        "take_profit": req.take_profit,
        "strategy": req.strategy,
        "ai_reasoning": req.ai_reasoning,
        "ai_confidence": req.ai_confidence,
    }
    trade = await crud.create_trade(db, trade_data)

    # ── Sync positions from Alpaca ──
    try:
        positions = await broker.get_positions()
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
    except Exception as exc:
        logger.warning("Failed to sync positions after trade: %s", exc)

    return {"ok": True, "order": order, "trade": trade}


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


# ══════════════════════════════════════════════════════════════════════════
# Backtest Endpoints
# ══════════════════════════════════════════════════════════════════════════


@app.post("/api/backtest/run", response_model=dict[str, Any])
async def run_backtest_endpoint(
    req: BacktestRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Run a full backtest with the given parameters.

    Always uses internal mock-mode clients so backtesting is fast and
    never consumes real API quota, even when MOCK_MODE=false in .env.
    """
    # Always use mock mode for backtest — live market data / real AI calls
    # are unnecessary for historical simulation.
    dc = TwelveDataClient(api_key="backtest", mock_mode=True)
    ai = DeepSeekAnalyzer(api_key="backtest", mock_mode=True)

    strategy_params = {
        "stop_loss_pct": req.stop_loss_pct,
        "take_profit_pct": req.take_profit_pct,
        "max_position_size_pct": req.max_position_size_pct,
        "use_ai": req.use_ai,
    }

    engine = BacktestEngine(
        data_client=dc,
        ai_analyzer=ai,
        initial_capital=req.initial_capital,
        commission_pct=req.commission_pct,
        slippage_pct=req.slippage_pct,
    )

    try:
        result = await engine.run(
            symbol=req.symbol,
            start_date=req.start_date,
            end_date=req.end_date,
            strategy_params=strategy_params,
        )
        result_dict = result.to_dict()

        # Save to DB (creates backtest record + individual trades)
        try:
            await crud.save_backtest_result(db, result_dict)
        except Exception as save_exc:
            logger.warning("Failed to save backtest result: %s", save_exc)

        return {"ok": True, "result": result_dict}

    except Exception as exc:
        logger.exception("Backtest failed")
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        await dc.close()
        await ai.close()


@app.get("/api/backtest/results", response_model=list[dict[str, Any]])
async def get_backtest_results(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return all stored backtest results."""
    results = await crud.get_backtest_results(db, limit=limit)
    return results


@app.get("/api/backtest/results/{backtest_id}", response_model=dict[str, Any])
async def get_backtest_detail(
    backtest_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return a single backtest result by ID with full details."""
    result = await crud.get_backtest_by_id(db, backtest_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Backtest result not found")
    return result


# ── Settings ────────────────────────────────────────────────────────


class UpdateSettingsRequest(BaseModel):
    mock_mode: bool | None = None


@app.post("/api/settings")
async def update_settings(req: UpdateSettingsRequest) -> dict[str, bool | str]:
    """Update runtime settings and save to .env file.

    Currently supports toggling MOCK_MODE. The backend auto-reloads via
    --reload after writing, so the new value is picked up on the next
    startup. The endpoint returns immediately.
    """
    import os

    env_path = os.path.join(os.path.dirname(__file__), ".env")
    updates: list[str] = []

    if req.mock_mode is not None:
        val = "true" if req.mock_mode else "false"
        _update_env_file(env_path, "MOCK_MODE", val)
        updates.append(f"MOCK_MODE={val}")

    return {
        "ok": True,
        "updates": ", ".join(updates),
        "restart_required": True,
    }


def _update_env_file(path: str, key: str, value: str) -> None:
    """Find *key=...* in the file at *path* and replace it with *key=value*.

    If the key does not exist it is appended to the end.  The caller is
    expected to trigger a uvicorn reload (--reload picks up modified
    .py files automatically after the .env is written).
    """
    import os
    import re

    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(f"{key}={value}\n")
        return

    with open(path, "r") as f:
        lines = f.readlines()

    pattern = re.compile(rf"^{key}\s*=\s*.*", re.IGNORECASE)
    found = False
    new_lines: list[str] = []
    for line in lines:
        if pattern.match(line.strip()):
            new_lines.append(f"{key}={value}\n")
            found = True
        else:
            new_lines.append(line)

    if not found:
        new_lines.append(f"{key}={value}\n")

    with open(path, "w") as f:
        f.writelines(new_lines)
