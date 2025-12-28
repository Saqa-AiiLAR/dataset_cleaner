# SaqaParser

A Python tool for processing PDF files, extracting text, and cleaning Sakha language text by removing Russian words, numbers, and special characters.

## Overview

SaqaParser is designed to process PDF documents containing Sakha (Yakut) language text. It extracts text from PDF files, removes Russian words and special characters, and produces cleaned text files suitable for language processing and analysis.

## Features

- **PDF Text Extraction**: Extract text from PDF files using `pdfplumber`
- **Russian Word Removal**: Intelligent detection and removal of Russian words using language detection and morphological analysis
- **Text Cleaning**: Remove special characters, numbers, and punctuation while preserving Sakha text
- **Modular Architecture**: Well-organized codebase with separate modules for PDF processing and text cleaning
- **Comprehensive Logging**: Detailed logging with both file and console output
- **Error Handling**: Robust error handling with custom exceptions
- **Input Validation**: Validates files and paths before processing

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Steps

1. Clone the repository:
```bash
git clone <repository-url>
cd SaqaParser
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Dependencies

- `pdfplumber` - PDF text extraction
- `langdetect` - Language detection
- `pymorphy2` - Russian morphological analysis
- `natasha` - Russian NLP toolkit
- `regex` - Advanced regular expressions

## Usage

### Basic Workflow

The tool operates in two main steps:

1. **Extract text from PDFs** → `saqa.txt`
2. **Clean the extracted text** → `saqaCleaned.txt`

### Step 1: Extract Text from PDFs

Place PDF files in the `source/` folder, then run:

```bash
python pdf_insert.py
```

This will:
- Extract text from all PDF files in `source/`
- Append extracted text to `saqa.txt`
- Move processed PDFs to `archive/`
- Log processing details to `logs`

### Step 2: Clean the Extracted Text

After extracting text, clean it by running:

```bash
python cleaner.py
```

This will:
- Read text from `saqa.txt`
- Remove special characters and numbers
- Remove Russian words
- Save cleaned text to `saqaCleaned.txt`
- Log processing details to `logs`

## Project Structure

```
SaqaParser/
├── src/                      # Source code modules
│   ├── __init__.py          # Package initialization
│   ├── config.py            # Configuration management
│   ├── pdf_processor.py     # PDF extraction logic
│   ├── text_cleaner.py      # Text cleaning logic
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
- **Language settings**: `primary_language` (default: "ru" for Russian)

### Example: Custom Configuration

```python
from src.config import Config
from src.pdf_processor import PDFProcessor

# Create custom configuration
custom_config = Config(
    source_folder=Path("my_pdfs"),
    archive_folder=Path("my_archive"),
    progress_interval_pages=5
)

# Use custom configuration
processor = PDFProcessor(
    source_folder=custom_config.source_folder,
    archive_folder=custom_config.archive_folder
)
```

## Output Files

- **`saqa.txt`**: Raw extracted text from all processed PDFs
- **`saqaCleaned.txt`**: Cleaned text with Russian words and special characters removed
- **`logs`**: Processing log with timestamps and statistics

## Logging

The tool uses Python's `logging` module with:
- **File logging**: Appends to `logs` file
- **Console logging**: Displays progress and errors
- **Log levels**: INFO, WARNING, ERROR

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

## Testing

Run tests using:

```bash
python -m pytest tests/
```

Or using unittest:

```bash
python -m unittest discover tests
```

## Development

### Code Structure

- **Modular design**: Separate modules for different functionalities
- **Type hints**: Functions include type annotations
- **Documentation**: Docstrings for all classes and functions
- **Error handling**: Comprehensive exception handling

### Adding New Features

1. Add new modules to `src/`
2. Update `src/__init__.py` to export new components
3. Add tests in `tests/`
4. Update this README

## Troubleshooting

### No PDF files found
- Ensure PDF files are in the `source/` folder
- Check file extensions are `.pdf` (case-sensitive)

### Language detection issues
- Some words may be misclassified
- The tool uses multiple methods (language detection, morphology, names) for accuracy

### Memory issues with large PDFs
- Process PDFs in smaller batches
- Consider splitting large PDFs before processing

## License

See LICENSE file for details.

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## Notes

- PDF files are moved (not copied) to `archive/` after processing
- The `source/` and `archive/` folders are preserved in Git but their contents are ignored
- Large files (PDFs, text files) are excluded from Git tracking
