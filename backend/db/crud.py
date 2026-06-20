"""Async CRUD operations for the trading database."""

from __future__ import annotations

import logging
import json
from datetime import datetime, date
from typing import Any, Optional

from sqlalchemy import select, func, desc, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Trade, DailyReport, Position, BacktestResult, TradeStatus

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────
# Trades
# ──────────────────────────────────────────────────────────────────────────

async def create_trade(db: AsyncSession, trade_data: dict[str, Any]) -> dict[str, Any]:
    """Create a new trade record and return it as a dict."""
    trade = Trade(
        symbol=trade_data["symbol"],
        side=trade_data["side"],
        qty=trade_data["qty"],
        entry_price=trade_data["entry_price"],
        entry_time=trade_data.get("entry_time", datetime.utcnow()),
        stop_loss=trade_data.get("stop_loss"),
        take_profit=trade_data.get("take_profit"),
        strategy=trade_data.get("strategy"),
        ai_reasoning=trade_data.get("ai_reasoning"),
        ai_confidence=trade_data.get("ai_confidence"),
        status=TradeStatus.OPEN,
    )
    db.add(trade)
    await db.commit()
    await db.refresh(trade)
    logger.info("Created trade: %s %s %d @ %.2f", trade.symbol, trade.side.value, trade.qty, trade.entry_price)
    return trade.to_dict()


async def close_trade(
    db: AsyncSession, trade_id: int, exit_price: float, pnl: float | None = None
) -> dict[str, Any] | None:
    """Close an open trade by setting its exit data and returning the updated dict."""
    result = await db.execute(select(Trade).where(Trade.id == trade_id))
    trade = result.scalar_one_or_none()
    if trade is None:
        logger.warning("Trade %d not found", trade_id)
        return None

    # Calculate PnL if not provided
    if pnl is None:
        if trade.side == "BUY":
            pnl = round((exit_price - trade.entry_price) * trade.qty, 2)
        else:
            pnl = round((trade.entry_price - exit_price) * trade.qty, 2)

    pnl_pct = round((exit_price / trade.entry_price - 1) * 100, 2) if trade.entry_price else 0.0

    trade.exit_price = exit_price
    trade.exit_time = datetime.utcnow()
    trade.pnl = pnl
    trade.pnl_pct = pnl_pct
    trade.status = TradeStatus.CLOSED

    await db.commit()
    await db.refresh(trade)
    logger.info("Closed trade %d: pnl=%.2f", trade_id, pnl)
    return trade.to_dict()


async def get_open_trades(db: AsyncSession) -> list[dict[str, Any]]:
    """Return all currently open trades."""
    result = await db.execute(
        select(Trade).where(Trade.status == TradeStatus.OPEN).order_by(Trade.entry_time.desc())
    )
    return [t.to_dict() for t in result.scalars().all()]


async def get_trade_history(
    db: AsyncSession,
    limit: int = 50,
    status: str | None = None,
    symbol: str | None = None,
) -> list[dict[str, Any]]:
    """Return recent trade history with optional filters."""
    query = select(Trade)

    if status:
        try:
            ts = TradeStatus(status.upper())
            query = query.where(Trade.status == ts)
        except ValueError:
            pass

    if symbol:
        query = query.where(Trade.symbol == symbol.upper())

    query = query.order_by(Trade.entry_time.desc()).limit(limit)
    result = await db.execute(query)
    return [t.to_dict() for t in result.scalars().all()]


async def get_trades_by_date(db: AsyncSession, trade_date: date) -> list[dict[str, Any]]:
    """Return all trades that were entered on a specific date."""
    day_start = datetime(trade_date.year, trade_date.month, trade_date.day)
    day_end = datetime(trade_date.year, trade_date.month, trade_date.day, 23, 59, 59)

    result = await db.execute(
        select(Trade).where(
            Trade.entry_time >= day_start,
            Trade.entry_time <= day_end,
        ).order_by(Trade.entry_time.desc())
    )
    return [t.to_dict() for t in result.scalars().all()]


# ──────────────────────────────────────────────────────────────────────────
# Daily Reports
# ──────────────────────────────────────────────────────────────────────────

