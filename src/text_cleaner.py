"""
Text cleaning module for removing Russian words and special characters.
"""
import regex
from pathlib import Path
from typing import List, Optional
import logging

from .config import config
from .utils import format_file_size, get_timestamp
from .exceptions import TextCleaningError, MissingFileError
from .language_detector import get_classifier
from .base_processor import BaseProcessor

logger = logging.getLogger("SaqaParser.text_cleaner")

# Pre-compiled regex patterns for performance
_WORD_PATTERN = regex.compile(r'[\p{L}]+(?:[-–_\n][\p{L}]+)*')
_LETTER_SPACE_NEWLINE_PATTERN = regex.compile(r'[\p{L} \n]')
_SPACED_LETTERS_PATTERN = regex.compile(r'\b(?:\p{L}\s+)+\p{L}\b')
_WORD_WITH_DOT_PATTERN = regex.compile(r'\p{L}+\.?')
_SINGLE_LETTER_PATTERN = regex.compile(r'\p{L}')
_UPPERCASE_CYRILLIC_PATTERN = regex.compile(r'^[А-ЯЁ]{2,5}$')
_LATIN_ONLY_PATTERN = regex.compile(r'^[A-Za-z]+$')
_ROMAN_NUMERAL_PATTERN = regex.compile(r'^[IVXLCDM]+$', regex.IGNORECASE)
_WHITESPACE_PATTERN = regex.compile(r'\s+')
_LETTER_PATTERN = regex.compile(r'\p{L}+')


