"""
Parquet processing module for extracting text from Parquet files.
"""

from __future__ import annotations

import pandas as pd
import shutil
from pathlib import Path
from typing import Tuple, Optional
import logging

try:
    import pyarrow
    import pyarrow.lib
except ImportError:
    # pyarrow not available, will handle in code
    pyarrow = None

from .config import config
from .utils import format_file_size, get_timestamp
from .exceptions import ParquetProcessingError, ValidationError, MissingFileError
from .base_processor import BaseProcessor
from .progress import ProgressBar

logger = logging.getLogger("SaqaParser.parquet_processor")


class ParquetProcessor(BaseProcessor):
    """Handles Parquet text extraction and file management."""

    def __init__(
        self,
        input_folder: Optional[Path] = None,
        archive_folder: Optional[Path] = None,
        output_file: Optional[Path] = None,
        log_file: Optional[Path] = None,
    ):
        """
        Initialize Parquet processor.

        Args:
            input_folder: Folder containing Parquet files to process
            archive_folder: Folder to move processed Parquet files to
            output_file: File to append extracted text to
            log_file: File to write log entries to
        """
        super().__init__(log_file=log_file or config.log_file)
        self.input_folder = input_folder or config.input_folder
        self.archive_folder = archive_folder or config.archive_folder
        self.output_file = output_file or config.output_file

        # Validate and create paths using base class methods
        self.validate_directory(self.input_folder, must_exist=True)
        self.validate_directory(self.archive_folder, must_exist=False, create_if_missing=True)
        self.ensure_output_directory(self.output_file)

    def _is_value_null(self, value) -> bool:
        """
        Safely check if a value (scalar or array) is null/NaN.

        Handles scalars, lists, tuples, numpy arrays, and pandas Series.
        For arrays, returns True only if all elements are null.

        Args:
            value: Value to check (can be scalar, list, array, or Series)

        Returns:
            True if value is null/NaN (for scalars) or all elements are null (for arrays)
        """
        try:
            # Check if value is array-like (but not a string)
            if hasattr(value, "__iter__") and not isinstance(value, str):
                # For array-like values, check if all elements are null
                if isinstance(value, (list, tuple)):
                    # For lists/tuples, check each element
                    if len(value) == 0:
                        return True
                    return all(pd.isna(v) if not isinstance(v, str) else False for v in value)
                elif hasattr(value, "tolist"):
                    # For numpy arrays or pandas Series, convert to list first
                    try:
                        value_list = value.tolist()
                        if len(value_list) == 0:
                            return True
                        return all(pd.isna(v) if not isinstance(v, str) else False for v in value_list)
                    except (AttributeError, TypeError):
                        # Fallback: treat as scalar
                        return pd.isna(value)
                else:
                    # Other iterable types - try to iterate
                    try:
                        items = list(value)
                        if len(items) == 0:
                            return True
                        return all(pd.isna(v) if not isinstance(v, str) else False for v in items)
                    except (TypeError, ValueError):
                        # Can't iterate, treat as scalar
                        return pd.isna(value)
            else:
                # Scalar value - use standard pandas null check
                return pd.isna(value)
        except Exception:
            # If anything goes wrong, fallback to basic check
            try:
                return pd.isna(value)
            except Exception:
                # Last resort: check if None or empty
                return value is None or (hasattr(value, "__len__") and len(value) == 0)

    def _convert_value_to_text(self, value) -> str:
        """
        Convert any value type (scalar, list, array, Series) to a space-joined string.

        For lists/arrays: joins non-null elements with spaces.
        For scalars: converts to string and strips whitespace.
        Returns empty string for null/empty values.

        Args:
            value: Value to convert (can be scalar, list, array, or Series)

        Returns:
            Space-joined string representation of the value
        """
        try:
            # Handle array-like values (but not strings)
            if hasattr(value, "__iter__") and not isinstance(value, str):
                text_parts = []
                if isinstance(value, (list, tuple)):
                    # For lists/tuples, process each element
                    for v in value:
                        if v is not None and not pd.isna(v):
                            text_part = str(v).strip()
                            if text_part:
                                text_parts.append(text_part)
                elif hasattr(value, "tolist"):
                    # For numpy arrays or pandas Series, convert to list first
                    try:
                        value_list = value.tolist()
                        for v in value_list:
                            if v is not None and not pd.isna(v):
                                text_part = str(v).strip()
                                if text_part:
                                    text_parts.append(text_part)
                    except (AttributeError, TypeError):
                        # Fallback: convert entire value to string
                        text_parts = [str(value).strip()]
                else:
                    # Other iterable types
                    try:
                        for v in value:
                            if v is not None and not pd.isna(v):
                                text_part = str(v).strip()
                                if text_part:
                                    text_parts.append(text_part)
                    except (TypeError, ValueError):
                        # Can't iterate, treat as scalar
                        text_parts = [str(value).strip()]
                
                return " ".join(text_parts) if text_parts else ""
            else:
                # Scalar value - convert to string and strip whitespace
                return str(value).strip()
        except Exception as e:
            # Fallback: convert to string representation
            logger.debug(f"Error converting value to text: {e}")
            try:
                return str(value).strip()
            except Exception:
                return ""

    def extract_text_from_parquet(self, parquet_path: Path) -> Tuple[str, int]:
        """
        Extract text from a Parquet file.

        Reads all text/string columns and concatenates their values row by row.

        Args:
            parquet_path: Path to the Parquet file

        Returns:
            Tuple of (extracted_text, row_count)

        Raises:
            MissingFileError: If Parquet file doesn't exist
            ValidationError: If Parquet file is invalid or unreadable
            ParquetProcessingError: If Parquet processing fails
        """
        # Validate Parquet file
        if not parquet_path.exists():
            raise MissingFileError(f"Parquet file does not exist: {parquet_path}")

        if not parquet_path.is_file():
            raise ValidationError(f"Path is not a file: {parquet_path}")

        if not parquet_path.suffix.lower() == ".parquet":
            raise ValidationError(f"File is not a Parquet file: {parquet_path}")

        extracted_text = ""
        row_count = 0

        try:
            # Read parquet file using pyarrow engine
            df = pd.read_parquet(parquet_path, engine="pyarrow")
            row_count = len(df)

            if row_count == 0:
                logger.warning(f"Parquet file {parquet_path.name} contains no rows")
                return "", 0

            logger.info(f"Extracting text from {row_count} rows...")

            # Identify text/string columns
            # Include 'object' (string) and 'string' dtype columns
            text_columns = df.select_dtypes(include=["object", "string"]).columns.tolist()

            if not text_columns:
                logger.warning(
                    f"No text columns found in {parquet_path.name}. "
                    "File may contain only numeric or other non-text data."
                )
                return "", row_count

            logger.debug(f"Found {len(text_columns)} text column(s): {', '.join(text_columns)}")

            # Extract text from each row
            # For each row, concatenate values from all text columns
            row_texts = []
            for _idx, row in df.iterrows():
                # Get values from all text columns for this row
                row_values = []
                for col in text_columns:
                    value = row[col]
                    # Handle NaN/null values by skipping them
                    if not self._is_value_null(value):
                        # Convert to string representation (handles scalars, lists, arrays)
                        text_value = self._convert_value_to_text(value)
                        if text_value:  # Only add non-empty values
                            row_values.append(text_value)

                # Join values from different columns with space, then add to row_texts
                if row_values:
                    row_text = " ".join(row_values)
                    row_texts.append(row_text)

            # Join all rows with newlines
            extracted_text = "\n".join(row_texts)

            logger.info(f"Extracted text from {row_count} rows")

        except Exception as e:
            # Check if it's a pyarrow exception (parquet-specific errors)
            if pyarrow and isinstance(
                e, (pyarrow.lib.ArrowInvalid, pyarrow.lib.ArrowIOError, pyarrow.lib.ArrowException)
            ):
                error_msg = f"Invalid Parquet file format in {parquet_path.name}: {str(e)}"
                logger.error(error_msg)
                raise ParquetProcessingError(error_msg) from e
            # For other exceptions, check if it's a parquet-related error by message
            error_str = str(e).lower()
            if "parquet" in error_str or "arrow" in error_str:
                error_msg = f"Invalid Parquet file format in {parquet_path.name}: {str(e)}"
                logger.error(error_msg)
                raise ParquetProcessingError(error_msg) from e
            error_msg = f"Error extracting text from {parquet_path.name}: {str(e)}"
            logger.error(error_msg)
            raise ParquetProcessingError(error_msg) from e

        return extracted_text, row_count

    def process_parquet(self, parquet_path: Path) -> Tuple[int, int]:
        """
        Process a single Parquet file: extract text, save to output, move to archive.

        Args:
            parquet_path: Path to the Parquet file

        Returns:
            Tuple of (character_count, file_size_bytes)
        """
        file_size = parquet_path.stat().st_size

        try:
            # Extract text
            extracted_text, row_count = self.extract_text_from_parquet(parquet_path)
            char_count = len(extracted_text)

            # Append to output file
            if extracted_text:
                with open(self.output_file, "a", encoding="utf-8") as f:
                    f.write(extracted_text)
                logger.info(
                    f"Extracted and saved text from {parquet_path.name} "
                    f"({char_count} chars, {row_count} rows)"
                )
            else:
                if char_count == 0 and row_count > 0:
                    logger.warning(
                        f"No text extracted from {parquet_path.name} - "
                        "file may contain only non-text columns or empty text values"
                    )
                else:
                    logger.warning(
                        f"No text extracted from {parquet_path.name} - "
                        "file may be empty or unreadable"
                    )
                # Still continue processing even if no text extracted

            # Move to archive
            archive_path = self.archive_folder / parquet_path.name
            shutil.move(str(parquet_path), str(archive_path))
            logger.info(f"Moved {parquet_path.name} to archive folder")

            # Write log entry
            self._write_log_entry(parquet_path.name, char_count, file_size, row_count)

            return char_count, file_size

        except (ParquetProcessingError, MissingFileError, ValidationError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            error_msg = f"Unexpected error processing {parquet_path.name}: {str(e)}"
            logger.error(error_msg)
            self._write_log_entry(parquet_path.name, 0, file_size, 0, error=error_msg)
            raise ParquetProcessingError(error_msg) from e

    def _write_log_entry(
        self,
        filename: str,
        char_count: int,
        file_size: int,
        row_count: int,
        error: Optional[str] = None,
    ):
        """
        Write a log entry to the log file.

        Args:
            filename: Name of the processed file
            char_count: Number of characters extracted
            file_size: Size of the file in bytes
            row_count: Number of rows in the Parquet file
            error: Optional error message
        """
        timestamp = get_timestamp()
        if error:
            log_entry = f"ParquetProcessor - {filename} - {timestamp} - ERROR: {error}\n"
        else:
            log_entry = (
                f"ParquetProcessor - {filename} - {timestamp} - "
                f"{char_count} chars - {file_size} bytes - {row_count} rows\n"
            )

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)

    def process(self) -> int:
        """
        Process all Parquet files (implements BaseProcessor interface).

        Returns:
            Number of files processed successfully
        """
        return self.process_all_parquets()

    def process_all_parquets(self) -> int:
        """
        Process all Parquet files in the source folder.

        Returns:
            Number of files processed successfully
        """
        parquet_files = list(self.input_folder.glob("*.parquet"))

        if not parquet_files:
            logger.warning(f"No Parquet files found in input folder: {self.input_folder}")
            return 0

        total_parquets = len(parquet_files)
        logger.info(f"Found {total_parquets} Parquet file(s) to process.")

        processed_count = 0
        progress = ProgressBar(total=total_parquets, desc="Processing Parquet")

        for parquet_index, parquet_path in enumerate(parquet_files, 1):
            try:
                char_count, file_size = self.process_parquet(parquet_path)
                processed_count += 1
                progress.update(parquet_index, suffix=parquet_path.name)
            except Exception as e:
                logger.error(f"Failed to process {parquet_path.name}: {str(e)}")
                progress.update(parquet_index, suffix=f"Error: {parquet_path.name}")
                continue

        progress.finish()
        logger.info(f"Processing complete. Processed {processed_count}/{total_parquets} file(s).")
        return processed_count
