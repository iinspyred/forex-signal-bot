from pydantic import Field
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    TWELVEDATA_API_KEY: str = Field(..., env="TWELVEDATA_API_KEY")
    FINNHUB_API_KEY: str = Field(..., env="FINNHUB_API_KEY")
    TELEGRAM_BOT_TOKEN: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: str = Field(..., env="TELEGRAM_CHAT_ID")
    PORT: int = Field(8000, env="PORT")
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    PAIRS: List[str] = Field(["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD"], env="PAIRS")
    TIMEFRAMES: List[str] = Field(["1m", "5m"], env="TIMEFRAMES")
    DATABASE_URL: str = Field("sqlite:///./data/signals.db", env="DATABASE_URL")

    class Config:
        env_file = ".env"


settings = Settings()
