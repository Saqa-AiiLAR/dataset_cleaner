# Installation Guide

Complete installation instructions for SaqaParser.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (for cloning the repository)

## Installation Methods

### Method 1: Using pyproject.toml (Recommended)

This method installs SaqaParser as a package with all entry points.

```bash
# Clone the repository
git clone <repository-url>
cd SaqaParser

# Upgrade packaging tooling (helps avoid pyproject/install issues)
python -m pip install --upgrade pip

# Install in editable mode
pip install -e .

# Verify installation
saqa-run --help
```

### Method 2: Using requirements.txt

For simpler installations without package management:

```bash
# Clone the repository
git clone <repository-url>
cd SaqaParser

# Install dependencies
pip install -r requirements.txt

# Optional: Parquet support (pandas + pyarrow)
pip install -r requirements-parquet.txt

# Run using Python modules
python -m cli.run --help
```

### Method 3: Development Installation

For contributors and developers:

```bash
# Clone the repository
git clone <repository-url>
cd SaqaParser

# Upgrade packaging tooling (helps avoid pyproject/install issues)
python -m pip install --upgrade pip

# Install with development dependencies
pip install -e ".[dev]"

# Optional: Parquet support (pandas + pyarrow)
pip install -e ".[dev,parquet]"

# Set up pre-commit hooks
pre-commit install

# Verify dev tools
black --version
ruff --version
mypy --version
pytest --version
```

## Initial Setup

Workspace directories are created automatically when you run any CLI command. 
No manual setup is required!

The workspace structure includes:
- `workspace/input/` - Place your PDF files here
- `workspace/archive/` - Processed PDFs moved here
- `workspace/logs/` - Log files stored here
- `workspace/results/` - Timestamped output folders
- `workspace/additional/` - Optional word lists for filtering

## Dependencies

### Core Dependencies

- `pdfplumber>=0.10.0,<1.0.0` - PDF text extraction
- `langdetect>=1.0.9,<2.0.0` - Language detection
- `pymorphy2>=0.9.1,<1.0.0` - Russian morphological analysis
- `natasha>=1.5.0,<2.0.0` - Russian NLP toolkit
- `regex>=2023.0.0,<2026.0.0` - Advanced regular expressions

### Optional Dependencies

- `pandas` + `pyarrow` - Required only for Parquet input support (`.[parquet]`)

### Development Dependencies

- `pytest>=7.0.0` - Testing framework
- `pytest-cov>=4.0.0` - Code coverage
- `black>=24.1.0` - Code formatter
- `ruff>=0.1.0` - Fast linter
- `mypy>=1.8.0` - Type checker
- `pre-commit>=3.5.0` - Git hooks

## Verification

Test your installation:

```bash
# Check entry points
saqa-run --help
saqa-pdf-extract --help
saqa-clean --help

# Run tests
pytest tests/

# Check code quality
black --check src/ cli/ tests/
ruff check src/ cli/ tests/
mypy src/ cli/
```

## Troubleshooting

### Import Errors

If you get import errors:

```bash
# Ensure you're in the project root
cd /path/to/SaqaParser

# Reinstall in editable mode
pip install -e .

# Or add to PYTHONPATH temporarily
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Missing Dependencies

```bash
# Reinstall all dependencies
pip install -r requirements.txt

# Or reinstall package
pip uninstall saqaparser
pip install -e ".[dev]"
```

### Permission Errors

```bash
# Use user install
pip install --user -e .

# Or use virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

### Python Version Issues

```bash
# Check Python version
python --version  # Should be 3.8+

# Use specific Python version
python3.8 -m pip install -e .
python3.9 -m pip install -e .
```

## Platform-Specific Notes

### macOS

```bash
# Install Python 3.8+ via Homebrew
brew install python@3.11

# Install SaqaParser
pip3 install -e ".[dev]"
```

### Linux

```bash
# Install Python 3.8+ (Ubuntu/Debian)
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# Install SaqaParser
pip3 install -e ".[dev]"
```

### Windows

```bash
# Install Python 3.8+ from python.org
# Then in Command Prompt or PowerShell:

pip install -e ".[dev]"
```

Notes:
- Parquet support requires **64-bit Python** on Windows (pyarrow has no 32-bit wheels).

## Virtual Environment (Recommended)

Using a virtual environment isolates dependencies:

```bash
# Create virtual environment
python -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install SaqaParser
pip install -e ".[dev]"

# Deactivate when done
deactivate
```

## Updating

To update to the latest version:

```bash
cd SaqaParser
git pull origin main
pip install -e ".[dev]"
```

## Uninstallation

```bash
# Uninstall package
pip uninstall saqaparser

# Remove repository
cd ..
rm -rf SaqaParser
```

## Next Steps

- **[Usage Guide](USAGE.md)** - Learn how to use SaqaParser
- **[Architecture](ARCHITECTURE.md)** - Understand how it works

