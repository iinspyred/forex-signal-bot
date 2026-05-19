from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging

import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD
from ta.volatility import AverageTrueRange

from app.core.state import Signal

logger = logging.getLogger(__name__)


class StrategyEngine:
    def __init__(self, cooldown_minutes: int = 30) -> None:
        self.cooldown = timedelta(minutes=cooldown_minutes)
        self._last_signal_at: dict[tuple[str, str, str], datetime] = {}

    def analyze(self, pair: str, timeframe: str, candles: pd.DataFrame) -> Signal | None:
        if len(candles) < 60:
            return None

        frame = self._with_indicators(candles)
        latest = frame.iloc[-1]
        previous = frame.iloc[-2]

        if latest[["rsi", "ema20", "ema50", "macd", "macd_signal", "atr"]].isna().any():
            return None

        trend = "Bullish" if latest["ema20"] > latest["ema50"] else "Bearish"
        volatility_ok = self._volatility_ok(latest)
        volume_ok = self._volume_ok(frame)
        bullish_cross = previous["ema20"] <= previous["ema50"] and latest["ema20"] > latest["ema50"]
        bearish_cross = previous["ema20"] >= previous["ema50"] and latest["ema20"] < latest["ema50"]
        macd_bullish = previous["macd"] <= previous["macd_signal"] and latest["macd"] > latest["macd_signal"]
        macd_bearish = previous["macd"] >= previous["macd_signal"] and latest["macd"] < latest["macd_signal"]

        direction: str | None = None
        strategy = ""
        if latest["rsi"] < 30 and bullish_cross and macd_bullish and volatility_ok:
            direction = "BUY"
            strategy = "EMA crossover + RSI oversold + MACD bullish crossover"
        elif latest["rsi"] > 70 and bearish_cross and macd_bearish and volatility_ok:
            direction = "SELL"
            strategy = "EMA crossover + RSI overbought + MACD bearish crossover"

        if direction is None or self._is_duplicate(pair, timeframe, direction):
            return None

        confidence = self._confidence_score(latest, volume_ok, volatility_ok, direction)
        self._last_signal_at[(pair, timeframe, direction)] = datetime.now(UTC)

        return Signal(
            pair=pair,
            timeframe=timeframe.replace("min", "m"),
            direction=direction,
            entry=float(latest["close"]),
            rsi=float(latest["rsi"]),
            trend=trend,
            confidence=confidence,
            strategy=strategy,
            timestamp=datetime.now(UTC),
            indicators={
                "ema20": float(latest["ema20"]),
                "ema50": float(latest["ema50"]),
                "macd": float(latest["macd"]),
                "macd_signal": float(latest["macd_signal"]),
                "atr": float(latest["atr"]),
            },
        )

    def _with_indicators(self, candles: pd.DataFrame) -> pd.DataFrame:
        frame = candles.copy()
        close = frame["close"]
        high = frame["high"]
        low = frame["low"]
        frame["rsi"] = RSIIndicator(close=close, window=14).rsi()
        frame["ema20"] = EMAIndicator(close=close, window=20).ema_indicator()
        frame["ema50"] = EMAIndicator(close=close, window=50).ema_indicator()
        macd = MACD(close=close)
        frame["macd"] = macd.macd()
        frame["macd_signal"] = macd.macd_signal()
        frame["atr"] = AverageTrueRange(high=high, low=low, close=close, window=14).average_true_range()
        return frame

    def _is_duplicate(self, pair: str, timeframe: str, direction: str) -> bool:
        key = (pair, timeframe, direction)
        last_seen = self._last_signal_at.get(key)
        return bool(last_seen and datetime.now(UTC) - last_seen < self.cooldown)

    @staticmethod
    def _volatility_ok(latest: pd.Series) -> bool:
        close = float(latest["close"])
        atr = float(latest["atr"])
        return close > 0 and 0.00005 <= atr / close <= 0.02

    @staticmethod
    def _volume_ok(frame: pd.DataFrame) -> bool:
        if "volume" not in frame or frame["volume"].sum() <= 0:
            return True
        recent_volume = float(frame["volume"].tail(5).mean())
        baseline = float(frame["volume"].tail(30).mean())
        return baseline <= 0 or recent_volume >= baseline * 0.8

    @staticmethod
    def _confidence_score(latest: pd.Series, volume_ok: bool, volatility_ok: bool, direction: str) -> float:
        rsi = float(latest["rsi"])
        macd_gap = abs(float(latest["macd"]) - float(latest["macd_signal"]))
        ema_gap = abs(float(latest["ema20"]) - float(latest["ema50"]))
        score = 50.0
        score += min(20.0, macd_gap * 100_000)
        score += min(15.0, ema_gap * 100_000)
        if direction == "BUY":
            score += min(10.0, max(0.0, 30.0 - rsi))
        else:
            score += min(10.0, max(0.0, rsi - 70.0))
        if volume_ok:
            score += 5.0
        if volatility_ok:
            score += 5.0
        return round(min(score, 99.0), 2)
