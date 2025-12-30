"""
Tests for pdf_processor module.
"""

import unittest
from pathlib import Path
import tempfile
import shutil

from src.pdf_processor import PDFProcessor
from src.exceptions import MissingFileError, ValidationError


class TestPDFProcessor(unittest.TestCase):
    """Test cases for PDFProcessor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.source_folder = Path(self.temp_dir) / "source"
        self.archive_folder = Path(self.temp_dir) / "archive"
        self.output_file = Path(self.temp_dir) / "output.txt"
        self.log_file = Path(self.temp_dir) / "log.txt"

        # Create source folder
        self.source_folder.mkdir(parents=True)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_processor_initialization_with_valid_folders(self):
        """Test PDFProcessor initialization with valid folders."""
        processor = PDFProcessor(
            input_folder=self.source_folder,
            archive_folder=self.archive_folder,
            output_file=self.output_file,
            log_file=self.log_file,
        )
        self.assertEqual(processor.input_folder, self.source_folder)
        self.assertEqual(processor.archive_folder, self.archive_folder)
        # Archive folder should be created
        self.assertTrue(self.archive_folder.exists())

    def test_processor_initialization_with_missing_source(self):
        """Test PDFProcessor initialization with missing source folder."""
        with self.assertRaises(MissingFileError):
            PDFProcessor(
                input_folder=Path(self.temp_dir) / "nonexistent",
                archive_folder=self.archive_folder,
                output_file=self.output_file,
                log_file=self.log_file,
            )

    def test_processor_creates_archive_folder(self):
        """Test that processor creates archive folder if it doesn't exist."""
        archive_path = Path(self.temp_dir) / "new_archive"
        PDFProcessor(
            input_folder=self.source_folder,
            archive_folder=archive_path,
            output_file=self.output_file,
            log_file=self.log_file,
        )
        self.assertTrue(archive_path.exists())
        self.assertTrue(archive_path.is_dir())

    def test_extract_text_from_pdf_with_nonexistent_file(self):
        """Test extract_text_from_pdf with nonexistent file."""
        processor = PDFProcessor(
            input_folder=self.source_folder,
            archive_folder=self.archive_folder,
            output_file=self.output_file,
            log_file=self.log_file,
        )

        with self.assertRaises(MissingFileError):
            processor.extract_text_from_pdf(Path(self.temp_dir) / "nonexistent.pdf")

    def test_extract_text_from_pdf_with_non_pdf_file(self):
        """Test extract_text_from_pdf with non-PDF file."""
        processor = PDFProcessor(
            input_folder=self.source_folder,
            archive_folder=self.archive_folder,
            output_file=self.output_file,
            log_file=self.log_file,
        )

        # Create a text file
        text_file = Path(self.temp_dir) / "test.txt"
        text_file.write_text("test content")

        with self.assertRaises(ValidationError):
            processor.extract_text_from_pdf(text_file)

    def test_process_all_pdfs_with_empty_folder(self):
        """Test process_all_pdfs with empty source folder."""
        processor = PDFProcessor(
            input_folder=self.source_folder,
            archive_folder=self.archive_folder,
            output_file=self.output_file,
            log_file=self.log_file,
        )

        result = processor.process_all_pdfs()
        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
