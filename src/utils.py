"""
Utility functions for SaqaParser project.
"""
from __future__ import annotations

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional


# Deprecated: Use src.logging_config.setup_logging instead
def setup_logging(log_file: Path, level: int = logging.INFO) -> logging.Logger:
    """
    Set up logging configuration (DEPRECATED).
    
    This function is deprecated. Use src.logging_config.setup_logging instead.
    
    Args:
        log_file: Path to the log file
        level: Logging level (default: INFO)
    
    Returns:
        Configured logger instance
    """
    from .logging_config import setup_logging as _setup_logging
    return _setup_logging(log_file, level=level, console=True)


def validate_path(path: Path, must_exist: bool = True, must_be_file: bool = False) -> bool:
    """
    Validate a file or directory path.
    
    Args:
        path: Path to validate
        must_exist: Whether the path must exist
        must_be_file: Whether the path must be a file (False means directory)
    
    Returns:
        True if path is valid, False otherwise
    """
    if must_exist and not path.exists():
        return False
    
    if must_exist:
        if must_be_file and not path.is_file():
            return False
        if not must_be_file and not path.is_dir():
            return False
    
    return True


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
    
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def get_timestamp() -> str:
    """
    Get current timestamp as formatted string.
    
    Returns:
        Timestamp string in format "YYYY-MM-DD HH:MM:SS"
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_timestamp_folder_name() -> str:
    """
    Get current timestamp formatted as folder name.
    
    Returns:
        Folder name string in format "DD-MM-YY-HH-MM-SS"
        Example: "19-01-25-19-28-32" (19 January 2025, 19:28:32)
    """
    return datetime.now().strftime("%d-%m-%y-%H-%M-%S")


def add_error_context(error: Exception, context: str) -> Exception:
    """
    Add context to an error message.
    
    Args:
        error: Original exception
        context: Additional context to add
    
    Returns:
        Exception with added context (same type as input)
    """
    error_type = type(error)
    new_msg = f"{context}: {str(error)}"
    return error_type(new_msg)