class TextCleaner(BaseProcessor):
    """Handles text cleaning and Russian word removal."""
    
    def __init__(self, input_file: Path = None, output_file: Path = None, 
                 log_file: Path = None):
        """
        Initialize text cleaner.
        
        Args:
            input_file: Path to input text file
            output_file: Path to output cleaned text file
            log_file: Path to log file
        """
        super().__init__(log_file=log_file or config.log_file)
        self.input_file = input_file or config.output_file
        self.output_file = output_file or config.cleaned_output_file
        self.classifier = get_classifier()
        
        # Validate paths using base class methods
        self.validate_file(self.input_file, must_exist=True, must_be_file=True)
        self.ensure_output_directory(self.output_file)
    
    def remove_russian_words(self, text: str) -> str:
        """
        Remove Russian words from text.
        
        Args:
            text: Input text
        
        Returns:
            Text with Russian words removed
        """
        # Extract words that may contain separators (-, –, _, \n)
        # Pattern matches sequences of letters with optional separators between them
        words = _WORD_PATTERN.findall(text)
        
        total_words = len(words)
        logger.info(f"Processing {total_words} words...")
        
        russian_words_found = []
        clean_words = []
        
        for i, w in enumerate(words, 1):
            if self.classifier.is_russian_word(w):
                russian_words_found.append(w)
            else:
                # For non-Russian words, replace separators (-, –, _, \n) with spaces
                cleaned_word = w.replace('-', ' ').replace('–', ' ').replace('_', ' ').replace('\n', ' ')
                # Remove extra spaces and add to clean words
                cleaned_word = ' '.join(cleaned_word.split())
                if cleaned_word:  # Only add if word is not empty after cleaning
                    clean_words.append(cleaned_word)
            
            # Show progress
            if i % config.progress_interval_words == 0 or i == total_words:
                percentage = (i / total_words) * 100
                logger.info(f"Progress: {i}/{total_words} words ({percentage:.1f}%) processed...")
        
        # Debug: show sample of Russian words found
        if russian_words_found:
            sample = russian_words_found[:config.debug_sample_size]
            logger.debug(f"Found {len(russian_words_found)} Russian words (showing first {config.debug_sample_size}): {sample}")
            logger.info(f"Keeping {len(clean_words)} non-Russian words")
        else:
            logger.info(f"No Russian words found, keeping all {len(clean_words)} words")
        
        return " ".join(clean_words)
    
    @staticmethod
    def remove_special_characters(text: str) -> str:
        """
        Remove all special characters and numbers, keeping only:
        - Letters (Cyrillic and non-Cyrillic)
        - Spaces
        - Line breaks (\n)
        
        Args:
            text: Input text
        
        Returns:
            Text with special characters removed
        """
        # Pattern to match: Unicode letters, spaces, or newlines
        # \p{L} matches any Unicode letter (includes Cyrillic and Latin)
        # Space character and \n for line breaks
        
        # Find all matching characters (letters, spaces, newlines)
        matches = _LETTER_SPACE_NEWLINE_PATTERN.findall(text)
        
        # Join the matches back together
        return ''.join(matches)
    
    def filter_invalid_words(self, text: str) -> str:
        """
        Filter out invalid words from text:
        - Single-letter words (Yakut language has no single-letter words)
        - Abbreviations (words with dots, short uppercase words)
        - Words where all letters are separated by spaces
        - English words (words consisting only of Latin letters)
        - Roman numerals (sequences of I, V, X, L, C, D, M)
        
        Args:
            text: Input text
        
        Returns:
            Text with invalid words removed
        """
        # Track statistics
        single_letter_count = 0
        abbreviation_count = 0
        spaced_letters_count = 0
        english_words_count = 0
        roman_numerals_count = 0
        
        # Step 1: Remove words where all letters are separated by spaces
        # Pattern: sequence of letters separated by spaces (e.g., "а б р е в")
        
        def remove_spaced_letters(match):
            nonlocal spaced_letters_count
            spaced_letters_count += 1
            return ''  # Remove the match
        
        text = _SPACED_LETTERS_PATTERN.sub(remove_spaced_letters, text)
        
        # Normalize spaces after removing spaced letters
        text = _WHITESPACE_PATTERN.sub(' ', text).strip()
        
        # Step 2: Split text into words and filter
        # Extract words (sequences of letters, possibly with dots at the end)
        words = _WORD_WITH_DOT_PATTERN.findall(text)
        
        filtered_words = []
        
        for word in words:
            word_stripped = word.strip()
            
            # Skip empty words
            if not word_stripped:
                continue
            
            # Filter 1: Remove single-letter words (all Unicode letters)
            if len(word_stripped) == 1 and _SINGLE_LETTER_PATTERN.match(word_stripped):
                single_letter_count += 1
                continue
            
            # Filter 2: Remove abbreviations with dots (e.g., "г.", "стр.", "т.д.")
            if '.' in word_stripped:
                abbreviation_count += 1
                continue
            
            # Filter 3: Remove short uppercase words (2-5 characters, all uppercase Cyrillic)
            # Pattern matches 2-5 uppercase Cyrillic letters
            if _UPPERCASE_CYRILLIC_PATTERN.match(word_stripped):
                abbreviation_count += 1
                continue
            
            # Filter 4: Remove English words (words consisting only of Latin letters)
            # Check if word contains only Latin letters (A-Z, a-z)
            if _LATIN_ONLY_PATTERN.match(word_stripped):
                english_words_count += 1
                continue
            
            # Filter 5: Remove Roman numerals (sequences of I, V, X, L, C, D, M)
            # Pattern matches sequences of Roman numeral characters
            if _ROMAN_NUMERAL_PATTERN.match(word_stripped):
                roman_numerals_count += 1
                continue
            
            # Keep the word
            filtered_words.append(word_stripped)
        
        # Log statistics
        if single_letter_count > 0:
            logger.info(f"Removed {single_letter_count} single-letter word(s)")
        if abbreviation_count > 0:
            logger.info(f"Removed {abbreviation_count} abbreviation(s)")
        if spaced_letters_count > 0:
            logger.info(f"Removed {spaced_letters_count} word(s) with spaced letters")
        if english_words_count > 0:
            logger.info(f"Removed {english_words_count} English word(s)")
        if roman_numerals_count > 0:
            logger.info(f"Removed {roman_numerals_count} Roman numeral(s)")
        else:
            logger.debug("Roman numeral filter checked - no Roman numerals found")
        
        if (single_letter_count == 0 and abbreviation_count == 0 and spaced_letters_count == 0 
            and english_words_count == 0 and roman_numerals_count == 0):
            logger.debug("No invalid words found to filter")
        
        # Join filtered words back with spaces
        return ' '.join(filtered_words)
    
    def process(self) -> int:
        """
        Process text cleaning (implements BaseProcessor interface).
        
        Returns:
            Number of characters in cleaned text
        """
        return self.clean_text()
    
    def clean_text(self) -> int:
        """
        Clean text from input file and save to output file.
        
        Returns:
            Number of characters in cleaned text
        
        Raises:
            MissingFileError: If input file doesn't exist
            TextCleaningError: If text cleaning fails
        """
        logger.info(f"Reading {self.input_file}...")
        
        # Read input file
        try:
            with open(self.input_file, "r", encoding="utf-8") as f:
                input_text = f.read()
        except UnicodeDecodeError as e:
            error_msg = f"Cannot decode input file {self.input_file}: {str(e)}"
            logger.error(error_msg)
            raise TextCleaningError(error_msg) from e
        except IOError as e:
            error_msg = f"Cannot read input file {self.input_file}: {str(e)}"
            logger.error(error_msg)
            raise TextCleaningError(error_msg) from e
        
        logger.info("Processing text (removing special characters, healing OCR errors, then Russian words)...")
        
        # Process text: first remove special characters, then heal OCR errors, then remove Russian words
        logger.info("Step 1: Removing special characters and numbers...")
        text_no_special = self.remove_special_characters(input_text)
        word_count = len(_LETTER_PATTERN.findall(text_no_special))
        logger.info(f"Removed special characters. Found {word_count} words to process.")
        
        # Step 2: Word healing (repair OCR-broken words) - dynamic step numbering
        step_num = 2
        if config.word_healer_enabled:
            logger.info(f"Step {step_num}: Applying word healing to repair OCR-broken words...")
            from .word_healer import WordHealer
            healer = WordHealer()
            text_no_special = healer.heal_text(text_no_special)
            logger.info("Word healing complete.")
            step_num += 1
        
        # Step X: Filter invalid words (abbreviations, single letters, spaced letters)
        logger.info(f"Step {step_num}: Filtering invalid words (abbreviations, single letters, spaced letters)...")
        text_no_special = self.filter_invalid_words(text_no_special)
        logger.info("Invalid words filtering complete.")
        step_num += 1
        
        logger.info(f"Step {step_num}: Removing Russian words...")
        cleaned_text = self.remove_russian_words(text_no_special)
        
        # Count characters in output
        char_count = len(cleaned_text)
        
        # Check if result is empty
        if not cleaned_text.strip():
            logger.warning("Cleaned text is empty - no Sakha words found or all text was filtered")
        
        logger.info(f"Writing cleaned text to {self.output_file}...")
        
        # Write output file
        try:
            with open(self.output_file, "w", encoding="utf-8") as f:
                f.write(cleaned_text)
        except IOError as e:
            error_msg = f"Cannot write output file {self.output_file}: {str(e)}"
            logger.error(error_msg)
            raise TextCleaningError(error_msg) from e
        
        # Get output file size
        file_size = self.output_file.stat().st_size
        
        logger.info(f"Processed and saved cleaned text ({char_count} chars, {format_file_size(file_size)})")
        
        # Write log entry
        self._write_log_entry(char_count, file_size)
        
        return char_count
    
    def _write_log_entry(self, char_count: int, file_size: int, error: Optional[str] = None) -> None:
        """
        Write a log entry to the log file.
        
        Args:
            char_count: Number of characters in cleaned text
            file_size: Size of output file in bytes
            error: Optional error message
        """
        timestamp = get_timestamp()
        if error:
            log_entry = f"TextCleaner - {self.input_file.name} -> {self.output_file.name} - {timestamp} - ERROR: {error}\n"
        else:
            log_entry = f"TextCleaner - {self.input_file.name} -> {self.output_file.name} - {timestamp} - {char_count} chars - {file_size} bytes\n"
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)

