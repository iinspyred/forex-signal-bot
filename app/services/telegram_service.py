from __future__ import annotations

import asyncio
import logging
from html import escape

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes

from app.config import Settings
from app.core.state import RuntimeState, Signal

logger = logging.getLogger(__name__)


class TelegramService:
    def __init__(self, settings: Settings, state: RuntimeState) -> None:
        self.settings = settings
        self.state = state
        self.application: Application | None = None
        self._running = False

    async def start(self) -> None:
        if not self.settings.telegram_bot_token:
            logger.warning("Telegram bot token is not configured; Telegram listener disabled")
            return

        self.application = Application.builder().token(self.settings.telegram_bot_token).build()
        self.application.add_handler(CommandHandler("start", self._start_command))
        self.application.add_handler(CommandHandler("help", self._help_command))
        self.application.add_handler(CommandHandler("status", self._status_command))

        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(drop_pending_updates=True)
        self._running = True
        logger.info("Telegram polling listener started")

    async def stop(self) -> None:
        if not self.application or not self._running:
            return
        await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()
        self._running = False

    async def send_startup(self) -> None:
        await self.send_message("Forex signal bot started. Scanner is warming up.")

    async def send_heartbeat(self) -> None:
        snapshot = self.state.snapshot()
        await self.send_message(
            "Heartbeat\n"
            f"Uptime: {snapshot['uptime_seconds']}s\n"
            f"Signals: {snapshot['total_signals']}\n"
            f"Errors: {snapshot['errors']}"
        )

    async def send_error(self, message: str) -> None:
        await self.send_message(f"Error alert: {escape(message)}")

    async def send_signal(self, signal: Signal) -> None:
        icon = "BUY" if signal.direction == "BUY" else "SELL"
        message = (
            f"<b>{icon} SIGNAL</b>\n\n"
            f"Pair: <b>{escape(signal.pair)}</b>\n"
            f"Timeframe: {escape(signal.timeframe)}\n"
            f"Entry: {signal.entry:.5f}\n"
            f"RSI: {signal.rsi:.2f}\n"
            f"Trend: {escape(signal.trend)}\n"
            f"Confidence: {signal.confidence:.2f}%\n\n"
            f"Strategy:\n{escape(signal.strategy)}\n\n"
            f"Timestamp: {signal.timestamp.isoformat()}"
        )
        await self.send_message(message, parse_mode=ParseMode.HTML)

    async def send_message(self, message: str, parse_mode: str | None = None) -> None:
        if not self.application or not self.settings.telegram_chat_id:
            return
        try:
            await self.application.bot.send_message(
                chat_id=self.settings.telegram_chat_id,
                text=message,
                parse_mode=parse_mode,
                disable_web_page_preview=True,
            )
        except Exception:
            logger.exception("Telegram message delivery failed")

    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        del context
        if update.effective_message:
            await update.effective_message.reply_text(
                "Forex signal bot is online. Use /status for scanner health and latest signal."
            )

    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        del context
        if update.effective_message:
            await update.effective_message.reply_text("/start - Start bot\n/help - Commands\n/status - Bot status")

    async def _status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        del context
        snapshot = self.state.snapshot()
        last_signal = snapshot["last_signal"]
        text = (
            f"Scanner running: {snapshot['scanner_running']}\n"
            f"Uptime: {snapshot['uptime_seconds']}s\n"
            f"Signals: {snapshot['total_signals']}\n"
            f"Errors: {snapshot['errors']}\n"
            f"Last signal: {last_signal['direction'] + ' ' + last_signal['pair'] if last_signal else 'none'}"
        )
        if update.effective_message:
            await update.effective_message.reply_text(text)


async def safe_telegram_call(coro: object) -> None:
    try:
        await coro  # type: ignore[misc]
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("Telegram operation failed")
