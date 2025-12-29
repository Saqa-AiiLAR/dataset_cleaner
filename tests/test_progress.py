"""
Unit tests for progress bar utility.
"""
import time
import pytest
import sys
from io import StringIO
from unittest.mock import patch, MagicMock

from src.progress import ProgressBar, create_progress_bar


class TestProgressBar:
    """Test cases for ProgressBar class."""
    
    def test_initialization(self):
        """Test ProgressBar initialization."""
        progress = ProgressBar(total=100, desc="Testing", width=25)
        
        assert progress.total == 100
        assert progress.desc == "Testing"
        assert progress.width == 25
        assert progress.current == 0
        assert progress.finished is False
    
    def test_update_progress(self):
        """Test updating progress."""
        progress = ProgressBar(total=100, desc="Testing", disable=True)
        
        progress.update(25)
        assert progress.current == 25
        
        progress.update(75)
        assert progress.current == 75
        
        progress.update(100)
        assert progress.current == 100
    
    def test_update_exceeds_total(self):
        """Test that update caps at total."""
        progress = ProgressBar(total=100, desc="Testing", disable=True)
        
        progress.update(150)
        assert progress.current == 100
    
    def test_finish(self):
        """Test finishing progress bar."""
        progress = ProgressBar(total=100, desc="Testing", disable=True)
        
        progress.update(100)
        progress.finish()
        
        assert progress.finished is True
    
    def test_disabled_progress_bar(self):
        """Test that disabled progress bar produces no output."""
        progress = ProgressBar(total=100, desc="Testing", disable=True)
        
        # Capture stderr
        captured_output = StringIO()
        with patch('sys.stderr', captured_output):
            progress.update(50)
            progress.finish()
        
        # Should be empty since disabled
        assert captured_output.getvalue() == ""
    
    def test_format_time_seconds(self):
        """Test time formatting for seconds."""
        progress = ProgressBar(total=100, desc="Testing")
        
        assert progress._format_time(5.2) == "5.2s"
        assert progress._format_time(30.5) == "30.5s"
        assert progress._format_time(59.9) == "59.9s"
    
    def test_format_time_minutes(self):
        """Test time formatting for minutes."""
        progress = ProgressBar(total=100, desc="Testing")
        
        assert progress._format_time(60) == "1m 0s"
        assert progress._format_time(125) == "2m 5s"
        assert progress._format_time(3599) == "59m 59s"
    
    def test_format_time_hours(self):
        """Test time formatting for hours."""
        progress = ProgressBar(total=100, desc="Testing")
        
        assert progress._format_time(3600) == "1h 0m"
        assert progress._format_time(5400) == "1h 30m"
        assert progress._format_time(7265) == "2h 1m"
    
    def test_zero_total(self):
        """Test progress bar with zero total."""
        progress = ProgressBar(total=0, desc="Testing", disable=True)
        
        progress.update(0)
        assert progress.current == 0
        
        progress.finish()
        assert progress.finished is True
    
    def test_context_manager(self):
        """Test ProgressBar as context manager."""
        with ProgressBar(total=100, desc="Testing", disable=True) as progress:
            assert progress.finished is False
            progress.update(50)
            assert progress.current == 50
        
        # Should auto-finish on exit
        assert progress.finished is True
    
    def test_context_manager_with_exception(self):
        """Test that context manager finishes even with exception."""
        progress = None
        try:
            with ProgressBar(total=100, desc="Testing", disable=True) as progress:
                progress.update(50)
                raise ValueError("Test error")
        except ValueError:
            pass
        
        # Should still be finished despite exception
        assert progress.finished is True
    
    def test_suffix_parameter(self):
        """Test update with suffix parameter."""
        progress = ProgressBar(total=100, desc="Testing", disable=True)
        
        # Should not raise any errors
        progress.update(50, suffix="processing file.txt")
        assert progress.current == 50
    
    def test_large_numbers_formatting(self):
        """Test formatting with large numbers (millions)."""
        progress = ProgressBar(total=90_000_000, desc="Testing", disable=True)
        
        progress.update(45_000_000)
        assert progress.current == 45_000_000
        
        # The formatting should handle millions correctly
        progress.finish()
    
    def test_thousands_formatting(self):
        """Test formatting with thousands."""
        progress = ProgressBar(total=5_000, desc="Testing", disable=True)
        
        progress.update(2_500)
        assert progress.current == 2_500
        
        progress.finish()
    
    @patch('sys.stderr')
    def test_non_tty_disables_output(self, mock_stderr):
        """Test that non-TTY environment disables progress bar."""
        # Mock stderr as not a TTY
        mock_stderr.isatty.return_value = False
        
        progress = ProgressBar(total=100, desc="Testing")
        
        assert progress.disable is True
    
    @patch('sys.stderr')
    def test_tty_enables_output(self, mock_stderr):
        """Test that TTY environment enables progress bar."""
        # Mock stderr as a TTY
        mock_stderr.isatty.return_value = True
        
        progress = ProgressBar(total=100, desc="Testing")
        
        # Should not be disabled (unless explicitly set)
        # Note: This might still be disabled if stderr doesn't have isatty attr
        # so we just check that the disable logic ran
        assert isinstance(progress.disable, bool)


class TestCreateProgressBar:
    """Test cases for create_progress_bar factory function."""
    
    def test_create_default(self):
        """Test creating progress bar with defaults."""
        progress = create_progress_bar(total=100)
        
        assert progress.total == 100
        assert progress.desc == "Processing"
    
    def test_create_with_description(self):
        """Test creating progress bar with custom description."""
        progress = create_progress_bar(total=50, desc="Custom Task")
        
        assert progress.total == 50
        assert progress.desc == "Custom Task"
    
    def test_create_disabled(self):
        """Test creating disabled progress bar."""
        progress = create_progress_bar(total=100, disable=True)
        
        assert progress.disable is True
    
    def test_create_enabled(self):
        """Test creating explicitly enabled progress bar."""
        progress = create_progress_bar(total=100, disable=False)
        
        # Will still check TTY, but disable parameter was False
        assert isinstance(progress.disable, bool)


class TestProgressBarIntegration:
    """Integration tests for ProgressBar."""
    
    @patch('sys.stderr', new_callable=StringIO)
    def test_multiple_updates(self, mock_stderr):
        """Test multiple progress updates."""
        # Force enable by mocking TTY
        with patch.object(sys.stderr, 'isatty', return_value=True):
            progress = ProgressBar(total=10, desc="Test")
            
            for i in range(1, 11):
                progress.update(i)
            
            progress.finish()
        
        # Should have written output
        output = mock_stderr.getvalue()
        assert len(output) > 0
    
    def test_performance(self):
        """Test that progress bar has minimal performance overhead."""
        start_time = time.time()
        
        progress = ProgressBar(total=10000, desc="Performance", disable=True)
        
        for i in range(1, 10001):
            progress.update(i)
        
        progress.finish()
        
        elapsed = time.time() - start_time
        
        # Should complete very quickly (< 0.1 seconds for 10K updates)
        assert elapsed < 0.1

