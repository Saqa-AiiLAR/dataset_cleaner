# SaqaParser

A Python tool for extracting text from PDF files and cleaning Sakha (Yakut) language text by removing Russian words, special characters, and repairing OCR errors.

## Quick Start

### Install

```bash
git clone <repository-url>
cd SaqaParser
python -m pip install --upgrade pip
pip install -e ".[dev]"

# Optional: enable Parquet support (requires pandas + pyarrow)
pip install -e ".[dev,parquet]"
```

### Run

```bash
# Place PDF files in workspace/input/ folder, then:
saqa-run

# Results will be saved to workspace/results/DD-MM-YY-HH-MM-SS/
# - saqa.txt (extracted text)
# - saqaCleaned.txt (cleaned text)
# - logs (processing log)
```

That's it! Your cleaned Sakha text is ready.

## What It Does

SaqaParser processes Sakha language PDFs in three steps:

1. **Extracts text** from PDF files
   - (Optionally) extract text from Parquet files if installed with `.[parquet]`
2. **Repairs OCR errors** (fixes broken words like `о ҕ о л о р` → `оҕолор`)
3. **Removes Russian words** using intelligent multi-layer detection:
   - Sakha-specific characters (ҕ, ҥ, ө, һ, ү)
   - Sakha diphthongs (уо, иэ, ыа, үө)
   - Russian marker characters (щ, ц, ъ, ф, в)
   - Morphological patterns
   - Language detection

## Features

- **Smart OCR Repair**: Fixes character hallucinations (6→ҕ, h→һ, o→ө) and merges broken words
- **Multi-Layer Classification**: Accurate Russian/Sakha word separation using 4-layer priority system
- **Adaptive PDF Extraction**: Automatically adjusts extraction parameters for better quality
- **CLI Interface**: Simple commands with flexible options
- **Modular Architecture**: Well-organized, extensible codebase
- **Comprehensive Logging**: Detailed logs with progress tracking

## Basic Usage

### Option 1: Unified Pipeline (Recommended)

Process everything in one command:

```bash
saqa-run                                    # Use default folders
saqa-run --input ./my_pdfs --verbose        # Custom input, show details
saqa-run --results ./output --quiet         # Custom output, quiet mode
```

### Option 2: Step by Step

Process in separate steps:

```bash
# Step 1: Extract text from PDFs
saqa-pdf-extract --input ./pdfs --output extracted.txt

# Step 2: Clean the text
saqa-clean --input extracted.txt --output cleaned.txt
```

## Common Options

```bash
--input PATH      # Input folder (PDFs) or file (text)
--output PATH     # Output file
--archive PATH    # Archive folder for processed PDFs
--results PATH    # Results folder for timestamped output
-v, --verbose     # Show detailed logging
-q, --quiet       # Only log to file (no console output)
```

## Configuration

Edit `src/config.py` or use programmatically:

```python
from src.config import config

# Disable 'в' as Russian marker
config.use_v_as_russian_marker = False

# Adjust word healing
config.word_healer_passes = 7

# Change sensitivity
config.pattern_matching_sensitivity = 0.9
```

## Project Structure

```
SaqaParser/
├── src/              # Core modules
│   ├── pdf_processor.py      # PDF text extraction
│   ├── text_cleaner.py       # Russian word removal
│   ├── word_healer.py        # OCR error repair
│   ├── language_detector.py  # Word classification
│   └── config.py             # Configuration
├── cli/              # Command-line interface
├── tests/            # Test suite
├── workspace/        # Working directory
│   ├── input/        # Place PDF files here
│   ├── archive/      # Processed PDFs moved here
│   └── results/      # Timestamped output folders
└── docs/             # Detailed documentation
```

## Programmatic Usage

```python
from src.pdf_processor import PDFProcessor
from src.text_cleaner import TextCleaner

# Extract text
processor = PDFProcessor(
    input_folder=Path("pdfs"),
    output_file=Path("output.txt")
)
count = processor.process_all_pdfs()

# Clean text
cleaner = TextCleaner(
    input_file=Path("output.txt"),
    output_file=Path("cleaned.txt")
)
char_count = cleaner.clean_text()
```

## How It Works

The tool uses a sophisticated **4-layer priority system** to distinguish Russian from Sakha words:

1. **Layer 1: Sakha Anchors** (Highest - Always Keep)
   - Sakha characters: `ҕ, ҥ, ө, һ, ү`
   - Sakha diphthongs: `уо, иэ, ыа, үө`

2. **Layer 2: Russian Markers** (High - Always Delete)
   - Russian-specific: `щ, ц, ъ, ф, в` (configurable)

3. **Layer 3: Morphological Patterns** (Medium)
   - Russian endings: `-ться, -тся, -ий, -ый, -ость`
   - Sakha endings: `-лар, -лер, -та, -тэ`

4. **Layer 4: Fallback** (Low)
- Language detection (langdetect)
- Morphological analysis (pymorphy2)

## Documentation

- **[Installation Guide](docs/INSTALLATION.md)** - Detailed setup instructions
- **[Usage Guide](docs/USAGE.md)** - Advanced usage, configuration, troubleshooting
- **[Architecture](docs/ARCHITECTURE.md)** - How it works under the hood

## Testing

```bash
pytest tests/                   # Run all tests
pytest tests/ --cov=src        # With coverage
python -m unittest discover    # Alternative with unittest
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install

# Format code
black src/ cli/ tests/

# Lint code
ruff check src/ cli/ tests/

# Type check
mypy src/ cli/
```

## Requirements

- Python 3.8+
- `pip` (up-to-date recommended)
- **Windows note**: Parquet support requires **64-bit Python** (pyarrow has no 32-bit wheels)
- See `pyproject.toml` for dependency groups (`.[dev]`, `.[parquet]`)

## License

See LICENSE file for details.

---

**Quick Links:** [Installation](docs/INSTALLATION.md) | [Usage Guide](docs/USAGE.md) | [Architecture](docs/ARCHITECTURE.md)
