"""
Common CLI utilities for SaqaParser command-line tools.

Provides shared functionality for argument parsing, logging setup, and error handling.
"""

import argparse
import contextlib
import logging
import sys
from pathlib import Path
from typing import Optional, Callable

# Add project root to Python path for direct script execution
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.config import config  # noqa: E402
from src.logging_config import setup_logging, disable_console_logging  # noqa: E402
from src.exceptions import SaqaParserError  # noqa: E402


def ensure_workspace_directories() -> None:
    """
    Ensure workspace directories exist, creating them if needed.

    This is called automatically when CLI commands start to avoid requiring
    users to run setup_workspace.py manually.
    """
    with contextlib.suppress(Exception):
        # If automatic setup fails, processors will handle directory creation
        # via their own validation, so we don't need to fail here
        config.setup_directories()


def setup_cli_logging(
    log_file: Optional[Path], verbose: bool = False, quiet: bool = False
) -> logging.Logger:
    """
    Set up logging for CLI applications with consistent configuration.

    Args:
        log_file: Path to log file (or None to use config default)
        verbose: Enable DEBUG level logging
        quiet: Suppress console output (only log to file)

    Returns:
        Configured logger instance
    """
    # Ensure workspace directories exist before setting up logging
    ensure_workspace_directories()

    log_level = logging.DEBUG if verbose else logging.INFO
    logger = setup_logging(log_file or config.log_file, level=log_level)

    if quiet:
        disable_console_logging(logger)

    return logger


def add_common_arguments(
    parser: argparse.ArgumentParser,
    include_log: bool = True,
    include_verbose: bool = True,
    include_quiet: bool = True,
) -> None:
    """
    Add common CLI arguments to an argument parser.

    Args:
        parser: ArgumentParser instance to add arguments to
        include_log: Include --log argument
        include_verbose: Include --verbose argument
        include_quiet: Include --quiet argument
    """
    if include_log:
        parser.add_argument(
            "--log", type=Path, default=None, help=f"Log file path (default: {config.log_file})"
        )

    if include_verbose:
        parser.add_argument(
            "-v", "--verbose", action="store_true", help="Enable verbose logging (DEBUG level)"
        )

    if include_quiet:
        parser.add_argument(
            "-q", "--quiet", action="store_true", help="Suppress console output (only log to file)"
        )


def handle_cli_execution(func: Callable[[], int], logger: logging.Logger) -> int:
    """
    Execute a CLI function with consistent error handling.

    Args:
        func: Function to execute (should return exit code)
        logger: Logger instance for error reporting

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    try:
        return func()

    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        return 130

    except SaqaParserError as e:
        logger.error(f"Error: {str(e)}")
        return 1

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        return 1
