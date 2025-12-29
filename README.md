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
- **Word Healer**: Advanced OCR repair module that fixes broken words and character hallucinations
  - Character normalization (6→ҕ, h→һ, o→ө, etc.)
  - Broken word repair (merges single letters separated by spaces)
  - Word boundary protection (prevents merging separate words)
  - False hyphen removal (fixes line break artifacts)
  - Exception dictionary support
- **Adaptive PDF Extraction**: Intelligent tolerance adjustment for better text extraction
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

### Initial Setup

After cloning the repository, run the setup script to create the required workspace folder structure:

```bash
python scripts/setup_workspace.py
```

This script will:
- Create `workspace/input/` - Place your PDF files here
- Create `workspace/archive/` - Processed PDFs are moved here
- Create `workspace/logs/` - Log files are stored here
- Create `workspace/results/` - Timestamped results are saved here

**Why this is needed:**
- The workspace folder structure is tracked in Git via `.gitkeep` files
- Each workspace subfolder has its own `.gitignore` file to ignore user content (PDFs, text files, etc.)
- This approach ensures folders exist after cloning while keeping user files out of version control

**Setup script options:**
```bash
# Dry run (see what would be created)
python scripts/setup_workspace.py --dry-run

# Include optional folders (logs, results)
python scripts/setup_workspace.py --include-optional

# Quiet mode (only errors)
python scripts/setup_workspace.py --quiet

# Specify repository root
python scripts/setup_workspace.py --root /path/to/repo
```

## Usage

### Basic Workflow

The tool can be used in two ways:

**Option 1: Unified pipeline (Recommended)**
- Run `saqa-run` to extract and clean in one command, saving results to timestamped folders

**Option 2: Separate steps**
1. **Extract text from PDFs** → `saqa.txt`
2. **Clean the extracted text** → `saqaCleaned.txt`

### Option 1: Unified Pipeline (saqa-run)

The `saqa-run` command performs both extraction and cleaning sequentially, saving results to timestamped folders in the `results/` directory.

**Basic usage:**
```bash
saqa-run
# or if not installed:
python -m cli.run
```

This will:
- Create a timestamped folder in `workspace/results/` (format: `DD-MM-YY-HH-MM-SS`, e.g., `19-01-25-19-28-32`)
- Extract text from all PDF files in `workspace/input/` folder
- Clean the extracted text
- Save `saqa.txt`, `saqaCleaned.txt`, and `logs` in the timestamped folder
- Move processed PDFs to `workspace/archive/` folder

**With CLI options:**
```bash
# Custom input and results paths
saqa-run --input ./my_pdfs --results ./my_results

# Verbose mode for detailed logging
saqa-run --verbose

# Quiet mode (only file logging)
saqa-run --quiet

# Full example with all options
saqa-run --input ./pdfs --archive ./processed --results ./output --verbose
```

**Result structure:**
```
workspace/results/
├── 19-01-25-19-28-32/
│   ├── saqa.txt
│   ├── saqaCleaned.txt
│   └── logs
├── 19-01-25-20-15-45/
│   ├── saqa.txt
│   ├── saqaCleaned.txt
│   └── logs
└── ...
```

### Option 2: Separate Steps

##### Step 1: Extract Text from PDFs

Place PDF files in the `workspace/input/` folder, then run:

**Basic usage:**
```bash
python -m cli.pdf_extract
# or if installed:
saqa-pdf-extract
```

**With CLI options:**
```bash
# Custom input and output paths
python -m cli.pdf_extract --input ./my_pdfs --output ./output.txt

# Verbose mode for detailed logging
python -m cli.pdf_extract --verbose

# Quiet mode (only file logging)
python -m cli.pdf_extract --quiet

# Full example with all options
python -m cli.pdf_extract --input ./pdfs --archive ./processed --output ./text.txt --log ./app.log --verbose
```

**Using entry point (if installed):**
```bash
saqa-pdf-extract --input ./my_pdfs --output ./output.txt
```

