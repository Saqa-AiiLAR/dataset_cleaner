"""
Entry point for unified PDF processing pipeline.
Extracts text from PDFs and cleans it, saving results to timestamped folders.
"""
import argparse
import sys
import logging
from pathlib import Path

from src.pdf_processor import PDFProcessor
from src.text_cleaner import TextCleaner
from src.logging_config import setup_logging, disable_console_logging
from src.config import config
from src.exceptions import SaqaParserError
from src.utils import get_timestamp_folder_name


def main():
    """Main entry point for unified processing pipeline."""
    parser = argparse.ArgumentParser(
        description="Extract text from PDFs and clean it, saving to timestamped folder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s --source ./my_pdfs --verbose
  %(prog)s --results ./my_results
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
        "--results",
        type=Path,
        default=None,
        help=f"Results folder for output (default: {config.results_folder})"
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
    
    # Generate timestamp folder name
    timestamp_folder = get_timestamp_folder_name()
    
    # Determine results folder
    results_base = args.results or config.results_folder
    results_base = Path(results_base)
    
    # Create timestamped folder path
    timestamp_path = results_base / timestamp_folder
    timestamp_path.mkdir(parents=True, exist_ok=True)
    
    # Set up file paths in timestamped folder
    output_file = timestamp_path / "saqa.txt"
    cleaned_output_file = timestamp_path / "saqaCleaned.txt"
    log_file = timestamp_path / "logs"
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logging(log_file, level=log_level)
    
    if args.quiet:
        disable_console_logging(logger)
    
    logger.info(f"Starting processing pipeline. Results will be saved to: {timestamp_path}")
    
    try:
        # Step 1: Extract text from PDFs
        logger.info("Step 1: Extracting text from PDF files...")
        processor = PDFProcessor(
            source_folder=args.source,
            archive_folder=args.archive,
            output_file=output_file,
            log_file=log_file
        )
        
        processed_count = processor.process_all_pdfs()
        
        if processed_count == 0:
            logger.warning("No PDF files were processed. Skipping text cleaning.")
            return 1
        
        logger.info(f"Successfully processed {processed_count} PDF file(s).")
        
        # Step 2: Clean the extracted text
        logger.info("Step 2: Cleaning extracted text...")
        cleaner = TextCleaner(
            input_file=output_file,
            output_file=cleaned_output_file,
            log_file=log_file
        )
        
        char_count = cleaner.clean_text()
        
        logger.info(f"Processing complete!")
        logger.info(f"Results saved to: {timestamp_path}")
        logger.info(f"  - Extracted text: {output_file}")
        logger.info(f"  - Cleaned text: {cleaned_output_file}")
        logger.info(f"  - Logs: {log_file}")
        logger.info(f"Cleaned text contains {char_count} characters.")
        
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

