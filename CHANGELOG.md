# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-XX

### Added
- Initial release of SaqaParser
- PDF text extraction from PDF files
- Russian word removal with multi-layer classification system
- Text cleaning (removal of special characters and numbers)
- CLI interface with command-line options
- Comprehensive logging system
- Modular architecture with base processor class
- Language detection with lazy loading
- Linguistic constants module
- Word classifier with Sakha/Russian detection
- Custom exception handling
- Input validation
- Progress reporting for long operations

### Features
- **PDF Processing**: Extract text from PDF files using pdfplumber
- **Language Detection**: Multi-layer word classification system:
  - Layer 1: Sakha anchor characters and diphthongs (highest priority)
  - Layer 2: Russian marker characters
  - Layer 3: Morphological pattern matching
  - Layer 4: Language detection and morphological analysis (fallback)
- **CLI Interface**: Command-line options for both PDF extraction and text cleaning
- **Configuration**: Flexible configuration system with customizable settings
- **Logging**: File and console logging with different verbosity levels

### Technical Details
- Python 3.8+ support
- Modular architecture with separation of concerns
- Type hints throughout the codebase
- Comprehensive error handling
- Lazy loading of heavy dependencies (pymorphy2, natasha)

[1.0.0]: https://github.com/yourusername/saqaparser/releases/tag/v1.0.0