This will:
- Extract text from all PDF files in `workspace/input/` (or specified folder)
- Append extracted text to `saqa.txt` (or specified output file)
- Move processed PDFs to `workspace/archive/` (or specified archive folder)
- Log processing details to `workspace/logs` (or specified log file)

#### Step 2: Clean the Extracted Text

After extracting text, clean it by running:

**Basic usage:**
```bash
python -m cli.text_clean
# or if installed:
saqa-clean
```

**With CLI options:**
```bash
# Custom input and output paths
python -m cli.text_clean --input ./input.txt --output ./cleaned.txt

# Verbose mode
python -m cli.text_clean --verbose

# Quiet mode
python -m cli.text_clean --quiet

# Full example
python -m cli.text_clean --input saqa.txt --output cleaned.txt --log app.log --verbose
```

**Using entry point (if installed):**
```bash
saqa-clean --input saqa.txt --output cleaned.txt
```

This will:
- Read text from `saqa.txt` (or specified input file)
- Remove special characters and numbers
- **Apply word healing** to repair OCR-broken words (normalize characters, merge broken words)
- Remove Russian words using multi-layer classification
- Save cleaned text to `saqaCleaned.txt` (or specified output file)
- Log processing details to `workspace/logs` (or specified log file)

### CLI Options

#### saqa-run Options

- `--input PATH` - Input folder containing PDF files (default: `workspace/input/`)
- `--archive PATH` - Archive folder for processed PDFs (default: `workspace/archive/`)
- `--results PATH` - Results folder for timestamped output (default: `workspace/results/`)
- `-v, --verbose` - Enable verbose logging (DEBUG level)
- `-q, --quiet` - Suppress console output (only log to file)
- `-h, --help` - Show help message

#### pdf_extract Options

- `--input PATH` - Input folder containing PDF files (default: `workspace/input/`)
- `--archive PATH` - Archive folder for processed PDFs (default: `workspace/archive/`)
- `--output PATH` - Output file for extracted text (default: `saqa.txt`)
- `--log PATH` - Log file path (default: `workspace/logs`)
- `-v, --verbose` - Enable verbose logging (DEBUG level)
- `-q, --quiet` - Suppress console output (only log to file)
- `-h, --help` - Show help message

#### text_clean Options

