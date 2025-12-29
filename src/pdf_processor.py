"""
PDF processing module for extracting text from PDF files.
"""
import pdfplumber
import shutil
from pathlib import Path
from typing import List, Tuple, Optional
import logging

from .config import config
from .utils import format_file_size, get_timestamp
from .exceptions import PDFProcessingError, ValidationError, MissingFileError
from .base_processor import BaseProcessor

logger = logging.getLogger("SaqaParser.pdf_processor")


class PDFProcessor(BaseProcessor):
    """Handles PDF text extraction and file management."""
    
    def __init__(self, source_folder: Optional[Path] = None, 
                 archive_folder: Optional[Path] = None,
                 output_file: Optional[Path] = None,
                 log_file: Optional[Path] = None):
        """
        Initialize PDF processor.
        
        Args:
            source_folder: Folder containing PDF files to process
            archive_folder: Folder to move processed PDFs to
            output_file: File to append extracted text to
            log_file: File to write log entries to
        """
        super().__init__(log_file=log_file or config.log_file)
        self.source_folder = source_folder or config.source_folder
        self.archive_folder = archive_folder or config.archive_folder
        self.output_file = output_file or config.output_file
        
        # Validate and create paths using base class methods
        self.validate_directory(self.source_folder, must_exist=True)
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
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                page_count = len(pdf.pages)
                logger.info(f"Extracting text from {page_count} pages...")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = self._extract_page_text_adaptive(page, page_num)
                    if page_text:
                        extracted_text += page_text
                    
                    # Show progress
                    if page_num % config.progress_interval_pages == 0 or page_num == page_count:
                        percentage = (page_num / page_count) * 100
                        logger.info(f"Progress: Page {page_num}/{page_count} ({percentage:.1f}%)")
        
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
    
    def _extract_page_text_adaptive(self, page, page_num: int) -> str:
        """
        Extract text from a page using adaptive tolerance strategy.
        
        Starts with conservative tolerance and increases if badness score is high.
        
        Args:
            page: pdfplumber page object
            page_num: Page number for logging
            
        Returns:
            Extracted text
        """
        if not config.pdf_adaptive_tolerance:
            # Use default tolerance if adaptive mode is disabled
            return page.extract_text(
                x_tolerance=config.pdf_x_tolerance,
                y_tolerance=config.pdf_y_tolerance,
                layout=config.pdf_layout_mode
            )
        
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
                    return page_text
                
                # Track best result so far
                if score < best_score:
                    best_score = score
                    best_text = page_text
                    
            except Exception as e:
                logger.warning(f"Page {page_num}: Error with tolerance ({x_tol}, {y_tol}): {e}")
                continue
        
        # Use best result found
        if best_text:
            logger.debug(f"Page {page_num}: Using best tolerance, score: {best_score:.3f}")
        else:
            # Fallback: try with default settings
            logger.warning(f"Page {page_num}: All tolerance levels failed, using default")
            best_text = page.extract_text(
                x_tolerance=config.pdf_x_tolerance,
                y_tolerance=config.pdf_y_tolerance,
                layout=config.pdf_layout_mode
            ) or ""
        
        return best_text
    
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
                logger.warning(f"No text extracted from {pdf_path.name}")
            
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
            log_entry = f"pdf_insert.py - {filename} - {timestamp} - ERROR: {error}\n"
        else:
            log_entry = f"pdf_insert.py - {filename} - {timestamp} - {char_count} chars - {file_size} bytes - {page_count} pages\n"
        
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
        pdf_files = list(self.source_folder.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning("No PDF files found in source folder.")
            return 0
        
        total_pdfs = len(pdf_files)
        logger.info(f"Found {total_pdfs} PDF file(s) to process.")
        
        processed_count = 0
        
        for pdf_index, pdf_path in enumerate(pdf_files, 1):
            try:
                logger.info(f"\n[{pdf_index}/{total_pdfs}] Processing: {pdf_path.name}")
                char_count, file_size = self.process_pdf(pdf_path)
                processed_count += 1
                logger.info(f"Successfully processed {pdf_path.name} ({format_file_size(file_size)})")
            except Exception as e:
                logger.error(f"Failed to process {pdf_path.name}: {str(e)}")
                continue
        
        logger.info(f"\nProcessing complete. Processed {processed_count}/{total_pdfs} file(s).")
        return processed_count

