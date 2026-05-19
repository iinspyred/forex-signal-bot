from fastapi import APIRouter
from datetime import datetime
from app.core.logger import logger
from app.config import settings

router = APIRouter()

START_TIME = datetime.utcnow()
_last_signals = []


@router.get("/")
async def root():
    return {"service": "forex-signal-bot", "uptime": (datetime.utcnow() - START_TIME).total_seconds()}


@router.get("/health")
async def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat() + "Z"}


@router.get("/signals")
async def signals():
    # placeholder returning last signals in memory
    return {"last_signals": _last_signals}


@router.get("/stats")
async def stats():
    return {"uptime": (datetime.utcnow() - START_TIME).total_seconds(), "pairs": settings.PAIRS}
