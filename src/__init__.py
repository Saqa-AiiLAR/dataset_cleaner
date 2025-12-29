"""
SaqaParser - PDF text extraction and cleaning tool for Sakha language processing.
"""
from .config import config, Config
from .pdf_processor import PDFProcessor
from .text_cleaner import TextCleaner
from .base_processor import BaseProcessor
from .language_detector import WordClassifier, get_classifier
from .word_healer import WordHealer
from .utils import validate_path, format_file_size, get_timestamp
from .exceptions import (
    SaqaParserError,
    ConfigurationError,
    MissingFileError,
    PDFProcessingError,
    TextCleaningError,
    ValidationError,
)
from .constants import SAKHA_NORMALIZATION_MAP

__version__ = "1.0.0"
__all__ = [
    "config",
    "Config",
    "PDFProcessor",
    "TextCleaner",
    "BaseProcessor",
    "WordClassifier",
    "get_classifier",
    "WordHealer",
    "SAKHA_NORMALIZATION_MAP",
    "validate_path",
    "format_file_size",
    "get_timestamp",
    "SaqaParserError",
    "ConfigurationError",
    "MissingFileError",
    "PDFProcessingError",
    "TextCleaningError",
    "ValidationError",
]

