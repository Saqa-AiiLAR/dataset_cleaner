"""
Tests for utils module.
"""
import unittest
from pathlib import Path
import tempfile
import os

from src.utils import validate_path, format_file_size, get_timestamp


class TestUtils(unittest.TestCase):
    """Test cases for utility functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_validate_path_existing_file(self):
        """Test validate_path with existing file."""
        test_file = Path(self.temp_dir) / "test.txt"
        test_file.write_text("test")
        
        result = validate_path(test_file, must_exist=True, must_be_file=True)
        self.assertTrue(result)
    
    def test_validate_path_nonexistent_file(self):
        """Test validate_path with nonexistent file."""
        test_file = Path(self.temp_dir) / "nonexistent.txt"
        
        result = validate_path(test_file, must_exist=True, must_be_file=True)
        self.assertFalse(result)
    
    def test_validate_path_existing_directory(self):
        """Test validate_path with existing directory."""
        result = validate_path(Path(self.temp_dir), must_exist=True, must_be_file=False)
        self.assertTrue(result)
    
    def test_format_file_size_bytes(self):
        """Test format_file_size with bytes."""
        result = format_file_size(500)
        self.assertEqual(result, "500.0 B")
    
    def test_format_file_size_kb(self):
        """Test format_file_size with kilobytes."""
        result = format_file_size(2048)
        self.assertIn("KB", result)
    
    def test_format_file_size_mb(self):
        """Test format_file_size with megabytes."""
        result = format_file_size(2097152)
        self.assertIn("MB", result)
    
    def test_get_timestamp_format(self):
        """Test get_timestamp returns correct format."""
        timestamp = get_timestamp()
        # Should be in format YYYY-MM-DD HH:MM:SS
        self.assertRegex(timestamp, r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")


if __name__ == "__main__":
    unittest.main()

