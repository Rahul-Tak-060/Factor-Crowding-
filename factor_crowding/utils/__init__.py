"""Logging utilities for the factor crowding package."""

import logging
import sys
from pathlib import Path
from typing import Optional

from factor_crowding.config import logging_config


def setup_logger(
    name: str,
    log_file: Path | None = None,
    level: str | None = None,
) -> logging.Logger:
    """Set up a logger with console and file handlers.

    Args:
        name: Logger name
        log_file: Optional path to log file. Uses config default if None.
        level: Optional log level. Uses config default if None.

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    log_level = getattr(logging, (level or logging_config.log_level).upper())
    logger.setLevel(log_level)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        logging_config.log_format,
        datefmt=logging_config.date_format,
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler
    if log_file is None:
        log_file = Path(logging_config.log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(
        logging_config.log_format,
        datefmt=logging_config.date_format,
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger
