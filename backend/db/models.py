"""SQLAlchemy async models for the trading database."""

from __future__ import annotations

from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    Enum as SAEnum,
    create_engine,
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import enum


# ── Enums ──────────────────────────────────────────────────────────────────

class TradeStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class TradeSide(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"


# ── Base ───────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ── Models ─────────────────────────────────────────────────────────────────

class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(SAEnum(TradeSide), nullable=False)
    qty = Column(Integer, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    entry_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    exit_time = Column(DateTime, nullable=True)
    pnl = Column(Float, nullable=True)
    pnl_pct = Column(Float, nullable=True)
    status = Column(SAEnum(TradeStatus), default=TradeStatus.OPEN, nullable=False)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    strategy = Column(String(100), nullable=True)
    ai_reasoning = Column(Text, nullable=True)
    ai_confidence = Column(Integer, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "symbol": self.symbol,
            "side": self.side.value if self.side else None,
            "qty": self.qty,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "entry_time": self.entry_time.isoformat() if self.entry_time else None,
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "pnl": self.pnl,
            "pnl_pct": self.pnl_pct,
            "status": self.status.value if self.status else None,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "strategy": self.strategy,
            "ai_reasoning": self.ai_reasoning,
            "ai_confidence": self.ai_confidence,
        }


class DailyReport(Base):
    __tablename__ = "daily_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), nullable=False, unique=True, index=True)
    total_pnl = Column(Float, default=0.0)
    win_count = Column(Integer, default=0)
    loss_count = Column(Integer, default=0)
    total_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    starting_balance = Column(Float, default=0.0)
    ending_balance = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "date": self.date,
            "total_pnl": self.total_pnl,
            "win_count": self.win_count,
            "loss_count": self.loss_count,
            "total_trades": self.total_trades,
            "win_rate": self.win_rate,
            "starting_balance": self.starting_balance,
            "ending_balance": self.ending_balance,
            "notes": self.notes,
        }


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, unique=True, index=True)
    qty = Column(Integer, nullable=False)
    avg_entry_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    unrealized_pnl = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "symbol": self.symbol,
            "qty": self.qty,
            "avg_entry_price": self.avg_entry_price,
            "current_price": self.current_price,
            "unrealized_pnl": self.unrealized_pnl,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ── Database initialisation ────────────────────────────────────────────────

_engine: object | None = None
_session_maker: async_sessionmaker[AsyncSession] | None = None


async def get_db_path() -> str:
    """Return the database path configured in the app settings."""
    # Lazy import to avoid circular dependency at module level
    import sys

    if "config" in sys.modules:
        from config import settings

        return settings.DB_PATH
    return "data/trading.db"


async def init_db(db_path: str | None = None) -> AsyncGenerator[AsyncSession, None]:
    """Create tables and return a session generator."""
    global _engine, _session_maker

    if db_path is None:
        db_path = await get_db_path()

    # Ensure directory exists
    import os

    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

    async_engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", echo=False)
    _engine = async_engine

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    _session_maker = async_sessionmaker(async_engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a DB session."""
    if _session_maker is None:
        await init_db()
    maker = _session_maker
    if maker is None:
        raise RuntimeError("Database not initialised")
    async with maker() as session:
        yield session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yield an async DB session."""
    async for session in get_session():
        yield session
