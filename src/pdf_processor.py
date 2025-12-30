"""
PDF processing module for extracting text from PDF files.
"""
import pdfplumber
import shutil
import regex
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

from .config import config
from .utils import format_file_size, get_timestamp
from .exceptions import PDFProcessingError, ValidationError, MissingFileError
from .base_processor import BaseProcessor
from .progress import ProgressBar

logger = logging.getLogger("SaqaParser.pdf_processor")

# Pre-compiled regex pattern for hyphenated line breaks
# Matches: word ending with hyphen, optional whitespace, newline, optional whitespace, word continuation
_HYPHENATED_LINE_BREAK_PATTERN = regex.compile(r'([\p{L}]+)-\s*\n\s*([\p{L}]+)', regex.UNICODE)


class PDFProcessor(BaseProcessor):
    """Handles PDF text extraction and file management."""
    
    def __init__(self, input_folder: Optional[Path] = None, 
                 archive_folder: Optional[Path] = None,
                 output_file: Optional[Path] = None,
                 log_file: Optional[Path] = None):
        """
        Initialize PDF processor.
        
        Args:
            input_folder: Folder containing PDF files to process
            archive_folder: Folder to move processed PDFs to
            output_file: File to append extracted text to
            log_file: File to write log entries to
        """
        super().__init__(log_file=log_file or config.log_file)
        self.input_folder = input_folder or config.input_folder
        self.archive_folder = archive_folder or config.archive_folder
        self.output_file = output_file or config.output_file
        
        # Validate and create paths using base class methods
        self.validate_directory(self.input_folder, must_exist=True)
        self.validate_directory(self.archive_folder, must_exist=False, create_if_missing=True)
        self.ensure_output_directory(self.output_file)
    
    def extract_text_from_pdf(self, pdf_path: Path) -> Tuple[str, int]:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
        
        Returns:
            Tuple of (extracted_text, page_count)
        
        Raises:
            MissingFileError: If PDF file doesn't exist
            ValidationError: If PDF file is invalid or unreadable
            PDFProcessingError: If PDF processing fails
        """
        # Validate PDF file
        if not pdf_path.exists():
            raise MissingFileError(f"PDF file does not exist: {pdf_path}")
        
        if not pdf_path.is_file():
            raise ValidationError(f"Path is not a file: {pdf_path}")
        
        if not pdf_path.suffix.lower() == '.pdf':
            raise ValidationError(f"File is not a PDF: {pdf_path}")
        
        extracted_text = ""
        page_count = 0
        warning_counts: Dict[str, int] = {}  # Dictionary to count repeating warnings
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                page_count = len(pdf.pages)
                logger.info(f"Extracting text from {page_count} pages...")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text, warning_msg = self._extract_page_text_adaptive(page, page_num, warning_counts)
                    if page_text:
                        extracted_text += page_text
                    
                    # Show progress
                    if page_num % config.progress_interval_pages == 0 or page_num == page_count:
                        percentage = (page_num / page_count) * 100
                        logger.info(f"Progress: Page {page_num}/{page_count} ({percentage:.1f}%)")
                
                # Log grouped warnings at the end
                for warning_msg, count in warning_counts.items():
                    if count >= 1:
                        page_word = "page" if count == 1 else "pages"
                        logger.warning(f"{count} {page_word}: {warning_msg}")
                
                # Merge hyphenated line breaks in the complete extracted text
                extracted_text, merge_count = self._merge_hyphenated_line_breaks(extracted_text)
                if merge_count > 0:
                    logger.info(f"Merged {merge_count} hyphenated line break(s) in extracted text")
        
        except pdfplumber.exceptions.PDFSyntaxError as e:
            error_msg = f"Invalid PDF syntax in {pdf_path.name}: {str(e)}"
            logger.error(error_msg)
            raise PDFProcessingError(error_msg) from e
        except Exception as e:
            error_msg = f"Error extracting text from {pdf_path.name}: {str(e)}"
            logger.error(error_msg)
            raise PDFProcessingError(error_msg) from e
        
        return extracted_text, page_count
    
    def _calculate_badness_score(self, text: str) -> float:
        """
        Calculate badness score: ratio of single-character "words" to total words.
        
        Higher score indicates more broken words (likely OCR issues).
        
        Args:
            text: Extracted text to analyze
            
        Returns:
            Badness score (0.0-1.0), where 1.0 means all words are single characters
        """
        if not text.strip():
            return 0.0
        
        words = text.split()
        if not words:
            return 0.0
        
        single_char_words = sum(1 for w in words if len(w) == 1)
        return single_char_words / len(words)
    
    def _merge_hyphenated_line_breaks(self, text: str) -> Tuple[str, int]:
        """
        Merge words that are split across lines with hyphens.
        
        Detects pattern: word ending with hyphen, followed by newline, followed by word continuation.
        Merges them into a single word by removing the hyphen, newline, and any whitespace.
        
        Example: "word-\ncontinues" → "wordcontinues"
        
        Args:
            text: Extracted text that may contain hyphenated line breaks
            
        Returns:
            Tuple of (merged_text, count_of_merges)
        """
        if not text:
            return text, 0
        
        merge_count = 0
        
        def merge_match(match):
            """Replace hyphenated line break with merged word."""
            nonlocal merge_count
            merge_count += 1
            # Group 1: word part before hyphen
            # Group 2: word continuation after newline
            return match.group(1) + match.group(2)
        
        merged_text = _HYPHENATED_LINE_BREAK_PATTERN.sub(merge_match, text)
        
        if merge_count > 0:
            logger.debug(f"Merged {merge_count} hyphenated line break(s)")
        
        return merged_text, merge_count
    
    def _extract_page_text_adaptive(self, page, page_num: int, warning_counts: dict) -> Tuple[str, Optional[str]]:
        """
        Extract text from a page using adaptive tolerance strategy.
        
        Starts with conservative tolerance and increases if badness score is high.
        
        Args:
            page: pdfplumber page object
            page_num: Page number for logging
            warning_counts: Dictionary to track repeating warnings
            
        Returns:
            Tuple of (extracted_text, warning_message or None)
        """
        if not config.pdf_adaptive_tolerance:
            # Use default tolerance if adaptive mode is disabled
            text = page.extract_text(
                x_tolerance=config.pdf_x_tolerance,
                y_tolerance=config.pdf_y_tolerance,
                layout=config.pdf_layout_mode
            ) or ""
            return text, None
        
        # Adaptive strategy: try increasing tolerance levels
        tolerance_levels = [
            (1, 1),   # Conservative
            (config.pdf_x_tolerance, config.pdf_y_tolerance),  # Default
            (5, 5),  # Aggressive
        ]
        
        best_text = ""
        best_score = 1.0  # Start with worst possible score
        
        for x_tol, y_tol in tolerance_levels:
            try:
                page_text = page.extract_text(
                    x_tolerance=x_tol,
                    y_tolerance=y_tol,
                    layout=config.pdf_layout_mode
                ) or ""
                
                if not page_text:
                    continue
                
                # Calculate badness score
                score = self._calculate_badness_score(page_text)
                
                # If score is below threshold, this is good enough
                if score <= config.pdf_badness_threshold:
                    logger.debug(f"Page {page_num}: Using tolerance ({x_tol}, {y_tol}), score: {score:.3f}")
                    return page_text, None
                
                # Track best result so far
                if score < best_score:
                    best_score = score
                    best_text = page_text
                    
            except Exception as e:
                logger.debug(f"Page {page_num}: Error with tolerance ({x_tol}, {y_tol}): {e}")
                continue
        
        # Use best result found
        if best_text:
            logger.debug(f"Page {page_num}: Using best tolerance, score: {best_score:.3f}")
            return best_text, None
        else:
            # Fallback: try with default settings
            warning_msg = "All tolerance levels failed, using default"
            logger.debug(f"Page {page_num}: {warning_msg}")
            # Track this warning for grouping
            warning_counts[warning_msg] = warning_counts.get(warning_msg, 0) + 1
            best_text = page.extract_text(
                x_tolerance=config.pdf_x_tolerance,
                y_tolerance=config.pdf_y_tolerance,
                layout=config.pdf_layout_mode
            ) or ""
            return best_text, warning_msg
    
    def process_pdf(self, pdf_path: Path) -> Tuple[int, int]:
        """
        Process a single PDF file: extract text, save to output, move to archive.
        
        Args:
            pdf_path: Path to the PDF file
        
        Returns:
            Tuple of (character_count, file_size_bytes)
        """
        file_size = pdf_path.stat().st_size
        
        try:
            # Extract text
            extracted_text, page_count = self.extract_text_from_pdf(pdf_path)
            char_count = len(extracted_text)
            
            # Append to output file
            if extracted_text:
                with open(self.output_file, "a", encoding="utf-8") as f:
                    f.write(extracted_text)
                logger.info(f"Extracted and saved text from {pdf_path.name} ({char_count} chars, {page_count} pages)")
            else:
                if char_count == 0 and page_count > 0:
                    logger.warning(
                        f"No text extracted from {pdf_path.name} - "
                        "file may be scanned PDF (images without text layer), "
                        "protected, or have unreadable structure"
                    )
                else:
                    logger.warning(f"No text extracted from {pdf_path.name} - file may be empty or unreadable")
                # Still continue processing even if no text extracted
            
            # Move to archive
            archive_path = self.archive_folder / pdf_path.name
            shutil.move(str(pdf_path), str(archive_path))
            logger.info(f"Moved {pdf_path.name} to archive folder")
            
            # Write log entry
            self._write_log_entry(pdf_path.name, char_count, file_size, page_count)
            
            return char_count, file_size
        
        except (PDFProcessingError, MissingFileError, ValidationError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            error_msg = f"Unexpected error processing {pdf_path.name}: {str(e)}"
            logger.error(error_msg)
            self._write_log_entry(pdf_path.name, 0, file_size, 0, error=error_msg)
            raise PDFProcessingError(error_msg) from e
    
    def _write_log_entry(self, filename: str, char_count: int, file_size: int, 
                        page_count: int, error: Optional[str] = None):
        """
        Write a log entry to the log file.
        
        Args:
            filename: Name of the processed file
            char_count: Number of characters extracted
            file_size: Size of the file in bytes
            page_count: Number of pages in the PDF
            error: Optional error message
        """
        timestamp = get_timestamp()
        if error:
            log_entry = f"PDFProcessor - {filename} - {timestamp} - ERROR: {error}\n"
        else:
            log_entry = f"PDFProcessor - {filename} - {timestamp} - {char_count} chars - {file_size} bytes - {page_count} pages\n"
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
    
    def process(self) -> int:
        """
        Process all PDF files (implements BaseProcessor interface).
        
        Returns:
            Number of files processed successfully
        """
        return self.process_all_pdfs()
    
    def process_all_pdfs(self) -> int:
        """
        Process all PDF files in the source folder.
        
        Returns:
            Number of files processed successfully
        """
        pdf_files = list(self.input_folder.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in input folder: {self.input_folder}")
            return 0
        
        total_pdfs = len(pdf_files)
        logger.info(f"Found {total_pdfs} PDF file(s) to process.")
        
        processed_count = 0
        progress = ProgressBar(total=total_pdfs, desc="Processing PDFs")
        
        for pdf_index, pdf_path in enumerate(pdf_files, 1):
            try:
                char_count, file_size = self.process_pdf(pdf_path)
                processed_count += 1
                progress.update(pdf_index, suffix=pdf_path.name)
            except Exception as e:
                logger.error(f"Failed to process {pdf_path.name}: {str(e)}")
                progress.update(pdf_index, suffix=f"Error: {pdf_path.name}")
                continue
        
        progress.finish()
        logger.info(f"Processing complete. Processed {processed_count}/{total_pdfs} file(s).")
        return processed_count

