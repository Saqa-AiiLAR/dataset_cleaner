"""
Base processor class for common functionality.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
import logging

from .utils import validate_path
from .exceptions import ValidationError, MissingFileError

logger = logging.getLogger("SaqaParser.base_processor")


class BaseProcessor(ABC):
    """
    Abstract base class for processors.
    
    Provides common functionality for path validation, directory creation,
    and logging setup.
    """
    
    def __init__(self, log_file: Optional[Path] = None) -> None:
        """
        Initialize base processor.
        
        Args:
            log_file: Path to log file
        """
        self.log_file = log_file
        self._validate_log_file_path()
    
    def _validate_log_file_path(self) -> None:
        """
        Validate and create log file directory if needed.
        
        Raises:
            ValidationError: If log file directory cannot be created
        """
        if self.log_file:
            if self.log_file.parent and not self.log_file.parent.exists():
                try:
                    self.log_file.parent.mkdir(parents=True, exist_ok=True)
                except OSError as e:
                    raise ValidationError(
                        f"Cannot create log directory {self.log_file.parent}: {e}"
                    )
    
    def validate_directory(
        self, 
        directory: Path, 
        must_exist: bool = True, 
        create_if_missing: bool = False
    ) -> None:
        """
        Validate a directory path.
        
        Args:
            directory: Directory path to validate
            must_exist: Whether the directory must exist
            create_if_missing: Whether to create directory if it doesn't exist
        
        Raises:
            MissingFileError: If directory doesn't exist and must_exist is True
            ValidationError: If directory is not a directory or cannot be created
        """
        if must_exist and not validate_path(directory, must_exist=True, must_be_file=False):
            raise MissingFileError(f"Directory does not exist: {directory}")
        
        if must_exist and not directory.is_dir():
            raise ValidationError(f"Path is not a directory: {directory}")
        
        if create_if_missing and not directory.exists():
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise ValidationError(f"Cannot create directory {directory}: {e}")
    
    def validate_file(
        self, 
        file_path: Path, 
        must_exist: bool = True,
        must_be_file: bool = True
    ) -> None:
        """
        Validate a file path.
        
        Args:
            file_path: File path to validate
            must_exist: Whether the file must exist
            must_be_file: Whether the path must be a file
        
        Raises:
            MissingFileError: If file doesn't exist and must_exist is True
            ValidationError: If path is not a file or is empty
        """
        if must_exist and not validate_path(file_path, must_exist=True, must_be_file=must_be_file):
            raise MissingFileError(f"File does not exist: {file_path}")
        
        if must_exist and must_be_file:
            if not file_path.is_file():
                raise ValidationError(f"Path is not a file: {file_path}")
            
            # Check if file is readable and not empty
            if file_path.stat().st_size == 0:
                raise ValidationError(f"File is empty: {file_path}")
    
    def ensure_output_directory(self, output_path: Path) -> None:
        """
        Ensure output file's parent directory exists.
        
        Args:
            output_path: Path to output file
        
        Raises:
            ValidationError: If directory cannot be created
        """
        if output_path.parent and not output_path.parent.exists():
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise ValidationError(
                    f"Cannot create output directory {output_path.parent}: {e}"
                )
    
    @abstractmethod
    def process(self) -> int:
        """
        Process the input and return a result count.
        
        Returns:
            Number of items processed
        
        Raises:
            Exception: If processing fails
        """
        pass

