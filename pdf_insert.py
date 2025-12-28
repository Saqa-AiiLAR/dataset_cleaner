"""
Entry point for PDF text extraction.
Extracts text from PDF files in source/ folder and appends to saqa.txt.
"""
import argparse
import sys
import logging
from pathlib import Path

from src.pdf_processor import PDFProcessor
from src.utils import setup_logging
from src.config import config
from src.exceptions import SaqaParserError


def main():
    """Main entry point for PDF extraction."""
    parser = argparse.ArgumentParser(
        description="Extract text from PDF files and append to output file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s --source ./my_pdfs --output ./output.txt
  %(prog)s --verbose
        """
    )
    
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help=f"Source folder containing PDF files (default: {config.source_folder})"
    )
    
    parser.add_argument(
        "--archive",
        type=Path,
        default=None,
        help=f"Archive folder for processed PDFs (default: {config.archive_folder})"
    )
    
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=f"Output file for extracted text (default: {config.output_file})"
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
        # Remove console handler
        for handler in logger.handlers[:]:
            if isinstance(handler, logging.StreamHandler):
                logger.removeHandler(handler)
    
    try:
        # Create processor with custom paths if provided
        processor = PDFProcessor(
            source_folder=args.source,
            archive_folder=args.archive,
            output_file=args.output,
            log_file=args.log
        )
        
        processed_count = processor.process_all_pdfs()
        
        if processed_count > 0:
            logger.info(f"Successfully processed {processed_count} PDF file(s).")
            return 0
        else:
            logger.warning("No PDF files were processed.")
            return 1
    
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