- `--input PATH` - Input text file (default: `saqa.txt`)
- `--output PATH` - Output cleaned text file (default: `saqaCleaned.txt`)
- `--log PATH` - Log file path (default: `workspace/logs`)
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
│   ├── word_healer.py       # OCR word repair module
│   ├── utils.py             # Utility functions
│   └── exceptions.py        # Custom exceptions
├── tests/                   # Test files
│   ├── __init__.py
│   ├── test_pdf_processor.py
│   ├── test_text_cleaner.py
│   ├── test_word_healer.py
│   └── test_utils.py
├── workspace/               # Working directory for all project files
│   ├── .gitkeep            # Tracks workspace directory in Git
│   ├── input/               # Place PDF files here (contents ignored via .gitignore)
│   │   ├── .gitkeep        # Tracks folder in Git
│   │   └── .gitignore      # Local ignore rules for this folder
│   ├── archive/             # Processed PDFs moved here (contents ignored)
│   │   ├── .gitkeep
│   │   └── .gitignore
│   ├── logs/                # Log files (contents ignored)
│   │   ├── .gitkeep
│   │   └── .gitignore
│   └── results/             # Timestamped results (contents ignored)
│       ├── .gitkeep
│       └── .gitignore
│       └── DD-MM-YY-HH-MM-SS/  # Individual run results (created by saqa-run)
├── scripts/                 # Setup and utility scripts
│   ├── __init__.py
│   └── setup_workspace.py  # Script to create workspace folder structure
├── cli/                     # Command-line interface entry points
│   ├── __init__.py
│   ├── pdf_extract.py      # Entry point for PDF extraction
│   └── text_clean.py       # Entry point for text cleaning
├── requirements.txt         # Python dependencies
├── pyproject.toml          # Modern Python project configuration
├── CHANGELOG.md            # Version history
├── README.md               # This file
└── .gitignore              # Git ignore rules
```

## Configuration

Configuration is managed in `src/config.py`. You can modify:

- **Folder paths**: `input_folder`, `archive_folder`, `results_folder`
- **File paths**: `output_file`, `cleaned_output_file`, `log_file`
- **Processing settings**: 
  - `progress_interval_pages`: Show progress every N pages (default: 10)
  - `progress_interval_words`: Show progress every N words (default: 1000)
  - `debug_sample_size`: Number of Russian words to show in debug (default: 20)
- **Language detection settings**: 
  - `primary_language`: Primary language to detect (default: "ru" for Russian)
  - `use_v_as_russian_marker`: Include 'в' as Russian marker (default: True)
  - `pattern_matching_sensitivity`: Threshold for morphological pattern matching (default: 0.8)
- **Word healer settings**:
  - `word_healer_enabled`: Enable word healing for OCR repair (default: True)
  - `word_healer_passes`: Maximum number of repair iterations (default: 5)
  - `word_healer_exceptions_file`: Optional path to exceptions file (default: None)
- **PDF extraction settings**:
  - `pdf_x_tolerance`: Horizontal tolerance for text extraction (default: 3)
  - `pdf_y_tolerance`: Vertical tolerance for text extraction (default: 3)
  - `pdf_adaptive_tolerance`: Enable adaptive tolerance strategy (default: True)
  - `pdf_badness_threshold`: Threshold for retry with higher tolerance (default: 0.3)
  - `pdf_layout_mode`: Use layout-aware extraction (default: True)

### Example: Custom Configuration

```python
from pathlib import Path
from src.config import Config
from src.pdf_processor import PDFProcessor

# Create custom configuration
custom_config = Config(
    input_folder=Path("my_pdfs"),
    archive_folder=Path("my_archive"),
    progress_interval_pages=5,
    use_v_as_russian_marker=False,  # Disable 'в' as Russian marker
    pattern_matching_sensitivity=0.9  # Higher sensitivity
)

