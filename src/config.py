"""
Configuration management for SaqaParser project.
"""
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from .exceptions import ConfigurationError, ValidationError


@dataclass
class Config:
    """Configuration settings for the SaqaParser application."""
    
    # Folder paths
    source_folder: Path = field(default_factory=lambda: Path("source"))
    archive_folder: Path = field(default_factory=lambda: Path("archive"))
    
    # File paths
    output_file: Path = field(default_factory=lambda: Path("saqa.txt"))
    cleaned_output_file: Path = field(default_factory=lambda: Path("saqaCleaned.txt"))
    log_file: Path = field(default_factory=lambda: Path("logs"))
    
    # Processing settings
    progress_interval_pages: int = 10  # Show progress every N pages
    progress_interval_words: int = 1000  # Show progress every N words
    debug_sample_size: int = 20  # Number of Russian words to show in debug output
    
    # Language detection settings
    primary_language: str = "ru"  # Primary language to detect (Russian)
    
    # Russian word removal settings
    use_v_as_russian_marker: bool = True  # Include 'в' as Russian marker (can be disabled)
    pattern_matching_sensitivity: float = 0.8  # Threshold for morphological pattern matching (0.0-1.0)
    
    # Word healer settings
    word_healer_enabled: bool = True  # Enable word healing for OCR repair
    word_healer_passes: int = 5  # Maximum number of repair iterations
    word_healer_exceptions_file: Optional[Path] = None  # Optional path to exceptions file
    
    # PDF extraction settings
    pdf_x_tolerance: int = 3  # Default horizontal tolerance for text extraction
    pdf_y_tolerance: int = 3  # Default vertical tolerance for text extraction
    pdf_adaptive_tolerance: bool = True  # Enable adaptive tolerance strategy
    pdf_badness_threshold: float = 0.3  # Threshold for retry with higher tolerance (0.0-1.0)
    pdf_layout_mode: bool = True  # Use layout-aware extraction
    
    def __post_init__(self) -> None:
        """Ensure all paths are Path objects."""
        self.source_folder = Path(self.source_folder)
        self.archive_folder = Path(self.archive_folder)
        self.output_file = Path(self.output_file)
        self.cleaned_output_file = Path(self.cleaned_output_file)
        self.log_file = Path(self.log_file)
        
        # Convert exceptions file to Path if provided
        if self.word_healer_exceptions_file is not None:
            self.word_healer_exceptions_file = Path(self.word_healer_exceptions_file)
    
    def setup_directories(self) -> None:
        """
        Create required directories if they don't exist.
        
        This method should be called explicitly after config initialization
        to avoid side effects during configuration.
        
        Raises:
            ConfigurationError: If directories cannot be created
        """
        try:
            self.archive_folder.mkdir(parents=True, exist_ok=True)
            self.source_folder.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise ConfigurationError(f"Cannot create required directories: {e}") from e
    
    def validate(self) -> None:
        """
        Validate configuration values.
        
        Raises:
            ValidationError: If configuration values are invalid
        """
        # Validate progress intervals
        if self.progress_interval_pages < 1:
            raise ValidationError(f"progress_interval_pages must be >= 1, got {self.progress_interval_pages}")
        
        if self.progress_interval_words < 1:
            raise ValidationError(f"progress_interval_words must be >= 1, got {self.progress_interval_words}")
        
        # Validate sensitivity
        if not 0.0 <= self.pattern_matching_sensitivity <= 1.0:
            raise ValidationError(
                f"pattern_matching_sensitivity must be between 0.0 and 1.0, got {self.pattern_matching_sensitivity}"
            )
        
        # Validate word healer passes
        if self.word_healer_passes < 1:
            raise ValidationError(f"word_healer_passes must be >= 1, got {self.word_healer_passes}")
        
        # Validate PDF tolerance values
        if self.pdf_x_tolerance < 0:
            raise ValidationError(f"pdf_x_tolerance must be >= 0, got {self.pdf_x_tolerance}")
        
        if self.pdf_y_tolerance < 0:
            raise ValidationError(f"pdf_y_tolerance must be >= 0, got {self.pdf_y_tolerance}")
        
        # Validate badness threshold
        if not 0.0 <= self.pdf_badness_threshold <= 1.0:
            raise ValidationError(
                f"pdf_badness_threshold must be between 0.0 and 1.0, got {self.pdf_badness_threshold}"
            )
        
        # Validate exceptions file if provided
        if self.word_healer_exceptions_file is not None:
            if not self.word_healer_exceptions_file.is_file() and self.word_healer_exceptions_file.exists():
                raise ValidationError(
                    f"word_healer_exceptions_file must be a file or not exist, got {self.word_healer_exceptions_file}"
                )


# Global configuration instance
config = Config()
# Setup directories automatically for backward compatibility
# This can be disabled if needed by calling config.setup_directories() explicitly elsewhere
config.setup_directories()

