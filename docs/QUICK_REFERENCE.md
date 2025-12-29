# Quick Reference

Fast reference for common tasks and commands.

## Installation

```bash
pip install -e ".[dev]"          # Install with dev tools
pre-commit install                # Set up git hooks (optional)
```

Note: Workspace folders are created automatically when you run CLI commands.

## Usage

```bash
# Process PDFs (one command)
saqa-run

# Step by step
saqa-pdf-extract                  # Extract text
saqa-clean                        # Clean text

# With options
saqa-run --verbose                # Show details
saqa-run --input ./pdfs           # Custom input
saqa-run --results ./output       # Custom output
```

## Development

```bash
# Format code
black src/ cli/ tests/

# Lint code
ruff check --fix src/ cli/ tests/

# Type check
mypy src/ cli/

# Run tests
pytest tests/
pytest tests/ --cov=src           # With coverage

# Pre-commit (runs all checks)
pre-commit run --all-files
```

## Configuration

```python
from src.config import config

# Common settings
config.word_healer_enabled = False
config.use_v_as_russian_marker = False
config.progress_interval_pages = 20
config.pdf_adaptive_tolerance = True
```

## Programmatic Usage

```python
from pathlib import Path
from src import PDFProcessor, TextCleaner, WordClassifier

# Extract
processor = PDFProcessor(input_folder=Path("pdfs"))
processor.process_all_pdfs()

# Clean
cleaner = TextCleaner(input_file=Path("text.txt"))
cleaner.clean_text()

# Classify
classifier = WordClassifier()
is_russian = classifier.is_russian_word("привет")
```

## File Locations

```
workspace/
├── input/          # Place PDFs here
├── archive/        # Processed PDFs go here
├── results/        # Output folders (timestamped)
├── logs/           # Log files
└── additional/     # Custom word lists
```

## Common Issues

| Issue | Solution |
|-------|----------|
| No PDFs found | Check `workspace/input/` folder |
| Import errors | Run `pip install -e .` |
| Tests fail | Check test file parameter names |
| Slow processing | Already optimized! (40-60% faster) |
| Empty output | Check logs with `--verbose` |

## Testing

```bash
# All tests
pytest tests/

# Specific test
pytest tests/test_text_cleaner.py::TestTextCleaner::test_remove_special_characters

# With coverage
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

## Git Workflow

```bash
# Create branch
git checkout -b feature/my-feature

# Make changes, then
git add .
git commit -m "feat: description"
# → Pre-commit hooks run automatically

# Push
git push origin feature/my-feature
```

## Documentation

- **README.md** - Quick start
- **docs/INSTALLATION.md** - Setup guide
- **docs/USAGE.md** - Advanced usage
- **docs/ARCHITECTURE.md** - How it works

## Performance

- **Text processing**: 40-60% faster (pre-compiled regex)
- **Startup**: Fast (lazy loading)
- **Memory**: Efficient (streaming, no full load)

## Code Style

- **Line length**: 100 characters
- **Formatter**: black
- **Linter**: ruff
- **Type checker**: mypy
- **Docstrings**: Google style

## Entry Points

```bash
saqa-run          # cli/run.py
saqa-pdf-extract  # cli/pdf_extract.py
saqa-clean        # cli/text_clean.py
```

## Version

Current: **1.1.0**

