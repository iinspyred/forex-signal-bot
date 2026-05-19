from typing import List, Dict, Any
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD
from app.core.logger import logger


class StrategyEngine:
    """Modular strategy engine implementing indicators and signal rules."""

    def __init__(self):
        self.recent_signals = {}  # prevent duplicates: (pair,tf) -> last_side

    def _compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        # ensure monotonically increasing time index
        df = df.copy()
        df["rsi"] = RSIIndicator(df["close"], window=14).rsi()
        df["ema20"] = EMAIndicator(df["close"], window=20).ema_indicator()
        df["ema50"] = EMAIndicator(df["close"], window=50).ema_indicator()
        macd = MACD(df["close"]) 
        df["macd"] = macd.macd()
        df["macd_signal"] = macd.macd_signal()
        # volume moving average for confirmation
        df["vol_ma20"] = df["volume"].rolling(20).mean()
        return df

    def analyze(self, df: pd.DataFrame, pair: str, timeframe: str) -> List[Dict[str, Any]]:
        """Analyze dataframe and return list of signals.

        Each signal is a dict: {side, entry, details}
        """
        if df.shape[0] < 60:
            return []
        df = self._compute_indicators(df)
        last = df.iloc[-1]
        prev = df.iloc[-2]

        signals = []

        # EMA crossover
        ema_cross_up = prev["ema20"] < prev["ema50"] and last["ema20"] > last["ema50"]
        ema_cross_down = prev["ema20"] > prev["ema50"] and last["ema20"] < last["ema50"]

        # MACD crossover
        macd_bull = prev["macd"] < prev["macd_signal"] and last["macd"] > last["macd_signal"]
        macd_bear = prev["macd"] > prev["macd_signal"] and last["macd"] < last["macd_signal"]

        # RSI thresholds
        rsi = last["rsi"]

        # Volume confirmation
        vol_conf = last["volume"] > (last["vol_ma20"] if not pd.isna(last["vol_ma20"]) else 0)

        # BUY
        if rsi < 35 and ema_cross_up and macd_bull and vol_conf:
            side = "BUY"
            entry = float(last["close"])
            details = {"RSI": int(rsi), "Trend": "Bullish", "Strategy": "EMA+MACD+RSI"}
            if self._allow_signal(pair, timeframe, side):
                signals.append({"side": side, "entry": entry, "details": details})

        # SELL
        if rsi > 65 and ema_cross_down and macd_bear and vol_conf:
            side = "SELL"
            entry = float(last["close"])
            details = {"RSI": int(rsi), "Trend": "Bearish", "Strategy": "EMA+MACD+RSI"}
            if self._allow_signal(pair, timeframe, side):
                signals.append({"side": side, "entry": entry, "details": details})

        return signals

    def _allow_signal(self, pair: str, timeframe: str, side: str) -> bool:
        key = f"{pair}:{timeframe}"
        last = self.recent_signals.get(key)
        if last == side:
            # prevent duplicate consecutive signal
            logger.debug("Duplicate signal suppressed for %s %s", pair, timeframe)
            return False
        self.recent_signals[key] = side
        return True
