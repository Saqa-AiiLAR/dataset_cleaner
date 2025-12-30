"""
Tests for Parquet optional dependency behavior.

These tests ensure the project can be installed/run without pandas/pyarrow,
which are intentionally optional (used only for Parquet input support).
"""

import builtins
import sys
import tempfile
import unittest
from pathlib import Path

from src.parquet_processor import ParquetProcessor


class _BlockImports:
    """Context manager that blocks importing specific top-level modules."""

    def __init__(self, blocked_prefixes: tuple[str, ...]):
        self._blocked_prefixes = blocked_prefixes
        self._real_import = builtins.__import__

    def __enter__(self):
        def _fake_import(name, globals=None, locals=None, fromlist=(), level=0):  # noqa: A002
            if any(name == p or name.startswith(p + ".") for p in self._blocked_prefixes):
                raise ModuleNotFoundError(f"No module named '{name}'")
            return self._real_import(name, globals, locals, fromlist, level)

        builtins.__import__ = _fake_import  # type: ignore[assignment]
        return self

    def __exit__(self, exc_type, exc, tb):
        builtins.__import__ = self._real_import  # type: ignore[assignment]
        return False


class TestParquetOptionalDependencies(unittest.TestCase):
    """Verify Parquet processing degrades gracefully without optional deps."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.input_dir = self.root / "input"
        self.archive_dir = self.root / "archive"
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.output_file = self.root / "out.txt"
        self.log_file = self.root / "log.txt"

    def tearDown(self):
        self._tmp.cleanup()

    @staticmethod
    def _purge_optional_modules():
        # Ensure subsequent imports go through __import__ again.
        for name in list(sys.modules.keys()):
            if name == "pandas" or name.startswith("pandas.") or name == "pyarrow" or name.startswith("pyarrow."):
                sys.modules.pop(name, None)

    def test_no_parquet_files_does_not_require_optional_deps(self):
        """No *.parquet files => returns 0 without importing pandas/pyarrow."""
        processor = ParquetProcessor(
            input_folder=self.input_dir,
            archive_folder=self.archive_dir,
            output_file=self.output_file,
            log_file=self.log_file,
        )

        self._purge_optional_modules()
        with _BlockImports(("pandas", "pyarrow")):
            processed = processor.process_all_parquets()

        self.assertEqual(processed, 0)

    def test_parquet_files_present_but_deps_missing_is_graceful(self):
        """With *.parquet files present, missing deps should not crash the run."""
        (self.input_dir / "data.parquet").write_bytes(b"not a real parquet file")

        processor = ParquetProcessor(
            input_folder=self.input_dir,
            archive_folder=self.archive_dir,
            output_file=self.output_file,
            log_file=self.log_file,
        )

        self._purge_optional_modules()
        with _BlockImports(("pandas", "pyarrow")):
            processed = processor.process_all_parquets()

        # We skip Parquet processing when deps are missing.
        self.assertEqual(processed, 0)


if __name__ == "__main__":
    unittest.main()

