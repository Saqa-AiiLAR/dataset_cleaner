# SaqaParser

A Python tool for processing PDF files, extracting text, and cleaning Sakha language text by removing Russian words, numbers, and special characters.

## Overview

SaqaParser is designed to process PDF documents containing Sakha (Yakut) language text. It extracts text from PDF files, removes Russian words and special characters, and produces cleaned text files suitable for language processing and analysis.

## Features

- **PDF Text Extraction**: Extract text from PDF files using `pdfplumber`
- **Russian Word Removal**: Intelligent multi-layer detection and removal of Russian words using:
  - Sakha-specific character detection (ҕ, ҥ, ө, һ, ү)
  - Sakha diphthong detection (уо, иэ, ыа, үө)
  - Russian marker character detection (щ, ц, ъ, ф, в)
  - Morphological pattern matching
  - Language detection and morphological analysis
- **Text Cleaning**: Remove special characters, numbers, and punctuation while preserving Sakha text
- **CLI Interface**: Command-line interface with flexible options for both PDF extraction and text cleaning
- **Modular Architecture**: Well-organized codebase with separate modules for different functionalities
- **Base Processor Architecture**: Common base class for consistent behavior across processors
- **Lazy Loading**: Heavy dependencies (pymorphy2, natasha) are loaded only when needed
- **Comprehensive Logging**: Detailed logging with both file and console output, with verbosity control
- **Error Handling**: Robust error handling with custom exceptions
- **Input Validation**: Validates files and paths before processing

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Steps

1. Clone the repository:
```bash
git clone <repository-url>
cd SaqaParser
```

2. Install dependencies:

**Option A: Using requirements.txt**
```bash
pip install -r requirements.txt
```

**Option B: Using pyproject.toml (recommended)**
```bash
pip install -e .
```

**Option C: Install with development dependencies**
```bash
pip install -e ".[dev]"
```

### Dependencies

- `pdfplumber>=0.10.0,<1.0.0` - PDF text extraction
- `langdetect>=1.0.9,<2.0.0` - Language detection
- `pymorphy2>=0.9.1,<1.0.0` - Russian morphological analysis
- `natasha>=1.5.0,<2.0.0` - Russian NLP toolkit
- `regex>=2023.0.0,<2026.0.0` - Advanced regular expressions

## Usage

### Basic Workflow

The tool operates in two main steps:

1. **Extract text from PDFs** → `saqa.txt`
2. **Clean the extracted text** → `saqaCleaned.txt`

### Step 1: Extract Text from PDFs

Place PDF files in the `source/` folder, then run:

**Basic usage:**
```bash
python pdf_insert.py
```

**With CLI options:**
```bash
# Custom source and output paths
python pdf_insert.py --source ./my_pdfs --output ./output.txt

# Verbose mode for detailed logging
python pdf_insert.py --verbose

# Quiet mode (only file logging)
python pdf_insert.py --quiet

# Full example with all options
python pdf_insert.py --source ./pdfs --archive ./processed --output ./text.txt --log ./app.log --verbose
```

**Using entry point (if installed):**
```bash
saqa-pdf-extract --source ./my_pdfs --output ./output.txt
```

This will:
- Extract text from all PDF files in `source/` (or specified folder)
- Append extracted text to `saqa.txt` (or specified output file)
- Move processed PDFs to `archive/` (or specified archive folder)
- Log processing details to `logs` (or specified log file)

### Step 2: Clean the Extracted Text

After extracting text, clean it by running:

**Basic usage:**
```bash
python cleaner.py
```

**With CLI options:**
```bash
# Custom input and output paths
python cleaner.py --input ./input.txt --output ./cleaned.txt

# Verbose mode
python cleaner.py --verbose

# Quiet mode
python cleaner.py --quiet

# Full example
python cleaner.py --input saqa.txt --output cleaned.txt --log app.log --verbose
```

**Using entry point (if installed):**
```bash
saqa-clean --input saqa.txt --output cleaned.txt
```

This will:
- Read text from `saqa.txt` (or specified input file)
- Remove special characters and numbers
- Remove Russian words using multi-layer classification
- Save cleaned text to `saqaCleaned.txt` (or specified output file)
- Log processing details to `logs` (or specified log file)

### CLI Options

Both `pdf_insert.py` and `cleaner.py` support the following options:

