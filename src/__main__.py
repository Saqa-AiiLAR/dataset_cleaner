"""
Package-level entry point for SaqaParser.

Allows running the package with: python -m src
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import cli modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli.pdf_extract import main

if __name__ == "__main__":
    sys.exit(main())
