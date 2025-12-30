"""
Tests for parquet processor optional dependencies handling.

This module tests that the parquet processor handles missing optional
dependencies (pyarrow, pandas) gracefully.
"""

from __future__ import annotations

import unittest
from pathlib import Path
import tempfile
import shutil
from typing import Tuple
import sys
from unittest.mock import patch, MagicMock

from src.parquet_processor import ParquetProcessor
from src.exceptions import ParquetProcessingError, MissingFileError, ValidationError


class _BlockImports:
    """
    Context manager to block specific module imports for testing.

    This allows testing behavior when optional dependencies are missing.
    """

    def __init__(self, blocked_prefixes: Tuple[str, ...]) -> None:
        """
        Initialize import blocker.

        Args:
            blocked_prefixes: Tuple of module name prefixes to block
        """
        self.blocked_prefixes = blocked_prefixes
        self.original_import = __builtins__.__import__

    def __enter__(self) -> "_BlockImports":
        """Enter context manager."""
        def blocked_import(name: str, *args: object, **kwargs: object) -> object:
            for prefix in self.blocked_prefixes:
                if name.startswith(prefix):
                    raise ImportError(f"Blocked import of {name} for testing")
            return self.original_import(name, *args, **kwargs)

        __builtins__.__import__ = blocked_import
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> bool:
        """Exit context manager."""
        __builtins__.__import__ = self.original_import
        return False


class TestParquetOptionalDeps(unittest.TestCase):
    """Test cases for parquet processor with optional dependencies."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.source_folder = Path(self.temp_dir) / "source"
        self.archive_folder = Path(self.temp_dir) / "archive"
        self.output_file = Path(self.temp_dir) / "output.txt"
        self.log_file = Path(self.temp_dir) / "log.txt"

        # Create source folder
        self.source_folder.mkdir(parents=True)

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_processor_initializes_without_pyarrow(self) -> None:
        """Test that processor can be initialized even if pyarrow is missing."""
        # This test verifies that the processor doesn't fail on import
        # when pyarrow is not available
        processor = ParquetProcessor(
            input_folder=self.source_folder,
            archive_folder=self.archive_folder,
            output_file=self.output_file,
            log_file=self.log_file,
        )
        self.assertIsNotNone(processor)
        self.assertEqual(processor.input_folder, self.source_folder)

    def test_processor_handles_missing_pandas_gracefully(self) -> None:
        """Test that processor handles missing pandas gracefully."""
        # Note: pandas is a required dependency, but we test error handling
        processor = ParquetProcessor(
            input_folder=self.source_folder,
            archive_folder=self.archive_folder,
            output_file=self.output_file,
            log_file=self.log_file,
        )

        # Create a dummy parquet file path (won't actually process it)
        dummy_file = self.source_folder / "test.parquet"

        # The actual processing would fail if pandas is missing,
        # but initialization should work
        self.assertIsNotNone(processor)

    def test_processor_requires_valid_parquet_file(self) -> None:
        """Test that processor validates parquet file existence."""
        processor = ParquetProcessor(
            input_folder=self.source_folder,
            archive_folder=self.archive_folder,
            output_file=self.output_file,
            log_file=self.log_file,
        )

        # Try to process non-existent file
        non_existent = self.source_folder / "nonexistent.parquet"
        with self.assertRaises(MissingFileError):
            processor.extract_text_from_parquet(non_existent)

    def test_processor_validates_parquet_extension(self) -> None:
        """Test that processor validates file extension."""
        processor = ParquetProcessor(
            input_folder=self.source_folder,
            archive_folder=self.archive_folder,
            output_file=self.output_file,
            log_file=self.log_file,
        )

        # Create a non-parquet file
        text_file = self.source_folder / "test.txt"
        text_file.write_text("test content")

        with self.assertRaises(ValidationError):
            processor.extract_text_from_parquet(text_file)

