"""
SaqaParser - PDF text extraction and cleaning tool for Sakha language processing.
"""
from .config import config, Config
from .pdf_processor import PDFProcessor
from .text_cleaner import TextCleaner
from .base_processor import BaseProcessor
from .language_detector import WordClassifier, get_classifier
from .utils import setup_logging, validate_path, format_file_size, get_timestamp
from .exceptions import (
    SaqaParserError,
    ConfigurationError,
    FileNotFoundError,
    PDFProcessingError,
    TextCleaningError,
    ValidationError,
)

__version__ = "1.0.0"
__all__ = [
    "config",
    "Config",
    "PDFProcessor",
    "TextCleaner",
    "BaseProcessor",
    "WordClassifier",
    "get_classifier",
    "setup_logging",
    "validate_path",
    "format_file_size",
    "get_timestamp",
    "SaqaParserError",
    "ConfigurationError",
    "FileNotFoundError",
    "PDFProcessingError",
    "TextCleaningError",
    "ValidationError",
]

