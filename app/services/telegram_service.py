import asyncio
from datetime import datetime
from typing import Any
from telegram import Bot, Update
from telegram.error import TelegramError
from app.config import settings
from app.core.logger import logger


class TelegramService:
    """Handles Telegram notifications and command processing."""

    def __init__(self):
        self.bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.polling_offset = 0

    async def send_message(self, text: str, chat_id: str | None = None) -> None:
        target = chat_id or self.chat_id
        try:
            await self.bot.send_message(chat_id=target, text=text, parse_mode="HTML")
            logger.info("Sent Telegram message to %s", target)
        except Exception:
            logger.exception("Failed to send Telegram message")

    async def send_startup(self) -> None:
        text = f"🤖 <b>Forex Signal Bot started</b>\nTime: {datetime.utcnow().isoformat()}Z"
        await self.send_message(text)

    async def send_signal(self, pair: str, timeframe: str, side: str, entry: float, details: dict) -> None:
        text = (
            f"{ '🚀 BUY SIGNAL' if side == 'BUY' else '🔻 SELL SIGNAL' }\n"
            f"Pair: {pair}\n"
            f"Timeframe: {timeframe}\n"
            f"Entry: {entry:.5f}\n"
            + "\n".join([f"{k}: {v}" for k, v in details.items()])
            + f"\nTime: {datetime.utcnow().isoformat()}Z"
        )
        await self.send_message(text)

    async def setup_webhook(self) -> bool:
        if settings.TELEGRAM_WEBHOOK_URL:
            try:
                result = await self.bot.set_webhook(settings.TELEGRAM_WEBHOOK_URL)
                if result:
                    logger.info("Telegram webhook set to %s", settings.TELEGRAM_WEBHOOK_URL)
                    return True
                logger.warning("Telegram webhook setup returned false")
            except TelegramError:
                logger.exception("Failed to set Telegram webhook")
            return False
        logger.info("No Telegram webhook URL configured; falling back to polling")
        return False

    async def poll_updates(self) -> None:
        logger.info("Starting Telegram polling listener")
        while True:
            try:
                updates = await self.bot.get_updates(offset=self.polling_offset, timeout=20, allowed_updates=["message"])
                for update in updates:
                    self.polling_offset = update.update_id + 1
                    await self._process_update(update)
            except Exception:
                logger.exception("Polling updates failed")
                await asyncio.sleep(5)

    async def handle_webhook(self, payload: dict[str, Any]) -> None:
        try:
            logger.debug("Received Telegram webhook payload: %s", payload)
            update = Update.de_json(payload, self.bot)
            await self._process_update(update)
        except Exception:
            logger.exception("Webhook update handling failed")
            raise

    async def _process_update(self, update: Update) -> None:
        if not update.message or not update.message.text:
            return
        text = update.message.text.strip()
        chat_id = str(update.message.chat.id)
        if text.startswith("/start"):
            await self._reply_start(chat_id)
            return
        if text.startswith("/status"):
            await self._reply_status(chat_id)
            return
        if text.startswith("/help"):
            await self._reply_help(chat_id)
            return
        logger.debug("Received unsupported Telegram message: %s", text)

    async def _reply_start(self, chat_id: str) -> None:
        text = (
            "🤖 <b>Forex Signal Bot</b>\n"
            "Hello! I am your forex signal assistant.\n"
            "Use /status to check health and /help for available commands."
        )
        await self.send_message(text, chat_id=chat_id)

    async def _reply_status(self, chat_id: str) -> None:
        text = (
            "📡 <b>Bot Status</b>\n"
            f"Status: <b>Running</b>\n"
            f"Pairs: {', '.join(settings.PAIRS)}\n"
            f"Timeframes: {', '.join(settings.TIMEFRAMES)}\n"
            f"Webhook: {'enabled' if settings.TELEGRAM_WEBHOOK_URL else 'polling'}"
        )
        await self.send_message(text, chat_id=chat_id)

    async def _reply_help(self, chat_id: str) -> None:
        text = (
            "📘 <b>Forex Signal Bot Commands</b>\n"
            "/start - Initialize bot and confirm connectivity\n"
            "/status - Show bot health and active pairs\n"
            "/help - Show this message"
        )
        await self.send_message(text, chat_id=chat_id)
