"""
Entry point for unified PDF processing pipeline.
Extracts text from PDFs and cleans it, saving results to timestamped folders.
"""
import argparse
import sys
from pathlib import Path

# Add project root to Python path for direct script execution
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.pdf_processor import PDFProcessor  # noqa: E402
from src.parquet_processor import ParquetProcessor  # noqa: E402
from src.text_cleaner import TextCleaner  # noqa: E402
from src.config import config  # noqa: E402
from src.utils import get_timestamp_folder_name  # noqa: E402
from cli.common import setup_cli_logging, add_common_arguments, handle_cli_execution  # noqa: E402


def main():
    """Main entry point for unified processing pipeline."""
    parser = argparse.ArgumentParser(
        description="Extract text from PDFs, Parquet files and clean it, saving to timestamped folder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s --input ./my_pdfs --verbose
  %(prog)s --results ./my_results
        """
    )
    
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help=f"Input folder containing PDF and Parquet files (default: {config.input_folder})"
    )
    
    parser.add_argument(
        "--archive",
        type=Path,
        default=None,
        help=f"Archive folder for processed PDFs and Parquet files (default: {config.archive_folder})"
    )
    
    parser.add_argument(
        "--results",
        type=Path,
        default=None,
        help=f"Results folder for output (default: {config.results_folder})"
    )
    
    add_common_arguments(parser, include_log=False)  # Log is in timestamped folder
    
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
    logger = setup_cli_logging(log_file, args.verbose, args.quiet)
    
    logger.info(f"Starting processing pipeline. Results will be saved to: {timestamp_path}")
    
    def run_pipeline() -> int:
        """Inner function for execution logic."""
        # Step 1: Extract text from PDFs
        logger.info("Step 1: Extracting text from PDF files...")
        pdf_processor = PDFProcessor(
            input_folder=args.input,
            archive_folder=args.archive,
            output_file=output_file,
            log_file=log_file
        )
        
        pdf_count = pdf_processor.process_all_pdfs()
        logger.info(f"Successfully processed {pdf_count} PDF file(s).")
        
        # Step 1b: Extract text from Parquet files
        logger.info("Step 1b: Extracting text from Parquet files...")
        parquet_processor = ParquetProcessor(
            input_folder=args.input,
            archive_folder=args.archive,
            output_file=output_file,
            log_file=log_file
        )
        
        parquet_count = parquet_processor.process_all_parquets()
        logger.info(f"Successfully processed {parquet_count} Parquet file(s).")
        
        total_processed = pdf_count + parquet_count
        if total_processed == 0:
            logger.warning("No PDF or Parquet files were processed. Skipping text cleaning.")
            return 1
        
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
    
    return handle_cli_execution(run_pipeline, logger)


if __name__ == "__main__":
    sys.exit(main())

