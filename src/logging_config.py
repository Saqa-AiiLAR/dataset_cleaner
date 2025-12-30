"""
Centralized logging configuration for SaqaParser.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    log_file: Path, level: int = logging.INFO, console: bool = True, file_mode: str = "a"
) -> logging.Logger:
    """
    Set up logging configuration with both file and console handlers.

    Args:
        log_file: Path to the log file
        level: Logging level (default: INFO)
        console: Whether to include console output (default: True)
        file_mode: File mode for log file ('a' for append, 'w' for overwrite)

    Returns:
        Configured logger instance

    Raises:
        OSError: If log file directory cannot be created
    """
    logger = logging.getLogger("SaqaParser")
    logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # File handler - append mode by default
    try:
        # Ensure log file directory exists
        if log_file.parent and not log_file.parent.exists():
            log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8", mode=file_mode)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except OSError as e:
        # If file logging fails, log to stderr and re-raise
        sys.stderr.write(f"Warning: Cannot set up file logging: {e}\n")
        if not console:
            raise

    # Console handler (optional)
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = logging.Formatter("%(levelname)s - %(message)s")
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger


def get_logger(name: str = "SaqaParser") -> logging.Logger:
    """
    Get a logger instance by name.

    Args:
        name: Logger name (default: "SaqaParser")

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def disable_console_logging(logger: Optional[logging.Logger] = None) -> None:
    """
    Remove console handlers from logger.

    Args:
        logger: Logger instance (default: root SaqaParser logger)
    """
    if logger is None:
        logger = logging.getLogger("SaqaParser")

    # Remove all StreamHandlers (console handlers)
    for handler in logger.handlers[:]:
        if isinstance(handler, logging.StreamHandler):
            logger.removeHandler(handler)
