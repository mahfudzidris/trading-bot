"""Market watcher daemon — runs evaluate_symbol on a loop during market hours.

The watcher is started as a background asyncio task in the FastAPI lifespan.
It checks Alpaca's market clock, and only runs analysis when the market is open
(on weekdays between 9:30-16:00 ET). Outside market hours it sleeps efficiently,
waking up every N minutes to re-check the clock.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class MarketWatcher:
    """Background loop that runs strategy evaluation during market hours.

    Parameters
    ----------
    strategy_engine : StrategyEngine
        The engine with evaluate_symbol / run_daily_analysis.
    broker_client : AlpacaClient
        Used to fetch market clock status.
    interval_minutes : int
        How often (in minutes) to check during market hours.
    auto_run : bool
        Whether the loop should actually run evaluation (vs just sleep).
    """

    def __init__(
        self,
        strategy_engine: Any,
        broker_client: Any,
        interval_minutes: int = 30,
        auto_run: bool = False,
        db_session_factory: Any = None,
    ) -> None:
        self.engine = strategy_engine
        self.broker = broker_client
        self.interval = interval_minutes
        self.auto_run = auto_run
        self._task: asyncio.Task | None = None
        self._running = False
        self._last_tick_error: str | None = None
        self._last_tick_time: datetime | None = None
        self._total_ticks: int = 0
        self._failed_ticks: int = 0
        self._db_factory = db_session_factory  # async generator that yields AsyncSession

    # ── Public API ──────────────────────────────────────────────────────

    @property
    def status(self) -> dict[str, Any]:
        """Return a status snapshot for the health endpoint."""
        return {
            "running": self.is_alive,
            "auto_run": self.auto_run,
            "interval_minutes": self.interval,
            "total_ticks": self._total_ticks,
            "failed_ticks": self._failed_ticks,
            "last_tick_time": self._last_tick_time.isoformat() if self._last_tick_time else None,
            "last_tick_error": self._last_tick_error,
        }

    @property
    def is_alive(self) -> bool:
        return self._running and self._task is not None and not self._task.done()

    async def start(self) -> None:
        """Start the background watcher loop."""
        if self.is_alive:
            logger.warning("Market watcher already running — skipping start")
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info(
            "🚀 Market watcher started (interval=%d min, auto_run=%s)",
            self.interval,
            self.auto_run,
        )

    async def stop(self) -> None:
        """Stop the background watcher loop gracefully."""
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("⏹ Market watcher stopped")

    def set_auto_run(self, enabled: bool) -> None:
        """Toggle auto_run at runtime (no restart needed)."""
        self.auto_run = enabled
        logger.info("Market watcher auto_run → %s", enabled)

    def set_interval(self, minutes: int) -> None:
        """Change check interval at runtime."""
        self.interval = max(1, minutes)
        logger.info("Market watcher interval → %d min", self.interval)

    # ── Internal loop ───────────────────────────────────────────────────

    async def _loop(self) -> None:
        """Main loop — runs until :meth:`stop` is called."""
        logger.info("Market watcher loop started (pid=%s)", id(self))

        while self._running:
            try:
                await self._tick()
            except asyncio.CancelledError:
                logger.info("Market watcher cancelled")
                break
            except Exception as exc:
                logger.exception("Market watcher tick error: %s", exc)

            # Sleep between ticks (check every N minutes regardless of market state)
            await asyncio.sleep(self.interval * 60)

        logger.info("Market watcher loop exited")

    async def _tick(self) -> None:
        """Single tick — check clock, run analysis if market open & auto_run."""
        if not self.auto_run:
            logger.debug("Market watcher: auto_run=OFF, sleeping")
            return

        # 1. Check market clock via Alpaca
        try:
            clock = await self.broker.get_clock()
        except Exception:
            logger.warning("Market watcher: cannot fetch market clock, skipping tick")
            self._last_tick_error = "Cannot fetch market clock"
            return

        is_open = clock.get("is_open", False)

        if not is_open:
            logger.debug("Market watcher: market closed, sleeping until next tick")
            return

        # 2. Market is open — run the strategy engine
        logger.info("📊 Market watcher — market OPEN, running analysis...")
        self._total_ticks += 1

        try:
            result = await self.engine.run_daily_analysis()
            analyses = result.get("analyses", [])

            total_pnl = sum(a.get("pnl_impact", 0) for a in analyses)
            executed = [a for a in analyses if a.get("action_taken") is not None]
            decisions = [a.get("decision", {}).get("action", "HOLD") for a in analyses]

            # 3. Verify orders and persist to DB
            for a in executed:
                order = a.get("action_taken", {}).get("order", {})
                if order.get("status") == "FAILED":
                    err = order.get("error", "Unknown error")
                    logger.error("🔴 Auto-trade FAILED: %s", err)
                    self._last_tick_error = f"Order failed: {err}"
                    self._failed_ticks += 1
                elif order.get("status") in ("accepted", "new", "pending_new", "filled"):
                    logger.info("✅ Auto-trade order accepted by Alpaca: %s", order.get("id"))

            # 4. Persist executed trades to database
            if executed and self._db_factory:
                try:
                    from db.crud import create_trade

                    async for session in self._db_factory():
                        for a in executed:
                            action = a.get("action_taken", {})
                            decision = a.get("decision", {})
                            order = action.get("order", {})
                            # Skip failed orders
                            if order.get("status") == "FAILED":
                                continue
                            trade_data = {
                                "symbol": a["symbol"],
                                "side": action.get("type", decision.get("action", "HOLD")),
                                "qty": action.get("qty", 0),
                                # Use filled price from Alpaca order, fallback to analysis price
                                "entry_price": order.get("filled_avg_price", 0) or action.get("price", 0),
                                "stop_loss": order.get("stop_loss", decision.get("stop_loss")),
                                "take_profit": order.get("take_profit", decision.get("take_profit")),
                                "strategy": "daily_ai_analysis",
                                "ai_reasoning": decision.get("reasoning", ""),
                                "ai_confidence": decision.get("confidence", 0),
                            }
                            created = await create_trade(session, trade_data)
                            logger.info("💾 Trade saved to DB: %s %s qty=%s @ $%.2f",
                                        trade_data["symbol"], trade_data["side"],
                                        trade_data["qty"], trade_data["entry_price"])
                        break  # Only use first session
                    logger.info("✅ Auto-trade DB persistence complete")
                except Exception as exc:
                    logger.warning("⚠️ Could not persist trades to DB: %s", exc)
                    self._last_tick_error = f"DB persistence failed: {exc}"

            logger.info(
                "📊 Market watcher tick complete: %d symbol(s), "
                "decisions=%s, %d executed, PnL=%.2f",
                len(analyses),
                decisions,
                len(executed),
                total_pnl,
            )
            self._last_tick_time = datetime.utcnow()
            self._last_tick_error = None
        except Exception as exc:
            logger.exception("🔴 Market watcher tick FAILED: %s", exc)
            self._last_tick_error = str(exc)
            self._failed_ticks += 1
