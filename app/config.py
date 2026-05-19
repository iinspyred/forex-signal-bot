from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables only."""

    app_name: str = "AI Forex Signal Bot"
    environment: Literal["development", "production", "test"] = "development"
    log_level: str = "INFO"

    twelvedata_api_key: str = Field(default="", alias="TWELVEDATA_API_KEY")
    finnhub_api_key: str = Field(default="", alias="FINNHUB_API_KEY")
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(default="", alias="TELEGRAM_CHAT_ID")

    scan_interval_seconds: int = Field(default=60, alias="SCAN_INTERVAL_SECONDS", ge=15)
    signal_cooldown_minutes: int = Field(default=30, alias="SIGNAL_COOLDOWN_MINUTES", ge=1)
    heartbeat_interval_seconds: int = Field(default=3600, alias="HEARTBEAT_INTERVAL_SECONDS", ge=60)
    request_timeout_seconds: float = Field(default=12.0, alias="REQUEST_TIMEOUT_SECONDS", ge=2)
    api_max_retries: int = Field(default=3, alias="API_MAX_RETRIES", ge=1, le=5)
    database_url: str = Field(default="sqlite:///./signals.db", alias="DATABASE_URL")

    pairs: tuple[str, ...] = ("EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD")
    timeframes: tuple[str, ...] = ("1min", "5min")
    max_recent_signals: int = Field(default=100, alias="MAX_RECENT_SIGNALS", ge=10)
    rate_limit_per_minute: int = Field(default=120, alias="RATE_LIMIT_PER_MINUTE", ge=10)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
        case_sensitive=False,
    )

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        return value.upper()

    @property
    def telegram_enabled(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)

    @property
    def market_data_enabled(self) -> bool:
        return bool(self.twelvedata_api_key or self.finnhub_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
