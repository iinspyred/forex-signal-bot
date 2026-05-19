import asyncio
from datetime import datetime
from typing import Optional
from telegram import Bot
from app.config import settings
from app.core.logger import logger


class TelegramService:
    """Handles Telegram notifications via python-telegram-bot Bot (async).

    Uses environment config from `settings`.
    """

    def __init__(self):
        self.bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self._last_heartbeat = None

    async def send_message(self, text: str) -> None:
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=text, parse_mode="HTML")
            logger.info("Sent Telegram message")
        except Exception:
            logger.exception("Failed to send Telegram message")

    async def send_startup(self) -> None:
        text = f"🤖 <b>Forex Signal Bot started</b>\nTime: {datetime.utcnow().isoformat()}Z"
        await self.send_message(text)

    async def send_signal(self, pair: str, timeframe: str, side: str, entry: float, details: dict) -> None:
        text = (
            f"{ '🚀 BUY SIGNAL' if side=='BUY' else '🔻 SELL SIGNAL' }\n"
            f"Pair: {pair}\n"
            f"Timeframe: {timeframe}\n"
            f"Entry: {entry:.5f}\n"
            + "\n".join([f"{k}: {v}" for k, v in details.items()])
            + f"\nTime: {datetime.utcnow().isoformat()}Z"
        )
        await self.send_message(text)

    async def heartbeat_task(self) -> None:
        """Send hourly heartbeat to indicate service is alive."""
        while True:
            try:
                await self.send_message(f"💓 Heartbeat: {datetime.utcnow().isoformat()}Z")
            except Exception:
                logger.exception("Heartbeat failed")
            await asyncio.sleep(3600)
