"""Application configuration via pydantic-settings."""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Loads configuration from environment variables or .env file."""

    # ── API Keys ──────────────────────────────────────────────────────────
    TWELVEDATA_API_KEY: str = ""
    ALPACA_API_KEY: str = ""
    ALPACA_SECRET_KEY: str = ""
    DEEPSEEK_API_KEY: str = ""

    # ── Model / Provider ──────────────────────────────────────────────────
    DEEPSEEK_MODEL: str = "deepseek-v4-flash"

    # ── Database ──────────────────────────────────────────────────────────
    DB_PATH: str = "data/trading.db"

    # ── Trading Parameters ────────────────────────────────────────────────
    SYMBOLS: List[str] = ["SPLG"]
    TRADE_MAX_POSITION_SIZE: float = 0.1
    TRADE_STOP_LOSS_PCT: float = 0.01  # 1% SL (tighter for small capital)
    TRADE_TAKE_PROFIT_PCT: float = 0.02  # 2% TP

    # ── DCA (Dollar Cost Average) ─────────────────────────────────────────
    DCA_ENABLED: bool = True
    DCA_TRANCHES: int = 3  # split position into N entries

    # ── Trailing Stop ─────────────────────────────────────────────────────
    TRAILING_STOP_ENABLED: bool = True
    TRAILING_STOP_ACTIVATION_PCT: float = 0.01  # 1% profit → activate trailing
    TRAILING_STOP_TRAIL_PCT: float = 0.005  # 0.5% trail distance

    # ── Short Trades ──────────────────────────────────────────────────────
    SHORT_TRADES_ENABLED: bool = False  # Cash account can't short; enable for margin
    
    # ── Operational ──────────────────────────────────────────────────────
    ALPACA_PAPER: bool = True
    MOCK_MODE: bool = True
    AUTO_TRADE: bool = False
    MARKET_AUTO_RUN: bool = False    # 24/7 background watcher loop
    MARKET_WATCH_INTERVAL: int = 15  # minutes between market-hour checks
    PORT: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
