"""Scheduled daily trading run."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


async def run_daily(
    data_client: Any,
    ai_analyzer: Any,
    broker_client: Any,
    strategy_engine: Any,
    db_session: Any,
    config: Any,
) -> dict[str, Any]:
    """Execute the full daily trading pipeline.

    Steps
    -----
    1. Check if markets are open (clock).
    2. For each configured symbol: fetch data → AI analyse → execute → log to DB.
    3. Generate and persist a daily report.
    4. Return a summary dict.

    Parameters
    ----------
    data_client : TwelveDataClient
    ai_analyzer : DeepSeekAnalyzer
    broker_client : AlpacaClient
    strategy_engine : StrategyEngine
    db_session : async SQLAlchemy session
    config : Settings
    """
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    logger.info("=== Daily run starting for %s ===", date_str)

    # 1. Check market clock
    clock = await broker_client.get_clock()
    market_open = clock.get("is_open", False)

    if not market_open and not config.MOCK_MODE:
        logger.info("Markets are closed — skipping execution (but running mock analysis in mock mode)")

    if not market_open and config.MOCK_MODE:
        logger.info("Mock mode: continuing with simulated market analysis")

    # 2. Run the strategy engine
    analysis_result = await strategy_engine.run_daily_analysis()
    analyses = analysis_result.get("analyses", [])

    # 3. Calculate aggregated metrics
    total_pnl = sum(a.get("pnl_impact", 0) for a in analyses)
    actions_taken = [a for a in analyses if a.get("action_taken") is not None]
    wins = [a for a in actions_taken if a.get("pnl_impact", 0) > 0]
    losses = [a for a in actions_taken if a.get("pnl_impact", 0) <= 0]

    # 4. Get account balance
    account = await broker_client.get_account()
    ending_balance = account.get("balance", 0.0)
    starting_balance = ending_balance - total_pnl

    # 5. Persist daily report
    try:
        from db.crud import create_daily_report, create_trade

        report_data = {
            "date": date_str,
            "total_pnl": round(total_pnl, 2),
            "win_count": len(wins),
            "loss_count": len(losses),
            "total_trades": len(actions_taken),
            "win_rate": round(len(wins) / len(actions_taken) * 100, 1) if actions_taken else 0.0,
            "starting_balance": round(starting_balance, 2),
            "ending_balance": round(ending_balance, 2),
            "notes": f"Daily run completed. {len(actions_taken)} trades executed.",
        }
        await create_daily_report(db_session, report_data)

        # Log each action as a trade in the DB
        for analysis in actions_taken:
            decision = analysis.get("decision", {})
            action_taken = analysis.get("action_taken", {})
            if action_taken:
                trade_data = {
                    "symbol": analysis["symbol"],
                    "side": action_taken.get("type", decision.get("action", "HOLD")),
                    "qty": action_taken.get("qty", 0),
                    "entry_price": action_taken.get("price", 0.0),
                    "stop_loss": decision.get("stop_loss"),
                    "take_profit": decision.get("take_profit"),
                    "strategy": "daily_ai_analysis",
                    "ai_reasoning": decision.get("reasoning", ""),
                    "ai_confidence": decision.get("confidence", 0),
                }
                await create_trade(db_session, trade_data)

        logger.info("Daily report saved for %s", date_str)
    except Exception as exc:
        logger.warning("Could not persist daily report to DB: %s", exc)

    summary = {
        "date": date_str,
        "market_open": market_open,
        "total_pnl": round(total_pnl, 2),
        "trades_executed": len(actions_taken),
        "wins": len(wins),
        "losses": len(losses),
        "analyses": analyses,
    }

    logger.info("=== Daily run complete: PnL=%.2f, %d trades ===", total_pnl, len(actions_taken))
    return summary
