import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_logging(log_level: str = "INFO") -> None:
    """Configure console, application, and trade logs."""

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    root = logging.getLogger()
    root.setLevel(log_level)
    root.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    app_handler = RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    app_handler.setFormatter(formatter)
    app_handler.setLevel(log_level)

    error_handler = RotatingFileHandler(
        log_dir / "errors.log",
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)

    root.addHandler(console_handler)
    root.addHandler(app_handler)
    root.addHandler(error_handler)

    trade_logger = logging.getLogger("trades")
    trade_logger.setLevel(logging.INFO)
    trade_handler = RotatingFileHandler(
        log_dir / "trades.log",
        maxBytes=1_000_000,
        backupCount=10,
        encoding="utf-8",
    )
    trade_handler.setFormatter(formatter)
    trade_logger.addHandler(trade_handler)
    trade_logger.propagate = False
