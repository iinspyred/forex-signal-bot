from __future__ import annotations

import pandas as pd

from app.strategies.strategy_engine import StrategyEngine


def _candles(closes: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "datetime": pd.date_range("2026-01-01", periods=len(closes), freq="min", tz="UTC"),
            "open": closes,
            "high": [value + 0.0005 for value in closes],
            "low": [value - 0.0005 for value in closes],
            "close": closes,
            "volume": [100.0 for _ in closes],
        }
    )


def test_no_signal_for_flat_market() -> None:
    engine = StrategyEngine(cooldown_minutes=30)
    signal = engine.analyze("EUR/USD", "1min", _candles([1.1 for _ in range(120)]))
    assert signal is None


def test_duplicate_prevention() -> None:
    engine = StrategyEngine(cooldown_minutes=30)
    engine._last_signal_at[("EUR/USD", "1min", "BUY")] = pd.Timestamp.utcnow().to_pydatetime()
    assert engine._is_duplicate("EUR/USD", "1min", "BUY") is True
