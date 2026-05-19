from __future__ import annotations

import sqlite3
from pathlib import Path

from app.core.state import Signal


class SignalRepository:
    def __init__(self, database_url: str) -> None:
        if database_url.startswith("sqlite:///"):
            self.path = Path(database_url.replace("sqlite:///", "", 1))
        else:
            self.path = Path("signals.db")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pair TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    entry REAL NOT NULL,
                    rsi REAL NOT NULL,
                    trend TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    strategy TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
                """
            )

    def save_signal(self, signal: Signal) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO signals (
                    pair, timeframe, direction, entry, rsi, trend, confidence, strategy, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    signal.pair,
                    signal.timeframe,
                    signal.direction,
                    signal.entry,
                    signal.rsi,
                    signal.trend,
                    signal.confidence,
                    signal.strategy,
                    signal.timestamp.isoformat(),
                ),
            )
