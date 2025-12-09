"""Logging configuration helpers."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

from loguru import logger

# 日志目录
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)


def setup_logging(level: str = "INFO", log_to_file: bool = True) -> None:
    """Configure stdlib logging and integrate loguru.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to write logs to file
    """

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
    
    # 控制台输出
    logger.add(
        sys.stdout, 
        level=level, 
        enqueue=True, 
        backtrace=False, 
        diagnose=False, 
        colorize=sys.stdout.isatty(),
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # 文件输出
    if log_to_file:
        logger.add(
            LOG_DIR / "app.log",
            level=level,
            enqueue=True,
            backtrace=True,
            diagnose=True,
            rotation="10 MB",  # 每10MB轮转
            retention="7 days",  # 保留7天
            compression="zip",  # 压缩旧日志
            encoding="utf-8",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
        )
        
        # 单独的错误日志文件
        logger.add(
            LOG_DIR / "error.log",
            level="ERROR",
            enqueue=True,
            backtrace=True,
            diagnose=True,
            rotation="10 MB",
            retention="30 days",
            compression="zip",
            encoding="utf-8",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
        )


def set_log_level(level: str, log_to_file: bool = True) -> None:
    """Adjust log level at runtime."""

    logger.remove()
    logger.add(
        sys.stdout, 
        level=level.upper(), 
        enqueue=True, 
        backtrace=False, 
        diagnose=False, 
        colorize=sys.stdout.isatty(),
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    if log_to_file:
        logger.add(
            LOG_DIR / "app.log",
            level=level.upper(),
            enqueue=True,
            backtrace=True,
            diagnose=True,
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            encoding="utf-8",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
        )
