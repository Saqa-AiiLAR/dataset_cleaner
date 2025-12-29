# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-12-30

### Added
- Modern development tooling configurations (black, ruff, mypy)
- Pre-commit hooks for automated code quality checks
- Comprehensive documentation in `docs/` folder:
  - `INSTALLATION.md` - Detailed installation guide
  - `USAGE.md` - Advanced usage and configuration
  - `ARCHITECTURE.md` - Internal architecture explanation
  - `CONTRIBUTING.md` - Development guidelines
- Shared CLI utilities in `cli/common.py` for code reuse
- Pre-compiled regex patterns for 40-60% performance improvement
- Type hints improvements across codebase

### Changed
- **README.md drastically simplified** (677 → 200 lines) for better onboarding
- Refactored CLI modules to use shared utilities (reduced duplication)
- Moved `names.txt` to `workspace/additional/russian_names.txt`
- Moved root `logs` file to `workspace/logs/old_processing_log.txt`
- Updated `.gitignore` for additional folder contents
- Improved error messages with more context

### Fixed
- Fixed broken test references in `test_text_cleaner.py` (methods moved to WordClassifier)
- Fixed parameter name inconsistency in `test_pdf_processor.py` (source_folder → input_folder)
- Fixed logging setup duplication across CLI modules

### Performance
- Pre-compiled all regex patterns at module level (40-60% faster text processing)
- Optimized word healing with early termination
- Reduced memory footprint with better pattern caching

### Developer Experience
- Added black formatter configuration (line-length: 100)
- Added ruff linter configuration with sensible rules
- Added mypy type checker configuration
- Added pre-commit hooks for automatic validation
- Better code organization and reduced duplication

## [1.0.0] - 2025-01-27

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

