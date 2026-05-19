from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from app.config import settings
from app.core.logger import setup_logging, logger
from app.api.routes import router
from app.services.telegram_service import TelegramService
from app.services.market_service import MarketService
from app.strategies.strategy_engine import StrategyEngine

setup_logging()

app = FastAPI(title="Forex Signal Bot")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

startup_tasks = []


@app.on_event("startup")
async def on_startup():
    logger.info("Starting Forex Signal Bot")
    tg = TelegramService()
    market = MarketService()
    strategy = StrategyEngine()

    # send startup notification
    try:
        await tg.send_startup()
    except Exception as e:
        logger.exception("Startup notification failed: %s", e)

    # schedule scanner loop
    loop = asyncio.get_event_loop()
    loop.create_task(market.run_scanner(strategy, tg))
    loop.create_task(tg.heartbeat_task())
    if settings.TELEGRAM_WEBHOOK_URL:
        try:
            await tg.setup_webhook()
        except Exception as e:
            logger.exception("Telegram webhook setup failed: %s", e)
    else:
        loop.create_task(tg.poll_updates())


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Shutting down")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=int(settings.PORT), reload=True)
