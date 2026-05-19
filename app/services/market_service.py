import asyncio
from typing import List, Dict, Any
import httpx
import pandas as pd
from app.config import settings
from app.core.logger import logger
from app.strategies.strategy_engine import StrategyEngine
from app.services.telegram_service import TelegramService

TD_BASE = "https://api.twelvedata.com"


class MarketService:
    """Fetches candle data from TwelveData and manages scanning tasks."""

    def __init__(self):
        self.td_api_key = settings.TWELVEDATA_API_KEY
        self.pairs = settings.PAIRS
        self.timeframes = settings.TIMEFRAMES
        self.client = httpx.AsyncClient(timeout=20.0)

    async def fetch_candles(self, pair: str, interval: str, outputsize: int = 200) -> pd.DataFrame:
        # TwelveData expects symbol like EUR/USD -> EUR/USD
        params = {
            "symbol": pair,
            "interval": interval,
            "outputsize": outputsize,
            "format": "JSON",
            "apikey": self.td_api_key,
        }
        url = f"{TD_BASE}/time_series"
        r = await self.client.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        if "values" not in data:
            logger.error("No candle data for %s %s: %s", pair, interval, data)
            return pd.DataFrame()
        df = pd.DataFrame(data["values"])  # strings
        # convert types and sort
        df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.rename(columns={"datetime": "time"})
        df = df.sort_values("time").reset_index(drop=True)
        return df

    async def run_scanner(self, strategy: StrategyEngine, telegram: TelegramService) -> None:
        """Main loop: fetch candles, run strategies, send signals."""
        # Polling loop; keeps resource usage low by spacing requests.
        while True:
            try:
                for pair in self.pairs:
                    for tf in self.timeframes:
                        df = await self.fetch_candles(pair, tf)
                        if df.empty:
                            continue
                        signals = strategy.analyze(df, pair, tf)
                        for sig in signals:
                            await telegram.send_signal(pair, tf, sig["side"], sig["entry"], sig["details"]) 
                # sleep to avoid tight loop; adjust based on smallest timeframe
                await asyncio.sleep(15)
            except Exception:
                logger.exception("Scanner loop error")
                await asyncio.sleep(5)
