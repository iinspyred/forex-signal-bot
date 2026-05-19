from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

import httpx
import pandas as pd

from app.config import Settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class CandleRequest:
    pair: str
    timeframe: str
    outputsize: int = 120


class MarketDataError(RuntimeError):
    pass


class MarketService:
    """Async market data client using TwelveData first and Finnhub as fallback."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = httpx.AsyncClient(timeout=settings.request_timeout_seconds)

    async def close(self) -> None:
        await self._client.aclose()

    async def fetch_candles(self, request: CandleRequest) -> pd.DataFrame:
        errors: list[str] = []
        if self.settings.twelvedata_api_key:
            try:
                return await self._fetch_twelvedata(request)
            except Exception as exc:
                errors.append(f"TwelveData: {exc}")
                logger.warning("TwelveData fetch failed for %s %s: %s", request.pair, request.timeframe, exc)

        if self.settings.finnhub_api_key:
            try:
                return await self._fetch_finnhub_quote_snapshot(request)
            except Exception as exc:
                errors.append(f"Finnhub: {exc}")
                logger.warning("Finnhub fallback failed for %s: %s", request.pair, exc)

        raise MarketDataError("; ".join(errors) or "No market data provider configured")

    async def _fetch_twelvedata(self, request: CandleRequest) -> pd.DataFrame:
        params = {
            "symbol": request.pair,
            "interval": request.timeframe,
            "outputsize": request.outputsize,
            "apikey": self.settings.twelvedata_api_key,
            "format": "JSON",
        }
        payload = await self._get_json("https://api.twelvedata.com/time_series", params)
        if payload.get("status") == "error":
            raise MarketDataError(str(payload.get("message", "TwelveData error")))

        values = payload.get("values")
        if not values:
            raise MarketDataError("TwelveData returned no candles")

        frame = pd.DataFrame(values)
        frame["datetime"] = pd.to_datetime(frame["datetime"], utc=True)
        for column in ("open", "high", "low", "close"):
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
        if "volume" in frame:
            frame["volume"] = pd.to_numeric(frame["volume"], errors="coerce").fillna(0)
        else:
            frame["volume"] = 0.0

        frame = frame.dropna(subset=["open", "high", "low", "close"])
        frame = frame.sort_values("datetime").reset_index(drop=True)
        if len(frame) < 60:
            raise MarketDataError("Not enough candle history for indicators")
        return frame

    async def _fetch_finnhub_quote_snapshot(self, request: CandleRequest) -> pd.DataFrame:
        symbol = f"OANDA:{request.pair.replace('/', '_')}"
        payload = await self._get_json(
            "https://finnhub.io/api/v1/quote",
            {"symbol": symbol, "token": self.settings.finnhub_api_key},
        )
        current = float(payload.get("c") or 0)
        previous = float(payload.get("pc") or current)
        high = float(payload.get("h") or max(current, previous))
        low = float(payload.get("l") or min(current, previous))
        if current <= 0:
            raise MarketDataError("Finnhub returned empty quote")

        now = pd.Timestamp.utcnow()
        rows = []
        base = previous
        step = (current - previous) / 120 if current != previous else 0.0
        for index in range(120):
            close = base + step * index
            rows.append(
                {
                    "datetime": now - pd.Timedelta(minutes=120 - index),
                    "open": close - step,
                    "high": max(high, close),
                    "low": min(low, close),
                    "close": close,
                    "volume": 0.0,
                }
            )
        return pd.DataFrame(rows)

    async def _get_json(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        delay = 1.0
        last_error: Exception | None = None
        for attempt in range(1, self.settings.api_max_retries + 1):
            try:
                response = await self._client.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except (httpx.HTTPError, ValueError) as exc:
                last_error = exc
                if attempt == self.settings.api_max_retries:
                    break
                await asyncio.sleep(delay)
                delay *= 2
        raise MarketDataError(str(last_error))
