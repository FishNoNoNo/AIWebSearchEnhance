from __future__ import annotations

import sys

from loguru import logger

from src.core.config_loader import LoggingSettings


def configure_logging(settings: LoggingSettings) -> None:
    logger.remove()
    serialize = settings.format == "json"
    if settings.output == "stdout":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
        sink = sys.stdout
    else:
        sink = settings.output
    logger.add(
        sink,
        level=settings.level,
        serialize=serialize,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message} | {extra}",
        backtrace=False,
        diagnose=False,
        colorize=False,
    )


__all__ = ["configure_logging", "logger"]