#### pdf_insert.py Options

- `--source PATH` - Source folder containing PDF files (default: `source/`)
- `--archive PATH` - Archive folder for processed PDFs (default: `archive/`)
- `--output PATH` - Output file for extracted text (default: `saqa.txt`)
- `--log PATH` - Log file path (default: `logs`)
- `-v, --verbose` - Enable verbose logging (DEBUG level)
- `-q, --quiet` - Suppress console output (only log to file)
- `-h, --help` - Show help message

#### cleaner.py Options

- `--input PATH` - Input text file (default: `saqa.txt`)
- `--output PATH` - Output cleaned text file (default: `saqaCleaned.txt`)
- `--log PATH` - Log file path (default: `logs`)
- `-v, --verbose` - Enable verbose logging (DEBUG level)
- `-q, --quiet` - Suppress console output (only log to file)
- `-h, --help` - Show help message

## Project Structure

```
SaqaParser/
├── src/                      # Source code modules
│   ├── __init__.py          # Package initialization
│   ├── config.py            # Configuration management
│   ├── constants.py         # Linguistic constants (Sakha/Russian patterns)
│   ├── base_processor.py    # Base processor class
│   ├── language_detector.py # Word classification logic
│   ├── pdf_processor.py     # PDF extraction logic
│   ├── text_cleaner.py       # Text cleaning logic
│   ├── utils.py             # Utility functions
│   └── exceptions.py        # Custom exceptions
├── tests/                   # Test files
│   ├── __init__.py
│   ├── test_pdf_processor.py
│   ├── test_text_cleaner.py
│   └── test_utils.py
├── source/                  # Input folder for PDF files
│   └── .gitkeep            # Preserves folder structure
├── archive/                 # Output folder for processed PDFs
│   └── .gitkeep            # Preserves folder structure
├── pdf_insert.py            # Entry point for PDF extraction
├── cleaner.py               # Entry point for text cleaning
├── requirements.txt         # Python dependencies
├── pyproject.toml          # Modern Python project configuration
├── CHANGELOG.md            # Version history
├── README.md               # This file
└── .gitignore              # Git ignore rules
```

## Configuration

Configuration is managed in `src/config.py`. You can modify:

- **Folder paths**: `source_folder`, `archive_folder`
- **File paths**: `output_file`, `cleaned_output_file`, `log_file`
- **Processing settings**: 
  - `progress_interval_pages`: Show progress every N pages (default: 10)
  - `progress_interval_words`: Show progress every N words (default: 1000)
  - `debug_sample_size`: Number of Russian words to show in debug (default: 20)
- **Language detection settings**: 
  - `primary_language`: Primary language to detect (default: "ru" for Russian)
  - `use_v_as_russian_marker`: Include 'в' as Russian marker (default: True)
  - `pattern_matching_sensitivity`: Threshold for morphological pattern matching (default: 0.8)

### Example: Custom Configuration

```python
from pathlib import Path
from src.config import Config
from src.pdf_processor import PDFProcessor

# Create custom configuration
custom_config = Config(
    source_folder=Path("my_pdfs"),
    archive_folder=Path("my_archive"),
    progress_interval_pages=5,
    use_v_as_russian_marker=False,  # Disable 'в' as Russian marker
    pattern_matching_sensitivity=0.9  # Higher sensitivity
)

# Use custom configuration
processor = PDFProcessor(
    source_folder=custom_config.source_folder,
    archive_folder=custom_config.archive_folder
)
```

### Programmatic Usage

You can also use the modules programmatically:

```python
from src.pdf_processor import PDFProcessor
from src.text_cleaner import TextCleaner
from src.language_detector import WordClassifier

# PDF extraction
processor = PDFProcessor(
    source_folder=Path("pdfs"),
    archive_folder=Path("archived"),
    output_file=Path("extracted.txt")
)
count = processor.process_all_pdfs()

# Text cleaning
cleaner = TextCleaner(
    input_file=Path("extracted.txt"),
    output_file=Path("cleaned.txt")
)
char_count = cleaner.clean_text()

# Word classification
classifier = WordClassifier()
is_russian = classifier.is_russian_word("привет")  # True
is_sakha = classifier.is_russian_word("баҕар")     # False
```

## Multi-Layer Word Classification

