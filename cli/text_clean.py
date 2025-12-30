"""
Entry point for text cleaning.
Removes Russian words and special characters from saqa.txt and saves to saqaCleaned.txt.
"""

import argparse
import sys
from pathlib import Path

# Add project root to Python path for direct script execution
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.text_cleaner import TextCleaner  # noqa: E402
from src.config import config  # noqa: E402
from cli.common import setup_cli_logging, add_common_arguments, handle_cli_execution  # noqa: E402


def main():
    """Main entry point for text cleaning."""
    parser = argparse.ArgumentParser(
        description="Clean text by removing Russian words and special characters",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s --input ./input.txt --output ./cleaned.txt
  %(prog)s --verbose
        """,
    )

    parser.add_argument(
        "--input", type=Path, default=None, help=f"Input text file (default: {config.output_file})"
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=f"Output cleaned text file (default: {config.cleaned_output_file})",
    )

    add_common_arguments(parser)

    args = parser.parse_args()

    # Set up logging
    logger = setup_cli_logging(args.log, args.verbose, args.quiet)

    def run_text_cleaning() -> int:
        """Inner function for execution logic."""
        # Create cleaner with custom paths if provided
        cleaner = TextCleaner(input_file=args.input, output_file=args.output, log_file=args.log)

        char_count = cleaner.clean_text()

        logger.info(f"Processing complete. Cleaned text contains {char_count} characters.")
        return 0

    return handle_cli_execution(run_text_cleaning, logger)


if __name__ == "__main__":
    sys.exit(main())
