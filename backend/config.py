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
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # ── Database ──────────────────────────────────────────────────────────
    DB_PATH: str = "data/trading.db"

    # ── Trading Parameters ────────────────────────────────────────────────
    SYMBOLS: List[str] = ["AAPL", "TSLA", "MSFT", "GOOGL", "AMZN"]
    TRADE_MAX_POSITION_SIZE: float = 0.1
    TRADE_STOP_LOSS_PCT: float = 0.02
    TRADE_TAKE_PROFIT_PCT: float = 0.05

    # ── Operational ──────────────────────────────────────────────────────
    ALPACA_PAPER: bool = True
    MOCK_MODE: bool = True
    PORT: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
