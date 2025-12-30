"""
Custom exceptions for SaqaParser project.
"""


class SaqaParserError(Exception):
    """Base exception for SaqaParser."""

    pass


class ConfigurationError(SaqaParserError):
    """Raised when there's a configuration error."""

    pass


class MissingFileError(SaqaParserError):
    """Raised when a required file or directory is not found.

    This is a custom exception to distinguish from Python's built-in
    FileNotFoundError while maintaining clear semantics.
    """

    pass


class PDFProcessingError(SaqaParserError):
    """Raised when PDF processing fails."""

    pass


class ParquetProcessingError(SaqaParserError):
    """Raised when Parquet processing fails."""

    pass


class TextCleaningError(SaqaParserError):
    """Raised when text cleaning fails."""

    pass


class ValidationError(SaqaParserError):
    """Raised when validation fails."""

    pass