# Use custom configuration
processor = PDFProcessor(
    input_folder=custom_config.input_folder,
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
    input_folder=Path("pdfs"),
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

# Word healing (OCR repair)
from src.word_healer import WordHealer

healer = WordHealer()
broken_text = "о 6 о л о р  баhар"
healed_text = healer.heal_text(broken_text)
# Result: "оҕолор баһар" (normalized and repaired)
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

## Word Healer Module

The Word Healer module repairs OCR-related errors in Sakha text before Russian word removal. It addresses common OCR issues:

### Character Normalization

OCR often confuses similar characters. The healer normalizes:
- `6` → `ҕ` (digit 6 confused with Sakha ҕ)
- `h` → `һ` (Latin h confused with Sakha һ)
- `o` → `ө` (Latin o confused with Sakha ө)
- `y` → `ү` (Latin y confused with Sakha ү)
- `б` → `ҕ` (Cyrillic б sometimes confused with ҕ)

**Protection**: Numeric sequences (dates, phone numbers, ISBN) are protected from normalization.

### Broken Word Repair

OCR can break words with spaces: `"оҕолор"` → `"о ҕ о л о р"`. The healer:
- Merges single letters separated by single spaces
- Preserves word boundaries (double spaces indicate separate words)
- Uses multiple passes with early termination
- Validates merged words using Sakha character detection

### Word Boundary Protection

To prevent merging separate short Sakha words (like `"бу"` and `"кинигэ"`):
- Double or multiple spaces are marked as word boundaries
- Boundaries are preserved during repair
- Prevents false merging of adjacent words

### False Hyphen Removal

Removes hyphens that are line break artifacts:
- `"оҕо-лор"` → `"оҕолор"` (if both parts contain Sakha characters)
- Only merges when both parts are Sakha words

### Exception Dictionary

Words that should NOT be merged or repaired can be specified:
- Built-in exceptions: `г.`, `стр.`, `т.д.`, `и т.д.`
- Optional file-based exceptions: Create `exceptions.txt` with one pattern per line

**Example `exceptions.txt`:**
```
# Abbreviations that should not be merged
г.
стр.
т.д.

# Short words (context-dependent)
бу
уо
```

### Configuration

Word healing is enabled by default but can be configured:
```python
from src.config import config

# Disable word healing
config.word_healer_enabled = False

# Adjust number of repair passes
config.word_healer_passes = 7

# Specify exceptions file
config.word_healer_exceptions_file = Path("my_exceptions.txt")
```

## Adaptive PDF Extraction

The PDF processor uses an adaptive tolerance strategy to improve text extraction:

1. **First attempt**: Conservative extraction with `x_tolerance=1, y_tolerance=1`
2. **Badness score calculation**: Ratio of single-character "words" to total words
3. **Adaptive retry**: If score > threshold (0.3), retry with higher tolerance
4. **Progressive tolerance**: Try `(3, 3)`, then `(5, 5)` if needed
5. **Layout-aware**: Uses `layout=True` for better column detection

This prevents merging text from different columns while still repairing broken words.

### Configuration

```python
from src.config import config

# Disable adaptive tolerance (use fixed values)
config.pdf_adaptive_tolerance = False

# Adjust tolerance values
config.pdf_x_tolerance = 5
config.pdf_y_tolerance = 5

# Adjust badness threshold
config.pdf_badness_threshold = 0.4  # More aggressive retry

# Disable layout mode
config.pdf_layout_mode = False
```

## Output Files

### Using saqa-run

Results are saved in timestamped folders under `workspace/results/`:
- **`workspace/results/DD-MM-YY-HH-MM-SS/saqa.txt`**: Raw extracted text from all processed PDFs
- **`workspace/results/DD-MM-YY-HH-MM-SS/saqaCleaned.txt`**: Cleaned text with Russian words and special characters removed
- **`workspace/results/DD-MM-YY-HH-MM-SS/logs`**: Processing log with timestamps and statistics

### Using separate commands

- **`saqa.txt`**: Raw extracted text from all processed PDFs (in project root)
- **`saqaCleaned.txt`**: Cleaned text with Russian words and special characters removed (in project root)
- **`logs`**: Processing log with timestamps and statistics (in project root)

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
- `MissingFileError`: File or folder not found (custom exception)
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
- Ensure PDF files are in the `workspace/input/` folder (or use `--input` option)
- Check file extensions are `.pdf` (case-sensitive)

### Language detection issues
- Some words may be misclassified
- The tool uses multiple methods (anchors, markers, patterns, language detection, morphology) for accuracy
- Adjust `use_v_as_russian_marker` if needed
- Modify `pattern_matching_sensitivity` for different sensitivity levels

### OCR word breakage issues
- If words are still broken after healing, increase `word_healer_passes` in config
- Check that word boundaries (double spaces) are preserved in source text
- Verify that character normalization is working (check logs with `--verbose`)
- Add problematic patterns to `exceptions.txt` if they're being incorrectly merged

### PDF extraction quality
- If text from different columns is merging, disable `pdf_adaptive_tolerance` or reduce tolerance values
- Increase `pdf_badness_threshold` if too many single-character words remain
- Try disabling `pdf_layout_mode` for simpler layouts

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

- PDF files are moved (not copied) to `workspace/archive/` after processing
- Workspace folder structure uses local `.gitignore` files in each subfolder to ignore user content (PDFs, text files) while tracking folder structure via `.gitkeep` files
- Run `python scripts/setup_workspace.py` after cloning to create the required folder structure
- The tool uses lazy loading for heavy dependencies (pymorphy2, natasha) to improve startup performance
