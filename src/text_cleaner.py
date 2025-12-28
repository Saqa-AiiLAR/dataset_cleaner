"""
Text cleaning module for removing Russian words and special characters.
"""
import regex
from langdetect import detect
import pymorphy2
from natasha import (
    Segmenter,
    MorphVocab,
    NamesExtractor
)
from pathlib import Path
from typing import List
import logging

from .config import config
from .utils import validate_path, format_file_size, get_timestamp
from .exceptions import TextCleaningError, ValidationError, FileNotFoundError

logger = logging.getLogger("SaqaParser.text_cleaner")

# Initialize Russian language tools (module-level for efficiency)
_morph = pymorphy2.MorphAnalyzer()
_segmenter = Segmenter()
_morph_vocab = MorphVocab()
_names_extractor = NamesExtractor(_morph_vocab)
_CYRILLIC_RE = regex.compile(r'\p{IsCyrillic}+')


class TextCleaner:
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
        self.input_file = input_file or config.output_file
        self.output_file = output_file or config.cleaned_output_file
        self.log_file = log_file or config.log_file
        
        # Validate input file
        if not validate_path(self.input_file, must_exist=True, must_be_file=True):
            raise FileNotFoundError(f"Input file does not exist: {self.input_file}")
        
        if not self.input_file.is_file():
            raise ValidationError(f"Input path is not a file: {self.input_file}")
        
        # Check if input file is readable
        if not self.input_file.stat().st_size > 0:
            raise ValidationError(f"Input file is empty: {self.input_file}")
        
        # Check if output file's parent directory exists
        if self.output_file.parent and not self.output_file.parent.exists():
            try:
                self.output_file.parent.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise ValidationError(f"Cannot create output directory {self.output_file.parent}: {e}")
    
    @staticmethod
    def is_russian_word(word: str) -> bool:
        """
        Check if a word is Russian.
        
        Args:
            word: Word to check
        
        Returns:
            True if word is Russian, False otherwise
        """
        word = word.strip()
        
        if not word:
            return False
        
        # 1. Language detection - PRIMARY check (should distinguish Russian from Sakha)
        detected_lang = None
        try:
            detected_lang = detect(word)
            if detected_lang == config.primary_language:
                # Language detection says it's Russian - trust this
                return True
            elif detected_lang and detected_lang != config.primary_language:
                # Language detection says it's NOT Russian (e.g., Sakha) - trust this
                return False
        except Exception:
            pass
        
        # 2. Russian names & surnames
        matches = _names_extractor(word)
        if matches:
            return True
        
        # 3. Morphological analysis - only trust if language detection was inconclusive
        # pymorphy2 is specifically for Russian morphology, but it might parse Sakha words too
        # So we need to be more strict
        try:
            parses = _morph.parse(word)
            if parses:
                # Only trust morphological analysis if:
                # - Language detection didn't work (detected_lang is None)
                # - AND we get high-confidence parses (not just any parse)
                for p in parses:
                    if p.tag is not None and str(p.tag) != 'UNKN':
                        # Check if it's a high-confidence parse (normalized form exists)
                        if p.normal_form and p.normal_form != word.lower():
                            # This suggests it's a real Russian word with morphology
                            # But only if language detection didn't say it's NOT Russian
                            if detected_lang is None:
                                return True
        except Exception:
            pass
        
        # 4. Cyrillic check - only as absolute last resort
        # Only use if language detection failed AND morphological analysis suggests Russian
        if _CYRILLIC_RE.search(word) and detected_lang is None:
            try:
                parses = _morph.parse(word)
                if parses and any(p.tag is not None and str(p.tag) != 'UNKN' for p in parses):
                    # Only if we have a normalized form (suggests real Russian word)
                    if any(p.normal_form and p.normal_form != word.lower() for p in parses):
                        return True
            except Exception:
                pass
        
        return False
    
    @staticmethod
    def remove_russian_words(text: str) -> str:
        """
        Remove Russian words from text.
        
        Args:
            text: Input text
        
        Returns:
            Text with Russian words removed
        """
        # Extract words that may contain separators (-, –, _, \n)
        # Pattern matches sequences of letters with optional separators between them
        words = regex.findall(r'[\p{L}]+(?:[-–_\n][\p{L}]+)*', text)
        
        total_words = len(words)
        logger.info(f"Processing {total_words} words...")
        
        russian_words_found = []
        clean_words = []
        
        for i, w in enumerate(words, 1):
            if TextCleaner.is_russian_word(w):
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
        pattern = regex.compile(r'[\p{L} \n]')
        
        # Find all matching characters (letters, spaces, newlines)
        matches = pattern.findall(text)
        
        # Join the matches back together
        return ''.join(matches)
    
    def clean_text(self) -> int:
        """
        Clean text from input file and save to output file.
        
        Returns:
            Number of characters in cleaned text
        
        Raises:
            FileNotFoundError: If input file doesn't exist
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
        
        logger.info("Processing text (removing special characters, then Russian words)...")
        
        # Process text: first remove special characters, then remove Russian words
        logger.info("Step 1: Removing special characters and numbers...")
        text_no_special = self.remove_special_characters(input_text)
        word_count = len(regex.findall(r'\p{L}+', text_no_special))
        logger.info(f"Removed special characters. Found {word_count} words to process.")
        
        logger.info("Step 2: Removing Russian words...")
        cleaned_text = self.remove_russian_words(text_no_special)
        
        # Count characters in output
        char_count = len(cleaned_text)
        
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
    
    def _write_log_entry(self, char_count: int, file_size: int, error: str = None):
        """
        Write a log entry to the log file.
        
        Args:
            char_count: Number of characters in cleaned text
            file_size: Size of output file in bytes
            error: Optional error message
        """
        timestamp = get_timestamp()
        if error:
            log_entry = f"cleaner.py - {self.input_file.name} -> {self.output_file.name} - {timestamp} - ERROR: {error}\n"
        else:
            log_entry = f"cleaner.py - {self.input_file.name} -> {self.output_file.name} - {timestamp} - {char_count} chars - {file_size} bytes\n"
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)