async def create_daily_report(
    db: AsyncSession, report_data: dict[str, Any]
) -> dict[str, Any]:
    """Create or update a daily PnL report."""
    date_str = report_data["date"]

    # Check if report exists for this date
    result = await db.execute(
        select(DailyReport).where(DailyReport.date == date_str)
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.total_pnl = report_data.get("total_pnl", existing.total_pnl)
        existing.win_count = report_data.get("win_count", existing.win_count)
        existing.loss_count = report_data.get("loss_count", existing.loss_count)
        existing.total_trades = report_data.get("total_trades", existing.total_trades)
        existing.win_rate = report_data.get("win_rate", existing.win_rate)
        existing.starting_balance = report_data.get("starting_balance", existing.starting_balance)
        existing.ending_balance = report_data.get("ending_balance", existing.ending_balance)
        existing.notes = report_data.get("notes", existing.notes)
        await db.commit()
        await db.refresh(existing)
        return existing.to_dict()

    report = DailyReport(
        date=date_str,
        total_pnl=report_data.get("total_pnl", 0.0),
        win_count=report_data.get("win_count", 0),
        loss_count=report_data.get("loss_count", 0),
        total_trades=report_data.get("total_trades", 0),
        win_rate=report_data.get("win_rate", 0.0),
        starting_balance=report_data.get("starting_balance", 0.0),
        ending_balance=report_data.get("ending_balance", 0.0),
        notes=report_data.get("notes"),
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report.to_dict()


async def get_daily_reports(
    db: AsyncSession, limit: int = 30
) -> list[dict[str, Any]]:
    """Return the most recent daily reports."""
    result = await db.execute(
        select(DailyReport).order_by(DailyReport.date.desc()).limit(limit)
    )
    return [r.to_dict() for r in result.scalars().all()]


# ──────────────────────────────────────────────────────────────────────────
# Positions
# ──────────────────────────────────────────────────────────────────────────

async def update_position(
    db: AsyncSession, position_data: dict[str, Any]
) -> dict[str, Any]:
    """Upsert a position record and return it as a dict."""
    symbol = position_data["symbol"].upper()

    result = await db.execute(
        select(Position).where(Position.symbol == symbol)
    )
    pos = result.scalar_one_or_none()

    if pos:
        pos.qty = position_data.get("qty", pos.qty)
        pos.avg_entry_price = position_data.get("avg_entry_price", pos.avg_entry_price)
        pos.current_price = position_data.get("current_price", pos.current_price)
        pos.unrealized_pnl = position_data.get("unrealized_pnl", pos.unrealized_pnl)
        pos.updated_at = datetime.utcnow()
    else:
        pos = Position(
            symbol=symbol,
            qty=position_data["qty"],
            avg_entry_price=position_data["avg_entry_price"],
            current_price=position_data.get("current_price", 0.0),
            unrealized_pnl=position_data.get("unrealized_pnl", 0.0),
        )
        db.add(pos)

    await db.commit()
    await db.refresh(pos)
    return pos.to_dict()


async def get_positions(db: AsyncSession) -> list[dict[str, Any]]:
    """Return all tracked positions."""
    result = await db.execute(select(Position).order_by(Position.symbol))
    return [p.to_dict() for p in result.scalars().all()]


async def delete_position(db: AsyncSession, symbol: str) -> bool:
    """Remove a position when it is fully closed."""
    result = await db.execute(
        select(Position).where(Position.symbol == symbol.upper())
    )
    pos = result.scalar_one_or_none()
    if pos:
        await db.delete(pos)
        await db.commit()
        return True
    return False


# ──────────────────────────────────────────────────────────────────────────
# Backtest Results
# ──────────────────────────────────────────────────────────────────────────

async def save_backtest_result(
    db: AsyncSession, result_dict: dict
) -> dict[str, Any]:
    """Save a completed backtest result to the database."""
    # Serialise complex fields to JSON
    monthly_returns = result_dict.get("monthly_returns", {})
    errors_list = result_dict.get("errors", [])
    trades_list = result_dict.get("trades", [])
    equity_curve = result_dict.get("equity_curve", [])

    bt = BacktestResult(
        symbol=result_dict.get("symbol", ""),
        start_date=result_dict.get("start_date", ""),
        end_date=result_dict.get("end_date", ""),
        initial_capital=result_dict.get("initial_capital", 100_000.0),
        days=result_dict.get("days", 0),
        total_pnl=result_dict.get("total_pnl", 0.0),
        total_pnl_pct=result_dict.get("total_pnl_pct", 0.0),
        final_capital=result_dict.get("final_capital", 0.0),
        total_trades=result_dict.get("total_trades", 0),
        wins=result_dict.get("wins", 0),
        losses=result_dict.get("losses", 0),
        win_rate=result_dict.get("win_rate", 0.0),
        avg_win=result_dict.get("avg_win", 0.0),
        avg_loss=result_dict.get("avg_loss", 0.0),
        best_trade=result_dict.get("best_trade", 0.0),
        worst_trade=result_dict.get("worst_trade", 0.0),
        avg_trade=result_dict.get("avg_trade", 0.0),
        profit_factor=result_dict.get("profit_factor", 0.0),
        expectancy=result_dict.get("expectancy", 0.0),
        max_drawdown=result_dict.get("max_drawdown", 0.0),
        max_drawdown_pct=result_dict.get("max_drawdown_pct", 0.0),
        sharpe_ratio=result_dict.get("sharpe_ratio", 0.0),
        sortino_ratio=result_dict.get("sortino_ratio", 0.0),
        calmar_ratio=result_dict.get("calmar_ratio", 0.0),
        cagr=result_dict.get("cagr", 0.0),
        volatility=result_dict.get("volatility", 0.0),
        avg_bars_held=result_dict.get("avg_bars_held", 0.0),
        max_consecutive_wins=result_dict.get("max_consecutive_wins", 0),
        max_consecutive_losses=result_dict.get("max_consecutive_losses", 0),
        monthly_returns_json=json.dumps(monthly_returns) if monthly_returns else None,
        errors=json.dumps(errors_list) if errors_list else None,
    )
    db.add(bt)
    await db.commit()
    await db.refresh(bt)

    # Also save individual trades from the backtest into the trades table
    for trade in trades_list:
        try:
            entry_time = datetime.strptime(trade.get("entry_time", ""), "%Y-%m-%d") if trade.get("entry_time") else datetime.utcnow()
            exit_time = datetime.strptime(trade.get("exit_time", ""), "%Y-%m-%d") if trade.get("exit_time") else None
        except (ValueError, TypeError):
            entry_time = datetime.utcnow()
            exit_time = None

        trade_data = {
            "symbol": trade.get("symbol", bt.symbol),
            "side": trade.get("side", "BUY"),
            "qty": trade.get("qty", 0),
            "entry_price": trade.get("entry_price", 0.0),
            "exit_price": trade.get("exit_price"),
            "entry_time": entry_time,
            "exit_time": exit_time,
            "pnl": trade.get("pnl"),
            "pnl_pct": trade.get("pnl_pct"),
            "status": "CLOSED",
            "stop_loss": trade.get("stop_loss"),
            "take_profit": trade.get("take_profit"),
            "strategy": f"backtest_{bt.symbol}_{bt.start_date}_{bt.end_date}",
            "ai_reasoning": trade.get("ai_reasoning", ""),
            "ai_confidence": trade.get("ai_confidence", 0),
        }
        await create_trade(db, trade_data)

    return bt.to_dict()


async def get_backtest_results(
    db: AsyncSession, limit: int = 20
) -> list[dict[str, Any]]:
    """Return the most recent backtest results."""
    result = await db.execute(
        select(BacktestResult).order_by(BacktestResult.created_at.desc()).limit(limit)
    )
    return [r.to_dict() for r in result.scalars().all()]


async def get_backtest_by_id(
    db: AsyncSession, backtest_id: int
) -> dict[str, Any] | None:
    """Fetch a single backtest result by ID."""
    result = await db.execute(
        select(BacktestResult).where(BacktestResult.id == backtest_id)
    )
    bt = result.scalar_one_or_none()
    if bt is None:
        return None
    d = bt.to_dict()
    # Parse stored JSON fields
    if bt.monthly_returns_json:
        try:
            d["monthly_returns"] = json.loads(bt.monthly_returns_json)
        except (json.JSONDecodeError, TypeError):
            d["monthly_returns"] = {}
    if bt.errors:
        try:
            d["errors"] = json.loads(bt.errors)
        except (json.JSONDecodeError, TypeError):
            d["errors"] = []
    return d
