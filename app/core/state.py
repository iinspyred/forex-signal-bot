from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from threading import Lock
from typing import Any


@dataclass(slots=True)
class Signal:
    pair: str
    timeframe: str
    direction: str
    entry: float
    rsi: float
    trend: str
    confidence: float
    strategy: str
    timestamp: datetime
    indicators: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["timestamp"] = self.timestamp.isoformat()
        return payload


class RuntimeState:
    def __init__(self, max_recent_signals: int = 100) -> None:
        self.started_at = datetime.now(UTC)
        self.max_recent_signals = max_recent_signals
        self.recent_signals: list[Signal] = []
        self.total_signals = 0
        self.errors = 0
        self.scanner_running = False
        self.last_scan_at: datetime | None = None
        self.last_heartbeat_at: datetime | None = None
        self.win_count = 0
        self.loss_count = 0
        self._lock = Lock()

    def uptime_seconds(self) -> int:
        return int((datetime.now(UTC) - self.started_at).total_seconds())

    def add_signal(self, signal: Signal) -> None:
        with self._lock:
            self.recent_signals.insert(0, signal)
            self.recent_signals = self.recent_signals[: self.max_recent_signals]
            self.total_signals += 1

    def mark_error(self) -> None:
        with self._lock:
            self.errors += 1

    def mark_scan(self) -> None:
        with self._lock:
            self.last_scan_at = datetime.now(UTC)

    def set_scanner_running(self, running: bool) -> None:
        with self._lock:
            self.scanner_running = running

    def mark_heartbeat(self) -> None:
        with self._lock:
            self.last_heartbeat_at = datetime.now(UTC)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            last_signal = self.recent_signals[0].to_dict() if self.recent_signals else None
            return {
                "started_at": self.started_at.isoformat(),
                "uptime_seconds": self.uptime_seconds(),
                "scanner_running": self.scanner_running,
                "last_scan_at": self.last_scan_at.isoformat() if self.last_scan_at else None,
                "last_heartbeat_at": self.last_heartbeat_at.isoformat() if self.last_heartbeat_at else None,
                "total_signals": self.total_signals,
                "errors": self.errors,
                "wins": self.win_count,
                "losses": self.loss_count,
                "last_signal": last_signal,
            }

    def signals(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            return [signal.to_dict() for signal in self.recent_signals[:limit]]
