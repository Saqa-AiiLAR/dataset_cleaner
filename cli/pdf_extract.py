"""
Entry point for PDF text extraction.
Extracts text from PDF files in workspace/input/ folder and appends to saqa.txt.
"""

import argparse
import sys
from pathlib import Path

# Add project root to Python path for direct script execution
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.pdf_processor import PDFProcessor  # noqa: E402
from src.config import config  # noqa: E402
from cli.common import setup_cli_logging, add_common_arguments, handle_cli_execution  # noqa: E402


def main():
    """Main entry point for PDF extraction."""
    parser = argparse.ArgumentParser(
        description="Extract text from PDF files and append to output file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s --input ./my_pdfs --output ./output.txt
  %(prog)s --verbose
        """,
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help=f"Input folder containing PDF files (default: {config.input_folder})",
    )

    parser.add_argument(
        "--archive",
        type=Path,
        default=None,
        help=f"Archive folder for processed PDFs (default: {config.archive_folder})",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=f"Output file for extracted text (default: {config.output_file})",
    )

    add_common_arguments(parser)

    args = parser.parse_args()

    # Set up logging
    logger = setup_cli_logging(args.log, args.verbose, args.quiet)

    def run_pdf_extraction() -> int:
        """Inner function for execution logic."""
        # Create processor with custom paths if provided
        processor = PDFProcessor(
            input_folder=args.input,
            archive_folder=args.archive,
            output_file=args.output,
            log_file=args.log,
        )

        processed_count = processor.process_all_pdfs()

        if processed_count > 0:
            logger.info(f"Successfully processed {processed_count} PDF file(s).")
            return 0
        else:
            logger.warning("No PDF files were processed.")
            return 1

    return handle_cli_execution(run_pdf_extraction, logger)


if __name__ == "__main__":
    sys.exit(main())
