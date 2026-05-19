from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import AsyncIterator

from fastapi import FastAPI

from app.api.routes import router
from app.config import get_settings
from app.core.logging import configure_logging
from app.core.state import RuntimeState
from app.services.database import SignalRepository
from app.services.market_service import CandleRequest, MarketService
from app.services.telegram_service import TelegramService
from app.strategies.strategy_engine import StrategyEngine
from app.utils.rate_limit import RateLimitMiddleware

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)
trade_logger = logging.getLogger("trades")


async def scanner_loop(app: FastAPI) -> None:
    state: RuntimeState = app.state.runtime_state
    market: MarketService = app.state.market_service
    telegram: TelegramService = app.state.telegram_service
    strategy: StrategyEngine = app.state.strategy_engine
    repository: SignalRepository = app.state.signal_repository

    state.set_scanner_running(True)
    consecutive_errors = 0
    try:
        while True:
            cycle_started = datetime.now(UTC)
            for pair in settings.pairs:
                for timeframe in settings.timeframes:
                    try:
                        candles = await market.fetch_candles(CandleRequest(pair=pair, timeframe=timeframe))
                        signal = strategy.analyze(pair, timeframe, candles)
                        if signal:
                            state.add_signal(signal)
                            repository.save_signal(signal)
                            trade_logger.info("%s %s %s %.5f", signal.direction, signal.pair, signal.timeframe, signal.entry)
                            await telegram.send_signal(signal)
                        consecutive_errors = 0
                    except asyncio.CancelledError:
                        raise
                    except Exception as exc:
                        consecutive_errors += 1
                        state.mark_error()
                        logger.exception("Scan failed for %s %s", pair, timeframe)
                        if consecutive_errors in {3, 10}:
                            await telegram.send_error(f"Scanner failure streak: {consecutive_errors}. Last error: {exc}")
                    await asyncio.sleep(0.2)

            state.mark_scan()
            if (
                not state.last_heartbeat_at
                or (datetime.now(UTC) - state.last_heartbeat_at).total_seconds() >= settings.heartbeat_interval_seconds
            ):
                await telegram.send_heartbeat()
                state.mark_heartbeat()

            elapsed = (datetime.now(UTC) - cycle_started).total_seconds()
            await asyncio.sleep(max(1.0, settings.scan_interval_seconds - elapsed))
    except asyncio.CancelledError:
        logger.info("Scanner loop cancelled")
        raise
    finally:
        state.set_scanner_running(False)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.runtime_state = RuntimeState(settings.max_recent_signals)
    app.state.market_service = MarketService(settings)
    app.state.telegram_service = TelegramService(settings, app.state.runtime_state)
    app.state.strategy_engine = StrategyEngine(settings.signal_cooldown_minutes)
    app.state.signal_repository = SignalRepository(settings.database_url)

    await app.state.telegram_service.start()
    await app.state.telegram_service.send_startup()
    app.state.scanner_task = asyncio.create_task(scanner_loop(app))
    logger.info("Application startup complete")

    try:
        yield
    finally:
        app.state.scanner_task.cancel()
        await asyncio.gather(app.state.scanner_task, return_exceptions=True)
        await app.state.telegram_service.stop()
        await app.state.market_service.close()
        logger.info("Application shutdown complete")


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.rate_limit_per_minute)
app.include_router(router)
