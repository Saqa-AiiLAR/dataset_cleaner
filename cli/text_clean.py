"""
Entry point for text cleaning.
Removes Russian words and special characters from saqa.txt and saves to saqaCleaned.txt.
"""
import argparse
import sys
import logging
from pathlib import Path

from src.text_cleaner import TextCleaner
from src.logging_config import setup_logging, disable_console_logging
from src.config import config
from src.exceptions import SaqaParserError


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
        """
    )
    
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help=f"Input text file (default: {config.output_file})"
    )
    
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=f"Output cleaned text file (default: {config.cleaned_output_file})"
    )
    
    parser.add_argument(
        "--log",
        type=Path,
        default=None,
        help=f"Log file path (default: {config.log_file})"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging (DEBUG level)"
    )
    
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress console output (only log to file)"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logging(args.log or config.log_file, level=log_level)
    
    if args.quiet:
        disable_console_logging(logger)
    
    try:
        # Create cleaner with custom paths if provided
        cleaner = TextCleaner(
            input_file=args.input,
            output_file=args.output,
            log_file=args.log
        )
        
        char_count = cleaner.clean_text()
        
        logger.info(f"Processing complete. Cleaned text contains {char_count} characters.")
        return 0
    
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        return 130
    
    except SaqaParserError as e:
        logger.error(f"Error: {str(e)}")
        return 1
    
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

