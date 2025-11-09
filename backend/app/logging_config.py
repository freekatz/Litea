"""Logging configuration helpers."""

from __future__ import annotations

import logging
import sys
from typing import Optional

from loguru import logger


def setup_logging(level: str = "INFO") -> None:
    """Configure stdlib logging and integrate loguru."""

    class InterceptHandler(logging.Handler):
        """Redirect standard logging to loguru."""

        def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover
            try:
                level_name = logger.level(record.levelname).name
            except ValueError:
                level_name = str(record.levelno)
            logger.opt(depth=6, exception=record.exc_info).log(level_name, record.getMessage())

    logging.basicConfig(handlers=[InterceptHandler()], level=logging.getLevelName(level))
    logger.remove()
    logger.add(sys.stdout, level=level, enqueue=True, backtrace=False, diagnose=False, colorize=sys.stdout.isatty())


def set_log_level(level: str) -> None:
    """Adjust log level at runtime."""

    logger.remove()
    logger.add(sys.stdout, level=level.upper(), enqueue=True, backtrace=False, diagnose=False, colorize=sys.stdout.isatty())
