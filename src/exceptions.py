"""
Custom exceptions for SaqaParser project.
"""


class SaqaParserError(Exception):
    """Base exception for SaqaParser."""
    pass


class ConfigurationError(SaqaParserError):
    """Raised when there's a configuration error."""
    pass


class FileNotFoundError(SaqaParserError):
    """Raised when a required file is not found.
    
    Note: This is a custom exception. For standard FileNotFoundError,
    use the built-in exception from Python.
    """
    pass


class PDFProcessingError(SaqaParserError):
    """Raised when PDF processing fails."""
    pass


class TextCleaningError(SaqaParserError):
    """Raised when text cleaning fails."""
    pass


class ValidationError(SaqaParserError):
    """Raised when validation fails."""
    pass

