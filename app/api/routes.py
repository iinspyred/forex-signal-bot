from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.config import Settings, get_settings

router = APIRouter()


class TradingViewWebhook(BaseModel):
    pair: str = Field(min_length=3, max_length=12)
    timeframe: str = Field(min_length=1, max_length=8)
    direction: str = Field(pattern="^(BUY|SELL)$")
    price: float = Field(gt=0)
    message: str | None = Field(default=None, max_length=500)


@router.get("/")
async def root(settings: Annotated[Settings, Depends(get_settings)]) -> dict[str, object]:
    return {
        "name": settings.app_name,
        "status": "online",
        "active_pairs": settings.pairs,
        "timeframes": tuple(tf.replace("min", "m") for tf in settings.timeframes),
    }


@router.get("/health")
async def health(request: Request) -> dict[str, object]:
    state = request.app.state.runtime_state
    snapshot = state.snapshot()
    return {
        "status": "healthy" if snapshot["scanner_running"] else "starting",
        **snapshot,
    }


@router.get("/signals")
async def signals(request: Request, limit: int = 50) -> dict[str, object]:
    state = request.app.state.runtime_state
    return {"signals": state.signals(max(1, min(limit, 100)))}


@router.get("/stats")
async def stats(request: Request, settings: Annotated[Settings, Depends(get_settings)]) -> dict[str, object]:
    snapshot = request.app.state.runtime_state.snapshot()
    return {
        "uptime_seconds": snapshot["uptime_seconds"],
        "active_pairs": settings.pairs,
        "timeframes": tuple(tf.replace("min", "m") for tf in settings.timeframes),
        "total_signals": snapshot["total_signals"],
        "wins": snapshot["wins"],
        "losses": snapshot["losses"],
        "win_rate": None,
        "last_signal": snapshot["last_signal"],
    }


@router.post("/webhook/tradingview")
async def tradingview_webhook(payload: TradingViewWebhook) -> dict[str, object]:
    return {
        "accepted": True,
        "received_at": datetime.now(UTC).isoformat(),
        "payload": payload.model_dump(),
    }
