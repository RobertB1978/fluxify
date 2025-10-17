from __future__ import annotations

import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Any

from .config import settings

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s %(message)s"


def configure_logging(extra_handlers: list[logging.Handler] | None = None) -> None:
    log_dir = Path(settings.log_directory)
    log_dir.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level.upper())

    file_handler = TimedRotatingFileHandler(
        filename=log_dir / "backend.log",
        when="midnight",
        backupCount=settings.log_retention_days,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter(_LOG_FORMAT))

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(_LOG_FORMAT))

    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)

    if extra_handlers:
        for handler in extra_handlers:
            root_logger.addHandler(handler)


def get_logger(name: str, **extra: Any) -> logging.LoggerAdapter[Any]:
    base_logger = logging.getLogger(name)
    return logging.LoggerAdapter(base_logger, extra)
