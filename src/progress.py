"""
Simple progress bar utility with no external dependencies.

Provides visual feedback for long-running operations with percentage,
elapsed time, and ETA estimation.
"""

from __future__ import annotations

import sys
import time
from typing import Optional


class ProgressBar:
    """
    Simple progress bar that updates in place on a single line.

    Features:
    - Percentage completion
    - Current/total counts
    - Elapsed time
    - Estimated time remaining (ETA)
    - Graceful degradation for non-TTY environments

    Example:
        >>> progress = ProgressBar(total=100, desc="Processing")
        >>> for i in range(100):
        ...     progress.update(i + 1)
        >>> progress.finish()
        Processing: [=========================>] 100% (100/100) | 5.2s elapsed
    """

    def __init__(
        self, total: int, desc: str = "Processing", width: int = 25, disable: bool = False
    ):
        """
        Initialize progress bar.

        Args:
            total: Total number of items to process
            desc: Description text shown before the progress bar
            width: Width of the progress bar in characters
            disable: If True, disable progress bar (no output)
        """
        self.total = total
        self.desc = desc
        self.width = width
        self.disable = disable
        self.start_time = time.time()
        self.current = 0
        self.finished = False

        # Check if we're in a TTY (terminal) environment
        self.is_tty = hasattr(sys.stderr, "isatty") and sys.stderr.isatty()

        # If not TTY or disabled, suppress output
        if not self.is_tty or self.disable:
            self.disable = True

    def update(self, current: int, suffix: str = "") -> None:
        """
        Update progress bar to current position.

        Args:
            current: Current progress value (0 to total)
            suffix: Optional suffix text to append
        """
        # Update state FIRST, before checking disable/finished
        self.current = min(current, self.total)

        if self.disable or self.finished:
            return  # Skip output but state is already updated

        # Calculate percentage
        percent = (self.current / self.total) * 100 if self.total > 0 else 100

        # Calculate elapsed time
        elapsed = time.time() - self.start_time

        # Calculate ETA
        if self.current > 0 and self.current < self.total and elapsed > 0:
            rate = self.current / elapsed
            remaining = (self.total - self.current) / rate if rate > 0 else 0
            eta_str = f"ETA: {self._format_time(remaining)}"
        else:
            eta_str = ""

        # Build progress bar
        filled = int(self.width * self.current / self.total) if self.total > 0 else self.width
        bar = "=" * filled + ">" if filled < self.width else "=" * self.width
        bar = bar.ljust(self.width)

        # Format counts
        if self.total >= 1_000_000:
            count_str = f"{self.current / 1_000_000:.1f}M/{self.total / 1_000_000:.1f}M"
        elif self.total >= 1_000:
            count_str = f"{self.current / 1_000:.1f}K/{self.total / 1_000:.1f}K"
        else:
            count_str = f"{self.current}/{self.total}"

        # Build complete line
        parts = [
            f"{self.desc}:",
            f"[{bar}]",
            f"{percent:5.1f}%",
            f"({count_str})",
            f"| {self._format_time(elapsed)} elapsed",
        ]

        if eta_str:
            parts.append(f"| {eta_str}")

        if suffix:
            parts.append(f"| {suffix}")

        line = " ".join(parts)

        # Write to stderr with carriage return to update in place
        sys.stderr.write(f"\r{line}")
        sys.stderr.flush()

    def finish(self, suffix: str = "") -> None:
        """
        Complete progress bar and move to next line.

        Args:
            suffix: Optional suffix text to append
        """
        # Update state FIRST, before checking disable/finished
        self.finished = True
        self.current = self.total

        if self.disable:
            return  # Skip output but state is already updated

        self.update(self.total, suffix)
        sys.stderr.write("\n")
        sys.stderr.flush()

    def _format_time(self, seconds: float) -> str:
        """
        Format time duration in human-readable format.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time string (e.g., "5.2s", "2m 30s", "1h 15m")
        """
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure progress bar is finished."""
        if not self.finished:
            self.finish()
        return False


def create_progress_bar(
    total: int, desc: str = "Processing", disable: Optional[bool] = None
) -> ProgressBar:
    """
    Factory function to create a progress bar.

    Can be controlled by config or environment variables.

    Args:
        total: Total number of items
        desc: Description text
        disable: Force enable/disable (None = auto-detect)

    Returns:
        ProgressBar instance
    """
    if disable is None:
        # Could check config here: disable = not config.progress_bar_enabled
        disable = False

    return ProgressBar(total=total, desc=desc, disable=disable)
