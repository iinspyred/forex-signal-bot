import logging
import os
from logging.handlers import RotatingFileHandler
from app.config import settings


def setup_logging() -> None:
    os.makedirs("logs", exist_ok=True)
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(level)

    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    fh = RotatingFileHandler("logs/forex_bot.log", maxBytes=5_000_000, backupCount=3)
    fh.setFormatter(fmt)
    logger.addHandler(fh)


setup_logging()
logger = logging.getLogger("forex_bot")
