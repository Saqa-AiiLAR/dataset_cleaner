# Usage Guide

Advanced usage instructions, configuration options, and troubleshooting for SaqaParser.

## Table of Contents

- [Command-Line Interface](#command-line-interface)
- [Configuration](#configuration)
- [Word Healing](#word-healing)
- [PDF Extraction](#pdf-extraction)
- [Programmatic Usage](#programmatic-usage)
- [Troubleshooting](#troubleshooting)

## Command-Line Interface

### saqa-run (Unified Pipeline)

The recommended way to process PDFs - extracts and cleans in one command.

#### Basic Usage

```bash
saqa-run                                    # Use defaults
saqa-run --input ./pdfs                     # Custom input folder
saqa-run --results ./output                 # Custom results folder
saqa-run --archive ./processed              # Custom archive folder
saqa-run --verbose                          # Show detailed logs
saqa-run --quiet                            # Only file logging
```

#### Arguments

- `--input PATH` - Input folder with PDF files (default: `workspace/input/`)
- `--archive PATH` - Archive folder for processed PDFs (default: `workspace/archive/`)
- `--results PATH` - Results folder for output (default: `workspace/results/`)
- `-v, --verbose` - Enable DEBUG logging
- `-q, --quiet` - Suppress console output

#### Output Structure

Results are saved in timestamped folders:

```
workspace/results/
└── DD-MM-YY-HH-MM-SS/       # e.g., 30-12-25-14-30-00
    ├── saqa.txt              # Raw extracted text
    ├── saqaCleaned.txt       # Cleaned text
    └── logs                  # Processing log
```

### saqa-pdf-extract

Extract text from PDF files without cleaning.

```bash
saqa-pdf-extract                            # Use defaults
saqa-pdf-extract --input ./pdfs             # Custom input
saqa-pdf-extract --output text.txt          # Custom output
saqa-pdf-extract --archive ./done           # Custom archive
saqa-pdf-extract --log ./app.log            # Custom log
```

#### Arguments

- `--input PATH` - Input folder (default: `workspace/input/`)
- `--archive PATH` - Archive folder (default: `workspace/archive/`)
- `--output PATH` - Output file (default: `saqa.txt`)
- `--log PATH` - Log file (default: `workspace/logs`)
- `-v, --verbose` - Enable DEBUG logging
- `-q, --quiet` - Suppress console output

### saqa-clean

Clean already-extracted text.

```bash
saqa-clean                                  # Use defaults
saqa-clean --input text.txt                 # Custom input
saqa-clean --output cleaned.txt             # Custom output
saqa-clean --log ./app.log                  # Custom log
```

#### Arguments

- `--input PATH` - Input text file (default: `saqa.txt`)
- `--output PATH` - Output file (default: `saqaCleaned.txt`)
- `--log PATH` - Log file (default: `workspace/logs`)
- `-v, --verbose` - Enable DEBUG logging
- `-q, --quiet` - Suppress console output

## Configuration

Configuration is managed in `src/config.py` using a dataclass.

### File and Folder Paths

```python
from src.config import config

# Change default folders
config.input_folder = Path("my_pdfs")
config.archive_folder = Path("processed")
config.results_folder = Path("output")

# Change default files
config.output_file = Path("extracted.txt")
config.cleaned_output_file = Path("cleaned.txt")
config.log_file = Path("app.log")
```

### Processing Settings

```python
# Progress reporting
config.progress_interval_pages = 5      # Report every 5 pages
config.progress_interval_words = 500    # Report every 500 words
config.debug_sample_size = 30           # Show 30 sample words in debug

# Language detection
config.primary_language = "ru"          # Primary language (Russian)
config.use_v_as_russian_marker = False  # Disable 'в' as Russian marker
config.pattern_matching_sensitivity = 0.9  # Higher sensitivity (0.0-1.0)
```

### Word Healer Settings

```python
# Enable/disable word healing
config.word_healer_enabled = True

# Number of repair iterations
config.word_healer_passes = 7

# Exception file (words to NOT repair)
config.word_healer_exceptions_file = Path("exceptions.txt")
```

### PDF Extraction Settings

```python
# Tolerance for text extraction
config.pdf_x_tolerance = 5
config.pdf_y_tolerance = 5

# Adaptive tolerance (automatically adjust)
config.pdf_adaptive_tolerance = True
config.pdf_badness_threshold = 0.4      # Threshold for retry (0.0-1.0)

# Layout-aware extraction
config.pdf_layout_mode = True
```

### Custom Configuration Example

```python
from pathlib import Path
from src.config import Config
from src.pdf_processor import PDFProcessor

# Create custom configuration
custom_config = Config(
    input_folder=Path("my_pdfs"),
    archive_folder=Path("done"),
    progress_interval_pages=5,
    use_v_as_russian_marker=False,
    word_healer_passes=7
)

# Use in processor
processor = PDFProcessor(
    input_folder=custom_config.input_folder,
    archive_folder=custom_config.archive_folder
)
```

## Word Healing

The Word Healer module repairs OCR errors before Russian word removal.

### Character Normalization

OCR often confuses similar characters:

| OCR Error | Correct | Example |
|-----------|---------|---------|
| `6` | `ҕ` | `о6олор` → `оҕолор` |
| `h` | `һ` | `баhар` → `баһар` |
| `o` | `ө` | `бoрo` → `бөрө` |
| `y` | `ү` | `yрэн` → `үрэн` |
| `8` | `ө` | `8лөр` → `өлөр` |

### Broken Word Repair

Merges single letters separated by spaces:

```
Before: о ҕ о л о р   б а һ а р
After:  оҕолор баһар
```

Configuration:

```python
config.word_healer_passes = 5  # More passes = more thorough
```

### Word Boundary Protection

Double spaces mark word boundaries to prevent false merging:

```
Input:  "бу  кинигэ"  # Double space = boundary
Output: "бу кинигэ"   # Stays as two words
```

### False Hyphen Removal

Removes line-break hyphens:

```
Before: оҕо-лор (hyphen from PDF line break)
After:  оҕолор
```

### Exception Dictionary

Create `workspace/additional/exceptions.txt` to exclude patterns:

```
# Abbreviations
г.
стр.
т.д.

# Short words (if needed)
бу
уо
```

## PDF Extraction

### Adaptive Tolerance

The PDF processor automatically adjusts extraction parameters:

1. **First attempt**: Conservative (`x_tolerance=1, y_tolerance=1`)
2. **Quality check**: Calculate "badness score" (ratio of single-char words)
3. **Adaptive retry**: If score > 0.3, retry with higher tolerance
4. **Progressive**: Try `(3,3)`, then `(5,5)` if needed

### Configuration

```python
# Disable adaptive mode (use fixed tolerance)
config.pdf_adaptive_tolerance = False
config.pdf_x_tolerance = 5
config.pdf_y_tolerance = 5

# Adjust badness threshold
config.pdf_badness_threshold = 0.4  # Higher = more aggressive retry

# Disable layout mode
config.pdf_layout_mode = False
```

### Common Issues

#### Text from Different Columns Merging

```python
# Reduce tolerance
config.pdf_x_tolerance = 1
config.pdf_y_tolerance = 1
```

#### Too Many Single-Character Words

```python
# Lower badness threshold (retry sooner)
config.pdf_badness_threshold = 0.2
```

#### Scanned PDFs (No Text Layer)

SaqaParser requires PDFs with text layers. For scanned PDFs:
1. Use OCR software first (Tesseract, Adobe Acrobat, ABBYY FineReader)
2. Then process with SaqaParser

## Programmatic Usage

### Basic Example

```python
from pathlib import Path
from src.pdf_processor import PDFProcessor
from src.text_cleaner import TextCleaner

# Extract text
processor = PDFProcessor(
    input_folder=Path("pdfs"),
    output_file=Path("output.txt")
)
count = processor.process_all_pdfs()
print(f"Processed {count} files")

# Clean text
cleaner = TextCleaner(
    input_file=Path("output.txt"),
    output_file=Path("cleaned.txt")
)
char_count = cleaner.clean_text()
print(f"Cleaned text: {char_count} characters")
```

### Word Classification

```python
from src.language_detector import WordClassifier

classifier = WordClassifier()

# Check if word is Russian
is_russian = classifier.is_russian_word("привет")  # True
is_sakha = classifier.is_russian_word("баҕар")     # False

# Check specific features
has_anchor = classifier.has_sakha_anchor_chars("оҕолор")  # True
has_marker = classifier.has_russian_marker_chars("царь")   # True
```

### Word Healing

```python
from src.word_healer import WordHealer

healer = WordHealer()

# Repair broken text
broken = "о 6 о л о р  б а h а р"
healed = healer.heal_text(broken)
print(healed)  # "оҕолор баһар"

# With custom exceptions
healer = WordHealer(exceptions_file=Path("my_exceptions.txt"))
```

### Custom Configuration

```python
from pathlib import Path
from src.config import Config
from src.pdf_processor import PDFProcessor

# Create custom config
cfg = Config(
    input_folder=Path("data/pdfs"),
    archive_folder=Path("data/done"),
    progress_interval_pages=20,
    word_healer_enabled=False,
    pdf_adaptive_tolerance=True
)

# Validate configuration
cfg.validate()

# Create directories
cfg.setup_directories()

# Use in processor
processor = PDFProcessor(
    input_folder=cfg.input_folder,
    archive_folder=cfg.archive_folder
)
```

## Additional Word Lists

Place text files in `workspace/additional/` to mark words as Russian:

```
workspace/additional/
├── russian_names.txt
├── technical_terms.txt
└── custom_words.txt
```

Format (one word per line):

```
# This is a comment
привет
мир
здравствуй
```

The tool extracts stems automatically, so `привет` will match `привета`, `приветом`, etc.

## Troubleshooting

### No PDF Files Found

```bash
# Check input folder
ls workspace/input/

# Ensure files have .pdf extension
# Use custom input folder
saqa-run --input ./my_pdfs
```

### Language Detection Issues

Some words may be misclassified. To adjust:

```python
# Disable 'в' as Russian marker (if causing issues)
config.use_v_as_russian_marker = False

# Increase sensitivity
config.pattern_matching_sensitivity = 0.9

# Add words to additional folder
echo "проблемное_слово" >> workspace/additional/custom.txt
```

### OCR Repair Issues

If words are still broken after healing:

```python
# Increase repair passes
config.word_healer_passes = 10

# Check word boundaries in source text
# Ensure double spaces separate distinct words
```

### Memory Issues with Large PDFs

```bash
# Process in smaller batches
# Split large PDFs before processing
# Use quiet mode to reduce logging overhead
saqa-run --quiet
```

### Empty Output

Check logs for details:

```bash
# Run with verbose mode
saqa-run --verbose

# Check log file
cat workspace/results/DD-MM-YY-HH-MM-SS/logs
```

Common causes:
- All words were classified as Russian
- Input file is empty or unreadable
- PDF has no text layer (scanned images)

## Performance Tips

1. **Use quiet mode** for large batches: `saqa-run --quiet`
2. **Adjust progress intervals** for less logging:
   ```python
   config.progress_interval_pages = 50
   config.progress_interval_words = 5000
   ```
3. **Disable word healing** if not needed:
   ```python
   config.word_healer_enabled = False
   ```
4. **Process PDFs in batches** rather than all at once

## Best Practices

1. **Always backup** original PDFs before processing
2. **Test with small batch** first to verify results
3. **Review cleaned output** to ensure quality
4. **Keep logs** for debugging and record-keeping
5. **Use version control** for configuration changes

## Next Steps

- **[Architecture Guide](ARCHITECTURE.md)** - Understand how it works
- **[Contributing Guide](CONTRIBUTING.md)** - Contribute to the project