The tool uses a sophisticated multi-layer classification system to distinguish Russian from Sakha words:

### Layer 1: Sakha Anchor Rules (Highest Priority - KEEP)
- **Sakha-specific characters**: `ҕ, ҥ, ө, һ, ү`
- **Sakha diphthongs**: `уо, иэ, ыа, үө`
- If a word contains any of these, it is **always kept** (not deleted)

### Layer 2: Russian Marker Rules (High Priority - DELETE)
- **Russian-specific characters**: `щ, ц, ъ, ф, в` (configurable)
- If a word contains any of these, it is **deleted** (unless overridden by Layer 1)

### Layer 3: Morphological Pattern Rules (Medium Priority)
- **Russian patterns** (DELETE):
  - Verbs: `-ться, -тся, -ешь, -ишь`
  - Adjectives: `-ий, -ый, -ая, -ое, -ые`
  - Nouns: `-ость, -ение, -ание`
- **Sakha patterns** (KEEP):
  - Plural: `-лар, -лер, -лор, -лөр` (and variations)
  - Possessive: `-та, -тэ, -тын, -быт`

### Layer 4: Fallback Logic
- Language detection (langdetect)
- Morphological analysis (pymorphy2)
- Name extraction (natasha)

## Output Files

- **`saqa.txt`**: Raw extracted text from all processed PDFs
- **`saqaCleaned.txt`**: Cleaned text with Russian words and special characters removed
- **`logs`**: Processing log with timestamps and statistics

## Logging

The tool uses Python's `logging` module with:
- **File logging**: Appends to `logs` file (or specified log file)
- **Console logging**: Displays progress and errors (can be suppressed with `--quiet`)
- **Log levels**: DEBUG (with `--verbose`), INFO (default), WARNING, ERROR

Log entries include:
- Timestamp
- Script name
- File name
- Character count
- File size
- Page count (for PDFs)
- Error messages (if any)

## Error Handling

The tool includes custom exceptions:
- `SaqaParserError`: Base exception
- `FileNotFoundError`: File or folder not found
- `ValidationError`: Invalid input or configuration
- `PDFProcessingError`: PDF processing failures
- `TextCleaningError`: Text cleaning failures
- `ConfigurationError`: Configuration errors

## Testing

Run tests using:

```bash
# Using pytest (if installed)
python -m pytest tests/

# Using unittest
python -m unittest discover tests

# With coverage (if pytest-cov installed)
python -m pytest tests/ --cov=src
```

## Development

### Code Structure

- **Modular design**: Separate modules for different functionalities
- **Base processor**: Common base class for consistent behavior
- **Lazy loading**: Heavy dependencies loaded only when needed
- **Type hints**: Functions include comprehensive type annotations
- **Documentation**: Docstrings for all classes and functions
- **Error handling**: Comprehensive exception handling

### Adding New Features

1. Add new modules to `src/`
2. Update `src/__init__.py` to export new components
3. Add tests in `tests/`
4. Update `CHANGELOG.md` with changes
5. Update this README

### Project Setup

The project uses modern Python packaging with `pyproject.toml`:
- Build system: setuptools
- Entry points defined for CLI commands
- Version management in `src/__init__.py`

## Troubleshooting

### No PDF files found
- Ensure PDF files are in the `source/` folder (or use `--source` option)
- Check file extensions are `.pdf` (case-sensitive)

### Language detection issues
- Some words may be misclassified
- The tool uses multiple methods (anchors, markers, patterns, language detection, morphology) for accuracy
- Adjust `use_v_as_russian_marker` if needed
- Modify `pattern_matching_sensitivity` for different sensitivity levels

### Memory issues with large PDFs
- Process PDFs in smaller batches
- Consider splitting large PDFs before processing
- Use `--quiet` mode to reduce memory usage from logging

### Import errors
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version is 3.8 or higher: `python --version`

## License

See LICENSE file for details.

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Update `CHANGELOG.md`
5. Submit a pull request

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and changes.

## Notes

- PDF files are moved (not copied) to `archive/` after processing
- The `source/` and `archive/` folders are preserved in Git but their contents are ignored
- Large files (PDFs, text files) are excluded from Git tracking
- The tool uses lazy loading for heavy dependencies (pymorphy2, natasha) to improve startup performance
