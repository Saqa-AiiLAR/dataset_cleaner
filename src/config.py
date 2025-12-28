"""
Configuration management for SaqaParser project.
"""
from pathlib import Path
from dataclasses import dataclass


@dataclass
class Config:
    """Configuration settings for the SaqaParser application."""
    
    # Folder paths
    source_folder: Path = Path("source")
    archive_folder: Path = Path("archive")
    
    # File paths
    output_file: Path = Path("saqa.txt")
    cleaned_output_file: Path = Path("saqaCleaned.txt")
    log_file: Path = Path("logs")
    
    # Processing settings
    progress_interval_pages: int = 10  # Show progress every N pages
    progress_interval_words: int = 1000  # Show progress every N words
    debug_sample_size: int = 20  # Number of Russian words to show in debug output
    
    # Language detection settings
    primary_language: str = "ru"  # Primary language to detect (Russian)
    
    def __post_init__(self):
        """Ensure all paths are Path objects."""
        self.source_folder = Path(self.source_folder)
        self.archive_folder = Path(self.archive_folder)
        self.output_file = Path(self.output_file)
        self.cleaned_output_file = Path(self.cleaned_output_file)
        self.log_file = Path(self.log_file)
        
        # Create folders if they don't exist
        self.archive_folder.mkdir(exist_ok=True)
        self.source_folder.mkdir(exist_ok=True)


# Global configuration instance
config = Config()

